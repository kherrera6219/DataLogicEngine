# DataLogicEngine — TODO

**Last Updated:** 2026-05-12
**Validated against codebase:** Yes

---

## 🟢 Medium Priority

### Microsoft Store Listing (no assets exist yet)
- [ ] Write conservative AI capability description for store listing
- [ ] Capture 5–10 screenshots of actual UI (no mockups)
- [ ] Prepare feature list
- [ ] Draft pricing disclosure (if applicable)
- [ ] Complete data practices disclosure form
- [ ] Create app icon in all required sizes (beyond `frontend/public/icon.png`)
- [ ] Prepare promotional banner images

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
- [x] Provider used shown per response (`frontend/components/Chat/MessageBubble.tsx`)
- [x] Data export endpoint user-accessible (`routes/user_data_routes.py`)
- [x] Data deletion endpoint user-accessible (`routes/user_data_routes.py`)
- [x] Privacy controls page (`frontend/app/settings/privacy/page.tsx`)
- [x] Background activity disclosure (`frontend/app/settings/privacy/page.tsx`)
- [x] Privacy link in settings (`frontend/app/settings/page.tsx`)
- [x] Privacy policy link in global footer (`frontend/app/layout.tsx`)
- [x] Enable/Disable AI processing toggle (`frontend/components/settings/AiModelSettings.tsx`)
- [x] Chat history opt-out toggle (`frontend/components/settings/AiModelSettings.tsx`)

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

| Area | Evidence |
|------|----------|
| Security (CSRF, headers, MFA, RBAC, rate limiting, lockout) | `backend/security/` |
| 10-layer simulation + QuadPersona + 17-axis graph | `core/simulation/`, `core/axes/` |
| 116 Knowledge Algorithms (incl. KA-61 adversarial shield) | `backend/knowledge_algorithms/`, `sdk/UKG_Python_SDK/ukg_sdk/overlay.py:62` |
| KA risk tier classifier | `backend/knowledge_algorithms/risk_classifier.py` |
| Tool Execution History page | `frontend/app/tools/history/page.tsx` |
| KA confirmation dialog | `frontend/components/ConfirmationDialog.tsx` |
| Truth Engine + TruthLink blockchain | `backend/truth_engine/` |
| MCP connectors (Salesforce, Jira) | `backend/mcp_server/` |
| User AI preferences model + migration | `models.py` (`UserAIPreferences`), `migrations/versions/c1d2e3f4a5b6_*.py` |
| User AI preferences API | `backend/routes/settings_routes.py` |
| User preferences wired into LLM gateway | `backend/llm_gateway/gateway.py` |
| AI enable/disable + history opt-out UI | `frontend/components/settings/AiModelSettings.tsx` |
| Provider badge per chat message | `frontend/components/Chat/MessageBubble.tsx` |
| Privacy policy footer link (global) | `frontend/app/layout.tsx` |
| Background activity disclosure | `frontend/app/settings/privacy/page.tsx` |
| Improved user-facing error messages | `frontend/components/ui/api-error-boundary.tsx`, `ChatInterface.tsx` |
| pip-audit clean (all 12 CVEs patched) | `requirements.txt` |
| Frontend lint passing (eslint-plugin-storybook added) | `frontend/package.json`, `frontend/eslint.config.mjs` |
| Frontend typecheck passing | `frontend/tsconfig.typecheck.json` |
| Celery background tasks | `backend/celery_app.py` |
| Sentry error tracking | `app.py`, `deploy/validate_production.py` |
| Redis caching + rate limiting | throughout `backend/` |
| Database migrations (Alembic) | `migrations/versions/` |
| Backup scripts | `deploy/backup_database.sh` |
| Load testing | `tests/performance/locustfile.py` |
| API versioning + pagination + ETags | `routes/`, `backend/middleware.py` |
| CDN support | `NEXT_PUBLIC_CDN_URL` in `frontend/next.config.ts` |
| Cloud disclosure banner | `frontend/components/CloudDisclosureBanner.tsx` |
| User data export/delete (GDPR) | `routes/user_data_routes.py` |
| Privacy policy + page | `docs/PRIVACY_POLICY.md`, `frontend/app/legal/privacy/page.tsx` |
| AI limitations page | `frontend/app/about/ai-limitations/page.tsx` |
| Cloud services disclosure page | `frontend/app/about/cloud-services/page.tsx` |
| Developer onboarding guide | `docs/DEVELOPER_GUIDE.md`, `docs/ENGINEER_ONBOARDING.md` |
| Deployment documentation | `docs/DEPLOYMENT.md`, `deploy/DEPLOYMENT_CHECKLIST.md` |
