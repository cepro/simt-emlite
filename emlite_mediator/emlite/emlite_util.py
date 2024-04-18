from datetime import datetime, timedelta

from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum

epoch2000 = datetime(2000, 1, 1, 0, 0, 0)


def emop_timestamp_encode(ts: datetime) -> float:
    time_diff = ts - epoch2000
    return time_diff.total_seconds()


def emop_timestamp_decode(seconds: float) -> datetime:
    return epoch2000 + timedelta(seconds=seconds)


def emop_object_id_encode(object_id: ObjectIdEnum) -> bytes:
    return emop_u3be_encode(object_id.value)


def emop_u3be_encode(value: int) -> bytes:
    return value.to_bytes(3, byteorder="big")
