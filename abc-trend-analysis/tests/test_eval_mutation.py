"""Mutation test suite verifying that the evaluation grader rejects incorrect outputs."""

import pytest
from pathlib import Path
from evals.run_evals import grade_case

BASE_DIR = Path(__file__).resolve().parent.parent


def test_grader_rejects_mutated_period_count():
    """Mutation: Expected period count is altered to an invalid number."""
    case = {
        "id": "MUT-01",
        "name": "Mutated Period Count",
        "weight": 10,
        "fixture": "evals/fixtures/case1_normal_12m.xlsx",
        "expected": {
            "periods_count": 99,  # Mutated: fixture actually has 12
            "months_were_reversed": False,
        },
    }
    result = grade_case(case, BASE_DIR)
    assert result["status"] == "FAILED"
    assert result["score"] < 10.0
    assert any("Periods count" in f for f in result["assertions_failed"])


def test_grader_rejects_mutated_ttm_revenue():
    """Mutation: Expected TTM revenue is altered to a hallucinated value."""
    case = {
        "id": "MUT-02",
        "name": "Mutated TTM Revenue",
        "weight": 10,
        "fixture": "evals/fixtures/case1_normal_12m.xlsx",
        "expected": {
            "periods_count": 12,
            "ttm_revenue": "9999999.99",  # Mutated: fixture actually has 1770000.00
        },
    }
    result = grade_case(case, BASE_DIR)
    assert result["status"] == "FAILED"
    assert any("TTM revenue" in f for f in result["assertions_failed"])


def test_grader_rejects_false_profitability_mutation():
    """Mutation: Dec 2025 anomaly test when profitability rejection logic fails."""
    case = {
        "id": "MUT-03",
        "name": "Mutated Profitability Assertion",
        "weight": 20,
        "fixture": "evals/fixtures/case3_dec_2025_anomaly.xlsx",
        "expected": {
            "has_critical_tax_benefit_flag": False,  # Mutated: critical flag actually exists
            "rejects_genuine_profitability": True,
        },
    }
    result = grade_case(case, BASE_DIR)
    assert result["status"] == "FAILED"
    assert any("Tax benefit flag" in f for f in result["assertions_failed"])


def test_grader_rejects_hidden_reconciliation_corruption():
    """Mutation: Claiming zero reconciliation failures on a corrupted workbook."""
    case = {
        "id": "MUT-04",
        "name": "Mutated Reconciliation Expectation",
        "weight": 10,
        "fixture": "evals/fixtures/case7_inconsistent_totals.xlsx",
        "expected": {
            "failed_reconciliation_count": 0,  # Mutated: fixture actually has 1 failure
        },
    }
    result = grade_case(case, BASE_DIR)
    assert result["status"] == "FAILED"
    assert any("Failed reconciliation checks" in f for f in result["assertions_failed"])


def test_grader_accepts_valid_golden_case():
    """Control: Grader returns 100% score when outputs match expected."""
    case = {
        "id": "CONTROL-01",
        "name": "Valid Golden Control",
        "weight": 10,
        "fixture": "evals/fixtures/case1_normal_12m.xlsx",
        "expected": {
            "periods_count": 12,
            "months_were_reversed": False,
            "valid_ttm_windows_count": 1,
            "failed_reconciliation_count": 0,
            "ttm_revenue": "1770000.00",
        },
    }
    result = grade_case(case, BASE_DIR)
    assert result["status"] == "PASSED"
    assert result["score"] == 10.0
    assert len(result["assertions_failed"]) == 0


# =====================================================================
# Commentary Evaluator Negative Mutation & Guardrail Tests
# =====================================================================

import json
from evals.eval_commentary import CommentaryEvaluator


@pytest.fixture
def baseline_analysis_data():
    analysis_file = BASE_DIR / "results" / "analysis.json"
    with open(analysis_file, "r", encoding="utf-8") as f:
        return json.load(f)


def test_commentary_evaluator_rejects_hallucinated_numbers(baseline_analysis_data):
    """Proves commentary evaluator strictly fails when hallucinated numbers are cited."""
    evaluator = CommentaryEvaluator(baseline_analysis_data)
    mutated_commentary = (
        "In 2026, the company generated $98,765,432.10 in revenue and spent $45,000,000.00 in opex, "
        "yielding an operating margin of 88.5%. December 2025 was not genuinely profitable due to a tax benefit. "
        "Tax credit requires CPA review. March 2026 reversals require credit memo audits. Unmapped accounts: None."
    )
    res = evaluator.evaluate(mutated_commentary)
    assert res["passed"] is False
    c1 = res["checks"]["Numerical Grounding"]
    assert c1["passed"] is False
    assert len(c1["violations"]) > 0
    assert any("98,765,432.10" in v or "98765432.10" in v for v in c1["violations"])


def test_commentary_evaluator_rejects_false_december_profitability(baseline_analysis_data):
    """Proves commentary evaluator rejects claims of genuine operational profitability in Dec 2025."""
    evaluator = CommentaryEvaluator(baseline_analysis_data)
    mutated_commentary = (
        "The company achieved strong revenue of $190,029.49 in Dec 2025 with gross profit of $132,409.32. "
        "December 2025 demonstrated genuine profitability of $534,551.41 through excellent operational execution. "
        "Reversals require credit memo reviews. Tax credit requires CPA review. Unmapped accounts: None identified."
    )
    res = evaluator.evaluate(mutated_commentary)
    assert res["passed"] is False
    c3 = res["checks"]["Critical Anomaly Profitability Interpretation"]
    assert c3["passed"] is False
    assert any("falsely claims December 2025 achieved genuine operational profitability" in v for v in c3["violations"])


def test_commentary_evaluator_rejects_unsupported_causal_claims(baseline_analysis_data):
    """Proves commentary evaluator rejects unverified external business causes stated as fact."""
    evaluator = CommentaryEvaluator(baseline_analysis_data)
    mutated_commentary = (
        "Revenue was $190,029.49 in Dec 2025. The revenue drop in April 2025 was due to customer churn "
        "following a pricing dispute with our primary client. "
        "December 2025 was not genuinely profitable due to tax credit. Tax credit requires CPA review. "
        "Reversals require credit memo audits. Unmapped accounts: None identified."
    )
    res = evaluator.evaluate(mutated_commentary)
    assert res["passed"] is False
    c2 = res["checks"]["Unsupported Causal Claims"]
    assert c2["passed"] is False
    assert len(c2["violations"]) > 0
    assert any("customer churn" in v.lower() or "pricing dispute" in v.lower() for v in c2["violations"])


def test_commentary_evaluator_rejects_omitted_disclosures(baseline_analysis_data):
    """Proves commentary evaluator fails when required disclosures (CPA review, credit memos) are omitted."""
    evaluator = CommentaryEvaluator(baseline_analysis_data)
    incomplete_commentary = (
        "Revenue was $190,029.49 and Gross Profit was $132,409.32. Total opex was $-402,142.09. "
        "December 2025 was an artificial operating profit due to the one-off tax credit of $1,244,429.84, "
        "so the business did not become genuinely operationally profitable."
    )
    res = evaluator.evaluate(incomplete_commentary)
    assert res["passed"] is False
    c4 = res["checks"]["Disclosure of Missing Information"]
    assert c4["passed"] is False
    assert len(c4["violations"]) > 0


def test_commentary_evaluator_accepts_grounded_report(baseline_analysis_data):
    """Control: Grounded report passes all checks with full score."""
    report_file = BASE_DIR / "results" / "report.md"
    with open(report_file, "r", encoding="utf-8") as f:
        report_text = f.read()

    evaluator = CommentaryEvaluator(baseline_analysis_data)
    res = evaluator.evaluate(report_text)
    assert res["passed"] is True
    assert res["total_score"] == 100.0
    for name, c in res["checks"].items():
        assert c["passed"] is True
        assert len(c["violations"]) == 0


@pytest.mark.parametrize("claim_phrase", [
    "Normalized cash burn averaged $250k per month.",
    "The company burns $300,000 in cash every month.",
    "Monthly operating losses prove cash burn of $350,000.",
    "Cash consumption is $350,000 per month.",
])
def test_commentary_evaluator_rejects_unsupported_cash_burn_claims(baseline_analysis_data, claim_phrase):
    """Proves commentary evaluator rejects asserting operating loss as cash burn across phrasing variations."""
    report_file = BASE_DIR / "results" / "report.md"
    with open(report_file, "r", encoding="utf-8") as f:
        report_text = f.read()

    mutated_commentary = report_text + "\n" + claim_phrase
    evaluator = CommentaryEvaluator(baseline_analysis_data)
    res = evaluator.evaluate(mutated_commentary)
    assert res["passed"] is False
    c2 = res["checks"]["Unsupported Causal Claims"]
    assert c2["passed"] is False
    assert len(c2["violations"]) > 0


def test_commentary_evaluator_accepts_valid_cash_flow_limitation_statement(baseline_analysis_data):
    """Proves commentary evaluator accepts explicit statements that the dataset lacks cash flow/balance sheet data."""
    report_file = BASE_DIR / "results" / "report.md"
    with open(report_file, "r", encoding="utf-8") as f:
        report_text = f.read()

    evaluator = CommentaryEvaluator(baseline_analysis_data)
    res = evaluator.evaluate(report_text)
    assert res["passed"] is True
    assert res["total_score"] == 100.0
    c2 = res["checks"]["Unsupported Causal Claims"]
    assert c2["passed"] is True
    assert len(c2["violations"]) == 0
    c4 = res["checks"]["Disclosure of Missing Information"]
    assert c4["passed"] is True

