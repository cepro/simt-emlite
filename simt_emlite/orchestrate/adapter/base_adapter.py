import os
from abc import ABC, abstractmethod
from typing import Dict, List

from simt_emlite.orchestrate.adapter.container import Container, ContainerState


class BaseAdapter(ABC):
    def __init__(self) -> None:
        pass

    def get(
        self,
        meter_id: str,
    ) -> Container | None:
        meters = self.list(("meter_id", meter_id))
        return meters[0] if len(meters) != 0 else None

    @abstractmethod
    def list(
        self,
        metadata_filter: tuple[str, str] | None = None,
        status_filter: ContainerState | None = None,
    ) -> List[Container]:
        pass

    @abstractmethod
    def create(
        self,
        cmd: str,
        meter_id: str,
        serial: str,
        ip_address: str,
        port: int | None = None,
        additional_internal_port: int | None = None,
        skip_confirm=False,
        use_cert_auth=False,
    ) -> str:
        pass

    @abstractmethod
    def start(self, id: str) -> None:
        pass

    @abstractmethod
    def stop(self, id: str) -> None:
        pass

    @abstractmethod
    def destroy(self, id: str, force: bool) -> None:
        pass

    @abstractmethod
    def mediator_address(self, meter_id: str, serial: str) -> str | None:
        pass

    def _env_vars(
        self, ip_address: str, use_cert_auth: bool
    ) -> Dict[str, str | int | None]:
        MEDIATOR_INACTIVITY_SECONDS = os.environ.get("MEDIATOR_INACTIVITY_SECONDS")

        env_vars: Dict[str, str | int | None] = {
            "EMLITE_HOST": ip_address,
            "MEDIATOR_INACTIVITY_SECONDS": MEDIATOR_INACTIVITY_SECONDS,
        }

        socks_dict: Dict | None = self._socks_dict()
        if socks_dict is not None:
            env_vars.update(socks_dict)

        if use_cert_auth:
            certs_dict: Dict = self._certificates_dict()
            if certs_dict is not None:
                env_vars.update(certs_dict)

        return env_vars

    def _socks_dict(self) -> Dict[str, str | None] | None:
        SOCKS_HOST = os.environ.get("SOCKS_HOST")
        SOCKS_PORT = os.environ.get("SOCKS_PORT")
        SOCKS_USERNAME = os.environ.get("SOCKS_USERNAME")
        SOCKS_PASSWORD = os.environ.get("SOCKS_PASSWORD")

        socks_dict: Dict[str, str | None] = {
            "SOCKS_HOST": SOCKS_HOST,
            "SOCKS_PORT": SOCKS_PORT,
            "SOCKS_USERNAME": SOCKS_USERNAME,
            "SOCKS_PASSWORD": SOCKS_PASSWORD,
        }

        use_socks = all(
            socks_dict[f"SOCKS_{v}"] is not None
            for v in [
                "HOST",
                "PORT",
                "USERNAME",
                "PASSWORD",
            ]
        )

        return socks_dict if use_socks is True else None

    def _certificates_dict(self) -> Dict:
        MEDIATOR_SERVER_CERT = os.environ.get("MEDIATOR_SERVER_CERT")
        MEDIATOR_SERVER_KEY = os.environ.get("MEDIATOR_SERVER_KEY")
        MEDIATOR_CA_CERT = os.environ.get("MEDIATOR_CA_CERT")

        have_certs = (
            MEDIATOR_SERVER_CERT is not None
            and MEDIATOR_SERVER_KEY is not None
            and MEDIATOR_CA_CERT is not None
        )

        if not have_certs:
            raise Exception(
                "use_cert_auth is True but certificate environment variables not set"
            )

        return {
            "MEDIATOR_SERVER_CERT": MEDIATOR_SERVER_CERT,
            "MEDIATOR_SERVER_KEY": MEDIATOR_SERVER_KEY,
            "MEDIATOR_CA_CERT": MEDIATOR_CA_CERT,
        }

    def _metadata(self, meter_id, ip_address: str):
        return {"meter_id": meter_id, "emlite_host": ip_address}
