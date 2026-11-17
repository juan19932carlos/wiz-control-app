"""Where discovered bulbs are kept. In memory only: see ADR 0001, Persistence."""

import abc

from wiz_server.domain.model import Bulb


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, bulb: Bulb) -> None: ...

    @abc.abstractmethod
    def get(self, bulb_id: str) -> Bulb | None: ...

    @abc.abstractmethod
    def list(self) -> list[Bulb]: ...


class InMemoryRepository(AbstractRepository):
    def __init__(self) -> None:
        self._bulbs: dict[str, Bulb] = {}

    def add(self, bulb: Bulb) -> None:
        self._bulbs[bulb.id] = bulb

    def get(self, bulb_id: str) -> Bulb | None:
        return self._bulbs.get(bulb_id)

    def list(self) -> list[Bulb]:
        return list(self._bulbs.values())
