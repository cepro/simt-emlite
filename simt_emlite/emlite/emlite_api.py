from datetime import datetime

import crcmod.predefined
from emop_frame_protocol.emop_data import EmopData
from emop_frame_protocol.emop_frame import EmopFrame
from emop_frame_protocol.emop_object_id_enum import ObjectIdEnum
from emop_frame_protocol.util import emop_encode_u3be
from emop_frame_protocol.vendor.kaitaistruct import BytesIO, KaitaiStream

from simt_emlite.util.logging import get_logger

from . import emlite_net

logger = get_logger(__name__, __file__)

crc16 = crcmod.predefined.mkCrcFun("crc-ccitt-false")


"""
    This class sends bytes to the meters using the EmliteNet module.
    
    Bytes are packed and unpacked, to and from EMOP frames and EMOP data
    fields.
    
    While this class is responsible for building the frames and data fields it
    has no knowledge of the structure of the payload embedded in the data
    field. Caller should build those payloads and pass them into this API.
"""


class EmliteAPI:
    def __init__(self, host, port=8080):
        self.net = emlite_net.EmliteNET(host, port)
        self.last_request_datetime = None
        global logger
        logger.bind(host=host)

    def send_message(self, req_data_field_bytes: bytes):
        data_field = EmopData(
            len(req_data_field_bytes), KaitaiStream(BytesIO(req_data_field_bytes))
        )
        data_field._read()
        return self.send_message_with_data_instance(data_field)

    def send_message_with_data_instance(self, req_data_field: EmopData):
        req_bytes: bytes = self._build_frame_bytes(req_data_field)
        rsp_bytes: bytes = self.net.send_message(req_bytes)

        frame = EmopFrame(KaitaiStream(BytesIO(rsp_bytes)))
        frame._read()
        logger.info("response frame parsed", frame=str(frame))

        self.last_request_datetime = datetime.now()

        data_field = frame.data

        if data_field.format in [
            EmopData.RecordFormat.default,
            EmopData.RecordFormat.event_log,
        ]:
            return frame.data.message.payload
        else:
            # assume profile log message - no others handled as yet
            return frame.data.message.response_payload

    def read_element(self, object_id: bytearray):
        data_field = self._build_data_field(object_id)
        payload_bytes = self.send_message_with_data_instance(data_field)
        return payload_bytes

    def write_element(self, object_id: ObjectIdEnum, payload: bytes):
        data_field = self._build_data_field(
            object_id,
            read_write_flag=EmopData.ReadWriteFlags.write,
            payload=payload,
        )

        kt_stream = KaitaiStream(BytesIO(bytearray(data_field.len_data)))
        data_field._write(kt_stream)
        message_bytes = kt_stream.to_byte_array()

        self.send_message(message_bytes)

    def _build_data_field(
        self,
        object_id: bytearray,
        read_write_flag=EmopData.ReadWriteFlags.read,
        payload=bytes(),
    ) -> EmopData:
        len_data = len(payload)

        message_field = EmopData.DefaultRec(len_data)
        message_field.object_id = object_id
        message_field.read_write = read_write_flag
        message_field.payload = payload

        data_field = EmopData(5 + len(payload))
        data_field.format = EmopData.RecordFormat.default
        data_field.message = message_field

        return data_field

    def _build_frame_bytes(self, data_field) -> bytes:
        req_frame = EmopFrame()

        req_frame.frame_delimeter = b"\x7e"
        # TODO: use an incremented sequence number here (bits 0..2)
        req_frame.control = 5
        req_frame.destination_device_type = b"\x00"
        req_frame.destination_address = b"\x00\x00\x00"
        req_frame.source_device_type = b"\x00"
        # TODO: generate a random address here (not fixed):
        req_frame.source_address = emop_encode_u3be(2207298)

        req_frame.data = data_field

        # frame length is "The Length is the total length of the message in
        # bytes excluding the Frame Delimiter."
        #
        # which is 12 bytes (length 1, control 1, destination 4, source 4, crc 2)
        #   plus data field length which depends on format and payload
        frame_length = 12

        if data_field.format == EmopData.RecordFormat.default:
            # 5 (format 1, object id 3, rw flag 1) plus payload length
            frame_length = frame_length + 5 + len(data_field.message.payload)
        elif data_field.format == EmopData.RecordFormat.event_log:
            # 5 (format 1, object id 3, rw flag 1)
            frame_length = frame_length + 5
        else:
            # assume profile log message - no others handled as yet
            # 5 (format 1, timestamp 4)
            is_request = not hasattr(data_field.message, "response_payload")
            frame_length += 5 + (
                0 if is_request else len(data_field.message.response_payload)
            )

        req_frame.frame_length = frame_length

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

        return _io.to_byte_array()
