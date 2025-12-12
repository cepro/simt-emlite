# downloader_config.py

from collections import OrderedDict
from pathlib import Path

import javaproperties

from simt_emlite.profile_logs.group_config import GroupConfig


class ConfigException(Exception):
    pass


class DownloaderConfig:
    CONFIG_PROPERTIES_FILENAME_SUFFIX = "downloader"
    PROPERTY_ROOT_FOLDER = "rootfolder"
    PROPERTY_SLEEPSECONDS = "sleepseconds"
    PROPERTY_TESTMODE = "testmode"

    def __init__(self, properties: dict[str, str]):
        root_folder_str = properties.get(self.PROPERTY_ROOT_FOLDER)
        if not root_folder_str:
            raise ConfigException("no rootfolder property set - specify a rootfolder to download the files to")

        default_props = self.defaults_from_properties(properties)

        sleep_seconds_str = properties.get(self.PROPERTY_SLEEPSECONDS)
        if not sleep_seconds_str or sleep_seconds_str.strip() == "":
            print("sleepseconds not set - defaulting to 5 seconds")
            sleep_seconds_str = "5"

        test_mode_str = properties.get(self.PROPERTY_TESTMODE)

        self.root_folder = Path(root_folder_str)
        self.sleep_seconds = int(sleep_seconds_str)
        self.test_mode = test_mode_str == "yes"

        self.groups = self.groups_from_properties(properties, default_props)

    @staticmethod
    def get_instance(filename: str) -> "DownloaderConfig":
        with open(filename, 'r', encoding='utf-8') as f:
            properties = javaproperties.load(f)
        return DownloaderConfig(properties)

    def get_groups(self):
        return self.groups

    def get_root_folder(self):
        return self.root_folder

    def get_sleep_seconds(self):
        return self.sleep_seconds

    def get_test_mode(self):
        return self.test_mode

    @staticmethod
    def groups_from_properties(all_props, default_props):
        names = DownloaderConfig.group_names_from_properties(all_props)
        groups = OrderedDict()
        for name in names:
            groups[name] = GroupConfig.get_instance_from_properties(name, all_props, default_props)
        return groups

    @staticmethod
    def group_names_from_properties(all_props):
        return [k.replace(".folder", "") for k in all_props.keys() if k.endswith(".folder")]

    @staticmethod
    def defaults_from_properties(all_props):
        prefix = "default."
        default_props = {}
        for key in all_props.keys():
            if key.startswith(prefix):
                default_props[key.replace(prefix, "")] = all_props[key]
        return default_props
