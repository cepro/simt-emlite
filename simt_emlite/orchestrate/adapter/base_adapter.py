import os
from abc import ABC, abstractmethod
from typing import List

from simt_emlite.orchestrate.adapter.container import Container, ContainerState


class BaseAdapter(ABC):
    def __init__(self):
        self.socks_dict = {
            "SOCKS_HOST": os.environ.get("SOCKS_HOST"),
            "SOCKS_PORT": os.environ.get("SOCKS_PORT"),
            "SOCKS_USERNAME": os.environ.get("SOCKS_USERNAME"),
            "SOCKS_PASSWORD": os.environ.get("SOCKS_PASSWORD"),
        }

        self.use_socks = all(
            self.socks_dict[f"SOCKS_{v}"] is not None
            for v in [
                "HOST",
                "PORT",
                "USERNAME",
                "PASSWORD",
            ]
        )

    @abstractmethod
    def list(
        self,
        metadata_filter: tuple[str, str] = None,
        status_filter: ContainerState = None,
    ) -> List[Container]:
        pass

    def get(
        self,
        meter_id: str,
    ) -> Container:
        meters = self.list(("meter_id", meter_id))
        return meters[0] if len(meters) != 0 else None

    @abstractmethod
    def create(
        self, cmd: str, name: str, meter_id: str, ip_address: str, mediator_port: int
    ) -> str:
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
    def mediator_host_port(self, meter_id: str, serial: str):
        pass
