# DataLogicEngine AI system card

DataLogicEngine is an app-owned governed reasoning and evidence-trace system for
desktop chat, retrieval, structured analysis, and auditable Knowledge Algorithm
workflows. It is intended to help a human examine supplied information and the
system's recorded reasoning controls. It is not an autonomous authority and is
not approved to replace qualified medical, legal, financial, safety, or
regulatory judgment.

Requests pass admission policy, measured routing, local retrieval, deterministic
personas, production-enabled TruthCore KAs, a configured OpenAI or Google model
when needed, output controls, claim/citation validation, bounded convergence,
and transactional trace persistence. Selected prompts and retrieved context may
leave the device for the configured provider. Local control-plane and trace data
remain app-owned subject to the documented storage lifecycle.

Evaluation uses the versioned synthetic golden corpus, semantic automated
metrics, per-provider/model rows, production KA invariants, and a blinded human
rubric. A displayed numeric value is evidence-support coverage from the named
`dle-confidence.v1` components, not a probability of correctness. Missing
quality, freshness, provenance, claim-support, or validator inputs produce `not
measured`.

Known failure modes include incomplete or stale sources, retrieval misses,
provider drift/outage, ambiguous claims, imperfect deterministic term-overlap
support checks, prompt injection, and human disagreement. The system may abstain,
block, or return a provider failure. Human oversight is mandatory for high-risk
use and for release approval. OpenAI/Google installed-build evaluation and the
blinded acceptance sample are currently pending, so production release remains
NO-GO.
