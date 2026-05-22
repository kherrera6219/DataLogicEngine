# Research: React Native Integration for Mobile Axis

**Status**: Planning
**Phase**: 30 (v3.0 Strategy)
**Target**: Mobile iOS/Android App ("Mobile Axis")

## 1. Executive Summary
This document outlines the strategy for bringing DataLogicEngine's "Truth Engine" and "17-Axis Graph" to mobile devices. The goal is to reuse 70-80% of the existing frontend logic (TypeScript, Hooks, State) while delivering a high-performance native experience using React Native.

**Recommendation**: Adopt **Expo (Managed Workflow)** with **NativeWind** for styling and **React Three Fiber** for 3D Graph rendering.

## 2. Shared Architecture Strategy

### 2.1 Monorepo Structure
To maximize code reuse between `frontend` (Next.js) and `mobile` (React Native), we should refactor the repository into a Monorepo using **Turborepo** or **Nx**.

**Proposed Structure**:
```text
/apps
  /web        (Current Next.js frontend)
  /mobile     (New Expo/React Native app)
  /electron   (Desktop wrapper)
/packages
  /ui         (Shared UI components - primitive buttons, cards)
  /core       (Shared logic, hooks, Zod schemas, API clients)
  /types      (Shared TypeScript definitions)
  /config     (Shared Tailwind, ESLint, TSConfig)
```

### 2.2 Shared Logic (`/packages/core`)
- **API Clients**: The existing `lib/api.ts` can be reused directly if it uses standard `fetch`.
- **State Management**: `ReviewContext`, `AuthContext` (if not cookie-based), and `SWR` hooks can be shared.
- **MCP Client**: The generic MCP client logic (WebSockets) is platform-agnostic and should be moved to a shared package.

## 3. UI & Styling Compatibility

### 3.1 Styling Engine: NativeWind v4
The current frontend uses Tailwind CSS. Porting to standard `StyleSheet` is time-consuming.
- **Solution**: Use **NativeWind v4**. It allows using Tailwind classes directly in React Native components (`className="..."`).
- **Benefit**: We can copy-paste many simpler components (divs -> View, spans -> Text) and keep the classes.

### 3.2 Component Library: "Universal Components"
Current `components/ui` uses Radix UI (Headless) + Tailwind.
Radix UI primitives are DOM-based and **do not work** in React Native.
- **Solution**: Adopt **rn-primitives** or **Gluestack UI**.
  - `rn-primitives` provides Radix-like API but renders native views.
  - Allows creating a "Universal Design System" where `<Card>` renders a div on Web and a View on Mobile.

### 3.3 Fluent Design on Mobile
Recap: We implemented "Fluent Design" (Acrylic, Reveal).
- **Mobile Equivalent**: use `expo-blur` for Acrylic/Glassmorphism.
- **Reveal Effects**: Harder to implement perfectly on touch, but can use `react-native-reanimated` for similar press/hover interactions.

## 4. Key Feature Feasibility

### 4.1 17-Axis Knowledge Graph
**Challenge**: Rendering 3D interactive graphs on mobile.
- **Web**: Uses `react-force-graph-3d` (Three.js).
- **Mobile Option A**: `WebView` wrapping the web graph.
  - *Pros*: Instant port.
  - *Cons*: Performance overhead, non-native touch feel.
- **Mobile Option B**: **React Three Fiber (R3F)** native.
  - *Pros*: Native OpenGL performance (via `expo-gl`).
  - *Cons*: Requires rewriting the graph renderer using primitive meshes instead of the convenience library.
- **Recommendation**: Start with **Option A (WebView)** for POC, migrate to **Option B** for v3.0 release.

### 4.2 Chat Interface
**Feasibility**: High.
- **WebSockets**: Supported natively.
- **UI**: Infinite lists (FlatList/FlashList) are more performant on mobile than DOM divs.
- **Input**: `KeyboardAvoidingView` handling is the detailed work needed here.

### 4.3 MCP Integration
- Mobile app can connect to the same Remote MCP Gateway via WebSocket.
- **Local MCP**: Not feasible to run Python MCP Servers *on* the phone. The mobile app will purely be a *Client* connecting to the Cloud/Desktop Server.

## 5. Deployment & CI/CD
- **Expo Application Services (EAS)**: Best-in-class for building iOS/Android binaries in the cloud.
- **Updates**: Over-the-air (OTA) updates for JS changes via EAS Update.

## 6. Next Steps (POC)
1. Initialize `apps/mobile` with Expo.
2. Configure `NativeWind`.
3. Extract `types` and `api` to shared packages.
4. Build a simple "Read-Only Dashboard" to verify API connectivity.
