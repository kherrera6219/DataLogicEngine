"""Rewrite HANDOFF.md with updated session section and open items."""
path = r"C:\software\DataLogicEngine\HANDOFF.md"
content = open(path, encoding="utf-8").read()

# Replace the header block with updated date
OLD_HDR = """# DataLogicEngine — Session Handoff

_Last updated: 2026-05-31 (desktop chat enablement session)_

This document captures the current working state of the DataLogicEngine desktop
app, the issues fixed in recent sessions, the build/deploy process, and the
known-good verification steps. It is the primary handoff reference; the
`docs/WINDOWS_11_LOCAL_RUNBOOK.md` has the detailed local-run instructions.

> **Latest session (2026-05-31): end-to-end Enterprise AI chat enabled.** The
> full root-cause chain for "chat falls to the offline queue" was found and
> fixed; OpenAI standardized on gpt-5.5; several desktop UI glitches fixed; and a
> large in-progress modularization refactor was reverted to keep `main` green.
> Full detail in [Section 10](#10-desktop-chat-enablement-2026-05-31)."""

NEW_HDR = """# DataLogicEngine — Session Handoff

_Last updated: 2026-06-07 (routes audit session)_

This document captures the current working state of the DataLogicEngine desktop
app, the issues fixed in recent sessions, the build/deploy process, and the
known-good verification steps. It is the primary handoff reference; the
`docs/WINDOWS_11_LOCAL_RUNBOOK.md` has the detailed local-run instructions.

> **Latest session (2026-06-07): routes audit complete.** All 22 route files
> across `routes/` and `backend/routes/` reviewed live. 20 issues found,
> 2 are functional bugs (RT-1, RT-2). Sprint tasks RT-1 through RT-18 defined.
> See `docs/audits/DataLogicEngine_Routes_Audit.md`. Prior session (2026-05-31)
> enabled end-to-end Enterprise AI chat; full detail in
> [Section 10](#10-desktop-chat-enablement-2026-05-31)."""

content = content.replace(OLD_HDR, NEW_HDR, 1)

# Replace the Open / Next section
OLD_OPEN = """## 8. Open / Next

- ~~Confirm end-to-end chat success~~ — **root cause fixed (Section 10);** chat
  returns real gpt-5.5 replies through the gateway. The latest installer
  (`DataLogicEngine Setup Latest.exe` at repo root) carries the fix; reinstall to
  pick it up.
- ~~`anthropic` package not installed in `.venv311`~~ — **resolved (non-issue):**
  the Anthropic provider (`sdk/UKG_Python_SDK/ukg_sdk/providers/anthropic.py`)
  calls the Messages API over raw `httpx` and needs no `anthropic` SDK package.
- Consider surfacing the new `test_provider` status codes in the Settings UI so
  an invalid key shows "Invalid API key" inline (`ApiOverlayConfig.tsx`).
- **Known minor:** `RAG context retrieval failed: Access is denied ... llama_index`
  in the installed app — llama_index touches a path under read-only Program Files.
  It is caught (non-fatal; chat works without RAG context). Move the RAG/index
  working dir to the per-user runtime dir if RAG context is needed in chat.
- The Google/Gemini and Anthropic SDK providers still use async `httpx`; if those
  become the active chat provider, apply the same sync-call pattern used for
  OpenAI (Section 10) to avoid the Flask `async_to_sync` event-loop issue."""

NEW_OPEN = """## 8. Open / Next

### Immediate (functional bugs — fix before next demo)

- **RT-1 FUNCTIONAL BUG — `backend/routes/multimodal_routes.py`:** All 4 route
  handlers are named `process_document`. Python silently overwrites the earlier
  three; only `/document/process` actually dispatches correctly. Audio transcribe,
  audio synthesize, and video analyze all call the wrong handler. Rename to
  `transcribe_audio`, `synthesize_audio`, `analyze_video`, `process_document`.
- **RT-2 SECURITY — `backend/routes/search_routes.py`:** The `/suggest` endpoint
  has no `@login_required` decorator. Every other search endpoint requires auth.
  Add `@login_required` to match the blueprint.

### Routes sprint (RT-1 through RT-18)

Full task list and exit gates: `docs/audits/DataLogicEngine_Routes_Audit.md`

**Priority order:**

1. RT-1 + RT-2: fix the two functional bugs above
2. RT-3, RT-4, RT-5: register the three missing non-overlapping blueprints
   (`settings_bp`, `analytics_bp`, `retention_bp`) — each is one line in
   `routes/__init__.py`
3. RT-6: consolidate the three overlapping user-data deletion/export endpoints
   into a single canonical implementation in `routes/user_data_routes.py`
4. RT-7 through RT-18: remaining quality and consistency fixes

### Carry-over from prior sessions

- ~~End-to-end chat~~ — resolved (Section 10). gpt-5.5 returns real replies.
- ~~`anthropic` package~~ — non-issue; provider uses raw `httpx`.
- **Minor:** `RAG context retrieval failed: Access is denied ... llama_index` in
  installed app — llama_index touches a path under read-only Program Files.
  Non-fatal; chat works without RAG context. Move RAG index dir to per-user
  runtime dir when RAG context in chat becomes a priority.
- **Minor:** Gemini/Anthropic providers still use async `httpx`. If either
  becomes the active chat provider, apply the sync-call pattern from Section 10
  to avoid the Flask `async_to_sync` event-loop issue.
- Settings UI: consider surfacing `test_provider` status codes inline in
  `ApiOverlayConfig.tsx` so an invalid key shows "Invalid API key" in the UI."""

content = content.replace(OLD_OPEN, NEW_OPEN, 1)

open(path, "w", encoding="utf-8").write(content)
print("HANDOFF.md patched successfully")
