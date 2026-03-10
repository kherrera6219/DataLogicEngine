# Process Maps — DataLogicEngine

**Document Control**

| Field | Value |
|-------|-------|
| Owner | Platform Architecture |
| Last Updated | March 2026 |
| Status | Active |
| Audience | Engineers, product managers, QA, technical reviewers |
| Review Cadence | Every 60 days |
| Notation | BPMN-inspired swimlane process maps rendered in Mermaid |

---

## Table of Contents

1. [PM-01: User Onboarding and Authentication](#pm-01-user-onboarding-and-authentication)
2. [PM-02: Chat Workflow — Full Lifecycle](#pm-02-chat-workflow--full-lifecycle)
3. [PM-03: Knowledge Node Creation Workflow](#pm-03-knowledge-node-creation-workflow)
4. [PM-04: MCP Connector Registration Workflow](#pm-04-mcp-connector-registration-workflow)
5. [PM-05: Run Execution Lifecycle](#pm-05-run-execution-lifecycle)
6. [PM-06: LLM Provider Configuration Workflow](#pm-06-llm-provider-configuration-workflow)
7. [PM-07: Simulation Execution Workflow](#pm-07-simulation-execution-workflow)
8. [PM-08: Incident Response Process](#pm-08-incident-response-process)
9. [PM-09: Release and Deployment Process](#pm-09-release-and-deployment-process)
10. [PM-10: Security Vulnerability Response Process](#pm-10-security-vulnerability-response-process)

---

## PM-01: User Onboarding and Authentication

This map covers the full lifecycle from a new user arriving at the application through to an authenticated, active session.

```mermaid
flowchart TD
    START([New user\narrives at application])

    subgraph "Mode Detection"
        MODE{Deployment\nmode?}
        DESKTOP[Desktop / Electron\nno-login path]
        WEB[Web application\nlogin required]
    end

    subgraph "Desktop Path"
        SID_LOOKUP[Look up Windows SID\nfrom OS context]
        SID_MATCH{SID matches\nexisting user?}
        AUTO_LOGIN[Auto-login as\nlocal owner user]
        SID_CREATE[Create new user\nfrom SID + hostname]
    end

    subgraph "Web Login Path"
        LOGIN_PAGE[Login page]
        AUTH_METHOD{Authentication\nmethod?}

        subgraph "Local Auth"
            ENTER_CREDS[Enter username\n+ password]
            CHK_LOCK{Account\nlocked?}
            CHK_PASS[Verify password\nhash]
            PASS_FAIL[Increment failed\nattempts counter]
            LOCK_CHK{Failed attempts\n≥ threshold?}
            LOCK_ACCT[Lock account\nuntil cooldown]
        end

        subgraph "OIDC / Azure AD"
            REDIRECT_OIDC[Redirect to\nAzure AD / Entra ID]
            OIDC_CALLBACK[OAuth callback\ntoken exchange]
            OIDC_MAP[Map OIDC claims\nto local user]
        end

        MFA_GATE{MFA\nenabled?}
        TOTP_PROMPT[Prompt for\nTOTP code]
        TOTP_VERIFY[Verify TOTP\nor backup code]
        TOTP_FAIL[MFA verification\nfailed — retry]
        MAX_MFA{Max MFA\nattempts?}

        CREATE_SESSION[Create encrypted\nRedis session]
        JWT_ISSUE[Issue JWT\n(API clients)]
    end

    subgraph "Post-Login"
        ROLE_LOAD[Load user roles\nand permissions]
        TENANT_SET[Set tenant_id\nin request context]
        LAST_LOGIN[Update\nlast_successful_login]
        AUDIT_LOGIN[Write login\naudit event]
        DASHBOARD[Redirect to\nDashboard]
    end

    START --> MODE
    MODE -->|"Electron"| DESKTOP
    MODE -->|"Browser"| WEB

    DESKTOP --> SID_LOOKUP --> SID_MATCH
    SID_MATCH -->|"Found"| AUTO_LOGIN
    SID_MATCH -->|"New"| SID_CREATE --> AUTO_LOGIN

    WEB --> LOGIN_PAGE --> AUTH_METHOD
    AUTH_METHOD -->|"Local"| ENTER_CREDS
    AUTH_METHOD -->|"OIDC"| REDIRECT_OIDC

    ENTER_CREDS --> CHK_LOCK
    CHK_LOCK -->|"Locked"| E423[423 Account locked\nshow unlock instructions]
    CHK_LOCK -->|"Active"| CHK_PASS
    CHK_PASS -->|"Match"| MFA_GATE
    CHK_PASS -->|"No match"| PASS_FAIL --> LOCK_CHK
    LOCK_CHK -->|"Yes"| LOCK_ACCT --> E423
    LOCK_CHK -->|"No"| LOGIN_PAGE

    REDIRECT_OIDC --> OIDC_CALLBACK --> OIDC_MAP --> MFA_GATE

    MFA_GATE -->|"Disabled"| CREATE_SESSION
    MFA_GATE -->|"Enabled"| TOTP_PROMPT --> TOTP_VERIFY
    TOTP_VERIFY -->|"Valid"| CREATE_SESSION
    TOTP_VERIFY -->|"Invalid"| TOTP_FAIL --> MAX_MFA
    MAX_MFA -->|"No"| TOTP_PROMPT
    MAX_MFA -->|"Yes"| E423

    AUTO_LOGIN & CREATE_SESSION --> ROLE_LOAD
    ROLE_LOAD --> TENANT_SET --> LAST_LOGIN --> AUDIT_LOGIN --> JWT_ISSUE --> DASHBOARD
```

---

## PM-02: Chat Workflow — Full Lifecycle

This is the primary user workflow. It covers submitting a message and receiving a response.

```mermaid
flowchart TD
    START([User opens\nChat page])

    subgraph "Session Setup"
        SESS_CHK{Existing\nchat session?}
        SESS_LOAD[Load session\nfrom DB]
        SESS_NEW[Create new\nChatSession record]
        MODEL_SEL[User selects\nAI model / provider]
    end

    subgraph "Message Submission"
        COMPOSE[User composes\nmessage]
        SUBMIT[Submit message]
        SAVE_MSG[Save ChatMessage\nto DB\nrole=user]
    end

    subgraph "Processing Pipeline"
        ACTIVE_DEF[Active Defense\nSupervisor LLM\nscores intent]
        THREAT{Threat\ndetected?}
        COORD_RES[17-Axis coordinate\nresolution]
        TIER_SEL[Truth Engine\ntier selection]
        KA_EXEC[Knowledge Algorithm\nexecution]
        REASONING[Multi-step\nreasoning workflow]
        LLM_CALL[LLM provider\ncall]
        SAFETY_GATE[Final safety\ngate]
    end

    subgraph "Response Handling"
        STREAM{Streaming\nmode?}
        STREAM_RESP[Stream tokens\nto UI via SSE]
        BATCH_RESP[Return complete\nresponse JSON]
        SAVE_RESP[Save ChatMessage\nto DB\nrole=assistant]
        UPDATE_USAGE[Update\nLLMProviderUsage]
        WRITE_TRACE[Write RunTrace\nrecord]
        WRITE_AUDIT[Write AuditLog\nhash-chain entry]
    end

    subgraph "UI Update"
        RENDER[Render response\nin chat UI]
        SHOW_TRACE[Show trace\nbutton if run linked]
        SHOW_COORD[Optionally show\nknowledge coordinates]
    end

    START --> SESS_CHK
    SESS_CHK -->|"Yes"| SESS_LOAD
    SESS_CHK -->|"No"| SESS_NEW
    SESS_LOAD & SESS_NEW --> MODEL_SEL

    MODEL_SEL --> COMPOSE --> SUBMIT --> SAVE_MSG

    SAVE_MSG --> ACTIVE_DEF --> THREAT
    THREAT -->|"Safe"| COORD_RES
    THREAT -->|"Blocked"| BLOCK_RESP[Return safety\nblock message]

    COORD_RES --> TIER_SEL --> KA_EXEC --> REASONING --> LLM_CALL --> SAFETY_GATE
    SAFETY_GATE -->|"Approved"| STREAM
    SAFETY_GATE -->|"Blocked"| BLOCK_RESP

    STREAM -->|"Yes"| STREAM_RESP --> SAVE_RESP
    STREAM -->|"No"| BATCH_RESP --> SAVE_RESP

    SAVE_RESP --> UPDATE_USAGE --> WRITE_TRACE --> WRITE_AUDIT

    WRITE_AUDIT --> RENDER --> SHOW_TRACE --> SHOW_COORD
    SHOW_COORD -->|"Continue\nconversation"| COMPOSE
    SHOW_COORD -->|"View run trace"| TRACE_VIEW([Run Trace\nViewer page])
```

---

## PM-03: Knowledge Node Creation Workflow

```mermaid
flowchart TD
    START([User or API\nsubmits node data])

    subgraph "Input Validation"
        SCHEMA[Validate against\nNodeSchema\nPydantic / Marshmallow]
        SCHEMA_FAIL[Return 422\nValidation Error]
        PERM_CHK[Check UKG_WRITE\npermission]
        PERM_FAIL[Return 403\nForbidden]
    end

    subgraph "Deduplication"
        HASH_GEN[Generate content\nhash SHA-256]
        DEDUP_CHK{Node with same\nhash exists?}
        RETURN_EXIST[Return existing\nnode_id]
    end

    subgraph "17-Axis Coordinate Resolution"
        PARSE_AXES[Parse axis values\ninto AxisCoordinate objects]
        VALIDATE_AXES[Validate axis numbers\n1-17 range enforcement]
        BUILD_COORD[Build UnifiedCoordinate\n17-dimensional address]
        GEN_NODE_ID[Generate node_id\nSHA-256 of coordinate string]
    end

    subgraph "Knowledge Algorithm Pre-Processing"
        KA_004[KA-004\nInput sanitization]
        KA_010[KA-010\nBias detection]
        KA_034[KA-034\nAdversarial reasoning check]
        KA_PASS{All KA gates\npassed?}
        KA_BLOCK[Block write\nreturn KA violation]
    end

    subgraph "Multi-Store Write"
        PG_WRITE[Write KnowledgeNode\nto PostgreSQL\n+ tenant_id RLS]
        NEO_WRITE[Write node + edges\nto Neo4j\ngraph relationships]
        EMBED[Generate embeddings\nvia LLM provider]
        CHROMA_WRITE[Write embeddings\nto ChromaDB\nRAG index]
    end

    subgraph "Audit and Response"
        AUDIT_WRITE[Write AuditLog\nhash-chain entry]
        TRACE_WRITE[Update RunTrace\nif within a run]
        RESP[Return node_id\n+ coordinate string\n+ 201 Created]
    end

    START --> SCHEMA
    SCHEMA -->|"Invalid"| SCHEMA_FAIL
    SCHEMA -->|"Valid"| PERM_CHK
    PERM_CHK -->|"Denied"| PERM_FAIL
    PERM_CHK -->|"Granted"| HASH_GEN

    HASH_GEN --> DEDUP_CHK
    DEDUP_CHK -->|"Duplicate"| RETURN_EXIST
    DEDUP_CHK -->|"New"| PARSE_AXES

    PARSE_AXES --> VALIDATE_AXES
    VALIDATE_AXES -->|"Invalid axis"| SCHEMA_FAIL
    VALIDATE_AXES -->|"Valid"| BUILD_COORD --> GEN_NODE_ID

    GEN_NODE_ID --> KA_004 --> KA_010 --> KA_034 --> KA_PASS
    KA_PASS -->|"No"| KA_BLOCK
    KA_PASS -->|"Yes"| PG_WRITE

    PG_WRITE --> NEO_WRITE --> EMBED --> CHROMA_WRITE
    CHROMA_WRITE --> AUDIT_WRITE --> TRACE_WRITE --> RESP
```

---

## PM-04: MCP Connector Registration Workflow

```mermaid
flowchart TD
    START([Admin initiates\nAdd Connector])

    subgraph "Admin Authorization"
        PERM[Check MCP_ADMIN\npermission]
        PERM_FAIL[Return 403\nForbidden]
    end

    subgraph "Connector Configuration"
        ENTER_CONFIG[Enter connector details\nname · base_url · auth_type\nscopes · description]
        VALIDATE_URL[Validate base_url\nSSRF guard allowlist check]
        URL_FAIL[Return 400\nURL not in allowlist]
    end

    subgraph "OAuth Flow (if OAuth connector)"
        OAUTH_INIT[Initiate OAuth\nauthorization code flow]
        REDIRECT[Redirect admin\nto provider consent screen]
        CALLBACK[OAuth callback\nreceive auth code]
        TOKEN_EXCHANGE[Exchange code\nfor access + refresh token]
        TOKEN_STORE[Encrypt and store\nMCPOAuthToken in DB]
    end

    subgraph "Connector Registration"
        TOOL_DISC[Discover available\ntools from connector]
        SCOPE_MAP[Map required scopes\nto ToolDefinition objects]
        REGISTRY_ADD[Register tools\ninto ToolRegistry]
        DB_SAVE[Save MCPConnector\nrecord to PostgreSQL\ncredentials encrypted]
    end

    subgraph "Validation"
        HEALTH_CHK[Perform connector\nhealth check]
        HEALTH_FAIL{Health check\npassed?}
        MARK_ACTIVE[Mark connector\nstatus = active]
        MARK_INACTIVE[Mark connector\nstatus = inactive\nlog error]
    end

    subgraph "Audit"
        AUDIT[Write AuditLog\nconnector registered]
        RESP[Return connector_id\n+ tool list\n+ 201 Created]
    end

    START --> PERM
    PERM -->|"Denied"| PERM_FAIL
    PERM -->|"Granted"| ENTER_CONFIG

    ENTER_CONFIG --> VALIDATE_URL
    VALIDATE_URL -->|"Blocked"| URL_FAIL
    VALIDATE_URL -->|"Allowed"| OAUTH_INIT

    OAUTH_INIT -->|"OAuth required"| REDIRECT --> CALLBACK --> TOKEN_EXCHANGE --> TOKEN_STORE
    OAUTH_INIT -->|"API key auth"| TOOL_DISC
    TOKEN_STORE --> TOOL_DISC

    TOOL_DISC --> SCOPE_MAP --> REGISTRY_ADD --> DB_SAVE
    DB_SAVE --> HEALTH_CHK --> HEALTH_FAIL

    HEALTH_FAIL -->|"Yes"| MARK_ACTIVE --> AUDIT
    HEALTH_FAIL -->|"No"| MARK_INACTIVE --> AUDIT

    AUDIT --> RESP
```

---

## PM-05: Run Execution Lifecycle

A "Run" is the platform's fundamental unit of traceable work — a complete, recorded execution of a knowledge workflow.

```mermaid
flowchart TD
    START([User or API\ninitiates a Run])

    subgraph "Run Initialization"
        CREATE_RUN[Create Run record\nin PostgreSQL\nstatus=pending]
        ASSIGN_CORR[Assign correlation_id\nand run_id]
        PERM_CHK[Check required\npermissions]
    end

    subgraph "Step Execution Loop"
        NEXT_STEP{Next step\nin plan?}
        EXECUTE_STEP[Execute step\n via Truth Engine]
        WRITE_STEP[Write RunStep record\nstep_name · input · output\nduration_ms · status]
        STEP_FAIL{Step\nfailed?}
        RETRY{Retry\ncount < max?}
        MARK_STEP_FAIL[Mark step\nstatus=failed]
        UPDATE_STATUS[Update Run\nstatus=running]
    end

    subgraph "Tool Calls within a Step"
        TOOL_CALL{Step requires\ntool call?}
        MCP_EXEC[Execute via\nMCP Server]
        WRITE_TOOL[Write tool call\nto RunTrace]
    end

    subgraph "Run Completion"
        ALL_DONE{All steps\ncomplete?}
        MARK_SUCCESS[Mark Run\nstatus=completed]
        MARK_FAILED[Mark Run\nstatus=failed]
        WRITE_SUMMARY[Write run summary\nand token usage]
        SIGN_TRACE[Sign trace envelope\nfor export integrity]
        AUDIT_COMPLETE[Write AuditLog\nrun completed]
    end

    subgraph "Post-Run"
        NOTIFY[Notify user\nif async run]
        VIEWABLE[Run viewable\nin Runs page]
        EXPORT_AVAIL[Trace export\navailable]
    end

    START --> CREATE_RUN --> ASSIGN_CORR --> PERM_CHK
    PERM_CHK -->|"Denied"| E403[403 Forbidden]
    PERM_CHK -->|"Granted"| NEXT_STEP

    NEXT_STEP -->|"Yes"| EXECUTE_STEP
    NEXT_STEP -->|"No"| ALL_DONE

    EXECUTE_STEP --> TOOL_CALL
    TOOL_CALL -->|"Yes"| MCP_EXEC --> WRITE_TOOL --> WRITE_STEP
    TOOL_CALL -->|"No"| WRITE_STEP

    WRITE_STEP --> STEP_FAIL
    STEP_FAIL -->|"No"| UPDATE_STATUS --> NEXT_STEP
    STEP_FAIL -->|"Yes"| RETRY
    RETRY -->|"Yes"| EXECUTE_STEP
    RETRY -->|"No"| MARK_STEP_FAIL --> ALL_DONE

    ALL_DONE -->|"All succeeded"| MARK_SUCCESS
    ALL_DONE -->|"Any failed"| MARK_FAILED

    MARK_SUCCESS & MARK_FAILED --> WRITE_SUMMARY --> SIGN_TRACE --> AUDIT_COMPLETE
    AUDIT_COMPLETE --> NOTIFY --> VIEWABLE --> EXPORT_AVAIL
```

---

## PM-06: LLM Provider Configuration Workflow

```mermaid
flowchart TD
    START([Admin opens\nAI Model Settings])

    subgraph "Provider Setup"
        SELECT_PROV[Select provider\nOpenAI · Anthropic · Gemini · Grok · Codestral]
        ENTER_KEY[Enter API key]
        ENCRYPT_KEY[Encrypt API key\nusing EncryptionManager AES-256]
        SAVE_PROV[Save LLMProvider\nrecord to DB]
    end

    subgraph "Key Validation"
        TEST_BTN[Click Test Connection]
        TEST_CALL[Make test inference\ncall to provider]
        TEST_RESULT{Success?}
        MARK_VALID[Mark provider\nstatus=active]
        MARK_INVALID[Mark provider\nstatus=error\nshow error message]
    end

    subgraph "Model Selection"
        SEL_MODEL[Select default model\nfor this provider]
        SEL_PROFILE[Optionally map\ntask profiles:\ncode · analysis · reasoning]
        SAVE_PROFILE[Save routing profile\nconfiguration]
    end

    subgraph "Circuit Breaker Config"
        CB_THRESH[Set error threshold\nfor circuit breaker trip]
        CB_TIMEOUT[Set cooldown period\nbefore retry]
        FAILOVER_ORDER[Set provider\nfailover order]
        SAVE_CB[Save circuit breaker\nconfiguration]
    end

    subgraph "Audit"
        AUDIT_WRITE[Write AuditLog\nprovider configured]
        RESP[Provider active\nand routing enabled]
    end

    START --> SELECT_PROV --> ENTER_KEY --> ENCRYPT_KEY --> SAVE_PROV
    SAVE_PROV --> TEST_BTN --> TEST_CALL --> TEST_RESULT
    TEST_RESULT -->|"Success"| MARK_VALID --> SEL_MODEL
    TEST_RESULT -->|"Failed"| MARK_INVALID --> ENTER_KEY

    SEL_MODEL --> SEL_PROFILE --> SAVE_PROFILE
    SAVE_PROFILE --> CB_THRESH --> CB_TIMEOUT --> FAILOVER_ORDER --> SAVE_CB
    SAVE_CB --> AUDIT_WRITE --> RESP
```

---

## PM-07: Simulation Execution Workflow

```mermaid
flowchart TD
    START([User creates\nnew simulation])

    subgraph "Simulation Setup"
        SIM_CONFIG[Configure simulation\nname · scenario · axes · KAs]
        PERM_CHK[Check SIMULATION_EXECUTE\npermission]
        CREATE_SIM[Create Simulation record\nin DB status=configured]
    end

    subgraph "Pre-Execution Validation"
        VALIDATE_AXES[Validate 17-axis\ncoordinate configuration]
        VALIDATE_KAS[Validate selected\nKnowledge Algorithms]
        VALIDATE_BUDGET[Check TruthGate\nbudget allocation]
        BUDGET_FAIL[Return 402\nBudget exceeded]
    end

    subgraph "Simulation Layer Execution"
        L1[Layer 1\nKnowledge Retrieval\ncoordinate resolution]
        L2[Layer 2\nVector Similarity\nRAG retrieval]
        L3[Layer 3\nGraph Traversal\nNeo4j exploration]
        L4[Layer 4\nCross-Domain Linking\nHoneycomb/Octopus]
        L5[Layer 5\nQuantitative Modeling\nGNN / NN computation]
        L6[Layer 6\nScenario Projection\nfuture state simulation]
        L7[Layer 7\nRisk Assessment\nconfidence scoring]
    end

    subgraph "Result Processing"
        COLLECT_RESULTS[Collect layer outputs\ninto SimulationRun record]
        GEN_REPORT[Generate simulation\nreport with visualizations]
        SIGN_OUTPUT[Sign output envelope\nfor integrity]
        WRITE_AUDIT[Write AuditLog\nhash-chain entry]
    end

    subgraph "Review and Export"
        VIEW_RESULTS[View results\nin Simulations page]
        EXPORT{Export\nrequested?}
        SANITIZE[Sanitize export\nremove internal keys]
        DOWNLOAD[Download signed\nsimulation report]
    end

    START --> SIM_CONFIG --> PERM_CHK
    PERM_CHK -->|"Denied"| E403[403 Forbidden]
    PERM_CHK -->|"Granted"| CREATE_SIM

    CREATE_SIM --> VALIDATE_AXES --> VALIDATE_KAS --> VALIDATE_BUDGET
    VALIDATE_BUDGET -->|"Over budget"| BUDGET_FAIL
    VALIDATE_BUDGET -->|"Within budget"| L1

    L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7
    L7 --> COLLECT_RESULTS --> GEN_REPORT --> SIGN_OUTPUT --> WRITE_AUDIT

    WRITE_AUDIT --> VIEW_RESULTS --> EXPORT
    EXPORT -->|"Yes"| SANITIZE --> DOWNLOAD
    EXPORT -->|"No"| VIEW_RESULTS
```

---

## PM-08: Incident Response Process

```mermaid
flowchart TD
    TRIGGER([Incident trigger:\nAlert · User report · Automated detection])

    subgraph "Detection and Triage (0–1 hour)"
        DETECT{Source of\ndetection?}
        SENTRY_ALERT[Sentry crash alert]
        SIEM_ALERT[SIEM security event\nalert]
        USER_REPORT[User-reported\nfailure]

        SEV_ASSESS{Severity\nassessment}
        SEV_P1[P1 — Critical\nData breach · Full outage]
        SEV_P2[P2 — High\nPartial outage · Security event]
        SEV_P3[P3 — Medium\nDegraded performance]
        SEV_P4[P4 — Low\nCosmetic · Single user]
    end

    subgraph "Containment (1–4 hours)"
        ISOLATE[Isolate affected\ncomponents]
        REVOKE_CREDS[Revoke compromised\ncredentials / tokens]
        PRESERVE_LOGS[Preserve audit logs\nand forensic evidence]
        NOTIFY_TEAM[Notify security team\nand stakeholders]
    end

    subgraph "Investigation"
        AUDIT_REVIEW[Review hash-chained\naudit log]
        TRACE_REVIEW[Review run traces\nand correlation IDs]
        BUNDLE[Generate sanitized\nsupport bundle]
        ROOT_CAUSE[Identify root cause]
    end

    subgraph "Remediation"
        PATCH[Develop and test\npatch]
        DEPLOY_PATCH[Deploy patch\nvia CI/CD pipeline]
        RESTORE[Restore from\nverified clean backup\nif needed]
        VERIFY[Verify remediation\nvia security tests]
    end

    subgraph "Post-Incident"
        POSTMORTEM[Post-mortem\nwithin 5 business days]
        UPDATE_RUNBOOK[Update runbooks\nand detection rules]
        DISCLOSE[Coordinate disclosure\nif external reporter]
        CLOSE[Close incident\nrecord]
    end

    TRIGGER --> DETECT
    DETECT --> SENTRY_ALERT & SIEM_ALERT & USER_REPORT
    SENTRY_ALERT & SIEM_ALERT & USER_REPORT --> SEV_ASSESS

    SEV_ASSESS --> SEV_P1 & SEV_P2 & SEV_P3 & SEV_P4

    SEV_P1 & SEV_P2 --> ISOLATE
    SEV_P3 & SEV_P4 --> ROOT_CAUSE

    ISOLATE --> REVOKE_CREDS --> PRESERVE_LOGS --> NOTIFY_TEAM
    NOTIFY_TEAM --> AUDIT_REVIEW

    AUDIT_REVIEW --> TRACE_REVIEW --> BUNDLE --> ROOT_CAUSE
    ROOT_CAUSE --> PATCH --> DEPLOY_PATCH
    DEPLOY_PATCH --> RESTORE
    RESTORE --> VERIFY --> POSTMORTEM

    POSTMORTEM --> UPDATE_RUNBOOK --> DISCLOSE --> CLOSE
```

---

## PM-09: Release and Deployment Process

```mermaid
flowchart TD
    START([Release initiated\nversion bump in CHANGELOG.md])

    subgraph "Pre-Release Gates (CI)"
        LINT[Ruff lint\nzero findings]
        TESTS[pytest suite\n70%+ coverage]
        SECURITY_SCAN[Bandit + pip-audit\n+ CodeQL]
        SCHEMA_PARITY[SQLite ↔ Postgres\nschema parity check]
        STARTUP_CHECK[Deterministic startup\nprecheck runtime_precheck.py]
        ENV_PARITY[Environment variable\nparity verification]
        LOCKFILE[Lockfile integrity\nverification]
    end

    subgraph "Installer Build (Windows)"
        ELECTRON_BUILD[npm run electron:dist]
        SHA256[Generate SHA256\nchecksums]
        CODE_SIGN[Code-sign installer\nNSIS governance validation]
        SIGN_VERIFY[Verify signature\n+ revocation check]
        ARTIFACT_STORE[Store signed artifacts\nin release]
    end

    subgraph "Container Build"
        DOCKER_BUILD[docker build\nDockerfile.cloud]
        PUSH_REGISTRY[Push to container\nregistry]
        SCAN_IMAGE[Scan image\nfor CVEs]
    end

    subgraph "Deployment (Cloud)"
        STAGE_DEPLOY[Deploy to\nstaging environment]
        STAGE_SMOKE[Run smoke tests\nagainst staging]
        STAGE_PASS{Staging\npassed?}
        PROD_DEPLOY[Deploy to\nproduction]
        PROD_HEALTH[Verify production\nhealth endpoints]
        ROLLBACK[Rollback to\nprevious version]
    end

    subgraph "Release Publication"
        GH_RELEASE[Create GitHub Release\nwith signed artifacts]
        CHANGELOG_PUB[Publish CHANGELOG\nentry]
        TAG[Create git tag\nvX.Y.Z]
    end

    START --> LINT & TESTS & SECURITY_SCAN
    LINT & TESTS & SECURITY_SCAN --> SCHEMA_PARITY
    SCHEMA_PARITY --> STARTUP_CHECK --> ENV_PARITY --> LOCKFILE

    LOCKFILE --> ELECTRON_BUILD --> SHA256 --> CODE_SIGN --> SIGN_VERIFY --> ARTIFACT_STORE
    LOCKFILE --> DOCKER_BUILD --> PUSH_REGISTRY --> SCAN_IMAGE

    ARTIFACT_STORE & SCAN_IMAGE --> STAGE_DEPLOY --> STAGE_SMOKE --> STAGE_PASS
    STAGE_PASS -->|"Yes"| PROD_DEPLOY
    STAGE_PASS -->|"No"| ROLLBACK

    PROD_DEPLOY --> PROD_HEALTH
    PROD_HEALTH -->|"Healthy"| GH_RELEASE --> CHANGELOG_PUB --> TAG
    PROD_HEALTH -->|"Unhealthy"| ROLLBACK
```

---

## PM-10: Security Vulnerability Response Process

```mermaid
flowchart TD
    REPORT([Vulnerability reported\nsecurity@datalogicengine.com\nor GitHub Advisory])

    subgraph "Triage (48 hours)"
        ACK[Acknowledge report\nwith tracking reference]
        REPRO[Attempt to\nreproduce vulnerability]
        REPRO_RESULT{Reproducible?}
        CLOSE_INVALID[Close as\nnot reproducible\nnotify reporter]
        SEVERITY[Assign CVSS\nseverity score]
    end

    subgraph "Severity SLA"
        SEV_C{Critical\nCVSS 9.0+?}
        SEV_H{High\nCVSS 7.0-8.9?}
        SEV_M{Medium\nCVSS 4.0-6.9?}
        SLA_C[48-hour patch SLA]
        SLA_H[7-day patch SLA]
        SLA_M[30-day patch SLA]
        SLA_L[Next release]
    end

    subgraph "Remediation"
        DEVELOP_FIX[Develop fix\non private branch]
        TEST_FIX[Security test\nthe fix]
        PREPARE_ADVISORY[Draft GitHub\nSecurity Advisory]
        COORD_REPORTER[Coordinate disclosure\ndate with reporter]
    end

    subgraph "Release"
        PATCH_RELEASE[Create patch release\nvia normal release process]
        PUBLISH_ADVISORY[Publish GitHub\nSecurity Advisory]
        CREDIT[Credit reporter\nin advisory and SECURITY.md]
        NOTIFY_USERS[Notify users\nvia GitHub release notes]
    end

    REPORT --> ACK --> REPRO --> REPRO_RESULT
    REPRO_RESULT -->|"No"| CLOSE_INVALID
    REPRO_RESULT -->|"Yes"| SEVERITY

    SEVERITY --> SEV_C
    SEV_C -->|"Yes"| SLA_C
    SEV_C -->|"No"| SEV_H
    SEV_H -->|"Yes"| SLA_H
    SEV_H -->|"No"| SEV_M
    SEV_M -->|"Yes"| SLA_M
    SEV_M -->|"No"| SLA_L

    SLA_C & SLA_H & SLA_M & SLA_L --> DEVELOP_FIX
    DEVELOP_FIX --> TEST_FIX --> PREPARE_ADVISORY --> COORD_REPORTER
    COORD_REPORTER --> PATCH_RELEASE --> PUBLISH_ADVISORY --> CREDIT --> NOTIFY_USERS
```
