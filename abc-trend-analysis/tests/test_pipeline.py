"""Pytest suite for the End-to-End Live QuickBooks Pipeline & Safety Guardrails.

Verifies:
1. Environment configuration and read-only safety checks.
2. Prevention of writes, updates, and deletes to QuickBooks.
3. Prevention of silent stale-report fallback when export fails.
4. Proper failure propagation from all pipeline stages (auth, network, CLI, evals).
5. Schema validation of QuickBooks Online Profit and Loss reports.
6. End-to-end pipeline execution and output artifact generation.
7. Integrity and preservation of canonical baseline fixtures.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from scripts.run_pipeline import (
    check_readonly_and_env,
    find_repo_root,
    run_command_step,
    main as pipeline_main,
)
from scripts.engine import FinancialCalculationEngine


BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
QBO_DIR = REPO_ROOT / "quickbooks-online-mcp-server"
BASELINE_WORKBOOK = BASE_DIR / "data" / "ABC Inc - Financial Statements.xlsx"
CANONICAL_QBO_REPORT = BASE_DIR / "results" / "qbo_live_pnl_report.json"


def test_check_readonly_and_env_success():
    """Verify that the production/sandbox .env file passes safety checks."""
    if not (QBO_DIR / ".env").exists():
        pytest.skip("quickbooks-online-mcp-server/.env not present (excluded from distribution)")
    ok, msg = check_readonly_and_env(QBO_DIR)
    assert ok is True
    assert "read-only enforcement strictly active" in msg
    assert "9341458481035247" in msg


def test_check_readonly_fails_if_flag_disabled(tmp_path):
    """Verify that if any read-only flag is false, the pipeline aborts immediately."""
    fake_env = tmp_path / ".env"
    fake_env.write_text(
        "QUICKBOOKS_DISABLE_WRITE=false\n"
        "QUICKBOOKS_DISABLE_UPDATE=true\n"
        "QUICKBOOKS_DISABLE_DELETE=true\n"
        "QUICKBOOKS_CLIENT_ID=test_id\n"
        "QUICKBOOKS_CLIENT_SECRET=test_secret\n"
        "QUICKBOOKS_REFRESH_TOKEN=test_refresh\n"
        "QUICKBOOKS_REALM_ID=9341458481035247\n",
        encoding="utf-8",
    )
    ok, msg = check_readonly_and_env(tmp_path)
    assert ok is False
    assert "Read-only safety flags are not strictly enforced" in msg


def test_check_readonly_fails_if_credentials_missing(tmp_path):
    """Verify that missing credentials cause the pipeline safety check to fail."""
    fake_env = tmp_path / ".env"
    fake_env.write_text(
        "QUICKBOOKS_DISABLE_WRITE=true\n"
        "QUICKBOOKS_DISABLE_UPDATE=true\n"
        "QUICKBOOKS_DISABLE_DELETE=true\n"
        "QUICKBOOKS_REALM_ID=9341458481035247\n",
        encoding="utf-8",
    )
    ok, msg = check_readonly_and_env(tmp_path)
    assert ok is False
    assert "Missing required QuickBooks credentials" in msg


def test_pipeline_stale_fallback_prevention_on_export_failure(tmp_path, monkeypatch):
    """CRITICAL SAFETY TEST: If live QBO export fails, pipeline MUST abort with code 1

    and MUST NOT silently fall back to existing saved/stale report data.
    """
    output_json = tmp_path / "analysis.json"
    output_report = tmp_path / "report.md"

    # Provide a valid fake .env in tmp_path so Step 1 passes independently of distribution environment
    fake_qbo = tmp_path / "quickbooks-online-mcp-server"
    fake_qbo.mkdir(parents=True, exist_ok=True)
    fake_env = fake_qbo / ".env"
    fake_env.write_text(
        "QUICKBOOKS_DISABLE_WRITE=true\n"
        "QUICKBOOKS_DISABLE_UPDATE=true\n"
        "QUICKBOOKS_DISABLE_DELETE=true\n"
        "QUICKBOOKS_CLIENT_ID=dummy_id\n"
        "QUICKBOOKS_CLIENT_SECRET=dummy_secret\n"
        "QUICKBOOKS_REFRESH_TOKEN=dummy_token\n"
        "QUICKBOOKS_REALM_ID=9341458481035247\n",
        encoding="utf-8",
    )
    fake_export_script = fake_qbo / "scripts" / "export-pnl.mjs"
    fake_export_script.parent.mkdir(parents=True, exist_ok=True)
    fake_export_script.write_text("// dummy", encoding="utf-8")

    fake_abc = tmp_path / "abc-trend-analysis" / "data"
    fake_abc.mkdir(parents=True, exist_ok=True)
    shutil.copy(BASELINE_WORKBOOK, fake_abc / BASELINE_WORKBOOK.name)

    monkeypatch.setattr("scripts.run_pipeline.find_repo_root", lambda: tmp_path)

    # Mock run_command_step for Step 2 (Export Live QuickBooks P&L) to simulate network or auth failure
    with patch("scripts.run_pipeline.run_command_step") as mock_step:
        # Simulate export failure (returncode = 1)
        mock_step.return_value = (False, "", "Simulated QBO API Authentication Failure (401)", 1)

        exit_code = pipeline_main([
            "--output-json", str(output_json),
            "--output-report", str(output_report),
            "--quiet",
        ])

        assert exit_code == 1
        # Confirm execution did not continue to generate new analysis artifacts
        assert not output_json.exists()
        assert not output_report.exists()
        # Verify the export step was indeed called
        mock_step.assert_called_once()
        assert "export-pnl.mjs" in str(mock_step.call_args[0][0])


def test_pipeline_auth_failure_propagation():
    """Verify that authentication failure returns nonzero exit code."""
    with patch("scripts.run_pipeline.check_readonly_and_env", return_value=(False, "Auth failure")):
        exit_code = pipeline_main(["--quiet"])
        assert exit_code == 1


def test_pipeline_network_failure_propagation(tmp_path):
    """Verify that a network timeout or connection error during export halts the pipeline."""
    with patch("scripts.run_pipeline.run_command_step", return_value=(False, "", "QuickBooks API request timed out after 30000ms", 1)):
        exit_code = pipeline_main(["--quiet"])
        assert exit_code == 1


def test_pipeline_invalid_or_empty_report_fails(tmp_path):
    """Verify that an empty or malformed report JSON halts the pipeline."""
    bad_report = tmp_path / "bad_report.json"
    bad_report.write_text("{}", encoding="utf-8")  # Missing Header and Columns

    exit_code = pipeline_main([
        "--offline",
        "--qbo-report-path", str(bad_report),
        "--quiet",
    ])
    assert exit_code == 1


def test_pipeline_engine_failure_propagation():
    """Verify that if the calculation engine fails, the pipeline aborts before evaluations."""
    call_counts = {"count": 0}

    def fake_step(cmd, cwd, step_name, quiet=False):
        call_counts["count"] += 1
        if "Financial Calculation Engine" in step_name:
            return False, "", "Engine crashed", 1
        return True, "OK", "", 0

    with patch("scripts.run_pipeline.run_command_step", side_effect=fake_step):
        exit_code = pipeline_main(["--offline", "--quiet"])
        assert exit_code == 1
        # Step 5 (evals) and Step 6 (commentary) must never have been called
        assert call_counts["count"] == 1


def test_pipeline_golden_eval_failure_propagation(tmp_path):
    """Verify that golden evaluation failure causes pipeline to return nonzero code."""
    out_json = tmp_path / "analysis.json"
    out_report = tmp_path / "report.md"

    # Pre-create valid outputs so Step 4 passes
    out_json.write_text(json.dumps({"reconciliation_checks": [{"is_valid": True}], "anomalies_and_flags": []}), encoding="utf-8")
    out_report.write_text("# Report", encoding="utf-8")

    def fake_step(cmd, cwd, step_name, quiet=False):
        if "Golden Evaluation Suite" in step_name:
            return False, "", "Case 7 regression detected", 1
        return True, "OK", "", 0

    with patch("scripts.run_pipeline.run_command_step", side_effect=fake_step):
        exit_code = pipeline_main([
            "--offline",
            "--output-json", str(out_json),
            "--output-report", str(out_report),
            "--quiet",
        ])
        assert exit_code == 1


def test_pipeline_commentary_eval_failure_propagation(tmp_path):
    """Verify that commentary evaluation failure causes pipeline to return nonzero code."""
    out_json = tmp_path / "analysis.json"
    out_report = tmp_path / "report.md"

    out_json.write_text(json.dumps({"reconciliation_checks": [{"is_valid": True}], "anomalies_and_flags": []}), encoding="utf-8")
    out_report.write_text("# Report", encoding="utf-8")

    def fake_step(cmd, cwd, step_name, quiet=False):
        if "Commentary Evaluator" in step_name:
            return False, "", "Violation: Hallucinated revenue figure", 1
        return True, "OK", "", 0

    with patch("scripts.run_pipeline.run_command_step", side_effect=fake_step):
        exit_code = pipeline_main([
            "--offline",
            "--output-json", str(out_json),
            "--output-report", str(out_report),
            "--quiet",
        ])
        assert exit_code == 1


def test_pipeline_offline_execution_end_to_end(tmp_path):
    """Verify complete end-to-end pipeline execution in offline/cached mode."""
    out_json = tmp_path / "analysis.json"
    out_report = tmp_path / "report.md"

    exit_code = pipeline_main([
        "--offline",
        "--output-json", str(out_json),
        "--output-report", str(out_report),
        "--quiet",
    ])

    assert exit_code == 0
    assert out_json.exists()
    assert out_report.exists()

    with open(out_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 126/126 checks must pass
    checks = data.get("reconciliation_checks", [])
    assert len(checks) == 126
    assert all(c["is_valid"] for c in checks)


def test_baseline_fixtures_preservation():
    """Verify that canonical Excel baseline and all 8 golden fixtures remain intact and unmodified."""
    assert BASELINE_WORKBOOK.exists()
    engine = FinancialCalculationEngine(str(BASELINE_WORKBOOK))
    res = engine.run_analysis()
    assert len(res.periods_analyzed) == 18
    assert len(res.reconciliation_checks) == 126
    assert all(c.is_valid for c in res.reconciliation_checks)

    # Check all 8 evaluation fixtures exist
    cases_file = BASE_DIR / "evals" / "eval_cases.json"
    assert cases_file.exists()
    with open(cases_file, "r", encoding="utf-8") as f:
        cases_data = json.load(f)

    for case in cases_data.get("cases", []):
        fixture_file = BASE_DIR / case["fixture"]
        assert fixture_file.exists(), f"Missing fixture file: {fixture_file}"


def test_export_pnl_node_validator_via_subprocess():
    """Verify export-pnl.mjs schema validation logic via Node subprocess."""
    node_modules_dir = QBO_DIR / "node_modules"
    if not node_modules_dir.exists():
        pytest.skip("run npm install in quickbooks-online-mcp-server first")

    node_script = QBO_DIR / "scripts" / "export-pnl.mjs"
    assert node_script.exists()

    # Run help to verify syntax and node loading
    proc = subprocess.run(
        ["node", str(node_script), "--help"],
        cwd=str(QBO_DIR),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "Usage: node export-pnl.mjs" in proc.stdout


def test_pipeline_verifier_anomaly_count_matches_engine(tmp_path, capsys):
    """Assert the pipeline verifier's anomaly count equals the engine's (12 on ABC data) and prints 'Identified Anomalies: 12'."""
    import re
    out_json = tmp_path / "analysis.json"
    out_report = tmp_path / "report.md"

    exit_code = pipeline_main([
        "--offline",
        "--output-json", str(out_json),
        "--output-report", str(out_report),
    ])
    assert exit_code == 0

    # Capture stdout from run_pipeline's verifier and assert it printed 12 anomalies
    captured = capsys.readouterr()
    assert re.search(r"Identified Anomalies:\s+12", captured.out) is not None

    # 1. Engine direct anomaly count on ABC data
    from scripts.adapters.qbo_adapter import QBOReportAdapter
    adapter = QBOReportAdapter(CANONICAL_QBO_REPORT)
    engine_result = adapter.run_analysis()
    engine_anomaly_count = len(engine_result.anomalies)
    assert engine_anomaly_count == 12

    # 2. Pipeline verifier anomaly count directly from analysis.json
    with open(out_json, "r", encoding="utf-8") as f:
        analysis_dict = json.load(f)

    # Verifier reads "anomalies_and_flags" directly without default
    verifier_anomaly_count = len(analysis_dict["anomalies_and_flags"])

    assert verifier_anomaly_count == engine_anomaly_count
    assert verifier_anomaly_count == 12


def test_golden_abc_report_byte_identical(tmp_path, monkeypatch):
    """Assert the offline pipeline output on ABC data equals tests/fixtures/golden_abc_report.md byte for byte."""
    golden_path = BASE_DIR / "tests" / "fixtures" / "golden_abc_report.md"
    assert golden_path.exists(), f"Missing golden fixture: {golden_path}"
    golden_bytes = golden_path.read_bytes()
    assert len(golden_bytes) == 13019

    out_json = tmp_path / "analysis.json"
    out_report = tmp_path / "report.md"

    canonical_root = Path("D:/RE-Financial-AI-Assignment")
    if canonical_root.exists():
        monkeypatch.setattr("scripts.run_pipeline.find_repo_root", lambda: canonical_root)

    exit_code = pipeline_main([
        "--offline",
        "--output-json", str(out_json),
        "--output-report", str(out_report),
        "--quiet",
    ])
    assert exit_code == 0
    assert out_report.exists()
    generated_bytes = out_report.read_bytes()
    assert len(generated_bytes) == 13019
    assert generated_bytes == golden_bytes


def test_leak_check_no_abc_literals_in_non_abc_reports(tmp_path):
    """Leak test: run the offline pipeline on CASE-08, CASE-09 and one tmp_path fixture with a different-size tax credit.

    The report must NOT contain:
    1,244,429.84, 334,660.53, 402,142.09, 534,551.41, 375,217.90, 278,457.61, 379,507.55, 1,608.09, "March 2026".
    """
    import openpyxl
    from scripts.cli import main as cli_main

    FORBIDDEN_ABC_LITERALS = [
        "1,244,429.84",
        "334,660.53",
        "402,142.09",
        "534,551.41",
        "375,217.90",
        "278,457.61",
        "379,507.55",
        "1,608.09",
        "March 2026",
    ]

    # Create tmp_path fixture with different-size tax credit
    src_path = BASE_DIR / "evals" / "fixtures" / "case8_different_company.xlsx"
    wb = openpyxl.load_workbook(src_path)
    ws = wb.active
    ws.insert_rows(20)
    ws.cell(20, 2, "Income Tax Benefit")
    for c in range(3, 15):
        ws.cell(20, c, 0.0)
    ws.cell(8, 13, 100000.0)
    ws.cell(9, 13, 0.0)
    ws.cell(10, 13, 100000.0)
    ws.cell(12, 13, 20000.0)
    ws.cell(13, 13, 0.0)
    ws.cell(14, 13, 20000.0)
    ws.cell(15, 13, 80000.0)
    ws.cell(17, 13, 0.0)
    ws.cell(18, 13, 0.0)
    ws.cell(19, 13, 150000.0)
    ws.cell(20, 13, -250000.0)
    ws.cell(21, 13, -100000.0)
    ws.cell(22, 13, 180000.0)
    ws.cell(23, 13, 180000.0)

    tax_fixture_path = tmp_path / "different_tax_credit.xlsx"
    wb.save(tax_fixture_path)

    test_targets = [
        ("CASE-08", BASE_DIR / "evals" / "fixtures" / "case8_different_company.xlsx"),
        ("CASE-09", BASE_DIR / "evals" / "fixtures" / "case9_subtotals_generalization.xlsx"),
        ("TMP_TAX", tax_fixture_path),
    ]

    for label, target_file in test_targets:
        out_json = tmp_path / f"{label}_analysis.json"
        out_report = tmp_path / f"{label}_report.md"
        cli_main([
            "--input", str(target_file),
            "--output-json", str(out_json),
            "--output-report", str(out_report),
        ])
        assert out_report.exists()
        report_text = out_report.read_text(encoding="utf-8")
        for literal in FORBIDDEN_ABC_LITERALS:
            assert literal not in report_text, f"Found ABC literal '{literal}' in {label} report"


def test_pipeline_live_mode_aborts_when_env_missing(tmp_path, monkeypatch):
    """Verify live mode aborts with code 1 before making network calls when .env is missing."""
    empty_qbo = tmp_path / "quickbooks-online-mcp-server"
    empty_qbo.mkdir(parents=True)
    fake_export_script = empty_qbo / "scripts" / "export-pnl.mjs"
    fake_export_script.parent.mkdir(parents=True, exist_ok=True)
    fake_export_script.write_text("// dummy", encoding="utf-8")

    fake_baseline = tmp_path / "abc-trend-analysis" / "data" / "ABC Inc - Financial Statements.xlsx"
    fake_baseline.parent.mkdir(parents=True, exist_ok=True)
    fake_baseline.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr("scripts.run_pipeline.find_repo_root", lambda: tmp_path)

    with patch("scripts.run_pipeline.run_command_step") as mock_step:
        exit_code = pipeline_main([])
        assert exit_code == 1
        mock_step.assert_not_called()


def test_pipeline_live_mode_aborts_when_disable_flag_not_true(tmp_path, monkeypatch):
    """Verify live mode aborts with code 1 before making network calls when any DISABLE_* flag is not 'true'."""
    fake_qbo = tmp_path / "quickbooks-online-mcp-server"
    fake_qbo.mkdir(parents=True)
    fake_export_script = fake_qbo / "scripts" / "export-pnl.mjs"
    fake_export_script.parent.mkdir(parents=True, exist_ok=True)
    fake_export_script.write_text("// dummy", encoding="utf-8")

    fake_baseline = tmp_path / "abc-trend-analysis" / "data" / "ABC Inc - Financial Statements.xlsx"
    fake_baseline.parent.mkdir(parents=True, exist_ok=True)
    fake_baseline.write_text("dummy", encoding="utf-8")

    (fake_qbo / ".env").write_text(
        "QUICKBOOKS_DISABLE_WRITE=false\n"
        "QUICKBOOKS_DISABLE_UPDATE=true\n"
        "QUICKBOOKS_DISABLE_DELETE=true\n"
        "QUICKBOOKS_CLIENT_ID=dummy_id\n"
        "QUICKBOOKS_CLIENT_SECRET=dummy_secret\n"
        "QUICKBOOKS_REFRESH_TOKEN=dummy_token\n"
        "QUICKBOOKS_REALM_ID=9341458481035247\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.run_pipeline.find_repo_root", lambda: tmp_path)

    with patch("scripts.run_pipeline.run_command_step") as mock_step:
        exit_code = pipeline_main([])
        assert exit_code == 1
        mock_step.assert_not_called()


