"""Prints the OpenAPI schema. The frontend generates its TypeScript types from it."""

import json

from wiz_server.adapters.repository import InMemoryRepository
from wiz_server.adapters.wiz_gateway import WizBulbGateway
from wiz_server.entrypoints.api import create_app


def openapi_json() -> str:
    # The schema does not run the lifespan, so no bulb is contacted.
    return json.dumps(create_app(WizBulbGateway(targets=[]), InMemoryRepository()).openapi(), indent=2)


def run() -> None:
    print(openapi_json())
