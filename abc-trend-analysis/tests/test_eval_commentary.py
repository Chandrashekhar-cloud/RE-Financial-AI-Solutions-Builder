"""Negative and positive test suite for CommentaryEvaluator.

Tests commentary evaluation against corrupted variations of the real report.md:
1. Positive test: Unmodified report.md must pass with 100.0 score.
2. Negative test a: Invented dollar figure not present in analysis.json.
3. Negative test b: Wrong anomaly count or missing anomaly count.
4. Negative test c: Missing data limitations disclosure; missing QBO-vs-Excel differences disclosure.
5. Negative test d: Unsupported causal claims using new words not in the old blacklist.
6. Negative test e: Misleading profitability claim in the critical accounting anomaly period.
"""

import json
import re
from pathlib import Path
import pytest

from evals.eval_commentary import CommentaryEvaluator


BASE_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"
REPORT_PATH = FIXTURES_DIR / "report.md"
ANALYSIS_PATH = FIXTURES_DIR / "analysis.json"
QBO_REPORT_PATH = FIXTURES_DIR / "qbo_live_pnl_report.json"


@pytest.fixture(scope="module")
def real_analysis_data():
    with open(ANALYSIS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def real_report_text():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestCommentaryEvaluatorGrounding:
    """Tests commentary evaluation against positive and deliberately corrupted reports."""

    def test_positive_unmodified_report_passes(self, real_analysis_data, real_report_text):
        """Positive test: The unmodified canonical report.md must pass with full score."""
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(real_report_text)

        assert result["passed"] is True, f"Unmodified report failed evaluation: {result}"
        assert result["total_score"] == 100.0, f"Expected 100.0 score, got {result['total_score']}"

    def test_negative_invented_dollar_figure(self, real_analysis_data, real_report_text):
        """Negative test a: Adding a dollar figure not in analysis.json must fail evaluation."""
        corrupted = real_report_text + "\n\nAdditionally, the company spent $789,123.45 on secret marketing campaigns.\n"
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail commentary with invented figure $789,123.45"
        assert result["checks"]["Numerical Grounding"]["passed"] is False

    def test_negative_near_miss_invented_dollar_figure(self, real_analysis_data, real_report_text):
        """Negative test: Changing tax credit slightly beyond rounding ($1,244,429.84 -> $1,261,000.00) must fail."""
        corrupted = real_report_text.replace("$1,244,429.84", "$1,261,000.00")
        assert corrupted != real_report_text, "Failed to substitute tax credit near miss"
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail commentary with near-miss dollar figure $1,261,000.00"
        assert result["checks"]["Numerical Grounding"]["passed"] is False

    def test_negative_near_miss_gross_margin_shifted(self, real_analysis_data, real_report_text):
        """Negative test: Shifting real gross margin percentage by 2 points (69.47% -> 71.47%) must fail."""
        corrupted = real_report_text.replace("69.47%", "71.47%")
        assert corrupted != real_report_text, "Failed to substitute gross margin near miss"
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail commentary with shifted gross margin 71.47%"
        assert result["checks"]["Numerical Grounding"]["passed"] is False

    def test_negative_near_miss_monthly_revenue_shifted(self, real_analysis_data, real_report_text):
        """Negative test: Shifting real monthly revenue by 3% ($190,029.49 -> $195,730.37) must fail."""
        corrupted = real_report_text.replace("$190,029.49", "$195,730.37")
        assert corrupted != real_report_text, "Failed to substitute revenue near miss"
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail commentary with shifted revenue $195,730.37"
        assert result["checks"]["Numerical Grounding"]["passed"] is False

    def test_negative_wrong_anomaly_count(self, real_analysis_data, real_report_text):
        """Negative test b: Changing or asserting the wrong anomaly count must fail evaluation."""
        # Add an explicit incorrect anomaly count statement
        corrupted = real_report_text + "\n\nTotal audit flags / anomalies identified: 5 (all minor).\n"
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail commentary with incorrect anomaly count"

    def test_negative_missing_data_limitations_disclosure(self, real_analysis_data, real_report_text):
        """Negative test c1: Removing data-limitations section must fail evaluation."""
        # Remove the cash-burn / balance-sheet limitation checklist item
        corrupted = re.sub(
            r'-\s+\[\s*\]\s+\*\*Cash Flow vs\. Operating Loss Disclosure:\*\*.*?\n',
            '',
            real_report_text,
            flags=re.DOTALL
        )
        assert corrupted != real_report_text, "Failed to strip data limitations disclosure"
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail commentary missing data-limitations disclosure"

    def test_negative_missing_qbo_vs_excel_differences_disclosure(self, real_analysis_data, real_report_text):
        """Negative test c2: Removing the QuickBooks-vs-Excel differences disclosure must fail evaluation."""
        # Strip Section 8 (Cross-Dataset Baseline Comparison)
        corrupted = re.split(r'## 8\. Cross-Dataset Baseline Comparison', real_report_text)[0]
        assert corrupted != real_report_text, "Failed to strip Section 8"
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail commentary missing QBO vs Excel differences disclosure"

    def test_negative_unsupported_causal_claim_new_words(self, real_analysis_data, real_report_text):
        """Negative test d: Unsupported causal claims using new vocabulary must fail evaluation."""
        causal_sentences = (
            "\n\nIn Q3 2025, revenue fell because clients paused subscriptions. "
            "Later in Q4, costs rose due to a new office lease. "
            "Finally, the dip was driven by seasonal hiring.\n"
        )
        corrupted = real_report_text + causal_sentences
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail commentary with unverified causal claims in new words"
        assert result["checks"]["Unsupported Causal Claims"]["passed"] is False

    def test_negative_misleading_profitability_claim(self, real_analysis_data, real_report_text):
        """Negative test e: Claiming genuine operational profitability in anomaly period must fail."""
        # Replace the rejection with an explicit claim of operational profitability in the anomaly period
        corrupted = real_report_text.replace(
            "The business DID NOT become genuinely operationally profitable in Dec 2025.",
            "The business became genuinely operationally profitable in the critical accounting-anomaly period of 2025-12."
        )
        assert corrupted != real_report_text, "Failed to substitute profitability claim"
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail commentary falsely asserting operational profitability"

    def test_negative_causal_loophole_grounded_word_fake_cause(self, real_analysis_data, real_report_text):
        """Negative test: Grounded words used as fake/unrelated causes must fail evaluation."""
        corrupted = real_report_text + (
            "\n\nRevenue fell because of a tax credit. "
            "Costs rose due to stock-based compensation in an unrelated month.\n"
        )
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)

        assert result["passed"] is False, "Evaluator should fail fake causal claims even if words are grounded"
        assert result["checks"]["Unsupported Causal Claims"]["passed"] is False

    def test_evaluator_passes_on_regenerated_pipeline_output(self, tmp_path):
        """Separate test: regenerates both analysis.json and report.md with offline pipeline into tmp_path and evaluates."""
        tmp_json = tmp_path / "analysis.json"
        tmp_report = tmp_path / "report.md"

        from scripts.run_pipeline import main as pipeline_main
        exit_code = pipeline_main([
            "--offline",
            "--qbo-report-path", str(QBO_REPORT_PATH.resolve()),
            "--output-json", str(tmp_json.resolve()),
            "--output-report", str(tmp_report.resolve()),
            "--quiet",
        ])

        assert exit_code == 0, f"Offline pipeline failed with exit code {exit_code}"
        assert tmp_json.exists(), f"Regenerated analysis.json missing at {tmp_json}"
        assert tmp_report.exists(), f"Regenerated report.md missing at {tmp_report}"

        with open(tmp_json, "r", encoding="utf-8") as f:
            gen_analysis = json.load(f)
        with open(tmp_report, "r", encoding="utf-8") as f:
            gen_report = f.read()

        evaluator = CommentaryEvaluator(gen_analysis)
        result = evaluator.evaluate(gen_report)

        assert result["passed"] is True, f"Evaluator failed on regenerated report: {result}"
        assert result["total_score"] == 100.0, f"Expected 100.0 score on regenerated report, got {result['total_score']}"

    def test_generalization_evaluator_passes_on_case9_fixture(self, tmp_path):
        """Generalization proof test: runs offline pipeline on CASE-09 fixture and verifies 100.0 commentary score."""
        tmp_json = tmp_path / "analysis.json"
        tmp_report = tmp_path / "report.md"
        case9_fixture = BASE_DIR / "evals" / "fixtures" / "case9_subtotals_generalization.xlsx"

        from scripts.cli import main as cli_main
        cli_main([
            "--input", str(case9_fixture.resolve()),
            "--output-json", str(tmp_json.resolve()),
            "--output-report", str(tmp_report.resolve()),
        ])

        assert tmp_json.exists() and tmp_report.exists()
        with open(tmp_json, "r", encoding="utf-8") as f:
            gen_analysis = json.load(f)
        with open(tmp_report, "r", encoding="utf-8") as f:
            gen_report = f.read()

        evaluator = CommentaryEvaluator(gen_analysis)
        result = evaluator.evaluate(gen_report)

        assert result["passed"] is True, f"CASE-09 commentary evaluation failed: {result}"
        assert result["total_score"] == 100.0, f"Expected 100.0 score, got {result['total_score']}"

    def test_generalization_evaluator_passes_on_case8_fixture(self, tmp_path):
        """Generalization proof test: runs offline pipeline on CASE-08 fixture and verifies 100.0 commentary score."""
        tmp_json = tmp_path / "analysis.json"
        tmp_report = tmp_path / "report.md"
        case8_fixture = BASE_DIR / "evals" / "fixtures" / "case8_different_company.xlsx"

        from scripts.cli import main as cli_main
        cli_main([
            "--input", str(case8_fixture.resolve()),
            "--output-json", str(tmp_json.resolve()),
            "--output-report", str(tmp_report.resolve()),
        ])

        assert tmp_json.exists() and tmp_report.exists()
        with open(tmp_json, "r", encoding="utf-8") as f:
            gen_analysis = json.load(f)
        with open(tmp_report, "r", encoding="utf-8") as f:
            gen_report = f.read()

        evaluator = CommentaryEvaluator(gen_analysis)
        result = evaluator.evaluate(gen_report)

        assert result["passed"] is True, f"CASE-08 commentary evaluation failed: {result}"
        assert result["total_score"] == 100.0, f"Expected 100.0 score, got {result['total_score']}"

    def test_negative_deleted_anomaly_bullet_fails(self, real_analysis_data, real_report_text):
        """Negative test: Deleting one anomaly bullet from the ABC report must cause the evaluator to fail."""
        lines = real_report_text.splitlines(keepends=True)
        deleted = False
        corrupted_lines = []
        for line in lines:
            if not deleted and line.strip().startswith("- **[") and "Income Tax Benefit" in line:
                deleted = True
                continue
            corrupted_lines.append(line)
        assert deleted, "Could not find target anomaly bullet in canonical report fixture"
        corrupted_report = "".join(corrupted_lines)

        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted_report)
        assert result["passed"] is False, "Evaluator should fail when an anomaly bullet is deleted"
        assert result["total_score"] < 100.0

    def test_unsupported_causal_seasonality_assertion(self, real_analysis_data, real_report_text):
        """Negative test: Asserting revenue drop was 'driven by seasonal decline' must fail causal checks."""
        corrupted = real_report_text + "\n\nIn June 2026, revenue dropped by -5.8% driven by seasonal decline from May's peak.\n"
        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(corrupted)
        assert result["passed"] is False
        assert result["checks"]["Unsupported Causal Claims"]["passed"] is False

    def test_corrected_llm_commentary_file_passes(self, real_analysis_data):
        """Verifies that results/llm_commentary.md passes all four dimensions of commentary evaluation."""
        llm_comm_path = BASE_DIR / "results" / "llm_commentary.md"
        assert llm_comm_path.exists(), "results/llm_commentary.md does not exist"
        with open(llm_comm_path, "r", encoding="utf-8") as f:
            commentary_text = f.read()

        evaluator = CommentaryEvaluator(real_analysis_data)
        result = evaluator.evaluate(commentary_text)
        assert result["passed"] is True, f"llm_commentary.md failed evaluation: {result['checks']}"
        assert result["total_score"] == 100.0, f"Expected 100.0, got {result['total_score']}"


