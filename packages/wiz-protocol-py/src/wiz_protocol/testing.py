"""A fake WiZ bulb that answers the UDP protocol on a local address."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeBulb(asyncio.DatagramProtocol):
    mac: str
    module_name: str = "ESP24_SHTWC_01"
    pilot: dict[str, Any] = field(
        default_factory=lambda: {"state": True, "sceneId": 0, "temp": 4100, "dimming": 36}
    )
    cct_range: list[int] = field(default_factory=lambda: [2700, 2700, 6500, 6500])
    min_dim_level: int = 10
    silent: bool = False
    received: list[dict[str, Any]] = field(default_factory=list)
    transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        assert isinstance(transport, asyncio.DatagramTransport)
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        request = json.loads(data)
        self.received.append(request)
        if self.silent or self.transport is None:
            return
        result = self._handle(request["method"], request.get("params", {}))
        reply = {"method": request["method"], "env": "pro", "result": result}
        self.transport.sendto(json.dumps(reply).encode(), addr)

    def _handle(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        match method:
            case "getPilot":
                return {"mac": self.mac, "rssi": -50, **self.pilot}
            case "setPilot":
                self.pilot.update(params)
                return {"success": True}
            case "getSystemConfig":
                return {"mac": self.mac, "moduleName": self.module_name, "fwVersion": "1.39.0"}
            case "getModelConfig":
                return {"minDimLevel": self.min_dim_level, "cctRange": self.cct_range}
            case _:
                return {"success": False}

    def close(self) -> None:
        if self.transport is not None:
            self.transport.close()


async def serve(bulb: FakeBulb, host: str, port: int) -> FakeBulb:
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(lambda: bulb, local_addr=(host, port))
    return bulb
