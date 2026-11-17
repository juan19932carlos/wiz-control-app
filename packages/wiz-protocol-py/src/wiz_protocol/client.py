"""Async UDP client for the WiZ protocol: JSON requests and replies on port 38899."""

import asyncio
import contextlib
import json
from dataclasses import dataclass
from typing import Any

from wiz_protocol.messages import ModelConfig, Pilot, SystemConfig

WIZ_PORT = 38899


class WizError(Exception):
    """The bulb answered with an error."""


class WizTimeoutError(WizError):
    """The bulb did not answer after every retry."""


class _Collector(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.replies: asyncio.Queue[tuple[dict[str, Any], str]] = asyncio.Queue()

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        with contextlib.suppress(json.JSONDecodeError):  # Not a WiZ reply. Ignore it.
            self.replies.put_nowait((json.loads(data), addr[0]))


def _encode(method: str, params: dict[str, Any]) -> bytes:
    return json.dumps({"method": method, "params": params}).encode()


class WizClient:
    def __init__(self, port: int = WIZ_PORT, timeout: float = 1.0, retries: int = 3) -> None:
        self.port = port
        self.timeout = timeout
        self.retries = retries

    async def call(self, ip: str, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send one request and return its `result`. UDP can drop packets, so it retries."""
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(_Collector, remote_addr=(ip, self.port))
        try:
            for _ in range(self.retries):
                transport.sendto(_encode(method, params or {}))
                try:
                    reply, _ = await asyncio.wait_for(protocol.replies.get(), self.timeout)
                except TimeoutError:
                    continue
                if "error" in reply:
                    raise WizError(f"{ip} {method}: {reply['error']}")
                return reply["result"]
        finally:
            transport.close()
        raise WizTimeoutError(f"{ip} did not answer {method} after {self.retries} tries")

    async def get_pilot(self, ip: str) -> Pilot:
        return Pilot.from_result(await self.call(ip, "getPilot"))

    async def set_pilot(
        self,
        ip: str,
        *,
        state: bool | None = None,
        dimming: int | None = None,
        temp: int | None = None,
        rgb: tuple[int, int, int] | None = None,
    ) -> None:
        """Change the light. The bulb answers `success` even to values it ignores, so validate first."""
        params: dict[str, Any] = {}
        if state is not None:
            params["state"] = state
        if dimming is not None:
            params["dimming"] = dimming
        if temp is not None:
            params["temp"] = temp
        if rgb is not None:
            params["r"], params["g"], params["b"] = rgb
        await self.call(ip, "setPilot", params)

    async def get_system_config(self, ip: str) -> SystemConfig:
        return SystemConfig.from_result(await self.call(ip, "getSystemConfig"))

    async def get_model_config(self, ip: str) -> ModelConfig:
        return ModelConfig.from_result(await self.call(ip, "getModelConfig"))


@dataclass(frozen=True)
class DiscoveredBulb:
    mac: str
    ip: str


async def discover(targets: list[str], port: int = WIZ_PORT, wait: float = 2.0) -> list[DiscoveredBulb]:
    """Send `getPilot` to every target and collect who answers within `wait` seconds.

    Targets can be broadcast addresses or single hosts. A host firewall often drops replies to a
    broadcast (the reply comes from the bulb's IP, not the broadcast IP), so sweeping the subnet
    host by host is the reliable fallback.
    """
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        _Collector, local_addr=("0.0.0.0", 0), allow_broadcast=True
    )
    found: dict[str, DiscoveredBulb] = {}
    try:
        message = _encode("getPilot", {})
        for target in targets:
            try:
                transport.sendto(message, (target, port))
            except OSError:
                continue  # Unreachable target. Others may still answer.
        deadline = loop.time() + wait
        while (remaining := deadline - loop.time()) > 0:
            try:
                reply, ip = await asyncio.wait_for(protocol.replies.get(), remaining)
            except TimeoutError:
                break
            mac = reply.get("result", {}).get("mac")
            if mac:
                found[mac] = DiscoveredBulb(mac=mac, ip=ip)
    finally:
        transport.close()
    return list(found.values())
