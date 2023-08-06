import socket
import logging

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

class EmliteNET:
    def __init__(self, host, port):
        self.host = host
        self.port = int(port)

    def send_message(self, req_bytes):
        sock = self._open_socket()
        try:
            logger.info("sending: [%s]", req_bytes.hex())
            self._write_bytes(sock, req_bytes)
            rsp_bytes = self._read_bytes(sock, 128)
            sock.close()
        except socket.error as e:
            sock.close()
            sock = None
            raise e
        logger.info("received: [%s]", rsp_bytes.hex())
        return rsp_bytes

    def _open_socket(self):
        logger.info("connecting to %s:%s", self.host, self.port)
        sock = socket.socket()
        try:
            sock.connect((self.host, self.port))
        except socket.error as e:
            logger.error("Error connecting to socket")
            sock.close()
            sock = None
            raise e
        return sock

    def _write_bytes(self, sock, data):
        try:
            sock.send(data)
        except socket.error as e:
            logger.error("Error writing to socket")
            raise e

    def _read_bytes(self, sock, num_bytes):
        try:
            return sock.recv(num_bytes)
        except socket.error as e:
            logger.error("Error reading from socket")
            raise e

