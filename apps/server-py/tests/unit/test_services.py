import pytest
from server_fakes import FakeGateway, make_bulb

from wiz_server.adapters.bulb_gateway import BulbUnreachable
from wiz_server.adapters.repository import InMemoryRepository
from wiz_server.domain.model import UnsupportedFeature
from wiz_server.service_layer import services


async def test_discover_stores_every_bulb_found() -> None:
    gateway = FakeGateway(make_bulb("aa01"), make_bulb("aa02"))
    repo = InMemoryRepository()

    await services.discover_bulbs(gateway, repo)

    assert sorted(b.id for b in repo.list()) == ["aa01", "aa02"]


async def test_rediscovery_updates_a_bulb_whose_ip_changed() -> None:
    repo = InMemoryRepository()
    await services.discover_bulbs(FakeGateway(make_bulb("aa01", ip="10.0.0.2")), repo)

    await services.discover_bulbs(FakeGateway(make_bulb("aa01", ip="10.0.0.9")), repo)

    assert [b.ip for b in repo.list()] == ["10.0.0.9"]


async def test_rediscovery_keeps_bulbs_that_did_not_answer_but_marks_them_unreachable() -> None:
    repo = InMemoryRepository()
    gateway = FakeGateway(make_bulb("aa01"), make_bulb("aa02"))
    await services.discover_bulbs(gateway, repo)

    gateway.unreachable.add("aa02")
    await services.discover_bulbs(gateway, repo)

    assert {b.id: b.reachable for b in repo.list()} == {"aa01": True, "aa02": False}


async def test_list_bulbs_refreshes_the_state_from_the_bulbs() -> None:
    # Someone changed the bulb from the WiZ phone app.
    gateway = FakeGateway(make_bulb("aa01", brightness=50))
    repo = InMemoryRepository()
    await services.discover_bulbs(gateway, repo)
    gateway.network["aa01"].state = make_bulb("aa01", brightness=90).state

    bulbs = await services.list_bulbs(gateway, repo)

    assert bulbs[0].state.brightness == 90


async def test_list_bulbs_marks_a_silent_bulb_unreachable_and_keeps_its_last_state() -> None:
    gateway = FakeGateway(make_bulb("aa01", brightness=50))
    repo = InMemoryRepository()
    await services.discover_bulbs(gateway, repo)
    gateway.unreachable.add("aa01")

    [bulb] = await services.list_bulbs(gateway, repo)

    assert (bulb.reachable, bulb.state.brightness) == (False, 50)


async def test_brighten_sends_the_new_state_to_the_bulb() -> None:
    gateway = FakeGateway(make_bulb("aa01", brightness=50))
    repo = InMemoryRepository()
    await services.discover_bulbs(gateway, repo)

    bulb = await services.brighten(gateway, repo, "aa01")

    assert bulb.state.brightness == 60
    assert gateway.applied[-1] == ("aa01", bulb.state)


async def test_an_invalid_change_sends_nothing() -> None:
    gateway = FakeGateway(make_bulb("aa01"))
    repo = InMemoryRepository()
    await services.discover_bulbs(gateway, repo)

    with pytest.raises(UnsupportedFeature):
        await services.set_color(gateway, repo, "aa01", (255, 0, 0))

    assert gateway.applied == []


async def test_a_change_to_an_unknown_bulb_fails() -> None:
    with pytest.raises(services.BulbNotFound):
        await services.turn_on(FakeGateway(), InMemoryRepository(), "nope")


async def test_a_change_to_an_unreachable_bulb_fails_and_marks_it() -> None:
    gateway = FakeGateway(make_bulb("aa01"))
    repo = InMemoryRepository()
    await services.discover_bulbs(gateway, repo)
    gateway.unreachable.add("aa01")

    with pytest.raises(BulbUnreachable):
        await services.turn_off(gateway, repo, "aa01")

    stored = repo.get("aa01")
    assert stored is not None
    assert (stored.reachable, stored.state.on) == (False, True)


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda g, r: services.turn_off(g, r, "aa01"), {"on": False}),
        (lambda g, r: services.set_brightness(g, r, "aa01", 30), {"brightness": 30}),
        (lambda g, r: services.dim(g, r, "aa01"), {"brightness": 40}),
        (lambda g, r: services.set_white(g, r, "aa01", 2700), {"kelvin": 2700}),
    ],
)
async def test_each_change_reaches_the_bulb(change, expected: dict[str, object]) -> None:
    gateway = FakeGateway(make_bulb("aa01"))
    repo = InMemoryRepository()
    await services.discover_bulbs(gateway, repo)

    await change(gateway, repo)

    sent = gateway.applied[-1][1]
    assert {k: getattr(sent, k) for k in expected} == expected
