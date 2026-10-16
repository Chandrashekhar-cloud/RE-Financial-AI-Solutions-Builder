"""Tests for the deterministic Numerical Claim Validator.

Verifies:
1. Correct values, incorrect values, and tolerance handling.
2. Percentage rounding tolerances (e.g. 78.79% vs 78.8%).
3. Negative values and sign verification (operating losses, credit reversals).
4. Valid vs invalid TTM windows.
5. Unsupported and ambiguous claims flagged for CPA review.
6. Zero silent replacement: claimed values are never altered.
7. Machine-readable JSON summary and Markdown report generation.
"""

import json
from pathlib import Path
import pytest

from evals.numerical_validator import NumericalClaimValidator, ClaimValidationResult


@pytest.fixture
def sample_analysis_data():
    """Load canonical analysis.json from results directory."""
    path = Path(__file__).resolve().parent.parent / "results" / "analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_correct_currency_value(sample_analysis_data):
    validator = NumericalClaimValidator(sample_analysis_data)
    claim = {
        "claim_text": "January 2025 revenue stood at $167,587.50.",
        "metric": "revenue",
        "period": "2025-01",
        "claimed_value": 167587.50,
        "claimed_unit": "currency",
    }
    result = validator.validate_claim(claim)
    assert result.status == "VERIFIED"
    assert result.difference == 0.0
    assert result.ground_truth_value == 167587.50


def test_incorrect_currency_value(sample_analysis_data):
    validator = NumericalClaimValidator(sample_analysis_data)
    claim = {
        "claim_text": "January 2025 revenue was $200,000.00.",
        "metric": "revenue",
        "period": "2025-01",
        "claimed_value": 200000.00,
        "claimed_unit": "currency",
    }
    result = validator.validate_claim(claim)
    assert result.status == "INVALID"
    assert result.ground_truth_value == 167587.50
    assert result.difference > 30000.0
    # Must preserve claimed value, not replace it
    assert result.claimed_value == 200000.00


def test_percentage_with_rounding_tolerance(sample_analysis_data):
    validator = NumericalClaimValidator(sample_analysis_data, tolerance_percentage=0.05)
    # Ground truth in Feb 2025 is 78.79%
    # Test exact value
    claim_exact = {
        "claim_text": "February 2025 gross margin was 78.79%.",
        "metric": "gross_margin_pct",
        "period": "Feb 2025",
        "claimed_value": 78.79,
        "claimed_unit": "percent",
    }
    res_exact = validator.validate_claim(claim_exact)
    assert res_exact.status == "VERIFIED"

    # Test within tolerance (e.g. rounded to 78.8%)
    claim_rounded = {
        "claim_text": "February 2025 gross margin rounded to 78.8%.",
        "metric": "gross_margin_pct",
        "period": "Feb 2025",
        "claimed_value": 78.80,
        "claimed_unit": "percent",
    }
    res_rounded = validator.validate_claim(claim_rounded)
    assert res_rounded.status == "VERIFIED"
    assert res_rounded.difference <= 0.05

    # Test outside tolerance
    claim_wrong = {
        "claim_text": "February 2025 gross margin was 75.0%.",
        "metric": "gross_margin_pct",
        "period": "Feb 2025",
        "claimed_value": 75.0,
        "claimed_unit": "percent",
    }
    res_wrong = validator.validate_claim(claim_wrong)
    assert res_wrong.status == "INVALID"


def test_negative_values_and_reversals(sample_analysis_data):
    validator = NumericalClaimValidator(sample_analysis_data)
    # Sales Commission reversal in March 2026: -$3,629.87
    claim = {
        "claim_text": "March 2026 sales commission reversal was -$3,629.87.",
        "metric": "reversal",
        "period": "2026-03",
        "claimed_value": -3629.87,
        "claimed_unit": "currency",
    }
    result = validator.validate_claim(claim)
    assert result.status == "VERIFIED"


def test_operating_loss_sign_handling(sample_analysis_data):
    validator = NumericalClaimValidator(sample_analysis_data)
    # Jan 2025 reported operating loss is -$382,905.03
    # Both signed -$382,905.03 and stated positive loss magnitude $382,905.03 should verify
    claim_signed = {
        "claim_text": "Jan 2025 reported operating loss was -$382,905.03.",
        "metric": "operating_income",
        "period": "2025-01",
        "claimed_value": -382905.03,
        "claimed_unit": "currency",
    }
    res_signed = validator.validate_claim(claim_signed)
    assert res_signed.status == "VERIFIED"

    claim_magnitude = {
        "claim_text": "Operating loss in Jan 2025 was $382,905.03.",
        "metric": "operating_loss",
        "period": "2025-01",
        "claimed_value": 382905.03,
        "claimed_unit": "currency",
    }
    res_mag = validator.validate_claim(claim_magnitude)
    assert res_mag.status == "VERIFIED"


def test_valid_and_invalid_ttm_windows(sample_analysis_data):
    validator = NumericalClaimValidator(sample_analysis_data)

    # Valid TTM window: Jun 2026 revenue is $2,304,366.76 (QBO) / $2,303,975.51 (Excel baseline)
    valid_ttm_claim = {
        "claim_text": "TTM Revenue ending June 2026 reached $2,304,366.76.",
        "metric": "revenue",
        "period": "TTM 2026-06",
        "claimed_value": 2304366.76,
        "claimed_unit": "currency",
        "is_ttm": True,
    }
    res_ttm = validator.validate_claim(valid_ttm_claim)
    assert res_ttm.status == "VERIFIED"
    assert res_ttm.is_ttm is True

    # Invalid TTM window: Aug 2025 has only 8 months history (insufficient for 12M TTM)
    invalid_ttm_claim = {
        "claim_text": "TTM Revenue ending August 2025 was $1,500,000.00.",
        "metric": "revenue",
        "period": "TTM 2025-08",
        "claimed_value": 1500000.00,
        "claimed_unit": "currency",
        "is_ttm": True,
    }
    res_invalid_ttm = validator.validate_claim(invalid_ttm_claim)
    assert res_invalid_ttm.status == "INVALID"


def test_special_anomalies_december_2025(sample_analysis_data):
    validator = NumericalClaimValidator(sample_analysis_data)

    # Tax benefit credit: -$1,244,429.84
    tax_claim = {
        "claim_text": "December 2025 recorded a non-recurring tax benefit of $1,244,429.84.",
        "metric": "tax_benefit",
        "period": "2025-12",
        "claimed_value": 1244429.84,
        "claimed_unit": "currency",
    }
    res_tax = validator.validate_claim(tax_claim)
    assert res_tax.status == "VERIFIED"

    # Stock-based compensation: +$334,660.53
    sbc_claim = {
        "claim_text": "Stock compensation in Dec 2025 was $334,660.53.",
        "metric": "stock_based_compensation",
        "period": "2025-12",
        "claimed_value": 334660.53,
        "claimed_unit": "currency",
    }
    res_sbc = validator.validate_claim(sbc_claim)
    assert res_sbc.status == "VERIFIED"

    # Normalized Core Operating Loss: -$381,241.27
    norm_claim = {
        "claim_text": "Dec 2025 normalized operating loss was -$381,241.27.",
        "metric": "normalized_operating_income",
        "period": "2025-12",
        "claimed_value": -381241.27,
        "claimed_unit": "currency",
    }
    res_norm = validator.validate_claim(norm_claim)
    assert res_norm.status == "VERIFIED"


def test_unsupported_and_ambiguous_claims(sample_analysis_data):
    validator = NumericalClaimValidator(sample_analysis_data)

    # Claim about customer churn rate (omitted from Income Statement)
    unsupported_claim = {
        "claim_text": "Customer churn rate increased by 4.2% in Q1.",
        "metric": "churn_rate",
        "period": "2025-03",
        "claimed_value": 4.2,
        "claimed_unit": "percent",
    }
    res = validator.validate_claim(unsupported_claim)
    assert res.status == "UNVERIFIED"
    assert "flagged for CPA review" in res.explanation


def test_no_silent_replacement_and_report_generation(sample_analysis_data):
    validator = NumericalClaimValidator(sample_analysis_data)
    claims = [
        {
            "claim_text": "January 2025 revenue was $167,587.50.",
            "metric": "revenue",
            "period": "2025-01",
            "claimed_value": 167587.50,
            "claimed_unit": "currency",
        },
        {
            "claim_text": "February 2025 revenue was $999,999.00 (fake).",
            "metric": "revenue",
            "period": "2025-02",
            "claimed_value": 999999.00,
            "claimed_unit": "currency",
        },
        {
            "claim_text": "Cash balance on balance sheet was $500,000.00.",
            "metric": "cash_balance",
            "period": "2025-02",
            "claimed_value": 500000.00,
            "claimed_unit": "currency",
        },
    ]

    output = validator.validate_claims(claims)
    summary = output["summary"]

    assert summary["total_claims"] == 3
    assert summary["verified_claims"] == 1
    assert summary["invalid_claims"] == 1
    assert summary["unverified_claims"] == 1
    assert summary["status"] == "FAIL"

    # Confirm claimed value in claim 2 was NOT silently replaced with ground truth
    invalid_claim = output["claims"][1]
    assert invalid_claim["claimed_value"] == 999999.00
    assert invalid_claim["ground_truth_value"] == 176651.19
    assert invalid_claim["status"] == "INVALID"

    # Test Markdown report generation
    report = validator.generate_markdown_report(output)
    assert "LLM Financial Commentary: Deterministic Numerical Grounding Audit" in report
    assert "VERIFIED" in report
    assert "INVALID" in report
    assert "UNVERIFIED" in report


def test_billion_vs_million_scale_detection(sample_analysis_data):
    """Regression test 1: Scale discrepancy (e.g. citing -$4.462B instead of -$4.462M)."""
    validator = NumericalClaimValidator(sample_analysis_data)

    # Claim asserting -$4.462B in billions (i.e. -4,462,000,000.00)
    billion_claim = {
        "claim_text": "Core operating losses improved from -$4.462B to -$4.064B in TTM windows.",
        "metric": "normalized_operating_income",
        "period": "2025-12",
        "claimed_value": -4462000000.00,
        "claimed_unit": "currency",
        "is_ttm": True,
    }
    res_billion = validator.validate_claim(billion_claim)
    assert res_billion.status == "INVALID"
    assert "Scale mismatch" in res_billion.explanation or "Scale discrepancy" in res_billion.explanation
    assert res_billion.ground_truth_value == -4462347.78

    # True verified value: -$4,462,347.78
    verified_claim = {
        "claim_text": "TTM normalized operating loss ending Dec 2025 was -$4,462,347.78.",
        "metric": "normalized_operating_income",
        "period": "2025-12",
        "claimed_value": -4462347.78,
        "claimed_unit": "currency",
        "is_ttm": True,
    }
    res_verified = validator.validate_claim(verified_claim)
    assert res_verified.status == "VERIFIED"
    assert res_verified.difference == 0.0


def test_december_2025_reconciliation_claims(sample_analysis_data):
    """Regression test 2: Reconciling Dec 2025 reported vs normalized operating income arithmetic."""
    validator = NumericalClaimValidator(sample_analysis_data)

    # Valid December 2025 reconciliation figures
    valid_claims = [
        {
            "claim_text": "Reported operating income in Dec 2025 was +$534,551.41.",
            "metric": "operating_income",
            "period": "2025-12",
            "claimed_value": 534551.41,
            "claimed_unit": "currency",
        },
        {
            "claim_text": "Normalized operating loss in Dec 2025 was -$381,241.27.",
            "metric": "normalized_operating_income",
            "period": "2025-12",
            "claimed_value": -381241.27,
            "claimed_unit": "currency",
        },
        {
            "claim_text": "Normalized core operating expenses in Dec 2025 were $513,650.59.",
            "metric": "normalized_core_opex",
            "period": "2025-12",
            "claimed_value": 513650.59,
            "claimed_unit": "currency",
        },
        {
            "claim_text": "Reported operating expenses in Dec 2025 were -$402,142.09.",
            "metric": "total_opex",
            "period": "2025-12",
            "claimed_value": -402142.09,
            "claimed_unit": "currency",
        },
    ]

    for c in valid_claims:
        res = validator.validate_claim(c)
        assert res.status == "VERIFIED", f"Failed verification for {c['metric']}: {res.explanation}"

    # Invalid / fabricated reconciliation claim (e.g. LLM invented -$1,580,432.22 adjustment)
    fake_claim = {
        "claim_text": "December 2025 operating income was adjusted by -$1,580,432.22.",
        "metric": "operating_income",
        "period": "2025-12",
        "claimed_value": -1580432.22,
        "claimed_unit": "currency",
    }
    res_fake = validator.validate_claim(fake_claim)
    assert res_fake.status == "INVALID"


def test_validator_distinguishes_numerical_from_qualitative(sample_analysis_data):
    """Regression test 3: Validator explicitly distinguishes numerical claims from qualitative narrative."""
    validator = NumericalClaimValidator(sample_analysis_data)
    claims = [
        {
            "claim_text": "January 2025 revenue stood at $167,587.50.",
            "metric": "revenue",
            "period": "2025-01",
            "claimed_value": 167587.50,
            "claimed_unit": "currency",
        }
    ]

    output = validator.validate_claims(claims)
    summary = output["summary"]

    # Explicit scope distinction keys
    assert summary["report_scope"] == "DISCRETE_NUMERICAL_CLAIMS_ONLY"
    assert summary["qualitative_audit_status"] == "UNVERIFIED_PENDING_HUMAN_AUDIT"
    assert summary["full_report_certification"] == "PARTIAL_VERIFICATION_NUMERICAL_ONLY"
    assert "scope_disclaimer" in summary
    assert "NOT verified by this numerical pass" in summary["scope_disclaimer"]

    # Report markdown must contain explicit warning and boundary notice
    report = validator.generate_markdown_report(output)
    assert "Scope & Verification Boundary Warning" in report
    assert "Qualitative commentary, causal interpretations" in report
    assert "does **not** certify the entire financial report narrative as 100% accurate" in report


def test_narrative_causal_statement_audit(sample_analysis_data):
    """Regression test 4: audit_commentary_narrative detects unsupported causal claims and magnitude errors."""
    validator = NumericalClaimValidator(sample_analysis_data)

    unqualified_text = (
        "Gross margins remained around 70%, indicating pricing power and cost control in core operations.\n"
        "June 2026 revenue was -$12,061.55 driven by seasonal decline from May's peak.\n"
        "Normalized performance improved from -$4.462B to -$4.064B, showing operational efficiency gains."
    )

    audit_result = validator.audit_commentary_narrative(unqualified_text)
    assert audit_result["narrative_quality_status"] == "CONTAINS_UNVERIFIED_ASSERTIONS"
    assert audit_result["unverified_causal_assertions_count"] >= 3
    assert audit_result["scale_warnings_count"] >= 2  # flags -$4.462B and -$4.064B

    flagged_types = [fa["type"] for fa in audit_result["flagged_assertions"]]
    assert "pricing power" in flagged_types
    assert "cost control" in flagged_types
    assert "seasonality" in flagged_types
    assert "operational efficiency" in flagged_types

    # Qualified / neutral text must be recognized as NEUTRAL_OR_QUALIFIED
    qualified_text = (
        "Gross margins remained around 70%. Note: Whether this indicates pricing power or cost control is an unverified hypothesis requiring finance confirmation.\n"
        "June 2026 observed contraction of -$12,061.55; attributing this to seasonality is an unverified hypothesis.\n"
        "Normalized operating loss narrowed from -$4,462,347.78 to -$4,064,285.76; attributing this to operational efficiency is a hypothesis pending review."
    )

    clean_audit = validator.audit_commentary_narrative(qualified_text)
    assert clean_audit["narrative_quality_status"] == "NEUTRAL_OR_QUALIFIED"
    assert clean_audit["unverified_causal_assertions_count"] == 0
    assert clean_audit["scale_warnings_count"] == 0
