from datetime import datetime, timedelta
import datetime as DT
import time
import dateutil.relativedelta as REL
import os
import discord
import requests
import sqlite3
from helpers import hyperlink, Emoji
from pybungie import BungieAPI, VendorHash, Definitions, Components, MembershipType, PlayerClass, DamageType

LOCATION_ROOT_PATH = 'https://paracausal.science/xur/current.json'  # credit to to @nev_rtheless
bungie_api = BungieAPI(api_key=os.getenv("API_KEY"))
bungie_api.input_xbox_credentials(xbox_live_email=os.getenv("XBOX_LIVE_EMAIL"),
                                  xbox_live_password=os.getenv("XBOX_LIVE_PASSWORD"))
bungie_api.start_oauth2(client_id=os.getenv("CLIENT_ID"), client_secret=os.getenv("CLIENT_SECRET"))


def add_bounty(embed: discord.Embed, name: str, description: str, bounty_type: str):
    embed.add_field(name=f'**{name}**', value=description, inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="\u200b", value=f"\n{bounty_type}\n", inline=True)


class Vendor:
    """
    Destiny 2 Vendor Class
    """

    def __new__(cls, name: str):
        """
        Creates an instance of a Destiny 2 vendor

        :param name: The name of the vendor you want to create
        """
        name = name.upper()
        if name == 'XUR':
            return Xur(name=name)
        else:
            return RegularVendor(name=name)


class RegularVendor:
    def __init__(self, name: str):
        """Standard class for non-Xur vendors in Destiny 2

        :param name: The name of the curr_vendor you want to create
        """
        try:
            self.hash_id = (VendorHash[name])
        except KeyError:
            self.hash_id = next((curr_vendor for curr_vendor in VendorHash if name in curr_vendor.name), None)
            if self.hash_id is None or self.hash_id is VendorHash.TESS_EVERIS:
                raise RuntimeError

        displayProperties = bungie_api.manifest((Definitions['VENDOR']).value, self.hash_id.value)['displayProperties']
        self.name = displayProperties['name']
        self.subtitle = displayProperties['subtitle']
        self.description = displayProperties['description']
        self.icon = displayProperties['smallTransparentIcon']
        self.membership_id = int(os.getenv("MEMBERSHIP_ID"))
        self.character_id = int(os.getenv("CHARACTER_ID"))
        self.days_between_refresh = 5
        self.cache_check = None
        self.cached_message = None

    def create_embed_title(self):
        embed = discord.Embed(
            title=self.name + ', ' + self.subtitle,
            description=self.description,
            color=discord.Color.blue()
        )
        return embed

    def message(self):
        """Creates an Embed that contains the vendors current bounties, or a generic response if they are not available

        :return: string or discord.Embed
        """
        today = DT.date.today()
        if self.cached_message and (
                (today == self.cache_check and datetime.now().hour < 12) or today != self.cache_check):
            return self.cached_message

        weekly_bounties, daily_bounties = self.items()
        embed = self.create_embed_title()
        embed.set_thumbnail(url=f'https://www.bungie.net/{self.icon}')
        if weekly_bounties:  # if any weekly bounties exist
            for bounty in weekly_bounties:
                add_bounty(embed=embed,
                           name=bounty["name"],
                           description=bounty['description'],
                           bounty_type="Weekly Bounty")
        if daily_bounties:  # if any daily bounties exist
            for bounty in daily_bounties:
                add_bounty(embed=embed,
                           name=bounty["name"],
                           description=bounty['description'],
                           bounty_type="Daily Bounty")
        if not daily_bounties and not weekly_bounties:
            raise RuntimeError
        self.cached_message = embed
        self.cache_check = today + timedelta(days=1)
        return self.cached_message

    def items(self):
        daily_bounties = []
        weekly_bounties = []
        curr_vendor = bungie_api.get_vendor(membership_type=MembershipType.STEAM,
                                            membership_id=self.membership_id,
                                            character_id=self.character_id, vendor_hash=self.hash_id,
                                            components=Components.VendorSales)
        items = curr_vendor['sales']['data']
        items = list(items.values())
        db = sqlite3.connect('destiny.db')
        db.row_factory = sqlite3.Row
        for item in items:
            hash_id = item['itemHash']
            db_item = db.execute("SELECT * FROM bounties WHERE hash=?", (hash_id,)).fetchone()
            if db_item:
                bounty_dict = dict(db_item)
            else:
                bounty = self.manifest_bounty(hash_id=hash_id)
                displayProperties = bounty['displayProperties']
                bounty_dict = {
                    'name': displayProperties['name'],
                    'description': displayProperties['description'],
                    'bountyType': bounty['itemTypeDisplayName'],
                    'hash': hash_id
                }
                if bounty_dict['bountyType'][:5] == "Daily" or bounty_dict['bountyType'][:6] == "Weekly":
                    db.execute("INSERT INTO bounties VALUES (:name, :description, :bountyType, :hash)", bounty_dict)
                    db.commit()

            bounty_type = bounty_dict['bountyType']
            if bounty_type[:5] == "Daily":
                daily_bounties.append(bounty_dict)
            if bounty_type[:6] == "Weekly":
                weekly_bounties.append(bounty_dict)
        db.close()
        return weekly_bounties, daily_bounties

    def manifest_bounty(self, hash_id: int):
        return bungie_api.manifest((Definitions['ITEM']).value, hash_id)


class Xur(RegularVendor):
    def __init__(self, name: str):
        super().__init__(name)
        self.days_between_refresh = 3
        self.embedded = False

    def message(self):
        """Creates an Embed that contains Xur's inventory, or a generic response if Xur is not available

        :return: string or discord.Embed
        """
        next_refresh = self.get_next_refresh()
        leaving_time = self.get_time_until_refresh(next_refresh=next_refresh)

        today = DT.date.today()
        next_friday = today + REL.relativedelta(weekday=REL.FR)
        curr_time = time.localtime().tm_hour

        if leaving_time.total_seconds() < 0 or (today == next_friday and curr_time < 12):
            self.embedded = False
            self.cached_message = "*I will return on Friday guardian*\n Try again on " + next_friday.strftime(
                "%B, %d %Y") + " at 12pm EST"
            return self.cached_message

        if next_refresh == self.cache_check and self.embedded:
            return self.cached_message

        try:
            embed = self.create_embed_title()
            embed.clear_fields()
            inventory = self.items()
            embed.set_thumbnail(url='https://www.bungie.net/' + self.icon)
            embed.add_field(name="**Location**", value=self.location(), inline=False)
            embed.add_field(name=Emoji[inventory['UNKNOWN']['damageType']].value + " **Weapon**",
                            value=hyperlink(inventory['UNKNOWN']), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="\u200b", value=inventory['UNKNOWN']['type'], inline=True)
            embed.add_field(name=Emoji.TITAN.value + " **Titan**", value=hyperlink(inventory['TITAN']),
                            inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="\u200b", value=inventory['TITAN']['type'], inline=True)
            embed.add_field(name=Emoji.HUNTER.value + " **Hunter**", value=hyperlink(inventory['HUNTER']),
                            inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="\u200b", value=inventory['HUNTER']['type'], inline=True)
            embed.add_field(name=Emoji.WARLOCK.value + " **Warlock**", value=hyperlink(inventory['WARLOCK']),
                            inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="\u200b", value=inventory['WARLOCK']['type'], inline=True)
            embed.set_footer(
                text='I will be leaving in ' + str(leaving_time)[:-10].replace(':', ' hours, and ') + ' minutes')
            self.embedded = True
            self.cache_check = next_refresh
            self.cached_message = embed
            return self.cached_message
        except KeyError:
            self.embedded = False
            return "*I will return on Friday guardian*\nTry again on " + next_friday.strftime(
                "%B, %d %Y") + " at 12pm EST"

    def items(self) -> dict:
        """Retrieve a vendor's inventory

        :return: dict -
            {'class_type': {'name': 'item_name', 'type': 'item_type', 'hash': 'item_hash', 'damageType': 'damage_type'}}
        """
        inventory = {}
        my_items = \
            bungie_api.get_public_vendors(components=Components.VendorSales)['sales']['data'][
                str(self.hash_id.value)][
                'saleItems']
        db = sqlite3.connect('destiny.db')
        db.row_factory = sqlite3.Row
        for item, count in zip(my_items,
                               range(5)):  # For each item they're selling, find it's name, type, hash and class type
            item_hash = my_items[item]['itemHash']  # current item hash
            if item_hash == 3875551374:
                continue
            db_item = db.execute("SELECT * FROM items WHERE hash=?", (item_hash,)).fetchone()
            if db_item:
                db_item = dict(db_item)
                inventory[db_item['classType']] = db_item
            else:
                item_info = bungie_api.manifest(entity_type=(Definitions['ITEM']).value, hash_identifier=item_hash)

                name = item_info['displayProperties']['name']
                class_type = (PlayerClass(item_info['classType'])).name
                item_type = item_info['itemTypeDisplayName']
                damage_type = (DamageType(item_info['defaultDamageType'])).name

                # create dictionary for current item
                item_dict = {
                    'name': name,
                    'type': item_type,
                    'hash': item_hash,
                    'damageType': damage_type,
                    'classType': class_type
                }
                db.execute("INSERT INTO items VALUES (:name, :type, :hash, :damageType, :classType)", item_dict)
                db.commit()
                inventory[class_type] = item_dict
        db.close()
        return inventory

    def get_next_refresh(self) -> [datetime, str]:
        """Returns Vendors next refresh date, or empty string

        :return: datetime or str
        """
        try:
            next_refresh_date = datetime.strptime(
                (bungie_api.get_vendor(membership_type=MembershipType.STEAM,
                                       membership_id=int(os.getenv("MEMBERSHIP_ID")),
                                       character_id=int(os.getenv("CHARACTER_ID")), vendor_hash=self.hash_id,
                                       components=Components.Vendors)['vendor']['data']['nextRefreshDate']),
                '%Y-%m-%dT%H:%M:%SZ')
            return next_refresh_date
        except:
            return ''

    def get_time_until_refresh(self, next_refresh: datetime) -> timedelta:
        return next_refresh - timedelta(days=self.days_between_refresh, hours=4) - datetime.now()

    def location(self) -> str:
        """Returns a Xur's location

        :return: str
        """
        page = requests.get(LOCATION_ROOT_PATH)
        json = page.json()
        return json['locationName']
