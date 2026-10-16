"""Evaluation suite runner and grading harness.

Executes golden evaluation cases, verifies expected financial outcomes,
computes weighted scores, detects regressions, and outputs structured results.
"""

import json
import sys
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List

from scripts.engine import FinancialCalculationEngine
from scripts.models import Severity, AnomalyCategory


def grade_case(case_def: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    case_id = case_def["id"]
    name = case_def["name"]
    weight = case_def["weight"]
    fixture_path = base_dir / case_def["fixture"]
    expected = case_def["expected"]

    assertions_passed = []
    assertions_failed = []

    try:
        engine = FinancialCalculationEngine(str(fixture_path))
        result = engine.run_analysis()
    except Exception as e:
        return {
            "id": case_id,
            "name": name,
            "weight": weight,
            "score": 0.0,
            "status": "ERROR",
            "error": str(e),
            "assertions_passed": [],
            "assertions_failed": [f"Execution crashed: {e}"],
        }

    # Run assertions based on case
    # Periods count
    if "periods_count" in expected:
        if len(result.periods_analyzed) == expected["periods_count"]:
            assertions_passed.append(f"Periods count == {expected['periods_count']}")
        else:
            assertions_failed.append(f"Periods count: expected {expected['periods_count']}, got {len(result.periods_analyzed)}")

    # Months were reversed
    if "months_were_reversed" in expected:
        if result.months_were_reversed == expected["months_were_reversed"]:
            assertions_passed.append(f"Months were reversed == {expected['months_were_reversed']}")
        else:
            assertions_failed.append(f"Months reversed: expected {expected['months_were_reversed']}, got {result.months_were_reversed}")

    # Chronological ordering
    if "first_period_chronological" in expected:
        if result.periods_analyzed[0]["key"] == expected["first_period_chronological"]:
            assertions_passed.append(f"First period == {expected['first_period_chronological']}")
        else:
            assertions_failed.append(f"First period: expected {expected['first_period_chronological']}, got {result.periods_analyzed[0]['key']}")

    if "last_period_chronological" in expected:
        if result.periods_analyzed[-1]["key"] == expected["last_period_chronological"]:
            assertions_passed.append(f"Last period == {expected['last_period_chronological']}")
        else:
            assertions_failed.append(f"Last period: expected {expected['last_period_chronological']}, got {result.periods_analyzed[-1]['key']}")

    # Valid TTM windows count
    if "valid_ttm_windows_count" in expected:
        actual_ttm_count = len([w for w in result.ttm_windows if w.is_valid])
        if actual_ttm_count == expected["valid_ttm_windows_count"]:
            assertions_passed.append(f"Valid TTM count == {expected['valid_ttm_windows_count']}")
        else:
            assertions_failed.append(f"Valid TTM count: expected {expected['valid_ttm_windows_count']}, got {actual_ttm_count}")

    # Reconciliation failures count
    if "failed_reconciliation_count" in expected:
        actual_failed_rec = len([rc for rc in result.reconciliation_checks if not rc.is_valid])
        if actual_failed_rec == expected["failed_reconciliation_count"]:
            assertions_passed.append(f"Failed reconciliation checks == {expected['failed_reconciliation_count']}")
        else:
            assertions_failed.append(f"Failed reconciliation checks: expected {expected['failed_reconciliation_count']}, got {actual_failed_rec}")

    # TTM limitation flag
    if "has_ttm_limitation_flag" in expected:
        has_flag = any(a.category == AnomalyCategory.LIMITATION and "TTM" in a.account for a in result.anomalies)
        if has_flag == expected["has_ttm_limitation_flag"]:
            assertions_passed.append("TTM limitation flag emitted correctly")
        else:
            assertions_failed.append(f"TTM limitation flag: expected {expected['has_ttm_limitation_flag']}, got {has_flag}")

    # Dec 2025 anomaly assertions
    if "has_critical_tax_benefit_flag" in expected:
        has_tax_flag = any(
            a.severity == Severity.CRITICAL and "tax benefit" in a.account.lower()
            for a in result.anomalies
        )
        if has_tax_flag == expected["has_critical_tax_benefit_flag"]:
            assertions_passed.append("Critical tax benefit anomaly flagged")
        else:
            assertions_failed.append(f"Tax benefit flag: expected {expected['has_critical_tax_benefit_flag']}, got {has_tax_flag}")

    if "has_sbc_warning_flag" in expected:
        has_sbc_flag = any("stock-based" in a.account.lower() or "stock based" in a.account.lower() for a in result.anomalies)
        if has_sbc_flag == expected["has_sbc_warning_flag"]:
            assertions_passed.append("Stock-based compensation warning flagged")
        else:
            assertions_failed.append(f"SBC flag: expected {expected['has_sbc_warning_flag']}, got {has_sbc_flag}")

    if "rejects_genuine_profitability" in expected:
        # Check Dec 2025 summary
        dec_summary = next((s for s in result.monthly_summaries if s.period == "2025-12"), None)
        if dec_summary:
            rep_oi = Decimal(dec_summary.operating_income)
            core_oi = Decimal(dec_summary.normalized_operating_income)
            if rep_oi > Decimal("0.00") and core_oi < Decimal("0.00"):
                assertions_passed.append("Reported Op Income positive while Normalized Core Op Income is negative (non-profitable)")
            else:
                assertions_failed.append(f"Dec profitability rejection check failed: rep_oi={rep_oi}, core_oi={core_oi}")
        else:
            assertions_failed.append("Dec 2025 summary period not found")

    # Reversal flags
    if "has_reversal_flags" in expected:
        has_rev = any(a.category == AnomalyCategory.REVERSAL for a in result.anomalies)
        if has_rev == expected["has_reversal_flags"]:
            assertions_passed.append("Reversal flags emitted")
        else:
            assertions_failed.append(f"Reversal flags: expected {expected['has_reversal_flags']}, got {has_rev}")

    # Missing period gap
    if "missing_period_detected" in expected:
        detected_gap = any(gap["missing_month"] == expected["missing_period_detected"] for gap in result.missing_period_gaps)
        if detected_gap:
            assertions_passed.append(f"Missing period {expected['missing_period_detected']} detected")
        else:
            assertions_failed.append(f"Missing period: expected {expected['missing_period_detected']} in {result.missing_period_gaps}")

    # Reconciliation failure detected
    if "reconciliation_failure_detected" in expected:
        has_failed = any(not rc.is_valid for rc in result.reconciliation_checks)
        if has_failed == expected["reconciliation_failure_detected"]:
            assertions_passed.append("Reconciliation failure caught as expected")
        else:
            assertions_failed.append(f"Reconciliation failure: expected {expected['reconciliation_failure_detected']}, got {has_failed}")

    # Values check
    if "ttm_revenue" in expected:
        latest_ttm = next((w for w in reversed(result.ttm_windows) if w.is_valid), None)
        if latest_ttm and latest_ttm.revenue == expected["ttm_revenue"]:
            assertions_passed.append(f"TTM revenue == {expected['ttm_revenue']}")
        else:
            actual_ttm_rev = latest_ttm.revenue if latest_ttm else "None"
            assertions_failed.append(f"TTM revenue: expected {expected['ttm_revenue']}, got {actual_ttm_rev}")

    if "revenue_latest" in expected:
        last_rev = result.monthly_summaries[-1].revenue if result.monthly_summaries else None
        if last_rev == expected["revenue_latest"]:
            assertions_passed.append(f"Latest revenue == {expected['revenue_latest']}")
        else:
            assertions_failed.append(f"Latest revenue: expected {expected['revenue_latest']}, got {last_rev}")

    if "critical_anomalies_count" in expected:
        crit_count = len([a for a in result.anomalies if a.severity == Severity.CRITICAL])
        if crit_count == expected["critical_anomalies_count"]:
            assertions_passed.append(f"Critical anomalies count == {expected['critical_anomalies_count']}")
        else:
            assertions_failed.append(f"Critical anomalies count: expected {expected['critical_anomalies_count']}, got {crit_count}")

    if "dec_reported_operating_income_positive" in expected:
        dec_s = next((s for s in result.monthly_summaries if s.period == "2025-12"), None)
        is_pos = (Decimal(dec_s.operating_income) > Decimal("0.00")) if dec_s else False
        if is_pos == expected["dec_reported_operating_income_positive"]:
            assertions_passed.append("Dec reported operating income is positive as expected")
        else:
            assertions_failed.append(f"Dec reported operating income positive: expected {expected['dec_reported_operating_income_positive']}, got {is_pos}")

    if "dec_normalized_operating_income_negative" in expected:
        dec_s = next((s for s in result.monthly_summaries if s.period == "2025-12"), None)
        is_neg = (Decimal(dec_s.normalized_operating_income) < Decimal("0.00")) if dec_s else False
        if is_neg == expected["dec_normalized_operating_income_negative"]:
            assertions_passed.append("Dec normalized operating income is negative as expected")
        else:
            assertions_failed.append(f"Dec normalized operating income negative: expected {expected['dec_normalized_operating_income_negative']}, got {is_neg}")

    if "mar_reversal_flagged" in expected:
        has_mar_rev = any(a.category == AnomalyCategory.REVERSAL and "03" in a.period for a in result.anomalies)
        if has_mar_rev == expected["mar_reversal_flagged"]:
            assertions_passed.append("March reversal anomaly flagged correctly")
        else:
            assertions_failed.append(f"March reversal flag: expected {expected['mar_reversal_flagged']}, got {has_mar_rev}")

    if "has_critical_missing_period_flag" in expected:
        has_crit_gap = any(a.category == AnomalyCategory.MISSING_PERIOD for a in result.anomalies)
        if has_crit_gap == expected["has_critical_missing_period_flag"]:
            assertions_passed.append("Critical missing period flag emitted")
        else:
            assertions_failed.append(f"Missing period flag: expected {expected['has_critical_missing_period_flag']}, got {has_crit_gap}")

    if "failed_period" in expected:
        failed_periods = [rc.period for rc in result.reconciliation_checks if not rc.is_valid]
        if expected["failed_period"] in failed_periods:
            assertions_passed.append(f"Failed reconciliation caught for {expected['failed_period']}")
        else:
            assertions_failed.append(f"Failed period: expected {expected['failed_period']} in {failed_periods}")

    # Evidence-based management commentary assertions
    if "commentary_checks" in expected:
        from scripts.reporter import FinancialReportGenerator
        rep_gen = FinancialReportGenerator(result)
        report_md = rep_gen.generate_markdown()
        for term in expected["commentary_checks"]:
            if term.lower() in report_md.lower():
                assertions_passed.append(f"Commentary contains '{term}'")
            else:
                assertions_failed.append(f"Commentary missing required term: '{term}'")

    total_assertions = len(assertions_passed) + len(assertions_failed)
    passed_count = len(assertions_passed)
    score = (passed_count / total_assertions * weight) if total_assertions > 0 else 0.0
    status = "PASSED" if len(assertions_failed) == 0 else "FAILED"

    return {
        "id": case_id,
        "name": name,
        "weight": weight,
        "score": round(score, 2),
        "status": status,
        "assertions_passed": assertions_passed,
        "assertions_failed": assertions_failed,
    }


def run_evals(base_dir: Path = None) -> Dict[str, Any]:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent

    eval_json_path = base_dir / "evals" / "eval_cases.json"
    with open(eval_json_path, "r", encoding="utf-8") as f:
        suite_def = json.load(f)

    results = []
    total_score = 0.0
    max_possible_score = 0.0

    print("=" * 65)
    print("RE Financial Services - Trend Analysis Evaluation Suite")
    print("=" * 65)

    for case in suite_def["cases"]:
        res = grade_case(case, base_dir)
        results.append(res)
        total_score += res["score"]
        max_possible_score += case["weight"]
        status_symbol = "PASS" if res["status"] == "PASSED" else "FAIL"
        print(f"[{status_symbol:4s}] {res['id']:7s} | {res['name']:38s} | Score: {res['score']:5.1f}/{res['weight']:2d} | {res['status']}")
        if res["assertions_failed"]:
            for f in res["assertions_failed"]:
                print(f"       Fail: {f}")

    pct_score = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0.0
    print("-" * 65)
    print(f"Overall Evaluation Score: {total_score:.1f} / {max_possible_score:.1f} ({pct_score:.1f}%)")
    print(f"Cases Passed: {len([r for r in results if r['status'] == 'PASSED'])} / {len(results)}")
    print("=" * 65)

    output_report = {
        "suite_description": suite_def["description"],
        "total_score": round(total_score, 2),
        "max_possible_score": round(max_possible_score, 2),
        "percentage_score": round(pct_score, 2),
        "total_cases": len(results),
        "cases_passed": len([r for r in results if r["status"] == "PASSED"]),
        "cases_failed": len([r for r in results if r["status"] == "FAILED"]),
        "case_results": results,
    }

    # Baseline comparison & regression detection
    baseline_path = base_dir / "evals" / "baseline_eval_report.json"
    regression_detected = False
    if baseline_path.exists():
        try:
            with open(baseline_path, "r", encoding="utf-8") as bf:
                baseline_data = json.load(bf)
            base_score = baseline_data.get("total_score", 0.0)
            score_diff = round(total_score - base_score, 2)
            print("-" * 65)
            print("Baseline Comparison (evals/baseline_eval_report.json):")
            print(f"  Baseline Score: {base_score:.1f} / {baseline_data.get('max_possible_score', 100.0):.1f}")
            print(f"  Current Score:  {total_score:.1f} / {max_possible_score:.1f}")
            if score_diff < 0:
                regression_detected = True
                print(f"  REGRESSION DETECTED: Score dropped by {abs(score_diff):.1f} points!")
            else:
                print(f"  Status:         Score delta: +{score_diff:.1f} pts [NO REGRESSION DETECTED]")
            print("-" * 65)
            output_report["baseline_comparison"] = {
                "baseline_score": base_score,
                "current_score": total_score,
                "score_delta": score_diff,
                "regression_detected": regression_detected,
            }
        except Exception as be:
            print(f"Warning: Could not compare against baseline: {be}")

    # Save to results/eval_report.json
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / "eval_report.json", "w", encoding="utf-8") as f:
        json.dump(output_report, f, indent=2)

    return output_report


if __name__ == "__main__":
    report = run_evals()
    sys.exit(0 if (report["cases_failed"] == 0 and not report.get("baseline_comparison", {}).get("regression_detected", False)) else 1)
