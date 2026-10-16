# System Architecture & Technical Specification
**RE Financial Services — AI Solutions Builder Assignment**  
**Deliverable:** Task 4 Architecture Note  
**Author:** Chandrashekhar H S  
**Status:** Working Prototype (Automated Pipeline) &bull; Enterprise Multi-Tenant Production Roadmap  
**Document Companion:** [architecture.pdf](architecture.pdf) (Executive 1-Page A4 Consulting PDF)

---

## Executive Summary & Architectural Boundaries

This technical architecture note provides an engineering specification of the financial trend analysis and ledger intelligence system developed for RE Financial Services. It details the implemented working prototype—a deterministic calculation engine, a strictly grounded Claude Skill, an official read-only QuickBooks Online Model Context Protocol (MCP) server, and an idempotent live developer sandbox integration—alongside a production-grade multi-tenant cloud architecture designed for enterprise scale.

### Separation of Responsibilities

1. **Deterministic Arithmetic in Python (`scripts/engine.py`):** The financial calculation engine executes 100% of arithmetic using Python `Decimal` quantized to cents (`ROUND_HALF_UP`). Floating-point arithmetic (IEEE 754) is strictly prohibited to eliminate probabilistic variance or rounding drift across rolling periods.
2. **Grounded Interpretation via Claude Skill (`.claude/skills/monthly-trend-analysis/SKILL.md`):** The deterministic Python engine calculates all financial metrics and creates structured results (`analysis.json`). The Claude Skill operates as an analytical reasoning layer constrained by 10 negative "never-rules," consuming those structured results to explain trends, variance drivers, and anomalies instead of independently recalculating figures in narrative text.
3. **Decoupled QuickBooks Integration (`quickbooks-online-mcp-server/`):** Claude Desktop connects to QuickBooks Online through an official Intuit Model Context Protocol (MCP) server operating strictly over stdio JSON-RPC. It enforces registration-time mutation suppression (suppressing `create_*`, `update_*`, `delete_*` tools, leaving 71 read-only tools registered out of 142).
4. **Actionable Human-in-the-Loop Governance:** Rather than automating journal entry corrections directly, ledger anomalies and non-operating distortions are surfaced as a prioritized 5-point Month-End Close Checklist for the Fractional CFO.

---

## Implemented Execution Topology & Data Flow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        IMPLEMENTED PIPELINE & DATA FLOW                                │
└────────────────────────────────────────────────────────────────────────────────────────┘

1. SOURCE CLIENT WORKBOOK / LIVE LEDGER
   • ABC Inc - Financial Statements.xlsx (data/): 18 monthly periods (Jan 2025 to Jun 2026)
   • Intuit V3 ProfitAndLoss JSON (results/qbo_live_pnl_report.json)
              │
              ▼
2. PRE-FLIGHT SAFETY GATE & INGESTION ADAPTER (scripts/run_pipeline.py, scripts/adapters/qbo_adapter.py)
   • Inspects read-only environment flags (QUICKBOOKS_DISABLE_WRITE=true, etc.)
   • Normalizes Intuit V3 hierarchical P&L JSON into canonical openpyxl workbook schema
   • Auto-sorts reverse-chronological columns into ascending chronological order
              │
              ▼
3. DETERMINISTIC CALCULATION ENGINE (scripts/engine.py)
   • Exact Decimal Math: Quantized to Decimal('0.01') using ROUND_HALF_UP (zero floating-point drift)
   • Backward Subtotal Isolation: Dynamically detects multi-tier subtotals to prevent double-counting
   • 126 Reconciliation Checks: 7 category balance checks across 18 periods (100% pass rate)
   • Strict 12-Month TTM Windows: Gates on 12 consecutive calendar periods; yields exactly 7 valid windows
   • Anomaly Isolation: Surfaces Dec 2025 tax credit (-$1,244,429.84) and derives Normalized Core Loss (-$381,241.27)
              │
              ├────────────────────────────────────────┬─────────────────────────────────┐
              ▼                                        ▼                                 ▼
4. MACHINE-READABLE JSON OUTPUT          5. EXECUTIVE MARKDOWN REPORT       6. CLAUDE SKILL REASONING
   results/analysis.json (238 KB)          results/report.md (13 KB)          .claude/skills/
   • 18 monthly normalized summaries       • Executive summary tables         • 10 anti-hallucination rules
   • 7 rolling TTM windows                 • MoM variance narratives          • Grounds solely on analysis.json
   • 126 reconciliation results            • Dec 2025 normalization bridge    • Formulates CFO close checklist
   • Full chart-of-accounts mapping        • 10-point CPA checklist
              │
              └────────────────────────────────────────┬─────────────────────────────────┘
                                                       ▼
7. DUAL EVALUATION SUITE & REGRESSION GATES (evals/ & tests/)
   • 9 Golden Cases (evals/run_evals.py): Score 110.0/110.0 (+0.0 delta vs committed baseline)
   • Commentary Guardrail Harness (evals/eval_commentary.py): Score 100.0/100.0 across 4 categories
   • Automated Pytest Suite (tests/): 99 passing unit, regression, CLI, adapter, and mutation tests
```

---

## Domain A: Project Setup & Component Architecture

### 1. Overall Application Structure & Module Decomposition
The repository is structured into decoupled, single-responsibility components and verified paths:

* **Calculation Engine (`abc-trend-analysis/scripts/engine.py`):** Deterministic financial calculation engine. Encapsulates `FinancialCalculationEngine`, parsing workbooks into structured dataclasses (`MonthPeriod`, `AnomalyFlag`, `ReconciliationCheck`). Enforces `ROUND_HALF_UP` cents math, auto-sorts reverse-chronological columns (June 2026 back to January 2025), isolates subtotal account hierarchies to eliminate double-counting, computes trailing-twelve-month windows, evaluates 126 reconciliation checks, and isolates accounting distortions.
* **QBO Report Adapter (`abc-trend-analysis/scripts/adapters/qbo_adapter.py`):** Normalizes Intuit QuickBooks Online Profit and Loss reports into the canonical engine format. Recursively traverses nested Intuit V3 P&L report rows, maps column metadata to calendar months, creates an in-memory openpyxl workbook, and verifies that 16 of 18 months match Excel exactly; the other 2 differ only by 3 pre-existing Intuit sandbox sample transactions ($300.00 and $391.25).
* **Pipeline Orchestrator (`scripts/run_pipeline.py` & `abc-trend-analysis/scripts/run_pipeline.py`):** Single-command launcher executing the entire end-to-end analysis workflow: environment validation, read-only guardrail checks, live or cached P&L retrieval, engine execution, output verification, and evaluation gates.
* **Executive Reporter (`abc-trend-analysis/scripts/reporter.py`):** Deterministically synthesizes `results/report.md`, rendering executive KPI cards, MoM variance breakdowns, the December 2025 anomaly bridge, and the 10-point CPA close checklist.
* **Claude Skill (`.claude/skills/monthly-trend-analysis/SKILL.md`):** Reusable instructions for financial trend analysis. The deterministic Python engine calculates all financial metrics and creates structured results (`results/analysis.json`). The Claude Skill uses those results to explain trends, variance drivers, and anomalies instead of independently recalculating figures in narrative text.
* **Evaluation & Verification Harnesses (`abc-trend-analysis/evals/`):** Houses synthetic golden test cases (`eval_cases.json`), grading harnesses (`run_evals.py` - score 110/110 across 9 cases, +0.0 delta), and commentary evaluation guardrails (`eval_commentary.py` - score 100/100 across 4 checks).
* **Structured Analysis Artifact (`abc-trend-analysis/results/analysis.json`):** Machine-readable structured output encapsulating 18 normalized monthly summaries, 7 rolling TTM windows, 126 balance checks, and detected ledger anomalies.
* **Executive Report Artifact (`abc-trend-analysis/results/report.md`):** Human-readable Markdown report containing executive KPI tables, anomaly disclosures, and the CFO close checklist.
* **CLI Interface (`abc-trend-analysis/scripts/cli.py`):** Production command-line tool supporting dual input formats (`--input <file.xlsx>` and `--qbo-json <report.json>`), customizable anomaly thresholds, baseline diffing, and configurable artifact output paths.
* **Comparator (`abc-trend-analysis/scripts/comparator.py`):** Cross-dataset reconciliation between the Excel baseline and live QuickBooks reports, categorizing variances into distinct accounting buckets.
* **QuickBooks Online MCP Server (`quickbooks-online-mcp-server/`):** Official Intuit Model Context Protocol server in TypeScript, exposing 71 tools registered with write/update/delete disabled (out of 142 total tools) across 29 entities over stdio JSON-RPC.

### 2. Configuration, Execution Flow & Memory Architecture
* **Execution Command:** `python scripts/run_pipeline.py [--offline]`
* **Sequential 6-Stage Execution Flow:**
  1. *Safety Verification:* Verifies `.env` presence, credential definitions, and read-only flags (`DISABLE_WRITE=true`, etc.). (Bypassed in `--offline` mode).
  2. *Ingestion:* In live mode, invokes `quickbooks-online-mcp-server/scripts/export-pnl.mjs` via Node.js to fetch the 18-month P&L. In offline mode, validates the existing cached JSON artifact (`results/qbo_live_pnl_report.json`).
  3. *Engine Processing:* Invokes `scripts.cli` to parse the normalized dataset, execute decimal arithmetic, evaluate TTM windows, and run 126 reconciliation checks.
  4. *Artifact Integrity Check:* Confirms generation and structural validity of `analysis.json` and `report.md`.
  5. *Golden Evaluation Gate:* Executes all 9 golden edge cases in `evals/run_evals.py`, asserting zero regression against the committed baseline.
  6. *Commentary Evaluation Gate:* Executes `evals/eval_commentary.py`, verifying numerical grounding and strict anti-hallucination guardrails.
* **Prototype Memory & State Model:**
  - **No Persistent Cross-Session Memory by Design:** The conversational agent retains no persistent state across sessions. This eliminates context contamination and hallucinations from stale conversation turns.
  - **State in Structured Artifacts & Configuration:** Analysis state is strictly encapsulated in structured output files (`analysis.json`, `report.md`) and configuration files (`thresholds.json`).
  - **Local Client Partitioning:** Separate client runs can be partitioned locally using client-specific folders and configuration parameters (e.g., `results/different_company_analysis.json`).
  - **Prototype Scope Boundary:** The current local prototype is a developer tool and not yet a complete multi-tenant service. Client-specific folders provide local operational separation during development and demonstration, but local folder segregation alone does NOT provide enterprise-grade security isolation.

### 3. Dependencies & Interfaces
* **Runtime Environments:** Python 3.10+ and Node.js 18+.
* **Python Libraries:** `openpyxl` (workbook parsing/generation), `pytest` (automated testing), `reportlab` & `pypdf` (Task 4 PDF generation).
* **Node.js Libraries:** `@modelcontextprotocol/sdk` (MCP protocol implementation), `zod` (runtime schema validation), `jest` (unit & integration testing).
* **Component Interfaces:** Cross-process stdio JSON-RPC for Claude Desktop to MCP server communication; Subprocess execution and structured filesystem artifacts (JSON, Markdown, XLSX) for pipeline orchestration.

---

## Domain B: Credential Security & Operational Guardrails

### 1. Secrets Management [Prototype (today)]
* **Credential Storage:** QuickBooks OAuth 2.0 credentials (`QUICKBOOKS_CLIENT_ID`, `QUICKBOOKS_CLIENT_SECRET`, `QUICKBOOKS_REFRESH_TOKEN`, `QUICKBOOKS_REALM_ID`) load from local `.env` configuration files inside `quickbooks-online-mcp-server/` into process memory.
* **Source Control Protection:** Secrets stay in gitignored .env files; the submission archive was scanned for them before packaging. Sanitized `.env.example` templates with empty placeholders are tracked.
* **No Hardcoded Secrets:** Zero credentials, private keys, or API tokens are hardcoded in application logic or checked into source control.

### 2. Enforced Read-Only Guardrails [Prototype (today)]
* **Registration-Time Mutation Suppression:** The MCP server enforces registration-time mutation suppression using runtime environment flags:
  ```ini
  QUICKBOOKS_DISABLE_WRITE=true
  QUICKBOOKS_DISABLE_UPDATE=true
  QUICKBOOKS_DISABLE_DELETE=true
  ```
  At server initialization, tool registration logic filters out any tool definition matching recognized mutation name prefixes (`create_*`, `create-*`, `update_*`, `update-*`, `delete_*`, `delete-*`). This leaves exactly 71 read-only tools registered (out of 142 total tools across 29 entities).
* **Defense-in-Depth Boundary:** Registration-time tool suppression prevents Claude Desktop from discovering or invoking mutation tools over stdio JSON-RPC. However, environment flags alone do not prove every conceivable mutation is impossible. Complete defense-in-depth requires enforcing read-only permissions at the QuickBooks OAuth user/app level and independently validating exposed tool implementations.
* **Pre-Flight Pipeline Safety Gate:** `scripts/run_pipeline.py` verifies these flags before executing any network operations. If any disable flag is not explicitly `"true"`, execution halts immediately with a fatal error.

### 3. Credential Vault & Lifecycle Management [Proposed Production Architecture]
* **Per-Tenant Credential Vault:** Store each client's QuickBooks OAuth credentials (`client_id`, `client_secret`, `refresh_token`, `realm_id`) separately in **AWS Secrets Manager** partitioned by tenant path: `/tenants/{tenant_id}/qbo_credentials`.
* **Least-Privilege IAM Scoping:** Compute workers assume temporary IAM roles granting read access strictly to their authenticated tenant's secret path. Do not reuse one client's refresh token or realm configuration for another.
* **Token Refresh Concurrency:** QuickBooks OAuth refresh tokens rotate on use (100-day rolling expiry, 5-year maximum). Distributed locks (e.g., Redis/ElastiCache) serialize token refresh operations across concurrent worker processes to prevent race conditions and token invalidation.

---

## Domain C: Hosting Architecture & Operational Model

### 1. Current Working Prototype (Local Developer Workstation)
* **Environment & Components:** Operates on developer workstations across Python 3.10+ (calculation engine, CLI, evaluation suites) and Node.js 18+ (QuickBooks MCP server). Claude Desktop runs locally, spawning the TypeScript MCP server as a child process via stdio JSON-RPC.
* **Storage & Configuration:** Local filesystem storage (`results/analysis.json`, `results/report.md`) and local `.env` configuration.
* **QuickBooks Sandbox Integration:** Verified against an Intuit developer sandbox using balanced journal entries; tenant-specific identifiers are kept out of documentation.
* **Development Fitness:** The local prototype is well-suited for rapid development, testing, offline evaluation, and interactive demos without cloud hosting overhead.
* **Telemetry & Failure Recovery:** Synchronous console output to stdout/stderr. The CLI is stateless and fails fast with exit code 1; recovery is achieved by re-running the command after correcting inputs or configuration.

### 2. Limitations of the Current Prototype at Ten-Client Scale
The local prototype architecture cannot support ten independent clients simultaneously:
* **Output Filename Collisions:** Shared output paths (`results/analysis.json`, `results/report.md`) collide and overwrite each other during concurrent runs.
* **Single Configuration / Realm:** A single active `.env` file or QuickBooks realm is insufficient for multiple independently authenticated client organizations.
* **Token Refresh Race Conditions:** Concurrent worker executions sharing OAuth credentials would attempt simultaneous token refreshes, corrupting or invalidating single-use refresh tokens.
* **Context & Data Leakage Risk:** Shared prompts, conversation context, in-memory caches, or filesystem artifacts could inadvertently expose proprietary financial data across client engagements.
* **Rate Limiting & Concurrency:** Intuit enforces API limits of 500 requests/minute and 10 concurrent requests per company/realm. Concurrency and rate limiting must be managed and throttled per company/realm independently.

### 3. Proposed Production Architecture (Cloud-Native AWS Design)
To host this system for an enterprise accounting firm supporting ten or more concurrent client engagements, the following cloud-native AWS architecture is proposed (not yet deployed). This design supports centralized multi-user operation, strong cryptographic access controls, comprehensive observability, and horizontal scaling:

```
                                [ENTERPRISE CLIENTS / FRACTIONAL CFOS]
                                                  │
                                                  │ HTTPS / TLS 1.3
                                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 AWS API GATEWAY                                        │
│ • Terminates TLS 1.3 & validates caller identity via OpenID Connect (OIDC)            │
│ • Enforces token-bucket rate limiting (500 requests/min and 10 concurrent per realm)   │
│ • Injects verified downstream context (X-Tenant-ID, X-Correlation-ID)                  │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
┌───────────────────────────────────┐           ┌───────────────────────────────────┐
│     ASYNC CALCULATION WORKERS     │           │   CONTAINERIZED MCP MICROSERVICES │
│ • AWS ECS Fargate (Stateless)     │           │ • AWS ECS Fargate / Cloud Run     │
│ • Python Engine Docker containers │           │ • TypeScript MCP microservice pool│
│ • Consumes jobs from Amazon SQS   │           │ • Strict read-only environment    │
└─────────────────┬─────────────────┘           └─────────────────┬─────────────────┘
                  │                                               │
                  ├───────────────────────┬───────────────────────┤
                  ▼                       ▼                       ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│     AMAZON S3 STORAGE     │ │   AWS SECRETS MANAGER     │ │   AMAZON CLOUDWATCH       │
│ • Encrypted bucket (KMS)  │ │ • Per-tenant OAuth vault  │ │ • Centralized JSON logs   │
│ • Tenant-prefixed storage │ │ • KMS envelope encryption │ │ • Container metric alarms │
│ • Versioned report storage│ │ • 100-day token rotation  │ │ • P99 latency monitoring  │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```

* **Serverless Compute (AWS ECS Fargate):** Containerize the Python engine and TypeScript MCP server into lightweight Docker containers executing in private VPC subnets with zero public ingress.
* **Asynchronous Queue (Amazon SQS):** Long-running workbook analyses and bulk ledger sync jobs are queued via Amazon SQS, decoupling API intake from computational workers.
* **Centralized Observability:** Structured JSON logging streamed to **Amazon CloudWatch Logs**, with metric filters tracking task execution durations and CloudWatch Alarms alerting on P99 latency or failure spikes.
* **Artifact Storage (Amazon S3):** Persist generated `analysis.json` and `report.md` artifacts in versioned, encrypted S3 buckets with automated 90-day transition to S3 Glacier.

---

## Domain D: Multi-Client Data Separation & Tenancy Boundaries

### 1. Tenancy Structure [Prototype (today)]
* **Single-Tenant Prototype:** Operates as a single-client CLI utility partitioned by filesystem paths and arguments (e.g., ABC Inc and Test Corp fixtures).
* **Local Separation Boundary:** While client runs can be segregated into local directories for development, local folder segregation does NOT provide enterprise security isolation. Ten-client enterprise scaling requires cryptographically enforced identity, storage, database, credential, and memory boundaries.

### 2. Tenancy Isolation Blueprint [Proposed Production Architecture]
To safely operate across ten or more enterprise clients, the proposed production architecture enforces strict tenant boundaries across every architectural layer:

1. **Tenant Identity & Ingress:**
   - Callers authenticate via enterprise OpenID Connect (OIDC) through Okta, Azure Active Directory, or AWS Cognito.
   - The API Gateway cryptographically verifies signed JWT identity tokens on the server, extracts claims (`iss`, `sub`, `tenant_id`), and injects an immutable `X-Tenant-ID` header into downstream requests.
   - Client-supplied tenant headers are stripped at ingress to prevent Insecure Direct Object References (IDOR); tenant ID is derived solely from verified server-side claims.
2. **Database Isolation (Proposed):**
   - PostgreSQL database utilizing **Row-Level Security (RLS)** with verified tenant context:
     ```sql
     ALTER TABLE financial_analyses ENABLE ROW LEVEL SECURITY;
     CREATE POLICY tenant_isolation_policy ON financial_analyses
       USING (tenant_id = current_setting('app.current_tenant')::uuid);
     ```
   - Every read and write is strictly scoped to the authenticated tenant. For highly regulated clients, dedicated schema-per-tenant isolation (`tenant_abc`, `tenant_xyz`) can be applied. (Note: Database architecture is proposed and not yet deployed).
3. **File and Object Storage Isolation:**
   - Storage is partitioned using tenant-scoped paths: `s3://re-financial-storage/{tenant_id}/analyses/analysis.json`.
   - AWS IAM session policies restrict compute worker access strictly to the prefix matching the caller's verified `tenant_id`.
   - Application-layer authorization prevents cross-tenant reads, writes, or listing.
4. **Tenant-Scoped Credentials & Concurrency:**
   - Store each client's QuickBooks OAuth credentials and tokens separately in **AWS Secrets Manager**: `/tenants/{tenant_id}/qbo_credentials`.
   - Access is restricted using least-privilege IAM roles; workers cannot access secrets of other tenants.
   - Refresh tokens and realm configurations are never reused across tenants. Distributed locks serialize refresh operations to prevent concurrent refresh conflicts.
5. **LLM Context and Memory Isolation:**
   - Ephemeral, stateless LLM agent sessions are created per analysis request.
   - Each session loads only that specific client's workbook, `analysis.json`, and configuration.
   - No prompts, conversation context, in-memory caches, or output artifacts are shared between tenants.
   - Persistent cross-client memory is strictly avoided.
6. **Operations, Rate Limiting & Error Isolation:**
   - Per-tenant authorization and token-bucket rate limiting enforce Intuit's 500 req/min and 10 concurrent requests per realm.
   - Asynchronous jobs and errors are tracked with tenant-safe correlation IDs (`X-Correlation-ID`).
   - Logging configurations strictly suppress financial line-item values and credential tokens.
   - Worker failures, retries, and dead-letter queues (DLQ) are isolated so one tenant's failure does not impact other clients.

---

## Live QuickBooks Sandbox Integration (Stretch Goal Details)

The optional stretch goal from the assignment was executed and verified against an isolated Intuit developer sandbox:

* **QuickBooks Sandbox Verification:** QuickBooks sandbox integration verified; tenant-specific identifiers are kept out of documentation.
* **Ingestion & Seeding Execution:**
  - Chart of Accounts: 86 planned accounts mapped (82 ABC accounts created, 4 matched to pre-existing standard accounts). All 86 accounts were verified and reused on final import with 0 accounts recreated.
  - Journal Entries: 18 balanced monthly Journal Entries posted (`ABC-2025-01` to `ABC-2026-06`) balancing to exact debits == credits ($0.00 difference).
* **Reconciliation Findings:**
  - 16 of 18 months match Excel exactly; the other 2 differ only by 3 pre-existing Intuit sandbox sample transactions ($300.00 and $391.25).
  - The ABC Inc financial dataset is isolated via its deterministic `ABC-2025-*` and `ABC-2026-*` journal entries, achieving 100% mathematical equivalence to the golden workbook.

---

## Architectural Verification & Scope Boundary Sign-Off

* **Prototype (today):**
  - Deterministic Python financial engine (Decimal cents precision, auto-sorts reverse-chronological columns, subtotal isolation, MoM % with absolute value denominators, strict 12-month TTM windows, Dec 2025 anomaly isolation, 126 reconciliation checks).
  - Reusable Claude Skill prompt with 10 negative never-rules and Fractional CFO close checklist.
  - Read-only TypeScript QuickBooks MCP server with registration-time mutation suppression (71 tools registered with write/update/delete disabled).
  - Dedicated Python developer sandbox seeder posting 18 balanced monthly Journal Entries.
  - QBO Report Adapter (`scripts/adapters/qbo_adapter.py`) where 16 of 18 months match Excel exactly; the other 2 differ only by 3 pre-existing Intuit sandbox sample transactions ($300.00 and $391.25).
  - Automated test suite (99 Pytest tests, 35 Jest test suites / 639 tests), 9 golden cases (110.0/110.0 score), and commentary evaluator (100.0/100.0).
* **Proposed Production Architecture:**
  - AWS ECS Fargate serverless microservice pools across private VPC subnets.
  - AWS API Gateway with cryptographically validated OIDC JWT identity claims and distributed token-bucket rate limiting (500 requests/min and 10 concurrent per realm).
  - AWS Secrets Manager per-tenant credential vault with customer-managed KMS envelope encryption and token rotation (100-day rolling expiry, 5-year maximum).
  - PostgreSQL Row-Level Security (RLS) and Amazon S3 per-tenant prefix partitioning (`s3://bucket/{tenant_id}/analyses/`).
  - Ephemeral, stateless LLM agent execution ensuring no prompt context shared between clients.
