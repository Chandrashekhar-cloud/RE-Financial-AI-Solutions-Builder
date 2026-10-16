# Monthly Financial Trend Analysis Skill & QuickBooks Connector
**RE Financial Services — AI Solutions Builder Hiring Assignment**

A deterministic, reusable financial analysis prototype designed for fractional CFOs, FP&A analysts, and month-end accounting close teams.

---

## 1. Executive Summary & Separation of Concerns

This project implements a **strict separation of responsibilities**:

```
┌────────────────────────────────────────┐       ┌────────────────────────────────────────┐
│      Deterministic Python Engine       │       │         Claude Analysis Skill          │
│          (scripts/engine.py)           │       │   (.claude/skills/.../SKILL.md)        │
├────────────────────────────────────────┤       ├────────────────────────────────────────┤
│ • 100% Decimal arithmetic (exact cents)│       │ • Consumes structured analysis.json    │
│ • Reverse chronological sorting        │ ────> │ • Never computes independent numbers   │
│ • Backward subtotal component matching │       │ • High-judgment narrative synthesis    │
│ • MoM % with absolute value denominator│       │ • Contextualizes audit anomalies       │
│ • Rolling 12-month TTM windows         │       │ • Actionable Fractional CFO checklist  │
│ • Outputs analysis.json & report.md    │       │ • Guardrailed against hallucinations   │
└────────────────────────────────────────┘       └────────────────────────────────────────┘
```

- **Arithmetic Responsibility (Python Engine):** Python performs all financial computations, reconciliation checks, calendar gap detections, and subtotal deductions. The engine is non-destructive and leaves original workbooks untouched.
- **Narrative Responsibility (Claude Skill):** Claude is strictly forbidden from inventing numbers or performing ad-hoc mathematical calculations. Claude reads `results/analysis.json` and crafts high-judgment commentary for human CPAs.

---

## 2. Directory Layout

```
abc-trend-analysis/
├── README.md                            # Comprehensive operational documentation
├── CLAUDE.md                            # Project guide, accounting rules, security mandates
├── .gitignore                           # Git exclusions (secrets, tokens, pycache, venv)
├── .env.example                         # Safe configuration template with empty placeholders
├── requirements.txt                     # Dependencies: openpyxl, pytest
├── conftest.py                          # Pytest environment discovery configuration
├── .claude/
│   └── skills/
│       └── monthly-trend-analysis/
│           └── SKILL.md                 # Reusable Claude skill definition & CFO guardrails
├── scripts/
│   ├── __init__.py
│   ├── engine.py                        # Core financial calculation and validation engine
│   ├── models.py                        # Strongly-typed data models & anomaly taxonomy
│   ├── cli.py                           # CLI entrypoint for batch & automated runs
│   └── reporter.py                      # Formats executive Markdown report
├── evals/
│   ├── eval_cases.json                  # 9 golden eval cases (110/110) with weights & assertions
│   ├── run_evals.py                     # Evaluation test harness, grading & baseline comparison
│   ├── baseline_eval_report.json        # Golden evaluation baseline (100.0% score)
│   ├── eval_commentary.py               # Deterministic commentary grounding evaluator
│   └── fixtures/                        # Synthetic test workbooks for edge-case evals
├── tests/
│   ├── __init__.py
│   ├── test_engine.py                   # Pytest suite for calculations, ordering, TTM, anomalies
│   ├── test_cli.py                      # Pytest suite for CLI execution and output validation
│   └── test_eval_mutation.py            # Mutation tests proving grader rejects faulty outputs
├── docs/
│   ├── architecture.md                  # System architecture, hosting choices & multi-tenant scaling
│   ├── architecture.pdf                 # Executive one-page architecture note (PDF deliverable)
│   ├── connection.md                    # QuickBooks MCP connection, alternatives, hosting, credentials
│   ├── evals.md                         # Evaluation methodology, scoring rubric & regression detection
│   └── screenshots/                     # Test runs, evaluation results & QuickBooks verification screenshots
│       ├── automated-tests.png
│       ├── eval-results.png
│       ├── eval-commentary.png
│       ├── mcp-server-running.png
│       ├── intuit-app-overview.png
│       ├── quickbooks-company-info.png
│       └── quickbooks-company-info-details.png
├── data/
│   └── ABC Inc - Financial Statements.xlsx  # Read-only untouched client source workbook
└── results/
    ├── analysis.json                    # Machine-readable financial output
    ├── report.md                        # Human-readable executive financial report
    └── eval_report.json                 # Evaluation results and scoring audit log
```

---

## 3. Financial Analysis Pipeline & Accounting Rules

1. **Workbook Preservation:**
   - Raw client workbooks (e.g. `data/ABC Inc - Financial Statements.xlsx`) are treated as immutable read-only assets.
2. **Reverse Chronological Month Handling:**
   - The primary workbook lists periods in reverse order (`Jun 2026` down to `Jan 2025`).
   - The engine automatically detects reverse ordering, normalizes calendar periods, and reorders them chronologically (`Jan 2025` to `Jun 2026`).
3. **Subtotal Non-Duplication (Backward Component Matching):**
   - In P&L statements, subtotals like `Total S & M Payroll` and `Total Marketing` appear alongside their component rows.
   - The engine utilizes a dynamic backward summation algorithm to resolve which rows roll up into each subtotal.
   - Operating expense summation explicitly excludes subtotal components when adding the subtotal (or sums leaf items and excludes subtotals), eliminating double-counting.
4. **December 2025 Accounting Anomaly (Tax Credit & SBC):**
   - December 2025 contains a massive non-recurring Income Tax Benefit of `-$1,244,429.84` and Stock-Based Compensation of `+$334,660.53` inside Operating Expenses.
   - This creates an artificial reported operating income of `+$534,551.41`.
   - The engine flags this as a **CRITICAL** accounting anomaly, computes **Normalized Core Operating Loss** (`-$381,241.27`), and explicitly instructs Claude and reviewers to **never claim the business became genuinely profitable** based on this one-off credit.
5. **March 2026 Negative Reversals:**
   - Detects negative entries including Partnership Income (`-$1,608.09`), White-Label (`-$550.00`), Sales Commission (`-$3,629.87`), and Events (`-$1,133.17`).
   - Flags each as a `WARNING` / `REVERSAL` with suggested credit memo / accrual true-up investigations.
6. **Operating Expense Misclassification:**
   - Identifies Interest Income (negative values reducing opex) and Interest Expense placed inside Operating Expenses.
   - Flags them as `MISCLASSIFICATION` for reclassification to Below-the-Line Non-Operating items under US GAAP.
7. **Trailing-Twelve-Month (TTM) Rolling Windows:**
   - Enforces a strict 12 consecutive calendar month requirement with zero gaps.
   - Exactly **7 valid TTM windows** are calculated from the 18-month dataset (ending Dec 2025 through Jun 2026).
   - If a dataset has only 11 months or a missing month, TTM is withheld and a `LIMITATION` / `MISSING_PERIOD` flag is generated.
8. **MoM Percentage Change Formula:**
   - Formula: `((current - prior) / abs(prior)) * 100`.
   - Using `abs(prior)` guarantees mathematically sound percentage changes even when the prior month is negative (e.g., Dec 2025 opex `-$402k` to Jan 2026 opex `+$487k` yields `+221.28%`).
   - Suppressed (`None`) when the prior month is 0 or missing (division-by-zero protection).

---

## 4. Installation & Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ (for local QuickBooks MCP server)
- Dependencies: `openpyxl`, `pytest` (pure Python engine)

### Setup
```powershell
cd D:\RE-Financial-AI-Assignment\abc-trend-analysis
pip install -r requirements.txt
```

### Running the Financial Trend Analysis Pipeline
Execute the pipeline against the included workbook:
```powershell
python -m scripts.cli --input "data/ABC Inc - Financial Statements.xlsx" --output-json "results/analysis.json" --output-report "results/report.md"
```

**Console Output:**
```
==================================================
RE Financial Services - Monthly Trend Analysis Engine
==================================================
Loading workbook: data\ABC Inc - Financial Statements.xlsx
Successfully processed 18 monthly periods.
Months reversed in source: True
Valid TTM windows calculated: 7
Total audit flags / anomalies identified: 13
Integrity check status: 100% reconciled (126 checks passed)
Saved machine-readable JSON: results\analysis.json
Saved human-readable Report: results\report.md
==================================================
```

---

## 5. Automated Tests & Evaluation Suite

### Automated Unit & Integration Tests (Pytest)
Run all 35 deterministic unit, integration, and mutation tests:
```powershell
python -m pytest -v
```
**Results:** `35 passed in 3.80s` (see terminal verification screenshot: **[docs/screenshots/automated-tests.png](docs/screenshots/automated-tests.png)**)
- `TestMonthOrdering`: Reverse order detection, ascending chronological sorting.
- `TestDecimalArithmeticPrecision`: Cent rounding, zero binary floating-point drift.
- `TestSubtotalHandling`: Subtotal isolation, no double counting of S&M Payroll and Marketing.
- `TestMoMCalculations`: First month suppression, absolute value denominator for negative prior, zero division protection.
- `TestTTMEligibility`: Exactly 7 windows on 18 months, 11-month ineligibility, missing gap invalidation.
- `TestAccountingAnomalies`: Dec 2025 tax credit & SBC flags, normalized core loss verification, Mar 2026 reversals, interest in opex.
- `TestGeneralizationAndIntegrity`: Multi-company support (Test Corp), reconciliation corruption catch, explicit unmapped accounts reporting.
- `TestRealWorkbookRegression`: Independent ground-truth regression test on supplied `data/ABC Inc - Financial Statements.xlsx` (18 periods, Dec 2025 normalized loss, Jun 2026 TTM revenue $2.30M / 69.46% margin, Mar 2026 credit reversals).
- `test_cli`: End-to-end artifact generation and missing file exit codes.
- `test_eval_mutation`: Mutation tests verifying the grader strictly catches corrupted outputs and commentary guardrail violations.

### Golden Case Evaluation Harness
Execute the 9-case evaluation harness:
```powershell
python -m evals.run_evals
```
**Results:** `110.0 / 110.0 (100.0%) - 9 / 9 Cases Passed`

> **Note on Evaluation Fixtures vs. Supplied Workbook:** The 9 cases in `evals/eval_cases.json` run against isolated **synthetic edge fixtures** in `evals/fixtures/` specifically constructed to stress edge conditions. The supplied real dataset (`data/ABC Inc - Financial Statements.xlsx`, 18 months) is evaluated in the deterministic regression suite `TestRealWorkbookRegression`. The Python evaluation runner grades the deterministic calculation engine (`scripts/engine.py`) and does not execute `SKILL.md` or invoke Claude.

- `CASE-01` (10/10): Normal Complete Financial Data (12 months, 1 TTM, 0 discrepancies).
- `CASE-02` (15/15): Reversed Month Ordering (detected and chronologically restored).
- `CASE-03` (20/20): Dec 2025 Accounting Anomaly (critical $1.0M tax flag in synthetic fixture, SBC warning, false profitability rejected; note real ABC Inc workbook contains -$1,244,429.84).
- `CASE-04` (15/15): 11 Months vs 12 Months TTM Eligibility (TTM correctly withheld).
- `CASE-05` (10/10): Negative Line-Item Reversals (March 2026 reversals flagged).
- `CASE-06` (10/10): Missing Calendar Month Gap (detected missing March 2025).
- `CASE-07` (10/10): Inconsistent Totals & Discrepancies (caught total opex mismatch).
- `CASE-08` (10/10): Generalization to Alternative Chart of Accounts (synthetic Test Corp test fixture in `evals/fixtures/case8_different_company.xlsx` processed with 0 code changes).
- `CASE-09` (10/10): Generalized Subtotals & Multi-Department Hierarchy (Apex Dynamics fixture processed without double-counting and 100% reconciliation).

Full grading results saved to `results/eval_report.json` and documented in **[docs/evals.md](docs/evals.md#6-successful-evaluation--test-evidence)** (see terminal verification screenshot: **[docs/screenshots/eval-results.png](docs/screenshots/eval-results.png)**).

---

## 6. QuickBooks Online MCP Integration

The project includes an integration with Intuit QuickBooks Online via the official Model Context Protocol (MCP) server located at `D:\RE-Financial-AI-Assignment\quickbooks-online-mcp-server`:

> **Architectural Decoupling:** The QuickBooks Online MCP server is a standalone TypeScript MCP tool for Claude Desktop/Code. It is **completely separate** from the Python calculation engine (`scripts/engine.py`) and is **not** integrated into its data-ingestion pipeline. The Python calculation engine operates exclusively offline on Excel workbooks (`.xlsx`), with zero network or QuickBooks API dependencies.

### Connecting through Local MCP
- **Protocol:** JSON-RPC over `stdio` launched by Claude Desktop or Claude Code.
- **Configured Target:** QuickBooks Online Sandbox (`QUICKBOOKS_ENVIRONMENT=sandbox`).
- **Tools Provided:** `get_company_info`, `read_reports`, `query`, `read_accounts`, etc.

### Enforcing Read-Only Safety Flags
The official MCP server registers write tools by default unless restriction flags are explicitly set. To protect client accounting ledgers against accidental writes, the project configuration explicitly enables the following restriction environment variables:
```env
QUICKBOOKS_DISABLE_WRITE=true
QUICKBOOKS_DISABLE_UPDATE=true
QUICKBOOKS_DISABLE_DELETE=true
```
When these flags are set to `true`, mutation tools (`create_*`, `update_*`, `delete_*`) are suppressed during registration, enforcing strict read-only operation.

### Verified Sandbox Execution Evidence
Live execution screenshots confirming read-only retrieval of QuickBooks company metadata via Claude Desktop and MCP are archived in `docs/screenshots/`:
- **[mcp-server-running.png](docs/screenshots/mcp-server-running.png):** `quickbooks-sandbox` MCP server actively running in Claude Desktop via local stdio.
- **[intuit-app-overview.png](docs/screenshots/intuit-app-overview.png):** Intuit Developer Portal configuration for `ABC Financial Analysis` development app.
- **[quickbooks-company-info.png](docs/screenshots/quickbooks-company-info.png):** Successful invocation of `get_company_info` showing Company Name (`Sandbox Company US c2f2`), ID, and domain.
- **[quickbooks-company-info-details.png](docs/screenshots/quickbooks-company-info-details.png):** Verified sandbox company address, contact information, and subscription settings.
- See detailed walkthrough in **[docs/connection.md](docs/connection.md#4-connection-verification--sandbox-evidence)**.

---

## 7. Security Precautions & Credential Protection

1. **Zero Credential Leakage:** Real credentials, OAuth Client Secrets, and refresh tokens are strictly excluded from source control via `.gitignore`.
2. **Safe Template:** `.env.example` provides an empty configuration template. Real secrets must never be committed.
3. **Sandbox Isolation:** Live production QuickBooks companies are never targeted; development and testing are restricted to Intuit Developer Sandboxes.
4. **Data Privacy:** Raw accounting workbooks and output JSON/Markdown files are stored locally in designated directories.

---

## 8. Example Pipeline Outputs

### Excerpt: `results/analysis.json` (Machine-Readable Contract)
```json
{
  "company_name": "ABC Inc",
  "statement_name": "Income Statement (Profit and Loss)",
  "periods_analyzed": [
    {"key": "2025-01", "label": "Jan 2025"},
    {"key": "2026-06", "label": "Jun 2026"}
  ],
  "months_were_reversed": true,
  "monthly_summaries": [
    {
      "period": "2025-12",
      "revenue": "190029.49",
      "gross_profit": "132409.32",
      "total_opex": "-402142.09",
      "operating_income": "534551.41",
      "normalized_core_opex": "513650.59",
      "normalized_operating_income": "-381241.27"
    }
  ],
  "ttm_windows": [
    {
      "start_period": "2025-07",
      "end_period": "2026-06",
      "revenue": "2303975.51",
      "gross_profit": "1600427.91",
      "gross_margin_pct": "69.46%",
      "operating_income": "-3089779.59",
      "normalized_operating_income": "-4064377.01"
    }
  ]
}
```

### Excerpt: `results/report.md` (Executive Financial Report)
```markdown
# Monthly Financial Trend Analysis: ABC Inc
**Reporting Window:** Jan 2025 to Jun 2026 (18 Months)

## 1. Executive Summary & Headline Metrics
- Latest TTM Revenue: $2,303,975.51 with Gross Margin of 69.46%.
- Latest TTM Operating Loss: Reported $-3,089,779.59; Normalized Core Operating Loss of $-4,064,377.01.
- Data Integrity: 100% of reported subtotals and formula totals reconciled across 126 checks.

## 2. Critical Accounting Findings
- [CRITICAL] Dec 2025 Tax Benefit: One-off $1.24M tax benefit inside opex produced artificial operating profit of +$534,551.41. True normalized core operating loss was -$381,241.27.
- [WARNING] March 2026 Reversals: Negative line items in Partnership Income (-$1,608.09) and Sales Commission (-$3,629.87) require credit memo audits.
```

---

## 9. How Claude Uses the Skill

1. **User Invocation in Claude:**
   A human reviewer or Fractional CFO invokes the skill in Claude Desktop or Claude Code:
   ```
   "Run monthly trend analysis on ABC Inc's financial statements."
   ```
2. **Skill Grounding & Constraints:**
   Claude loads `.claude/skills/monthly-trend-analysis/SKILL.md` and grounds its analysis exclusively on `results/analysis.json` without calculating numbers independently.
3. **Executive Synthesis & Reviewer Checklist:**
   Claude produces high-judgment commentary, explains departmental cost dynamics, highlights the non-recurring December 2025 tax credit, and generates a prioritized close signoff checklist for the Fractional CFO.

> **Testing Boundary Note:** The deterministic calculations, reconciliation audits, markdown report generation (`results/report.md`), CLI, and 9 golden cases are fully automated and verified via Python. The Claude skill file (`SKILL.md`) defines the specialized prompt instructions and anti-hallucination guardrails that govern Claude's narrative layer when reviewing `analysis.json`.

> **Note on Dual SKILL.md Placement:** The skill definition exists at two locations intentionally. Claude Desktop and Claude Code resolve `.claude/skills/` relative to the **working directory** from which they are launched. The root-level copy (`RE-Financial-AI-Assignment/.claude/skills/monthly-trend-analysis/SKILL.md`) is active when Claude is opened from the repository root. The project-level copy (`abc-trend-analysis/.claude/skills/monthly-trend-analysis/SKILL.md`) is active when Claude is opened with `abc-trend-analysis/` as the working directory. Both copies are byte-identical (SHA-256: `7F7DFEF28A6732D8C44ABFE5C89F8C1EA4B5ED3CB0FFACAB545DC8126F0CA9CC`). No content difference exists between them.

---

## 10. Implementation Status: What Works vs. What Is Not Implemented

To provide honest, transparent communication of the system's current state:

### ✅ What Works & Is Fully Verified
1. **Deterministic Calculation Engine:**
   - 100% Python `Decimal` monetary precision quantized to cents (0 IEEE 754 float drift).
   - Dynamic backward component summation isolating subtotals (`Total S & M Payroll`, `Total Marketing`) without double-counting.
   - Reverse-chronological sequence detection & automatic chronological sorting (Jan 2025 – Jun 2026).
   - Month-over-Month % change with absolute-value denominator (`(curr - prior) / abs(prior) * 100`).
   - Rolling 12-month TTM windows (7 windows on 18 months; withholds on <12 months or calendar gaps).
   - December 2025 accounting anomaly isolation ($1.244M tax credit and $334.6k SBC) with Normalized Core Operating Loss calculation (-$381,241.27 in Dec 2025; -$4,064,377.01 in latest TTM).
   - Automated formula reconciliation (126 checks, 100% reconciled).
2. **Claude AI Trend Analysis Skill Definition:**
   - Prompt guardrails in `.claude/skills/monthly-trend-analysis/SKILL.md` strictly prohibiting ad-hoc mathematical recalculation or hallucinated figures.
   - Strict instructions to reject false profitability in December 2025 and require tax credit reclassification.
   - Actionable 5-point Fractional CFO Month-End Close Action Checklist defined for human CPA reviews.
3. **Automated Testing & Golden Evaluations:**
   - 96/96 passing Pytest unit, integration, mutation, pipeline, and adapter tests (`tests/`).
   - 9/9 passing golden evaluation cases (`evals/run_evals.py`) scoring 110.0/110.0.
   - Automated baseline comparison and regression detection against `evals/baseline_eval_report.json`.
   - Mutation test suite verifying the evaluation grader rejects deliberately corrupted inputs.
4. **QuickBooks Online Sandbox MCP Server:**
   - Local MCP server running over JSON-RPC stdio targeted to Intuit Developer Sandbox (`QUICKBOOKS_ENVIRONMENT=sandbox`).
   - Read-only protection via restriction flags (`QUICKBOOKS_DISABLE_WRITE=true`, `QUICKBOOKS_DISABLE_UPDATE=true`, `QUICKBOOKS_DISABLE_DELETE=true`).
   - Secure credential hygiene (`.env` excluded, safe `.env.example`).
5. **Documentation Deliverables:**
   - `CLAUDE.md`: System guide, engineering rules, security mandates.
   - `docs/architecture.md`: Comprehensive system architecture and 10+ client scaling blueprint.
   - `docs/architecture.pdf`: Formal 1-page executive architecture note.
   - `docs/connection.md`: MCP connection evaluation, rejected alternatives, team hosting, credential handling.
   - `docs/evals.md`: Evaluation methodology, golden cases, scoring rubric, and regression detection.

### ⚠️ What Is Not Implemented (Enterprise Cloud Scope)
1. **Multi-Tenant Database Row-Level Security (RLS):**
   - The current prototype runs locally for single-workbook analysis.
   - Multi-tenant tenant_id isolation in PostgreSQL and tenant-partitioned S3 storage are detailed in `docs/architecture.md` as production architectural designs, but not deployed in local SQLite/Postgres code.
2. **Containerized Cloud MCP Deployment:**
   - Running the MCP server in auto-scaling AWS ECS Fargate tasks behind an Application Load Balancer is fully architected in `docs/connection.md`, but not deployed as a live cloud infrastructure in this submission.
3. **Automated Secret Manager Token Rotation:**
   - Centralized token rotation (100-day rolling expiry, 5-year maximum) via AWS Secrets Manager is specified as an enterprise solution; the local prototype relies on git-ignored local configuration.
4. **Live Bi-Directional Ledger Mutation (Stretch Goal):**
   - Writing modified workbook entries back into the live QuickBooks sandbox was an optional stretch goal. To maintain strict data integrity and ledger safety, write mutations are intentionally disabled via safety flags.

---

## 11. Documentation & References
- [Architecture Deep-Dive](docs/architecture.md)
- [One-Page Architecture PDF](docs/architecture.pdf)
- [QuickBooks MCP Connection Guide](docs/connection.md)
- [Evaluation Suite & Regression Methodology](docs/evals.md)

