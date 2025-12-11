# group_config.py

from datetime import datetime, timedelta
from pathlib import Path

class GroupConfig:
    UTC = 'UTC'
    DATE_FORMAT = '%Y-%m-%d'

    def __init__(self, folder, prefix, devicetype, element, startdate, enddate, yearadjust, overwrite, host, port, test, raw_properties):
        self.folder = Path(folder)
        self.prefix = prefix
        self.devicetype = devicetype
        self.element = element
        self.startdate = startdate
        self.enddate = enddate
        self.yearadjust = yearadjust
        self.overwrite = overwrite
        self.host = host
        self.port = port
        self.test = test
        self.raw_properties = raw_properties

    @staticmethod
    def get_property_or_default(prop_name, group_name, group_props, default_props):
        prop_key = f"{group_name}.{prop_name}"
        return group_props.get(prop_key, default_props.get(prop_name))

    @staticmethod
    def get_instance_from_properties(group_name, props, default_props):
        prop_prefix = f"{group_name}."

        start_date_str = GroupConfig.get_property_or_default("startdate", group_name, props, default_props)
        if start_date_str:
            start_date = datetime.strptime(start_date_str, GroupConfig.DATE_FORMAT).date()
        else:
            start_days_str = default_props.get("startdays", "30")
            start_days = int(start_days_str)
            start_date = datetime.now().date() - timedelta(days=start_days)

        end_date_str = GroupConfig.get_property_or_default("enddate", group_name, props, default_props)
        end_date = datetime.strptime(end_date_str, GroupConfig.DATE_FORMAT).date() if end_date_str else datetime.now().date()

        year_adjust_str = props.get(f"{prop_prefix}yearadjust")
        year_adjust = int(year_adjust_str) if year_adjust_str else None

        test = props.get(f"{prop_prefix}test") == "yes"

        port_str = GroupConfig.get_property_or_default("port", group_name, props, default_props)
        device_type = GroupConfig.get_property_or_default("devicetype", group_name, props, default_props)
        prefix = GroupConfig.get_property_or_default("prefix", group_name, props, default_props)

        overwrite_str = GroupConfig.get_property_or_default("overwrite", group_name, props, default_props)
        overwrite = overwrite_str is not None and overwrite_str.lower() == "true"

        return GroupConfig(
            folder=props.get(f"{prop_prefix}folder"),
            prefix=prefix,
            devicetype=device_type,
            element=props.get(f"{prop_prefix}element"),
            startdate=start_date,
            enddate=end_date,
            yearadjust=year_adjust,
            overwrite=overwrite,
            host=props.get(f"{prop_prefix}host"),
            port=int(port_str) if port_str else 8080,
            test=test,
            raw_properties=props
        )

    def get_address(self):
        return (self.host, self.port)

    def __str__(self):
        return (f"GroupConfig [\n"
                f"  devicetype={self.devicetype}\n"
                f"  element={self.element}\n"
                f"  folder={self.folder}\n"
                f"  startdate={self.startdate}\n"
                f"  enddate={self.enddate}\n"
                f"  yearadjust={self.yearadjust}\n"
                f"  overwrite={self.overwrite}\n"
                f"  host={self.host}\n"
                f"  port={self.port}\n"
                f"  test={self.test}\n"
                f"  prefix={self.prefix}\n"
                f"]")