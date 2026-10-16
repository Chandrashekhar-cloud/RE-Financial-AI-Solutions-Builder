# CLAUDE.md — RE Financial Services AI Solutions Builder Guide

## Project Overview & Architecture

> **New to this project?** Start with [`START_HERE.md`](../START_HERE.md) at the repository root for a 5-minute orientation.

This project is an automated, deterministic financial trend analysis pipeline prototype and Claude Skill developed for fractional CFOs, FP&A professionals, and accounting close teams.

The architecture enforces a strict **separation of concerns**:
1. **Deterministic Python Engine (`scripts/engine.py`)**:
   - Executes 100% of arithmetic calculations, subtotal rollups, calendar continuity checks, Trailing-Twelve-Month (TTM) rolling windows, and reconciliation integrity audits.
   - Operates with zero probabilistic variance or rounding drift.
   - Emits structured machine-readable `results/analysis.json` and human-readable executive `results/report.md`.
2. **Probabilistic Claude Skill (`.claude/skills/monthly-trend-analysis/SKILL.md`)**:
   - Consumes `results/analysis.json` as its sole factual source.
   - Synthesizes executive commentary, explains departmental variances, and highlights audit anomalies.
   - **Strict Rule:** Claude NEVER calculates independent mathematical figures, recalculates totals, or invents financial numbers.

---

## Core Engineering Rules & Accounting Standards

### 1. Decimal-Based Monetary Calculations
- All monetary arithmetic MUST use Python's standard library `Decimal` with cents precision (`Decimal("0.01")` / `ROUND_HALF_UP`).
- Binary floating-point arithmetic (`float`) is strictly prohibited for monetary calculations to prevent precision loss and IEEE 754 floating-point drift.
- Float input values from spreadsheets must be converted via `Decimal(str(val)).quantize(CENTS)` to maintain raw precision (e.g. preserving `(330756.07999999996)` as `-330756.08`).

### 2. Subtotal Double-Counting Prevention
- Workbooks frequently interleave subtotal rows (such as `Total S & M Payroll` and `Total Marketing`) with their respective component leaf rows.
- The engine uses a dynamic backward component accumulation algorithm to resolve rollup boundaries.
- Operating expense rollups must never double-count subtotals alongside leaf items.

### 3. Trailing-Twelve-Month (TTM) Eligibility
- A rolling TTM window strictly requires **12 consecutive calendar months** with zero month gaps.
- Datasets with fewer than 12 months (e.g. 11 months) or with calendar gaps (e.g. missing March) must withhold TTM calculations and record a diagnostic flag.
- In the baseline 18-month ABC Inc dataset (January 2025 through June 2026), exactly **7 valid rolling TTM windows** exist (ending December 2025 through June 2026).

### 4. Anomaly Reporting & Non-Operating Adjustments
- **December 2025 Non-Operating Tax Credit:**
  - December 2025 contains a massive non-recurring Income Tax Benefit of `-$1,244,429.84` and Stock-Based Compensation of `+$334,660.53` within operating expenses, creating an artificial reported operating income of `+$534,551.41`.
  - The engine flags this as a **CRITICAL** anomaly and isolates **Normalized Core Operating Income** (`-$381,241.27`).
  - Developers and Claude must **NEVER claim genuine operational profitability** in December 2025.
- **March 2026 Reversals:**
  - Negative values in revenue (`Partnership Income`, `White-Label`) and COGS/Opex (`Sales Commission`, `Events`) must be flagged as negative reversals requiring credit memo or accrual true-up audit.
- **Below-the-Line Misclassifications:**
  - Net interest income/expense embedded in operating expenses must be flagged for GAAP reclassification below operating income.

### 5. Workbook Preservation
- The source workbook (`data/ABC Inc - Financial Statements.xlsx`) is an immutable, read-only source of truth.
- Developers must never modify, re-save, or overwrite the source Excel files.

---

## Anti-Hallucination & Security Mandates

1. **No Fabricated Financial Results:**
   - Never report synthetic or hallucinated numbers. Every metric in reports or evaluations must trace directly to deterministic calculations in `analysis.json`.
2. **Zero Credential Exposure:**
   - Never commit or print secrets, OAuth tokens, Client Secrets, or `.env` files.
   - QuickBooks sandbox credentials must stay confined to local, git-ignored environment configurations.
   - Use `.env.example` with empty placeholders for template documentation.

---

## Common Development Commands

### Run Full Analysis Pipeline
```powershell
python -m scripts.cli --input "data/ABC Inc - Financial Statements.xlsx" --output-json results/analysis.json --output-report results/report.md
```

### Run Unit and Integration Tests (Pytest)
```powershell
python -m pytest -v
```

### Run Evaluation Suite (Golden Cases)
```powershell
python -m evals.run_evals
```
