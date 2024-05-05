import json

from typing import List
from . import EndpointConfig


def load_routes(filename: str, filepath: str) -> List[EndpointConfig]:
    with open(f"{filepath}/{filename}") as f:
        data = json.load(f)

    return [EndpointConfig(**{"endpoint": k, **v}) for k, v in data.items()]
