# Unison Project TODO

Prioritized follow-up tasks based on the latest review. Use the checkboxes to track progress.

## 1. Documentation & Tooling Hygiene _(last GitHub push: Section 1 complete on 2025-11-13)_
- [x] Normalize encoding across markdown/automation assets (remove mojibake in `unison-docs/README.md`, `unison-platform/Makefile`, etc.).
- [x] Add remark/misspell lint gates to `docs-lint.yml` and enforce in CI.
- [x] Refresh architecture/onboarding docs with an up-to-date repository + service map.

## 2. Service Modularization & Contracts
- [x] Break `unison-orchestrator/src/server.py` into packages (`api`, `policy_client`, `context_client`, `replay`, `telemetry`).
  - [x] Extracted telemetry + typed settings modules for orchestrator service.
  - [x] Added shared service client layer for context/policy/storage/inference calls.
  - [x] Moved policy + health evaluation helpers into dedicated orchestration services.
  - [x] Registered event/introspection/confirm/ingest routes via `orchestrator.api` module.
- [x] Apply the same modular structure to `unison-context-graph`, extracting durability/replay helpers.
- [x] Introduce typed configuration objects per service and validate at startup.
- [x] Added typed settings surface for `unison-context`.
- [x] Added typed settings surface for `unison-storage`.
- [x] Added typed settings surface for `unison-inference`.
- [x] Added typed settings + integration for `unison-policy`.
- [x] Added typed settings surface for `unison-consent`.
- [x] Mirrored typed settings + tests into `repos/unison-context`.
- [x] Added typed settings surface + tests for `repos/unison-orchestrator`.
- [x] Promote shared durability/replay utilities into `unison-common` for reuse.

## 3. Reliability & Observability Hardening
- [x] Ensure every inbound EventEnvelope path invokes `unison-common` validation before processing (see `EVENT_ENVELOPE_VALIDATION_AUDIT.md` and the new router regression test).
- [x] Extend tracing/consent propagation tests to cover orchestrator <-> policy <-> context flows end-to-end (validated via test_orchestrator_policy_context_tracing_and_consent).
- [x] Add integration tests for replay + WAL recovery using the durability plan and surface metrics to Grafana (tests/test_replay_wal_metrics.py, /metrics).

## 4. Workflow & Release Readiness
- [x] Move orchestration logic from the Makefile into reusable scripts (bash + PowerShell) invoked by `make` (`unison-platform/scripts/stack.sh` + `.ps1`).
- [x] Gate releases with combined docs lint, unit tests, contract tests, and devstack smoke deployment (`make release-gate` via `scripts/release-pipeline.*`).
- [x] Translate subsystem plan docs (identity, durability, phased deployment) into backlog issues with acceptance criteria (`RELIABILITY_BACKLOG.md`).
