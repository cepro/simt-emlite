import socket
import logging

from ..messages import emlite_frame
from kaitaistruct import KaitaiStream, BytesIO

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

def open_socket(host, port):
    s = socket.socket()
    try:
        s.connect((host, port))
    except socket.error as e:
        logger.exception("Error connecting to socket")
        s.close()
        s = None
    return s

def write_bytes(s, data):
    try:
        s.send(data)
    except socket.error as e:
        logger.exception("Error writing to socket")

def read_bytes(s, num_bytes):
    try:
        return s.recv(num_bytes)
    except socket.error as e:
        logger.exception("Error reading from socket")
        return b''

def send_raw_message(host, port, req_bytes):
    logger.info("connecting to %s:%s", host, port)

    s = open_socket(host, port)
    if s is None:
        logger.error("No socket available")
        exit()

    logger.info("sending: [%s]", req_bytes.hex())
    write_bytes(s, req_bytes)
    rsp_bytes = read_bytes(s, 128)
    
    s.close()

    logger.info("received: [%s]", rsp_bytes.hex())

    frame = emlite_frame.EmliteFrame(KaitaiStream(BytesIO(rsp_bytes)))
    frame._read()

    logger.info("frame: [%s]", frame)

    return frame.data.payload 

if __name__ == "__main__":
    host = '100.79.244.65'
    port = 8080 
    get_serial_req_hex = '7E110000000080D1C2480001600100001C32'
    rsp_payload = send_raw_message(host, port, bytearray.fromhex(get_serial_req_hex))
    print(rsp_payload.decode('ascii'))    


