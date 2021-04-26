from enum import Enum
from datetime import datetime, timedelta
import pytz
from api import manifest, public_vendor, requests
from constants import XUR_HASH, ITEM_DEF, LOCATION_ROOT_PATH, VendorSales, Vendors

cache = dict()

PST = pytz.timezone('US/Pacific')
EST = pytz.timezone('US/Eastern')
KEYS = ['name', 'type', 'hash', 'damageType']


class DamageType(Enum):
    """Enumeration type defining each Damage type as described in the Destiny API

    **Kinetic** = 1

    **Arc** = 2

    **Solar** = 3

    **Void** = 4

    """
    NONE = 0
    KINETIC = 1
    ARC = 2
    SOLAR = 3
    VOID = 4
    RAID = 5


class PlayerClass(Enum):
    """Enumeration type defining each player class as described in the Destiny API

    **Titan** = 0

    **Hunter** = 1

    **Warlock** = 2

    **Weapon** = 3

    """

    Titan = 0
    Hunter = 1
    Warlock = 2
    Weapon = 3


def items() -> dict:
    """Retrieve Xur's inventory

    :return: dict -
        {'class_type': {'name': 'item_name', 'type': 'item_type', 'hash': 'item_hash', 'damageType': 'damage_type'}}
    """
    inventory = {}
    xur_items = (public_vendor(XUR_HASH, VendorSales))['saleItems']
    for item, count in zip(xur_items,
                           range(4)):  # For each item he's selling, find it's name, type, hash and class type
        item_hash = xur_items[item]['itemHash']  # current item hash
        item_info = manifest(ITEM_DEF, item_hash)

        name = item_info['displayProperties']['name']  # current item name
        class_type = (PlayerClass(item_info['classType'])).name  # current item class
        item_type = item_info['itemTypeDisplayName']  # current item type
        damage_type = (DamageType(item_info['defaultDamageType'])).name  # current item damage type

        item_dict = dict(zip(KEYS, [name, item_type, item_hash, damage_type]))  # create dictionary for current item
        inventory[class_type] = item_dict  # set key 'class type' to current dictionary inside the inventory dictionary

    return inventory


def location() -> str:
    """Returns Xur's location

    :return: str
    """
    page = requests.get(LOCATION_ROOT_PATH)
    json = page.json()
    return json['locationName']


def leaving_datetime() -> [(timedelta, datetime), str]:
    """Returns Xur's leaving time and next refresh date, or empty string

    :return: (timedelta, datetime) or str
    """
    try:
        next_refresh_date = datetime.strptime(((public_vendor(XUR_HASH, Vendors))['nextRefreshDate']),
                                              '%Y-%m-%dT%H:%M:%SZ')
        bungie_time = PST.localize(next_refresh_date)
        eastern_time = bungie_time.astimezone(EST)
        time_until_return = eastern_time - datetime.now().astimezone(EST) - timedelta(3)
        return time_until_return, next_refresh_date
    except:
        return ''

