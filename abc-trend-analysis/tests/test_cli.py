"""Pytest test suite for CLI and end-to-end output generation."""

import json
from pathlib import Path
import pytest

from scripts.cli import main


BASE_DIR = Path(__file__).resolve().parent.parent
ABC_WORKBOOK = BASE_DIR / "data" / "ABC Inc - Financial Statements.xlsx"


def test_cli_end_to_end_execution(tmp_path):
    output_json = tmp_path / "test_analysis.json"
    output_report = tmp_path / "test_report.md"

    exit_code = main([
        "--input", str(ABC_WORKBOOK),
        "--output-json", str(output_json),
        "--output-report", str(output_report),
        "--quiet",
    ])

    assert exit_code == 0
    assert output_json.exists()
    assert output_report.exists()

    # Validate generated JSON structure
    with open(output_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "monthly_summaries" in data
    assert "ttm_windows" in data
    assert "reconciliation_checks" in data
    assert "anomalies_and_flags" in data

    assert data["metadata"]["company_name"] == "ABC Inc"
    assert data["metadata"]["total_periods_found"] == 18
    assert data["metadata"]["total_valid_ttm_windows"] == 7
    assert data["metadata"]["months_were_reversed_in_source"] is True
    assert "unmapped_accounts" in data["metadata"]
    assert data["metadata"]["unmapped_accounts_count"] == 0

    # Validate generated Markdown report content
    with open(output_report, "r", encoding="utf-8") as f:
        report_text = f.read()

    assert "Monthly Financial Trend Analysis: ABC Inc" in report_text
    assert "Jan 2025 to Jun 2026" in report_text
    assert "TTM Jun 2026" in report_text
    assert "Critical Accounting Anomalies & Audit Findings" in report_text
    assert "Income Tax Benefit" in report_text
    assert "Trailing-Twelve-Month (TTM) Rolling Performance" in report_text
    assert "Exactly 7 valid TTM rolling windows exist in this 18-month historical dataset (ending December 2025 through June 2026)." in report_text
    assert "Reported Operating Loss of $-3,089,779.59" in report_text
    assert "Normalized Core Operating Loss of $-4,064,377.01" in report_text
    assert "Unmapped accounts: None identified" in report_text
    assert "normalized cash burn has averaged" not in report_text.lower()
    assert "does not support a cash-burn calculation" in report_text.lower()
    assert "normalized core operating losses continued throughout" in report_text.lower()


def test_cli_missing_input_file(tmp_path):
    missing_file = tmp_path / "non_existent.xlsx"
    exit_code = main([
        "--input", str(missing_file),
        "--quiet",
    ])

    assert exit_code == 1


def test_cli_qbo_json_end_to_end_execution(tmp_path):
    qbo_fixture = BASE_DIR / "evals" / "fixtures" / "qbo_pnl_fixture.json"
    output_json = tmp_path / "qbo_cli_analysis.json"
    output_report = tmp_path / "qbo_cli_report.md"

    exit_code = main([
        "--qbo-json", str(qbo_fixture),
        "--output-json", str(output_json),
        "--output-report", str(output_report),
        "--quiet",
    ])

    assert exit_code == 0
    assert output_json.exists()
    assert output_report.exists()

    with open(output_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "monthly_summaries" in data
    assert "ttm_windows" in data
    assert "reconciliation_checks" in data
    assert data["metadata"]["total_periods_found"] == 18
    assert data["metadata"]["total_valid_ttm_windows"] == 7

    with open(output_report, "r", encoding="utf-8") as f:
        report_text = f.read()

    assert "Monthly Financial Trend Analysis: ABC Inc" in report_text
    assert "Trailing-Twelve-Month (TTM) Rolling Performance" in report_text


def test_cli_qbo_json_missing_file(tmp_path):
    missing_json = tmp_path / "non_existent_qbo.json"
    exit_code = main([
        "--qbo-json", str(missing_json),
        "--quiet",
    ])
    assert exit_code == 1


def test_cli_qbo_json_invalid_structure(tmp_path):
    bad_json = tmp_path / "bad_structure.json"
    with open(bad_json, "w", encoding="utf-8") as f:
        json.dump({"NotAValidQBOResponse": True}, f)

    exit_code = main([
        "--qbo-json", str(bad_json),
        "--quiet",
    ])
    assert exit_code == 1


def test_cli_qbo_json_malformed_syntax(tmp_path):
    malformed_json = tmp_path / "syntax_error.json"
    with open(malformed_json, "w", encoding="utf-8") as f:
        f.write("{ incomplete json")

    exit_code = main([
        "--qbo-json", str(malformed_json),
        "--quiet",
    ])
    assert exit_code == 1


def test_cli_test_corp_12m_dynamic_report(tmp_path):
    """Regression test: Test Corp 12m fixture must have dynamic periods and accurate wording."""
    test_corp_fixture = BASE_DIR / "evals" / "fixtures" / "case8_different_company.xlsx"
    output_json = tmp_path / "different_company_analysis.json"
    output_report = tmp_path / "different_company_report.md"

    exit_code = main([
        "--input", str(test_corp_fixture),
        "--output-json", str(output_json),
        "--output-report", str(output_report),
        "--quiet",
    ])

    assert exit_code == 0
    assert output_json.exists()
    assert output_report.exists()

    with open(output_report, "r", encoding="utf-8") as f:
        report_text = f.read()

    # 1. Company name and actual ending period (Dec 2025)
    assert "Monthly Financial Trend Analysis: Test Corp" in report_text
    assert "Jan 2025 to Dec 2025 (12 Months)" in report_text
    assert "TTM Dec 2025" in report_text
    assert "Latest Month (Dec 2025)" in report_text

    # 2. Must not contain Jun 2026 or hardcoded 7 TTM windows
    assert "Jun 2026" not in report_text
    assert "June 2026" not in report_text
    assert "2026-06" not in report_text
    assert "7 valid" not in report_text
    assert "seven TTM" not in report_text
    assert "Exactly 1 valid TTM rolling window exists in this 12-month historical dataset (ending December 2025)." in report_text

    # 3. Positive operating income must not be described as a loss
    assert "Reported Operating Income of $1,533,000.00" in report_text
    assert "Normalized Core Operating Income of $1,533,000.00" in report_text
    assert "Reported Operating Loss" not in report_text
    assert "Normalized Core Operating Loss" not in report_text
    assert "operating losses continued" not in report_text.lower()
    assert "normalized core operating income continued throughout" in report_text.lower()
    assert "Cash Flow and Operating Performance Disclosure" in report_text
    assert "Cash Flow vs. Operating Loss Disclosure" not in report_text

    # 4. Department categories & unmapped accounts integrity
    assert "Unmapped accounts (2 flagged for CPA review):" in report_text
    assert "Engineering Salaries" in report_text
    assert "Growth & Customer Acquisition" in report_text
    assert "Revenue" not in report_text.split("## 4. Operating Expenses by Department")[1].split("## 5.")[0]

    # 5. Anomaly commentary conditionals (no false tax benefit or SBC claims)
    assert "Dec 2025 tax benefit" not in report_text
    assert "SBC" not in report_text


def test_cli_dataset_without_valid_ttm_window(tmp_path):
    """Regression test: 11-month dataset without valid TTM window must withhold TTM metrics."""
    fixture_11m = BASE_DIR / "evals" / "fixtures" / "case4_11_months.xlsx"
    output_json = tmp_path / "case4_analysis.json"
    output_report = tmp_path / "case4_report.md"

    exit_code = main([
        "--input", str(fixture_11m),
        "--output-json", str(output_json),
        "--output-report", str(output_report),
        "--quiet",
    ])

    assert exit_code == 0
    assert output_json.exists()
    assert output_report.exists()

    with open(output_report, "r", encoding="utf-8") as f:
        report_text = f.read()

    # 1. Period span
    assert "Jan 2025 to Nov 2025 (11 Months)" in report_text
    assert "Latest Month (Nov 2025)" in report_text

    # 2. TTM metrics withheld
    assert "TTM metrics are withheld" in report_text
    assert "No valid 12-consecutive-month TTM rolling windows exist in this 11-month dataset" in report_text
    assert "Latest Trailing-12-Month (TTM) Performance:** Withheld" in report_text
    assert "Jun 2026" not in report_text
    assert "7 valid" not in report_text

    # 3. Income not described as loss
    assert "operating losses continued" not in report_text.lower()
    assert "normalized core operating income continued throughout" in report_text.lower()
    assert "Reported Operating Loss" not in report_text
    assert "Normalized Core Operating Loss" not in report_text


