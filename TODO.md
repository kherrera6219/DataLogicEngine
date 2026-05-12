# DataLogicEngine — TODO

**Last Updated:** 2026-05-12  
**Validated against codebase:** Yes  
**Consolidated from:** `docs/archive/TODO_legacy.md`, `docs/archive/assessments/2026-02/TODO.md`, `notes/microsoft_store_compliance_todo.md`, `notes/microsoft_store_implementation_plan.md`

All items from prior TODO files that were already implemented have been verified and closed. Only genuinely outstanding work remains below.

---

## 🔴 Critical

### Microsoft Store — Privacy Footer Link
- [ ] Add a global privacy policy footer link to `frontend/components/NavBar.tsx` (or a dedicated `Footer` component in `frontend/app/layout.tsx`)
  - Link target: `/legal/privacy` (page already exists at `frontend/app/legal/privacy/page.tsx`)
  - Required for Microsoft Store auto-approval and GDPR footer compliance

---

## 🟡 High Priority

### User AI Controls (`frontend/app/settings/page.tsx` + `backend/llm_gateway/gateway.py`)

The AI Models tab exists (`AiModelSettings.tsx`) and allows selecting a preferred provider/model. The following sub-features are still missing:

- [ ] Add **Enable/Disable AI Processing** toggle to settings AI tab
- [ ] Add **opt-out for AI history/chat storage** toggle to settings AI tab
- [ ] Show **which specific provider processed each request** inline in `frontend/components/Chat/MessageBubble.tsx` (CloudStatusIndicator only shows generic gateway status, not per-message provider)
- [ ] Wire user preferences through `backend/llm_gateway/gateway.py` (the `preferred_name` parameter already exists at line 848; needs per-user DB storage and read path)

**Files:**
- `frontend/app/settings/page.tsx` — add controls to AI Models tab
- `frontend/components/Chat/MessageBubble.tsx` — add provider badge per assistant message
- `backend/llm_gateway/gateway.py` — read user preference from DB

---

### Accessibility Testing

Automated a11y tests run in CI (`npm run test:a11y:ci`). Manual verification is still outstanding:

- [ ] Tab through all pages — verify visible focus indicators
- [ ] Test with NVDA or JAWS (Windows) / VoiceOver (macOS)
- [ ] Verify all images have meaningful `alt` text
- [ ] Verify color contrast ratios meet WCAG 2.1 AA
- [ ] Test keyboard shortcuts work as expected
- [ ] Verify all form inputs have associated `<label>` elements
- [ ] Fix any critical violations found during manual testing
- [ ] Document accessibility features in Microsoft Store listing

---

## 🟢 Medium Priority

### Cloud Processing — Provider Identity per Request
- [ ] Display the specific AI provider used for each response in `frontend/components/Chat/ChatInterface.tsx` or `MessageBubble.tsx`
  - Backend already returns model metadata; surface it in the UI

### Tool Confirmation Dialogs (no files exist yet)
- [ ] Classify Knowledge Algorithms by risk tier (read-only / write / destructive) — `backend/knowledge_algorithms/risk_classifier.py`
- [ ] Add confirmation dialogs for destructive KA operations — `frontend/components/ConfirmationDialog.tsx`
- [ ] Create Tool Execution History page — `frontend/app/tools/history/page.tsx`
- [ ] Implement per-user tool permission management

### Microsoft Store Listing (no assets exist yet)
- [ ] Write conservative AI capability description for store listing
- [ ] Capture 5–10 screenshots of actual UI (no mockups)
- [ ] Prepare feature list
- [ ] Draft pricing disclosure (if applicable)
- [ ] Complete data practices disclosure form
- [ ] Create app icon in all required sizes (beyond the single `frontend/public/icon.png`)
- [ ] Prepare promotional banner images

---

## ⚪ Low Priority

### Enhanced User-Facing Error Messages
`ApiErrorBoundary` exists. The following polish is outstanding:
- [ ] Audit all user-visible error messages for clarity (remove internal IDs / stack traces)
- [ ] Ensure every error explains what happened **and** the next step the user can take
- [ ] Add contextual help links where relevant

### Background Activity Disclosure
- [ ] Document what background sync activity occurs (health checks, WebSocket keep-alives, etc.)
- [ ] Add user-facing toggle in Settings to disable non-essential background activity
- [ ] Surface disclosure in `frontend/app/settings/privacy/page.tsx`

---

## 📋 Microsoft Store Pre-Submission Checklist

Complete this checklist before submitting to Partner Center.

### Documentation
- [x] Privacy policy drafted (`docs/PRIVACY_POLICY.md`)
- [x] Privacy policy published in-app (`frontend/app/legal/privacy/page.tsx`)
- [x] AI limitations documented (`frontend/app/about/ai-limitations/page.tsx`)
- [x] Third-party cloud services page (`frontend/app/about/cloud-services/page.tsx`)
- [ ] Privacy policy URL registered in Partner Center
- [ ] Cloud dependency explicitly disclosed in store listing description

### In-App Features
- [x] Cloud disclosure banner on first run (`frontend/components/CloudDisclosureBanner.tsx`)
- [x] AI output labels on all LLM responses (`frontend/components/Chat/MessageBubble.tsx`)
- [x] Data export endpoint user-accessible (`routes/user_data_routes.py`)
- [x] Data deletion endpoint user-accessible (`routes/user_data_routes.py`)
- [x] Privacy controls page (`frontend/app/settings/privacy/page.tsx`)
- [x] Privacy link in settings (`frontend/app/settings/page.tsx` → `/settings/privacy`)
- [ ] Privacy policy link in global app footer

### Testing
- [x] Automated accessibility audit in CI (`npm run test:a11y:ci`)
- [ ] Manual WCAG 2.1 AA audit passed
- [ ] Keyboard navigation manually tested across all pages
- [ ] Screen reader compatibility confirmed (NVDA / JAWS / VoiceOver)
- [ ] Cloud outage handling tested (graceful degradation)
- [ ] Auth failure handling tested end-to-end
- [ ] Rate-limit UX tested
- [ ] AI provider failure modes tested
- [ ] Data export and delete flows tested end-to-end

### Store Listing Assets
- [ ] App description written (conservative, accurate)
- [ ] AI capabilities described accurately (no overpromising)
- [ ] 5–10 real UI screenshots captured
- [ ] Privacy practices form completed
- [ ] Pricing clearly disclosed
- [ ] All third-party AI services listed

---

## ✅ Verified Complete (reference)

The following areas were fully validated against the codebase and are **done**:

| Area | Evidence |
|------|----------|
| Security (CSRF, headers, MFA, RBAC, rate limiting, lockout) | `backend/security/` |
| 10-layer simulation + QuadPersona + 17-axis graph | `core/simulation/`, `core/axes/` |
| 116 Knowledge Algorithms (incl. KA-61 adversarial shield) | `backend/knowledge_algorithms/`, `sdk/UKG_Python_SDK/ukg_sdk/overlay.py:62` |
| Truth Engine + TruthLink blockchain | `backend/truth_engine/` |
| MCP connectors (Salesforce, Jira) | `backend/mcp_server/` |
| Celery background tasks | `backend/celery_app.py` |
| Sentry error tracking | `app.py`, `deploy/validate_production.py` |
| Redis caching + rate limiting | throughout `backend/` |
| Database migrations (Alembic) | `migrations/versions/` |
| Backup scripts | `deploy/backup_database.sh` |
| Load testing | `tests/performance/locustfile.py` |
| API versioning + pagination + ETags | `routes/`, `backend/middleware.py` |
| CDN support | `NEXT_PUBLIC_CDN_URL` in `frontend/next.config.ts` |
| AI output labeling | `frontend/components/Chat/MessageBubble.tsx:88` |
| Cloud disclosure banner | `frontend/components/CloudDisclosureBanner.tsx` |
| User data export/delete (GDPR) | `routes/user_data_routes.py` |
| Privacy policy + page | `docs/PRIVACY_POLICY.md`, `frontend/app/legal/privacy/page.tsx` |
| AI limitations page | `frontend/app/about/ai-limitations/page.tsx` |
| Cloud services disclosure page | `frontend/app/about/cloud-services/page.tsx` |
| Privacy controls page | `frontend/app/settings/privacy/page.tsx` |
| Developer onboarding guide | `docs/DEVELOPER_GUIDE.md`, `docs/ENGINEER_ONBOARDING.md` |
| Deployment documentation | `docs/DEPLOYMENT.md`, `deploy/DEPLOYMENT_CHECKLIST.md` |
