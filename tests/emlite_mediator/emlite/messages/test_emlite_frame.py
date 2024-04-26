import unittest

import crcmod.predefined
from kaitaistruct import BytesIO, KaitaiStream

from emlite_mediator.emlite.messages.emlite_data import EmliteData
from emlite_mediator.emlite.messages.emlite_frame import EmliteFrame

crc16 = crcmod.predefined.mkCrcFun("crc-ccitt-false")


class TestEmliteFrame(unittest.TestCase):
    def test_deserialise_response(self):
        frame_hex = "7E15C06F0093000018B0010100020100333032309DBD"
        frame_bytes = bytearray.fromhex(frame_hex)

        frame = EmliteFrame(KaitaiStream(BytesIO(frame_bytes)))
        frame._read()
        frame_len = len(frame_bytes) - 1

        self.assertEqual(frame.frame_delimeter, b"\x7e")
        self.assertEqual(frame.frame_length, frame_len)

        self.assertEqual(frame.destination_device_type, b"\xc0")
        self.assertEqual(frame.destination_address, b"o\x00\x93")
        self.assertEqual(frame.source_device_type, b"\x00")
        self.assertEqual(frame.source_address, b"\x00\x18\xb0")

        self.assertEqual(frame.seq_num, 1)
        self.assertEqual(frame.ack_nak_code, EmliteFrame.AckNakCodes.ok)

        len_data = frame_len - 12
        self.assertEqual(frame.len_data, len_data)

        data_field = frame.data
        self.assertEqual(data_field.len_data, len_data)
        self.assertEqual(data_field.format, EmliteData.RecordFormat.default)
        self.assertEqual(
            data_field.message.payload, frame_bytes[16 : len(frame_bytes) - 2]
        )

        self.assertEqual(frame.crc16, frame_bytes[-2:])

    def test_serialise_request_no_payload(self):
        req_frame = EmliteFrame()

        req_frame.frame_delimeter = b"\x7e"
        req_frame.control = 5
        req_frame.destination_device_type = b"\x00"
        req_frame.destination_address = b"\x00\x00\x00"
        req_frame.source_device_type = b"\x00"
        req_frame.source_address = int(2207298).to_bytes(3, byteorder="big")

        data_payload_len = 5
        message_field = EmliteData.DefaultRec(data_payload_len)
        message_field.object_id = b"\x60\x01\x00"  # get serial obj id
        message_field.read_write = EmliteData.ReadWriteFlags.read
        message_field.payload = bytes()

        data_field = EmliteData(data_payload_len)
        data_field.format = EmliteData.RecordFormat.default
        data_field.message = message_field

        req_frame.data = data_field

        # 17 for all simple reads on an obj id:
        req_frame.frame_length = 17

        # len of frame including delimeter
        frame_bytes_len = req_frame.frame_length + 1

        # Serialize once first to get bytes for checksum compute:
        req_frame.crc16 = b"\x00\x00"
        _io = KaitaiStream(BytesIO(bytearray(frame_bytes_len)))
        req_frame._write(_io)
        frame_bytes_zero_checksum = _io.to_byte_array()

        # add checksum
        req_frame.crc16 = crc16(
            frame_bytes_zero_checksum[1 : frame_bytes_len - 2]
        ).to_bytes(2)

        # compute final frame bytes
        _io = KaitaiStream(BytesIO(bytearray(frame_bytes_len)))
        req_frame._write(_io)
        frame_bytes = _io.to_byte_array()

        self.assertEqual(frame_bytes.hex(), "7e11000000000021ae42050160010000c02f")

    # def test_print_frame(self):
    #     # frame_hex = "7E2501FFFFFFC01234560101FFC8030137313436363339343632313538393136313032300830"
    #     frame_bytes = bytearray.fromhex(frame_hex)

    #     frame = EmliteFrame(KaitaiStream(BytesIO(frame_bytes)))
    #     frame._read()
    #     print(frame)
