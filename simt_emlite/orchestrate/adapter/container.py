from dataclasses import dataclass
from enum import Enum
from typing import Dict


class ContainerEnvironment(Enum):
    DOCKER = 1
    FLY = 2


class ContainerState(Enum):
    STARTED = 1
    STOPPED = 2
    STOPPING = 3
    STARTING = 4
    REMOVING = 5
    CREATED = 6
    FAILED = 7


@dataclass
class Container:
    id: str
    name: str
    image: str
    port: int
    status: ContainerState
    container_environment: ContainerEnvironment
    metadata: Dict[str, str]

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "port": self.port,
            "status": self.status.name,
        }
