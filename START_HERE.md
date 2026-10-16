# RE Financial Services — AI Solutions Builder Submission

## Primary Reviewer Navigation Guide (START HERE)

Welcome to the **RE Financial Services AI Solutions Builder** placement assignment submission. This repository provides a complete, production-grade financial trend analysis platform that transforms complex client financial workbooks into validated executive commentary, supported by a deterministic calculation engine, automated evaluation suites, an official read-only QuickBooks Online Model Context Protocol (MCP) server, and an enterprise multi-tenant cloud architecture specification.

---

## 1. Executive Summary & Recommended Review Order

For the most efficient and structured evaluation (approximately 15–20 minutes), we recommend following this 5-step review order:

1. **Step 1: Read the Final Project Report (3 minutes)**  
   Open [`Project_Report.pdf`](Project_Report.pdf) at the project root for an executive summary of all four tasks, verified performance metrics, and deliverable locations.
2. **Step 2: Inspect Task 1 MCP Source & Saved Connection Evidence (3 minutes)**  
   Inspect the QuickBooks MCP source code in [`quickbooks-online-mcp-server/`](quickbooks-online-mcp-server/) and the visual proof in [`abc-trend-analysis/docs/screenshots/`](abc-trend-analysis/docs/screenshots/). Review tool registration safeguards in [`quickbooks-online-mcp-server/src/helpers/register-tool.ts`](quickbooks-online-mcp-server/src/helpers/register-tool.ts).
3. **Step 3: Inspect Task 2 Skill, Engine & Financial Results (4 minutes)**  
   Inspect the canonical skill in [`abc-trend-analysis/.claude/skills/monthly-trend-analysis/SKILL.md`](abc-trend-analysis/.claude/skills/monthly-trend-analysis/SKILL.md), the calculation engine in [`abc-trend-analysis/scripts/engine.py`](abc-trend-analysis/scripts/engine.py), and the generated outputs in [`abc-trend-analysis/results/analysis.json`](abc-trend-analysis/results/analysis.json) and [`abc-trend-analysis/results/report.md`](abc-trend-analysis/results/report.md).
4. **Step 4: Execute Task 3 Safe Offline Verification Commands (5 minutes)**  
   Run the single-command offline pipeline (`python scripts/run_pipeline.py --offline`), the automated test suite (`pytest`), and the golden evaluation harness (`python -m evals.run_evals`).
5. **Step 5: Review Task 4 Enterprise Architecture Note (3 minutes)**  
   Open [`architecture.pdf`](architecture.pdf) at the root (exactly 1 A4 page) and the comprehensive technical companion [`abc-trend-analysis/docs/architecture.md`](abc-trend-analysis/docs/architecture.md) detailing ten-client scaling, tenant isolation, and credential boundaries.

---

## 2. Four-Row Task-to-Evidence Mapping Table

| Task Number & Title | Main Source Code Path | Evidence & Documentation Path | Verification Command or Review Action | Expected Outcome (Actual Verified Results) |
| :--- | :--- | :--- | :--- | :--- |
| **Task 1: QuickBooks Sandbox + Claude Desktop MCP** | [`quickbooks-online-mcp-server/`](quickbooks-online-mcp-server/) (`src/index.ts`, `src/helpers/register-tool.ts`, `src/handlers/`, `src/clients/`) | [`abc-trend-analysis/docs/screenshots/`](abc-trend-analysis/docs/screenshots/) (`mcp-server-running.png`, `quickbooks-company-info.png`, `intuit-app-overview.png`), [`abc-trend-analysis/docs/connection.md`](abc-trend-analysis/docs/connection.md), [`abc-trend-analysis/results/qbo_live_pnl_report.json`](abc-trend-analysis/results/qbo_live_pnl_report.json) | Run Jest test suite:<br>`cd quickbooks-online-mcp-server`<br>`npm test` | **639 tests passed** across 35 test suites in ~11s. Registration-time mutation suppression suppresses write/update/delete tools; saved read-only P&L response verified. |
| **Task 2: Reusable Financial Trend Analysis Skill** | [`abc-trend-analysis/.claude/skills/monthly-trend-analysis/SKILL.md`](abc-trend-analysis/.claude/skills/monthly-trend-analysis/SKILL.md), [`abc-trend-analysis/scripts/engine.py`](abc-trend-analysis/scripts/engine.py), [`abc-trend-analysis/scripts/cli.py`](abc-trend-analysis/scripts/cli.py), [`abc-trend-analysis/scripts/reporter.py`](abc-trend-analysis/scripts/reporter.py) | [`abc-trend-analysis/data/ABC Inc - Financial Statements.xlsx`](abc-trend-analysis/data/ABC%20Inc%20-%20Financial%20Statements.xlsx), [`abc-trend-analysis/results/analysis.json`](abc-trend-analysis/results/analysis.json), [`abc-trend-analysis/results/report.md`](abc-trend-analysis/results/report.md), [`abc-trend-analysis/docs/screenshots/skill-*.png`](abc-trend-analysis/docs/screenshots/) | Run offline pipeline:<br>`python scripts/run_pipeline.py --offline` | **All 6 pipeline stages passed**. 18 monthly periods processed, 7 valid TTM windows, 126/126 checks reconciled (100%), Dec 2025 -$1.244M tax credit isolated to -$381k normalized loss. |
| **Task 3: Golden Cases, Regression Tests & Numerical Validation** | [`abc-trend-analysis/evals/`](abc-trend-analysis/evals/) (`run_evals.py`, `eval_commentary.py`, `numerical_validator.py`, `llm_inference.py`), [`abc-trend-analysis/tests/`](abc-trend-analysis/tests/) | [`abc-trend-analysis/evals/eval_cases.json`](abc-trend-analysis/evals/eval_cases.json), [`abc-trend-analysis/evals/fixtures/`](abc-trend-analysis/evals/fixtures/) (9 golden fixtures), [`abc-trend-analysis/evals/baseline_eval_report.json`](abc-trend-analysis/evals/baseline_eval_report.json), [`abc-trend-analysis/docs/evals.md`](abc-trend-analysis/docs/evals.md) | Run test & evaluation suites:<br>`cd abc-trend-analysis`<br>`python -m pytest -v`<br>`python -m evals.run_evals`<br>`python -m evals.eval_commentary` | **131 pytest tests passed** in ~45s; **9/9 golden cases passed** (110.0/110.0 score, +0.0 delta vs baseline, 0 regressions); **commentary evaluation 100.0/100.0** across all 4 categories. |
| **Task 4: Architecture & Ten-Client Scaling Strategy** | [`architecture.pdf`](architecture.pdf), [`abc-trend-analysis/docs/architecture.md`](abc-trend-analysis/docs/architecture.md), [`abc-trend-analysis/docs/generate_pdf.py`](abc-trend-analysis/docs/generate_pdf.py) | [`architecture.pdf`](architecture.pdf) (1-page A4 consulting PDF), [`abc-trend-analysis/docs/architecture.md`](abc-trend-analysis/docs/architecture.md) (comprehensive companion) | Inspect [`architecture.pdf`](architecture.pdf) and read [`abc-trend-analysis/docs/architecture.md`](abc-trend-analysis/docs/architecture.md) | Technical blueprint covering OIDC JWT identity, AWS Secrets Manager credential isolation, S3 tenant partitioning, PostgreSQL RLS, and CloudWatch alarms. Clear distinction between local prototype and proposed AWS cloud design. |

---

## 3. Task 1 Verification & Reviewer Instructions

The reviewer cannot automatically access the author's personal Claude Desktop account or computer.

**Verification & Evidence (about 2 minutes)**

1. **Connection evidence:** Inspect the screenshots in [`abc-trend-analysis/docs/screenshots/`](abc-trend-analysis/docs/screenshots/) showing the Claude Desktop MCP setup and connection status (`mcp-server-running.png`, `quickbooks-company-info.png`, `quickbooks-company-info-details.png`, `intuit-app-overview.png`).
2. **Workflow evidence:** Review the saved artifacts under [`abc-trend-analysis/docs/`](abc-trend-analysis/docs/) and [`abc-trend-analysis/results/`](abc-trend-analysis/results/) that document company-information retrieval and the read-only Profit & Loss workflow (`qbo_live_pnl_report.json`, `mcp_live_pnl_response.json`, `mcp_live_report.md`).
3. **Implementation evidence:** Inspect the QuickBooks MCP source in [`quickbooks-online-mcp-server/`](quickbooks-online-mcp-server/), including tool registration in [`src/helpers/register-tool.ts`](quickbooks-online-mcp-server/src/helpers/register-tool.ts) and the configured read-only safeguards, to understand how the integration works.

These submitted artifacts allow independent review without access to the author's personal Claude Desktop account. During a live review, the author can share their screen and demonstrate the connection. Reviewers who wish to reproduce the connection independently must configure their own Claude Desktop environment with their own authorized Sandbox credentials. No import or write operation is required for this demonstration.

> **Security Note:** Prefix-based tool suppression (`QUICKBOOKS_DISABLE_WRITE=true`, etc.) is an application-level prototype guard that withholds mutation tools at server startup. Complete defense-in-depth requires OAuth scope restrictions at the Intuit Developer App level and independent verification of all exposed tools.

---

## 4. Execution Modes: Offline vs. Saved Evidence vs. Live Demonstration

To ensure complete transparency during evaluation, the project defines three clear operational boundaries:

| Execution Mode | Credential Requirement | Network Access | What is Evaluated | How to Execute |
| :--- | :--- | :--- | :--- | :--- |
| **1. Offline Reproducible Pipeline (Primary Review)** | **Zero credentials needed** | **100% Offline** (No external calls) | Deterministic Python calculation engine, Decimal arithmetic, subtotal isolation, 126 reconciliation checks, 9 golden cases, commentary evaluation, and 131 unit/integration/mutation/validator tests. | `python scripts/run_pipeline.py --offline`<br>or `pytest` in `abc-trend-analysis/` |
| **2. Saved Historical Evidence Review** | **Zero credentials needed** | **100% Offline** | Verified artifacts from author's sandbox runs: saved Intuit V3 P&L JSON responses, 16 UI screenshots, Jest unit test logs, and financial diffing outputs. | Inspect files under `abc-trend-analysis/docs/screenshots/` and `abc-trend-analysis/results/` |
| **3. Live QuickBooks Sandbox Mode (Optional Stretch Goal)** | **Author's Sandbox Keys or Reviewer's own Sandbox App** | **Live HTTPS to Intuit API** | Direct OAuth token handshake, live P&L report generation from Sandbox Company US 6d74, and live MCP stdio communication. | Author screen-share demo, or reviewer configures `quickbooks-online-mcp-server/.env` with personal Intuit sandbox keys and runs `python scripts/run_pipeline.py` |

---

## 5. Exact Commands, Working Directories & Verification Outcomes

All commands below are safe, non-mutating, and reproducible without external credentials.

### Command 1: End-to-End Offline Automation Pipeline (Root Launcher)
* **Working Directory:** Project Root (`D:\RE-Financial-AI-Assignment`)
* **Command:** `python scripts/run_pipeline.py --offline`
* **What it Verifies:** Executes all 6 pipeline stages end-to-end: verifies read-only gate, validates saved QuickBooks P&L schema, runs calculation engine with baseline diffing, checks output artifact integrity, runs 9 golden evaluation cases, and executes the commentary grounding suite.
* **Expected Outcome:** `PIPELINE EXECUTION COMPLETE — ALL STAGES PASSED` (Exit code 0, completed in ~3 seconds).

### Command 2: Full Python Automated Test Suite (Pytest)
* **Working Directory:** `abc-trend-analysis/`
* **Command:** `python -m pytest -v` (or `pytest`)
* **What it Verifies:** 131 automated tests covering engine calculation logic, subtotal isolation, reverse date sorting, MoM %, TTM gating, accounting anomaly detection, QuickBooks report adapter, pipeline runner, mutation tests, reconciliation fixes, and numerical claim validators.
* **Expected Outcome:** `131 passed in ~45s` (100% pass rate).

### Command 3: Golden Evaluation Cases Regression Suite
* **Working Directory:** `abc-trend-analysis/`
* **Command:** `python -m evals.run_evals`
* **What it Verifies:** Evaluates all 9 golden edge-case fixtures (`evals/fixtures/case1_*.xlsx` through `case9_*.xlsx`) against defined assertions and checks for regression against `evals/baseline_eval_report.json`.
* **Expected Outcome:** `Overall Evaluation Score: 110.0 / 110.0 (100.0%)`, `Cases Passed: 9 / 9`, `[NO REGRESSION DETECTED]`.

### Command 4: Commentary Grounding & Quality Evaluation Harness
* **Working Directory:** `abc-trend-analysis/`
* **Command:** `python -m evals.eval_commentary`
* **What it Verifies:** Evaluates generated markdown report against 4 strict guardrails: (1) Numerical Grounding (25/25), (2) Unsupported Causal Claims (25/25), (3) Critical Anomaly Profitability Rejection (25/25), and (4) Missing Information Disclosure (25/25).
* **Expected Outcome:** `Total Score: 100.0 / 100.0 [PASSED]`.

### Command 5: Node.js QuickBooks MCP Jest Unit Test Suite
* **Working Directory:** `quickbooks-online-mcp-server/`
* **Command:** `npm test`
* **What it Verifies:** Unit tests for all QuickBooks MCP client handlers, tools, registration guards, token storage resilience, and schema parsers.
* **Expected Outcome:** `Test Suites: 35 passed, 35 total; Tests: 639 passed, 639 total` in ~11s.

### Command 6: Node.js QuickBooks P&L Schema Validation Tests
* **Working Directory:** `quickbooks-online-mcp-server/`
* **Command:** `npm run test:pnl`
* **What it Verifies:** Tests schema validator for Intuit V3 Profit & Loss JSON reports against 9 structural assertions (valid reports, non-objects, missing headers, missing columns, empty rows).
* **Expected Outcome:** `All 9 schema validation unit tests PASSED successfully`.

---

## 6. Environment Prerequisites

- **Python:** Python 3.10+ (tested on Python 3.12.0 64-bit on Windows).
  - Required packages: `openpyxl`, `pytest`, `reportlab`, `pypdf` (see `abc-trend-analysis/requirements.txt`).
  - Install command: `pip install -r abc-trend-analysis/requirements.txt`
- **Node.js:** Node.js 18+ (tested on Node.js v20+ with npm).
  - Required for running MCP server and Jest tests. Dependencies are pre-installed in `quickbooks-online-mcp-server/node_modules/` or installable via `npm install`.

---

## 7. Submission Deliverables Directory Map

```
RE-Financial-AI-Assignment/
├── START_HERE.md                      <-- Primary entry point and reviewer guide (this file)
├── README.md                          <-- Project overview & setup instructions
├── Project_Report.pdf                 <-- Clean 2-page project report (Tasks 1-4)
├── architecture.pdf                   <-- Executive 1-page LaTeX-style architecture note (Task 4)
├── .claude/skills/monthly-trend-analysis/
│   └── SKILL.md                       <-- Canonical Claude Skill definition (Tasks 1 & 2)
├── abc-trend-analysis/                <-- Core financial calculation, skill & evaluation project
│   ├── data/
│   │   └── ABC Inc - Financial Statements.xlsx  <-- Authoritative 18-month client workbook
│   ├── docs/
│   │   ├── architecture.md            <-- Comprehensive multi-tenant architecture companion (Task 4)
│   │   ├── architecture.pdf           <-- 1-page A4 consulting architecture PDF
│   │   ├── connection.md              <-- QuickBooks connection design, security & hosting (Task 1)
│   │   ├── evals.md                   <-- Evaluation harness, methodology, and rubrics (Task 3)
│   │   ├── generate_pdf.py            <-- ReportLab script compiling architecture.pdf
│   │   └── screenshots/               <-- 16 verified execution screenshots
│   ├── evals/
│   │   ├── eval_cases.json            <-- 9 golden cases specification
│   │   ├── fixtures/                  <-- 9 synthetic evaluation workbooks + QBO fixture
│   │   ├── run_evals.py               <-- Golden cases evaluation harness (110.0/110.0)
│   │   ├── eval_commentary.py         <-- Rule-based commentary evaluation harness (100.0/100.0)
│   │   ├── numerical_validator.py     <-- Deterministic numerical claim grounding validator
│   │   ├── llm_inference.py           <-- Dual Anthropic & OpenRouter review & validation harness
│   │   └── baseline_eval_report.json  <-- Fixed regression baseline report
│   ├── results/
│   │   ├── analysis.json              <-- Engine structured JSON output (18 periods)
│   │   ├── report.md                  <-- Generated executive financial summary
│   │   ├── qbo_live_pnl_report.json   <-- Saved live QuickBooks P&L response
│   │   └── llm_validation_report.md   <-- Grounding validation audit report
│   ├── scripts/
│   │   ├── engine.py                  <-- Deterministic calculation engine (Decimal arithmetic)
│   │   ├── reporter.py                <-- Markdown executive report generator
│   │   ├── cli.py                     <-- CLI entrypoint with baseline diffing
│   │   ├── models.py                  <-- Strongly-typed data models & anomaly taxonomy
│   │   ├── run_pipeline.py            <-- Automated pipeline execution script
│   │   ├── adapters/qbo_adapter.py    <-- QuickBooks Online P&L report adapter
│   │   └── tools/seed_qbo_sandbox.py  <-- Idempotent QuickBooks sandbox importer (Task 3 stretch)
│   └── tests/                         <-- 131 automated pytest tests
├── quickbooks-online-mcp-server/      <-- Official TypeScript QuickBooks Online MCP Server (Task 1)
│   ├── src/                           <-- MCP server source code
│   │   ├── index.ts                   <-- Main server entrypoint (stdio transport)
│   │   ├── helpers/register-tool.ts   <-- Tool registration & read-only safety guard
│   │   └── server/qbo-mcp-server.ts   <-- Core MCP server class
│   ├── tests/                         <-- 35 Jest test suites (639 passing tests)
│   ├── package.json                   <-- NPM configuration & scripts
│   └── .env.example                   <-- Sanitized credential template (no secrets)
└── scripts/
    ├── run_pipeline.py                <-- Root launcher for unified automation pipeline
    └── generate_final_report.py       <-- Script compiling 2-page Final Report PDF
```

---

## 8. Troubleshooting Guide (Zero Credential Exposure)

| Issue Observed | Root Cause | Safe Resolution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'openpyxl'` | Python environment missing dependencies. | Run `pip install -r abc-trend-analysis/requirements.txt` from a terminal with active internet access. |
| `ImportError: No module named scripts.engine` when running pytest from root | Pytest invoked without python module context. | Run either `cd abc-trend-analysis && pytest` or use the root launcher: `python scripts/run_pipeline.py --offline`. |
| `FATAL: Missing required .env file` when running `python scripts/run_pipeline.py` without flags | Live mode invoked without sandbox credentials. | By default, `run_pipeline.py` attempts live sandbox connection. For offline evaluation without credentials, pass the `--offline` flag: `python scripts/run_pipeline.py --offline`. |
| `npm test` fails with `Cannot find module 'jest'` | Node modules not installed in MCP directory. | Run `cd quickbooks-online-mcp-server && npm install`. |
| PowerShell script execution policy error (`ps1 cannot be loaded`) | Windows restricted execution policy for virtual environments. | Run commands directly using `python` instead of activating `.venv`, or run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. |

---

## 9. Security Mandates & Credential Protection

1. **Zero Active Secrets in Submission:** Active `.env` files, OAuth client secrets, access tokens, refresh tokens, and private API keys are strictly excluded via `.gitignore` and omitted from the submission ZIP.
2. **Sanitized Templates Only:** Configuration templates ([`quickbooks-online-mcp-server/.env.example`](quickbooks-online-mcp-server/.env.example) and [`abc-trend-analysis/.env.example`](abc-trend-analysis/.env.example)) contain placeholders only.
3. **Strict Mutation Suppression:** The MCP server suppresses all write, update, and delete tools when safety flags are active (`QUICKBOOKS_DISABLE_WRITE=true`, `QUICKBOOKS_DISABLE_UPDATE=true`, `QUICKBOOKS_DISABLE_DELETE=true`).
4. **Deterministic Financial Math:** Arithmetic is never delegated to LLMs; calculations are 100% deterministic in Python `Decimal(ROUND_HALF_UP)`.
