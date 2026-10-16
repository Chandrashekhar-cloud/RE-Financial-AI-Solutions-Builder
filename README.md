# RE Financial Services — AI Solutions Builder Submission
**Candidate Submission Package**

---

## Quick Start for Reviewers

1. **Unzip the package** into any directory.
2. **Offline Evaluation (Zero Credentials Needed):**
   ```bash
   python scripts/run_pipeline.py --offline
   pytest
   ```
   Verified total: **131 passing Pytest tests** (111 core financial engine, reconciliation, golden case, regression, and commentary grounding tests + 20 automated LLM inference, OpenRouter integration, and numerical claim validator tests).
   All financial engine, reconciliation, golden case, commentary grounding, and validator checks run offline against the included verified dataset.
3. **Live QuickBooks Sandbox Mode (Optional Stretch Goal):**
   To execute live sandbox queries (`python scripts/run_pipeline.py`), configure `quickbooks-online-mcp-server/.env` with sandbox credentials (see `.env.example`).

---

## 1. Submission Overview

This repository contains the complete deliverables for the **RE Financial Services AI Solutions Builder** hiring assignment:

1. **Deterministic Financial Analysis Pipeline (`abc-trend-analysis/`)**:
   - Python-based calculation engine using 100% `Decimal` monetary precision quantized to cents (0 IEEE 754 floating-point drift).
   - Dynamic backward component summation isolating subtotal rows (`Total S & M Payroll`, `Total Marketing`) without double-counting.
   - Reverse-chronological period detection & chronological normalization (`Jan 2025` to `Jun 2026`).
   - Month-over-Month % change using absolute-value denominators (`(curr - prior) / abs(prior) * 100`).
   - Strict 12-consecutive-month Trailing-Twelve-Month (TTM) rolling windows (7 valid windows; withholds on <12 months or calendar gaps).
   - Accounting anomaly isolation: December 2025 non-operating tax benefit credit (`-$1,244,429.84`) and stock-based compensation (`+$334,660.53`) with Normalized Core Operating Loss calculation (`-$381,241.27`).
   - 126 automated reconciliation checks (100% reconciled).
   - Automated unit, integration, mutation, real-workbook regression, and numerical grounding validation tests (131 passing tests: 111 core engine, reconciliation, and pipeline tests + 20 LLM harness and claim validator tests).
   - Golden case evaluation harness (9 golden cases (110/110), 100.0% score, zero regression) evaluating synthetic edge fixtures in `evals/fixtures/` (distinct from the supplied real ABC Inc workbook in `data/`).

2. **Claude Trend Analysis Skill (`.claude/skills/monthly-trend-analysis/`)**:
   - Specialized Claude skill prompt (`SKILL.md`) with strict negative constraints prohibiting hallucinated or independently calculated numbers.
   - Consumes `results/analysis.json` as its single source of truth.
   - Synthesizes executive commentary, contextualizes non-operating anomalies, and generates an actionable 5-point Fractional CFO Month-End Close Checklist.
   - Dedicated offline commentary evaluation suite (`evals/eval_commentary.py`) verifying numerical grounding, absence of unsupported causal claims, and rejection of false profitability.

3. **Standalone QuickBooks Online MCP Server (`quickbooks-online-mcp-server/`)**:
   - Official Intuit Model Context Protocol (MCP) server written in TypeScript for Claude Desktop over stdio JSON-RPC.
   - **Completely separate** from the Excel-based Python engine: not connected to or integrated into the Excel data-ingestion pipeline.
   - Configured with strict read-only safety flags (`QUICKBOOKS_DISABLE_WRITE=true`, `QUICKBOOKS_DISABLE_UPDATE=true`, `QUICKBOOKS_DISABLE_DELETE=true`) to suppress mutation tools.
   - Verified live sandbox connectivity via Claude Desktop tool calls (`get_company_info`) with execution evidence screenshots.

---

## 2. Directory Structure

```
RE-Financial-AI-Assignment/
├── START_HERE.md                        # Master reviewer orientation guide (primary entry point)
├── README.md                            # Top-level submission guide & reproduction instructions
├── Project_Report.pdf                 # Official 2-page executive report (Tasks 1-4)
├── architecture.pdf                     # Executive 1-page architecture note (Task 4)
├── .claude/
│   └── skills/
│       └── monthly-trend-analysis/
│           └── SKILL.md                 # Root Claude skill definition
├── abc-trend-analysis/
│   ├── README.md                        # Comprehensive project documentation
│   ├── CLAUDE.md                        # Engineering rules, accounting standards, security mandates
│   ├── requirements.txt                 # Dependencies: openpyxl, pytest
│   ├── conftest.py                      # Pytest discovery configuration
│   ├── .env.example                     # Safe configuration template (zero credentials)
│   ├── .gitignore                       # Git exclusion rules
│   ├── .claude/
│   │   └── skills/
│   │       └── monthly-trend-analysis/
│   │           └── SKILL.md             # Project Claude skill definition
│   ├── data/
│   │   └── ABC Inc - Financial Statements.xlsx  # Untouched source workbook
│   ├── docs/
│   │   ├── architecture.md              # System architecture & multi-client scaling strategy
│   │   ├── architecture.pdf             # Executive 1-page architecture note (PDF deliverable)
│   │   ├── connection.md                # QuickBooks MCP connection evaluation & team hosting
│   │   ├── evals.md                     # Evaluation methodology, scoring rubric & regression tests
│   │   └── screenshots/                 # Verified execution screenshots
│   │       ├── automated-tests.png      # Automated test suite execution (100% passing tests)
│   │       ├── eval-results.png         # 110.0/110.0 golden case evaluation run (9/9 passed)
│   │       ├── eval-commentary.png      # 100.0/100.0 commentary evaluation run (4/4 passed)
│   │       ├── mcp-server-running.png   # MCP server running in Claude Desktop via stdio
│   │       ├── intuit-app-overview.png  # Intuit Developer portal app overview
│   │       ├── quickbooks-company-info.png          # Read-only company info query output
│   │       └── quickbooks-company-info-details.png  # Address, contact & subscription details
│   ├── evals/
│   │   ├── eval_cases.json              # 9 golden cases (110/110) with weights & assertions
│   │   ├── run_evals.py                 # Evaluation test harness & baseline comparison
│   │   ├── baseline_eval_report.json    # Golden baseline report (100.0% score)
│   │   ├── eval_commentary.py           # Commentary guardrail evaluation suite
│   │   └── fixtures/                    # Synthetic workbooks for edge-case evals
│   ├── results/
│   │   ├── analysis.json                # Deterministic machine-readable output contract
│   │   ├── report.md                    # Executive financial report
│   │   └── eval_report.json             # Evaluation run audit report
│   ├── scripts/
│   │   ├── engine.py                    # Deterministic financial calculation engine
│   │   ├── models.py                    # Strongly-typed data models & anomaly taxonomy
│   │   ├── cli.py                       # CLI entrypoint
│   │   └── reporter.py                  # Executive markdown report generator
│   └── tests/
│       ├── test_cli.py                  # CLI tests
│       ├── test_engine.py               # Calculation, ordering, TTM & anomaly tests
│       └── test_eval_mutation.py        # Mutation tests proving grader catches corruptions
└── quickbooks-online-mcp-server/
    ├── dist/                            # Compiled JavaScript entrypoint (dist/index.js)
    ├── src/                             # TypeScript source code
    ├── .env.example                     # Safe configuration template (zero credentials)
    ├── package.json                     # Dependencies and scripts
    └── README.md                        # MCP server documentation
```

---

## 3. Quickstart & Reproduction Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ (for running the local QuickBooks MCP server)

### Step 1: Install Python Dependencies
```powershell
cd abc-trend-analysis
pip install -r requirements.txt
cd ..
```

### Step 2: Single-Command End-to-End Live Pipeline (Recommended)
Execute live sandbox data retrieval, report validation, calculation engine analysis, baseline diffing, and evaluation grading with a single command from the project root:
```powershell
python scripts/run_pipeline.py
```
*(Use `--offline` to run without network queries against the saved QuickBooks report).*

### Step 3: Run Deterministic Unit, Mutation & LLM Validator Tests
Navigate to `abc-trend-analysis/` (individual test and evaluation modules must be run from `abc-trend-analysis/` unless using the unified root runner `python scripts/run_pipeline.py`):
```powershell
cd abc-trend-analysis
python -m pytest -v
```
**Expected Output:** `131 passed in ~45s` (zero failures).
- **111 Core Tests:** Calculation engine, subtotal isolation, reverse chronology detection, MoM change, rolling TTM windows, accounting anomalies, QuickBooks report adapter, pipeline runner, mutation tests, reconciliation fixes, and deterministic commentary evaluator.
- **20 Added Tests:** 9 deterministic numerical claim validator tests (`tests/test_numerical_validator.py`) and 11 automated LLM inference and OpenRouter harness tests (`tests/test_llm_inference.py`).

### Step 4: Run Golden Case Evaluation Suite
*(Execute from `abc-trend-analysis/`)*:
```powershell
python -m evals.run_evals
```
**Expected Output:** `110.0 / 110.0 (100.0%) - 9 / 9 Cases Passed` with `[NO REGRESSION DETECTED]` against `baseline_eval_report.json`.

### Step 5: Run Commentary Grounding Evaluation Suite
*(Execute from `abc-trend-analysis/`)*:
```powershell
python -m evals.eval_commentary
```
**Expected Output:** `100.0 / 100.0 (100.0%) - 4 / 4 Categories Passed` (grounding checks passed).

### Step 6: Automated LLM Review Harness & Claim Validator (Dry-Run / Mocked)
*(Execute from `abc-trend-analysis/`)*:
```powershell
# Inspect Anthropic configuration (dry-run without API calls)
python -m evals.llm_inference --dry-run

# Inspect OpenRouter configuration (dry-run without API calls)
python -m evals.llm_inference --provider openrouter --dry-run
```
> **Note on LLM Execution:** The automated harness supports both Anthropic and OpenRouter (`openrouter/free`). All prompt assembly, response parsing, and numerical grounding validation steps are fully verified offline via 100% passing mocked tests in `tests/test_llm_inference.py`. Live inference is dispatched only when user-supplied API credentials are configured in the environment.


---

## 4. QuickBooks MCP Configuration (Claude Desktop)

To run the verified QuickBooks Online MCP server locally:

```json
{
  "mcpServers": {
    "quickbooks-sandbox": {
      "command": "node",
      "args": [
        "D:\\RE-Financial-AI-Assignment\\quickbooks-online-mcp-server\\dist\\index.js"
      ],
      "env": {
        "QUICKBOOKS_ENVIRONMENT": "sandbox",
        "QUICKBOOKS_DISABLE_WRITE": "true",
        "QUICKBOOKS_DISABLE_UPDATE": "true",
        "QUICKBOOKS_DISABLE_DELETE": "true"
      }
    }
  }
}
```

> **Security Note:** In accordance with credential safety mandates, live `.env` files containing OAuth Client Secrets and refresh tokens are excluded from this submission package. Use `.env.example` to supply valid Intuit Developer Sandbox keys when connecting to a live sandbox realm.

---

## 5. Deliverable Summary & Key Documents

| Deliverable | Location | Description |
| :--- | :--- | :--- |
| **Final Project Report** | [`Project_Report.pdf`](Project_Report.pdf) | Clean 2-page project report, evidence map, and reviewer walkthrough |
| **Reviewer Orientation** | [`START_HERE.md`](START_HERE.md) | 5-minute reviewer orientation, deliverables matrix, and verification guide |
| **Claude Analysis Skill** | [`.claude/skills/monthly-trend-analysis/SKILL.md`](.claude/skills/monthly-trend-analysis/SKILL.md) | Core Claude Skill prompt definition, negative constraints, and workflow |

| **Executive Architecture Note** | [`abc-trend-analysis/docs/architecture.pdf`](abc-trend-analysis/docs/architecture.pdf) | Formal 1-page executive note on production hosting & multi-client scaling |
| **System Architecture Guide** | [`abc-trend-analysis/docs/architecture.md`](abc-trend-analysis/docs/architecture.md) | In-depth architectural evaluation and 10+ client scaling strategy |
| **QuickBooks MCP Guide** | [`abc-trend-analysis/docs/connection.md`](abc-trend-analysis/docs/connection.md) | MCP architecture, safety flags, and verified sandbox evidence |
| **Evaluation Suite Guide** | [`abc-trend-analysis/docs/evals.md`](abc-trend-analysis/docs/evals.md) | Golden cases, scoring formulas, and regression detection |
| **Executive Financial Report** | [`abc-trend-analysis/results/report.md`](abc-trend-analysis/results/report.md) | Human-readable financial trend analysis and CFO action checklist |
| **Machine Financial Contract** | [`abc-trend-analysis/results/analysis.json`](abc-trend-analysis/results/analysis.json) | Full deterministic financial model schema |

---

## 6. Scope & Design Decisions

- Commentary in `report.md` is deterministic by design, so every finance number is reproducible and auditable; the Claude Skill produces narrative for a human reviewer using `analysis.json`.
- The commentary evaluator catches fabricated numbers, wrong anomaly counts, missing disclosures and unsupported causal claims, and is verified by negative tests.
- Anomaly thresholds are configurable (`config/anomaly_thresholds.json`).
- The 7 QuickBooks-vs-Excel variances are isolated and explained (pre-existing sandbox sample data).
- Multi-client cloud hosting is a documented design in `docs/architecture.md`; the working system runs locally against the sandbox.

