from datetime import datetime, timedelta
import datetime as DT
import time
import dateutil.relativedelta as REL
import os
import discord
import pytz
import requests
from helpers import hyperlink, Emoji
from pybungie import BungieAPI, VendorHash, Definitions, Components, MembershipType, PlayerClass, DamageType

PST = pytz.timezone('US/Pacific')
EST = pytz.timezone('US/Eastern')
KEYS = ['name', 'type', 'hash', 'damageType']
LOCATION_ROOT_PATH = 'https://paracausal.science/xur/current.json'  # credit to to @nev_rtheless
bungie_api = BungieAPI(api_key=os.getenv("API_KEY"))
bungie_api.input_xbox_credentials(xbox_live_email=os.getenv("XBOX_LIVE_EMAIL"),
                                  xbox_live_password=os.getenv("XBOX_LIVE_PASSWORD"))
bungie_api.start_oauth2(client_id=os.getenv("CLIENT_ID"), client_secret=os.getenv("CLIENT_SECRET"))


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
        elif name == "ERIS":
            return RegularVendor(name="ERIS_MORN")
        else:
            return RegularVendor(name=name)


class RegularVendor:
    def __init__(self, name: str):
        """Standard class for non-Xur vendors in Destiny 2

        :param name: The name of the vendor you want to create
        """
        try:
            self.hash_id = (VendorHash[name])
        except KeyError:
            self.hash_id = next((vendor for vendor in VendorHash if name in vendor.name), None)
            if self.hash_id is None or self.hash_id is VendorHash.TESS_EVERIS:
                raise RuntimeError

        displayProperties = bungie_api.manifest((Definitions['VENDOR']).value, self.hash_id.value)[
            'displayProperties']
        self.name = displayProperties['name']
        self.subtitle = displayProperties['subtitle']
        self.description = displayProperties['description']
        self.icon = displayProperties['smallTransparentIcon']

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
        weekly_bounties, daily_bounties = self.items()
        embed = self.create_embed_title()
        embed.clear_fields()
        embed.set_thumbnail(url='https://www.bungie.net/' + self.icon)
        if weekly_bounties:  # if any weekly bounties exist
            for bounty in weekly_bounties:
                embed.add_field(name=f'**{bounty["name"]}**', value=bounty['description'], inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="\u200b", value="\nWeekly Bounty\n", inline=True)
        if daily_bounties:  # if any daily bounties exist
            for bounty in daily_bounties:
                embed.add_field(name=f'**{bounty["name"]}**', value=bounty['description'], inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="\u200b", value="\nDaily Bounty\n", inline=True)
        if not daily_bounties and not weekly_bounties:
            raise RuntimeError
        return embed

    def items(self):
        daily_bounties = []
        weekly_bounties = []
        vendor = bungie_api.get_vendor(membership_type=MembershipType.STEAM, membership_id=4611686018475645094,
                                       character_id=2305843009349174049, vendor_hash=self.hash_id,
                                       components=Components.VendorSales)
        items = vendor['sales']['data']
        items = list(items.values())
        for item in items:
            hash_id = item['itemHash']
            bounty = bungie_api.manifest((Definitions['ITEM']).value, hash_id)
            bounty_type = bounty['itemTypeDisplayName']
            displayProperties = bounty['displayProperties']
            bounty_dict = {
                'name': displayProperties['name'],
                'description': displayProperties['description']
            }
            if bounty_type == "Daily Bounty" or bounty_type == "Daily Trials Bounty":
                daily_bounties.append(bounty_dict)
            if bounty_type == "Weekly Bounty" or bounty_type == "Weekly Trials Bounty":
                weekly_bounties.append(bounty_dict)
        return weekly_bounties, daily_bounties


class Xur(RegularVendor):
    def __init__(self, name: str):
        super().__init__(name)
        self.embedded = False
        self.cache_check = None
        self.cached_message = None

    def message(self):
        """Creates an Embed that contains Xur's inventory, or a generic response if Xur is not available

        :return: string or discord.Embed
        """
        leaving_time, next_refresh = self.leaving_datetime()

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
        except:
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
        for item, count in zip(my_items,
                               range(4)):  # For each item they're selling, find it's name, type, hash and class type
            item_hash = my_items[item]['itemHash']  # current item hash
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
                'damageType': damage_type
            }

            inventory[
                class_type] = item_dict  # set key 'class type' to current dictionary inside the inventory dictionary
        return inventory

    def location(self) -> str:
        """Returns a Xur's location

        :return: str
        """
        page = requests.get(LOCATION_ROOT_PATH)
        json = page.json()
        return json['locationName']

    def leaving_datetime(self) -> [(timedelta, datetime), str]:
        """Returns Xur's leaving time and next refresh date, or empty string

        :return: (timedelta, datetime) or str
        """
        try:
            next_refresh_date = datetime.strptime(
                (bungie_api.get_public_vendors(components=Components.Vendors)['vendors']['data'][
                    str(self.hash_id.value)]['nextRefreshDate']),
                '%Y-%m-%dT%H:%M:%SZ')
            bungie_time = PST.localize(next_refresh_date)
            eastern_time = bungie_time.astimezone(EST)
            time_until_return = eastern_time - datetime.now().astimezone(EST) - timedelta(3)
            return time_until_return, next_refresh_date
        except:
            return ''