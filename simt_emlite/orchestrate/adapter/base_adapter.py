from abc import ABC, abstractmethod
from enum import Enum
from typing import List


class ContainerState(Enum):
    STARTED = 1
    STOPPED = 2


class BaseAdapter(ABC):
    @abstractmethod
    def list(
        self,
        metadata_filter: tuple[str, str] = None,
        status_filter: ContainerState = None
    ) -> List[str]:
        pass

    @abstractmethod
    def create(
        self,
        cmd: str,
        name: str,
        meter_id: str,
        ip_address: str,
        mediator_port: int
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
