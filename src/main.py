"""FastAPI entrypoint for the Unison Context Graph service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from context_graph import Config, ContextGraphService, ContextGraphSettings, register_routes

try:
    from unison_common import ContextBatonManager, ContextBatonSettings
except ImportError:
    class ContextBatonSettings:  # type: ignore
        pass

    class ContextBatonManager:  # type: ignore
        def __init__(self, settings: ContextBatonSettings | None = None) -> None:
            self.settings = settings
from context_graph.models import (
    ContextDimension,
    ContextPreferences,
    ContextQueryRequest,
    ContextState,
    ContextStateResponse,
    ContextUpdateRequest,
    EventTrace,
    ReplayRequest,
    TraceListResponse,
)
from context_graph.replay import ReplayStore

try:
    from unison_common import BatonMiddleware
except Exception:  # pragma: no cover - middleware optional in devstack
    BatonMiddleware = None  # type: ignore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = ContextGraphSettings.from_env()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    try:
        context_service._sqlite_replay.close()
    except Exception:
        logger.exception("Failed to close replay store cleanly during shutdown")


app = FastAPI(
    title="Unison Context Graph Service",
    description="Real-time context fusion and environmental intelligence",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

context_service = ContextGraphService(settings=settings)
baton_manager = ContextBatonManager(ContextBatonSettings())
app.state.baton_manager = baton_manager
register_routes(app, context_service, baton_manager=baton_manager)
if BatonMiddleware:
    app.add_middleware(BatonMiddleware)


__all__ = [
    "app",
    "Config",
    "ContextDimension",
    "ContextPreferences",
    "ContextQueryRequest",
    "ContextState",
    "ContextStateResponse",
    "ContextUpdateRequest",
    "ContextGraphService",
    "ContextGraphSettings",
    "EventTrace",
    "ReplayRequest",
    "TraceListResponse",
    "ReplayStore",
]

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )
