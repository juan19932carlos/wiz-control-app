"""Typed views of the `result` payloads the bulbs return."""

from dataclasses import dataclass
from typing import Any, Self


@dataclass(frozen=True)
class Pilot:
    """Current light state, from `getPilot`."""

    mac: str
    state: bool
    dimming: int
    temp: int | None
    rgb: tuple[int, int, int] | None
    scene_id: int

    @classmethod
    def from_result(cls, result: dict[str, Any]) -> Self:
        has_rgb = all(k in result for k in ("r", "g", "b"))
        return cls(
            mac=result["mac"],
            state=bool(result["state"]),
            dimming=int(result.get("dimming", 0)),
            temp=result.get("temp"),
            rgb=(result["r"], result["g"], result["b"]) if has_rgb else None,
            scene_id=int(result.get("sceneId", 0)),
        )


@dataclass(frozen=True)
class SystemConfig:
    """Hardware identity, from `getSystemConfig`."""

    mac: str
    module_name: str
    fw_version: str

    @property
    def has_rgb(self) -> bool:
        # The module name encodes the light type: SHRGB = color, SHTW = tunable white, SHDW = dimmable.
        return "RGB" in self.module_name

    @classmethod
    def from_result(cls, result: dict[str, Any]) -> Self:
        return cls(mac=result["mac"], module_name=result["moduleName"], fw_version=result["fwVersion"])


@dataclass(frozen=True)
class ModelConfig:
    """Hardware limits, from `getModelConfig`."""

    min_dim_level: int
    min_kelvin: int | None
    max_kelvin: int | None

    @classmethod
    def from_result(cls, result: dict[str, Any]) -> Self:
        cct = result.get("cctRange")
        return cls(
            min_dim_level=int(result.get("minDimLevel", 10)),
            min_kelvin=min(cct) if cct else None,
            max_kelvin=max(cct) if cct else None,
        )
