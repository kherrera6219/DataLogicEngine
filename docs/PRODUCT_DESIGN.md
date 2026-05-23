# DataLogicEngine product design

## Purpose

Define the current UX architecture, route model, interaction patterns, and design guardrails for DataLogicEngine.

## Audience

1. Product designers
2. Frontend engineers
3. QA and accessibility reviewers
4. Product and release managers

## Prerequisites

1. Access to a running frontend (`http://127.0.0.1:3000`)
2. Access to the frontend codebase (`frontend/app`, `frontend/components`)
3. Access to route policy scripts in `scripts/windows`

## Document control

1. Owner: Product Design and Frontend Engineering
2. Last updated: 2026-05-23
3. Status: Active
4. Review cadence: Every 30 days

## Related documents

1. `docs/PRODUCT_OVERVIEW.md`
2. `docs/USER_GUIDE.md`
3. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
4. `TODO.md`

## Design principles

1. Dark-first operations with readable light-mode parity.
2. Task-first navigation centered on chat, projects, simulations, and traces.
3. Progressive disclosure through collapsible sidebars, tabs, and detail panels.
4. Local-first posture with explicit cloud disclosure and privacy controls.
5. Role-aware access for admin capabilities.

## Information architecture

### Public surfaces

| Route | Purpose |
|---|---|
| `/` | Landing and capability entry points |
| `/about` | Product and architecture narrative |
| `/about/ai-limitations` | AI transparency and limitations |
| `/about/cloud-services` | Cloud dependency and data residency disclosure |
| `/legal/privacy` | Privacy policy and user rights |
| `/login` | Web mode authentication entry point |
| `/register` | Disabled in the current local-first build; redirects to `/dashboard` |

### Authenticated operator surfaces

| Route | Purpose |
|---|---|
| `/dashboard` | Operational overview and activity feed |
| `/chat` | Primary AI interaction workspace |
| `/projects`, `/projects/view` | Session browsing and message history |
| `/graph` | 3D knowledge graph exploration |
| `/simulations` | Simulation lifecycle monitoring |
| `/runs`, `/runs/view` | Reasoning trace history and detail |
| `/settings`, `/settings/privacy` | API/storage config, theme, and privacy controls |
| `/mcp` | MCP ecosystem hub and integration UI |
| `/knowledge`, `/analytics`, `/algorithms`, `/truth-engine`, `/profile` | Specialist views with mixed data maturity |

### Admin surfaces

| Route | Purpose |
|---|---|
| `/admin` | Role-gated admin dashboard |
| `/admin/compliance` | Compliance dashboard |
| `/admin/mcp` | MCP system status |
| `/admin/mcp/servers` | MCP server registry CRUD |

## Shell and layout system

1. Global shell:
   `RootLayout` composes `AppSidebar`, `NavBar`, `CloudDisclosureBanner`, and routed page content.
2. Primary navigation:
   `AppSidebar` is collapsible and persisted via `localStorage` key `ukg.sidebar.collapsed`.
3. Secondary navigation:
   `NavBar` exposes top-level links, cloud status, theme toggle, and user menu.
4. Page-level workspace panels:
   Chat uses left session rail and right trace rail; graph and settings include local collapsible side panels.

## Access and routing policy

1. Protected-route policy is enforced in `frontend/proxy.ts`.
2. Public routes include landing, auth, about, and legal pages.
3. Desktop requests can bypass login when loopback + desktop signal conditions are met.
4. Browser requests without auth session redirect to `/login?callbackUrl=...`.

## Performance and lazy-loading model

| Route | Lazy-loaded unit | Benefit |
|---|---|---|
| `/chat` | `ChatInterface` | Defers heavy chat workspace code from initial route load |
| `/settings` | `ApiOverlayConfig`, `DatabaseSettings` | Defers advanced config modules until needed |
| `/mcp` | All major tab panels | Reduces first paint and tab-switch load overhead |
| `/graph` | `react-force-graph-3d` | Avoids SSR failures and large initial JS cost |
| Global | `app/loading.tsx`, route `loading.tsx` files | Provides explicit loading affordances during transitions |

## UX state model

1. Authentication state is managed in `AuthContext` with desktop auto-login fallback logic.
2. Theme state is managed in `ThemeContext`; default theme is dark unless user override exists.
3. API data is fetched through `frontend/lib/api/*` with session-aware request behavior.
4. Real-time updates use websocket hooks for chat responses and simulation progress.

## Accessibility baseline

1. Global skip link is provided in the root layout.
2. Navigation and panel toggle buttons include explicit `aria-label` metadata.
3. Loading states and empty states are present on major data pages.
4. Light-mode readability was improved on primary operational surfaces in the February 2026 UX pass.

## Known UX debt

UX debt and product backlog items are consolidated in the root `TODO.md`. This design guide documents the current UX model and validation approach.

## Validation

Use these commands for route and UX validation:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\test_frontend_route_policy.ps1 -FrontendPort 3000
cd frontend
npm run test:e2e:visual
```

## Troubleshooting

1. If protected pages show unexpected redirects, verify auth cookies and desktop header conditions.
2. If graph or heavy views stall, check browser console for API or websocket connectivity failures.
3. If light mode appears unreadable, confirm latest frontend assets and cleared browser cache.
