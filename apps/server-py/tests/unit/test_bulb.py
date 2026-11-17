import pytest

from wiz_server.domain.model import (
    Bulb,
    Capabilities,
    InvalidValue,
    LightState,
    UnsupportedFeature,
)

WHITE_ONLY = Capabilities(min_brightness=10, min_kelvin=2700, max_kelvin=5000, rgb=False)
COLOR = Capabilities(min_brightness=10, min_kelvin=2200, max_kelvin=6500, rgb=True)


def make_bulb(capabilities: Capabilities = WHITE_ONLY, **state: object) -> Bulb:
    defaults: dict[str, object] = {"on": True, "brightness": 50, "kelvin": 4000, "rgb": None}
    defaults.update(state)
    return Bulb(
        id="aa01",
        ip="192.168.2.16",
        model="ESP21_SHTW_01",
        capabilities=capabilities,
        state=LightState(**defaults),  # type: ignore[arg-type]
    )


def test_turn_off_and_on() -> None:
    bulb = make_bulb()

    bulb.turn_off()
    assert bulb.state.on is False

    bulb.turn_on()
    assert bulb.state.on is True


def test_set_brightness_within_limits() -> None:
    bulb = make_bulb()

    bulb.set_brightness(80)

    assert bulb.state.brightness == 80


@pytest.mark.parametrize("level", [9, 101])
def test_set_brightness_outside_the_bulb_limits_is_rejected(level: int) -> None:
    # Real bulbs answer "success" to dimming 5 and ignore it. The domain must refuse it.
    bulb = make_bulb()

    with pytest.raises(InvalidValue):
        bulb.set_brightness(level)

    assert bulb.state.brightness == 50


def test_brighten_adds_one_step() -> None:
    bulb = make_bulb(brightness=50)

    bulb.brighten()

    assert bulb.state.brightness == 60


def test_brighten_stops_at_100() -> None:
    bulb = make_bulb(brightness=95)

    bulb.brighten()

    assert bulb.state.brightness == 100


def test_dim_stops_at_the_bulb_minimum() -> None:
    bulb = make_bulb(brightness=15)

    bulb.dim()

    assert bulb.state.brightness == 10


def test_brighten_turns_an_off_bulb_on() -> None:
    bulb = make_bulb(on=False, brightness=50)

    bulb.brighten()

    assert bulb.state.on is True


def test_set_white_within_the_bulb_range() -> None:
    bulb = make_bulb(COLOR, kelvin=None, rgb=(255, 0, 0))

    bulb.set_white(3000)

    assert (bulb.state.kelvin, bulb.state.rgb) == (3000, None)


@pytest.mark.parametrize("kelvin", [2600, 5100])
def test_set_white_outside_the_bulb_range_is_rejected(kelvin: int) -> None:
    bulb = make_bulb(WHITE_ONLY)

    with pytest.raises(InvalidValue):
        bulb.set_white(kelvin)


def test_set_white_on_a_bulb_without_white_range_is_unsupported() -> None:
    bulb = make_bulb(Capabilities(min_brightness=10, min_kelvin=None, max_kelvin=None, rgb=False))

    with pytest.raises(UnsupportedFeature):
        bulb.set_white(3000)


def test_set_color_on_a_color_bulb() -> None:
    bulb = make_bulb(COLOR)

    bulb.set_color((0, 128, 255))

    assert (bulb.state.rgb, bulb.state.kelvin) == ((0, 128, 255), None)


def test_set_color_on_a_white_only_bulb_is_unsupported() -> None:
    bulb = make_bulb(WHITE_ONLY)

    with pytest.raises(UnsupportedFeature):
        bulb.set_color((255, 0, 0))


def test_set_color_with_a_channel_out_of_range_is_rejected() -> None:
    bulb = make_bulb(COLOR)

    with pytest.raises(InvalidValue):
        bulb.set_color((256, 0, 0))


def test_changing_light_turns_the_bulb_on() -> None:
    bulb = make_bulb(COLOR, on=False)

    bulb.set_color((1, 2, 3))

    assert bulb.state.on is True
