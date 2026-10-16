# LLM Financial Commentary: Deterministic Numerical Grounding Audit

> [!WARNING]
> **Scope & Verification Boundary Warning**:
> This deterministic audit evaluates strictly **14 discrete structured numerical claims** against authoritative ground truth in `analysis.json`.
> **Qualitative commentary, causal interpretations (such as pricing power, cost control, seasonality, or operational efficiency), and unextracted narrative statements are NOT certified by this numerical claim check.**
> A 100% pass rate on selected numerical claims does **not** certify the entire financial report narrative as 100% accurate.

## Summary of Numerical Grounding vs. Qualitative Scope
| Audit Dimension | Result | Status | Scope / Limitation |
| :--- | :---: | :---: | :--- |
| **Tested Numerical Claims** | 14 / 14 passed (100.0%) | **PASS** | Discrete financial figures mapped to `analysis.json` |
| **Qualitative & Causal Narrative** | Unverified by claim table | ⚠️ **PENDING AUDIT** | Causal claims (seasonality, pricing power, efficiency) require CPA / FP&A confirmation |
| **Full Report Certification** | Partial | **PARTIAL** | Only verified numerical subset is certified |

### Metric Breakdown
- **Total Discrete Numerical Claims Evaluated:** 14
- **Verified Claims (Ground Truth Matched):** 14
- **Invalid Claims (Mathematical / Scale Discrepancies):** 0
- **Unverified / Disclosed Claims (Flagged for CPA Review):** 0
- **Tested Claims Accuracy Rate:** 100.0%
- **Discrete Numerical Status:** **PASS**

---

## Narrative & Qualitative Claim Review
- **Sentences Audited:** 106
- **Scale Warnings (e.g. Billions vs. Millions):** 0
- **Unverified Causal Assertions:** 0
- **Narrative Audit Status:** **NEUTRAL_OR_QUALIFIED**

---

## Detailed Claim-by-Claim Audit Table
| ID | Period | Metric | Claimed Value | Ground Truth | Status | Finding / Audit Context |
| :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | 2025-01 | revenue | $167,587.50 | $167,587.50 | ✅ **VERIFIED** | Verified metric 'revenue' for period 2025-01 (ground truth: 167587.5). |
| 2 | 2026-06 | revenue | $196,289.41 | $196,289.41 | ✅ **VERIFIED** | Verified metric 'revenue' for period 2026-06 (ground truth: 196289.41). |
| 3 | 2025-12 | operating_income | $534,551.41 | $534,551.41 | ✅ **VERIFIED** | Verified metric 'operating_income' for period 2025-12 (ground truth: 534551.41). |
| 4 | 2025-12 | normalized_operating_income | $-381,241.27 | $-381,241.27 | ✅ **VERIFIED** | Verified metric 'normalized_operating_income' for period 2025-12 (ground truth: -381241.27). |
| 5 | 2026-06 | revenue | $2,304,366.76 | $2,304,366.76 | ✅ **VERIFIED** | Verified against TTM window ending 2026-06 (ground truth: 2304366.76). |
| 6 | 2025-12 | gross_profit | $1,521,584.03 | $1,521,584.03 | ✅ **VERIFIED** | Verified against TTM window ending 2025-12 (ground truth: 1521584.03). |
| 7 | 2026-06 | operating_income | $-3,089,688.34 | $-3,089,688.34 | ✅ **VERIFIED** | Verified against TTM window ending 2026-06 (ground truth: -3089688.34). |
| 8 | 2025-06 | total_opex | $497,871.96 | $497,871.96 | ✅ **VERIFIED** | Verified metric 'total_opex' for period 2025-06 (ground truth: 497871.96). |
| 9 | 2025-12 | tax_benefit | $-1,244,429.84 | $-1,244,429.84 | ✅ **VERIFIED** | Verified ACCOUNTING_ANOMALY item 'Income Tax Benefit' for period 2025-12. |
| 10 | 2025-12 | stock_based_compensation | $334,660.53 | $334,660.53 | ✅ **VERIFIED** | Verified ACCOUNTING_ANOMALY item 'Stock-Based Compensation Expense' for period 2025-12. |
| 11 | 2025-12 | normalized_operating_income | $-4,462,347.78 | $-4,462,347.78 | ✅ **VERIFIED** | Verified against TTM window ending 2025-12 (ground truth: -4462347.78). |
| 12 | 2026-06 | normalized_operating_income | $-4,064,285.76 | $-4,064,285.76 | ✅ **VERIFIED** | Verified against TTM window ending 2026-06 (ground truth: -4064285.76). |
| 13 | 2025-12 | normalized_core_opex | $513,650.59 | $513,650.59 | ✅ **VERIFIED** | Verified metric 'normalized_core_opex' for period 2025-12 (ground truth: 513650.59). |
| 14 | 2025-12 | total_opex | $-402,142.09 | $-402,142.09 | ✅ **VERIFIED** | Verified metric 'total_opex' for period 2025-12 (ground truth: -402142.09). |
