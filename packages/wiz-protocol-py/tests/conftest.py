import socket
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from fake_bulb import FakeBulb, serve  # noqa: E402


@pytest.fixture
def port() -> int:
    """A free UDP port. Every fake bulb in a test listens on it, each on its own 127.0.0.x."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
async def start_bulb(port: int) -> AsyncIterator[Callable[..., Awaitable[FakeBulb]]]:
    bulbs: list[FakeBulb] = []

    async def start(host: str, **kwargs: object) -> FakeBulb:
        bulb = await serve(FakeBulb(**kwargs), host, port)  # type: ignore[arg-type]
        bulbs.append(bulb)
        return bulb

    yield start
    for bulb in bulbs:
        bulb.close()
