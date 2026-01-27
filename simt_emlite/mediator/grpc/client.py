# mypy: disable-error-code="import-untyped"

import os
from typing import Any

from emop_frame_protocol.emop_message import EmopMessage
from emop_frame_protocol.emop_object_id_enum import ObjectIdEnum
from emop_frame_protocol.vendor.kaitaistruct import BytesIO, KaitaiStream

import grpc
from simt_emlite.mediator.grpc.exception.EmliteConnectionFailure import (
    EmliteConnectionFailure,
)
from simt_emlite.mediator.grpc.exception.EmliteEOFError import EmliteEOFError
from simt_emlite.util.logging import get_logger

from .generated.mediator_pb2 import (
    GetInfoRequest,
    GetMetersRequest,
    ReadElementRequest,
    SendRawMessageRequest,
    WriteElementRequest,
)
from .generated.mediator_pb2_grpc import EmliteMediatorServiceStub, InfoServiceStub
from .util import decode_b64_secret_to_bytes

logger = get_logger(__name__, __file__)


# timeout considerations:
# 1) a successful call should take less than 5 seconds
# 2) emlite_net retries 3 times in case of timeouts, timeout is 10 seconds with
# a 1 second pause between each retry
# 3) grpc server queues requests and pauses for 4 seconds between each
TIMEOUT_SECONDS = 75


class EmliteMediatorGrpcClient:
    def __init__(
        self,
        mediator_address: str | None = "0.0.0.0:50051",
    ) -> None:
        self.client_cert_b64 = os.environ.get("MEDIATOR_CLIENT_CERT")
        self.client_key_b64 = os.environ.get("MEDIATOR_CLIENT_KEY")
        self.ca_cert_b64 = os.environ.get("MEDIATOR_CA_CERT")

        self.have_certs = (
            self.client_cert_b64 is not None
            and self.client_key_b64 is not None
            and self.ca_cert_b64 is not None
        )

        self.mediator_address = mediator_address or "0.0.0.0:50051"

        global logger
        self.log = logger.bind(mediator_address=self.mediator_address)
        self.log.debug(
            "init complete",
            mediator_address=self.mediator_address,
            have_certs=self.have_certs,
        )

    def read_element(self, serial: str, object_id: ObjectIdEnum | int) -> Any:
        obis = self._object_id_int(object_id)
        obis_name = (
            object_id.name if isinstance(object_id, ObjectIdEnum) else hex(object_id)
        )
        with self._get_channel() as channel:
            stub = EmliteMediatorServiceStub(channel)  # type: ignore[no-untyped-call]
            try:
                self.log.debug(
                    f"send request - reading element [{obis_name}]", meter_id=serial
                )
                rsp_obj = stub.readElement(
                    ReadElementRequest(serial=serial, objectId=obis),
                    timeout=TIMEOUT_SECONDS,
                )
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    self.log.warn(
                        "rpc timeout (deadline_exceeded)",
                        object_id=obis_name,
                        meter_id=serial,
                    )
                elif e.code() == grpc.StatusCode.INTERNAL:
                    details = str(e.details() or "")
                    if "EOFError" in details:
                        self.log.warn(
                            "EOFError from meter",
                            object_id=obis_name,
                            meter_id=serial,
                        )
                        raise EmliteEOFError(f"object_id={obis_name}, meter={serial}")
                    elif "failed to connect after retries" in details:
                        self.log.warn(e.details(), meter_id=serial)
                        raise EmliteConnectionFailure(
                            f"object_id={obis_name}, meter={serial}"
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
                        object_id=obis_name,
                        meter_id=serial,
                    )
                else:
                    self.log.error(
                        "readElement failed",
                        details=e.details(),
                        code=e.code(),
                        object_id=obis_name,
                        meter_id=serial,
                    )
                raise e

        payload_bytes = rsp_obj.response
        self.log.debug(
            "read_element response received",
            response_payload=payload_bytes.hex(),
            meter_id=serial,
        )

        emlite_rsp = EmopMessage(
            len(payload_bytes), object_id, KaitaiStream(BytesIO(payload_bytes))
        )
        emlite_rsp._read()
        return emlite_rsp.message

    def write_element(
        self, serial: str, object_id: ObjectIdEnum | int, payload: bytes
    ) -> None:
        obis = self._object_id_int(object_id)
        obis_name = (
            object_id.name if isinstance(object_id, ObjectIdEnum) else hex(object_id)
        )
        with self._get_channel() as channel:
            stub = EmliteMediatorServiceStub(channel)  # type: ignore[no-untyped-call]
            try:
                self.log.debug(
                    f"send request - write element [{obis_name}]", meter_id=serial
                )
                stub.writeElement(
                    WriteElementRequest(serial=serial, objectId=obis, payload=payload),
                    timeout=TIMEOUT_SECONDS,
                )
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    self.log.warn(
                        "rpc timeout (deadline_exceeded)",
                        object_id=obis_name,
                        meter_id=serial,
                    )
                elif e.code() == grpc.StatusCode.INTERNAL:
                    details = str(e.details() or "")
                    if "EOFError" in details:
                        self.log.warn(
                            "EOFError from meter",
                            object_id=obis_name,
                            meter_id=serial,
                        )
                        raise EmliteEOFError(
                            "object_id=" + obis_name + ", meter=" + serial
                        )
                    elif "failed to connect after retries" in details:
                        self.log.warn(e.details(), meter_id=serial)
                        raise EmliteConnectionFailure(
                            "object_id=" + obis_name + ", meter=" + serial
                        )
                    else:
                        raise e
                else:
                    self.log.error(
                        "writeElement failed",
                        details=e.details(),
                        code=e.code(),
                        object_id=obis_name,
                        meter_id=serial,
                    )
                raise e

    def send_message(self, serial: str, message: bytes) -> bytes:
        with self._get_channel() as channel:
            stub = EmliteMediatorServiceStub(channel)  # type: ignore[no-untyped-call]
            try:
                self.log.debug("send request - message", meter_id=serial)
                rsp_obj = stub.sendRawMessage(
                    SendRawMessageRequest(serial=serial, dataField=message),
                    timeout=TIMEOUT_SECONDS,
                )
            except grpc.RpcError as e:
                if (
                    e.code() == grpc.StatusCode.INTERNAL
                    and "failed to connect after retries" in (e.details() or "")
                ):
                    self.log.warn(e.details(), meter_id=serial)
                    raise EmliteConnectionFailure(f"meter={serial}")
                self.log.error(
                    "sendRawMessage",
                    details=e.details(),
                    code=e.code(),
                    meter_id=serial,
                )
                raise e

        payload_bytes: bytes = rsp_obj.response
        self.log.debug(
            "send_message response received",
            response_payload=payload_bytes.hex(),
            meter_id=serial,
        )
        return payload_bytes

    def get_info(self, serial: str) -> str:
        with self._get_channel() as channel:
            stub = InfoServiceStub(channel)
            try:
                self.log.debug("send request - get_info", meter_id=serial)
                rsp_obj = stub.GetInfo(
                    GetInfoRequest(serial=serial), timeout=TIMEOUT_SECONDS
                )
                return rsp_obj.json_data
            except grpc.RpcError as e:
                # Tolerate NOT_FOUND by returning empty string or raising specific exception?
                # User didn't specify, but `info_service.py` logs and aborts with NOT_FOUND.
                # raising e allows caller to handle.
                self.log.error(
                    "GetInfo failed",
                    details=e.details(),
                    code=e.code(),
                    meter_id=serial,
                )
                raise e

    def get_meters(self, esco: str | None = None) -> str:
        with self._get_channel() as channel:
            stub = InfoServiceStub(channel)
            try:
                self.log.debug("send request - get_meters", esco=esco)
                rsp_obj = stub.GetMeters(
                    GetMetersRequest(esco=esco), timeout=TIMEOUT_SECONDS
                )
                return rsp_obj.json_meters
            except grpc.RpcError as e:
                self.log.error("GetMeters failed", details=e.details(), code=e.code())
                raise e

    def _get_channel(self) -> grpc.Channel:
        if self.mediator_address is None:
            raise ValueError("mediator_address cannot be none")

        if self.have_certs:
            credentials = self._channel_credentials()
            return grpc.secure_channel(
                self.mediator_address,
                credentials,
                options=(("grpc.ssl_target_name_override", "cepro-mediators"),),
            )
        else:
            return grpc.insecure_channel(self.mediator_address)

    def _channel_credentials(self) -> grpc.ChannelCredentials:
        if not self.have_certs:
            raise Exception("client credentials not provided")

        client_cert = decode_b64_secret_to_bytes(self.client_cert_b64)
        client_key = decode_b64_secret_to_bytes(self.client_key_b64)
        ca_cert = decode_b64_secret_to_bytes(self.ca_cert_b64)

        return grpc.ssl_channel_credentials(
            root_certificates=ca_cert,
            private_key=client_key,
            certificate_chain=client_cert,
        )

    def _object_id_int(self, obj_id: ObjectIdEnum | int) -> int:
        return obj_id.value if isinstance(obj_id, ObjectIdEnum) else obj_id
