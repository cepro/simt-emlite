from abc import ABC, abstractmethod
from typing import Dict, List

from simt_emlite.orchestrate.adapter.container import Container, ContainerState
from simt_emlite.util.config import load_config


class BaseAdapter(ABC):
    def __init__(self):
        pass

    def get(
        self,
        meter_id: str,
    ) -> Container:
        meters = self.list(("meter_id", meter_id))
        return meters[0] if len(meters) != 0 else None

    @abstractmethod
    def list(
        self,
        metadata_filter: tuple[str, str] = None,
        status_filter: ContainerState = None,
    ) -> List[Container]:
        pass

    @abstractmethod
    def create(self, cmd: str, meter_id: str, serial: str, ip_address: str) -> str:
        pass

    @abstractmethod
    def start(self, id: str):
        pass

    @abstractmethod
    def stop(self, id: str):
        pass

    @abstractmethod
    def destroy(self, id: str):
        pass

    @abstractmethod
    def mediator_address(self, meter_id: str, serial: str):
        pass

    def _env_vars(self, ip_address: str) -> Dict:
        config = load_config()

        env_vars: Dict = {
            "EMLITE_HOST": ip_address,
            "MEDIATOR_INACTIVITY_SECONDS": config["mediator_inactivity_seconds"],
        }

        socks_dict: Dict = self._socks_dict(config)
        if socks_dict is not None:
            env_vars.update(socks_dict)

        return env_vars

    def _socks_dict(self, config) -> Dict:
        socks_dict = {
            "SOCKS_HOST": config["socks_host"],
            "SOCKS_PORT": config["socks_port"],
            "SOCKS_USERNAME": config["socks_username"],
            "SOCKS_PASSWORD": config["socks_password"],
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

    def _metadata(self, meter_id, ip_address: str):
        return {"meter_id": meter_id, "emlite_host": ip_address}
