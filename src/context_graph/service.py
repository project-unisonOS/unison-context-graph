"""Context graph service implementation with durability hooks."""

from __future__ import annotations

import os
import sqlite3
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Body

from .models import (
    ContextPreferences,
    ContextQueryRequest,
    ContextState,
    ContextStateResponse,
    ContextUpdateRequest,
    EventTrace,
    ReplayRequest,
    TraceListResponse,
    TraceSearchRequest,
)
from .replay import ReplayStore, SQLiteReplayStore
from unison_common.durability import DurabilityManager


@dataclass
class ContextGraphSettings:
    host: str = "0.0.0.0"
    port: int = 8081
    allowed_origins: Optional[list[str]] = None

    @classmethod
    def from_env(cls) -> "ContextGraphSettings":
        host = os.getenv("CONTEXT_GRAPH_HOST", cls.host)
        port = int(os.getenv("CONTEXT_GRAPH_PORT", str(cls.port)))
        origins = os.getenv("ALLOWED_ORIGINS")
        allowed = [o.strip() for o in origins.split(",")] if origins else None
        return cls(host=host, port=port, allowed_origins=allowed)


# Backwards-compatible alias used by the FastAPI entrypoint.
Config = ContextGraphSettings


class ContextGraphService:
    def __init__(self, settings: ContextGraphSettings, db_path: Optional[Path] = None) -> None:
        self.settings = settings
        self._states: Dict[str, ContextState] = {}
        self.db_path = db_path or Path(os.getenv("CONTEXT_GRAPH_DB_PATH", "data/context_replay.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._durability = DurabilityManager(str(self.db_path))
        self._sqlite_replay = SQLiteReplayStore(self.db_path, self._durability)
        self._replay = ReplayStore()
        self._capabilities: Dict[str, object] = {"modalities": {"displays": []}}
        self._ensure_capabilities_table()
        self._load_capabilities_from_store()

    def _ensure_capabilities_table(self) -> None:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                manifest TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS capabilities_person (
                person_id TEXT PRIMARY KEY,
                manifest TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Seed default manifest if empty
        cur.execute("SELECT COUNT(*) FROM capabilities")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute(
                "INSERT INTO capabilities (id, manifest) VALUES (1, ?)",
                (json.dumps(self._capabilities),),
            )
            conn.commit()
        conn.close()

    def _load_capabilities_from_store(self) -> None:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cur = conn.cursor()
        cur.execute("SELECT manifest FROM capabilities WHERE id = 1")
        row = cur.fetchone()
        if row and row[0]:
            try:
                self._capabilities = json.loads(row[0])
            except Exception:
                self._capabilities = {"modalities": {"displays": []}}
        conn.close()

    def update_state(self, request: ContextUpdateRequest) -> ContextState:
        state = self._states.get(
            request.user_id,
            ContextState(
                user_id=request.user_id,
                preferences=ContextPreferences(),
                dimensions=[],
            ),
        )
        if request.dimensions is not None:
            state.dimensions = request.dimensions
        if request.preferences is not None:
            state.preferences = request.preferences
        self._states[request.user_id] = state
        return state

    def get_state(self, request: ContextQueryRequest) -> ContextState:
        if request.user_id not in self._states:
            raise KeyError(request.user_id)
        return self._states[request.user_id]

    def replay(self, request: ReplayRequest) -> ContextState:
        # Store the replay trace and return latest known state.
        self._replay.apply(request)
        self._sqlite_replay.apply(request)
        return self._states.get(
            request.user_id,
            ContextState(user_id=request.user_id, preferences=ContextPreferences(), dimensions=[]),
        )

    def search_traces(self, request: TraceSearchRequest) -> TraceListResponse:
        """
        Search recorded traces for a user by tags and time window.

        This is a best-effort helper built on top of the SQLite replay store; it
        filters events client-side based on metadata fields set by upstream
        services (e.g., origin_intent, tags, created_at).
        """
        all_traces = self._sqlite_replay.list(request.user_id).traces
        filtered: list[EventTrace] = []
        required_tags = request.tags or []
        since = request.since
        for trace in all_traces:
            meta = trace.metadata or {}
            tags = meta.get("tags") or []
            if required_tags:
                if not isinstance(tags, list) or not any(t in tags for t in required_tags):
                    continue
            if since and trace.timestamp < since:
                continue
            filtered.append(trace)
        limit = request.limit or 50
        return TraceListResponse(traces=filtered[:limit])


def register_routes(app: FastAPI, service: ContextGraphService, baton_manager: object | None = None) -> None:
    router = APIRouter()

    @router.get("/readyz")
    async def readyz() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/context/update", response_model=ContextStateResponse)
    async def update_context(request: ContextUpdateRequest) -> ContextStateResponse:
        state = service.update_state(request)
        return ContextStateResponse(state=state)

    @router.post("/context/query", response_model=ContextStateResponse)
    async def query_context(request: ContextQueryRequest) -> ContextStateResponse:
        try:
            state = service.get_state(request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Context not found") from exc
        return ContextStateResponse(state=state)

    @router.post("/traces/replay", response_model=ContextStateResponse)
    async def replay_trace(request: ReplayRequest) -> ContextStateResponse:
        state = service.replay(request)
        return ContextStateResponse(state=state)

    @router.post("/traces/search", response_model=TraceListResponse)
    async def search_traces(request: TraceSearchRequest) -> TraceListResponse:
        return service.search_traces(request)

    @router.get("/capabilities")
    async def get_capabilities(person_id: str | None = None) -> dict:
        if person_id:
            conn = sqlite3.connect(service.db_path, check_same_thread=False)
            cur = conn.cursor()
            cur.execute("SELECT manifest FROM capabilities_person WHERE person_id=?", (person_id,))
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                try:
                    return {"manifest": json.loads(row[0])}
                except Exception:
                    pass
        return {"manifest": service._capabilities}

    @router.post("/capabilities")
    async def set_capabilities(manifest: dict = Body(...), person_id: str | None = None) -> dict:
        # minimal validation: must include modalities
        if not isinstance(manifest, dict) or "modalities" not in manifest:
            raise HTTPException(status_code=400, detail="Invalid manifest")
        conn = sqlite3.connect(service.db_path, check_same_thread=False)
        cur = conn.cursor()
        if person_id:
            cur.execute(
                "INSERT INTO capabilities_person (person_id, manifest, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(person_id) DO UPDATE SET manifest=excluded.manifest, updated_at=excluded.updated_at",
                (person_id, json.dumps(manifest)),
            )
        else:
            service._capabilities = manifest
            cur.execute(
                "INSERT INTO capabilities (id, manifest, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(id) DO UPDATE SET manifest=excluded.manifest, updated_at=excluded.updated_at",
                (json.dumps(manifest),),
            )
        conn.commit()
        conn.close()
        return {"ok": True, "manifest": manifest, "person_id": person_id}

    @router.get("/durability/status")
    async def durability_status() -> dict:
        conn = sqlite3.connect(service.db_path, check_same_thread=False)
        status = service._durability.get_status(conn)
        conn.close()
        return status

    @router.post("/durability/run_ttl")
    async def run_ttl_cleanup() -> dict:
        conn = sqlite3.connect(service.db_path, check_same_thread=False)
        deleted = service._durability.ttl_manager.cleanup_expired(conn)
        metrics = service._durability.metrics.to_dict()
        conn.close()
        return {"deleted": deleted, "metrics": metrics}

    @router.post("/durability/run_pii")
    async def run_pii_scrubbing() -> dict:
        conn = sqlite3.connect(service.db_path, check_same_thread=False)
        scrubbed = service._durability.pii_scrubber.scrub_old_records(conn)
        metrics = service._durability.metrics.to_dict()
        conn.close()
        return {"scrubbed": scrubbed, "metrics": metrics}

    @router.get("/metrics")
    async def metrics() -> dict:
        conn = sqlite3.connect(service.db_path, check_same_thread=False)
        status = service._durability.get_status(conn)
        conn.close()
        return status.get("metrics", {})

    app.include_router(router)
