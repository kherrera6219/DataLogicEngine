# UI/UX Improvement Plan

This plan highlights concrete enhancements to strengthen the Universal Knowledge Graph (UKG) application's wireframes, usability, and visual language.

## Navigation and Information Architecture
- Standardize global navigation (Home, Chat/Workbench, Graph Explorer, Compliance) so the destinations in the hero CTAs map to a persistent top bar and footer links. Expose secondary routes such as Regulatory, Timeline, and Honeycomb via a mega-menu or command palette for quick pivoting.
- Add an always-visible breadcrumb + page title region on product surfaces (chat, dashboards, graph) to orient users within the 13-axis model and provide a “Back to Hub” affordance.
- Introduce a left-rail variant for data-heavy screens (knowledge-graph, compliance dashboards) with collapsible filters for Axis, Persona, and Time. Pair it with a right-rail for summaries, risk callouts, and export actions.

## AI Workbench (Chat) Experience
- Replace the plain text input with a segmented control for Text / Voice / Upload and show inline chips for personas (KE/SE/RE/CE) and context toggles so users see active constraints before sending. Persist the quick prompts as horizontally scrollable cards with icons.
- Add system message scaffolding (source list, confidence badge, and action buttons: "Open in Graph", "Generate Report", "Bookmark") to each response. Show streaming states, tokens-per-second, and latency in a compact status bar near the composer instead of deep within the layout.
- Include empty, loading, and error states in the transcript column; add skeletons for the first reply to reduce perceived latency and keep scroll position stable.

## Knowledge Graph & Visual Analytics
- Create a split-view wireframe: left filters (Axis, Sector, Regulatory, Time), center canvas, right insights panel with breadcrumbs and cross-links back to chat. Provide toggleable layouts (Force, Honeycomb, Timeline) with preview thumbnails.
- Add node details drawer with tabs for "Summary", "Evidence", and "Compliance Links"; include quick actions to pin, follow, or export node paths.
- For the timeline and honeycomb pages, add zoom controls, mini-map, and an overlay legend explaining color/shape encodings. Use consistent badges and tooltips for risk posture across graph and dashboard views.

## Compliance Dashboards & Reports
- Establish consistent card hierarchy for metrics (title, sparkline, delta, severity). Add filter chips for frameworks (SOC 2, NIST, HIPAA) and persona presets (Compliance Officer, Procurement Lead).
- Provide prebuilt layouts for "Audit Readiness", "Control Drift", and "Evidence Queue" with step-wise progress headers and export buttons (PDF/CSV/API). Include a printable/light theme variant for regulatory submissions.

## Visual Language & Theming
- Build a unified design token sheet (spacing, radius, shadows) and map glassmorphism accents to meaningful interaction states (primary vs. secondary surfaces). Use elevation ramp + blur for panels instead of ad-hoc `glass-panel` usages.
- Adopt a restrained palette that improves readability: dark background with high-contrast neutrals and a single accent brand color. Audit text on gradients and apply consistent typography scale for headings, metric chips, and badges.
- Enhance microinteractions: smooth hover transitions on CTAs, pulsating scroll indicator on hero, and motion guidelines for graph loading/filters to stay under 200ms to preserve perceived speed.

## Accessibility & Content Strategy
- Enforce WCAG 2.2 AA/AAA targets: 4.5:1 contrast, focus outlines on all interactive elements, skip-to-content link in the layout, and descriptive aria-labels on icon-only controls.
- Add in-product explanations of the 13-axis model via tooltips and an onboarding tour. Provide glossary links from personas and axis filters, and include user education on how AI decisions map to compliance outputs.

## Wireframe Delivery Checklist
- Produce low-fidelity flows for: Home/Onboarding, Chat/Workbench, Knowledge Graph Explorer (Force + Honeycomb + Timeline), Compliance Dashboards, and Reports. Each frame should show navigation, filter rails, empty/loading/error states, and export/hand-off controls.
- Deliver a component inventory (buttons, chips, badges, cards, drawers, breadcrumbs, modals) with variants and spacing tokens to guide developers implementing the Next.js + Fluent UI + Bootstrap stack.
