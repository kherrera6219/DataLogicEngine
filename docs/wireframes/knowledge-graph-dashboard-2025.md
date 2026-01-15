# Knowledge Graph & Dashboard Wireframes - 2025 Design

## Overview
Interactive knowledge graph visualization with 17-axis navigation, real-time data exploration, and comprehensive compliance dashboard with modern data visualization.

## Microsoft Enterprise Updates (Fluent 2)
- Fluent command bar at top with app launcher, environment selector (Prod/Sandbox), search, help, notifications, and presence.
- Segoe UI Variable typography and Fluent neutral cards for graph controls and dashboard widgets; focus-visible rings on all filters and sliders.
- Export controls updated to "Open in Excel", "Export to Power BI", and "Download CSV" to match Microsoft enterprise workflows.
- Compliance dashboard includes "Data residency" and "Sensitivity label" badges (Purview-style) plus privacy/terms links in the footer.

### Fluent Command Bar Overlay
```
┌ waffle │ Knowledge Graph │ Environment: Prod │ Search nodes... │ Open in Excel │ Help │ 🔔 │ 👤 │ ⋮ ┐
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Knowledge Graph Explorer - Desktop (1920x1080)

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ [Logo] Knowledge Graph Explorer                          [🔍] [⚙️ Settings] [👤 User] [🔔 Notif]      ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ AXIS SELECTOR (100%)                                                                                   ║
║ ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐ ║
║ │ [1]      [2]       [3]        [4]        [5]       [6]        [7]       [8]       [9]     ...     │ ║
║ │ Pillars  Hierarchy Honeycomb  Workflows  Algorithms Regulatory Compliance Location Industry [13]  │ ║
║ │   ●        ○         ○          ○          ○          ○          ○         ○        ○       ○     │ ║
║ └────────────────────────────────────────────────────────────────────────────────────────────────────┘ ║
║  ↑ Horizontal scrollable tabs with active indicator                                                   ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                        ║
║ SIDEBAR (320px)    │              GRAPH VISUALIZATION AREA (1280px)            │  DETAILS (320px)     ║
║ ════════════       │              ═══════════════════════════════              │  ════════════        ║
║                    │                                                            │                      ║
║ Axis 1: Pillars    │  ╔════════════════════════════════════════════════════╗   │  Selected Node       ║
║ ───────────────    │  ║                                                    ║   │  ──────────────      ║
║                    │  ║                    ┌─────┐                         ║   │                      ║
║ 🔍 [Search...]     │  ║              ┌────│  A  │────┐                     ║   │  📊 Knowledge Pillar ║
║                    │  ║              │    └─────┘    │                     ║   │                      ║
║ Filters            │  ║          ┌───┴───┐       ┌───┴───┐                ║   │  **ID**: KP-001      ║
║ ───────            │  ║      ┌──│   B   │       │   C   │──┐             ║   │  **Name**: Federal   ║
║                    │  ║      │  └───────┘       └───────┘  │             ║   │  Acquisition Regs    ║
║ Node Type:         │  ║  ┌───┴───┐                     ┌───┴───┐         ║   │                      ║
║ ☑ Pillars          │  ║  │   D   │                     │   E   │         ║   │  **Type**: Core      ║
║ ☑ Sub-pillars      │  ║  └───┬───┘                     └───┬───┘         ║   │  **Status**: Active  ║
║ ☑ Topics           │  ║      │  ┌───────┐       ┌───────┐  │             ║   │                      ║
║ ☐ Entities         │  ║      └──│   F   │       │   G   │──┘             ║   │  Connected Nodes:    ║
║                    │  ║         └───┬───┘       └───┬───┘                ║   │  • FAR (12)          ║
║ Confidence:        │  ║             │               │                     ║   │  • DFARS (8)         ║
║ ▬▬▬▬▬●▬▬▬ >0.70    │  ║         ┌───┴───┐       ┌───┴───┐                ║   │  • NIST (15)         ║
║                    │  ║         │   H   │       │   I   │                ║   │                      ║
║ Depth:             │  ║         └───────┘       └───────┘                ║   │  Metadata:           ║
║ [●────────] 2      │  ║                                                    ║   │  Created: 2024-01    ║
║                    │  ║   ↑ Force-directed graph with D3.js               ║   │  Updated: 2025-11    ║
║ ─────────          │  ║   Nodes scale based on importance                 ║   │  Confidence: 0.94    ║
║                    │  ║   Colors indicate type/category                   ║   │                      ║
║ View Options       │  ║   Hover for quick info, click for details         ║   │  ┌────────────────┐  ║
║ ────────────       │  ║                                                    ║   │  │ [View Full]    │  ║
║                    │  ║                                                    ║   │  │ [Edit]         │  ║
║ Layout:            │  ║                                                    ║   │  │ [Export]       │  ║
║ ◉ Force            │  ║                                                    ║   │  │ [Share]        │  ║
║ ○ Hierarchical     │  ╚════════════════════════════════════════════════════╝   │  └────────────────┘  ║
║ ○ Radial           │                                                            │                      ║
║ ○ Tree             │  ┌────────────────────────────────────────────────────┐   │  Related Searches    ║
║                    │  │ Graph Controls:                                    │   │  ────────────────    ║
║ Zoom:              │  │                                                    │   │                      ║
║ [−] ▬▬●▬▬ [+]      │  │ [🔍+] [🔍−] [⟲ Reset] [📸 Screenshot] [⚙️ Layout]│   │  • Show compliance   ║
║                    │  │                                                    │   │  • Related FAR       ║
║ ☑ Labels           │  │ [2D] [3D] [🎨 Theme] [💾 Save View] [📊 Stats]   │   │  • Timeline view     ║
║ ☑ Connections      │  └────────────────────────────────────────────────────┘   │                      ║
║ ☐ Clusters         │                                                            │  ┌────────────────┐  ║
║ ☐ Heatmap          │  Legend:                                                   │  │ 💡 Quick Actions│ ║
║                    │  ● Core Pillar  ● Sub-pillar  ● Topic  ● Entity          │  │                │  ║
║ ─────────          │  ═══ Strong    ─── Moderate   ··· Weak                   │  │ • Add node     │  ║
║                    │                                                            │  │ • Run analysis │  ║
║ [🗂️ Collections]   │  Statistics:                                              │  │ • AI explain   │  ║
║ [📥 Export]        │  Nodes: 247 | Edges: 1,823 | Clusters: 13                │  │ • Generate doc │  ║
║ [🔄 Refresh]       │  Avg Confidence: 0.87 | Last Updated: 2 min ago           │  └────────────────┘  ║
║                    │                                                            │                      ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  Status: Live • Last Sync: 2 min ago • Health: ●●●●● Excellent                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 3D Knowledge Graph View

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ [Logo] Knowledge Graph Explorer - 3D View                [2D] [3D ●] [VR] [⚙️] [👤] [🔔]              ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                        ║
║  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐ ║
║  │                                                                                                  │ ║
║  │                           /\                                                                     │ ║
║  │                          /  \          ●                                                         │ ║
║  │                         /    \        /│\                                                        │ ║
║  │                    ●───/──────\───●  / │ \                                                       │ ║
║  │                   /   /        \   \/  │  \                                                      │ ║
║  │                  /   /    ●     \  /\  │   ●                                                     │ ║
║  │                 /   /    /│\     \/  \ │  /│\                                                    │ ║
║  │            ●───/───/────/ │ \────/\───●─/ │ \                                                    │ ║
║  │           /│\ /   /    /  │  \  /  \ /│\/  │  \                                                  │ ║
║  │          / │X   ●/────/───●───\/────X │ \  │   ●                                                 │ ║
║  │         /  │ \ /│\  /    /│\  /\   /│\│  \ │  /│\                                                │ ║
║  │        ●───●──X─ │ \/────/ │ \/  \ / ││   ●─/ │ \                                                │ ║
║  │       /│\ /│\│\ │ /\    /  │ /\   X  │ \  /│\/  │  \                                             │ ║
║  │      / │X  │ ││\│/  \  /   │/  \ /│\ │  \/─ │ \ │   ●                                            │ ║
║  │     /  ││\ │ ││ X    \/    ●────X ││ │  /\  │  \│  /                                             │ ║
║  │    ●───││─●─││/│\   /\    /│\  /│\││ │ /  \ │   ●─/                                              │ ║
║  │        ││   ││ │ \ /  \  / │ \/  ││ │/    \│  /                                                  │ ║
║  │        │ \  ││ │  X    \/  │ /\  ││ ●──────●─/                                                   │ ║
║  │        │  \ ││ │ /│\   /\  │/  \ ││                                                              │ ║
║  │        │   ●──●  │ \ /  \ ●──────●                                                               │ ║
║  │        │      │  │  X    \│                                                                       │ ║
║  │        │      │  │ /│\    ●                                                                       │ ║
║  │                                                                                                   │ ║
║  │  ↑ Three.js powered 3D visualization                                                             │ ║
║  │  • Rotate: Click + drag                                                                          │ ║
║  │  • Zoom: Scroll wheel                                                                            │ ║
║  │  • Pan: Right-click + drag                                                                       │ ║
║  └──────────────────────────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                                                        ║
║  [◀ Rotate] [▲▼ Tilt] [🔄 Auto-rotate: On] [📸 Capture] [VR Mode] [Reset View]                      ║
║                                                                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## Compliance Dashboard - Desktop (1920x1080)

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ [Logo] Compliance Dashboard                              [📅 Last 30 Days ▼] [⚙️] [👤] [🔔]          ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                        ║
║  KEY METRICS (Glass Cards in Grid)                                                                    ║
║  ──────────────────────────────                                                                       ║
║                                                                                                        ║
║  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  ║
║  │ ╔══════════════════╗ │  │ ╔══════════════════╗ │  │ ╔══════════════════╗ │  │ ╔══════════════╗ │  ║
║  │ ║ Overall Score    ║ │  │ ║ Active Issues    ║ │  │ ║ Last Audit       ║ │  │ ║ Coverage     ║ │  ║
║  │ ║                  ║ │  │ ║                  ║ │  │ ║                  ║ │  │ ║              ║ │  ║
║  │ ║      ┌─────┐     ║ │  │ ║       12         ║ │  │ ║    ✅ Passed     ║ │  │ ║   ┌──────┐   ║ │  ║
║  │ ║      │ 94% │     ║ │  │ ║      ▲ 2         ║ │  │ ║                  ║ │  │ ║   │  97% │   ║ │  ║
║  │ ║      └─────┘     ║ │  │ ║                  ║ │  │ ║  Nov 15, 2025    ║ │  │ ║   └──────┘   ║ │  ║
║  │ ║   ●●●●○ (94%)    ║ │  │ ║  3 Critical ⚠️   ║ │  │ ║                  ║ │  │ ║   ●●●●●      ║ │  ║
║  │ ║                  ║ │  │ ║  5 High          ║ │  │ ║  [View Report]   ║ │  │ ║   Controls   ║ │  ║
║  │ ║  +2% this month  ║ │  │ ║  4 Medium        ║ │  │ ║                  ║ │  │ ║   Covered    ║ │  ║
║  │ ╚══════════════════╝ │  │ ╚══════════════════╝ │  │ ╚══════════════════╝ │  │ ╚══════════════╝ │  ║
║  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘  └──────────────────┘  ║
║                                                                                                        ║
║  TRENDS & ANALYTICS                                                                                   ║
║  ──────────────────                                                                                   ║
║                                                                                                        ║
║  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐   ║
║  │ Compliance Score Trend                                                      [Week▼] [Export]   │   ║
║  │ ──────────────────────                                                                         │   ║
║  │                                                                                                │   ║
║  │ 100%│                                              ●─────●                                     │   ║
║  │  95%│                           ●──────●──────●───/       \                                    │   ║
║  │  90%│                  ●───────/                            \                                  │   ║
║  │  85%│         ●───────/                                      \───●                             │   ║
║  │  80%│  ●─────/                                                                                 │   ║
║  │  75%│                                                                                          │   ║
║  │     └──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬─│   ║
║  │       Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov                         │   ║
║  │                                                                                                │   ║
║  │ Legend: ● Overall  ● SOC2  ● ISO27001  ● NIST                                                 │   ║
║  └────────────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                        ║
║  ┌─────────────────────────────────────────────┐  ┌──────────────────────────────────────────────┐   ║
║  │ Top Issues by Severity                      │  │ Control Category Breakdown                   │   ║
║  │ ─────────────────────                       │  │ ─────────────────────────                    │   ║
║  │                                             │  │                                              │   ║
║  │  ⚠️ Critical (3)                            │  │    ┌───────────────────────────────┐        │   ║
║  │  ▓▓▓░░░░░░░░░░░░░░░░░ 15%                  │  │    │  Access Control  ▓▓▓▓▓ 28%   │        │   ║
║  │                                             │  │    │  Data Protection ▓▓▓▓░ 22%   │        │   ║
║  │  🔴 High (5)                                │  │    │  Network Sec     ▓▓▓░░ 18%   │        │   ║
║  │  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░ 25%                  │  │    │  Incident Resp   ▓▓░░░ 12%   │        │   ║
║  │                                             │  │    │  Audit & Monitor ▓▓░░░ 10%   │        │   ║
║  │  🟡 Medium (4)                              │  │    │  Other           ▓░░░░ 10%   │        │   ║
║  │  ▓▓▓▓▓▓▓░░░░░░░░░░░░░ 20%                  │  │    └───────────────────────────────┘        │   ║
║  │                                             │  │                                              │   ║
║  │  🟢 Low (8)                                 │  │    Total Controls: 247                       │   ║
║  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░ 40%                  │  │    Passing: 232 (94%)                        │   ║
║  │                                             │  │    Failing: 15 (6%)                          │   ║
║  │  [View All Issues →]                       │  │                                              │   ║
║  └─────────────────────────────────────────────┘  └──────────────────────────────────────────────┘   ║
║                                                                                                        ║
║  RECENT ACTIVITY                                                                                      ║
║  ───────────────                                                                                      ║
║                                                                                                        ║
║  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐   ║
║  │ ⚠️ Critical  │ Encryption key rotation overdue                │ 2h ago    │ [Resolve] [View] │   ║
║  ├────────────────────────────────────────────────────────────────────────────────────────────────┤   ║
║  │ ⚠️ Critical  │ MFA not enabled for 3 admin accounts           │ 5h ago    │ [Resolve] [View] │   ║
║  ├────────────────────────────────────────────────────────────────────────────────────────────────┤   ║
║  │ ⚠️ Critical  │ Security patch pending (CVE-2024-12345)        │ 1d ago    │ [Resolve] [View] │   ║
║  ├────────────────────────────────────────────────────────────────────────────────────────────────┤   ║
║  │ 🔴 High      │ Access review overdue for 12 users             │ 2d ago    │ [Resolve] [View] │   ║
║  ├────────────────────────────────────────────────────────────────────────────────────────────────┤   ║
║  │ 🔴 High      │ Backup verification failed                     │ 3d ago    │ [Resolve] [View] │   ║
║  ├────────────────────────────────────────────────────────────────────────────────────────────────┤   ║
║  │ 🟡 Medium    │ Password policy update required                │ 5d ago    │ [Resolve] [View] │   ║
║  ├────────────────────────────────────────────────────────────────────────────────────────────────┤   ║
║  │ ✅ Resolved  │ Firewall rule updated                          │ 1w ago    │          [View] │   ║
║  ├────────────────────────────────────────────────────────────────────────────────────────────────┤   ║
║  │ ✅ Resolved  │ Quarterly audit completed                      │ 2w ago    │          [View] │   ║
║  └────────────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                        ║
║  [View All Activity →]                                                                                ║
║                                                                                                        ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  [📊 Generate Report] [📥 Export Data] [🔍 Run Audit] [⚙️ Configure Alerts]                          ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## Honeycomb Visualization (Axis 3)

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ [Logo] Axis 3: Honeycomb Pattern Analysis                       [🔍] [⚙️] [👤] [🔔]                   ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                        ║
║                                                                                                        ║
║                           ____        ____        ____                                                ║
║                          /    \      /    \      /    \                                               ║
║                         /  A1  \____/  A2  \____/  A3  \                                              ║
║                         \      /    \      /    \      /                                              ║
║                    ____  \____/  B1  \____/  B2  \____/  ____                                         ║
║                   /    \      \      /    \      /      /    \                                        ║
║                  /  A0  \  B0  \____/  C1  \____/  B3  /  A4  \                                       ║
║                  \      /      /    \      /    \      \      /                                       ║
║                   \____/  C0  /  C2  \____/  C3  \  B4  \____/                                        ║
║                        \      \      /    \      /      /                                             ║
║                    D0   \____  \____/  D1  \____/  ____/   C4                                         ║
║                         /    \      \      /      /    \                                              ║
║                        /  E0  \  D2  \____/  D3  /  C5  \                                             ║
║                        \      /      /    \      \      /                                             ║
║                         \____/  E1  /  E2  \  D4  \____/                                              ║
║                              \      \      /      /                                                   ║
║                               \____  \____/  ____/                                                    ║
║                                    \      /                                                           ║
║                                     \____/                                                            ║
║                                                                                                        ║
║  ↑ SVG-based hexagonal cells with clip-path                                                           ║
║                                                                                                        ║
║  Legend:                                                                                               ║
║  ▓▓▓ High relevance    ░░░ Medium relevance    ··· Low relevance    ○ No data                        ║
║                                                                                                        ║
║  Hover over cells to see details • Click to expand • Double-click to drill down                       ║
║                                                                                                        ║
║  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐   ║
║  │ Selected Cell: C1                                                                              │   ║
║  │ ─────────────────                                                                              │   ║
║  │ Title: Federal Acquisition Regulation (FAR) Part 15                                            │   ║
║  │ Relevance: High (0.94)                                                                         │   ║
║  │ Connected Cells: 6                                                                             │   ║
║  │ Last Updated: 2 days ago                                                                       │   ║
║  │                                                                                                │   ║
║  │ [Expand] [View Details] [Export] [Share]                                                       │   ║
║  └────────────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## Timeline Visualization (Axis 17)

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ [Logo] Axis 17: Observability & Analytics
                         [🔍] [⚙️] [👤] [🔔]                   ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                        ║
║  TIMELINE VIEW                                                                      [Month▼] [Export]  ║
║  ─────────────                                                                                         ║
║                                                                                                        ║
║  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐   ║
║  │ 2020         2021         2022         2023         2024         2025         2026            │   ║
║  │   │            │            │            │            │            │            │              │   ║
║  │   │            │            ●────────────●            │            │            │              │   ║
║  │   │            │           FAR Update  DFARS         │            │            │              │   ║
║  │   │            │           2022.1      Amendment     │            │            │              │   ║
║  │   │            │                                      │            │            │              │   ║
║  │   ●────────────●                                      │            ●            │              │   ║
║  │  NIST         SOC2                                    │          Policy         │              │   ║
║  │  800-171      Audit                                   │          Review         │              │   ║
║  │  Published    Passed                                  │          2025           │              │   ║
║  │   │            │                                      │            │            │              │   ║
║  │   │            │            │                         ●────────────●────────────●              │   ║
║  │   │            │            │                       ISO27001    FedRAMP      Planned           │   ║
║  │   │            │            │                       Certified   Moderate     CMMC L3          │   ║
║  │   │            │            │                       2024        Authorization 2026            │   ║
║  │   │            │            │            │            │            │            │              │   ║
║  ├───┼────────────┼────────────┼────────────┼────────────┼────────────┼────────────┼──────────────┤   ║
║  │                                                                                                │   ║
║  │   ◀ Past                                                          Future ▶                     │   ║
║  └────────────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                        ║
║  CAUSAL RELATIONSHIPS                                                                                 ║
║  ────────────────────                                                                                 ║
║                                                                                                        ║
║  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐   ║
║  │                                                                                                │   ║
║  │    ┌─────────────┐                                                                            │   ║
║  │    │  NIST       │                                                                            │   ║
║  │    │  800-171    │────────┐                                                                   │   ║
║  │    └─────────────┘        │                                                                   │   ║
║  │                           ▼                                                                   │   ║
║  │    ┌─────────────┐    ┌─────────────┐        ┌─────────────┐                                │   ║
║  │    │  FAR Update │───▶│   DFARS     │───────▶│  FedRAMP    │                                │   ║
║  │    │  2022.1     │    │  Amendment  │        │  Moderate   │                                │   ║
║  │    └─────────────┘    └─────────────┘        └─────────────┘                                │   ║
║  │                           │                           │                                       │   ║
║  │                           ▼                           ▼                                       │   ║
║  │                       ┌─────────────┐        ┌─────────────┐                                │   ║
║  │                       │  Policy     │        │  SOC2 Type  │                                │   ║
║  │                       │  Review     │        │  II Audit   │                                │   ║
║  │                       └─────────────┘        └─────────────┘                                │   ║
║  │                                                                                                │   ║
║  │  Legend:  ───▶ Direct causation   ····▶ Indirect influence   ═══▶ Strong dependency         │   ║
║  └────────────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## Mobile View - Knowledge Graph (375x812)

```
┌─────────────────────────────┐
│ ☰  Graph Explorer      [⋮]  │
├─────────────────────────────┤
│                             │
│ Axes: [1▼]                  │
│ ● Pillars                   │
│                             │
│ ╔═════════════════════════╗ │
│ ║                         ║ │
│ ║      ┌──●──┐            ║ │
│ ║     ●   │   ●           ║ │
│ ║    │ \ │ / │            ║ │
│ ║    ●───●───●            ║ │
│ ║    │ / │ \ │            ║ │
│ ║     ●   │   ●           ║ │
│ ║      └──●──┘            ║ │
│ ║                         ║ │
│ ║  Pinch to zoom          ║ │
│ ║  Tap nodes for info     ║ │
│ ║                         ║ │
│ ╚═════════════════════════╝ │
│                             │
│ [🔍] [⚙️] [2D] [📸]         │
│                             │
├─────────────────────────────┤
│ Selected: Federal Acq...    │
│                             │
│ ID: KP-001                  │
│ Type: Core Pillar           │
│ Confidence: 0.94            │
│                             │
│ Connections: 12             │
│ • FAR                       │
│ • DFARS                     │
│ • NIST                      │
│ [View All ▼]                │
│                             │
│ [View Full] [Share]         │
└─────────────────────────────┘
```

---

## Mobile View - Dashboard (375x812)

```
┌─────────────────────────────┐
│ ☰  Dashboard           [⋮]  │
├─────────────────────────────┤
│                             │
│ ┌─────────────────────────┐ │
│ │ Overall Score           │ │
│ │                         │ │
│ │       94%               │ │
│ │    ●●●●○ (94%)          │ │
│ │                         │ │
│ │    +2% this month       │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ Active Issues: 12 ▲2    │ │
│ │                         │ │
│ │ 3 Critical ⚠️           │ │
│ │ 5 High     🔴           │ │
│ │ 4 Medium   🟡           │ │
│ │                         │ │
│ │ [View All →]            │ │
│ └─────────────────────────┘ │
│         ↓ Swipe             │
│ ┌─────────────────────────┐ │
│ │ Last Audit              │ │
│ │ ✅ Passed               │ │
│ │ Nov 15, 2025            │ │
│ └─────────────────────────┘ │
│                             │
│ ● ○ ○  ← Cards carousel    │
│                             │
├─────────────────────────────┤
│ Compliance Trend            │
│ ────────────────            │
│                             │
│ 100%│         ●──●          │
│  90%│    ●───/    \         │
│  80%│ ●─/          \─●      │
│     └──┬──┬──┬──┬──┬──      │
│       M  A  M  J  J  A      │
│                             │
├─────────────────────────────┤
│ Recent Issues               │
│ ─────────────               │
│                             │
│ ⚠️ Encryption overdue       │
│ 2h ago        [View →]      │
│                             │
│ ⚠️ MFA not enabled          │
│ 5h ago        [View →]      │
│                             │
│ 🔴 Access review            │
│ 2d ago        [View →]      │
│                             │
│ [View All (12) →]           │
│                             │
├─────────────────────────────┤
│ [📊 Report] [🔍 Audit]      │
└─────────────────────────────┘
```

---

## Key Features & Interactions

### Knowledge Graph
1. **Interactive Navigation**
   - Click & drag to pan
   - Scroll/pinch to zoom
   - Click nodes for details
   - Double-click to expand/collapse

2. **Layout Algorithms**
   - Force-directed (default)
   - Hierarchical tree
   - Radial/circular
   - Custom layouts per axis

3. **Visual Encoding**
   - Node size = Importance
   - Node color = Type/category
   - Edge thickness = Relationship strength
   - Edge color = Relationship type

4. **Performance**
   - WebGL rendering for large graphs
   - Level-of-detail (LOD) optimization
   - Virtual nodes for massive datasets
   - Progressive loading

### Dashboard
1. **Real-Time Updates**
   - WebSocket connections
   - Auto-refresh intervals
   - Push notifications
   - Live status indicators

2. **Interactive Charts**
   - Hover for tooltips
   - Click for drill-down
   - Drag to select time range
   - Export to PNG/SVG/CSV

3. **Customization**
   - Drag & drop widgets
   - Resize cards
   - Hide/show sections
   - Save layouts

4. **Alerts & Notifications**
   - Configurable thresholds
   - Email/Slack/Teams integration
   - Severity-based routing
   - Escalation policies

---

## Accessibility

- Keyboard navigation for all graphs
- Screen reader descriptions
- High contrast mode
- Reduce motion option
- Focus indicators
- Alt text for visualizations

---

## Performance Optimizations

- Canvas/WebGL for large datasets
- Virtual scrolling
- Lazy loading
- Data pagination
- Efficient re-rendering
- Worker threads for computation

---

## Tech Stack

- **2D Graphs**: D3.js v7
- **3D Graphs**: Three.js + react-three-fiber
- **Force Simulation**: d3-force
- **Charts**: Recharts / Chart.js
- **Real-time**: Socket.io
- **State**: Zustand + React Query
- **Styling**: Tailwind CSS 4

---

This comprehensive visualization system provides powerful data exploration capabilities with modern, performant, and accessible interfaces aligned with 2025 design standards.
