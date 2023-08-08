import crcmod.predefined 
import logging

from kaitaistruct import KaitaiStream, BytesIO

from ..messages import emlite_data, emlite_frame 
from ..messages.emlite_object_id_enum import ObjectIdEnum

from . import emlite_net

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

crc16 = crcmod.predefined.mkCrcFun('crc-ccitt-false')

class EmliteAPI:
    def __init__(self, host, port):
        self.net = emlite_net.EmliteNET(host, port)

    def send_message(self, req_data_field_bytes):
        return self.send_message_from_bytes(req_data_field_bytes)
    
    def send_message_from_bytes(self, req_data_field_bytes):
        data_field = emlite_data.EmliteData(len(req_data_field_bytes), KaitaiStream(BytesIO(req_data_field_bytes)))
        data_field._read()
        return self.send_message_from_instance(data_field)

    def send_message_from_instance(self, req_data_field):
        req_bytes = self._build_frame(req_data_field)
        rsp_bytes = self.net.send_message(req_bytes)

        frame = emlite_frame.EmliteFrame(KaitaiStream(BytesIO(rsp_bytes)))
        frame._read()
        logger.info("frame: [%s]", frame)

        return frame.data.payload

    def read_element(self, object_id: ObjectIdEnum):
        return self.read_element_with_object_id_bytes((object_id.value).to_bytes(3, byteorder='big'))

    def read_element_with_object_id_bytes(self, object_id: bytearray):
        data_field = self._build_data_field(object_id)
        payload_bytes = self.send_message_from_instance(data_field)
        logger.info("payload: [%s]", payload_bytes.hex())
        return payload_bytes

    def _build_data_field(self, object_id: bytearray, read_write_flag = emlite_data.EmliteData.ReadWriteFlags.read, payload = bytes()):
        data_field = emlite_data.EmliteData(5 + len(payload))
        data_field.format = b'\x01'
        data_field.object_id = object_id
        data_field.read_write = read_write_flag
        data_field.payload = payload
        return data_field

    def _build_frame(self, data_field):
        req_frame = emlite_frame.EmliteFrame()
        
        req_frame.frame_delimeter = b'\x7e' 
        # TODO: use an incremented sequence number here (bits 0..2)
        req_frame.control = 5
        req_frame.destination_device_type = b'\x00'
        req_frame.destination_address = b'\x00\x00\x00'
        req_frame.source_device_type = b'\x00'
        # TODO: generate a random address here (not fixed):
        req_frame.source_address = int(2207298).to_bytes(3, byteorder='big')

        req_frame.data = data_field
        
        # 17 for all fields NOT including the optional data field payload:
        req_frame.frame_length = 17 + len(data_field.payload)

        # len of frame including delimeter
        frame_bytes_len = req_frame.frame_length + 1

        # Serialize once first to get bytes for checksum compute:
        req_frame.crc16 = b'\x00\x00'
        _io = KaitaiStream(BytesIO(bytearray(frame_bytes_len)))
        req_frame._write(_io)
        frame_bytes_zero_checksum = _io.to_byte_array()
        
        # add checksum
        req_frame.crc16 = crc16(frame_bytes_zero_checksum[1:frame_bytes_len-2]).to_bytes(2)
        
        # compute final frame bytes
        _io = KaitaiStream(BytesIO(bytearray(frame_bytes_len)))
        req_frame._write(_io)

        return _io.to_byte_array()

if __name__ == "__main__":
    host = '100.79.244.65'
    port = 8080 
    api = EmliteAPI(host, port)

    rsp_payload = api.read_element(ObjectIdEnum.serial)
    print(rsp_payload.decode('ascii'))    


