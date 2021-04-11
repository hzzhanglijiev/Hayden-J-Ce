import requests

from constants import *


def manifest(entity_type: str, hash_identifier: int) -> dict:
    """ Manifests the specified entity. Returns general information about the entity, see API documentation for more details:
        https://bungie-net.github.io/#Destiny2.GetDestinyEntityDefinition

    :param entity_type: The type of entity for whom you would like results. These correspond to the entity's
        definition contract name. See constants.py/Definitions
    :param hash_identifier: The hash identifier for the specific Entity you want returned.
    :return: dict
    """
    api_call = requests.get(API_ROOT_PATH + "/Destiny2/Manifest/" + entity_type + "/" + str(hash_identifier),
                            headers=HEADERS)
    return (api_call.json())['Response']


def public_vendor(vendor_hash: str, components: int) -> dict:
    """Returns information on the requested vendor, see API documentation for more details:
        https://bungie-net.github.io/#Destiny2.GetPublicVendors

    :param vendor_hash: The hash identifier for the specific Vendor you want returned.
    :param components: See constants.py/Components
    :return: dict
    """
    api_call = requests.get(API_ROOT_PATH + '/Destiny2//Vendors/?components=' + str(components), headers=HEADERS)
    if components is Vendors:
        response = (api_call.json())['Response']['vendors']['data'][vendor_hash]
    elif components is VendorSales:
        response = (api_call.json())['Response']['sales']['data'][vendor_hash]
    elif components is VendorCategories:
        response = (api_call.json())['Response']['categories']['data'][vendor_hash]
    else:
        response = (api_call.json())['Response']
    return response


def search_entities(entity_type: str, search_term: str) -> dict:
    """Searches for the specified entity in the API, see API documentation for more details:
        https://bungie-net.github.io/#Destiny2.SearchDestinyEntities

    :param entity_type: The type of entity for whom you would like results. These correspond to the entity's
        definition contract name. See constants.py/Definitions
    :param search_term: The string to use when searching for Destiny entities.
    :return: dict
    """
    api_call = requests.get(API_ROOT_PATH + '/Destiny2/Armory/Search/' + entity_type + "/" + search_term + "/",
                            headers=HEADERS)
    return (api_call.json())['Response']
