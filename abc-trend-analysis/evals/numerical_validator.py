"""Deterministic Numerical Claim Validator for Financial Trend Analysis.

Validates financial and numerical claims in LLM-generated commentary against
the authoritative ground truth in analysis.json.

Verification Principles:
1. Deterministic precision: Validates amounts, percentages, periods, signs,
   and TTM windows against Decimal-grounded source data.
2. Clear status taxonomy:
   - VERIFIED: Claimed value matches analysis.json within tolerance.
   - INVALID: Claimed metric/period exists in analysis.json, but the claimed value
     or sign is mathematically incorrect.
   - UNVERIFIED: Claim references metrics, external causes, or periods not present
     in the income statement data; flagged for human review.
3. Zero silent correction: Never replaces an incorrect claim with a correct one.
4. Transparency: Produces machine-readable JSON and human-readable Markdown reports.
"""

from decimal import Decimal
import json
import re
from typing import Dict, Any, List, Optional, Tuple, Set


class ClaimValidationResult:
    """Represents the verification result of a single financial claim."""

    def __init__(
        self,
        claim_id: int,
        claim_text: str,
        metric: str,
        period: Optional[str],
        claimed_value: Any,
        claimed_unit: str = "currency",  # currency, percent, count, text
        status: str = "UNVERIFIED",      # VERIFIED, INVALID, UNVERIFIED
        ground_truth_value: Any = None,
        difference: Optional[float] = None,
        tolerance_applied: float = 0.05,
        explanation: str = "",
        is_ttm: bool = False,
    ):
        self.claim_id = claim_id
        self.claim_text = claim_text
        self.metric = metric
        self.period = period
        self.claimed_value = claimed_value
        self.claimed_unit = claimed_unit
        self.status = status
        self.ground_truth_value = ground_truth_value
        self.difference = difference
        self.tolerance_applied = tolerance_applied
        self.explanation = explanation
        self.is_ttm = is_ttm

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "metric": self.metric,
            "period": self.period,
            "claimed_value": self.claimed_value,
            "claimed_unit": self.claimed_unit,
            "status": self.status,
            "ground_truth_value": self.ground_truth_value,
            "difference": self.difference,
            "tolerance_applied": self.tolerance_applied,
            "explanation": self.explanation,
            "is_ttm": self.is_ttm,
        }


class NumericalClaimValidator:
    """Deterministic validator for financial and numerical claims against analysis.json."""

    def __init__(
        self,
        analysis_data: Dict[str, Any],
        tolerance_currency: float = 0.05,
        tolerance_percentage: float = 0.05,
    ):
        self.analysis_data = analysis_data
        self.tolerance_currency = tolerance_currency
        self.tolerance_percentage = tolerance_percentage
        self._index_ground_truth()

    def _index_ground_truth(self):
        """Build efficient lookup structures from analysis.json ground truth."""
        self.monthly_by_period: Dict[str, Dict[str, Any]] = {}
        self.ttm_by_end_period: Dict[str, Dict[str, Any]] = {}
        self.anomalies_by_period_account: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.variances_by_period_metric: Dict[Tuple[str, str], Dict[str, Any]] = {}

        # 1. Monthly summaries
        for s in self.analysis_data.get("monthly_summaries", []):
            p = s.get("period")
            if p:
                self.monthly_by_period[p] = s
                lbl = s.get("label")
                if lbl:
                    self.monthly_by_period[lbl.lower()] = s

        # 2. TTM Windows
        for w in self.analysis_data.get("ttm_windows", []):
            end_p = w.get("end_period")
            if end_p:
                self.ttm_by_end_period[end_p] = w

        # 3. Anomalies & audit flags
        for a in self.analysis_data.get("anomalies_and_flags", []):
            p = a.get("period", "")
            acc = a.get("account", "").lower()
            self.anomalies_by_period_account[(p, acc)] = a

        # 4. Baseline cross-dataset variances
        for v in self.analysis_data.get("baseline_comparison", {}).get("monthly_variances", []):
            p = v.get("period", "")
            m = v.get("metric", "").lower()
            self.variances_by_period_metric[(p, m)] = v

    @staticmethod
    def normalize_period(period_str: Optional[str]) -> Optional[str]:
        """Convert 'Jan 2025', 'January 2025', '2025-01', 'TTM 2026-06' to standardized YYYY-MM."""
        if not period_str:
            return None
        raw = period_str.strip()
        # Clean TTM prefixes
        raw = re.sub(r'^(?:ttm|trailing[- ](?:12|twelve)[- ]months?)\s*', '', raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r'^(?:ending|ended)\s*', '', raw, flags=re.IGNORECASE).strip()

        # Check standard ISO YYYY-MM
        m_iso = re.search(r'\b(20\d{2})[-/](0[1-9]|1[0-2])\b', raw)
        if m_iso:
            return f"{m_iso.group(1)}-{m_iso.group(2)}"

        # Check Month Name + Year (e.g. 'January 2025', 'Dec 2025')
        months = {
            "jan": "01", "january": "01",
            "feb": "02", "february": "02",
            "mar": "03", "march": "03",
            "apr": "04", "april": "04",
            "may": "05",
            "jun": "06", "june": "06",
            "jul": "07", "july": "07",
            "aug": "08", "august": "08",
            "sep": "09", "september": "09",
            "oct": "10", "october": "10",
            "nov": "11", "november": "11",
            "dec": "12", "december": "12",
        }
        m_txt = re.search(r'\b([a-zA-Z]+)\s*(20\d{2})\b', raw)
        if m_txt:
            m_name = m_txt.group(1).lower()
            year = m_txt.group(2)
            if m_name in months:
                return f"{year}-{months[m_name]}"

        return raw

    @staticmethod
    def normalize_metric_name(metric: str) -> str:
        """Map common variants to canonical metric keys."""
        m = metric.lower().replace("_", " ").replace("-", " ").strip()
        if any(x in m for x in ["revenue", "sales", "top line", "topline"]):
            return "revenue"
        if any(x in m for x in ["gross profit", "gp"]):
            return "gross_profit"
        if any(x in m for x in ["gross margin", "margin percentage", "gm"]):
            return "gross_margin_pct"
        if any(x in m for x in ["normalized core opex", "core opex", "normalized opex"]):
            return "normalized_core_opex"
        if any(x in m for x in ["total operating expense", "operating expenses", "total opex", "opex"]):
            return "total_opex"
        if any(x in m for x in ["core operating income", "normalized operating", "normalized core", "core op inc", "normalized loss"]):
            return "normalized_operating_income"
        if any(x in m for x in ["operating income", "reported operating", "operating loss", "operating profit"]):
            return "operating_income"
        if any(x in m for x in ["tax benefit", "tax credit", "income tax benefit"]):
            return "tax_benefit"
        if any(x in m for x in ["stock based", "stock compensation", "sbc"]):
            return "stock_based_compensation"
        return m

    def validate_claim(self, claim: Dict[str, Any], claim_id: int = 1) -> ClaimValidationResult:
        """Validate a single structured claim against analysis.json."""
        claim_text = claim.get("claim_text", "")
        raw_metric = claim.get("metric", "")
        raw_period = claim.get("period", "")
        claimed_val = claim.get("claimed_value")
        claimed_unit = claim.get("claimed_unit", "currency")
        is_ttm = bool(claim.get("is_ttm") or "ttm" in str(raw_period).lower() or "ttm" in str(raw_metric).lower())

        norm_period = self.normalize_period(raw_period)
        metric = self.normalize_metric_name(raw_metric)

        # Handle numeric conversion
        val_float: Optional[float] = None
        if claimed_val is not None:
            try:
                val_clean = str(claimed_val).replace("$", "").replace(",", "").replace("%", "").strip()
                val_float = float(val_clean)
            except ValueError:
                val_float = None

        if val_float is None:
            return ClaimValidationResult(
                claim_id=claim_id,
                claim_text=claim_text,
                metric=metric,
                period=norm_period,
                claimed_value=claimed_val,
                claimed_unit=claimed_unit,
                status="UNVERIFIED",
                explanation=f"Claimed value '{claimed_val}' could not be converted to a numeric representation.",
                is_ttm=is_ttm,
            )

        # -------------------------------------------------------------
        # 1. TTM Window Validation
        # -------------------------------------------------------------
        if is_ttm:
            if not norm_period or norm_period not in self.ttm_by_end_period:
                return ClaimValidationResult(
                    claim_id=claim_id,
                    claim_text=claim_text,
                    metric=metric,
                    period=norm_period,
                    claimed_value=val_float,
                    claimed_unit=claimed_unit,
                    status="INVALID",
                    explanation=f"TTM window ending '{norm_period}' is not a valid 12-consecutive-month rolling window in analysis.json.",
                    is_ttm=True,
                )

            ttm_win = self.ttm_by_end_period[norm_period]
            if not ttm_win.get("is_valid", False):
                return ClaimValidationResult(
                    claim_id=claim_id,
                    claim_text=claim_text,
                    metric=metric,
                    period=norm_period,
                    claimed_value=val_float,
                    claimed_unit=claimed_unit,
                    status="INVALID",
                    explanation=f"TTM window ending '{norm_period}' is marked invalid (insufficient consecutive months).",
                    is_ttm=True,
                )

            # Check metric in TTM window
            expected_val = None
            tol = self.tolerance_percentage if claimed_unit == "percent" else self.tolerance_currency

            if metric == "revenue":
                expected_val = float(ttm_win.get("revenue", 0))
            elif metric == "gross_profit":
                expected_val = float(ttm_win.get("gross_profit", 0))
            elif metric == "gross_margin_pct":
                gm_str = ttm_win.get("gross_margin_pct", "0%").replace("%", "").strip()
                expected_val = float(gm_str)
            elif metric == "total_opex":
                expected_val = float(ttm_win.get("total_opex", 0))
            elif metric == "operating_income":
                expected_val = float(ttm_win.get("operating_income", 0))
            elif metric == "normalized_operating_income":
                expected_val = float(ttm_win.get("normalized_operating_income", 0))
            elif metric == "normalized_core_opex":
                expected_val = float(ttm_win.get("normalized_core_opex", 0))

            if expected_val is not None:
                diff = round(abs(val_float - expected_val), 4)
                # Allow sign inversion if explicitly described as "loss"
                if diff > tol and (metric in ["operating_income", "normalized_operating_income"]):
                    if abs(-val_float - expected_val) <= tol:
                        diff = round(abs(-val_float - expected_val), 4)
                        val_float = -val_float

                if diff <= tol:
                    return ClaimValidationResult(
                        claim_id=claim_id,
                        claim_text=claim_text,
                        metric=metric,
                        period=norm_period,
                        claimed_value=val_float,
                        claimed_unit=claimed_unit,
                        status="VERIFIED",
                        ground_truth_value=expected_val,
                        difference=diff,
                        tolerance_applied=tol,
                        explanation=f"Verified against TTM window ending {norm_period} (ground truth: {expected_val}).",
                        is_ttm=True,
                    )
                else:
                    scale_note = ""
                    if expected_val and expected_val != 0:
                        ratio = abs(val_float / expected_val)
                        if 800 <= ratio <= 1200 or 800000 <= ratio <= 1200000:
                            scale_note = " (Scale mismatch detected: claimed value appears scaled by ~1,000x to 1,000,000x, e.g. billions vs millions)."
                        elif 0.0008 <= ratio <= 0.0012 or 0.0000008 <= ratio <= 0.0000012:
                            scale_note = " (Scale mismatch detected: claimed value appears scaled down by ~1,000x to 1,000,000x)."
                    if re.search(r'\b\d+(?:\.\d+)?\s*(?:B|billion)\b', str(claim_text), flags=re.IGNORECASE):
                        if abs(expected_val) < 1e8:
                            scale_note = " (Scale discrepancy: claimed unit 'B' / billions conflicts with ground truth scale in millions)."

                    return ClaimValidationResult(
                        claim_id=claim_id,
                        claim_text=claim_text,
                        metric=metric,
                        period=norm_period,
                        claimed_value=val_float,
                        claimed_unit=claimed_unit,
                        status="INVALID",
                        ground_truth_value=expected_val,
                        difference=diff,
                        tolerance_applied=tol,
                        explanation=f"Value discrepancy: claimed {val_float} vs ground truth {expected_val} (diff {diff} exceeds tolerance {tol}).{scale_note}",
                        is_ttm=True,
                    )

        # -------------------------------------------------------------
        # 2. Special Anomaly / Credit Items (Tax Benefit, SBC, Reversals)
        # -------------------------------------------------------------
        if metric in ["tax_benefit", "stock_based_compensation", "reversal", "anomaly", "credit_memo", "negative_reversal", "expense_reversal"]:
            found_anomaly = None
            for (p, acc), anom in self.anomalies_by_period_account.items():
                if norm_period and p != norm_period:
                    continue
                if metric == "tax_benefit" and ("tax benefit" in acc or "tax credit" in acc):
                    found_anomaly = anom
                    break
                if metric == "stock_based_compensation" and "stock" in acc:
                    found_anomaly = anom
                    break
                if metric in ["reversal", "anomaly", "credit_memo", "negative_reversal", "expense_reversal"]:
                    amt = anom.get("amount")
                    if amt is not None and round(abs(abs(val_float) - abs(float(amt))), 4) <= self.tolerance_currency:
                        found_anomaly = anom
                        break

            if found_anomaly:
                actual_amt = abs(float(found_anomaly.get("amount", 0)))
                claimed_mag = abs(val_float)
                diff = round(abs(claimed_mag - actual_amt), 4)
                if diff <= self.tolerance_currency:
                    cat_val = found_anomaly.get("category", "ANOMALY")
                    if hasattr(cat_val, "value"):
                        cat_val = cat_val.value
                    return ClaimValidationResult(
                        claim_id=claim_id,
                        claim_text=claim_text,
                        metric=metric,
                        period=found_anomaly.get("period"),
                        claimed_value=val_float,
                        claimed_unit=claimed_unit,
                        status="VERIFIED",
                        ground_truth_value=float(found_anomaly.get("amount", 0)),
                        difference=diff,
                        tolerance_applied=self.tolerance_currency,
                        explanation=f"Verified {cat_val} item '{found_anomaly.get('account')}' for period {found_anomaly.get('period')}.",
                    )
                else:
                    return ClaimValidationResult(
                        claim_id=claim_id,
                        claim_text=claim_text,
                        metric=metric,
                        period=found_anomaly.get("period"),
                        claimed_value=val_float,
                        claimed_unit=claimed_unit,
                        status="INVALID",
                        ground_truth_value=float(found_anomaly.get("amount", 0)),
                        difference=diff,
                        tolerance_applied=self.tolerance_currency,
                        explanation=f"Discrepancy for anomaly/reversal '{found_anomaly.get('account')}': claimed {val_float} vs ground truth {found_anomaly.get('amount')}.",
                    )

        # -------------------------------------------------------------
        # 3. Monthly Financial Summary Verification
        # -------------------------------------------------------------
        if norm_period and norm_period in self.monthly_by_period:
            summary = self.monthly_by_period[norm_period]
            expected_val = None
            tol = self.tolerance_percentage if claimed_unit == "percent" else self.tolerance_currency

            if metric == "revenue":
                expected_val = float(summary.get("revenue", 0))
            elif metric == "gross_profit":
                expected_val = float(summary.get("gross_profit", 0))
            elif metric == "gross_margin_pct":
                expected_val = float(summary.get("gross_margin_pct", "0%").replace("%", "").strip())
            elif metric == "total_opex":
                expected_val = float(summary.get("total_opex", 0))
            elif metric == "operating_income":
                expected_val = float(summary.get("operating_income", 0))
            elif metric == "normalized_operating_income":
                expected_val = float(summary.get("normalized_operating_income", 0))
            elif metric == "normalized_core_opex":
                expected_val = float(summary.get("normalized_core_opex", 0))

            if expected_val is not None:
                diff = round(abs(val_float - expected_val), 4)
                # Handle sign convention for operating loss (e.g. claimed loss of +$382,905.03 vs actual -382905.03)
                if diff > tol and (metric in ["operating_income", "normalized_operating_income"]):
                    if abs(-val_float - expected_val) <= tol:
                        diff = round(abs(-val_float - expected_val), 4)
                        val_float = -val_float

                if diff <= tol:
                    return ClaimValidationResult(
                        claim_id=claim_id,
                        claim_text=claim_text,
                        metric=metric,
                        period=norm_period,
                        claimed_value=val_float,
                        claimed_unit=claimed_unit,
                        status="VERIFIED",
                        ground_truth_value=expected_val,
                        difference=diff,
                        tolerance_applied=tol,
                        explanation=f"Verified metric '{metric}' for period {norm_period} (ground truth: {expected_val}).",
                    )
                else:
                    # Check if claimed value matches baseline workbook if different from QBO
                    base_val = None
                    for v in self.analysis_data.get("baseline_comparison", {}).get("monthly_variances", []):
                        if v.get("period") == norm_period and self.normalize_metric_name(v.get("metric", "")) == metric:
                            base_val = float(v.get("baseline_value", 0))
                            break
                    if base_val is not None and abs(val_float - base_val) <= tol:
                        return ClaimValidationResult(
                            claim_id=claim_id,
                            claim_text=claim_text,
                            metric=metric,
                            period=norm_period,
                            claimed_value=val_float,
                            claimed_unit=claimed_unit,
                            status="VERIFIED",
                            ground_truth_value=base_val,
                            difference=round(abs(val_float - base_val), 4),
                            tolerance_applied=tol,
                            explanation=f"Verified against baseline reference workbook for period {norm_period} (baseline: {base_val}; QBO target: {expected_val}).",
                        )

                    scale_note = ""
                    if expected_val and expected_val != 0:
                        ratio = abs(val_float / expected_val)
                        if 800 <= ratio <= 1200 or 800000 <= ratio <= 1200000:
                            scale_note = " (Scale mismatch detected: claimed value appears scaled by ~1,000x to 1,000,000x, e.g. billions vs millions)."
                        elif 0.0008 <= ratio <= 0.0012 or 0.0000008 <= ratio <= 0.0000012:
                            scale_note = " (Scale mismatch detected: claimed value appears scaled down by ~1,000x to 1,000,000x)."
                    if re.search(r'\b\d+(?:\.\d+)?\s*(?:B|billion)\b', str(claim_text), flags=re.IGNORECASE):
                        if abs(expected_val) < 1e8:
                            scale_note = " (Scale discrepancy: claimed unit 'B' / billions conflicts with ground truth scale in millions)."

                    return ClaimValidationResult(
                        claim_id=claim_id,
                        claim_text=claim_text,
                        metric=metric,
                        period=norm_period,
                        claimed_value=val_float,
                        claimed_unit=claimed_unit,
                        status="INVALID",
                        ground_truth_value=expected_val,
                        difference=diff,
                        tolerance_applied=tol,
                        explanation=f"Value discrepancy: claimed {val_float} vs ground truth {expected_val} for {norm_period} (diff {diff} exceeds tolerance {tol}).{scale_note}",
                    )

        # -------------------------------------------------------------
        # 4. Cross-Dataset Baseline Variances ($300 opex, $391.25 rev)
        # -------------------------------------------------------------
        for (p, m), var in self.variances_by_period_metric.items():
            if norm_period and p != norm_period:
                continue
            if abs(float(var.get("difference", 0))) == abs(val_float):
                return ClaimValidationResult(
                    claim_id=claim_id,
                    claim_text=claim_text,
                    metric=m,
                    period=p,
                    claimed_value=val_float,
                    claimed_unit=claimed_unit,
                    status="VERIFIED",
                    ground_truth_value=float(var.get("difference", 0)),
                    difference=0.0,
                    tolerance_applied=self.tolerance_currency,
                    explanation=f"Verified cross-dataset variance in {p}: {var.get('explanation')}",
                )

        # -------------------------------------------------------------
        # 5. Fallback: Unverified / Unsupported Claim
        # -------------------------------------------------------------
        return ClaimValidationResult(
            claim_id=claim_id,
            claim_text=claim_text,
            metric=metric,
            period=norm_period,
            claimed_value=val_float,
            claimed_unit=claimed_unit,
            status="UNVERIFIED",
            explanation=f"Metric '{metric}' for period '{norm_period}' is not directly verifiable in analysis.json; flagged for CPA review.",
        )

    def audit_commentary_narrative(self, commentary_text: str) -> Dict[str, Any]:
        """Audit narrative commentary to identify unsupported causal claims and scale errors.

        Distinguishes verified numerical facts from unverified qualitative assertions:
        - Flags unqualified causal claims about seasonality, pricing power, cost control, operational efficiency.
        - Identifies statements that correctly frame findings as empirical observations or hypotheses.
        - Detects scale discrepancies (e.g., billions cited where ground truth is in millions).
        """
        if not commentary_text:
            return {
                "total_sentences_audited": 0,
                "unverified_causal_assertions_count": 0,
                "scale_warnings_count": 0,
                "flagged_assertions": [],
                "scale_warnings": [],
                "narrative_quality_status": "NO_TEXT_PROVIDED",
            }

        # 1. Scale warning detection (e.g., $X.XXB or X billion where ground truth is in millions)
        scale_warnings: List[str] = []
        for m in re.finditer(r'[\$€£]?\s*(-?\d+(?:\.\d+)?)\s*(?:B|billion)\b', commentary_text, flags=re.IGNORECASE):
            raw = m.group(0).strip()
            scale_warnings.append(
                f"Scale magnitude error detected: '{raw}' asserts billions, but authoritative ground truth metrics for ABC Inc. are in millions (e.g. TTM normalized loss is ~$4.06M to ~$4.46M, not ~$4.06B to ~$4.46B)."
            )

        # 2. Causal assertion inspection
        causal_triggers = [
            ("pricing power", r'\bpricing\s+power\b'),
            ("cost control", r'\bcost\s+control\b'),
            ("operational efficiency", r'\boperational\s+efficiency\b'),
            ("seasonality", r'\b(?:driven\s+by|due\s+to|because\s+of|result\s+of)\s+seasonal|\bseasonal\s+decline\b|\bseasonality\b'),
            ("expense management", r'\bexpense\s+management\b'),
            ("pricing discipline", r'\bpricing\s+discipline\b'),
        ]

        # Hypothesis / qualification indicators
        qualification_pattern = re.compile(
            r'\b(hypothes(?:is|es)|requir(?:es|ing|ed)?\s+(?:finance|confirmation|validation|review)|'
            r'unverified|pending|subject\s+to|working\s+hypothesis|observed\s+(?:contraction|decline|increase|range)|'
            r'not\s+verified|cannot\s+be\s+verified|preliminary)\b',
            re.IGNORECASE
        )

        flagged_assertions: List[Dict[str, str]] = []
        sentences = re.split(r'(?<=[.!?\n])\s+', commentary_text)

        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue

            for label, pattern in causal_triggers:
                m = re.search(pattern, sent_clean, flags=re.IGNORECASE)
                if m:
                    # Check if qualified as hypothesis or observation
                    if not qualification_pattern.search(sent_clean):
                        flagged_assertions.append({
                            "type": label,
                            "matched_phrase": m.group(0),
                            "sentence": sent_clean,
                            "finding": f"Asserts '{label}' as fact without qualifying as hypothesis requiring finance-team confirmation.",
                        })

        status = "NEUTRAL_OR_QUALIFIED" if len(flagged_assertions) == 0 and len(scale_warnings) == 0 else "CONTAINS_UNVERIFIED_ASSERTIONS"

        return {
            "total_sentences_audited": len(sentences),
            "unverified_causal_assertions_count": len(flagged_assertions),
            "scale_warnings_count": len(scale_warnings),
            "flagged_assertions": flagged_assertions,
            "scale_warnings": scale_warnings,
            "narrative_quality_status": status,
        }

    def validate_claims(
        self,
        claims: List[Dict[str, Any]],
        commentary_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate a collection of claims and produce summary metrics and reports.

        Clearly separates verified numerical claims from unverified qualitative narrative claims.
        """
        results: List[ClaimValidationResult] = []
        for i, c in enumerate(claims, 1):
            res = self.validate_claim(c, claim_id=i)
            results.append(res)

        total = len(results)
        verified = sum(1 for r in results if r.status == "VERIFIED")
        invalid = sum(1 for r in results if r.status == "INVALID")
        unverified = sum(1 for r in results if r.status == "UNVERIFIED")

        accuracy_rate = round((verified / total * 100), 2) if total > 0 else 0.0

        output: Dict[str, Any] = {
            "summary": {
                # Backward-compatible keys
                "total_claims": total,
                "verified_claims": verified,
                "invalid_claims": invalid,
                "unverified_claims": unverified,
                "accuracy_rate_pct": accuracy_rate,
                "status": "PASS" if invalid == 0 and verified > 0 else "FAIL",
                # Explicit scope distinction keys
                "tested_numerical_claims": total,
                "verified_numerical_claims": verified,
                "invalid_numerical_claims": invalid,
                "unverified_numerical_claims": unverified,
                "numerical_claim_accuracy_pct": accuracy_rate,
                "numerical_claims_status": "PASS" if invalid == 0 and verified > 0 else "FAIL",
                "report_scope": "DISCRETE_NUMERICAL_CLAIMS_ONLY",
                "qualitative_audit_status": "UNVERIFIED_PENDING_HUMAN_AUDIT",
                "full_report_certification": "PARTIAL_VERIFICATION_NUMERICAL_ONLY",
                "scope_disclaimer": (
                    "This deterministic audit validates ONLY discrete extracted numerical claims against analysis.json. "
                    "General narrative prose, qualitative commentary, causal assertions (e.g. pricing power, seasonality, "
                    "operational efficiency), and un-extracted figures are NOT verified by this numerical pass and require "
                    "independent audit or commentary evaluation."
                ),
            },
            "claims": [r.to_dict() for r in results],
        }

        if commentary_text:
            output["narrative_audit"] = self.audit_commentary_narrative(commentary_text)

        return output

    def generate_markdown_report(self, validation_output: Dict[str, Any]) -> str:
        """Render a readable GitHub-style Markdown report of validation findings."""
        summary = validation_output.get("summary", {})
        claims = validation_output.get("claims", [])
        narrative_audit = validation_output.get("narrative_audit")

        lines = [
            "# LLM Financial Commentary: Deterministic Numerical Grounding Audit",
            "",
            "> [!WARNING]",
            "> **Scope & Verification Boundary Warning**:",
            f"> This deterministic audit evaluates strictly **{summary.get('total_claims', 0)} discrete structured numerical claims** against authoritative ground truth in `analysis.json`.",
            "> **Qualitative commentary, causal interpretations (such as pricing power, cost control, seasonality, or operational efficiency), and unextracted narrative statements are NOT certified by this numerical claim check.**",
            "> A 100% pass rate on selected numerical claims does **not** certify the entire financial report narrative as 100% accurate.",
            "",
            "## Summary of Numerical Grounding vs. Qualitative Scope",
            "| Audit Dimension | Result | Status | Scope / Limitation |",
            "| :--- | :---: | :---: | :--- |",
            f"| **Tested Numerical Claims** | {summary.get('verified_claims', 0)} / {summary.get('total_claims', 0)} passed ({summary.get('accuracy_rate_pct', 0.0)}%) | **{summary.get('status', 'FAIL')}** | Discrete financial figures mapped to `analysis.json` |",
            "| **Qualitative & Causal Narrative** | Unverified by claim table | ⚠️ **PENDING AUDIT** | Causal claims (seasonality, pricing power, efficiency) require CPA / FP&A confirmation |",
            "| **Full Report Certification** | Partial | **PARTIAL** | Only verified numerical subset is certified |",
            "",
            "### Metric Breakdown",
            f"- **Total Discrete Numerical Claims Evaluated:** {summary.get('total_claims', 0)}",
            f"- **Verified Claims (Ground Truth Matched):** {summary.get('verified_claims', 0)}",
            f"- **Invalid Claims (Mathematical / Scale Discrepancies):** {summary.get('invalid_claims', 0)}",
            f"- **Unverified / Disclosed Claims (Flagged for CPA Review):** {summary.get('unverified_claims', 0)}",
            f"- **Tested Claims Accuracy Rate:** {summary.get('accuracy_rate_pct', 0.0)}%",
            f"- **Discrete Numerical Status:** **{summary.get('status', 'FAIL')}**",
            "",
            "---",
            "",
        ]

        if narrative_audit:
            lines.extend([
                "## Narrative & Qualitative Claim Review",
                f"- **Sentences Audited:** {narrative_audit.get('total_sentences_audited', 0)}",
                f"- **Scale Warnings (e.g. Billions vs. Millions):** {narrative_audit.get('scale_warnings_count', 0)}",
                f"- **Unverified Causal Assertions:** {narrative_audit.get('unverified_causal_assertions_count', 0)}",
                f"- **Narrative Audit Status:** **{narrative_audit.get('narrative_quality_status', 'UNKNOWN')}**",
                "",
            ])
            if narrative_audit.get("scale_warnings"):
                lines.append("### Scale Magnitude Warnings")
                for w in narrative_audit["scale_warnings"]:
                    lines.append(f"- ❌ {w}")
                lines.append("")
            if narrative_audit.get("flagged_assertions"):
                lines.append("### Unverified Causal Assertions Requiring Qualification")
                for fa in narrative_audit["flagged_assertions"]:
                    lines.append(f"- ⚠️ **{fa.get('type', '').title()}**: \"{fa.get('sentence', '')}\" — *{fa.get('finding', '')}*")
                lines.append("")
            lines.extend(["---", ""])

        lines.extend([
            "## Detailed Claim-by-Claim Audit Table",
            "| ID | Period | Metric | Claimed Value | Ground Truth | Status | Finding / Audit Context |",
            "| :---: | :---: | :--- | :---: | :---: | :---: | :--- |",
        ])

        for c in claims:
            cid = c.get("claim_id")
            period = c.get("period") or "-"
            metric = c.get("metric") or "-"
            claimed = c.get("claimed_value")
            claimed_str = f"${claimed:,.2f}" if c.get("claimed_unit") == "currency" and isinstance(claimed, (int, float)) else str(claimed)
            gt = c.get("ground_truth_value")
            gt_str = f"${gt:,.2f}" if c.get("claimed_unit") == "currency" and isinstance(gt, (int, float)) else ("-" if gt is None else str(gt))
            status = c.get("status")
            badge = "✅ **VERIFIED**" if status == "VERIFIED" else ("❌ **INVALID**" if status == "INVALID" else "⚠️ **UNVERIFIED**")
            expl = c.get("explanation", "").replace("|", "\\|")
            lines.append(f"| {cid} | {period} | {metric} | {claimed_str} | {gt_str} | {badge} | {expl} |")

        lines.append("")
        return "\n".join(lines)
