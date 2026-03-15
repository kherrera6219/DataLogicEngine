# DataLogicEngine Frontend

Modern Next.js 16 frontend application for the Universal Knowledge Graph (UKG) system.

## Tech Stack

- **Framework**: [Next.js 16](https://nextjs.org/) (App Router)
- **React**: React 18.3
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 4.x (CSS-only config via `@import "tailwindcss"`)
- **UI Components**: Shadcn UI (built on Radix UI)
- **Icons**: Lucide React
- **Data Fetching**: SWR 2.x for caching and revalidation
- **API Communication**: Fetch API with Next.js rewrites
- **Desktop Shell**: Electron 40 (optional, Windows)
- **Charts**: Recharts 3.x
- **3D Graph**: Three.js + react-force-graph-3d

## Getting Started

### Prerequisites

- Node.js 18.17+
- npm or yarn
- Backend running on `http://localhost:5000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

### Electron Desktop Build

```bash
npm run electron:dev       # Dev mode (Next.js + Electron together)
npm run electron:dist      # Full Windows installer build
```

### Linting & Type Checking

```bash
npm run lint
npm run typecheck
```

## Application Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── (auth)/                 # Auth group layout
│   │   ├── login/              # Login page
│   │   └── register/           # Registration page
│   ├── dashboard/              # Main dashboard
│   ├── chat/                   # AI chat interface
│   ├── graph/                  # Knowledge graph (Three.js 3D)
│   ├── knowledge/              # Knowledge node/edge browser
│   ├── runs/                   # Trace runs explorer
│   │   └── view/               # Run detail view
│   ├── analytics/              # System analytics
│   ├── algorithms/             # Knowledge Algorithm browser
│   ├── simulations/            # Simulation management
│   ├── projects/               # Project management
│   │   └── [id]/               # Dynamic project detail
│   ├── mcp/                    # MCP connector registry
│   ├── truth-engine/           # Truth Engine monitoring
│   ├── admin/                  # Admin section
│   │   ├── compliance/         # Compliance audit
│   │   └── mcp/                # MCP server management
│   │       └── servers/        # Server list
│   ├── settings/               # User settings
│   │   └── privacy/            # Privacy settings
│   ├── profile/                # User profile
│   ├── about/                  # About page
│   │   ├── ai-limitations/     # AI limitations disclosure
│   │   └── cloud-services/     # Cloud services disclosure
│   ├── legal/
│   │   └── privacy/            # Privacy policy
│   ├── layout.tsx              # Root layout + all providers
│   ├── page.tsx                # Root redirect → /dashboard
│   └── globals.css             # Global styles + Fluent design tokens
│
├── components/                 # React components
│   ├── Chat/                   # ChatInterface, MessageBubble, TraceVisualizer,
│   │                           # LiveTracePanel, AdvancedControls, DetailedResponseView
│   ├── Dashboard/              # CommandBar, ComplianceTrendChart
│   ├── Graph/                  # AxisSelector
│   ├── layout/                 # AppSidebar (collapsible, localStorage-persisted)
│   ├── mcp/                    # McpHub, McpAnalytics, McpClientConfig,
│   │                           # McpServerConfig, McpIntegrationExamples
│   ├── projects/               # ProjectDetail
│   ├── settings/               # AiModelSettings, DatabaseSettings, ApiOverlayConfig
│   ├── feature-flags/          # FeatureFlagGate
│   ├── ui/                     # Base Shadcn primitives (Button, Card, Dialog,
│   │                           # Input, Table, Badge, Skeleton, etc.)
│   ├── AppInitializer.tsx      # Desktop auto-login + app bootstrap
│   ├── ClientErrorBootstrap.tsx# Client-side error reporting setup
│   ├── CloudDisclosureBanner.tsx# Feature-gated cloud dependency notice
│   ├── DesktopStatus.tsx       # Electron connection status indicator
│   ├── NavBar.tsx              # Top navigation bar
│   ├── PlaceholderPage.tsx     # Shared placeholder for in-progress sections
│   └── ThemeToggle.tsx         # Light/dark theme switch
│
├── lib/                        # Utilities & helpers
│   ├── api/                    # API client functions
│   │   ├── types.ts            # TypeScript interfaces for all API responses
│   │   ├── index.ts            # Base request handler + CSRF handling
│   │   ├── auth.ts             # Login, logout, session, desktop auto-login
│   │   ├── chat.ts             # Chat session and message API
│   │   ├── compliance.ts       # Compliance status API
│   │   ├── knowledge.ts        # Knowledge graph node/edge API
│   │   ├── mcp.ts              # MCP connector CRUD + OAuth flow
│   │   ├── simulation.ts       # Simulation management API
│   │   ├── system_chat.ts      # System-level chat API
│   │   └── trace.ts            # Trace run fetch + export
│   ├── feature-flags/
│   │   └── definitions.ts      # All feature flag definitions and defaults
│   ├── runtime/
│   │   └── policy.ts           # Runtime policy helpers
│   ├── security/
│   │   └── input-sanitization.ts # Client-side input sanitization
│   ├── state/
│   │   └── storage.ts          # Persistent client state helpers
│   ├── telemetry/
│   │   └── client-errors.ts    # Client error telemetry
│   ├── socket.ts               # Socket.io client (real-time updates)
│   └── utils.ts                # Utility functions (cn, etc.)
│
├── contexts/                   # React Context providers
│   ├── AuthContext.tsx          # Auth state + login/logout actions
│   ├── ThemeContext.tsx         # Light/dark theme management
│   └── FeatureFlagContext.tsx   # Runtime feature flag overrides
│
├── electron/                   # Electron desktop shell
│   ├── main.ts                 # Main process, BrowserWindow, IPC
│   └── preload.ts              # Context bridge for safe IPC exposure
│
├── public/                     # Static assets
├── next.config.ts              # Next.js configuration (CDN, API proxy, Electron export)
├── tsconfig.json               # TypeScript configuration
└── package.json                # Dependencies
```

## Root Layout Provider Stack

`app/layout.tsx` composes providers in this order (outer → inner):

```
FeatureFlagProvider
  └── ClientErrorBootstrap (side-effect only)
  └── ThemeProvider
        └── SWRConfig (global SWR settings)
              └── AuthProvider
                    └── AppInitializer (desktop auto-login + health check)
                          └── ToastProvider
                                └── ApiErrorBoundary
                                      ├── AppSidebar
                                      ├── CloudDisclosureBanner (feature-gated)
                                      ├── NavBar
                                      └── <main> {children}
```

## Key Features

### Dashboard
- Real-time system monitoring
- Compliance trend chart
- Quick-access command bar

### Chat Interface
- Interactive chat with UKG-enhanced LLMs
- Streaming responses
- Message history
- Trace ID linking for auditability
- Advanced model control panel
- Detailed response view with evidence

### Trace Explorer
- Comprehensive trace run visualization
- Stage-by-stage execution breakdown
- Evidence and claims viewer
- Persona and policy decision tracking
- Export functionality

### Knowledge Graph
- Interactive 3D graph visualization (Three.js + react-force-graph-3d)
- Node and edge browser
- Search and filter capabilities
- 17-axis coordinate navigation

### Truth Engine Monitor
- Real-time Truth Engine execution status
- Tier routing visibility

### Simulations
- Simulation configuration and launch
- Results and status tracking

### Projects
- Project CRUD
- Per-project detail view with run history

### MCP Hub
- Connector registry
- OAuth token management
- Analytics per connector
- Server configuration

### Admin Panel
- **Granular User Management**: Manage users, roles, and status (locked/active/admin).
- **RBAC Enforcement**: UI-level permission checks for sensitive operations.
- **LLM Provider Configuration**: Securely manage external model endpoints.
- **MCP Server Management**: Monitor and control MCP-compliant agents.
- **Compliance Dashboard**: Real-time status of security headers and audit logs.
- **Audit Log Export**: Comprehensive event extraction for auditors.

### Authentication & Security
- **Secure Auth Flow**: Session-based login with CSRF protection.
- **Desktop Auto-Login**: Windows identity-based silent login via `AppInitializer`.
- **MFA Setup**: Guided TOTP setup with QR code and backup codes.
- **Account Lockout**: Automatic UI notification of temporary account suspension.
- **Strict Headers**: Integrated support for HSTS, CSP, and secure cookies.

### Feature Flags

Runtime-controlled flags defined in `lib/feature-flags/definitions.ts`:

| Flag | Default | Local Override |
|------|---------|---------------|
| `cloudDisclosureBanner` | `true` | Yes |
| `strictInputSanitization` | `true` | No |
| `storyA11yChecks` | `true` | Yes |
| `visualRegressionGate` | `true` | Yes |
| `enterpriseThemeOverrides` | `true` | Yes |

### Analytics
- System performance metrics
- Usage statistics
- LLM provider analytics
- Knowledge Algorithm execution stats

## API Integration

The frontend communicates with the backend via a Next.js API proxy configured in `next.config.ts`:

```typescript
rewrites: async () => [
  {
    source: '/api/:path*',
    destination: 'http://127.0.0.1:5000/api/:path*',
  },
],
```

All API calls go to `/api/v1/*` relative paths. The proxy is only active in `standalone` mode (web); in `electron` export mode, the Electron app communicates directly with the backend.

CSRF tokens are fetched automatically by the base request handler in `lib/api/index.ts`.

## Environment Variables

Create a `.env.local` file (optional):

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_CDN_URL=                     # Optional CDN prefix for static assets
ANALYZE=true                             # Enable bundle analyzer
```

## Design System Patterns

Every authenticated page follows a consistent Fluent layout convention:

```tsx
<div className="min-h-full bg-background text-foreground font-sans">
  <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">

    {/* Sticky acrylic topbar */}
    <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10
                    flex items-center justify-between px-8 backdrop-blur-3xl">
      {/* Page icon, title, subtitle, and optional action button */}
    </div>

    {/* Content area */}
    <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">
      {/* Page content */}
    </div>
  </div>
</div>
```

**CSS utility classes** (defined in `globals.css`):
- `.fluent-acrylic` — backdrop-blur + semi-transparent background (sidebar + topbars)
- `.fluent-mica` — flat surface background (secondary panels)
- `.fluent-card` — elevated card with border, shadow, and hover lift
- `.glass-card` — glass morphism variant (auth pages)
- `.animate-connected-enter` — page entrance animation (fade-in + slide up)
- `.reveal-hover` — shimmer sweep effect on hover
- `.no-scrollbar` — hide native scrollbar (Firefox + WebKit)

**Topbar icon accent colors by section:**
| Page | Icon Color |
|------|-----------|
| Dashboard | `text-blue-400` + `bg-blue-500/10` |
| Analytics | `text-purple-400` + `bg-purple-500/10` |
| Knowledge | `text-blue-400` + `bg-blue-500/10` |
| Simulations | `text-blue-400` + `bg-blue-500/10` |
| MCP Hub | `text-emerald-400` + `bg-emerald-500/10` |
| Projects | `text-blue-400` + `bg-blue-500/10` |
| Admin | `text-red-500` + `bg-red-900/10` |
| Settings | `text-slate-400` |

## Styling

Tailwind CSS 4.x — configuration is CSS-only (no `tailwind.config.ts`):

```css
/* globals.css */
@import "tailwindcss";
@plugin "tailwindcss-animate";
@import "./generated-tokens.css";
```

Design tokens from `generated-tokens.css` define semantic colors (`--background`, `--foreground`, `--accent`, etc.) and the Fluent-inspired surface materials (`.fluent-card`, `.fluent-acrylic`, `.fluent-mica`).

Font: **Inter** (loaded via `next/font/google` in `app/layout.tsx`).

## Component Library

The application uses Shadcn UI components built on Radix UI primitives:

- Accessible by default (ARIA, keyboard navigation)
- Fully typed with TypeScript
- Customizable with Tailwind CSS
- Dark mode support via `ThemeProvider`

Common components in `components/ui/`:
- `Button`, `Input`, `Select`, `Card`, `Badge`
- `Dialog`, `Alert Dialog`, `Sheet`
- `DropdownMenu`, `Tooltip`
- `Table`, `Tabs`, `Separator`
- `Skeleton`, `Progress`, `Slider`
- `ScrollArea`, `Avatar`
- `ApiErrorBoundary` (wraps module sections)
- `PageLayout`, `Breadcrumbs`

## Data Fetching

Uses SWR for data fetching with global config in `app/layout.tsx`:

```typescript
<SWRConfig value={{
  revalidateOnFocus: false,
  revalidateOnReconnect: true,
  dedupingInterval: 3000,
  errorRetryCount: 3,
  shouldRetryOnError: true
}}>
```

Example:
```typescript
import useSWR from 'swr'

const { data, error, isLoading } = useSWR('/api/v1/trace/runs', fetcher)
```

## Type Safety

All API responses are typed using TypeScript interfaces in `lib/api/types.ts`:

```typescript
interface TraceRun {
  run_id: string;
  status: 'pass' | 'fail' | 'pending';
  created_at: string;
  scores: {
    confidence: number;
    entropy: number;
  };
}
```

## Testing

```bash
npm run test              # Unit tests (Vitest)
npm run test:watch        # Watch mode
npm run test:coverage     # Coverage report
npm run test:a11y:ci      # Accessibility CI scan (axe-core)
npm run test:e2e          # Playwright Electron E2E tests
npm run test:e2e:visual   # Visual regression tests
npm run storybook         # Storybook component explorer
```

Tests use Vitest + Testing Library. Storybook runs on port 6006 with a11y and interaction addons.

## Contributing

1. Follow the existing code structure
2. Use TypeScript for type safety
3. Follow the component naming convention (PascalCase)
4. Use Tailwind CSS for styling
5. Ensure components are accessible
6. Test in both light and dark modes

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Shadcn UI](https://ui.shadcn.com)
- [SWR Documentation](https://swr.vercel.app)
- [Radix UI](https://www.radix-ui.com)

## License

PolyForm Noncommercial License 1.0.0. See the root [LICENSE](../LICENSE).
