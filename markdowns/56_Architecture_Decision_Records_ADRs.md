# DOCUMENT 56: ARCHITECTURE DECISION RECORDS (ADRs)
## Holy Grail Refinery - Documentation & Training

**Document ID:** 56  
**Version:** 1.0  
**Created:** February 6, 2026  
**Category:** Documentation & Training  
**Status:** Specification Complete

---

## EXECUTIVE SUMMARY

This document contains **Architecture Decision Records (ADRs)** for the Holy Grail Refinery project. ADRs document the rationale behind major technical and architectural decisions, providing context for future developers and maintaining institutional knowledge.

**Purpose of ADRs:**
- 📝 **Document Context** - Capture the problem and constraints
- 🎯 **Record Decisions** - State what was decided clearly
- 🤔 **Explain Rationale** - Why this choice over alternatives
- ⚖️ **Accept Trade-offs** - Acknowledge consequences
- 🔄 **Enable Evolution** - Supersede when circumstances change

**ADR Process:**
1. Propose ADR in draft status
2. Discuss with stakeholders
3. Accept or reject
4. Implement decision
5. Monitor consequences
6. Supersede if needed

---

## TABLE OF CONTENTS

1. [ADR Template & Process](#1-adr-template--process)
2. [ADR-001: Use Redis for Semantic Bus](#adr-001-use-redis-for-semantic-bus)
3. [ADR-002: 35-Agent Architecture](#adr-002-35-agent-architecture)
4. [ADR-003: Local-First Deployment](#adr-003-local-first-deployment)
5. [ADR-004: Refined-IR as Universal Format](#adr-004-refined-ir-as-universal-format)
6. [ADR-005: LangGraph for Orchestration](#adr-005-langgraph-for-orchestration)
7. [ADR-006: PostgreSQL for Structured Data](#adr-006-postgresql-for-structured-data)
8. [ADR-007: Context Isolation per Agent](#adr-007-context-isolation-per-agent)
9. [ADR-008: 0.0001% Tolerance Standard](#adr-008-00001-tolerance-standard)
10. [ADR Index](#adr-index)

---

## 1. ADR TEMPLATE & PROCESS

### 1.1 ADR Format

```markdown
# ADR-XXX: [Title]

**Date:** YYYY-MM-DD  
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-YYY  
**Deciders:** [Names/Roles]  
**Tags:** [architecture, infrastructure, security, etc.]

## Context

[Describe the forces at play:
- What is the problem?
- What are the constraints?
- What requirements must be met?
- What is the current situation?]

## Decision

[State the decision clearly and concisely in one or two sentences]

## Rationale

[Why was this decision made?
- What evidence supports it?
- What principles guided the choice?
- What analysis was performed?]

## Consequences

### Positive
- [Expected benefit 1]
- [Expected benefit 2]

### Negative
- [Trade-off accepted 1]
- [Trade-off accepted 2]

### Neutral
- [Side effect 1]
- [Side effect 2]

## Alternatives Considered

### Alternative 1: [Name]
**Description:** [Brief description]  
**Rejected because:** [Specific reasons]

### Alternative 2: [Name]
**Description:** [Brief description]  
**Rejected because:** [Specific reasons]

## Related Decisions

- [ADR-XXX: Related decision]
- [ADR-YYY: Superseded by this]

## Notes

[Additional context, implementation notes, or follow-up items]
```

### 1.2 ADR Lifecycle

```
┌──────────┐
│ PROPOSED │ ← Initial draft
└────┬─────┘
     │
     ├─→ Discussion & Review
     │
     ▼
┌──────────┐
│ ACCEPTED │ ← Decision made
└────┬─────┘
     │
     ├─→ Implementation
     │
     ▼
┌────────────┐         ┌─────────────┐
│   STABLE   │────────→│ DEPRECATED  │
└────────────┘         └─────────────┘
     │
     ├─→ Circumstances change
     │
     ▼
┌─────────────┐
│ SUPERSEDED  │ ← Replaced by newer ADR
└─────────────┘
```

---

## ADR-001: Use Redis for Semantic Bus

**Date:** 2025-11-15  
**Status:** Accepted  
**Deciders:** Chief Architect, Infrastructure Lead  
**Tags:** infrastructure, messaging, performance

### Context

The Holy Grail Refinery requires a messaging system for 35 agents to communicate. Key requirements:
- High throughput (1000+ messages/second)
- Low latency (< 10ms)
- Pub/sub pattern support
- Message persistence optional
- Simple deployment model
- Must run locally on AW1 hardware

Initial system design used direct HTTP calls between agents, but this created tight coupling and made it difficult to add new agents.

### Decision

Use Redis Pub/Sub as the "Semantic Bus" for all agent-to-agent communication.

### Rationale

**Performance:**
- Redis achieves <1ms latency for pub/sub
- Handles 100K+ messages/second on commodity hardware
- In-memory operation ensures speed

**Simplicity:**
- Single process deployment
- No complex cluster setup needed
- Familiar to developers

**Flexibility:**
- Supports multiple subscribers per channel
- Easy to add new agents/channels
- Built-in pattern matching for subscriptions

**Local-First:**
- Runs entirely on localhost
- No cloud dependencies
- Minimal resource overhead

### Consequences

#### Positive
- ✅ Low latency messaging (<5ms observed)
- ✅ Simple deployment (single Docker container)
- ✅ Easy to debug (redis-cli for inspection)
- ✅ Scales to system requirements

#### Negative
- ❌ No built-in message persistence (messages lost if Redis crashes)
- ❌ No guaranteed delivery (pub/sub is fire-and-forget)
- ❌ No message ordering guarantees across channels

#### Neutral
- Messages are ephemeral (acceptable for our use case)
- Requires Redis client library in each agent

### Alternatives Considered

#### Alternative 1: RabbitMQ
**Description:** Full-featured message broker with queues and exchanges  
**Rejected because:**
- Overkill for our needs (complex setup)
- Higher resource overhead
- Persistence features not needed
- More complex to operate

#### Alternative 2: Apache Kafka
**Description:** Distributed streaming platform  
**Rejected because:**
- Designed for multi-node clusters (our system is single-node)
- Complex setup and operation
- High resource requirements
- Over-engineered for 35 agents

#### Alternative 3: ZeroMQ
**Description:** Lightweight messaging library  
**Rejected because:**
- No built-in broker (requires custom routing)
- More code to write and maintain
- Less operational tooling
- No persistence option

### Related Decisions

- ADR-003: Local-First Deployment
- ADR-020: Message Protocol Design (future)

### Notes

Consider Redis Streams for future versions if message persistence becomes critical.

---

## ADR-002: 35-Agent Architecture

**Date:** 2025-11-20  
**Status:** Accepted  
**Deciders:** Chief Architect, Product Lead  
**Tags:** architecture, agents, organization

### Context

Initial design had 3 monolithic agents: Extractor, Analyzer, Synthesizer. This created bottlenecks and made the system difficult to reason about.

Need to support 14 programming languages with deep specialization while maintaining coordination. Must balance:
- Specialization (deep language expertise)
- Coordination (agents must work together)
- Scalability (add languages without redesign)
- Maintainability (clear responsibilities)

### Decision

Organize system as 35 specialized agents in 4 tiers:
- **Executive (2):** PM Agent, CEO Agent
- **Support Ring (9):** Infrastructure and cross-cutting concerns
- **Refinery Pods (24):** 4 pods × 6 agents each
  - Pod A: Dynamic (Python, JavaScript, Ruby, PHP)
  - Pod B: Systems (C, C++, Rust, Zig)
  - Pod C: Enterprise (Java, C#, Scala, Kotlin)
  - Pod D: Mathematical (MATLAB, R, Julia, Mathematica)

### Rationale

**Specialization:**
- Each language specialist becomes expert in one language
- Sub-Managers specialize in pod-level patterns
- Audit agents specialize in verification

**14 → 4 → 1 Model:**
- 14 language specialists extract LogicNodes
- 4 pod managers consolidate to paradigm level
- 1 CEO performs grand fusion

**Conway's Law:**
- System structure mirrors communication patterns
- Clear ownership reduces conflicts
- Explicit interfaces reduce coupling

**Scalability:**
- Adding new language = new specialist + pod assignment
- No changes to other agents
- Pod structure accommodates 4-6 languages each

### Consequences

#### Positive
- ✅ Clear responsibilities (single responsibility principle)
- ✅ Deep language expertise
- ✅ Easy to add languages
- ✅ Parallel processing (24 specialists can work simultaneously)
- ✅ Isolated failures (one agent crash doesn't kill system)

#### Negative
- ❌ More complex coordination
- ❌ 35 Docker containers to manage
- ❌ Higher resource usage
- ❌ More complex debugging

#### Neutral
- Requires Semantic Bus for coordination
- Each agent needs LLM API access

### Alternatives Considered

#### Alternative 1: Monolithic Analyzer
**Description:** Single agent handles all languages  
**Rejected because:**
- No deep specialization
- Prompt becomes too complex
- Context window limitations
- Bottleneck for parallelization

#### Alternative 2: Per-Language Agents Only (14 agents)
**Description:** Just language specialists, no managers  
**Rejected because:**
- No coordination layer
- Difficult to consolidate results
- No paradigm-level understanding
- User-facing agent unclear

#### Alternative 3: Microservices Architecture (100+ services)
**Description:** Fine-grained services (parser, analyzer, optimizer, etc.)  
**Rejected because:**
- Over-engineered
- Complex service mesh
- Operational overhead
- Network latency

### Related Decisions

- ADR-001: Redis Semantic Bus
- ADR-005: LangGraph Orchestration

### Notes

35 agents is the sweet spot. Fewer = less specialization. More = coordination overhead.

---

## ADR-003: Local-First Deployment

**Date:** 2025-11-18  
**Status:** Accepted  
**Deciders:** Chief Architect, Security Lead  
**Tags:** deployment, infrastructure, security

### Context

Cloud deployment (AWS, Azure, GCP) offers scalability but introduces:
- Data sovereignty concerns (code sent to cloud)
- Network latency (upload → process → download)
- Ongoing costs (compute + storage + network)
- Internet dependency (offline unavailable)

Target hardware (AW1) has sufficient resources:
- Intel i7-14700F (20 cores, 28 threads)
- RTX 4060 Ti (16GB VRAM)
- 32GB+ RAM
- 1TB NVMe SSD

### Decision

Design system for local-first deployment on AW1 hardware, with cloud as optional enhancement.

All core functionality must work offline except LLM API calls.

### Rationale

**Data Sovereignty:**
- Code never leaves local machine
- Intellectual property protected
- Regulatory compliance easier

**Performance:**
- No network latency
- Database on NVMe SSD (microsecond access)
- All agents on same host (sub-millisecond IPC)

**Cost:**
- No ongoing cloud bills
- LLM API costs only
- One-time hardware cost

**Reliability:**
- No internet dependency (except LLM)
- No cloud outages
- Predictable performance

### Consequences

#### Positive
- ✅ Complete data control
- ✅ Consistent performance
- ✅ Low operational cost
- ✅ Offline capable (with local LLM)

#### Negative
- ❌ Limited by single-node resources
- ❌ No automatic scaling
- ❌ Manual backups required
- ❌ Hardware maintenance user's responsibility

#### Neutral
- Docker enables cloud migration if needed
- Can add cloud storage for backups

### Alternatives Considered

#### Alternative 1: Cloud-Native (AWS/Azure/GCP)
**Description:** Deploy all components to cloud  
**Rejected because:**
- Data sovereignty concerns
- Ongoing costs
- Internet dependency
- Latency for code upload/download

#### Alternative 2: Hybrid (Local + Cloud Burst)
**Description:** Local primary, cloud for overflow  
**Rejected because:**
- Complexity of hybrid setup
- Data sync challenges
- Unpredictable costs
- Not needed for initial version

### Related Decisions

- ADR-010: Docker Containerization
- ADR-015: Backup Strategy

---

## ADR-004: Refined-IR as Universal Format

**Date:** 2025-11-22  
**Status:** Accepted  
**Deciders:** Chief Architect, Language Team Leads  
**Tags:** architecture, data-model, core

### Context

Need a universal format to represent computational intent across 14 programming languages.

Requirements:
- Language-agnostic (works for Python through Assembly)
- Paradigm-agnostic (functional, OOP, procedural, mathematical)
- Semantic not syntactic (captures intent, not syntax)
- Verifiable (can prove equivalence)
- Extensible (add domains/concepts over time)

Initial attempts used AST transformation (language A → language B AST), but this was lossy and language-specific.

### Decision

Create "Refined-IR" (Refined Intermediate Representation) as universal LogicNode format with:
- **Paradigm:** Dynamic, Systems, Enterprise, Mathematical
- **Domain:** list_operations, async_programming, etc.
- **Concept:** filter, map, malloc, async_await, etc.
- **Intent:** Plain English description
- **Inputs/Outputs:** Typed parameters
- **Preconditions/Postconditions:** Formal constraints
- **Side Effects:** State mutations

### Rationale

**Semantic Focus:**
- Captures "what" not "how"
- `[x for x in items if x > 10]` and `items.filter(x => x > 10)` → same LogicNode

**Universal:**
- Works across all paradigms
- Extensible domain/concept model
- Not tied to any language's semantics

**Verifiable:**
- Preconditions/postconditions enable formal verification
- 1,000 equivalence tests per LogicNode
- 0.0001% tolerance achievable

**Composable:**
- LogicNodes can reference other LogicNodes
- Complex operations built from simple ones
- Graph structure emerges naturally

### Consequences

#### Positive
- ✅ True cross-language understanding
- ✅ Verification possible
- ✅ Extensions don't break existing
- ✅ AI-friendly representation

#### Negative
- ❌ Custom format (not industry standard)
- ❌ Initial learning curve
- ❌ Must maintain concept catalog
- ❌ Some nuances lost in abstraction

#### Neutral
- JSON serialization works well
- Can export to other formats if needed

### Alternatives Considered

#### Alternative 1: LLVM IR
**Description:** Use LLVM's intermediate representation  
**Rejected because:**
- Too low-level (designed for compilation)
- Loses high-level semantics
- C-family bias
- Not suitable for dynamic languages

#### Alternative 2: WebAssembly
**Description:** Use WASM as universal format  
**Rejected because:**
- Execution format, not analysis format
- Loses semantic information
- Requires compilation
- Not designed for equivalence testing

#### Alternative 3: Direct AST Comparison
**Description:** Compare abstract syntax trees  
**Rejected because:**
- Language-specific structure
- Syntactic not semantic
- Brittle to style differences
- No universal representation

### Related Decisions

- ADR-008: 0.0001% Tolerance Standard
- ADR-011: Concept Catalog Design

---

## ADR-005: LangGraph for Orchestration

**Date:** 2025-12-01  
**Status:** Accepted  
**Deciders:** Chief Architect, Infrastructure Lead  
**Tags:** infrastructure, orchestration, workflow

### Context

Need to orchestrate 35 agents with complex dependencies:
- PM → CEO → Sub-Managers → Specialists → Audit → CEO → PM
- Parallel execution within pods
- State checkpointing for fault tolerance
- Conditional branching (if audit fails, retry)

Requirements:
- State machine execution
- Parallel task support
- Checkpoint/resume capability
- Clear visualization
- Python-native

### Decision

Use LangGraph for multi-agent workflow orchestration.

### Rationale

**State Machine Model:**
- Natural fit for agent states (IDLE → PROCESSING → COMPLETE)
- Visual graph representation
- Conditional edges for branching

**Built for LLMs:**
- Designed for multi-agent systems
- Handles LLM context naturally
- Streaming support

**Persistence:**
- State checkpointing built-in
- Resume from failure
- Audit trail automatic

**Python-Native:**
- Integrates with agent code
- Type safety with Pydantic
- Good documentation

### Consequences

#### Positive
- ✅ Clear workflow visualization
- ✅ State persistence
- ✅ Fault tolerance
- ✅ Parallel execution

#### Negative
- ❌ LangGraph learning curve
- ❌ Relatively new library
- ❌ Vendor lock-in (LangChain ecosystem)

#### Neutral
- Python-only (acceptable for our stack)

### Alternatives Considered

#### Alternative 1: Apache Airflow
**Description:** Workflow orchestration platform  
**Rejected because:**
- Designed for data pipelines, not agents
- Heavy infrastructure (web server, scheduler, executor)
- Overkill for local deployment

#### Alternative 2: Temporal
**Description:** Durable execution framework  
**Rejected because:**
- Requires separate Temporal server
- Complex for local deployment
- Go-based (prefer Python)

#### Alternative 3: Custom State Machine
**Description:** Build our own orchestrator  
**Rejected because:**
- Reinventing the wheel
- More code to maintain
- No visualization tools

### Related Decisions

- ADR-002: 35-Agent Architecture
- ADR-014: Checkpoint Strategy

---

## ADR-006: PostgreSQL for Structured Data

**Date:** 2025-12-05  
**Status:** Accepted  
**Deciders:** Chief Architect, Database Lead  
**Tags:** database, infrastructure

### Context

Need relational database for:
- State Graph (missions, tasks, agents)
- LogicNode Registry (all extracted LogicNodes)
- Traceability Ledger (audit trail)

Requirements:
- ACID transactions
- Rich query capabilities
- JSON support (for LogicNode storage)
- Local deployment
- Reliable and mature

### Decision

Use PostgreSQL as primary relational database.

### Rationale

**Reliability:**
- 30+ years of development
- ACID compliant
- Well-tested

**Features:**
- JSONB for semi-structured data
- Full-text search
- GIN indexes for JSON queries
- Window functions for analytics

**Performance:**
- Handles millions of LogicNodes
- Efficient indexing
- Query optimization

**Operations:**
- Docker deployment
- pg_dump for backups
- Extensive tooling (pgAdmin, DBeaver)

### Consequences

#### Positive
- ✅ Proven reliability
- ✅ Rich query capabilities
- ✅ JSONB perfect for LogicNodes
- ✅ Great tooling

#### Negative
- ❌ Must manage schema migrations
- ❌ Backup/restore user responsibility
- ❌ Not horizontally scalable (single-node only)

#### Neutral
- SQL knowledge required

### Alternatives Considered

#### Alternative 1: MongoDB
**Description:** Document database  
**Rejected because:**
- No ACID transactions (historically)
- Less mature than PostgreSQL
- Schema-less can cause issues
- PostgreSQL JSONB provides same flexibility

#### Alternative 2: SQLite
**Description:** Embedded database  
**Rejected because:**
- Limited concurrency (writer locks entire database)
- No network access
- Less suitable for production

### Related Decisions

- ADR-021: Database Schema Design
- ADR-015: Backup Strategy

---

## ADR-007: Context Isolation per Agent

**Date:** 2025-12-10  
**Status:** Accepted  
**Deciders:** Chief Architect, ML Lead  
**Tags:** ai, architecture, isolation

### Context

Each agent uses LLM (Claude) with 1M token context window. Question: Should agents share context or maintain isolation?

**Sharing context:**
- Could reduce redundant information
- Agents see each other's reasoning
- Lower token consumption

**Isolating context:**
- Each agent has independent context
- No cross-contamination
- Clear ownership

### Decision

Each agent maintains completely isolated context. No agent can see another agent's LLM context.

Communication only through Semantic Bus messages.

### Rationale

**Clarity:**
- Agent decisions traceable to own context
- No hidden dependencies
- Debugging easier

**Independence:**
- Agents can evolve separately
- No implicit coupling
- Parallel execution safe

**Security:**
- Sensitive data not leaked between agents
- Clear data boundaries

**Specialization:**
- Each agent's context optimized for its role
- No dilution from irrelevant information

### Consequences

#### Positive
- ✅ Clear reasoning boundaries
- ✅ Independent debugging
- ✅ Parallel safe
- ✅ No context contamination

#### Negative
- ❌ Higher token consumption
- ❌ Must communicate explicitly
- ❌ Cannot share "common knowledge"

#### Neutral
- Requires Semantic Bus (already decided)

### Alternatives Considered

#### Alternative 1: Shared Context Pool
**Description:** All agents share global context  
**Rejected because:**
- Complex to manage
- Debugging nightmare
- Coupling between agents
- Security concerns

#### Alternative 2: Hierarchical Context
**Description:** Managers see specialist contexts  
**Rejected because:**
- Still creates coupling
- Managers overwhelmed with detail
- Violates encapsulation

### Related Decisions

- ADR-002: 35-Agent Architecture
- ADR-012: Context Caching Strategy

---

## ADR-008: 0.0001% Tolerance Standard

**Date:** 2025-12-12  
**Status:** Accepted  
**Deciders:** Chief Architect, Quality Lead  
**Tags:** quality, testing, verification

### Context

Need verification standard for LogicNodes. How accurate must extraction be?

**Loose standard (90%):**
- Easier to achieve
- Faster verification
- More false positives

**Strict standard (99.99%):**
- High confidence
- Slower verification
- Fewer false positives

### Decision

Require 999 of 1,000 equivalence tests to pass (0.0001% tolerance).

Each LogicNode must demonstrate >99.9% accuracy.

### Rationale

**High Confidence:**
- System outputs must be trustworthy
- Used for production code analysis
- Errors compound through 35 agents

**Statistical Validity:**
- 1,000 tests provide good coverage
- 999/1000 = very high confidence
- Rare edge cases acceptable

**Industry Standard:**
- Similar to formal verification standards
- Comparable to compiler correctness
- Meets safety-critical requirements

**Achievable:**
- Audit agents can generate 1,000 tests
- Run in reasonable time (<30 seconds)
- Automated verification possible

### Consequences

#### Positive
- ✅ High confidence in results
- ✅ Professional-grade quality
- ✅ Trustworthy for production use
- ✅ Clear pass/fail criteria

#### Negative
- ❌ Slower verification
- ❌ Some valid LogicNodes rejected
- ❌ Edge cases may fail unfairly

#### Neutral
- Requires automated test generation
- Audit agents do heavy lifting

### Alternatives Considered

#### Alternative 1: 90% Standard
**Description:** 900 of 1,000 tests pass  
**Rejected because:**
- Too many false positives
- Insufficient confidence
- Not suitable for production
- Compounds errors across system

#### Alternative 2: 100% Standard
**Description:** All 1,000 tests must pass  
**Rejected because:**
- Unrealistic
- Edge cases always exist
- Would reject valid LogicNodes
- Perfect is enemy of good

#### Alternative 3: Formal Proof
**Description:** Mathematical proof of correctness  
**Rejected because:**
- Not automatable
- Requires theorem prover
- Too slow
- Overkill for our use case

### Related Decisions

- ADR-004: Refined-IR Format
- ADR-022: Test Generation Strategy

---

## ADR Index

### By Number
- ADR-001: Redis for Semantic Bus
- ADR-002: 35-Agent Architecture
- ADR-003: Local-First Deployment
- ADR-004: Refined-IR Format
- ADR-005: LangGraph Orchestration
- ADR-006: PostgreSQL Database
- ADR-007: Context Isolation
- ADR-008: 0.0001% Tolerance

### By Category

**Architecture:**
- ADR-002: 35-Agent Architecture
- ADR-004: Refined-IR Format
- ADR-007: Context Isolation

**Infrastructure:**
- ADR-001: Redis Semantic Bus
- ADR-003: Local-First Deployment
- ADR-005: LangGraph Orchestration
- ADR-006: PostgreSQL Database

**Quality:**
- ADR-008: 0.0001% Tolerance Standard

### By Status
**Accepted:** All current ADRs
**Proposed:** None
**Deprecated:** None
**Superseded:** None

---

## DOCUMENT METADATA

**Document ID:** 56  
**Version:** 1.0  
**Created:** February 6, 2026  
**Category:** Documentation & Training  
**Owner:** Chief Architect  
**Next Document:** 57 (FAQ Document)

---

*End of Architecture Decision Records*
