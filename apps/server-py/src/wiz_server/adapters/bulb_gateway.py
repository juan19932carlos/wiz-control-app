"""Port to the physical bulbs. The real adapter speaks the WiZ protocol; tests use a fake."""

import abc

from wiz_server.domain.model import Bulb, LightState


class BulbUnreachable(Exception):
    """The bulb did not answer. It may be switched off at the wall."""


class AbstractBulbGateway(abc.ABC):
    @abc.abstractmethod
    async def discover(self) -> list[Bulb]:
        """Find every bulb that answers now, with its capabilities and state."""

    @abc.abstractmethod
    async def read_state(self, bulb: Bulb) -> LightState:
        """Ask the bulb for its current light. Raises BulbUnreachable."""

    @abc.abstractmethod
    async def apply(self, bulb: Bulb) -> None:
        """Send the bulb's state to the hardware. Raises BulbUnreachable."""
