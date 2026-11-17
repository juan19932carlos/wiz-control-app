"""The real gateway: translates between the domain and the WiZ UDP protocol."""

import asyncio
from typing import Any

from wiz_protocol import Pilot, WizClient, WizTimeoutError, discover
from wiz_server.adapters.bulb_gateway import AbstractBulbGateway, BulbUnreachable
from wiz_server.domain.model import Bulb, Capabilities, LightState


def _to_state(pilot: Pilot) -> LightState:
    return LightState(on=pilot.state, brightness=pilot.dimming, kelvin=pilot.temp, rgb=pilot.rgb)


class WizBulbGateway(AbstractBulbGateway):
    def __init__(
        self, targets: list[str], client: WizClient | None = None, discovery_wait: float = 2.0
    ) -> None:
        self.targets = targets
        self.client = client or WizClient()
        self.discovery_wait = discovery_wait

    async def discover(self) -> list[Bulb]:
        found = await discover(self.targets, port=self.client.port, wait=self.discovery_wait)
        results = await asyncio.gather(*(self._describe(b.ip) for b in found), return_exceptions=True)
        return [bulb for bulb in results if isinstance(bulb, Bulb)]  # A bulb that went quiet is skipped.

    async def _describe(self, ip: str) -> Bulb:
        system = await self.client.get_system_config(ip)
        model = await self.client.get_model_config(ip)
        pilot = await self.client.get_pilot(ip)
        return Bulb(
            id=system.mac,
            ip=ip,
            model=system.module_name,
            capabilities=Capabilities(
                min_brightness=model.min_dim_level,
                min_kelvin=model.min_kelvin,
                max_kelvin=model.max_kelvin,
                rgb=system.has_rgb,
            ),
            state=_to_state(pilot),
        )

    async def read_state(self, bulb: Bulb) -> LightState:
        try:
            return _to_state(await self.client.get_pilot(bulb.ip))
        except WizTimeoutError as e:
            raise BulbUnreachable(bulb.id) from e

    async def apply(self, bulb: Bulb) -> None:
        state = bulb.state
        params: dict[str, Any] = {"state": state.on}
        if state.on:
            params["dimming"] = state.brightness
            if state.rgb is not None:
                params["rgb"] = state.rgb
            elif state.kelvin is not None:
                params["temp"] = state.kelvin
        try:
            await self.client.set_pilot(bulb.ip, **params)
        except WizTimeoutError as e:
            raise BulbUnreachable(bulb.id) from e
