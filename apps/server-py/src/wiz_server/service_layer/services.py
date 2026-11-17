"""Use cases. Each one loads the bulb, asks the domain to change it, and sends the result."""

import asyncio
from collections.abc import Callable

from wiz_server.adapters.bulb_gateway import AbstractBulbGateway, BulbUnreachable
from wiz_server.adapters.repository import AbstractRepository
from wiz_server.domain.model import RGB, Bulb


class BulbNotFound(Exception):
    pass


async def discover_bulbs(gateway: AbstractBulbGateway, repo: AbstractRepository) -> list[Bulb]:
    found = {bulb.id: bulb for bulb in await gateway.discover()}
    for known in repo.list():
        if known.id not in found:
            known.reachable = False  # Kept, so it reappears with the same identity when it comes back.
    for bulb in found.values():
        repo.add(bulb)
    return repo.list()


async def list_bulbs(gateway: AbstractBulbGateway, repo: AbstractRepository) -> list[Bulb]:
    """Refresh every bulb from the hardware. Its state can change outside this app (WiZ phone app)."""
    bulbs = repo.list()
    await asyncio.gather(*(_refresh(gateway, bulb) for bulb in bulbs))
    return bulbs


async def _refresh(gateway: AbstractBulbGateway, bulb: Bulb) -> None:
    try:
        bulb.state = await gateway.read_state(bulb)
        bulb.reachable = True
    except BulbUnreachable:
        bulb.reachable = False


def get_bulb(repo: AbstractRepository, bulb_id: str) -> Bulb:
    bulb = repo.get(bulb_id)
    if bulb is None:
        raise BulbNotFound(bulb_id)
    return bulb


async def _change(
    gateway: AbstractBulbGateway, repo: AbstractRepository, bulb_id: str, change: Callable[[Bulb], None]
) -> Bulb:
    bulb = get_bulb(repo, bulb_id)
    before = bulb.state
    change(bulb)  # Domain errors raise here, before anything is sent.
    try:
        await gateway.apply(bulb)
    except BulbUnreachable:
        bulb.state = before
        bulb.reachable = False
        raise
    bulb.reachable = True
    return bulb


async def turn_on(gateway: AbstractBulbGateway, repo: AbstractRepository, bulb_id: str) -> Bulb:
    return await _change(gateway, repo, bulb_id, Bulb.turn_on)


async def turn_off(gateway: AbstractBulbGateway, repo: AbstractRepository, bulb_id: str) -> Bulb:
    return await _change(gateway, repo, bulb_id, Bulb.turn_off)


async def brighten(gateway: AbstractBulbGateway, repo: AbstractRepository, bulb_id: str) -> Bulb:
    return await _change(gateway, repo, bulb_id, Bulb.brighten)


async def dim(gateway: AbstractBulbGateway, repo: AbstractRepository, bulb_id: str) -> Bulb:
    return await _change(gateway, repo, bulb_id, Bulb.dim)


async def set_brightness(
    gateway: AbstractBulbGateway, repo: AbstractRepository, bulb_id: str, level: int
) -> Bulb:
    return await _change(gateway, repo, bulb_id, lambda b: b.set_brightness(level))


async def set_white(
    gateway: AbstractBulbGateway, repo: AbstractRepository, bulb_id: str, kelvin: int
) -> Bulb:
    return await _change(gateway, repo, bulb_id, lambda b: b.set_white(kelvin))


async def set_color(gateway: AbstractBulbGateway, repo: AbstractRepository, bulb_id: str, rgb: RGB) -> Bulb:
    return await _change(gateway, repo, bulb_id, lambda b: b.set_color(rgb))
