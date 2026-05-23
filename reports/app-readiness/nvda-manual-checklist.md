# NVDA Manual Screen Reader Checklist

Status: Not executed in this environment. NVDA was not found on the local PATH or under Program Files during the May 23, 2026 repo pass.

Use this checklist for the manual Windows accessibility pass before release:

1. Install or launch NVDA on Windows.
2. Start the packaged DataLogicEngine desktop app.
3. Verify the dashboard announces the page heading, sidebar navigation, primary actions, and status content in reading order.
4. Navigate with Tab and Shift+Tab through `/dashboard`, `/chat`, `/settings`, `/settings/privacy`, and `/admin/mcp/servers`.
5. Confirm controls announce accessible names, roles, and state changes for sidebar toggles, settings section buttons, privacy export/delete actions, provider test actions, and modal/dialog flows.
6. Confirm toast/status feedback is reachable or announced after export, provider test, storage health, and failure-mode actions.
7. Record pass/fail findings, NVDA version, Windows version, app version, tester, date, and any remediation links.

Release readiness remains open until this checklist is executed and the results are saved under `reports/app-readiness/`.
