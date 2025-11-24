"""Replay storage utilities (in-memory and SQLite-backed)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from unison_common.durability import DurabilityManager

from .models import ContextPreferences, ContextState, ContextStateResponse
from .models import EventTrace, ReplayRequest, TraceListResponse


class ReplayStore:
    def __init__(self) -> None:
        self._events: Dict[str, List[EventTrace]] = {}
        self._states: Dict[str, ContextState] = {}

    def record(self, user_id: str, trace: List[EventTrace]) -> None:
        existing = self._events.setdefault(user_id, [])
        existing.extend(trace)

    def list(self, user_id: str) -> TraceListResponse:
        return TraceListResponse(traces=self._events.get(user_id, []))

    def apply(self, request: ReplayRequest) -> TraceListResponse:
        self.record(request.user_id, request.trace)
        return self.list(request.user_id)


class SQLiteReplayStore:
    """SQLite-backed replay store that works with durability utilities."""

    def __init__(self, db_path: Path, durability: DurabilityManager) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.durability = durability
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS event_traces (
                trace_id TEXT PRIMARY KEY,
                person_id TEXT NOT NULL,
                session_id TEXT,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_data TEXT NOT NULL,
                context_snapshot TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                scrubbed_at TEXT
            )
            """
        )
        self.conn.commit()
        self.durability.initialize(self.conn)

    def _upsert_state(self, user_id: str, trace: List[EventTrace]) -> ContextState:
        # Keep a simple local state for responses
        preferences = ContextPreferences()
        state = ContextState(user_id=user_id, preferences=preferences, dimensions=[])
        return state

    def record(self, user_id: str, trace: List[EventTrace]) -> None:
        cursor = self.conn.cursor()
        expires_at = self.durability.ttl_manager.calculate_expiry()
        for event in trace:
            trace_id = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO event_traces (
                    trace_id, person_id, session_id, event_type, timestamp,
                    event_data, context_snapshot, expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    user_id,
                    None,
                    event.event,
                    event.timestamp.isoformat(),
                    json.dumps(event.metadata or {}),
                    None,
                    expires_at,
                ),
            )
        self.conn.commit()
        self.durability.on_transaction(self.conn)

    def list(self, user_id: str) -> TraceListResponse:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT timestamp, event_type, event_data FROM event_traces WHERE person_id = ? ORDER BY timestamp",
            (user_id,),
        )
        rows = cursor.fetchall()
        traces: List[EventTrace] = []
        for row in rows:
            traces.append(
                EventTrace(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    event=row["event_type"],
                    metadata=json.loads(row["event_data"] or "{}"),
                )
            )
        return TraceListResponse(traces=traces)

    def apply(self, request: ReplayRequest) -> TraceListResponse:
        self.record(request.user_id, request.trace)
        return self.list(request.user_id)

    def close(self) -> None:
        try:
            self.durability.shutdown(self.conn)
            self.conn.close()
        except Exception:
            pass
