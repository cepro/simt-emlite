from datetime import datetime, timedelta
from decimal import Decimal

from kaitaistruct import BytesIO, KaitaiStream

from emlite_mediator.emlite.messages.emlite_message import EmliteMessage
from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum

epoch2000 = datetime(2000, 1, 1, 0, 0, 0)
priceAmountScaleFactor = Decimal(100_000)


def emop_datetime_to_epoch_seconds(ts: datetime) -> int:
    time_diff = ts - epoch2000
    return int(time_diff.total_seconds())


def emop_epoch_seconds_to_datetime(seconds: int) -> datetime:
    return epoch2000 + timedelta(seconds=seconds)


def emop_scale_price_amount(amount: Decimal) -> Decimal:
    return amount / priceAmountScaleFactor


def emop_upscale_price_amount(amount: Decimal) -> Decimal:
    return amount * priceAmountScaleFactor


def emop_encode_object_id(object_id: ObjectIdEnum) -> bytes:
    return emop_encode_u3be(object_id.value)


def emop_encode_u3be(value: int) -> bytes:
    return value.to_bytes(3, byteorder="big")


def emop_encode_timestamp_as_u4le_rec(ts: datetime) -> bytes:
    return emop_encode_u4le_rec(emop_datetime_to_epoch_seconds(ts))


def emop_encode_amount_as_u4le_rec(amount: Decimal) -> bytes:
    return emop_encode_u4le_rec(int(emop_upscale_price_amount(amount)))


def emop_encode_u4le_rec(value: int) -> bytes:
    _io = KaitaiStream(BytesIO(bytearray(4)))

    rec = EmliteMessage.U4leValueRec()
    rec.value = value
    rec._write(_io)

    return _io.to_byte_array()
