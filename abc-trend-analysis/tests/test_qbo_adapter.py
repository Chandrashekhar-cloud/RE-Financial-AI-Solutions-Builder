"""
Unit and regression tests for QuickBooks Online P&L Report Adapter.

Verifies that QBO ProfitAndLoss reports are normalized accurately and produce
identical financial metrics, reconciliation checks, TTM windows, and anomalies
when compared to the authoritative source workbook.
"""

import pytest
from pathlib import Path
from decimal import Decimal

from scripts.adapters.qbo_adapter import QBOReportAdapter
from scripts.engine import FinancialCalculationEngine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = PROJECT_ROOT / "evals" / "fixtures" / "qbo_pnl_fixture.json"
EXCEL_PATH = PROJECT_ROOT / "data" / "ABC Inc - Financial Statements.xlsx"


class TestQBOReportAdapterOffline:
    """Offline unit tests for QBOReportAdapter using the verified Intuit P&L fixture."""

    def test_adapter_initialization_and_metadata(self):
        adapter = QBOReportAdapter(FIXTURE_PATH)
        assert adapter.statement_name == "ProfitAndLoss"
        assert len(adapter.month_columns) == 18
        # Verify first and last month column titles
        assert adapter.month_columns[0][1] == "Jan 2025"
        assert adapter.month_columns[-1][1] == "Jun 2026"

    def test_adapter_invalid_input_rejection(self):
        with pytest.raises(ValueError, match="Invalid QBO report"):
            QBOReportAdapter({"InvalidKey": 123})

    def test_adapter_to_workbook_generation(self, tmp_path):
        adapter = QBOReportAdapter(FIXTURE_PATH)
        out_wb = tmp_path / "test_norm_wb.xlsx"
        generated_path = adapter.to_workbook(out_wb)
        assert generated_path.exists()
        assert generated_path.stat().st_size > 0

    def test_qbo_vs_excel_end_to_end_equivalence(self, tmp_path):
        """CRITICAL REGRESSION TEST: Proves that the QuickBooks-derived pipeline

        reproduces the exact figures, reconciliations, TTM windows, and anomaly
        findings of the original Excel workbook with zero variance.
        """
        # Run standard engine on Excel
        excel_engine = FinancialCalculationEngine(str(EXCEL_PATH))
        excel_result = excel_engine.run_analysis()

        # Run QBO adapter on Intuit P&L fixture
        adapter = QBOReportAdapter(FIXTURE_PATH)
        norm_wb = tmp_path / "qbo_normalized.xlsx"
        qbo_result = adapter.run_analysis(output_workbook_path=norm_wb)

        # 1. Period coverage
        assert len(qbo_result.periods_analyzed) == 18
        qbo_periods = [p["key"] for p in qbo_result.periods_analyzed]
        excel_periods = [p["key"] for p in excel_result.periods_analyzed]
        assert qbo_periods == excel_periods

        # 2. Monthly summaries ($0.00 drift across all 18 periods)
        assert len(qbo_result.monthly_summaries) == 18
        for q_sum, e_sum in zip(qbo_result.monthly_summaries, excel_result.monthly_summaries):
            assert q_sum.period == e_sum.period
            assert Decimal(q_sum.revenue) == Decimal(e_sum.revenue), f"Revenue diff in {q_sum.period}"
            assert Decimal(q_sum.cogs) == Decimal(e_sum.cogs), f"COGS diff in {q_sum.period}"
            assert Decimal(q_sum.gross_profit) == Decimal(e_sum.gross_profit), f"GP diff in {q_sum.period}"
            assert Decimal(q_sum.total_opex) == Decimal(e_sum.total_opex), f"Opex diff in {q_sum.period}"
            assert Decimal(q_sum.operating_income) == Decimal(e_sum.operating_income), f"OI diff in {q_sum.period}"
            assert Decimal(q_sum.normalized_operating_income) == Decimal(e_sum.normalized_operating_income), (
                f"Norm OI diff in {q_sum.period}"
            )

        # 3. Trailing-Twelve-Month (TTM) windows (exactly 7 valid windows)
        assert len(qbo_result.ttm_windows) == len(excel_result.ttm_windows)
        qbo_valid_ttm = [w for w in qbo_result.ttm_windows if w.is_valid]
        excel_valid_ttm = [w for w in excel_result.ttm_windows if w.is_valid]
        assert len(qbo_valid_ttm) == 7
        assert len(excel_valid_ttm) == 7

        for q_ttm, e_ttm in zip(qbo_valid_ttm, excel_valid_ttm):
            assert q_ttm.end_period == e_ttm.end_period
            assert Decimal(q_ttm.revenue) == Decimal(e_ttm.revenue)
            assert Decimal(q_ttm.gross_profit) == Decimal(e_ttm.gross_profit)
            assert Decimal(q_ttm.total_opex) == Decimal(e_ttm.total_opex)
            assert Decimal(q_ttm.operating_income) == Decimal(e_ttm.operating_income)
            assert Decimal(q_ttm.normalized_operating_income) == Decimal(e_ttm.normalized_operating_income)

        # 4. Reconciliation integrity (126 checks, 100% pass rate)
        assert len(qbo_result.reconciliation_checks) == 126
        assert all(rc.is_valid for rc in qbo_result.reconciliation_checks)

        # 5. December 2025 Anomaly Detection
        dec_anomalies = [a for a in qbo_result.anomalies if a.period == "2025-12"]
        tax_credit_flag = next((a for a in dec_anomalies if "tax" in a.description.lower()), None)
        sbc_flag = next((a for a in dec_anomalies if "stock" in a.description.lower()), None)

        assert tax_credit_flag is not None, "Dec 2025 tax credit must be flagged"
        assert tax_credit_flag.amount == "-1244429.84"
        assert tax_credit_flag.severity.value == "CRITICAL"

        assert sbc_flag is not None, "Dec 2025 SBC must be flagged"
        assert sbc_flag.amount == "334660.53"

        # Dec 2025 Normalized Operating Income must be negative despite positive reported
        dec_summary = next(s for s in qbo_result.monthly_summaries if s.period == "2025-12")
        assert Decimal(dec_summary.operating_income) > Decimal("0.00")
        assert Decimal(dec_summary.normalized_operating_income) == Decimal("-381241.27")

        # 6. March 2026 Reversals
        mar26_anomalies = [a for a in qbo_result.anomalies if a.period == "2026-03"]
        assert len(mar26_anomalies) >= 4, "March 2026 reversals must be surfaced"

    def test_adapter_to_json_contract(self, tmp_path):
        adapter = QBOReportAdapter(FIXTURE_PATH)
        out_json = tmp_path / "qbo_analysis.json"
        out_report = tmp_path / "qbo_report.md"
        data = adapter.to_json(output_json_path=out_json, output_report_path=out_report)

        assert out_json.exists()
        assert out_report.exists()
        assert "metadata" in data
        assert "monthly_summaries" in data
        assert "ttm_windows" in data
        assert "reconciliation_checks" in data
        assert "anomalies_and_flags" in data
        assert data["metadata"]["total_periods_found"] == 18
        assert data["metadata"]["total_valid_ttm_windows"] == 7

    def test_adapter_unwraps_mcp_client_envelope(self):
        """Verify QBOReportAdapter seamlessly unwraps Claude Desktop / MCP client response envelope."""
        import json
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            raw_pnl = json.load(f)

        mcp_envelope = {
            "content": [
                {"type": "text", "text": "Profit and Loss Report:"},
                {"type": "text", "text": json.dumps(raw_pnl)},
            ]
        }

        adapter = QBOReportAdapter(mcp_envelope)
        assert adapter.statement_name == "ProfitAndLoss"
        assert len(adapter.month_columns) == 18
        result = adapter.run_analysis()
        assert len(result.periods_analyzed) == 18
        assert len(result.reconciliation_checks) == 126
        assert all(rc.is_valid for rc in result.reconciliation_checks)

    def test_adapter_unwraps_mcp_file_envelope(self, tmp_path):
        """Verify QBOReportAdapter unwraps MCP tool response envelope when loaded from file."""
        import json
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            raw_pnl = json.load(f)

        mcp_envelope = {
            "content": [
                {"type": "text", "text": "Profit and Loss Report:"},
                {"type": "text", "text": json.dumps(raw_pnl)},
            ]
        }
        mcp_file = tmp_path / "mcp_pnl_response.json"
        with open(mcp_file, "w", encoding="utf-8") as f:
            json.dump(mcp_envelope, f)

        adapter = QBOReportAdapter(mcp_file)
        assert adapter.statement_name == "ProfitAndLoss"
        assert len(adapter.month_columns) == 18
        result = adapter.run_analysis()
        assert len(result.periods_analyzed) == 18

    def test_adapter_unwraps_mcp_handler_result(self):
        """Verify QBOReportAdapter unwraps MCP handler response object."""
        import json
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            raw_pnl = json.load(f)

        handler_response = {
            "result": raw_pnl,
            "isError": False,
            "error": None,
        }
        adapter = QBOReportAdapter(handler_response)
        assert adapter.statement_name == "ProfitAndLoss"
        assert len(adapter.month_columns) == 18

