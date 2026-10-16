"""Unit and regression tests for reconciliation exception handling and fixes.

Verifies:
1. Fix 1: CLI integrity claims calculate actual pass rate and never claim 100% on failure.
2. Fix 2: Reporter integrity claims calculate dynamic accuracy and enumerate failures.
3. Fix 3: Subtotal handling avoids double-counting (resolving the May 2026 $300 variance).
4. Fix 4: Recommendations are source-aware / source-neutral (no false 'Excel formula' claim on QBO).
5. Fix 5: Cross-dataset baseline comparison discloses June 2026 $391.25 and May 2026 $300 variances.
"""

import json
from pathlib import Path
from decimal import Decimal
import pytest

from scripts.cli import main
from scripts.engine import FinancialCalculationEngine
from scripts.reporter import FinancialReportGenerator
from scripts.adapters.qbo_adapter import QBOReportAdapter
from scripts.comparator import compare_financial_results
from scripts.models import (
    FinancialAnalysisResult,
    ReconciliationCheck,
    MonthlySummary,
    AnomalyFlag,
    Severity,
    AnomalyCategory,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = PROJECT_ROOT / "data" / "ABC Inc - Financial Statements.xlsx"
QBO_LIVE_PATH = PROJECT_ROOT / "results" / "qbo_live_pnl_report.json"
CASE7_PATH = PROJECT_ROOT / "evals" / "fixtures" / "case7_inconsistent_totals.xlsx"


class TestReconciliationFixes:
    """Tests for all 5 audit defect fixes."""

    def test_fix1_cli_integrity_reporting_on_failure(self, capsys, tmp_path):
        """FIX 1: Verify CLI reports actual discrepancies and never prints 100% on failure."""
        out_json = tmp_path / "case7_analysis.json"
        out_report = tmp_path / "case7_report.md"

        exit_code = main([
            "--input", str(CASE7_PATH),
            "--output-json", str(out_json),
            "--output-report", str(out_report),
        ])
        assert exit_code == 0
        captured = capsys.readouterr().out

        # Must NOT claim 100% reconciled
        assert "100% reconciled" not in captured
        # Must report actual failure count and pass percentage
        assert "1 discrepancy/discrepancies detected" in captured
        assert "checks passed" in captured
        assert "accuracy" in captured

    def test_fix1_cli_integrity_reporting_on_success(self, capsys, tmp_path):
        """FIX 1: Verify CLI reports 100% reconciled only when zero discrepancies exist."""
        out_json = tmp_path / "excel_analysis.json"
        out_report = tmp_path / "excel_report.md"

        exit_code = main([
            "--input", str(EXCEL_PATH),
            "--output-json", str(out_json),
            "--output-report", str(out_report),
        ])
        assert exit_code == 0
        captured = capsys.readouterr().out

        assert "100% reconciled (126/126 checks passed)" in captured

    def test_fix2_reporter_integrity_claims_on_failure(self):
        """FIX 2: Verify reporter dynamically calculates accuracy and enumerates failed checks."""
        # Create a mock result with 2 passing checks and 1 failing check
        checks = [
            ReconciliationCheck(
                metric="Total Income",
                period="2025-01",
                reported_value="100.00",
                calculated_value="100.00",
                difference="0.00",
                is_valid=True,
            ),
            ReconciliationCheck(
                metric="Total COGS",
                period="2025-01",
                reported_value="50.00",
                calculated_value="50.00",
                difference="0.00",
                is_valid=True,
            ),
            ReconciliationCheck(
                metric="Total Operating Expenses",
                period="2025-01",
                reported_value="200.00",
                calculated_value="250.00",
                difference="50.00",
                is_valid=False,
            ),
        ]
        summaries = [
            MonthlySummary(
                period="2025-01",
                label="Jan 2025",
                revenue="100.00",
                cogs="50.00",
                gross_profit="50.00",
                gross_margin_pct="50.00%",
                total_opex="200.00",
                operating_income="-150.00",
                net_income="-150.00",
            )
        ]
        result = FinancialAnalysisResult(
            company_name="Test Inc",
            statement_name="Income Statement",
            as_of_date="2025-01",
            periods_analyzed=[{"key": "2025-01", "label": "Jan 2025"}],
            months_were_reversed=False,
            missing_period_gaps=[],
            monthly_summaries=summaries,
            category_summaries=[],
            line_items=[],
            ttm_windows=[],
            reconciliation_checks=checks,
            anomalies=[],
            unmapped_accounts=[],
            metadata={},
        )

        gen = FinancialReportGenerator(result)
        report_text = gen.generate_markdown()

        # Section 1 must NOT claim zero discrepancies
        assert "zero discrepancies" not in report_text
        assert "1 arithmetic discrepancy/discrepancies detected" in report_text
        assert "66.7% accuracy" in report_text

        # Section 6 must calculate dynamic percentage and enumerate failure
        assert "**Passed Checks:** 2 / 3 (66.7% accuracy)" in report_text
        assert "Failed Checks (1):" in report_text
        assert "Total Operating Expenses (2025-01):** Reported=200.00, Calculated=250.00, Difference=50.00" in report_text

    def test_fix3_subtotal_double_counting_resolved_on_live_qbo(self):
        """FIX 3: Verify subtotal double-counting is resolved on live QuickBooks report."""
        adapter = QBOReportAdapter(QBO_LIVE_PATH)
        result = adapter.run_analysis()

        # All 126 reconciliation checks must now pass 100%
        assert len(result.reconciliation_checks) == 126
        failed_checks = [rc for rc in result.reconciliation_checks if not rc.is_valid]
        assert len(failed_checks) == 0, f"Expected 0 failed checks, got: {failed_checks}"

        # May 2026 checks must be exact $0.00 difference
        may26_checks = [rc for rc in result.reconciliation_checks if rc.period == "2026-05"]
        for mc in may26_checks:
            assert mc.is_valid is True
            assert Decimal(mc.difference) == Decimal("0.00")

        # May 2026 Total Operating Expenses must match QBO reported $479,081.03 (not double-counted $479,381.03)
        may26_opex = next(mc for mc in may26_checks if mc.metric == "Total Operating Expenses")
        assert may26_opex.calculated_value == "479081.03"
        assert may26_opex.reported_value == "479081.03"

    def test_fix4_source_neutral_recommendations(self):
        """FIX 4: Verify recommendation wording is source-aware and source-neutral."""
        # On QBO source, recommendation must point to QuickBooks auditing
        eng_qbo = FinancialCalculationEngine(str(EXCEL_PATH), source_type="quickbooks")
        # Force a failing check
        eng_qbo.reconciliation_checks.append(ReconciliationCheck(
            metric="Total Operating Expenses",
            period="2026-05",
            reported_value="100.00",
            calculated_value="200.00",
            difference="100.00",
            is_valid=False,
        ))
        eng_qbo._detect_anomalies_and_flags()
        qbo_flags = [a for a in eng_qbo.anomalies if a.category == AnomalyCategory.RECONCILIATION_DISCREPANCY]
        assert len(qbo_flags) > 0
        assert "QuickBooks" in qbo_flags[0].recommendation
        assert "Excel formula" not in qbo_flags[0].recommendation

        # On Excel source, recommendation must point to workbook formula definitions
        eng_excel = FinancialCalculationEngine(str(EXCEL_PATH), source_type="excel")
        eng_excel.reconciliation_checks.append(ReconciliationCheck(
            metric="Total Operating Expenses",
            period="2026-05",
            reported_value="100.00",
            calculated_value="200.00",
            difference="100.00",
            is_valid=False,
        ))
        eng_excel._detect_anomalies_and_flags()
        excel_flags = [a for a in eng_excel.anomalies if a.category == AnomalyCategory.RECONCILIATION_DISCREPANCY]
        assert len(excel_flags) > 0
        assert "workbook formula" in excel_flags[0].recommendation

    def test_fix5_cross_dataset_baseline_comparison(self, tmp_path):
        """FIX 5: Verify baseline comparison correctly isolates June $391.25 and May $300 variances."""
        adapter = QBOReportAdapter(QBO_LIVE_PATH)
        target_res = adapter.run_analysis()

        excel_engine = FinancialCalculationEngine(str(EXCEL_PATH))
        baseline_res = excel_engine.run_analysis()

        comparison = compare_financial_results(target_res, baseline_res)

        assert comparison["periods_compared"] == 18
        assert comparison["periods_with_zero_drift"] == 16
        assert comparison["total_variances_found"] == 7

        # Confirm June 2026 revenue variance of +$391.25
        jun26_rev = next(v for v in comparison["monthly_variances"] if v["period"] == "2026-06" and v["metric"] == "Revenue")
        assert Decimal(jun26_rev["difference"]) == Decimal("391.25")
        assert jun26_rev["is_known_sandbox_item"] is True
        assert "Invoice IDs 10 & 95" in jun26_rev["explanation"]

        # Confirm May 2026 opex variance of +$300.00
        may26_opex = next(v for v in comparison["monthly_variances"] if v["period"] == "2026-05" and v["metric"] == "Total Operating Expenses")
        assert Decimal(may26_opex["difference"]) == Decimal("300.00")
        assert may26_opex["is_known_sandbox_item"] is True
        assert "Bill ID 90" in may26_opex["explanation"]

        # Confirm Section 8 is included when baseline is provided to report generator
        gen_with_base = FinancialReportGenerator(target_res, baseline_comparison=comparison)
        report_with_base = gen_with_base.generate_markdown()
        assert "## 8. Cross-Dataset Baseline Comparison" in report_with_base
        assert "16 of 18 monthly periods match the baseline with exact $0.00 drift" in report_with_base
        assert "$+391.25" in report_with_base
        assert "$+300.00" in report_with_base

        # Confirm Section 8 is OMITTED when no baseline is supplied
        gen_without_base = FinancialReportGenerator(target_res)
        report_without_base = gen_without_base.generate_markdown()
        assert "## 8." not in report_without_base

    def test_june_2026_revenue_category_reconciles_to_monthly_revenue(self):
        """Regression test: Proves June 2026 Revenue category summary reconciles to the monthly revenue total ($196,289.41) on live QBO."""
        adapter = QBOReportAdapter(QBO_LIVE_PATH)
        result = adapter.run_analysis()

        # Find June 2026 monthly summary revenue
        jun26_summary = next(s for s in result.monthly_summaries if s.period == "2026-06")
        assert jun26_summary.revenue == "196289.41"

        # Find June 2026 Revenue category summary
        rev_cat = next(c for c in result.category_summaries if c.category == "Revenue")
        assert rev_cat.values["2026-06"] == jun26_summary.revenue
        assert Decimal(rev_cat.values["2026-06"]) == Decimal("196289.41")

