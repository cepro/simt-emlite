from typing import Optional
from datetime import datetime

class SMIPCSVRecord:
    """Represents a single record in the SMIP CSV format"""

    NA_VALUE = "NA"
    TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S%z"

    def __init__(self, timestamp: datetime, import_value: Optional[float], export_value: Optional[float]):
        self.timestamp = timestamp
        self.import_value = import_value
        self.export_value = export_value

    def to_csv_line(self) -> str:
        """Convert the record to a CSV line format"""
        timestamp_str = self.timestamp.strftime(self.TIMESTAMP_FORMAT)
        import_str = str(int(self.import_value)) if self.import_value is not None else self.NA_VALUE
        export_str = str(int(self.export_value)) if self.export_value is not None else self.NA_VALUE
        return f"{timestamp_str},{import_str},{export_str}"

    def __str__(self) -> str:
        """String representation of the record"""
        return f"timestamp={self.timestamp}, import_value={self.import_value}, export_value={self.export_value}"