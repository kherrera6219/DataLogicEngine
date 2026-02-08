# DataLogicEngine user guide

## Purpose

Provide practical, task-focused instructions for using DataLogicEngine in day-to-day operations.

## Audience

1. Analysts and operators
2. Team leads reviewing traces and simulations
3. Admin users managing access and MCP endpoints
4. Pilot users evaluating product capabilities

## Prerequisites

1. Running local stack or deployed environment
2. Internet access for model inference
3. At least one provider API key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, or equivalent)
4. User account and session for web mode, or desktop runtime for no-login mode

## Document control

1. Owner: Product Operations
2. Last updated: 2026-02-08
3. Status: Active
4. Review cadence: Every 30 days

## Related documents

1. `docs/PRODUCT_OVERVIEW.md`
2. `docs/PRODUCT_DESIGN.md`
3. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
4. `docs/PRIVACY_POLICY.md`

## Getting started

For Windows 11 local bring-up, follow:

1. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
2. `scripts/windows/start_local_stack.ps1`

After startup:

1. Frontend: `http://127.0.0.1:3000`
2. Backend health: `http://127.0.0.1:5000/health`

## Sign-in behavior by mode

1. Web mode:
   Open `/login` and authenticate with username/password.
2. Desktop mode:
   App can auto-login using Windows identity and open directly to operational routes.

## Navigation map

| Route | What you use it for | Key actions |
|---|---|---|
| `/dashboard` | Daily operations view | Check activity, status cards, quick links |
| `/chat` | Main AI workspace | Ask questions, upload files, toggle quad mode |
| `/projects` | Session workspace list | Search sessions, open detail views |
| `/projects/view?id=<session_id>` | Session detail | Review message timeline and session stats |
| `/simulations` | Simulation operations | Create runs, monitor progress, step active runs |
| `/runs` | Trace history | Open execution traces for audits or analysis |
| `/runs/view?id=<run_id>` | Trace detail | Inspect stages, personas, and axis data |
| `/graph` | Knowledge graph explorer | Filter nodes, inspect metadata, adjust view |
| `/settings` | Personal and system settings | Theme, API gateway, storage configuration |
| `/settings/privacy` | Privacy controls | Export data or delete local profile/data |
| `/mcp` | MCP integration workspace | Review hub views and integration examples |
| `/admin` | Admin-only controls | Manage users and system-level views |
| `/admin/mcp/servers` | Admin MCP registry | View and remove registered MCP servers |

## Core workflows

### 1. Configure AI provider access

1. Open `/settings`.
2. Select `API Gateway`.
3. Choose a provider.
4. Enter the API key and select `Test`.
5. Confirm status changes to connected.

### 2. Start an AI session

1. Open `/chat`.
2. Select `New Chat`.
3. Enter a prompt and select `Send`.
4. Optional:
   Toggle quad mode with the bolt icon for enhanced reasoning.
5. Optional:
   Attach document or video files for processing.

### 3. Review and organize session history

1. Open `/projects`.
2. Search for a session by title or ID.
3. Open the session from the card grid.
4. Use `/projects/view?id=<session_id>` for message-level review.

### 4. Run simulations

1. Open `/simulations`.
2. Select `New Simulation`.
3. Monitor live status and progress.
4. Use row action buttons to step active simulations when needed.

### 5. Inspect traces for auditability

1. Open `/runs`.
2. Select `View Trace` on a run.
3. Review run details, stage output, and persona/axis context.

### 6. Explore the knowledge graph

1. Open `/graph`.
2. Select axis and filter settings from the left panel.
3. Select a node to open detailed inspector data in the right panel.
4. Use camera controls to reset or adjust visualization context.

### 7. Validate local data services

1. Open `/settings`.
2. Select `Storage`.
3. Use `Refresh` to read current service health.
4. Use `Test Connection` per service as needed.
5. Use `Start All` or `Stop All` for local service lifecycle controls.

### 8. Use privacy controls

1. Open `/settings/privacy`.
2. Select `Export My Data` for a JSON export.
3. For destructive cleanup, select `Delete My Account and Data` and confirm.

### 9. Admin-only tasks

1. Open `/admin` (requires `owner` or `admin` role).
2. Review system and user management panels.
3. Open `/admin/mcp` and `/admin/mcp/servers` for MCP registry operations.

## Theme and navigation behavior

1. Dark mode is the default theme.
2. Theme can be changed in `Settings > General`.
3. Main left sidebar can be collapsed and expanded with the sidebar toggle button.
4. Settings sidebar has its own independent collapse control.

## Known limitations

1. `Settings > Notifications` and `Settings > AI Models` are not fully implemented.
2. Register page UI is present but does not currently submit registration requests.
3. Some MCP and admin metrics are demo values while integration work continues.
4. Some action buttons are visible placeholders without backend execution.

## Validation checklist

1. Dashboard loads without errors.
2. Chat returns responses after provider key configuration.
3. Projects list and session detail views render session history.
4. Simulations page creates and updates runs.
5. Runs and run detail pages display trace data.
6. Storage tab returns health status for configured services.

## Troubleshooting

1. Login redirects repeatedly:
   Verify session cookies and backend auth status (`/api/v1/auth/check`).
2. Desktop does not bypass login:
   Verify desktop runtime conditions and loopback desktop header behavior.
3. Chat fails with provider errors:
   Re-test provider key in settings and validate key status with `scripts/verify_api_keys.py`.
4. Storage services show offline:
   Check local ports and optional Docker service state before re-testing.
