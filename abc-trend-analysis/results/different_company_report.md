# Monthly Financial Trend Analysis: Test Corp
**Statement:** Income Statement (Profit and Loss) | **Reporting Window:** Jan 2025 to Dec 2025 (12 Months)

## 1. Executive Summary & Headline Metrics

- **Revenue Trajectory:** Monthly revenue moved from $300,000.00 (Jan 2025) to $432,000.00 (Dec 2025).
- **Latest Trailing-12-Month (TTM Dec 2025) Revenue:** $4,392,000.00 with a Gross Margin of **81.35%**.
- **Latest TTM Operating Performance:** Reported Operating Income of $1,533,000.00; Normalized Core Operating Income of $1,533,000.00.
- **Source Ordering Notice:** Original workbook stored months in chronological order; the calculation engine normalized this to strict chronological sequence.
- **Data Integrity Status:** 100% of reported subtotals, income totals, COGS totals, and operating expenses were validated against component arithmetic with zero discrepancies (60/60 checks passed).

## 2. Critical Accounting Anomalies & Audit Findings

## 3. Monthly Financial Trend Summary

| Period | Revenue ($) | Rev MoM % | Gross Profit ($) | Gross Margin | Total Opex ($) | Reported Op Income ($) | Core Op Income ($)* |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Jan 2025 | $300,000.00 | - | $240,000.00 | 80.00% | $170,000.00 | $70,000.00 | $70,000.00 |
| Feb 2025 | $312,000.00 | 4.00% | $250,500.00 | 80.29% | $170,000.00 | $80,500.00 | $80,500.00 |
| Mar 2025 | $324,000.00 | 3.85% | $261,000.00 | 80.56% | $170,000.00 | $91,000.00 | $91,000.00 |
| Apr 2025 | $336,000.00 | 3.70% | $271,500.00 | 80.80% | $170,000.00 | $101,500.00 | $101,500.00 |
| May 2025 | $348,000.00 | 3.57% | $282,000.00 | 81.03% | $170,000.00 | $112,000.00 | $112,000.00 |
| Jun 2025 | $360,000.00 | 3.45% | $292,500.00 | 81.25% | $170,000.00 | $122,500.00 | $122,500.00 |
| Jul 2025 | $372,000.00 | 3.33% | $303,000.00 | 81.45% | $170,000.00 | $133,000.00 | $133,000.00 |
| Aug 2025 | $384,000.00 | 3.23% | $313,500.00 | 81.64% | $170,000.00 | $143,500.00 | $143,500.00 |
| Sep 2025 | $396,000.00 | 3.13% | $324,000.00 | 81.82% | $170,000.00 | $154,000.00 | $154,000.00 |
| Oct 2025 | $408,000.00 | 3.03% | $334,500.00 | 81.99% | $170,000.00 | $164,500.00 | $164,500.00 |
| Nov 2025 | $420,000.00 | 2.94% | $345,000.00 | 82.14% | $170,000.00 | $175,000.00 | $175,000.00 |
| Dec 2025 | $432,000.00 | 2.86% | $355,500.00 | 82.29% | $170,000.00 | $185,500.00 | $185,500.00 |

*\*Core Op Income reflects normalized operating income after audit classifications.*

## 4. Operating Expenses by Department

| Department / Category | Q1 2025 Avg | Q2 2025 Avg | Q3 2025 Avg | Q4 2025 Avg | Latest Month (Dec 2025) | Latest TTM Total |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Sales & Marketing | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 |
| R&D / Development | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 |
| General & Administrative | $30,000.00 | $30,000.00 | $30,000.00 | $30,000.00 | $30,000.00 | $360,000.00 |
| Special / Non-Recurring | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 |
| Non-Operating in Opex | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 |
| Unmapped | $140,000.00 | $140,000.00 | $140,000.00 | $140,000.00 | $140,000.00 | $1,680,000.00 |

- **Unmapped accounts (2 flagged for CPA review):**
  - `Engineering Salaries`: Account classification unverified; flagged for Fractional CFO / CPA category assignment.
  - `Growth & Customer Acquisition`: Account classification unverified; flagged for Fractional CFO / CPA category assignment.

## 5. Trailing-Twelve-Month (TTM) Rolling Performance

| TTM Window Ending | Rolling 12M Revenue ($) | Rolling Gross Profit ($) | TTM Gross Margin | TTM Total Opex ($) | TTM Reported Op Inc ($) | TTM Core Op Inc ($) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 2025-12 (from 2025-01) | $4,392,000.00 | $3,573,000.00 | 81.35% | $2,040,000.00 | $1,533,000.00 | $1,533,000.00 |

*Note: Exactly 1 valid TTM rolling window exists in this 12-month historical dataset (ending December 2025).*

## 6. Financial Integrity & Subtotal Reconciliation

- **Total Formula Verification Checks:** 60
- **Passed Checks:** 60 / 60 (100.0% accuracy)
- **Subtotal Handling:** Component rolls and section summaries were tracked and isolated, guaranteeing that neither subtotals nor component rows were double-counted in operating expenses.
- **Arithmetic Method:** All sums, margin percentages, and variance calculations computed via Python `Decimal` (cents rounding), avoiding standard 64-bit binary floating-point drift.

## 7. Fractional CFO / Human Reviewer Checklist

- [ ] **Cash Flow and Operating Performance Disclosure:** Note that the available income statement dataset does not support a cash-burn calculation, as balance sheet and cash flow statements (working capital, CapEx, debt service) are omitted. Separately, normalized core operating income continued throughout H2 2025, ranging from $133,000.00 (Jul 2025) to $185,500.00 (Dec 2025).
- [ ] **Resolve Unmapped Accounts:** Review and classify 2 unmapped account(s) (Engineering Salaries, Growth & Customer Acquisition) into standard chart-of-accounts departments.
