# Phase 6 Risk Register

Date: 2026-07-13

| Risk | Disposition |
|---|---|
| CP6-F has no rebuilt-installed OpenAI or Google corpus result | Open release blocker; both provider/model rows remain quarantined until separately evaluated. |
| Blinded human acceptance is incomplete | Open release blocker; Kevin is the primary reviewer, a second reviewer and signed disagreement outcome remain required. |
| Owner release approval is not recorded | Open release blocker; implementation authorization is not release approval. |
| The local corpus is repository-authored and synthetic | Declared in the corpus; expand only with license-reviewed data and preserve corpus versioning. |
| A single refinement call may not resolve evidence insufficiency | Safe behavior is abstention; never add unbounded retries or fabricate confidence. |
| Experimental KAs can be explicitly invoked outside production workflows | Require recorded `allow_nonproduction` opt-in; they cannot be represented as production validators. |
| Phase 3/4/5 installed gates remain open | Carry exact-runtime, recovery, Windows protection, object-store selection, and installed trace gates forward. |
| SeaweedFS is not production-selected | Candidate-only under ADR-0004. MinIO remains authoritative until every Replacement Control gate and owner approval pass. |
| ChromaDB Dependabot alert 389 remains open | Critical release blocker; current containment is not upstream remediation or production approval. |

Production/public release remains **NO-GO**.
