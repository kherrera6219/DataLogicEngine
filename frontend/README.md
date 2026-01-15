# DataLogicEngine Frontend

Modern Next.js 16 frontend application for the Universal Knowledge Graph (UKG) system.

## Tech Stack

- **Framework**: [Next.js 16](https://nextjs.org/) (App Router)
- **React**: React 19
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 4.x
- **UI Components**: Shadcn UI (built on Radix UI)
- **Icons**: Lucide React
- **Data Fetching**: SWR for real-time updates and caching
- **API Communication**: Fetch API with Next.js rewrites

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

### Linting

```bash
npm run lint
```

## Application Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── (auth)/                # Auth group layout
│   │   ├── login/             # Login page
│   │   └── register/          # Registration page
│   ├── dashboard/             # Main dashboard
│   ├── chat/                  # Chat interface
│   ├── graph/                 # Knowledge graph visualization
│   ├── knowledge/             # Knowledge browser
│   ├── runs/                  # Trace runs explorer
│   ├── analytics/             # System analytics
│   ├── algorithms/            # Knowledge Algorithm browser
│   ├── admin/                 # Admin section
│   │   ├── compliance/        # Compliance audit
│   │   └── mcp/               # MCP server management
│   ├── settings/              # User settings
│   ├── profile/               # User profile
│   ├── about/                 # About page
│   ├── layout.tsx             # Root layout
│   ├── page.tsx               # Landing page
│   └── globals.css            # Global styles
│
├── components/                # React components
│   ├── Chat/                  # Chat components
│   ├── ui/                    # Base UI components (Shadcn)
│   ├── Graph/                 # Graph visualization
│   └── Analytics/             # Analytics widgets
│
├── lib/                       # Utilities & helpers
│   ├── api/                   # API client functions
│   │   ├── types.ts           # TypeScript interfaces
│   │   ├── trace.ts           # Trace API client
│   │   ├── auth.ts            # Auth API client
│   │   ├── mcp.ts             # MCP API client
│   │   ├── knowledge.ts       # Knowledge graph client
│   │   └── compliance.ts      # Compliance API client
│   └── utils.ts               # Utility functions
│
├── contexts/                  # React Context
├── public/                    # Static assets
├── next.config.ts             # Next.js configuration
├── tailwind.config.ts         # Tailwind configuration
├── tsconfig.json              # TypeScript configuration
└── package.json               # Dependencies
```

## Key Features

### Dashboard
- Real-time system monitoring
- System metrics and health status
- Quick access to all major features

### Chat Interface
- Interactive chat with UKG-enhanced LLMs
- Streaming responses
- Message history
- Trace ID linking for auditability

### Trace Explorer
- Comprehensive trace run visualization
- Stage-by-stage execution breakdown
- Evidence and claims viewer
- Persona and policy decision tracking
- Export functionality

### Knowledge Graph
- Interactive graph visualization
- Node and edge browser
- Search and filter capabilities
- Multi-dimensional axis navigation

### Admin Panel
- **Granular User Management**: Manage users, roles, and status (locked/active/admin).
- **RBAC Enforcement**: UI-level permission checks for sensitive operations.
- **LLM Provider Configuration**: Securely manage external model endpoints.
- **MCP Server Management**: Monitor and control MCP-compliant agents.
- **Compliance Dashboard**: Real-time status of security headers and audit logs.
- **Audit Log Export**: Comprehensive event extraction for auditors.

### Authentication & Security
- **Secure Auth Flow**: Session-based login with CSRF protection.
- **MFA Setup**: Guided TOTP setup with QR code and backup codes.
- **Account Lockout**: Automatic UI notification of temporary account suspension.
- **Strict Headers**: Integrated support for HSTS, CSP, and secure cookies.

### Analytics
- System performance metrics
- Usage statistics
- LLM provider analytics
- Knowledge Algorithm execution stats

## API Integration

The frontend communicates with the backend via API proxy configured in `next.config.ts`:

```typescript
rewrites: async () => [
  {
    source: '/api/:path*',
    destination: 'http://localhost:5000/api/:path*',
  },
],
```

This allows the frontend to make API calls to `/api/*` which are automatically proxied to the Flask backend.

## Environment Variables

Create a `.env.local` file (optional):

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Component Library

The application uses Shadcn UI components built on Radix UI primitives:

- Accessible by default
- Fully typed with TypeScript
- Customizable with Tailwind CSS
- Dark mode support

Common components:
- `Button`, `Input`, `Select`, `Card`
- `Dialog`, `Dropdown Menu`, `Tooltip`
- `Table`, `Tabs`, `Badge`
- And more in `components/ui/`

## Data Fetching

Uses SWR for data fetching with automatic:
- Revalidation
- Caching
- Real-time updates
- Error handling
- Loading states

Example:
```typescript
import useSWR from 'swr'

const { data, error, isLoading } = useSWR('/api/v1/trace/runs', fetcher)
```

## Styling

Tailwind CSS utility classes with custom configuration:

```typescript
// Example component
<div className="flex items-center justify-between p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
  <h2 className="text-xl font-semibold">Title</h2>
</div>
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
