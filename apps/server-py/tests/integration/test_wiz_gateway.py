import socket
from collections.abc import AsyncIterator

import pytest

from wiz_protocol import WizClient
from wiz_protocol.testing import FakeBulb, serve
from wiz_server.adapters.bulb_gateway import BulbUnreachable
from wiz_server.adapters.wiz_gateway import WizBulbGateway
from wiz_server.domain.model import Capabilities, LightState


@pytest.fixture
def port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
async def bulbs(port: int) -> AsyncIterator[dict[str, FakeBulb]]:
    white = await serve(
        FakeBulb(mac="aa01", module_name="ESP21_SHTW_01", cct_range=[2700, 2700, 5000, 5000]),
        "127.0.0.2",
        port,
    )
    color = await serve(
        FakeBulb(
            mac="aa02",
            module_name="ESP01_SHRGB1C_31",
            pilot={"state": False, "sceneId": 0, "r": 255, "g": 0, "b": 0, "dimming": 80},
            cct_range=[2200, 2200, 6500, 6500],
        ),
        "127.0.0.3",
        port,
    )
    yield {"white": white, "color": color}
    white.close()
    color.close()


@pytest.fixture
def gateway(port: int) -> WizBulbGateway:
    return WizBulbGateway(
        targets=["127.0.0.2", "127.0.0.3"],
        client=WizClient(port=port, timeout=0.1, retries=2),
        discovery_wait=0.2,
    )


async def test_discover_builds_bulbs_with_their_capabilities(bulbs, gateway: WizBulbGateway) -> None:
    found = {b.id: b for b in await gateway.discover()}

    assert found["aa01"].ip == "127.0.0.2"
    assert found["aa01"].model == "ESP21_SHTW_01"
    assert found["aa01"].capabilities == Capabilities(
        min_brightness=10, min_kelvin=2700, max_kelvin=5000, rgb=False
    )
    assert found["aa02"].capabilities.rgb is True


async def test_discover_reads_the_light_state(bulbs, gateway: WizBulbGateway) -> None:
    found = {b.id: b for b in await gateway.discover()}

    assert found["aa01"].state == LightState(on=True, brightness=36, kelvin=4100, rgb=None)
    assert found["aa02"].state == LightState(on=False, brightness=80, kelvin=None, rgb=(255, 0, 0))


async def test_apply_sends_white_and_brightness(bulbs, gateway: WizBulbGateway) -> None:
    [white] = [b for b in await gateway.discover() if b.id == "aa01"]
    white.set_white(3000)
    white.set_brightness(70)

    await gateway.apply(white)

    assert bulbs["white"].received[-1]["params"] == {"state": True, "dimming": 70, "temp": 3000}


async def test_apply_sends_color(bulbs, gateway: WizBulbGateway) -> None:
    [color] = [b for b in await gateway.discover() if b.id == "aa02"]
    color.set_color((0, 0, 255))

    await gateway.apply(color)

    assert bulbs["color"].received[-1]["params"] == {"state": True, "dimming": 80, "r": 0, "g": 0, "b": 255}


async def test_apply_off_sends_only_the_state(bulbs, gateway: WizBulbGateway) -> None:
    [white] = [b for b in await gateway.discover() if b.id == "aa01"]
    white.turn_off()

    await gateway.apply(white)

    assert bulbs["white"].received[-1]["params"] == {"state": False}


async def test_a_silent_bulb_is_unreachable(bulbs, gateway: WizBulbGateway) -> None:
    [white] = [b for b in await gateway.discover() if b.id == "aa01"]
    bulbs["white"].silent = True

    with pytest.raises(BulbUnreachable):
        await gateway.read_state(white)
