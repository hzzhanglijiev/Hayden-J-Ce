from pybungie import VendorHash
from collections import defaultdict
import bisect
from Vendor import Vendor


class VendorDictionary:
    def __init__(self):
        vendor_dict = {}
        for vendor in VendorHash:
            vendor_dict[vendor.name.replace('_', ' ')] = Vendor(name=vendor.name)

        self.prefixes = defaultdict(dict)
        self.suffixes = {}
        self.full_vendor_dict = {}
        for key in vendor_dict:
            if len(key.split()) == 2:
                prefix, suffix = key.split()
                self.suffixes[suffix] = vendor_dict[key]
                self.prefixes[prefix].update({suffix: vendor_dict[key]})
                self.prefixes[prefix] = dict(sorted(self.prefixes[prefix].items()))
            else:
                for token in key.split():
                    self.full_vendor_dict[token] = vendor_dict[key]

        self.suffixes = dict(sorted(self.suffixes.items()))
        self.prefixes = dict(sorted(self.prefixes.items()))
        self.full_vendor_dict = dict(sorted(self.full_vendor_dict.items()))

    def search(self, name: str):
        name = name.upper()
        try:
            if ' ' in name:
                prefix, suffix = name.split()
                return self.__check_prefix(prefix=prefix, suffix=suffix)
            else:
                return self.__check_suffix(suffix=name)
        except KeyError:
            return self.__check_full_vendor_dict(name=name)

    def __check_prefix(self, prefix: str, suffix: str):
        prefix = self.__binary_search(key=prefix, dictionary=self.prefixes)
        if prefix is not None:
            for value in self.prefixes[prefix].keys():
                if suffix in value:
                    return self.prefixes[prefix][suffix]
        return None

    def __check_suffix(self, suffix: str):
        return self.suffixes[self.__binary_search(key=suffix, dictionary=self.suffixes)]

    def __binary_search(self, key: str, dictionary: dict):
        keys = list(dictionary.keys())
        left_index = bisect.bisect_left(keys, key)
        right_index = bisect.bisect_right(keys, key)
        if left_index == right_index:
            if left_index > len(keys) or keys[left_index] is not key:
                return None
            else:
                return keys[left_index]
        else:
            return next(key for key in keys[left_index:right_index])

    def __check_full_vendor_dict(self, name: str):
        key = self.__binary_search(key=name, dictionary=self.full_vendor_dict)
        if key is not None:
            return self.full_vendor_dict[key]