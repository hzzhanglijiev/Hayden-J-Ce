from enum import Enum

DESTINY_TRACKER = "https://destinytracker.com/destiny-2/db/items/"


class Emoji(Enum):
    """Enumeration type mapping each DamageType to the appropriate Emoji
    """
    NONE = ''
    KINETIC = '<:kinetic:773719907371450379>'
    RAID = ''
    TITAN = '<:titan:773329359384608768>'
    HUNTER = '<:hunter:773329886244110346>'
    WARLOCK = '<:warlock:773329357627195402>'
    VOID = '<:void:773391417879298058>'
    SOLAR = '<:solar:773391417446891521>'
    ARC = '<:arc:773391417438765057>'
    STASIS = '<:Stasis:806983313490444358>'
    ULDREN_THUMBS_DOWN = '<:Uldren_Thumbs_Down:769642874593345586>'


def hyperlink(item: dict) -> str:
    """Creates hyperlink to the item's Destiny Tracker page

    :param item:
        The item you are trying to hyperlink in the form of inventory['Class']

    :return: str
    """
    link = "[" + item['name'] + "]"
    link = link + "(" + DESTINY_TRACKER + str(item['hash']) + ")"
    return link
