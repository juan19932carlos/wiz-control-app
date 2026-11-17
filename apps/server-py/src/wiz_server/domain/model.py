"""The bulb model. Knows nothing about UDP, WiZ messages, or HTTP."""

from dataclasses import dataclass, replace

MAX_BRIGHTNESS = 100
BRIGHTNESS_STEP = 10

type RGB = tuple[int, int, int]


class DomainError(Exception):
    pass


class InvalidValue(DomainError):
    """The value is outside what this bulb accepts."""


class UnsupportedFeature(DomainError):
    """This bulb model cannot do that, for example color on a white-only bulb."""


@dataclass(frozen=True)
class Capabilities:
    """What the hardware supports. Not every WiZ bulb has color."""

    min_brightness: int
    min_kelvin: int | None
    max_kelvin: int | None
    rgb: bool

    @property
    def tunable_white(self) -> bool:
        return self.min_kelvin is not None and self.max_kelvin is not None


@dataclass(frozen=True)
class LightState:
    """The light as it is. A bulb shows either a white temperature or a color, never both."""

    on: bool
    brightness: int
    kelvin: int | None
    rgb: RGB | None


class Bulb:
    """Entity. Identity is the MAC address: the IP can change, the MAC does not."""

    def __init__(
        self,
        id: str,
        ip: str,
        model: str,
        capabilities: Capabilities,
        state: LightState,
        reachable: bool = True,
    ) -> None:
        self.id = id
        self.ip = ip
        self.model = model
        self.capabilities = capabilities
        self.state = state
        self.reachable = reachable

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Bulb) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def turn_on(self) -> None:
        self.state = replace(self.state, on=True)

    def turn_off(self) -> None:
        self.state = replace(self.state, on=False)

    def set_brightness(self, level: int) -> None:
        low = self.capabilities.min_brightness
        if not low <= level <= MAX_BRIGHTNESS:
            raise InvalidValue(f"brightness must be between {low} and {MAX_BRIGHTNESS}, got {level}")
        self.state = replace(self.state, on=True, brightness=level)

    def brighten(self) -> None:
        self.set_brightness(min(self.state.brightness + BRIGHTNESS_STEP, MAX_BRIGHTNESS))

    def dim(self) -> None:
        self.set_brightness(max(self.state.brightness - BRIGHTNESS_STEP, self.capabilities.min_brightness))

    def set_white(self, kelvin: int) -> None:
        caps = self.capabilities
        if caps.min_kelvin is None or caps.max_kelvin is None:
            raise UnsupportedFeature(f"{self.model} has no adjustable white")
        if not caps.min_kelvin <= kelvin <= caps.max_kelvin:
            raise InvalidValue(
                f"white must be between {caps.min_kelvin}K and {caps.max_kelvin}K, got {kelvin}K"
            )
        self.state = replace(self.state, on=True, kelvin=kelvin, rgb=None)

    def set_color(self, rgb: RGB) -> None:
        if not self.capabilities.rgb:
            raise UnsupportedFeature(f"{self.model} is white only and has no color")
        if not all(0 <= channel <= 255 for channel in rgb):
            raise InvalidValue(f"every color channel must be between 0 and 255, got {rgb}")
        self.state = replace(self.state, on=True, rgb=rgb, kelvin=None)
