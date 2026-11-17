import json

from wiz_server.entrypoints.openapi import openapi_json


def test_the_schema_names_every_operation_for_the_typed_client() -> None:
    schema = json.loads(openapi_json())

    operation_ids = {op["operationId"] for path in schema["paths"].values() for op in path.values()}
    assert {"listBulbs", "discoverBulbs", "turnOn", "turnOff", "brighten", "dim"} <= operation_ids
    assert {"setBrightness", "setWhite", "setColor"} <= operation_ids
