# UI Placeholder Audit

Date: 2026-05-23

## Scope

Reviewed the release-facing MCP, admin, and shared toolbar surfaces for static metrics, inert controls, and placeholder-only panels.

## Findings And Disposition

| Surface | Finding | Disposition |
| --- | --- | --- |
| `frontend/components/Dashboard/CommandBar.tsx` | Application launcher, search, help, settings, export/history, and profile controls needed explicit destinations. Legacy Excel/BI and notification controls did not have backed release routes. | Wired available destinations to Dashboard, Graph search, About, Tools History, Settings, and Profile. Removed unsupported Excel/BI and notification actions from the release toolbar. |
| `frontend/components/mcp/McpIntegrationExamples.tsx` | LangChain tab showed a coming-soon placeholder and documentation/support buttons were inert. | Replaced the placeholder with a concrete LangChain tool example and removed inert buttons. |
| `frontend/app/admin/page.tsx` | User table exposed an action menu without an implemented user-management operation. | Removed the unsupported actions column so the page reflects live read-only admin telemetry. |
| `frontend/app/admin/mcp/page.tsx` | MCP metrics load from `/api/v1/mcp/stats`; zero values are fallback states after API errors, not hard-coded release metrics. | No code change required. |
| `frontend/app/admin/mcp/servers/page.tsx` | Server registry loads, creates, refreshes, and deletes via MCP API methods. | No code change required. |
| `frontend/app/mcp/page.tsx` and MCP child components | Hub, server config, client tools, analytics, and integration tabs use live API calls or concrete examples. | Placeholder integration panel fixed in this pass. |

## Remaining Release Notes

No release-blocking placeholder controls remain in the audited surfaces. Future user-management write operations should add backed endpoints and tests before returning row-level action menus.
