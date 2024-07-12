import os

from simt_emlite.orchestrate.adapter.docker_adapter import DockerAdapter
from simt_emlite.orchestrate.adapter.fly_adapter import FlyAdapter
from simt_emlite.util.config import load_config

fly_api_token = os.environ.get("FLY_TOKEN")
mediator_image = os.environ.get("SIMT_EMLITE_IMAGE")

if fly_api_token is None or mediator_image is None:
    config = load_config()
    fly_api_token = config["fly_token"]
    mediator_image = config["simt_emlite_image"]


def get_instance(esco: str = None):
    if fly_api_token is not None:
        adapter = FlyAdapter(fly_api_token, mediator_image, esco)
    else:
        adapter = DockerAdapter(mediator_image)
    return adapter
