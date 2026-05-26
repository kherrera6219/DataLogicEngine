# DSQP Technical Disclosure

**Disclosure date:** 2026-05-26
**Project:** DataLogicEngine / UKG
**Status:** Internal technical disclosure before public DSQP implementation

## Summary

The Dynamic Self-Questioning Protocol (DSQP) constructs query-specific expert personas at runtime. It replaces static persona templates with a seven-step self-questioning chain that derives each persona's job role, education, certifications, skills, training, career path, and related jobs from the query, coordinate context, and active UKG axes.

The implementation claim is that expert performance is primarily an activation problem for the local reasoning context, not a model-training problem. DSQP does not train a model or retrieve a fixed role card. It activates latent expert behavior by forcing the system to ask structured role-construction questions before persona reasoning begins.

## Seven-Step Protocol

For each persona axis, DSQP asks and answers these local construction questions:

1. **Job role:** What concrete professional role should own this query for the active axis?
2. **Education:** What formal education best supports that role?
3. **Certifications:** What credentials, licenses, or attestations are relevant?
4. **Skills:** What task skills and domain skills are required for this query?
5. **Training:** What training modules prepare the persona for the current risk and evidence context?
6. **Career path:** What professional experience makes the persona credible for this task?
7. **Related jobs:** Which adjacent roles should inform the persona's blind-spot coverage?

The protocol runs independently for the four persona axes: knowledge, sector, regulatory, and compliance. Each chain returns a seven-component persona profile and the question-answer evidence used to construct it.

## Activation-Not-Training Insight

General-purpose LLMs often contain enough latent knowledge to emulate expert reasoning, but static prompt labels such as "act as a compliance expert" under-specify the role. DSQP improves the activation surface by generating a structured expert profile from the current query and coordinate vector before reasoning. This gives downstream layers a concrete job role, credentials, skills, and constraints to reason against.

This differs from fine-tuning because no model weights change. It differs from retrieval because DSQP can construct a useful role even when no matching role document exists. Retrieval may enrich the profile, but the core protocol is local, deterministic, and offline-capable.

## Novelty

The novel element is query-specific dynamic role construction for each UKG persona axis. Existing approaches typically use:

- static role templates,
- prompt-only persona labels,
- document retrieval over fixed role descriptions,
- or model fine-tuning for a domain.

DSQP instead builds the seven-part role schema at runtime, validates coverage, records the chain, and passes the resulting persona objects into the TruthCore L5 multi-persona reasoning step.

## Prior-Art Search Notes

Items to compare before external filing or publication:

- self-ask prompting and decomposition prompting,
- role prompting and expert-prompt libraries,
- multi-agent persona orchestration systems,
- retrieval-augmented persona generation,
- chain-of-thought and tree-of-thought methods.

The differentiator to preserve is the combination of UKG axis grounding, seven-component persona construction, per-axis chain execution, coverage validation, audit persistence, and offline desktop execution.

## Implementation Boundary

The first implementation slice is deterministic and local-first. It creates a DSQP package, bundled question templates, validator, orchestrator, PersonaConstructionService integration, KA-012 integration, SDK client wrapper, and audit-chain serialization hooks. Later work can add LLM-assisted answer generation while preserving the same schema and validator.
