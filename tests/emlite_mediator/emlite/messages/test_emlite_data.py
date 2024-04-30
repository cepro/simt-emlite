import unittest
from datetime import datetime

from kaitaistruct import BytesIO, KaitaiStream

from emlite_mediator.emlite.emlite_util import (
    emop_datetime_to_epoch_seconds,
    emop_epoch_seconds_to_datetime,
)
from emlite_mediator.emlite.messages.emlite_data import EmliteData

PROFILE_LOG_1_RESPONSE_HEX = (
    # format byte - profile log 1
    "03"
    +
    # timestamp
    "0008bb2d"
    +
    # 80 byte profile log response data
    "60d0b02d0100f00600004507000068d7b02d0080f00600004507000070deb02d0080f00600004507000078e5b02d0080f00600004507000080ecb02d0080f00600004507000034000000000000000000"
)

PROFILE_LOG_1_RESPONSE_DATETIME = datetime(2024, 4, 24, 0, 0, 0)


class TestEmliteDataField(unittest.TestCase):
    def test_deserialise_format_default(self):
        # 7E15C06F0093000018B0010100020100333032309DBD
        data_hex = "010002010033303230"
        data_bytes = bytearray.fromhex(data_hex)

        data = EmliteData(len(data_bytes), KaitaiStream(BytesIO(data_bytes)))
        data._read()

        self.assertEqual(data.len_data, len(data_bytes))
        self.assertEqual(data.format, EmliteData.RecordFormat.default)
        self.assertEqual(data.message.object_id, b"\x00\x02\x01")
        self.assertEqual(data.message.read_write, EmliteData.ReadWriteFlags.read)
        self.assertEqual(data.message.payload, data_bytes[5:])

    def test_serialise_format_default(self):
        field_len = 8

        message_field = EmliteData.DefaultRec(field_len)
        message_field.object_id = b"\x60\x01\x00"  # get serial obj id
        message_field.read_write = EmliteData.ReadWriteFlags.read
        message_field.payload = b"\xff\x00\xaa"  # some arbitrary payload

        data_field = EmliteData(field_len)
        data_field.format = EmliteData.RecordFormat.default
        data_field.message = message_field

        _io = KaitaiStream(BytesIO(bytearray(field_len)))
        data_field._write(_io)
        data_field_bytes = _io.to_byte_array()

        self.assertEqual(data_field_bytes.hex(), "0160010000ff00aa")

    def test_deserialise_format_profile_log(self):
        data_bytes = bytearray.fromhex(PROFILE_LOG_1_RESPONSE_HEX)
        data = EmliteData(len(data_bytes), KaitaiStream(BytesIO(data_bytes)))
        data._read()

        self.assertEqual(data.len_data, len(data_bytes))
        self.assertEqual(data.format, EmliteData.RecordFormat.profile_log_1)
        self.assertEqual(
            emop_epoch_seconds_to_datetime(data.message.timestamp),
            PROFILE_LOG_1_RESPONSE_DATETIME,
        )
        self.assertEqual(data.message.response_payload, data_bytes[5:])

    def test_serialise_format_profile_log(self):
        field_len = 85

        message_field = EmliteData.ProfileLogRec(field_len)
        message_field.timestamp = emop_datetime_to_epoch_seconds(
            PROFILE_LOG_1_RESPONSE_DATETIME
        )
        message_field.response_payload = bytes.fromhex(PROFILE_LOG_1_RESPONSE_HEX)[5:]

        data_field = EmliteData(field_len)
        data_field.format = EmliteData.RecordFormat.profile_log_1
        data_field.message = message_field

        _io = KaitaiStream(BytesIO(bytearray(field_len)))
        data_field._write(_io)
        data_field_bytes = _io.to_byte_array()

        self.assertEqual(data_field_bytes.hex(), PROFILE_LOG_1_RESPONSE_HEX)
