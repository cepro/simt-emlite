import unittest

from emlite_mediator.emlite.messages.emlite_data import EmliteData
from kaitaistruct import KaitaiStream, BytesIO

class TestEmliteDataField(unittest.TestCase):
    def test_deserialise(self):
        # 7E15C06F0093000018B0010100020100333032309DBD
        data_hex = "010002010033303230"
        data_bytes = bytearray.fromhex(data_hex)
        
        data = EmliteData(len(data_bytes), KaitaiStream(BytesIO(data_bytes)))
        data._read()

        self.assertEqual(data.len_data, len(data_bytes))
        self.assertEqual(data.read_write, EmliteData.ReadWriteFlags.read)
        self.assertEqual(data.format, b'\x01')
        self.assertEqual(data.object_id, b'\x00\x02\x01')
        self.assertEqual(data.payload, data_bytes[5:])

    def test_serialise(self):
        field_len = 8

        data_field = EmliteData(field_len)
        data_field.format = b'\x01'
        data_field.object_id = b'\x60\x01\x00' # get serial obj id
        data_field.read_write = EmliteData.ReadWriteFlags.read
        data_field.payload = b'\xff\x00\xaa'   # some arbitrary payload

        _io = KaitaiStream(BytesIO(bytearray(field_len)))
        data_field._write(_io)
        data_field_bytes = _io.to_byte_array()

        self.assertEqual(data_field_bytes.hex(), '0160010000ff00aa')

