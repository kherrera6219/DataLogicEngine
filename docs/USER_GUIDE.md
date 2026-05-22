# DataLogicEngine User Guide

## Purpose

Task-focused usage instructions for day-to-day operation.

## Audience

1. Analysts and operators
2. Admin users
3. Pilot users validating workflows

## Prerequisites

1. Running local or deployed instance
2. Internet access for provider inference
3. At least one provider API key

## Mode Behavior

1. Web mode: use `/login` for authenticated access.
2. Desktop mode: app boots directly into internal dashboard (no login screen).

## Primary Navigation

| Route | Use |
|---|---|
| `/dashboard` | Operational overview and quick actions |
| `/chat` | AI conversation and uploads |
| `/projects` | Session list/workspace |
| `/projects/view?id=<session_id>` | Session detail timeline |
| `/simulations` | Simulation runs |
| `/runs` | Trace/run history |
| `/runs/view?id=<run_id>` | Trace detail |
| `/graph` | Knowledge graph exploration |
| `/settings` | API, storage, AI model, and preferences |
| `/settings/privacy` | Export/delete local profile data |
| `/admin` | Admin telemetry/user views (role gated) |
| `/admin/mcp/servers` | MCP server registry management |

## Core Workflows

### 1. Configure provider access

1. Open `/settings` and select `API Gateway`.
2. Choose provider and model.
3. Enter API key.
4. Select `Save Key`.
5. Select `Test Connection`.

### 2. Configure AI model defaults

1. Open `/settings` and select `AI Models`.
2. Select provider and model.
3. Enter API key and select `Save Model`.
4. Select `Test Model` to validate model-level access.

### 3. Start chat and upload workflow

1. Open `/chat`.
2. Enter prompt and send.
3. Use upload actions to attach supported files.
4. Review trace details from run/session links.

### 4. Review and manage sessions

1. Open `/projects`.
2. Search by title or ID.
3. Open `/projects/view?id=<session_id>` for message-level review.

### 5. Run storage checks and lifecycle actions

1. Open `/settings` and select `Storage`.
2. Use `Refresh` for current health.
3. Use `Test Connection` per service.
4. Use `Start All` / `Stop All` for local data services.
5. Use auto-start toggle for local launch behavior.

### 6. Use privacy tools

1. Open `/settings/privacy`.
2. Use `Export My Data` for JSON export.
3. Use delete action with confirmation for local data removal.

## Known Limitations

1. Manual accessibility and failure-mode validation evidence remains open in `TODO.md`.
2. `/register` redirects to `/dashboard` in the current local-first build; self-service registration is disabled unless web mode is reopened as a product requirement.
3. Release builds still require trusted production code-signing evidence before public distribution.

## Validation Checklist

1. Dashboard loads without route errors.
2. Chat returns provider response after key setup.
3. Projects list and detail pages show session data.
4. Runs and trace detail pages render successfully.
5. Storage status panel returns service state.
6. Admin route loads for admin/owner users.

## Troubleshooting

1. API test fails:
   Re-save key and re-run provider test in settings.
2. Desktop shows login unexpectedly:
   Verify desktop runtime and loopback desktop header path.
3. Storage offline:
   Start local services and refresh storage panel.
4. Route redirects incorrectly in web mode:
   Re-authenticate and verify session cookie state.

## Related Documents

1. `docs/PRODUCT_OVERVIEW.md`
2. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
3. `docs/PRIVACY_POLICY.md`
4. `docs/API.md`

## Document Control

1. Owner: Product Operations
2. Last updated: 2026-05-22
3. Status: Active
4. Review cadence: Every 30 days
