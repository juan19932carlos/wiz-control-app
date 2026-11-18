from collections.abc import Iterator
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from server_fakes import FakeGateway, make_bulb

from wiz_server.adapters.repository import InMemoryRepository
from wiz_server.entrypoints.api import create_app


@pytest.fixture
def gateway() -> FakeGateway:
    return FakeGateway(make_bulb("aa01", ip="10.0.0.2", brightness=50))


@pytest.fixture
def client(gateway: FakeGateway) -> Iterator[TestClient]:
    app = create_app(gateway, InMemoryRepository())
    with TestClient(app) as client:  # `with` runs the lifespan, which discovers once.
        yield client


def test_lists_the_bulbs_found_on_start(client: TestClient) -> None:
    response = client.get("/api/bulbs")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "aa01",
            "ip": "10.0.0.2",
            "model": "ESP21_SHTW_01",
            "reachable": True,
            "capabilities": {"min_brightness": 10, "min_kelvin": 2700, "max_kelvin": 5000, "rgb": False},
            "state": {"on": True, "brightness": 50, "kelvin": 4000, "rgb": None},
        }
    ]


def test_discover_finds_new_bulbs(client: TestClient, gateway: FakeGateway) -> None:
    new = make_bulb("aa02", ip="10.0.0.3")
    gateway.network[new.id] = new

    response = client.post("/api/bulbs/discover")

    assert sorted(b["id"] for b in response.json()) == ["aa01", "aa02"]


@pytest.mark.parametrize(
    ("method", "path", "body", "field", "value"),
    [
        ("post", "/api/bulbs/aa01/off", None, "on", False),
        ("post", "/api/bulbs/aa01/brighten", None, "brightness", 60),
        ("post", "/api/bulbs/aa01/dim", None, "brightness", 40),
        ("put", "/api/bulbs/aa01/brightness", {"level": 25}, "brightness", 25),
        ("put", "/api/bulbs/aa01/white", {"kelvin": 3000}, "kelvin", 3000),
    ],
)
def test_changes_return_the_new_state(client: TestClient, method, path, body, field, value) -> None:
    response = client.request(method.upper(), path, json=body)

    assert response.status_code == 200
    assert response.json()["state"][field] == value


def test_unknown_bulb_is_404(client: TestClient) -> None:
    assert client.post("/api/bulbs/nope/on").status_code == 404


def test_out_of_range_value_is_422_with_the_reason(client: TestClient) -> None:
    response = client.put("/api/bulbs/aa01/brightness", json={"level": 5})

    assert response.status_code == 422
    assert "between 10 and 100" in response.json()["detail"]


def test_color_on_a_white_only_bulb_is_409(client: TestClient) -> None:
    response = client.put("/api/bulbs/aa01/color", json={"r": 255, "g": 0, "b": 0})

    assert response.status_code == 409


def test_unreachable_bulb_is_503(client: TestClient, gateway: FakeGateway) -> None:
    gateway.unreachable.add("aa01")

    assert client.post("/api/bulbs/aa01/on").status_code == 503


def test_a_color_bulb_reports_rgb_as_an_object(gateway: FakeGateway) -> None:
    color = make_bulb("cc01")
    color.capabilities = replace(color.capabilities, rgb=True)
    gateway.network[color.id] = color

    with TestClient(create_app(gateway, InMemoryRepository())) as client:
        response = client.put("/api/bulbs/cc01/color", json={"r": 1, "g": 2, "b": 3})

    assert response.json()["state"]["rgb"] == {"r": 1, "g": 2, "b": 3}


def test_health_answers_without_contacting_bulbs(client: TestClient, gateway: FakeGateway) -> None:
    gateway.unreachable.add("aa01")

    response = client.get("/api/health")

    assert (response.status_code, response.json()) == (200, {"status": "ok"})
