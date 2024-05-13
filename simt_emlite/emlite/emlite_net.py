import os
import socket

from tenacity import retry, stop_after_attempt

from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

socket_timeout: float = float(os.environ.get("EMLITE_TIMEOUT_SECONDS") or 20.0)

"""
    Class responsible for talking to meters via TCP/IP.

    This class has no knowledge of the structure of the bytes it's sending
    and receiving. Just manages raw communication of bytes.
"""


class EmliteNET:
    def __init__(self, host, port=8080):
        self.host = host
        self.port = int(port)
        global logger
        logger = logger.bind(host=host)

    @retry(stop=stop_after_attempt(3))
    def send_message(self, req_bytes: bytes):
        sock = self._open_socket()
        try:
            logger.info("sending", request_payload=req_bytes.hex())
            self._write_bytes(sock, req_bytes)
            rsp_bytes = self._read_bytes(sock, 128)
            logger.info("closing socket ...")
            sock.close()
        except socket.timeout as e:
            logger.warn("Timeout in send_message", host=self.host)
            logger.info("closing socket in timeout exception ...")
            sock.close()
            sock = None
            raise e
        except socket.error as e:
            logger.info("closing socket in socket.error ...")
            sock.close()
            sock = None
            raise e
        logger.info("received response", response_payload=rsp_bytes.hex())
        return rsp_bytes

    @retry(stop=stop_after_attempt(3))
    def _open_socket(self):
        logger.info("connecting", host=self.host)
        sock = socket.socket()
        sock.settimeout(socket_timeout)  # seconds
        try:
            sock.connect((self.host, self.port))
            logger.info("connected", host=self.host)
        except socket.timeout as e:
            logger.info("Timeout connecting to socket", host=self.host, error=e)
            sock.close()
            sock = None
            raise e
        except socket.error as e:
            if (e.__class__.__name__ == 'ConnectionRefusedError'):
                # The meter is likely not ready to accept the second of 2 requests
                # we can observe a lot of these if there is no wait time between
                # requests. we currently wait 2 seconds between them which avoids
                # a lot of these but sometimes they still occur.
                # 
                # NOTE: Care is taken here not to log the string 'error' so it 
                # doesn't appear in papertrail filters for errors. We tolerate these
                # and usual a retry succeeds.
                logger.warn("ConnectionRefused connecting to socket", host=self.host)
            else: 
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
