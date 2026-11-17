import pytest

from wiz_protocol import ModelConfig, Pilot, SystemConfig


def test_parses_a_white_pilot() -> None:
    pilot = Pilot.from_result(
        {"mac": "6c2990840cfa", "rssi": -57, "state": True, "sceneId": 0, "temp": 4100, "dimming": 36}
    )

    assert pilot == Pilot(mac="6c2990840cfa", state=True, dimming=36, temp=4100, rgb=None, scene_id=0)


def test_parses_an_rgb_pilot() -> None:
    pilot = Pilot.from_result(
        {"mac": "a1", "state": True, "sceneId": 0, "r": 255, "g": 10, "b": 0, "dimming": 80}
    )

    assert pilot.rgb == (255, 10, 0)
    assert pilot.temp is None


def test_parses_system_config() -> None:
    config = SystemConfig.from_result(
        {"mac": "9877d54c152a", "moduleName": "ESP24_SHTWC_01", "fwVersion": "1.39.0", "homeId": 1}
    )

    assert config == SystemConfig(mac="9877d54c152a", module_name="ESP24_SHTWC_01", fw_version="1.39.0")


def test_model_config_reads_the_white_range_from_cct_range() -> None:
    config = ModelConfig.from_result({"minDimLevel": 10, "cctRange": [2700, 2700, 5000, 5000]})

    assert config == ModelConfig(min_dim_level=10, min_kelvin=2700, max_kelvin=5000)


def test_model_config_without_cct_range_has_no_white_range() -> None:
    config = ModelConfig.from_result({"minDimLevel": 10})

    assert (config.min_kelvin, config.max_kelvin) == (None, None)


@pytest.mark.parametrize(
    ("module_name", "has_rgb"),
    [("ESP24_SHTWC_01", False), ("ESP21_SHTW_01", False), ("ESP01_SHRGB1C_31", True)],
)
def test_system_config_knows_if_the_module_has_rgb(module_name: str, has_rgb: bool) -> None:
    config = SystemConfig(mac="x", module_name=module_name, fw_version="1")

    assert config.has_rgb is has_rgb
