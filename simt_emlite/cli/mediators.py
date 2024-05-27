import fire

from typing import Dict, List

from simt_emlite.util.config import load_config
from simt_emlite.util.logging import get_logger


logger = get_logger(__name__, __file__)

config = load_config()
supabase_url, supabase_anon_key, access_token = config.values()


"""
    This is a CLI for managing Emlite mediator processes.
"""

class MediatorsCLI():
    def start_one(self, meter_id: str) -> int:
        pass

    def start_many(self, meter_ids: List[str]) -> Dict[str, int]:
        pass

    def start_all(self) -> Dict[str, int]:
        pass

    def stop_all(self):
        pass

    def remove_all(self):
        pass

    def stop_one(self, meter_id: str):
        pass

def main():
    fire.Fire(MediatorsCLI)

if __name__ == "__main__":
    main()