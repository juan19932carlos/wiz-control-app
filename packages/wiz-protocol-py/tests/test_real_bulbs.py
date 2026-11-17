"""Read-only checks against real bulbs. Run with: WIZ_SUBNET=192.168.2.0/24 uv run pytest -m integration"""

import ipaddress
import os

import pytest

from wiz_protocol import WizClient, discover

pytestmark = pytest.mark.integration

SUBNET = os.environ.get("WIZ_SUBNET")


@pytest.fixture
def hosts() -> list[str]:
    if not SUBNET:
        pytest.skip("set WIZ_SUBNET, for example 192.168.2.0/24")
    return [str(h) for h in ipaddress.ip_network(SUBNET).hosts()]


async def test_finds_bulbs_and_reads_them(hosts: list[str]) -> None:
    found = await discover(hosts)
    assert found, "no bulb answered"

    client = WizClient()
    for bulb in found:
        pilot = await client.get_pilot(bulb.ip)
        system = await client.get_system_config(bulb.ip)
        model = await client.get_model_config(bulb.ip)
        assert pilot.mac == system.mac == bulb.mac
        assert model.min_dim_level >= 1
