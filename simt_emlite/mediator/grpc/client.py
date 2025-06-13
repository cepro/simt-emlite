import base64
import os

from emop_frame_protocol.emop_message import EmopMessage
from emop_frame_protocol.emop_object_id_enum import ObjectIdEnum
from emop_frame_protocol.vendor.kaitaistruct import BytesIO, KaitaiStream

import grpc
from simt_emlite.mediator.grpc.exception.EmliteConnectionFailure import (
    EmliteConnectionFailure,
)
from simt_emlite.mediator.grpc.exception.EmliteEOFError import EmliteEOFError
from simt_emlite.util.config import load_config
from simt_emlite.util.logging import get_logger

from .generated.mediator_pb2 import (
    ReadElementRequest,
    SendRawMessageRequest,
    WriteElementRequest,
)
from .generated.mediator_pb2_grpc import EmliteMediatorServiceStub

logger = get_logger(__name__, __file__)

config = load_config()

client_cert_b64 = os.environ.get("MEDIATOR_CLIENT_CERT")
client_key_b64 = os.environ.get("MEDIATOR_CLIENT_KEY")
ca_cert_b64 = os.environ.get("MEDIATOR_CA_CERT")

have_certs = (
    client_cert_b64 is not None
    and client_key_b64 is not None
    and ca_cert_b64 is not None
)

# timeout considerations:
# 1) a successful call should take less than 5 seconds
# 2) emlite_net retries 3 times in case of timeouts, timeout is 10 seconds with
# a 1 second pause between each retry
# 3) grpc server queues requests and pauses for 4 seconds between each
TIMEOUT_SECONDS = 75


class EmliteMediatorGrpcClient:
    def __init__(
        self,
        mediator_address="0.0.0.0:50051",
        meter_id=None,
        use_cert_auth=False,
    ):
        if use_cert_auth and not have_certs:
            raise Exception("use_cert_auth set but certs not seend")

        self.mediator_address = mediator_address
        self.meter_id = meter_id if meter_id is not None else "unknown"
        self.use_cert_auth = use_cert_auth

        global logger
        self.log = logger.bind(mediator_address=mediator_address, meter_id=meter_id)

    def read_element(self, object_id: ObjectIdEnum):
        with self._get_channel() as channel:
            stub = EmliteMediatorServiceStub(channel)
            try:
                rsp_obj = stub.readElement(
                    ReadElementRequest(objectId=object_id.value),
                    timeout=TIMEOUT_SECONDS,
                )
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    self.log.warn(
                        "rpc timeout (deadline_exceeded)", object_id=object_id.name
                    )
                elif e.code() == grpc.StatusCode.INTERNAL:
                    if "EOFError" in e.details():
                        # TODO: need to fix these or retry - for now longer sleep between requests may resolve and we'll mark warn
                        self.log.warn(
                            "EOFError from meter - logging warn - so far only seen with back to back 3p voltage requests",
                            object_id=object_id.name,
                        )
                        raise EmliteEOFError(
                            f"object_id={object_id.name}, meter={self.meter_id}"
                        )
                    elif "failed to connect after retries" in e.details():
                        self.log.warn(e.details())
                        raise EmliteConnectionFailure(
                            f"object_id={object_id.name}, meter={self.meter_id}"
                        )
                    else:
                        raise e
                elif e.code() == grpc.StatusCode.UNAVAILABLE:
                    # we get a lot of these for instantaneous_voltage for reasons unknown
                    # they can be tolerated as we still get a number of successful calls as well
                    log_level: str = (
                        "warning"
                        if object_id == ObjectIdEnum.instantaneous_voltage
                        or object_id
                        == ObjectIdEnum.three_phase_instantaneous_voltage_l1
                        else "error"
                    )
                    getattr(self.log, log_level)(
                        "readElement failed",
                        details=e.details(),
                        code=e.code(),
                        object_id=object_id.name,
                    )
                else:
                    self.log.error(
                        "readElement failed",
                        details=e.details(),
                        code=e.code(),
                        object_id=object_id.name,
                    )
                raise e

        payload_bytes = rsp_obj.response
        self.log.debug(
            "read_element response received", response_payload=payload_bytes.hex()
        )

        emlite_rsp = EmopMessage(
            len(payload_bytes), object_id, KaitaiStream(BytesIO(payload_bytes))
        )
        emlite_rsp._read()
        return emlite_rsp.message

    def write_element(self, object_id: ObjectIdEnum, payload: bytes):
        with self._get_channel() as channel:
            stub = EmliteMediatorServiceStub(channel)
            try:
                stub.writeElement(
                    WriteElementRequest(objectId=object_id.value, payload=payload),
                    timeout=TIMEOUT_SECONDS,
                )
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    self.log.warn(
                        "rpc timeout (deadline_exceeded)", object_id=object_id.name
                    )
                elif e.code() == grpc.StatusCode.INTERNAL:
                    if "EOFError" in e.details():
                        # TODO: need to fix these or retry - for now longer sleep between requests may resolve and we'll mark warn
                        self.log.warn(
                            "EOFError from meter - logging warn - so far only seen with back to back 3p voltage requests",
                            object_id=object_id.name,
                        )
                        raise EmliteEOFError(
                            "object_id=" + object_id.name + ", meter=" + self.meter_id
                        )
                    elif "failed to connect after retries" in e.details():
                        self.log.warn(e.details())
                        raise EmliteConnectionFailure(
                            "object_id=" + object_id.name + ", meter=" + self.meter_id
                        )
                    else:
                        raise e
                else:
                    self.log.error(
                        "writeElement failed",
                        details=e.details(),
                        code=e.code(),
                        object_id=object_id.name,
                    )
                raise e

    def send_message(self, message: bytes):
        with self._get_channel() as channel:
            stub = EmliteMediatorServiceStub(channel)
            try:
                rsp_obj = stub.sendRawMessage(
                    SendRawMessageRequest(dataField=message),
                    timeout=TIMEOUT_SECONDS,
                )
            except grpc.RpcError as e:
                self.log.error("sendRawMessage", details=e.details(), code=e.code())
                raise e

        payload_bytes = rsp_obj.response
        self.log.info(
            "send_message response received", response_payload=payload_bytes.hex()
        )
        return payload_bytes

    def _get_channel(self):
        if self.use_cert_auth:
            credentials = self._channel_credentials()
            return grpc.secure_channel(
                self.mediator_address,
                credentials,
                options=(("grpc.ssl_target_name_override", "cepro-mediators"),),
            )
        else:
            return grpc.insecure_channel(self.mediator_address)

    def _channel_credentials(self):
        if client_cert_b64 is None or client_key_b64 is None or ca_cert_b64 is None:
            raise Exception("client credentials not provided")

        client_cert = self._decode_b64_secret_to_bytes(client_cert_b64)
        client_key = self._decode_b64_secret_to_bytes(client_key_b64)
        ca_cert = self._decode_b64_secret_to_bytes(ca_cert_b64)

        return grpc.ssl_channel_credentials(
            root_certificates=ca_cert,
            private_key=client_key,
            certificate_chain=client_cert,
        )

    def _decode_b64_secret_to_bytes(self, b64_secret: str) -> bytes:
        return (
            base64.b64decode(b64_secret)
            .decode("utf-8")
            .replace("\\n", "\n")
            .encode("utf-8")
        )
