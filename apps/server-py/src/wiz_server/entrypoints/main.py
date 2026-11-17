"""Composition root: reads the settings and wires the real adapters into the app."""

import ipaddress
import os

import uvicorn

from wiz_server.adapters.repository import InMemoryRepository
from wiz_server.adapters.wiz_gateway import WizBulbGateway
from wiz_server.entrypoints.api import create_app


def discovery_targets(spec: str) -> list[str]:
    """`WIZ_TARGETS` is a comma list of IPs, broadcast addresses, or subnets (a subnet means every host)."""
    targets: list[str] = []
    for item in (part.strip() for part in spec.split(",")):
        if "/" in item:
            targets.extend(str(host) for host in ipaddress.ip_network(item, strict=False).hosts())
        elif item:
            targets.append(item)
    return targets


def build_app():  # noqa: ANN201 - uvicorn factory
    targets = discovery_targets(os.environ.get("WIZ_TARGETS", "255.255.255.255"))
    return create_app(WizBulbGateway(targets), InMemoryRepository())


def run() -> None:
    uvicorn.run(
        "wiz_server.entrypoints.main:build_app",
        factory=True,
        host=os.environ.get("WIZ_HOST", "127.0.0.1"),
        port=int(os.environ.get("WIZ_PORT", "8000")),
    )
