from datetime import datetime

import crcmod.predefined
from kaitaistruct import BytesIO, KaitaiStream

from emlite_mediator.emlite.emlite_util import emop_u3be_encode
from emlite_mediator.util.logging import get_logger

from . import emlite_net
from .messages import emlite_data, emlite_frame
from .messages.emlite_object_id_enum import ObjectIdEnum

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
        data_field = emlite_data.EmliteData(
            len(req_data_field_bytes), KaitaiStream(BytesIO(req_data_field_bytes))
        )
        data_field._read()
        return self.send_message_with_data_instance(data_field)

    def send_message_with_data_instance(self, req_data_field: emlite_data.EmliteData):
        req_bytes: bytes = self._build_frame_bytes(req_data_field)
        rsp_bytes: bytes = self.net.send_message(req_bytes)

        frame = emlite_frame.EmliteFrame(KaitaiStream(BytesIO(rsp_bytes)))
        frame._read()
        logger.info("response frame parsed", frame=str(frame))

        self.last_request_datetime = datetime.now()

        return frame.data.payload

    def read_element(self, object_id: bytearray):
        data_field = self._build_data_field(object_id)
        payload_bytes = self.send_message_with_data_instance(data_field)
        return payload_bytes

    def write_element(self, object_id: ObjectIdEnum, payload: bytes):
        data_field = self._build_data_field(
            object_id,
            read_write_flag=emlite_data.EmliteData.ReadWriteFlags.write,
            payload=payload,
        )

        kt_stream = KaitaiStream(BytesIO(bytearray(data_field.len_data)))
        data_field._write(kt_stream)
        message_bytes = kt_stream.to_byte_array()

        self.send_message(message_bytes)

    def _build_data_field(
        self,
        object_id: bytearray,
        read_write_flag=emlite_data.EmliteData.ReadWriteFlags.read,
        payload=bytes(),
    ) -> emlite_data.EmliteData:
        data_field = emlite_data.EmliteData(5 + len(payload))
        data_field.format = b"\x01"
        data_field.object_id = object_id
        data_field.read_write = read_write_flag
        data_field.payload = payload
        return data_field

    def _build_frame_bytes(self, data_field) -> bytes:
        req_frame = emlite_frame.EmliteFrame()

        req_frame.frame_delimeter = b"\x7e"
        # TODO: use an incremented sequence number here (bits 0..2)
        req_frame.control = 5
        req_frame.destination_device_type = b"\x00"
        req_frame.destination_address = b"\x00\x00\x00"
        req_frame.source_device_type = b"\x00"
        # TODO: generate a random address here (not fixed):
        req_frame.source_address = emop_u3be_encode(2207298)

        req_frame.data = data_field

        # 17 for all fields NOT including the optional data field payload:
        req_frame.frame_length = 17 + len(data_field.payload)

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
