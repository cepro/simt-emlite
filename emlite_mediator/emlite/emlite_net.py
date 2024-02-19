from emlite_mediator.util.logging import get_logger

import socket

from tenacity import retry, stop_after_attempt

logger = get_logger(__name__, __file__)


class EmliteNET:
    def __init__(self, host, port=8080):
        self.host = host
        self.port = int(port)
        global logger
        logger = logger.bind(host=host)

    @retry(stop=stop_after_attempt(3))
    def send_message(self, req_bytes):
        sock = self._open_socket()
        try:
            logger.info("sending", request_payload=req_bytes.hex())
            self._write_bytes(sock, req_bytes)
            rsp_bytes = self._read_bytes(sock, 128)
            sock.close()
        except socket.timeout as e:
            logger.warn("Timeout in send_message",
                        host=self.host)
            sock.close()
            sock = None
            raise e
        except socket.error as e:
            sock.close()
            sock = None
            raise e
        logger.info("received", response_payload=rsp_bytes.hex())
        return rsp_bytes

    @retry(stop=stop_after_attempt(3))
    def _open_socket(self):
        logger.info("connecting", host=self.host)
        sock = socket.socket()
        sock.settimeout(10.0)  # seconds
        try:
            sock.connect((self.host, self.port))
            logger.info("connected", host=self.host)
        except socket.timeout as e:
            logger.info("Timeout connecting to socket",
                        host=self.host, error=e)
            sock.close()
            sock = None
            raise e
        except socket.error as e:
            logger.warn("Error connecting to socket", host=self.host, error=e)
            sock.close()
            sock = None
            raise e
        return sock

    def _write_bytes(self, sock, data):
        try:
            sock.send(data)
        except socket.error as e:
            logger.error("Error writing to socket", error=e)
            raise e

    def _read_bytes(self, sock, num_bytes):
        try:
            return sock.recv(num_bytes)
        except socket.error as e:
            logger.warn("Error reading from socket", error=e)
            raise e
