import datetime
from dataclasses import dataclass

@dataclass
class SMIPReading:
    serial: str
    register: int
    timestamp: datetime.datetime
    imp: float
    exp: float
    errorCode: int

    def __str__(self):
        return (f"SMIPReading ["
                f"serial={self.serial}, "
                f"register={self.register}, "
                f"timestamp={self.timestamp}, "
                f"import={self.imp}, "
                f"export={self.exp}, "
                f"errorCode={self.errorCode}]")
