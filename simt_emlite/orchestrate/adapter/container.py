from dataclasses import dataclass
from enum import Enum
from typing import Dict


class ContainerEnvironment(Enum):
    DOCKER = 1
    FLY = 2


class ContainerState(Enum):
    STARTED = 1
    STOPPED = 2


@dataclass
class Container:
    id: str
    name: str
    image: str
    status: ContainerState
    container_environment: ContainerEnvironment
    metadata: Dict[str, str]
