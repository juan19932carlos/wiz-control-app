"""Test doubles shared by the server tests."""

from dataclasses import replace

from wiz_server.adapters.bulb_gateway import AbstractBulbGateway, BulbUnreachable
from wiz_server.domain.model import Bulb, Capabilities, LightState

WHITE_ONLY = Capabilities(min_brightness=10, min_kelvin=2700, max_kelvin=5000, rgb=False)


def make_bulb(id: str = "aa01", ip: str = "10.0.0.2", **state: object) -> Bulb:
    base = LightState(on=True, brightness=50, kelvin=4000, rgb=None)
    return Bulb(id=id, ip=ip, model="ESP21_SHTW_01", capabilities=WHITE_ONLY, state=replace(base, **state))


class FakeGateway(AbstractBulbGateway):
    """Bulbs that live in a dict. `network` is what the real bulbs would report."""

    def __init__(self, *bulbs: Bulb) -> None:
        self.network = {b.id: b for b in bulbs}
        self.unreachable: set[str] = set()
        self.applied: list[tuple[str, LightState]] = []

    async def discover(self) -> list[Bulb]:
        return [b for b in self.network.values() if b.id not in self.unreachable]

    async def read_state(self, bulb: Bulb) -> LightState:
        if bulb.id in self.unreachable:
            raise BulbUnreachable(bulb.id)
        return self.network[bulb.id].state

    async def apply(self, bulb: Bulb) -> None:
        if bulb.id in self.unreachable:
            raise BulbUnreachable(bulb.id)
        self.applied.append((bulb.id, bulb.state))
        self.network[bulb.id].state = bulb.state
