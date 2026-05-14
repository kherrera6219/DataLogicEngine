# DataLogicEngine TODO

**Last updated:** 2026-05-14  
**Status:** Canonical planning source

This is the only active TODO list for the repository. Keep open work here instead of adding separate project plans, roadmap files, assessment TODOs, or notes documents.

## Current Priority

### Microsoft Store Submission Readiness

#### Partner Center

- [ ] Register the published privacy policy URL in Partner Center.
- [ ] Complete the Partner Center data practices disclosure.
- [ ] Confirm pricing/subscription disclosure, or explicitly mark the app as free/no in-app purchases.
- [ ] List all third-party AI services used by the app.

#### Store Listing Copy

- [ ] Finalize conservative app description.
- [ ] Finalize conservative AI capability wording with no overpromising.
- [ ] Explicitly disclose cloud AI processing and internet requirement.
- [ ] Finalize feature list.
- [ ] Finalize privacy practices wording.

Draft listing baseline:

```text
DataLogicEngine is a local-first, cloud-augmented knowledge graph workspace for governed AI reasoning. It helps users organize enterprise knowledge, run traceable AI-assisted analysis, inspect provider/model usage, and manage privacy controls.

Internet access is required for AI reasoning features. Prompts and related context may be sent to configured third-party AI providers such as OpenAI, Anthropic, Google, or Microsoft Azure OpenAI. AI-generated responses may contain errors and should be verified before use in critical decisions.
```

#### Store Assets

- [ ] Capture 5-10 screenshots from the actual app UI.
- [ ] Add screenshots to `frontend/public/manifest.json` if publishing as a web/PWA surface.
- [ ] Create Microsoft Store icon assets in all required sizes beyond `frontend/public/icon.png`.
- [ ] Prepare promotional banner images.

Known asset gap:

- `frontend/public/manifest.json` references `/icons/icon-192.png` and `/icons/icon-512.png`, but those files are not present under `frontend/public/icons/`.

#### Manual Validation

- [ ] Manual WCAG 2.1 AA audit passed.
- [ ] Keyboard navigation manually tested across all primary pages.
- [ ] Screen reader compatibility confirmed with NVDA, JAWS, or VoiceOver.
- [ ] Cloud outage handling tested for graceful degradation.
- [ ] Auth failure handling tested end to end.
- [ ] Rate-limit user experience tested.
- [ ] AI provider failure modes tested.
- [ ] Data export and delete flows tested end to end.

## Completed Store-Readiness Work

| Area | Evidence |
| --- | --- |
| Privacy policy drafted | `docs/PRIVACY_POLICY.md` |
| Privacy policy published in-app | `frontend/app/legal/privacy/page.tsx` |
| AI limitations page | `frontend/app/about/ai-limitations/page.tsx` |
| Cloud services page | `frontend/app/about/cloud-services/page.tsx` |
| Cloud disclosure banner | `frontend/components/CloudDisclosureBanner.tsx` |
| AI output labels | `frontend/components/Chat/MessageBubble.tsx` |
| Provider/model shown per response | `frontend/components/Chat/MessageBubble.tsx` |
| User data export endpoint | `routes/user_data_routes.py` |
| User data deletion endpoint | `routes/user_data_routes.py` |
| Privacy controls page | `frontend/app/settings/privacy/page.tsx` |
| Privacy links in settings and footer | `frontend/app/settings/page.tsx`, `frontend/app/layout.tsx` |
| AI processing toggle | `frontend/components/settings/AiModelSettings.tsx` |
| Chat history opt-out toggle | `frontend/components/settings/AiModelSettings.tsx` |
| Automated accessibility audit command | `frontend/package.json` (`test:a11y:ci`) |

## Documentation Cleanup Policy

- Keep current planning in this file only.
- Keep release go/no-go criteria in `docs/RELEASE_CHECKLIST.md`.
- Keep active documentation discoverable from `README.md` and `docs/README.md`.
- Do not add new `PROJECT.md`, `ROADMAP.md`, `current_plan.md`, assessment TODOs, or archived planning summaries without first folding actionable items into this file.
