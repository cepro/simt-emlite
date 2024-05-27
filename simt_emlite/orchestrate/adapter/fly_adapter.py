from typing import List
import fire

from simt_fly_machines.api import API

from simt_emlite.orchestrate.adapter.base_adapter import BaseAdapter, ContainerState
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

fly_status = {
    ContainerState.STARTED: 'started',
    ContainerState.STOPPED: 'stopped',
}

def metadata_filter_fn(key, value):
    def machine_filter(machine) -> bool:
        metadata = machine["config"]["metadata"]
        return key in metadata and metadata[key] == value
    return machine_filter
    
class FlyAdapter(BaseAdapter):
    def __init__(self, fly_app: str, image: str):
        self.api = API()
        self.fly_app = fly_app
        self.image = image

    def list(
        self,
        metadata_filter: tuple[str, str] = None,
        status_filter: ContainerState = None
    ) -> List[str]:
        machines = self.api.list(self.fly_app)
        if metadata_filter:
            logger.debug(f"metadata filter [{metadata_filter}]")
            machines = list(filter(
                metadata_filter_fn(metadata_filter[0], metadata_filter[1]),
                machines
            ))

        if status_filter:
            logger.debug(f"status filter [{status_filter}]")
            machines = list(filter(
                lambda m: m["state"] == status_filter,
                machines
            ))

        machine_ids = list(map(lambda m: m["id"], machines))
        logger.info(
            f"list machine ids [{machine_ids}]",
            machine_ids=machine_ids
        )
        
        return machine_ids

    def create(
        self,
        cmd: str,
        name: str,
        meter_id: str,
        ip_address: str
    ) -> str:
        machine = self.api.create(
            self.fly_app, 
            self.image, 
            [cmd],
            name=name,
            env_vars={
                "EMLITE_HOST": ip_address
            },
            metadata={
                "meter_id": meter_id,
                "emlite_host": ip_address
            })
        logger.info(
            f"created machine with id {machine["id"]}",
            machine_id=machine["id"]
        )
        return machine["id"]

    def start(self, id: str):
        return self.api.start(self.fly_app, id)

    def stop(self, id: str):
        return self.api.stop(self.fly_app, id)

    def destroy(self, id: str):
        return self.api.destroy(self.fly_app, id)

def main():
    fire.Fire(FlyAdapter)

if __name__ == "__main__":
    main()