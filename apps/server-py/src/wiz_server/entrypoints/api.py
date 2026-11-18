"""HTTP API. Thin: it parses the request, calls a service, and maps errors to status codes."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from wiz_server.adapters.bulb_gateway import AbstractBulbGateway, BulbUnreachable
from wiz_server.adapters.repository import AbstractRepository
from wiz_server.domain.model import Bulb, InvalidValue, UnsupportedFeature
from wiz_server.service_layer import services


class CapabilitiesOut(BaseModel):
    min_brightness: int
    min_kelvin: int | None
    max_kelvin: int | None
    rgb: bool


class RgbOut(BaseModel):
    r: int
    g: int
    b: int


class StateOut(BaseModel):
    on: bool
    brightness: int
    kelvin: int | None
    rgb: RgbOut | None


class BulbOut(BaseModel):
    id: str
    ip: str
    model: str
    reachable: bool
    capabilities: CapabilitiesOut
    state: StateOut

    @classmethod
    def of(cls, bulb: Bulb) -> BulbOut:
        caps, state = bulb.capabilities, bulb.state
        return cls(
            id=bulb.id,
            ip=bulb.ip,
            model=bulb.model,
            reachable=bulb.reachable,
            capabilities=CapabilitiesOut(
                min_brightness=caps.min_brightness,
                min_kelvin=caps.min_kelvin,
                max_kelvin=caps.max_kelvin,
                rgb=caps.rgb,
            ),
            state=StateOut(
                on=state.on,
                brightness=state.brightness,
                kelvin=state.kelvin,
                rgb=RgbOut(r=state.rgb[0], g=state.rgb[1], b=state.rgb[2]) if state.rgb else None,
            ),
        )


class BrightnessIn(BaseModel):
    level: int


class WhiteIn(BaseModel):
    kelvin: int


class ColorIn(BaseModel):
    r: int = Field(ge=0, le=255)
    g: int = Field(ge=0, le=255)
    b: int = Field(ge=0, le=255)


class ErrorOut(BaseModel):
    detail: str


ERRORS = {
    404: {"model": ErrorOut},
    409: {"model": ErrorOut},
    422: {"model": ErrorOut},
    503: {"model": ErrorOut},
}


def create_app(gateway: AbstractBulbGateway, repo: AbstractRepository) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await services.discover_bulbs(gateway, repo)
        yield

    app = FastAPI(title="WiZ control", lifespan=lifespan)
    router = APIRouter(prefix="/api/bulbs", tags=["bulbs"], responses=ERRORS)  # type: ignore[arg-type]

    @router.get("", operation_id="listBulbs")
    async def list_bulbs() -> list[BulbOut]:
        return [BulbOut.of(b) for b in await services.list_bulbs(gateway, repo)]

    @router.post("/discover", operation_id="discoverBulbs")
    async def discover_bulbs() -> list[BulbOut]:
        return [BulbOut.of(b) for b in await services.discover_bulbs(gateway, repo)]

    @router.post("/{bulb_id}/on", operation_id="turnOn")
    async def turn_on(bulb_id: str) -> BulbOut:
        return BulbOut.of(await services.turn_on(gateway, repo, bulb_id))

    @router.post("/{bulb_id}/off", operation_id="turnOff")
    async def turn_off(bulb_id: str) -> BulbOut:
        return BulbOut.of(await services.turn_off(gateway, repo, bulb_id))

    @router.post("/{bulb_id}/brighten", operation_id="brighten")
    async def brighten(bulb_id: str) -> BulbOut:
        return BulbOut.of(await services.brighten(gateway, repo, bulb_id))

    @router.post("/{bulb_id}/dim", operation_id="dim")
    async def dim(bulb_id: str) -> BulbOut:
        return BulbOut.of(await services.dim(gateway, repo, bulb_id))

    @router.put("/{bulb_id}/brightness", operation_id="setBrightness")
    async def set_brightness(bulb_id: str, body: BrightnessIn) -> BulbOut:
        return BulbOut.of(await services.set_brightness(gateway, repo, bulb_id, body.level))

    @router.put("/{bulb_id}/white", operation_id="setWhite")
    async def set_white(bulb_id: str, body: WhiteIn) -> BulbOut:
        return BulbOut.of(await services.set_white(gateway, repo, bulb_id, body.kelvin))

    @router.put("/{bulb_id}/color", operation_id="setColor")
    async def set_color(bulb_id: str, body: ColorIn) -> BulbOut:
        return BulbOut.of(await services.set_color(gateway, repo, bulb_id, (body.r, body.g, body.b)))

    @app.get("/api/health", tags=["health"], operation_id="health")
    async def health() -> dict[str, str]:
        """Liveness for container healthchecks. Never talks to the bulbs."""
        return {"status": "ok"}

    app.include_router(router)
    _map_errors(app)
    return app


def _map_errors(app: FastAPI) -> None:
    status_by_error: dict[type[Exception], int] = {
        services.BulbNotFound: 404,
        UnsupportedFeature: 409,
        InvalidValue: 422,
        BulbUnreachable: 503,
    }

    async def handle(_: Request, exc: Exception) -> JSONResponse:
        status = status_by_error[type(exc)]
        detail = (
            f"bulb {exc} not found"
            if status == 404
            else f"bulb {exc} did not answer"
            if status == 503
            else str(exc)
        )
        return JSONResponse(status_code=status, content={"detail": detail})

    for error in status_by_error:
        app.add_exception_handler(error, handle)
