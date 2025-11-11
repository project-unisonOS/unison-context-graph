# Observability: Dashboards and Runbooks

This folder contains example dashboards and runbooks to help operate Unison services with tracing and structured logs.

- grafana-tracing-dashboard.json
  Example Grafana dashboard focusing on tracing metrics (rates, errors) and request correlation.
- runbooks.md
  Short playbooks for common operational scenarios.

Recommendations
- Set OTEL_SERVICE_NAME per service and use deployment.environment to scope dashboards.
- Ensure logs include request_id/trace_id/traceparent for correlation (already provided by log_json).
