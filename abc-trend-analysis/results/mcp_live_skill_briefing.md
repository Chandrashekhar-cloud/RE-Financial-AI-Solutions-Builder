# Executive Financial Briefing: ABC Inc (Live QuickBooks Online Sandbox MCP Ingestion)

**Analytical Protocol:** `.claude/skills/monthly-trend-analysis/SKILL.md`  
**Source of Truth:** `results/mcp_live_analysis.json`  
**Data Origin:** QuickBooks Online Sandbox (Realm ID `9341458481035247`) retrieved via Model Context Protocol (`get_profit_and_loss` over `StdioClientTransport`)  
**Reporting Window:** January 2025 through June 2026 (18 Consecutive Monthly Periods)  
**Reconciliation Status:** 126 / 126 Checks Passed (100.0% Mathematical Integrity)  

---

### A. Executive Summary

1. **Dataset Scope & Horizon:** The deterministic calculation engine successfully processed 18 continuous calendar months from January 2025 through June 2026. Calendar continuity verification confirmed zero monthly gaps (`metadata.has_missing_period_gaps: false`), and all 126 subtotal, category, and net formula reconciliation checks reconciled with $0.00 arithmetic variance. Zero unmapped ledger accounts were detected (`metadata.unmapped_accounts_count: 0`).
2. **Top-Line Scale & Trajectory:** Top-line revenue expanded from $167,587.50 in January 2025 to a peak of $208,350.96 in May 2026, closing at $196,289.41 in June 2026 (+17.13% net top-line expansion across the 18-month horizon).
3. **Core Profitability vs. Accounting Distortion:** While reported accounting figures show a dramatic single-month positive operating income of +$534,551.41 in December 2025, **the business did not achieve genuine operational profitability**. This figure was heavily distorted by a non-recurring income tax benefit credit of -$1,244,429.84 recorded directly inside operating expenses. When normalized for this tax credit, stock-based compensation (+$334,660.53), and non-operating financing items, the underlying core operating loss for December 2025 was **-$381,241.27** (or -$375,217.90 retaining non-operating interest), consistent with ongoing operational cash burn.
4. **Cross-Dataset Reconciliation:** 16 out of 18 monthly periods demonstrate exact $0.00 variance between the live QuickBooks Online sandbox dataset and the authoritative Excel baseline. The remaining 7 variances are strictly isolated to pre-existing developer sandbox sample transactions (May 2026 Bill ID 90 for $300.00; June 2026 Invoice IDs 10 & 95 totaling $391.25 net sales).

---

### B. Key Financial Metrics

| Period | Revenue ($) | Gross Profit ($) | Gross Margin % | Total Opex ($) | Reported Op Income ($) | Normalized Core Op Income ($)* | TTM Revenue ($)** | TTM Gross Margin % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Jan 2025** | $167,587.50 | $130,636.96 | 77.95% | $513,541.99 | -$382,905.03 | -$398,075.45 | *Withheld (<12 mo)* | - |
| **Feb 2025** | $176,651.19 | $139,174.90 | 78.79% | $555,578.55 | -$416,403.65 | -$430,123.16 | *Withheld (<12 mo)* | - |
| **Mar 2025** | $170,550.65 | $120,551.31 | 70.68% | $533,111.68 | -$412,560.37 | -$427,734.86 | *Withheld (<12 mo)* | - |
| **Apr 2025** | $154,136.03 | $104,585.32 | 67.85% | $495,053.56 | -$390,468.24 | -$404,668.50 | *Withheld (<12 mo)* | - |
| **May 2025** | $169,403.74 | $121,570.67 | 71.76% | $508,416.03 | -$386,845.36 | -$400,210.05 | *Withheld (<12 mo)* | - |
| **Jun 2025** | $190,555.65 | $141,625.74 | 74.32% | $497,871.96 | -$356,246.22 | -$368,957.50 | *Withheld (<12 mo)* | - |
| **Jul 2025** | $183,919.10 | $129,337.96 | 70.32% | $455,324.92 | -$325,986.96 | -$337,606.92 | *Withheld (<12 mo)* | - |
| **Aug 2025** | $181,747.20 | $127,159.98 | 69.97% | $452,560.27 | -$325,400.29 | -$337,015.68 | *Withheld (<12 mo)* | - |
| **Sep 2025** | $181,508.47 | $124,142.13 | 68.40% | $440,317.06 | -$316,174.93 | -$327,144.42 | *Withheld (<12 mo)* | - |
| **Oct 2025** | $191,426.63 | $130,593.42 | 68.22% | $447,211.53 | -$316,618.11 | -$327,677.30 | *Withheld (<12 mo)* | - |
| **Nov 2025** | $187,800.63 | $127,900.41 | 68.10% | $444,917.84 | -$317,017.43 | -$327,816.14 | *Withheld (<12 mo)* | - |
| **Dec 2025** | $190,029.49 | $142,674.87 | 75.08% | -$402,142.09 | +$534,551.41 | -$381,241.27 | $2,145,316.28 | 71.78% |
| **Jan 2026** | $204,153.96 | $143,398.85 | 70.24% | $487,711.23 | -$344,312.38 | -$348,872.79 | $2,181,882.74 | 71.18% |
| **Feb 2026** | $183,160.30 | $123,029.47 | 67.17% | $479,936.56 | -$356,907.09 | -$346,887.14 | $2,188,391.85 | 69.42% |
| **Mar 2026** | $191,468.19 | $133,315.20 | 69.63% | $463,770.43 | -$330,455.23 | -$330,364.83 | $2,209,309.39 | 69.83% |
| **Apr 2026** | $204,512.42 | $136,476.97 | 66.73% | $469,417.80 | -$332,940.83 | -$331,378.61 | $2,259,685.78 | 70.10% |
| **May 2026** | $208,350.96 | $139,681.43 | 67.04% | $479,081.03 | -$339,399.60 | -$340,435.44 | $2,298,633.00 | 70.22% |
| **Jun 2026** | $196,289.41 | $137,816.97 | 70.21% | $468,181.80 | -$330,364.83 | -$330,500.72 | $2,304,366.76 | 69.47% |

*\*Core Operating Income excludes non-operating financing items, non-recurring tax benefits, and stock-based compensation.*  
*\*\*TTM figures are strictly withheld for the first 11 months per SKILL.md rules requiring 12 consecutive months.*

---

### C. Month-over-Month (MoM) Variance Analysis

* **Top-Line Fluctuations:**
  * **Strongest Revenue Expansion:** June 2025 experienced +$21,151.91 MoM revenue expansion (+12.49% over May 2025 $169,403.74), driven by Usage Fees expanding from $116,207.91 to $148,168.94. January 2026 expanded +$14,124.47 (+7.43% over December 2025), driven by an initial $15,833.33 Professional Services billing.
  * **Sharpest Revenue Contraction:** February 2026 experienced a -$20,993.66 MoM contraction (-10.28% against January 2026 $204,153.96), primarily reflecting Professional Services normalizing from $15,833.33 down to $833.33 (-$15,000.00).
* **Gross Margin Profile:**
  * Gross margins remained stable within a range of **66.73%** (Apr 2026) to **78.79%** (Feb 2025).
  * COGS expanded moderately alongside usage growth, moving from $36,950.54 (Jan 2025) to $58,472.44 (Jun 2026), driven primarily by Hosting expanding from $11,299.23 to $19,593.94 and Customer Success Payroll moving from $14,427.08 to $27,589.97.
* **Operating Overhead Movements:**
  * Total recurring operating expenses contracted from baseline levels of ~$513.5k–$555.6k in Q1 2025 down to ~$440.3k–$452.6k in Q3 2025, before stabilizing in the ~$463.8k–$487.7k range throughout 2026.
  * R&D payroll remained the largest single operating commitment throughout the 18 months (~$138k–$175k/mo).

---

### D. Trailing-Twelve-Month (TTM) Trends

Per the strict rules of `SKILL.md`, TTM calculations require exactly 12 consecutive calendar months with zero missing periods. Exactly 7 valid TTM windows exist across the 18-month horizon:

1. **TTM 2025-12:** Revenue $2,145,316.28 | Gross Profit $1,539,949.77 (71.78%) | Core Operating Loss -$4,727,870.93
2. **TTM 2026-01:** Revenue $2,181,882.74 | Gross Profit $1,552,711.66 (71.18%) | Core Operating Loss -$4,678,668.27
3. **TTM 2026-02:** Revenue $2,188,391.85 | Gross Profit $1,534,420.80 (70.12%) | Core Operating Loss -$4,595,432.25
4. **TTM 2026-03:** Revenue $2,209,309.39 | Gross Profit $1,547,184.69 (70.03%) | Core Operating Loss -$4,498,062.22
5. **TTM 2026-04:** Revenue $2,259,685.78 | Gross Profit $1,579,076.34 (69.88%) | Core Operating Loss -$4,424,772.33
6. **TTM 2026-05:** Revenue $2,298,633.00 | Gross Profit $1,597,187.10 (69.48%) | Core Operating Loss -$4,366,419.19
7. **TTM 2026-06:** Revenue $2,304,366.76 | Gross Profit $1,600,821.57 (69.47%) | Core Operating Loss -$4,327,962.41

**Analytical Trajectory:** TTM top-line scale demonstrated steady expansion, growing from $2.15M to $2.30M (+7.41% over the eligible rolling horizon). Concurrently, annual core operating cash burn showed gradual discipline, improving from -$4.73M in the December 2025 window to -$4.33M in the June 2026 window (+8.46% loss reduction).

---

### E. Anomalies & Data Integrity Review

#### 1. Formula Reconciliations (126 / 126 Reconciled)
* **Reconciliation Accuracy:** 100.0% of reported subtotals, income totals, COGS totals, and operating expenses reconciled against component rows across all 18 periods with $0.00 discrepancy.

#### 2. December 2025 Tax Credit & SBC Distortion
* **Non-Operating Tax Credit:** In December 2025, an Income Tax Benefit of `-$1,244,429.84` was credited directly within General & Administrative operating expenses. This flipped Total Opex from ~$440k-$450k/mo to `-$402,142.09`, creating a deceptive reported operating profit of `+$534,551.41`.
* **Stock-Based Compensation:** December 2025 also recorded a one-off non-cash stock compensation expense of `+$334,660.53` (zero in all other 17 periods).
* **Underlying Run-Rate:** Isolating these two items confirms the company remained in an ongoing core operational loss position of `-$381,241.27` (or `-$375,217.90` retaining non-operating interest).

#### 3. Negative Line-Item Reversals & Billing Credits
The deterministic engine flagged 7 negative line-item entries requiring audit review:
* **April 2025:** Referral Fees (`-$1,800.00` in COGS); Events & Conferences (`-$3,216.91` in S&M).
* **March 2026:** Partnership Income (`-$1,608.09` in Revenue); White-Label (`-$550.00` in Revenue); Sales Commission (`-$3,629.87` in COGS); Events & Conferences (`-$1,133.17` in S&M); Federal & State Taxes (`-$566.33` in G&A).
* **June 2026:** Bad Debts (`-$1,806.24` in G&A).
* *Mechanism:* Suggests prior-period true-ups, invoice credit memos, commission clawbacks, or vendor credits.

#### 4. Analytical Misclassifications
* **Interest Expense & Interest Income:** Consistently reported within General & Administrative expenses. For FP&A normalized operational evaluation, these financing elements are segregated below Operating Income.

---

### F. Reported vs. Normalized Operating Results (December 2025)

| Line Item | Reported Value ($) | Adjustment ($) | Normalized Value ($) | Accounting Rationale |
| :--- | :---: | :---: | :---: | :--- |
| **Revenue** | $190,029.49 | $0.00 | $190,029.49 | Unadjusted monthly revenue. |
| **Cost of Goods Sold** | $47,354.62 | $0.00 | $47,354.62 | Unadjusted monthly direct costs. |
| **Gross Profit** | $142,674.87 | $0.00 | $142,674.87 | Unadjusted gross profit (75.08% margin). |
| **Operating Expenses (Reported)** | -$402,142.09 | - | - | Severely distorted by non-operating tax credit. |
| *— Remove Income Tax Benefit Credit* | -$1,244,429.84 | +$1,244,429.84 | $0.00 | Non-operating tax benefit credit removed from Opex. |
| *— Remove Stock-Based Compensation* | +$334,660.53 | -$334,660.53 | $0.00 | Non-cash equity compensation isolated for cash burn. |
| *— Segregate Net Interest (Financing)* | -$6,023.37 | +$6,023.37 | $0.00 | Analytical segregation of financing interest items. |
| **Normalized Core Operating Expenses** | - | - | **$523,916.14** | True operational cash overhead run-rate. |
| **Reported Operating Income** | **+$534,551.41** | - | - | Deceptive positive accounting operating income. |
| **Normalized Core Operating Income** | - | - | **-$381,241.27** | **True underlying operational performance.** |

---

### G. Prioritized Questions for the Finance Team (CFO Close Checklist)

1. **December 2025 Tax Benefit Credit Ledger Documentation:**  
   *Inquiry:* Provide the supporting tax advisory memo and journal entry schedule for the -$1,244,429.84 credit in General & Administrative expenses. Was this an R&D tax credit monetization, valuation allowance release, or prior-year tax overpayment refund? Confirm balance sheet offset.
2. **March 2026 Revenue & COGS Reversals True-Up:**  
   *Inquiry:* Obtain credit memo documentation and client correspondence for the -$1,608.09 Partnership Income reversal, -$550.00 White-Label reversal, and -$3,629.87 Sales Commission reversal. Confirm which contract periods these adjustments pertain to.
3. **April 2025 COGS & Marketing Vendor Credits:**  
   *Inquiry:* Verify supporting credit documentation for -$1,800.00 Referral Fees in COGS and -$3,216.91 Events & Conferences. Confirm whether these reflect cash refunds or vendor credits applied against future spend.
4. **June 2026 Bad Debt Recovery / Credit Entry:**  
   *Inquiry:* Provide the subledger detail supporting the -$1,806.24 credit entry in Bad Debts for June 2026. Was this an actual collection of an account previously written off, or an adjustment to the allowance for doubtful accounts?
5. **Ongoing Reclassification of Financing Items Below Opex:**  
   *Inquiry:* Align with external auditors to reclassify Interest Expense and Interest Income into a distinct non-operating "Other Income / (Expense)" section below Operating Income on statutory reporting to preserve reported EBITDA clarity.
