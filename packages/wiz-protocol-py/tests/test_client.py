import pytest

from wiz_protocol import WizClient, WizTimeoutError, discover


async def test_get_pilot_reads_the_bulb_state(start_bulb, port: int) -> None:
    await start_bulb(
        "127.0.0.2", mac="aa01", pilot={"state": True, "sceneId": 0, "temp": 3000, "dimming": 50}
    )
    client = WizClient(port=port)

    pilot = await client.get_pilot("127.0.0.2")

    assert (pilot.mac, pilot.state, pilot.dimming, pilot.temp) == ("aa01", True, 50, 3000)


async def test_set_pilot_sends_only_the_given_params(start_bulb, port: int) -> None:
    bulb = await start_bulb("127.0.0.2", mac="aa01")
    client = WizClient(port=port)

    await client.set_pilot("127.0.0.2", dimming=70, temp=2700)

    assert bulb.received[-1] == {"method": "setPilot", "params": {"dimming": 70, "temp": 2700}}


async def test_set_pilot_sends_rgb_as_r_g_b(start_bulb, port: int) -> None:
    bulb = await start_bulb("127.0.0.2", mac="aa01")
    client = WizClient(port=port)

    await client.set_pilot("127.0.0.2", rgb=(1, 2, 3))

    assert bulb.received[-1]["params"] == {"r": 1, "g": 2, "b": 3}


async def test_reads_system_and_model_config(start_bulb, port: int) -> None:
    await start_bulb("127.0.0.2", mac="aa01", module_name="ESP21_SHTW_01", cct_range=[2700, 2700, 5000, 5000])
    client = WizClient(port=port)

    system = await client.get_system_config("127.0.0.2")
    model = await client.get_model_config("127.0.0.2")

    assert system.module_name == "ESP21_SHTW_01"
    assert model.max_kelvin == 5000


async def test_a_silent_bulb_times_out_after_retries(start_bulb, port: int) -> None:
    bulb = await start_bulb("127.0.0.2", mac="aa01", silent=True)
    client = WizClient(port=port, timeout=0.05, retries=3)

    with pytest.raises(WizTimeoutError):
        await client.get_pilot("127.0.0.2")

    assert len(bulb.received) == 3


async def test_discover_finds_every_bulb_that_answers(start_bulb, port: int) -> None:
    await start_bulb("127.0.0.2", mac="aa01")
    await start_bulb("127.0.0.3", mac="aa02")

    found = await discover(["127.0.0.2", "127.0.0.3", "127.0.0.4"], port=port, wait=0.2)

    assert sorted((b.mac, b.ip) for b in found) == [("aa01", "127.0.0.2"), ("aa02", "127.0.0.3")]
