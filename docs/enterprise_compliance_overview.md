# Microsoft Enterprise Hardening Overview

This document summarizes the hardening work introduced to align the public web
application with Microsoft enterprise guidance.

## Configuration management

- Added `config/enterprise_settings.py` which centralizes strongly typed
  configuration handling and enforces secure defaults for production
  deployments.
- Standardized structured logging with correlation identifiers to support
  Microsoft 365 Defender and Azure Monitor ingestion pipelines.

## Security controls

- Introduced `backend/security/enterprise_security.py` to apply HTTP security
  headers, transport security, and host validation through `Flask-Talisman` in
  accordance with Microsoft SDL recommendations.
- Session cookies now default to `HttpOnly`, secure, and `SameSite=Lax` to
  reduce token exfiltration risk.

## Observability

- Added Azure Application Insights instrumentation via
  `backend/observability/app_insights.py` so production environments can stream
  telemetry to Azure Monitor.
- Implemented per-request correlation identifiers to make cross-system tracing
  easier when using Azure Monitor or Microsoft Sentinel.

## Operational logging

- Request lifecycle events are now captured with structured log messages that
  include correlation IDs and HTTP metadata, improving auditability and SOC
  readiness.
