# unison-context-graph

Operational context-state, replay, capability-manifest, and actuation-telemetry adapter for UnisonOS.

## Status
Active adapter. As of Phase 2, `unison-context` and its `/v2` governed repository
are authoritative for relationships, context spaces, memory, charters, goals,
commitments, membership, retention, and export. This service may retain bounded
operational/replay data, but it must not become an independent personal-memory
authority or infer access from a relationship edge.

## What is implemented
- `ContextGraphService` for per-user context state updates and queries.
- SQLite-backed replay storage with durability hooks from `unison-common`.
- Trace replay and trace search endpoints.
- Capability manifest persistence in SQLite, including a default seeded manifest.
- Actuation telemetry ingestion for lifecycle events.
- Optional Neo4j readiness checks when `GRAPH_DB_*` variables are configured.

## API surface
- `GET /healthz`
- `GET /authority`
- `GET /readyz`
- `POST /telemetry/actuation`
- `POST /context/update`
- `POST /context/query`
- `POST /graph/nodes`
- `POST /graph/relations`
- `POST /traces/replay`
- `POST /traces/search`
- `GET /capabilities`
- `POST /capabilities`
- `GET /durability/status`
- `POST /durability/run_ttl`
- `POST /durability/run_pii`
- `GET /metrics`

## Request model notes
- Context update/query payloads use `user_id`, not `person_id`.
- Replay payloads use `user_id` plus a `trace` array of event records.
- Capability manifests are stored as raw JSON payloads.

## Run locally
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -c ../constraints.txt -r requirements.txt
cp .env.example .env
python src/main.py
```

## Key configuration
- `CONTEXT_GRAPH_HOST`, `CONTEXT_GRAPH_PORT`
- `CONTEXT_GRAPH_DB_PATH`
- `ALLOWED_ORIGINS`
- `GRAPH_DB_URI`, `GRAPH_DB_USER`, `GRAPH_DB_PASSWORD`
- `DURABILITY_*` settings consumed via `unison-common`

## Related docs
- `REPLAY_README.md`
- `docs/DURABILITY.md`
- `docs/PRIVACY.md`

## Tests
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -c ../constraints.txt -r requirements.txt
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OTEL_SDK_DISABLED=true python -m pytest
```
