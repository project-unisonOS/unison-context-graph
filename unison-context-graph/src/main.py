"""FastAPI entrypoint for the Unison Context Graph service."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from context_graph import Config, ContextGraphService, ContextGraphSettings, register_routes
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = ContextGraphSettings.from_env()

app = FastAPI(
    title="Unison Context Graph Service",
    description="Real-time context fusion and environmental intelligence",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

context_service = ContextGraphService(settings=settings)
register_routes(app, context_service)

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
