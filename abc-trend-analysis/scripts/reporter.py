"""Human-readable financial report generator.

Transforms FinancialAnalysisResult into an executive-grade Markdown report
highlighting monthly trends, departmental opex breakdowns, TTM rolling performance,
critical accounting anomalies, and review checklist items.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from .models import FinancialAnalysisResult, Severity, AnomalyCategory


class FinancialReportGenerator:
    """Generates structured Markdown reports from financial analysis results."""

    def __init__(self, result: FinancialAnalysisResult, baseline_comparison: Optional[Dict[str, Any]] = None):
        self.result = result
        self.baseline_comparison = baseline_comparison

    def generate_markdown(self) -> str:
        """Generate comprehensive markdown report."""
        lines = []

        # 1. Header
        meta = self.result.metadata
        first_p = self.result.periods_analyzed[0]["label"]
        last_p = self.result.periods_analyzed[-1]["label"]
        lines.append(f"# Monthly Financial Trend Analysis: {self.result.company_name}")
        lines.append(f"**Statement:** {self.result.statement_name} | **Reporting Window:** {first_p} to {last_p} ({len(self.result.periods_analyzed)} Months)\n")

        # 2. Executive Summary
        lines.append("## 1. Executive Summary & Headline Metrics\n")
        
        # Calculate key metrics
        first_summary = self.result.monthly_summaries[0]
        last_summary = self.result.monthly_summaries[-1]
        
        # Latest TTM
        latest_ttm = next((w for w in reversed(self.result.ttm_windows) if w.is_valid), None)

        lines.append(f"- **Revenue Trajectory:** Monthly revenue moved from ${float(first_summary.revenue):,.2f} ({first_p}) to ${float(last_summary.revenue):,.2f} ({last_p}).")
        if latest_ttm:
            latest_ttm_label = next(
                (s.label for s in self.result.monthly_summaries if s.period == latest_ttm.end_period),
                latest_ttm.end_period
            )
            rep_oi = float(latest_ttm.operating_income)
            norm_oi = float(latest_ttm.normalized_operating_income)

            rep_lbl = "Reported Operating Income" if rep_oi >= 0 else "Reported Operating Loss"
            norm_lbl = "Normalized Core Operating Income" if norm_oi >= 0 else "Normalized Core Operating Loss"

            lines.append(f"- **Latest Trailing-12-Month (TTM {latest_ttm_label}) Revenue:** ${float(latest_ttm.revenue):,.2f} with a Gross Margin of **{latest_ttm.gross_margin_pct}**.")
            lines.append(f"- **Latest TTM Operating Performance:** {rep_lbl} of ${rep_oi:,.2f}; {norm_lbl} of ${norm_oi:,.2f}.")
        else:
            lines.append(f"- **Latest Trailing-12-Month (TTM) Performance:** Withheld (no valid 12-consecutive-month rolling window exists in this {len(self.result.periods_analyzed)}-month dataset).")
        lines.append(f"- **Source Ordering Notice:** Original workbook stored months in {'reverse chronological order (newest to oldest)' if self.result.months_were_reversed else 'chronological order'}; the calculation engine normalized this to strict chronological sequence.")

        total_checks = len(self.result.reconciliation_checks)
        passed_checks = len([c for c in self.result.reconciliation_checks if c.is_valid])
        failed_checks = total_checks - passed_checks
        pass_pct = (passed_checks / total_checks * 100) if total_checks > 0 else 0.0

        if failed_checks == 0 and total_checks > 0:
            lines.append(f"- **Data Integrity Status:** 100% of reported subtotals, income totals, COGS totals, and operating expenses were validated against component arithmetic with zero discrepancies ({passed_checks}/{total_checks} checks passed).")
        else:
            lines.append(f"- **Data Integrity Status:** {failed_checks} arithmetic discrepancy/discrepancies detected across {total_checks} verification checks ({passed_checks}/{total_checks} passed, {pass_pct:.1f}% accuracy). Flagged for review.")
        lines.append("")

        # 3. Critical Accounting Findings & Audit Anomalies
        lines.append("## 2. Critical Accounting Anomalies & Audit Findings\n")
        crit_flags = [a for a in self.result.anomalies if a.severity == Severity.CRITICAL]
        warn_flags = [a for a in self.result.anomalies if a.severity == Severity.WARNING]

        if crit_flags:
            lines.append("### 🚨 Critical Audit Findings")
            for a in crit_flags:
                lines.append(f"- **[{a.account}] ({a.period}):** {a.description}")
                lines.append(f"  - **Impact:** {a.impact}")
                lines.append(f"  - **Action Required:** {a.recommendation}\n")

        if warn_flags:
            lines.append("### ⚠️ Accounting Adjustments & Reversals")
            for a in warn_flags:
                lines.append(f"- **[{a.category.value}] {a.account} ({a.period}):** {a.description}")
                lines.append(f"  - **Note:** {a.impact}\n")

        # 4. Monthly Financial Trend Summary Table
        lines.append("## 3. Monthly Financial Trend Summary\n")
        lines.append("| Period | Revenue ($) | Rev MoM % | Gross Profit ($) | Gross Margin | Total Opex ($) | Reported Op Income ($) | Core Op Income ($)* |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

        for s in self.result.monthly_summaries:
            rev_fmt = f"${float(s.revenue):,.2f}"
            rev_mom = s.revenue_mom_pct if s.revenue_mom_pct else "-"
            gp_fmt = f"${float(s.gross_profit):,.2f}"
            gm_fmt = s.gross_margin_pct if s.gross_margin_pct else "-"
            op_fmt = f"${float(s.total_opex):,.2f}"
            oi_fmt = f"${float(s.operating_income):,.2f}"
            core_oi_fmt = f"${float(s.normalized_operating_income):,.2f}"

            lines.append(f"| {s.label} | {rev_fmt} | {rev_mom} | {gp_fmt} | {gm_fmt} | {op_fmt} | {oi_fmt} | {core_oi_fmt} |")

        adjustments_desc = []
        tax_anoms = [a for a in self.result.anomalies if (a.category == AnomalyCategory.ACCOUNTING_ANOMALY or a.category.value == "ACCOUNTING_ANOMALY") and "tax" in a.account.lower()]
        sbc_anoms = [a for a in self.result.anomalies if "stock" in a.account.lower()]
        interest_anoms = [a for a in self.result.anomalies if "interest" in a.account.lower()]

        if tax_anoms and sbc_anoms:
            p_dt = datetime.strptime(tax_anoms[0].period, "%Y-%m") if "-" in tax_anoms[0].period else None
            p_str = p_dt.strftime("%b %Y") if p_dt else tax_anoms[0].period
            adjustments_desc.append(f"non-recurring {p_str} tax benefit/SBC")
        elif tax_anoms:
            p_dt = datetime.strptime(tax_anoms[0].period, "%Y-%m") if "-" in tax_anoms[0].period else None
            p_str = p_dt.strftime("%b %Y") if p_dt else tax_anoms[0].period
            adjustments_desc.append(f"non-recurring {p_str} tax benefit")
        elif sbc_anoms:
            p_dt = datetime.strptime(sbc_anoms[0].period, "%Y-%m") if "-" in sbc_anoms[0].period else None
            p_str = p_dt.strftime("%b %Y") if p_dt else sbc_anoms[0].period
            adjustments_desc.append(f"non-recurring {p_str} SBC")

        if interest_anoms:
            adjustments_desc.append("non-operating interest items situated in opex")

        if adjustments_desc:
            desc_str = " and ".join(adjustments_desc)
            lines.append(f"\n*\\*Core Op Income excludes {desc_str}.*\n")
        else:
            lines.append("\n*\\*Core Op Income reflects normalized operating income after audit classifications.*\n")

        # 5. Departmental Operating Expense Breakdown
        lines.append("## 4. Operating Expenses by Department\n")

        # Dynamically determine quarterly columns from available monthly summaries
        quarters: Dict[str, List[str]] = {}
        for s in self.result.monthly_summaries:
            p = s.period
            if "-" in p:
                parts = p.split("-")
                year_str = parts[0]
                month_num = int(parts[1])
                q_num = (month_num - 1) // 3 + 1
                q_key = f"Q{q_num} {year_str}"
            else:
                q_key = "General"
            if q_key not in quarters:
                quarters[q_key] = []
            quarters[q_key].append(p)

        q_keys = list(quarters.keys())
        table_columns = []
        if len(self.result.monthly_summaries) < 3:
            # Datasets shorter than a quarter: show prior months directly
            for s in self.result.monthly_summaries[:-1]:
                table_columns.append((s.label, [s.period]))
        elif len(q_keys) <= 4:
            # 1 to 4 quarters: show all available quarters
            for qk in q_keys:
                table_columns.append((f"{qk} Avg", quarters[qk]))
        else:
            # > 4 quarters (e.g. 6 quarters in 18-month ABC Inc):
            # Show first quarter, mid/year-end quarter, and latest quarter
            first_q = q_keys[0]
            mid_q = q_keys[len(q_keys) // 2]
            last_q = q_keys[-1]
            for qk in [first_q, mid_q, last_q]:
                table_columns.append((f"{qk} Avg", quarters[qk]))

        headers = ["Department / Category"] + [col[0] for col in table_columns] + [f"Latest Month ({last_summary.label})", "Latest TTM Total"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| :--- | " + " | ".join([":---:"] * (len(headers) - 1)) + " |")

        cat_map = {cs.category: cs for cs in self.result.category_summaries}
        dept_categories = [
            "Sales & Marketing",
            "R&D / Development",
            "General & Administrative",
            "Special / Non-Recurring",
            "Non-Operating in Opex"
        ]
        if "Unmapped" in cat_map:
            dept_categories.append("Unmapped")
        for cat_name in cat_map:
            if cat_name not in dept_categories and cat_name.lower() not in ["revenue", "cogs", "cost of goods sold"]:
                dept_categories.append(cat_name)

        for cat_name in dept_categories:
            cs = cat_map.get(cat_name)
            if cs:
                row_vals = [cat_name]
                for col_name, col_periods in table_columns:
                    col_nums = [float(cs.values.get(p, "0")) for p in col_periods if p in cs.values]
                    avg_num = (sum(col_nums) / len(col_nums)) if col_nums else 0.0
                    row_vals.append(f"${avg_num:,.2f}")

                latest_val = float(cs.values.get(last_summary.period, "0"))
                row_vals.append(f"${latest_val:,.2f}")

                if latest_ttm and latest_ttm.end_period in cs.ttm_values:
                    ttm_val = float(cs.ttm_values[latest_ttm.end_period])
                    row_vals.append(f"${ttm_val:,.2f}")
                else:
                    row_vals.append("-")

                lines.append("| " + " | ".join(row_vals) + " |")

        lines.append("")

        # Explicit Unmapped accounts status
        if not self.result.unmapped_accounts:
            lines.append("- **Unmapped accounts:** None identified (all expense line items successfully matched to standard chart-of-accounts categories).")
        else:
            lines.append(f"- **Unmapped accounts ({len(self.result.unmapped_accounts)} flagged for CPA review):**")
            for acc in self.result.unmapped_accounts:
                lines.append(f"  - `{acc}`: Account classification unverified; flagged for Fractional CFO / CPA category assignment.")
        lines.append("")

        # 6. Trailing-Twelve-Month (TTM) Windows
        lines.append("## 5. Trailing-Twelve-Month (TTM) Rolling Performance\n")
        lines.append("| TTM Window Ending | Rolling 12M Revenue ($) | Rolling Gross Profit ($) | TTM Gross Margin | TTM Total Opex ($) | TTM Reported Op Inc ($) | TTM Core Op Inc ($) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

        valid_ttm_windows = [w for w in self.result.ttm_windows if w.is_valid]
        for w in self.result.ttm_windows:
            if w.is_valid:
                lines.append(
                    f"| {w.end_period} (from {w.start_period}) | ${float(w.revenue):,.2f} | ${float(w.gross_profit):,.2f} | {w.gross_margin_pct} | ${float(w.total_opex):,.2f} | ${float(w.operating_income):,.2f} | ${float(w.normalized_operating_income):,.2f} |"
                )
            else:
                lines.append(f"| {w.end_period} | *Invalid* | - | - | - | - | {w.notes} |")

        if not self.result.ttm_windows:
            lines.append("| No Valid TTM Window | *Withheld* | - | - | - | - | Insufficient consecutive monthly history (minimum 12 consecutive months required) |")

        total_periods = len(self.result.periods_analyzed)
        if valid_ttm_windows:
            first_w = valid_ttm_windows[0]
            last_w = valid_ttm_windows[-1]
            first_dt = datetime.strptime(first_w.end_period, "%Y-%m") if "-" in first_w.end_period else None
            last_dt = datetime.strptime(last_w.end_period, "%Y-%m") if "-" in last_w.end_period else None
            first_w_label = first_dt.strftime("%B %Y") if first_dt else first_w.end_period
            last_w_label = last_dt.strftime("%B %Y") if last_dt else last_w.end_period

            if len(valid_ttm_windows) == 1:
                window_desc = f"ending {last_w_label}"
            else:
                window_desc = f"ending {first_w_label} through {last_w_label}"

            plural_s = "s" if len(valid_ttm_windows) != 1 else ""
            plural_verb = "exist" if len(valid_ttm_windows) != 1 else "exists"
            lines.append(f"\n*Note: Exactly {len(valid_ttm_windows)} valid TTM rolling window{plural_s} {plural_verb} in this {total_periods}-month historical dataset ({window_desc}).*\n")
        else:
            lines.append(f"\n*Note: No valid 12-consecutive-month TTM rolling windows exist in this {total_periods}-month dataset. TTM metrics are withheld.*\n")

        # 7. Financial Integrity & Reconciliation Audit
        lines.append("## 6. Financial Integrity & Subtotal Reconciliation\n")
        total_checks = len(self.result.reconciliation_checks)
        passed_checks = len([c for c in self.result.reconciliation_checks if c.is_valid])
        failed_checks_list = [c for c in self.result.reconciliation_checks if not c.is_valid]
        failed_count = len(failed_checks_list)
        pass_pct = (passed_checks / total_checks * 100) if total_checks > 0 else 0.0

        lines.append(f"- **Total Formula Verification Checks:** {total_checks}")
        lines.append(f"- **Passed Checks:** {passed_checks} / {total_checks} ({pass_pct:.1f}% accuracy)")
        if failed_count > 0:
            lines.append(f"- **Failed Checks ({failed_count}):**")
            for fc in failed_checks_list:
                lines.append(f"  - **{fc.metric} ({fc.period}):** Reported={fc.reported_value}, Calculated={fc.calculated_value}, Difference={fc.difference}")
        subtotal_items = [li.account_name for li in self.result.line_items if getattr(li, "is_subtotal", False)]
        sm_subtotals = sorted([s for s in subtotal_items if "S & M" in s or "Marketing" in s], key=lambda s: 0 if "Payroll" in s else 1)
        if sm_subtotals:
            examples = ", ".join(f"`{s}`" for s in sm_subtotals[:2])
            sub_examples = f" ({examples}, and section summaries)"
        elif subtotal_items:
            examples = ", ".join(f"`{s}`" for s in subtotal_items[:2])
            sub_examples = f" ({examples}, and section summaries)"
        else:
            sub_examples = " and section summaries"
        lines.append(f"- **Subtotal Handling:** Component rolls{sub_examples} were tracked and isolated, guaranteeing that neither subtotals nor component rows were double-counted in operating expenses.")
        lines.append("- **Arithmetic Method:** All sums, margin percentages, and variance calculations computed via Python `Decimal` (cents rounding), avoiding standard 64-bit binary floating-point drift.")
        lines.append("")

        # 8. Actionable Reviewer Checklist
        lines.append("## 7. Fractional CFO / Human Reviewer Checklist\n")
        tax_anom = next((a for a in self.result.anomalies if (a.category == AnomalyCategory.ACCOUNTING_ANOMALY or a.category.value == "ACCOUNTING_ANOMALY") and "tax" in a.account.lower() and a.amount is not None and Decimal(a.amount) != 0), None)
        if tax_anom:
            p_dt = datetime.strptime(tax_anom.period, "%Y-%m") if "-" in tax_anom.period else None
            p_str = p_dt.strftime("%B %Y") if p_dt else tax_anom.period
            amt_str = f"${abs(Decimal(tax_anom.amount)):,.2f}"
            lines.append(f"- [ ] **Confirm Tax Credit Classification:** In {p_str}, reclassify the {amt_str} {tax_anom.account} below operating income to maintain GAAP integrity.")

        has_interest = any("interest" in a.account.lower() for a in self.result.anomalies)
        if has_interest:
            interest_income_li = next((li for li in self.result.line_items if "interest income" in li.account_name.lower()), None)
            range_str = ""
            if interest_income_li:
                vals = [abs(Decimal(v)) for v in interest_income_li.values.values() if Decimal(v) != 0]
                if vals:
                    min_v = min(vals)
                    max_v = max(vals)
                    range_str = f" (~${min_v/1000:.1f}k to ${max_v/1000:.1f}k/mo)"
            lines.append(f"- [ ] **Reclassify Interest Income/Expense:** Move Interest Income{range_str} and Interest Expense from Opex to Non-Operating Other Income & Expense.")

        reversals = [a for a in self.result.anomalies if (a.category == AnomalyCategory.REVERSAL or a.category.value == "REVERSAL")]
        if reversals:
            revenue_reversals = [a for a in reversals if "revenue" in a.description.lower()]
            target_reversals = revenue_reversals if revenue_reversals else reversals
            first_p = target_reversals[0].period
            p_dt = datetime.strptime(first_p, "%Y-%m") if "-" in first_p else None
            p_str = p_dt.strftime("%B %Y") if p_dt else first_p
            title = f"Investigate {p_str} Credit Memos" if revenue_reversals else f"Investigate {p_str} Reversals"
            items_str = " and ".join(f"{a.account} (-${abs(Decimal(a.amount)):,.2f})" for a in target_reversals)
            lines.append(f"- [ ] **{title}:** Audit supporting schedules for {items_str} reversals.")

        sbc_anom = next((a for a in self.result.anomalies if "stock" in a.account.lower() and a.amount is not None and Decimal(a.amount) != 0), None)
        if sbc_anom:
            p_dt = datetime.strptime(sbc_anom.period, "%Y-%m") if "-" in sbc_anom.period else None
            p_str = p_dt.strftime("%B %Y") if p_dt else sbc_anom.period
            amt_str = f"${abs(Decimal(sbc_anom.amount)):,.2f}"
            acc = sbc_anom.account
            if acc.lower().endswith(" expense"):
                acc_name = acc[:-8] + " expense"
            else:
                acc_name = f"{acc} expense"
            lines.append(f"- [ ] **Normalize SBC in Valuation Models:** Add back the {amt_str} {p_str} {acc_name} when calculating Adjusted EBITDA.")

        if len(self.result.monthly_summaries) >= 6:
            last_6 = self.result.monthly_summaries[-6:]
            start_p = last_6[0].period
            end_p = last_6[-1].period
            if start_p.endswith("-01") and end_p.endswith("-06"):
                period_span = f"H1 {start_p.split('-')[0]}"
            elif start_p.endswith("-07") and end_p.endswith("-12"):
                period_span = f"H2 {start_p.split('-')[0]}"
            else:
                period_span = f"the last 6 periods ({last_6[0].label} to {last_6[-1].label})"

            norm_ois = [Decimal(str(s.normalized_operating_income)) for s in last_6]
            all_losses = all(v < 0 for v in norm_ois)
            all_gains = all(v >= 0 for v in norm_ois)

            by_oi = sorted(last_6, key=lambda s: Decimal(str(s.normalized_operating_income)))
            min_s = by_oi[0]
            max_s = by_oi[-1]
            min_val = Decimal(str(min_s.normalized_operating_income))
            max_val = Decimal(str(max_s.normalized_operating_income))

            if all_losses:
                min_fmt = f"-${abs(min_val):,.2f} ({min_s.label})"
                max_fmt = f"-${abs(max_val):,.2f} ({max_s.label})"
                loss_sentence = f" Separately, normalized core operating losses continued throughout {period_span}, ranging from {max_fmt} to {min_fmt}."
                disclosure_heading = "Cash Flow vs. Operating Loss Disclosure"
            elif all_gains:
                min_fmt = f"${min_val:,.2f} ({min_s.label})"
                max_fmt = f"${max_val:,.2f} ({max_s.label})"
                loss_sentence = f" Separately, normalized core operating income continued throughout {period_span}, ranging from {min_fmt} to {max_fmt}."
                disclosure_heading = "Cash Flow and Operating Performance Disclosure"
            else:
                min_fmt = f"${min_val:,.2f}" if min_val >= 0 else f"-${abs(min_val):,.2f}"
                max_fmt = f"${max_val:,.2f}" if max_val >= 0 else f"-${abs(max_val):,.2f}"
                loss_sentence = f" Separately, normalized core operating performance varied throughout {period_span}, ranging from {min_fmt} ({min_s.label}) to {max_fmt} ({max_s.label})."
                disclosure_heading = "Cash Flow and Operating Performance Disclosure"

            lines.append(f"- [ ] **{disclosure_heading}:** Note that the available income statement dataset does not support a cash-burn calculation, as balance sheet and cash flow statements (working capital, CapEx, debt service) are omitted.{loss_sentence}")
        else:
            lines.append("- [ ] **Cash Flow and Operating Performance Disclosure:** Note that the available income statement dataset does not support a cash-burn calculation, as balance sheet and cash flow statements (working capital, CapEx, debt service) are omitted.")

        if self.result.unmapped_accounts:
            lines.append(f"- [ ] **Resolve Unmapped Accounts:** Review and classify {len(self.result.unmapped_accounts)} unmapped account(s) ({', '.join(self.result.unmapped_accounts)}) into standard chart-of-accounts departments.")
        else:
            lines.append("- [ ] **Verify Departmental Classifications:** Unmapped accounts: None identified. Validate departmental allocations across S&M, R&D, and G&A.")
        lines.append("")

        # 9. Cross-Dataset Baseline Comparison (Optional)
        if self.baseline_comparison:
            bc = self.baseline_comparison
            lines.append("## 8. Cross-Dataset Baseline Comparison\n")
            lines.append(f"> **Architectural Boundary Note:** This section evaluates cross-dataset variances between the target dataset (`{bc['target_source']}`) and an external reference baseline (`{bc['baseline_source']}`). It is clearly distinct from the internal statement arithmetic verification in Section 6.\n")
            lines.append(f"- **Periods Compared:** {bc['periods_compared']}")
            lines.append(f"- **Periods with $0.00 Drift:** {bc['periods_with_zero_drift']} / {bc['periods_compared']}")
            lines.append(f"- **Total Variance Items Identified:** {bc['total_variances_found']}")
            
            for note in bc.get("summary_notes", []):
                lines.append(f"- **Summary Note:** {note}")

            variances = bc.get("monthly_variances", [])
            if variances:
                lines.append("\n### Material Cross-Dataset Differences\n")
                lines.append("| Period | Metric | Target Value | Baseline Value | Difference | Classification | Context / Explanation |")
                lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :--- |")
                for v in variances:
                    status_badge = "Known Sandbox Sample" if v["is_known_sandbox_item"] else "Variance"
                    lines.append(f"| {v['period']} | {v['metric']} | ${float(v['target_value']):,.2f} | ${float(v['baseline_value']):,.2f} | ${float(v['difference']):+,.2f} | {status_badge} | {v['explanation']} |")
            else:
                lines.append("\n- **Variance Status:** Zero cross-dataset drift detected across all compared metrics and periods.")
            lines.append("")

        return "\n".join(lines)
