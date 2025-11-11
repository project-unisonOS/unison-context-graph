# Consent Enforcement Rollout Guide

This guide explains how to enable and validate consent enforcement across services.

## Endpoints Enforcing Consent

- Orchestrator
  - POST /ingest → requires INGEST_WRITE
- Context
  - POST /kv/get → requires REPLAY_READ
  - POST /kv/put, /kv/set → require INGEST_WRITE
- Inference
  - POST /inference/request → requires REPLAY_READ

## Enabling the Feature

- Flag: `UNISON_REQUIRE_CONSENT`
- Default: `false` (staged rollout)
- Set to `true` per service to enforce consent in that service.

## Sending Consent in Requests

- Header options
  - `Authorization: Bearer <consent_token>`
  - Or `X-Consent-Grant: <consent_token>` when separate from auth

## Testing Locally

- Use a consent stub to simulate `/introspect` and route via `httpx.ASGITransport`.
- Example (pytest):
  - Monkeypatch `httpx.AsyncClient` to set `transport=ASGITransport(app=consent_app)` and `base_url`.
  - Send `Authorization: Bearer valid-*` tokens as in the service-level tests.

## CI Canary

- Canary job `tests-matrix-consent` runs for:
  - `unison-orchestrator`, `unison-context`, `unison-inference`
  - With `UNISON_REQUIRE_CONSENT=true`
- Main matrix remains with the flag off until canary is green.

## Rollout Steps

1) Local/staging
- Set `UNISON_REQUIRE_CONSENT=true` for target services.
- Verify endpoints return 403 without consent and 200 (or service-appropriate code) with valid consent.

2) CI Canary (enabled)
- Monitor canary job results; fix tests to include consent tokens if failures occur.

3) Global CI Flip
- Set `UNISON_REQUIRE_CONSENT=true` in main matrix env for all services.
- Keep a per-job override if needed during transition.

## Troubleshooting

- 403 Forbidden
  - Missing/invalid `Authorization` or `X-Consent-Grant` header
  - Insufficient scopes; verify token has the required scope
- Consent service errors
  - Tests should stub `/introspect` to avoid network dependencies
  - In production, check connectivity/health of the consent service and Redis revocation cache
