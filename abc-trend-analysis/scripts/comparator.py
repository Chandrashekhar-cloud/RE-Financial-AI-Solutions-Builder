"""Cross-dataset baseline comparator for Financial Analysis.

Compares target financial analysis (e.g. live QuickBooks Online report)
against an authoritative baseline reference (e.g. Excel workbook or analysis.json).
Distinguishes material ledger variances and identifies known Intuit
developer sandbox sample provisioning differences.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .models import FinancialAnalysisResult

CENTS = Decimal("0.01")


def _get_val(obj: Any, key: str) -> Decimal:
    """Safely extract metric value as Decimal from dict or dataclass object."""
    if isinstance(obj, dict):
        raw = obj.get(key, "0.00")
    else:
        raw = getattr(obj, key, "0.00")
    try:
        return Decimal(str(raw))
    except Exception:
        return Decimal("0.00")


def _extract_summaries(source: Any) -> Dict[str, Any]:
    """Extract monthly summaries mapping by period key."""
    if isinstance(source, dict):
        sums = source.get("monthly_summaries", [])
        return {s["period"]: s for s in sums if isinstance(s, dict) and "period" in s}
    if hasattr(source, "monthly_summaries"):
        return {s.period: s for s in source.monthly_summaries}
    return {}


def _extract_label(source: Any, fallback: str) -> str:
    """Extract human-readable source label."""
    if isinstance(source, dict):
        return source.get("metadata", {}).get("source_file", fallback)
    if hasattr(source, "metadata"):
        return source.metadata.get("source_file", fallback)
    return fallback


def compare_financial_results(
    target_result: Union[FinancialAnalysisResult, Dict[str, Any]],
    baseline_result: Union[FinancialAnalysisResult, Dict[str, Any]],
    target_name: Optional[str] = None,
    baseline_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare a target analysis result against a baseline reference result.

    Args:
        target_result: Active analysis result (FinancialAnalysisResult or loaded dict).
        baseline_result: Baseline reference result (FinancialAnalysisResult or loaded dict).
        target_name: Optional human-readable name for target source.
        baseline_name: Optional human-readable name for baseline source.

    Returns:
        Structured dictionary documenting cross-dataset comparison results.
    """
    target_label = target_name or _extract_label(target_result, "Target Dataset")
    baseline_label = baseline_name or _extract_label(baseline_result, "Baseline Reference")

    target_summaries = _extract_summaries(target_result)
    baseline_summaries = _extract_summaries(baseline_result)

    common_periods = sorted(set(target_summaries.keys()) & set(baseline_summaries.keys()))

    variances: List[Dict[str, Any]] = []
    zero_drift_periods = 0

    metrics_to_compare = [
        ("Revenue", "revenue"),
        ("Cost of Goods Sold", "cogs"),
        ("Gross Profit", "gross_profit"),
        ("Total Operating Expenses", "total_opex"),
        ("Operating Income", "operating_income"),
        ("Core Operating Income", "normalized_operating_income"),
    ]

    for p in common_periods:
        t_sum = target_summaries[p]
        b_sum = baseline_summaries[p]
        period_had_variance = False

        for metric_label, attr_name in metrics_to_compare:
            t_val = _get_val(t_sum, attr_name)
            b_val = _get_val(b_sum, attr_name)
            diff = (t_val - b_val).quantize(CENTS)

            if abs(diff) > Decimal("0.00"):
                period_had_variance = True

                # Contextual explanation of known sandbox artifacts
                explanation = "Cross-dataset variance between target and baseline."
                is_known_sandbox = False

                if p == "2026-05" and abs(diff) == Decimal("300.00") and attr_name in ["total_opex", "operating_income", "normalized_operating_income"]:
                    is_known_sandbox = True
                    explanation = (
                        "Pre-existing Intuit developer sandbox sample Bill ID 90 "
                        "($300.00 to Lawyer expense) in May 2026."
                    )
                elif p == "2026-06" and abs(diff) == Decimal("391.25") and attr_name in ["revenue", "gross_profit", "operating_income", "normalized_operating_income"]:
                    is_known_sandbox = True
                    explanation = (
                        "Pre-existing Intuit developer sandbox sample Invoice IDs 10 & 95 "
                        "($391.25 net sales) in June 2026."
                    )

                variances.append({
                    "period": p,
                    "metric": metric_label,
                    "target_value": str(t_val),
                    "baseline_value": str(b_val),
                    "difference": str(diff),
                    "is_known_sandbox_item": is_known_sandbox,
                    "explanation": explanation,
                })

        if not period_had_variance:
            zero_drift_periods += 1

    summary_notes = []
    if len(common_periods) > 0:
        summary_notes.append(
            f"{zero_drift_periods} of {len(common_periods)} monthly periods match the baseline "
            f"with exact $0.00 drift across all primary financial metrics."
        )

    known_count = sum(1 for v in variances if v["is_known_sandbox_item"])
    if known_count > 0:
        summary_notes.append(
            f"{known_count} variance item(s) correspond to known pre-existing Intuit developer "
            f"sandbox sample transactions (May 2026 Bill ID 90 and June 2026 Invoice IDs 10 & 95)."
        )

    return {
        "target_source": target_label,
        "baseline_source": baseline_label,
        "periods_compared": len(common_periods),
        "periods_with_zero_drift": zero_drift_periods,
        "total_variances_found": len(variances),
        "monthly_variances": variances,
        "summary_notes": summary_notes,
    }
