"""Commentary Evaluation Suite for Financial Trend Analysis.

Evaluates saved or Claude-generated commentary against the ground-truth
financial facts in analysis.json across four dimensions:
1. Numerical Grounding (preventing hallucinated or mismatched figures)
2. Unsupported Causal Claims (enforcing Rule 2: no unverified external causes)
3. Critical Anomaly Profitability Interpretation (rejecting false profitability)
4. Disclosure of Missing Information (mandating CPA review, cash flow caveats, unmapped status)

OPERATIONAL BOUNDARY NOTE:
This evaluation suite runs deterministically offline against saved response
artifacts (e.g. results/report.md or saved Claude outputs). It does NOT invoke
live Claude via an API, preserving a strict distinction between offline evaluation
and live LLM orchestration.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List, Set, Tuple, Optional


class CommentaryEvaluationResult:
    def __init__(self, check_name: str, max_points: float = 25.0):
        self.check_name = check_name
        self.max_points = max_points
        self.score = 0.0
        self.passed = False
        self.violations: List[str] = []
        self.notes: List[str] = []

    def pass_with_score(self, score: float, note: str = ""):
        self.score = min(score, self.max_points)
        self.passed = self.score >= (self.max_points * 0.7)
        if note:
            self.notes.append(note)

    def fail_with_violations(self, violations: List[str], partial_score: float = 0.0):
        self.score = partial_score
        self.passed = False
        self.violations.extend(violations)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "score": round(self.score, 2),
            "max_points": self.max_points,
            "violations": self.violations,
            "notes": self.notes,
        }


class CommentaryEvaluator:
    """Evaluates narrative commentary against structured analysis.json factual data."""

    def __init__(self, analysis_data: Dict[str, Any]):
        self.analysis_data = analysis_data
        self.field_numbers = self._extract_field_numbers(analysis_data)
        self.known_numbers = self._extract_known_financial_numbers(analysis_data)
        self.grounded_causes = self._extract_grounded_causes(analysis_data)
        self.critical_periods = self._extract_critical_periods(analysis_data)
        self.anomaly_profiles = self._build_anomaly_profiles(analysis_data)

    def _extract_field_numbers(self, data: Dict[str, Any]) -> Dict[str, Set[float]]:
        """Extracts field-specific numbers from analysis.json for targeted metric validation."""
        fields: Dict[str, Set[float]] = {
            "margin": set(),
            "revenue": set(),
            "opex": set(),
            "operating_income": set(),
            "tax_credit": set(),
            "stock_comp": set(),
        }
        for s in data.get("monthly_summaries", []):
            if s.get("gross_margin_pct"):
                try:
                    fields["margin"].add(abs(float(s["gross_margin_pct"].replace("%", ""))))
                except ValueError:
                    pass
            if s.get("revenue") is not None:
                try:
                    fields["revenue"].add(abs(float(s["revenue"])))
                except ValueError:
                    pass
            if s.get("total_opex") is not None:
                try:
                    fields["opex"].add(abs(float(s["total_opex"])))
                except ValueError:
                    pass
            if s.get("normalized_core_opex") is not None:
                try:
                    fields["opex"].add(abs(float(s["normalized_core_opex"])))
                except ValueError:
                    pass
            if s.get("operating_income") is not None:
                try:
                    fields["operating_income"].add(abs(float(s["operating_income"])))
                except ValueError:
                    pass
            if s.get("normalized_operating_income") is not None:
                try:
                    fields["operating_income"].add(abs(float(s["normalized_operating_income"])))
                except ValueError:
                    pass

        for w in data.get("ttm_windows", []):
            if w.get("gross_margin_pct"):
                try:
                    fields["margin"].add(abs(float(w["gross_margin_pct"].replace("%", ""))))
                except ValueError:
                    pass
            if w.get("revenue") is not None:
                try:
                    fields["revenue"].add(abs(float(w["revenue"])))
                except ValueError:
                    pass
            if w.get("total_opex") is not None:
                try:
                    fields["opex"].add(abs(float(w["total_opex"])))
                except ValueError:
                    pass
            if w.get("normalized_core_opex") is not None:
                try:
                    fields["opex"].add(abs(float(w["normalized_core_opex"])))
                except ValueError:
                    pass
            if w.get("operating_income") is not None:
                try:
                    fields["operating_income"].add(abs(float(w["operating_income"])))
                except ValueError:
                    pass
            if w.get("normalized_operating_income") is not None:
                try:
                    fields["operating_income"].add(abs(float(w["normalized_operating_income"])))
                except ValueError:
                    pass

        for a in data.get("anomalies_and_flags", []):
            amt = a.get("amount")
            if amt is not None:
                try:
                    val = abs(float(amt))
                    txt = f"{a.get('account', '')} {a.get('description', '')}".lower()
                    if "tax benefit" in txt or "tax credit" in txt:
                        fields["tax_credit"].add(val)
                    elif "stock" in txt:
                        fields["stock_comp"].add(val)
                except ValueError:
                    pass
            # Also extract numbers from description and impact of tax benefit anomalies for normalized loss / tax credit fields
            txt = f"{a.get('account', '')} {a.get('description', '')} {a.get('impact', '')}".lower()
            if "tax benefit" in txt or "tax credit" in txt:
                for fld in ["description", "impact"]:
                    for m in re.finditer(r'[\$€£]?\s*(-?[\d,]+(?:\.\d+)?)\b', a.get(fld, "")):
                        try:
                            v = abs(float(m.group(1).replace(",", "")))
                            if v > 0:
                                fields["tax_credit"].add(v)
                                fields["operating_income"].add(v)
                        except ValueError:
                            pass

        return fields

    def _extract_critical_periods(self, data: Dict[str, Any]) -> List[str]:
        """Extracts date strings and formatted period representations for critical accounting anomalies."""
        critical_anomalies = [
            a for a in data.get("anomalies_and_flags", [])
            if a.get("severity") == "CRITICAL" or a.get("is_critical") is True or "CRITICAL" in a.get("impact", "")
        ]
        periods: List[str] = []
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_full = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

        for a in critical_anomalies:
            p = a.get("period", "")
            if p:
                periods.append(p)
                m = re.match(r'(\d{4})-(\d{2})', p)
                if m:
                    year, month = m.group(1), int(m.group(2))
                    if 1 <= month <= 12:
                        periods.append(f"{month_names[month-1]} {year}")
                        periods.append(f"{month_full[month-1]} {year}")
        return periods

    def _extract_grounded_causes(self, data: Dict[str, Any]) -> Set[str]:
        """Derives verified, ground-truth business and accounting causes from analysis.json."""
        causes: Set[str] = set()
        for a in data.get("anomalies_and_flags", []):
            text = f"{a.get('account', '')} {a.get('description', '')} {a.get('impact', '')}".lower()
            if "tax benefit" in text or "tax credit" in text:
                causes.update(["tax benefit", "tax credit", "income tax benefit", "non-recurring tax benefit"])
            if "stock-based compensation" in text or "sbc" in text:
                causes.update(["stock-based compensation", "stock compensation", "sbc", "non-cash compensation"])
            if "credit memo" in text or "billing correction" in text or "reversal" in text:
                causes.update(["credit memo", "billing correction", "invoice credit memo", "reversal", "negative reversal"])
            if "vendor credit" in text or "accrual true-up" in text:
                causes.update(["vendor credit", "accrual true-up", "expense reversal", "vendor credit or accrual true-up"])
            if "interest expense" in text or "interest income" in text:
                causes.update(["interest expense", "interest income", "reclassification"])
        for v in data.get("baseline_comparison", {}).get("detailed_variances", []):
            ctx = v.get("context", "").lower()
            if "sandbox sample" in ctx or "bill id" in ctx or "invoice id" in ctx:
                causes.update(["sandbox sample", "sample invoice", "sample bill", "pre-existing intuit developer sandbox sample", "developer sandbox sample"])
        return causes

    def _extract_known_financial_numbers(self, data: Dict[str, Any]) -> Set[float]:
        """Extracts all permissible financial figures and metrics from analysis.json."""
        known: Set[float] = set()

        def add_val(v: Any):
            if v is None:
                return
            if isinstance(v, (int, float)):
                known.add(abs(float(v)))
            elif isinstance(v, str):
                cleaned = v.replace("$", "").replace(",", "").replace("%", "").strip()
                try:
                    known.add(abs(float(cleaned)))
                except ValueError:
                    pass

        # Recursively extract structured field values without regex harvesting on prose strings
        def recurse_extract(obj: Any):
            if isinstance(obj, dict):
                for k, val in obj.items():
                    if k in ["explanation", "context", "description", "summary_notes", "impact", "recommended_action", "account", "category"]:
                        continue
                    recurse_extract(val)
            elif isinstance(obj, list):
                for item in obj:
                    recurse_extract(item)
            elif isinstance(obj, (int, float)):
                known.add(abs(float(obj)))
            elif isinstance(obj, str):
                add_val(obj)

        recurse_extract(data)

        # Departmental quarterly averages computed in executive reporting
        # Derived dynamically from the actual first, middle, and last 3 periods in analysis.json
        periods = [s.get("period") for s in data.get("monthly_summaries", []) if s.get("period")]
        if not periods:
            periods = data.get("metadata", {}).get("periods_chronological", [])

        w1_periods = periods[:3] if len(periods) >= 3 else periods
        w3_periods = periods[-3:] if len(periods) >= 3 else periods
        mid = len(periods) // 2
        w2_periods = periods[mid:mid+3] if len(periods) >= 6 else []

        for cat in data.get("category_summaries", []):
            vals_dict = cat.get("values", {})
            for w_periods in [w1_periods, w2_periods, w3_periods]:
                if w_periods:
                    vals = [float(vals_dict.get(p, "0")) for p in w_periods if p in vals_dict]
                    if vals:
                        known.add(abs(round(sum(vals) / len(vals), 2)))

        # Individual line items and min/max/sum ranges
        for li in data.get("line_items", []):
            line_vals: List[float] = []
            for v in li.get("values", {}).values():
                try:
                    flt = abs(float(v))
                    if flt > 0:
                        line_vals.append(flt)
                except (ValueError, TypeError):
                    pass
            if line_vals:
                known.add(min(line_vals))
                known.add(max(line_vals))
                known.add(sum(line_vals))

        # Structural counts derived dynamically from lists in analysis.json
        period_cnt = len(data.get("monthly_summaries", [])) or len(data.get("metadata", {}).get("periods_chronological", []))
        if period_cnt:
            known.add(float(period_cnt))

        anom_cnt = len(data.get("anomalies_and_flags", []))
        known.add(float(anom_cnt))

        rec_cnt = len(data.get("reconciliation_checks", []))
        if rec_cnt:
            known.add(float(rec_cnt))

        bc = data.get("baseline_comparison")
        if bc and isinstance(bc, dict):
            var_cnt = bc.get("total_variances_found", len(bc.get("monthly_variances", [])))
            known.add(float(var_cnt))
            zero_drift = bc.get("periods_with_zero_drift")
            if zero_drift is not None:
                known.add(float(zero_drift))
            comp_cnt = bc.get("periods_compared")
            if comp_cnt is not None:
                known.add(float(comp_cnt))

        ttm_cnt = len([w for w in data.get("ttm_windows", []) if w.get("is_valid", True)])
        if ttm_cnt:
            known.add(float(ttm_cnt))

        # Alternate normalized loss and dynamic figures computed inside anomalies:
        # Allowed strictly from anomalies_and_flags description/impact fields (not arbitrary prose)
        for a in data.get("anomalies_and_flags", []):
            for fld in ["description", "impact"]:
                text_val = a.get(fld, "")
                for m in re.finditer(r'[\$€£]?\s*(-?[\d,]+(?:\.\d+)?)\b', text_val):
                    try:
                        v = abs(float(m.group(1).replace(",", "")))
                        if v > 0:
                            known.add(v)
                    except ValueError:
                        pass

        # Basic natural numeric constants
        known.update([0.0, 1.0, 100.0])

        # Add exact deterministic reconciliation adjustments and differences
        for s in data.get("monthly_summaries", []):
            if s.get("operating_income") and s.get("normalized_operating_income"):
                try:
                    known.add(abs(round(float(s["operating_income"]) - float(s["normalized_operating_income"]), 2)))
                except (ValueError, TypeError):
                    pass
            if s.get("total_opex") and s.get("normalized_core_opex"):
                try:
                    known.add(abs(round(float(s["total_opex"]) - float(s["normalized_core_opex"]), 2)))
                except (ValueError, TypeError):
                    pass

        valid_ttms = [w for w in data.get("ttm_windows", []) if w.get("is_valid", True)]
        if len(valid_ttms) >= 2:
            first_w, last_w = valid_ttms[0], valid_ttms[-1]
            for m_key in ["revenue", "gross_profit", "total_opex", "operating_income", "normalized_operating_income", "normalized_core_opex"]:
                try:
                    diff_ttm = abs(round(float(last_w.get(m_key, 0)) - float(first_w.get(m_key, 0)), 2))
                    known.add(diff_ttm)
                except (ValueError, TypeError):
                    pass

        return known

    def _detect_preceding_field(self, preceding_text: str) -> Optional[str]:
        """Detects whether a cited number immediately follows a specific financial field label."""
        cleaned = preceding_text.strip().lower()
        if re.search(r'(?:gross\s+)?margin(?:\s+of)?[:\s*]*$', cleaned):
            return "margin"
        if re.search(r'revenue(?:\s+trajectory)?[:\s*]*$|revenue(?:\s+was|\s+reached|\s+of|to)?[:\s*]*$', cleaned):
            return "revenue"
        if re.search(r'tax\s+(?:benefit|credit)(?:\s+credit)?(?:\s+of)?[:\s*]*$', cleaned):
            return "tax_credit"
        if re.search(r'stock-based\s+compensation(?:\s+expense)?(?:\s+of)?[:\s*]*$', cleaned):
            return "stock_comp"
        if re.search(r'(?:total\s+)?(?:operating\s+expenses?|opex)(?:\s+of|to)?[:\s*]*$', cleaned):
            return "opex"
        if re.search(r'operating\s+(?:loss|income|profit)(?:\s+of)?[:\s*]*$', cleaned):
            return "operating_income"
        return None

    def _parse_text_numbers(self, text: str) -> List[Tuple[str, float, float, Optional[str]]]:
        """Finds monetary figures, percentages, and quantities with precision-based rounding tolerances."""
        findings: List[Tuple[str, float, float, Optional[str]]] = []

        currency_pattern = re.compile(
            r'[\$€£]\s*(-?[\d,]+(?:\.\d+)?)\s*([kKmMbB](?![a-zA-Z]))?|'
            r'(-?[\$€£]\s*[\d,]+(?:\.\d+)?)\s*([kKmMbB](?![a-zA-Z]))?|'
            r'\(\s*[\$€£]\s*([\d,]+(?:\.\d+)?)\s*\)\s*([kKmMbB](?![a-zA-Z]))?'
        )
        pct_pattern = re.compile(r'(-?[\d,]+(?:\.\d+)?)\s*%')

        matches = []
        for m in currency_pattern.finditer(text):
            matches.append((m.start(), m.end(), "currency", m))
        for m in pct_pattern.finditer(text):
            matches.append((m.start(), m.end(), "percentage", m))

        matches.sort(key=lambda x: x[0])

        for start, end, mtype, m in matches:
            preceding = text[max(0, start - 60):start]
            field = self._detect_preceding_field(preceding)

            if mtype == "currency":
                raw = m.group(0).strip()
                num_str = m.group(1) or m.group(3) or m.group(5)
                multiplier_str = m.group(2) or m.group(4) or m.group(6)
                if not num_str:
                    continue
                cleaned = num_str.replace("$", "").replace(",", "").replace("€", "").replace("£", "").strip()
                try:
                    val = float(cleaned)
                    decs = len(cleaned.split(".")[1]) if "." in cleaned else 0
                    if multiplier_str:
                        mult = multiplier_str.lower()
                        mult_val = 1e6 if mult == 'm' else (1e3 if mult == 'k' else 1e9)
                        val *= mult_val
                        tol = 0.55 * (10 ** -decs) * mult_val
                    else:
                        if decs >= 2:
                            tol = 0.02
                        elif decs == 1:
                            tol = 0.06
                        else:
                            tol = 0.55
                    findings.append((raw, abs(val), tol, field))
                except ValueError:
                    pass
            elif mtype == "percentage":
                raw = m.group(0).strip()
                try:
                    val = float(m.group(1).replace(",", ""))
                    decs = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
                    if decs >= 2:
                        tol = 0.015
                    elif decs == 1:
                        tol = 0.06
                    else:
                        tol = 0.55
                    pct_field = "margin" if "margin" in preceding.lower() else field
                    findings.append((raw, abs(val), tol, pct_field))
                except ValueError:
                    pass

        return findings

    def check_numerical_grounding(self, text: str) -> CommentaryEvaluationResult:
        """Verifies that every cited number is grounded in analysis.json."""
        res = CommentaryEvaluationResult("Numerical Grounding", max_points=25.0)
        extracted = self._parse_text_numbers(text)

        if not extracted:
            res.fail_with_violations(["Commentary contains zero numerical grounding (no numbers cited)."])
            return res

        ungrounded: List[str] = []
        for raw, val, tol, field in extracted:
            matched = False
            # Check field-specific numbers if field context is identified
            if field and field in self.field_numbers and self.field_numbers[field]:
                for k in self.field_numbers[field]:
                    if abs(val - k) <= tol:
                        matched = True
                        break
            else:
                for k in self.known_numbers:
                    if abs(val - k) <= tol:
                        matched = True
                        break

            if not matched:
                field_info = f" (expected field: {field})" if field else ""
                ungrounded.append(f"{raw} (value: {val:.2f}{field_info})")

        if ungrounded:
            unique_ungrounded = list(dict.fromkeys(ungrounded))
            res.fail_with_violations(
                [f"Ungrounded figure cited in commentary: {u}" for u in unique_ungrounded[:5]],
                partial_score=max(0.0, 25.0 - (len(unique_ungrounded) * 5.0))
            )
        else:
            res.pass_with_score(25.0, f"All {len(extracted)} cited numbers successfully grounded in analysis.json.")

        return res

    def _build_anomaly_profiles(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts structured profiles for verified anomalies to validate causal consistency."""
        profiles = []
        month_names = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        month_full = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

        for a in data.get("anomalies_and_flags", []):
            account = a.get("account", "").lower()
            desc = a.get("description", "").lower()
            period = a.get("period", "").lower()
            cat = a.get("category", "").lower()

            valid_periods = set()
            if period and period != "all":
                valid_periods.add(period)
                m = re.match(r'(\d{4})-(\d{2})', period)
                if m:
                    year, mo = m.group(1), int(m.group(2))
                    if 1 <= mo <= 12:
                        valid_periods.add(f"{month_names[mo-1]} {year}")
                        valid_periods.add(f"{month_full[mo-1]} {year}")
                        valid_periods.add(f"q{(mo-1)//3 + 1} {year}")

            cause_terms = set()
            if "tax benefit" in account or "tax benefit" in desc or "tax credit" in desc:
                cause_terms.update(["tax benefit", "tax credit", "income tax benefit", "tax benefit credit", "one-off tax credit"])
                forbidden_metrics = {"revenue", "sales", "cogs", "cost of goods"}
            elif "stock-based compensation" in account or "stock" in account or "stock" in desc:
                cause_terms.update(["stock-based compensation", "stock compensation", "sbc", "non-cash compensation"])
                forbidden_metrics = {"revenue", "sales", "cogs", "cost of goods"}
            elif "interest" in account:
                cause_terms.update(["interest expense", "interest income", "reclassification"])
                forbidden_metrics = set()
            elif "reversal" in desc or "credit entry" in desc or "reversal" in account:
                cause_terms.update(["credit memo", "billing correction", "reversal", "vendor credit", "accrual true-up", "expense reversal", "negative reversal"])
                if "revenue" in cat or "revenue" in desc:
                    forbidden_metrics = {"opex", "operating expense", "operating expenses"}
                elif "cogs" in cat or "cogs" in desc:
                    forbidden_metrics = {"revenue", "sales"}
                else:
                    forbidden_metrics = {"revenue", "sales"}
            else:
                cause_terms.add(account)
                forbidden_metrics = set()

            profiles.append({
                "account": account,
                "period": period,
                "valid_periods": valid_periods,
                "cause_terms": cause_terms,
                "forbidden_metrics": forbidden_metrics,
            })

        for v in data.get("baseline_comparison", {}).get("detailed_variances", []):
            period = v.get("period", "").lower()
            valid_periods = set()
            if period:
                valid_periods.add(period)
                m = re.match(r'(\d{4})-(\d{2})', period)
                if m:
                    year, mo = m.group(1), int(m.group(2))
                    if 1 <= mo <= 12:
                        valid_periods.add(f"{month_names[mo-1]} {year}")
                        valid_periods.add(f"{month_full[mo-1]} {year}")
            profiles.append({
                "account": "sandbox sample variance",
                "period": period,
                "valid_periods": valid_periods,
                "cause_terms": {"sandbox sample", "sample invoice", "sample bill", "developer sandbox sample", "pre-existing intuit developer sandbox sample"},
                "forbidden_metrics": set(),
            })

        return profiles

    def _extract_mentioned_periods(self, sent_lower: str) -> Set[str]:
        """Identifies calendar periods or explicit unrelated-period markers within a sentence."""
        if re.search(r'\b(?:unrelated|different|another)\s+(?:month|period|quarter|year)\b', sent_lower):
            return {"__unrelated_period__"}
        periods = set()
        for m in re.finditer(r'\b\d{4}-\d{2}\b', sent_lower):
            periods.add(m.group(0))
        months_pat = r'\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}\b'
        for m in re.finditer(months_pat, sent_lower):
            periods.add(m.group(0))
        for m in re.finditer(r'\bq[1-4]\s+\d{4}\b', sent_lower):
            periods.add(m.group(0))
        return periods

    def check_unsupported_causal_claims(self, text: str) -> CommentaryEvaluationResult:
        """Detects whether commentary asserts external business causes as facts without qualification."""
        res = CommentaryEvaluationResult("Unsupported Causal Claims", max_points=25.0)

        # 1. Existing blacklist of prohibited operational assertions
        hallucinated_causes = [
            r'\b(?:due to|because of|caused by|result of)\s+(?:customer|client)\s+churn\b',
            r'\b(?:due to|because of|caused by|result of)\s+(?:pricing|contract)\s+renegotiation\b',
            r'\b(?:due to|because of|caused by|result of)\s+(?:supply chain|vendor)\s+disruption\b',
            r'\b(?:due to|because of|caused by|result of)\s+(?:aggressive|massive)\s+hiring\b',
            r'\b(?:due to|because of|caused by|result of)\s+(?:loss of|won)\s+major\s+contract\b',
            r'\bpricing\s+dispute\b',
            r'\blost\s+key\s+customers?\b',
            r'\bmacroeconomic\s+headwinds?\b',
            r'\b(?:normalized|monthly|average[d]?|estimated|core|operational)?\s*cash\s+burn\s+(?:has\s+averaged|was|is|averaged|reached|equals?|totals?)\s+[\$€£]?\d',
            r'\b(?:normalized|monthly|average[d]?)\s+cash\s+burn\s+(?:has\s+averaged|was|is|averaged)\b',
            r'\bburns\s+[\$€£]?\d[\d,.]*(?:\s*[kmb]\b)?(?:\s+in\s+cash|\s+every\s+month|\s+per\s+month|\s+monthly)?\b',
            r'\b(?:operating\s+loss(?:es)?|opex|operational\s+loss(?:es)?)\s+(?:proves?|shows?|equates?\s+to|means?|indicates?)\s+(?:a\s+)?cash\s+burn\b',
            r'\b(?:proves?|equates?\s+to)\s+(?:a\s+)?cash\s+burn\b',
            r'\bcash\s+burn\s+of\s+[\$€£]?\d',
            r'\bcash\s+consumption\s+(?:is|was|reached|averaged|totals?|equals?|of)\s+[\$€£]?\d',
        ]

        violations: List[str] = []
        for pattern in hallucinated_causes:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                violations.append(f"Commentary asserts unverified operational cause as fact: '{matches[0]}'")

        # 2. General causal language detection checked against consistent ground-truth anomalies in analysis.json
        causal_pattern = re.compile(
            r'\b(because(?:\s+of)?|due\s+to|driven\s+by|as\s+a\s+result\s+of|caused\s+by|attributed\s+to|owing\s+to)\b',
            re.IGNORECASE
        )
        sentences = re.split(r'(?<=[.!?\n])\s+', text)
        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue
            m = causal_pattern.search(sent_clean)
            if m:
                sent_lower = sent_clean.lower()
                mentioned_periods = self._extract_mentioned_periods(sent_lower)

                matching_consistent = False
                found_candidate_cause = False

                for prof in self.anomaly_profiles:
                    matched_cause = [c for c in prof["cause_terms"] if c in sent_lower]
                    if not matched_cause:
                        continue
                    found_candidate_cause = True

                    # Check forbidden metrics
                    if any(re.search(rf'\b{re.escape(fm)}\b', sent_lower) for fm in prof["forbidden_metrics"]):
                        continue

                    # Check period consistency
                    if mentioned_periods:
                        if prof["period"] == "all":
                            pass
                        elif "__unrelated_period__" in mentioned_periods:
                            continue
                        else:
                            period_matched = False
                            for mp in mentioned_periods:
                                for vp in prof["valid_periods"]:
                                    if mp in vp or vp in mp:
                                        period_matched = True
                                        break
                                if period_matched:
                                    break
                            if not period_matched:
                                continue

                    matching_consistent = True
                    break

                if not found_candidate_cause:
                    violations.append(
                        f"Commentary asserts unsupported causal claim: '{sent_clean}' (causal language '{m.group(0)}' without ground-truth cause in analysis.json)"
                    )
                elif not matching_consistent:
                    violations.append(
                        f"Commentary asserts inconsistent/fake causal claim: '{sent_clean}' (cause is inconsistent with anomaly metric or period in analysis.json)"
                    )

        if violations:
            res.fail_with_violations(violations, partial_score=0.0)
        else:
            res.pass_with_score(25.0, "Zero unsupported or hallucinated causal claims detected.")

        return res

    def check_critical_anomaly_profitability(self, text: str) -> CommentaryEvaluationResult:
        """Verifies that commentary explicitly rejects genuine operational profitability in critical anomaly periods."""
        res = CommentaryEvaluationResult("Critical Anomaly Profitability Interpretation", max_points=25.0)

        # Build dynamic patterns for critical anomaly periods
        period_patterns = [r'critical accounting-anomaly period', r'anomaly period']
        for p in self.critical_periods:
            period_patterns.append(re.escape(p))
            parts = p.split()
            if len(parts) >= 2:
                period_patterns.append(rf'{re.escape(parts[0][:3])}(?:[a-z]+)?\s+{re.escape(parts[-1])}')

        combined_periods = '|'.join(period_patterns) if period_patterns else r'anomaly period'

        false_profit_patterns = [
            rf'\b(?:{combined_periods})\s+(?:achieved|demonstrated|delivered|proved|was)\s+(?:a\s+)?(?:genuine|sustainable|true|strong|operational|operationally)\s+profitab\w*',
            rf'\b(?:turned|became)\s+(?:genuinely\s+)?(?:operationally\s+)?profitable\s+(?:in|during)\s+(?:the\s+)?(?:{combined_periods})\b',
            rf'\b(?:{combined_periods})\s+profitability\s+reflects\s+core\s+business\b',
            rf'\bbusiness\s+became\s+(?:genuinely\s+)?(?:operationally\s+)?profitable\s+(?:in|during)\s+(?:the\s+)?(?:{combined_periods})\b',
            rf'\bbecame\s+(?:genuinely\s+)?operationally\s+profitable\s+in\s+the\s+critical\s+accounting-anomaly\s+period\b',
        ]

        for p in false_profit_patterns:
            if re.search(p, text, flags=re.IGNORECASE):
                period_display = next((cp for cp in self.critical_periods if any(m in cp for m in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])), None)
                if not period_display:
                    period_display = self.critical_periods[0] if self.critical_periods else "the anomaly period"
                res.fail_with_violations([
                    f"CRITICAL ERROR: Commentary falsely claims {period_display} achieved genuine operational profitability."
                ])
                return res

        has_critical_tax_anomaly = any(
            a.get("severity") == "CRITICAL" and "tax" in a.get("account", "").lower()
            for a in self.analysis_data.get("anomalies_and_flags", [])
        )

        if not has_critical_tax_anomaly:
            res.pass_with_score(25.0, "No critical tax benefit anomaly present in dataset; standard operational profitability interpretation verified.")
            return res

        # Check for proper rejection of genuine profitability / tax credit identification
        tax_credit_identified = bool(re.search(r'tax\s+benefit|tax\s+credit', text, flags=re.IGNORECASE))
        profitability_rejected = bool(re.search(
            r'did\s+not\s+become\s+genuinely|not\s+genuinely|artificial|illusory|one-off|normalized\s+(?:core\s+)?operating\s+loss',
            text, flags=re.IGNORECASE
        ))

        if tax_credit_identified and profitability_rejected:
            res.pass_with_score(25.0, "Correctly identifies critical non-operating tax credit and rejects genuine profitability.")
        elif tax_credit_identified:
            res.pass_with_score(15.0, "Identifies tax credit but does not explicitly reject profitability in strong terms.")
        else:
            res.fail_with_violations([
                "Commentary failed to identify the critical tax benefit anomaly or normalize operating loss."
            ])

        return res

    def check_missing_information_disclosures(self, text: str) -> CommentaryEvaluationResult:
        """Verifies disclosure of missing statements, CPA audit requirements, unmapped status, and dataset integrity."""
        res = CommentaryEvaluationResult("Disclosure of Missing Information", max_points=25.0)
        violations: List[str] = []
        notes: List[str] = []
        score = 0.0

        expected_anom_cnt = len(self.analysis_data.get("anomalies_and_flags", []))
        expected_var_cnt = self.analysis_data.get("baseline_comparison", {}).get("total_variances_found", 0)

        # 1. Anomaly Count & Section Verification
        explicit_anom_matches = re.findall(
            r'(?:total\s+)?(?:audit\s+flags|anomalies|findings|accounting\s+anomalies)(?:\s+identified)?[:\s]+(\d+)|'
            r'(\d+)\s+(?:audit\s+flags|accounting\s+anomalies|anomalies|anomalous\s+items)\b',
            text,
            re.IGNORECASE
        )
        explicit_mismatch = False
        for m in explicit_anom_matches:
            cnt_str = m[0] or m[1]
            if cnt_str and int(cnt_str) != expected_anom_cnt:
                violations.append(
                    f"Incorrect anomaly count stated in commentary: stated {cnt_str}, expected {expected_anom_cnt} from analysis.json."
                )
                explicit_mismatch = True
                break

        sec2_match = re.search(r'## 2\. Critical Accounting Anomalies.*?(?=## 3\.|\Z)', text, re.DOTALL | re.IGNORECASE)
        sec2_items_cnt = 0
        if sec2_match:
            sec2_text = sec2_match.group(0)
            sec2_items = re.findall(r'-\s+\*\*\[.*?\]', sec2_text)
            sec2_items_cnt = len(sec2_items)

        if explicit_mismatch:
            pass
        elif sec2_items_cnt == expected_anom_cnt or (explicit_anom_matches and not explicit_mismatch):
            score += 5.0
            notes.append(f"Correct anomaly count verified ({expected_anom_cnt} items matching analysis.json).")
        else:
            violations.append(
                f"Anomaly count mismatch or missing anomaly disclosures: found {sec2_items_cnt} items, expected {expected_anom_cnt}."
            )

        # 2. QuickBooks vs Excel Baseline Comparison Disclosure
        has_baseline = "baseline_comparison" in self.analysis_data and self.analysis_data["baseline_comparison"] is not None
        if has_baseline:
            has_baseline_section = bool(re.search(
                r'## 8\. Cross-Dataset Baseline Comparison|baseline\s+comparison|quickbooks-?vs-?excel',
                text,
                re.IGNORECASE
            ))
            var_cnt_matches = re.findall(
                r'(?:total\s+variance\s+items?\s+identified|total\s+variances?)[*:\s]+(\d+)|'
                r'(\d+)\s+variance\s+item\(?s\)?',
                text,
                re.IGNORECASE
            )
            extracted_var_counts = [int(m[0] or m[1]) for m in var_cnt_matches if (m[0] or m[1])]
            var_cnt_correct = (expected_var_cnt in extracted_var_counts)

            if has_baseline_section and var_cnt_correct:
                score += 5.0
                notes.append(f"Disclosed QuickBooks vs Excel baseline comparison with correct variance count ({expected_var_cnt}).")
            elif not has_baseline_section:
                violations.append("Missing disclosure: QuickBooks-vs-Excel cross-dataset differences (baseline comparison) not disclosed.")
            else:
                violations.append(
                    f"Baseline comparison disclosure error: stated variance count does not match expected {expected_var_cnt} from analysis.json."
                )
        else:
            score += 5.0
            notes.append("Single-dataset analysis: no external cross-dataset baseline comparison required.")

        # 3. Data Limitations (Cash flow vs. Operating loss / Balance sheet omission)
        has_data_limitations = bool(re.search(
            r'(?:cash\s+flow\s+vs\.?\s+operating\s+loss|data\s+limitations?).*?(?:does\s+not\s+support\s+a\s+cash-?burn|balance\s+sheet.*?omitted|cash\s+flow\s+statements?.*?omitted)',
            text,
            re.IGNORECASE | re.DOTALL
        )) or bool(re.search(
            r'does\s+not\s+support\s+a\s+cash-?burn\s+calculation',
            text,
            re.IGNORECASE
        ))

        if has_data_limitations:
            score += 5.0
            notes.append("Disclosed data limitations (balance sheet/cash flow omitted, cash-burn calculation unsupported).")
        else:
            violations.append("Missing disclosure: Lacks explicit data limitations disclosure regarding omitted balance sheet/cash flow and unsupported cash burn calculation.")

        # 4. Tax credit requires CPA verification / tax return review
        has_tax_credit = any(
            "tax" in a.get("account", "").lower() or "tax" in a.get("description", "").lower()
            for a in self.analysis_data.get("anomalies_and_flags", [])
        )
        if has_tax_credit:
            if re.search(r'cpa|tax\s+(?:cpa|return|provision|schedule)|reclassify.*tax', text, flags=re.IGNORECASE):
                score += 4.0
                notes.append("Disclosed requirement for tax CPA review / tax return reconciliation.")
            else:
                violations.append("Missing disclosure: Tax credit requires tax CPA review or tax return reconciliation.")
        else:
            score += 4.0
            notes.append("No tax credit anomaly in dataset; tax CPA review disclosure not applicable.")

        # 5. Credit memo / reversal documentation review
        has_reversals = any(
            a.get("category") == "Reversal" or "reversal" in a.get("description", "").lower()
            for a in self.analysis_data.get("anomalies_and_flags", [])
        )
        if has_reversals:
            if re.search(r'credit\s+memo|reversal|audit\s+supporting|supporting\s+schedules|vendor\s+credit', text, flags=re.IGNORECASE):
                score += 3.0
                notes.append("Disclosed requirement to audit supporting credit memos for negative reversals.")
            else:
                violations.append("Missing disclosure: Negative reversals require credit memo audit.")
        else:
            score += 3.0
            notes.append("No negative line-item reversals in dataset; credit memo audit disclosure not applicable.")

        # 6. Unmapped accounts disclosure
        if re.search(r'unmapped\s+accounts?.*?(?:none|none\s+identified|\d+)', text, flags=re.IGNORECASE):
            score += 3.0
            notes.append("Explicit unmapped accounts status disclosed.")
        else:
            violations.append("Missing disclosure: Unmapped accounts status not explicitly declared.")

        if violations:
            res.fail_with_violations(violations, partial_score=score)
        else:
            res.pass_with_score(score, "All required disclosures verified.")

        return res

    def evaluate(self, commentary_text: str) -> Dict[str, Any]:
        """Runs all 4 checks and compiles complete evaluation score."""
        c1 = self.check_numerical_grounding(commentary_text)
        c2 = self.check_unsupported_causal_claims(commentary_text)
        c3 = self.check_critical_anomaly_profitability(commentary_text)
        c4 = self.check_missing_information_disclosures(commentary_text)

        checks = [c1, c2, c3, c4]
        total_score = sum(c.score for c in checks)
        all_passed = all(c.passed for c in checks)

        checks_dict = {c.check_name: c.to_dict() for c in checks}

        return {
            "evaluation_mode": "SAVED_RESPONSE_OFFLINE",
            "total_score": round(total_score, 2),
            "max_score": 100.0,
            "passed": all_passed,
            "checks": checks_dict,
            "summary": "PASSED" if all_passed else "FAILED",
        }


def evaluate_commentary_file(report_path: Path, analysis_path: Path) -> Dict[str, Any]:
    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis_data = json.load(f)
    with open(report_path, "r", encoding="utf-8") as f:
        commentary_text = f.read()

    evaluator = CommentaryEvaluator(analysis_data)
    return evaluator.evaluate(commentary_text)


def main(argv=None) -> int:
    base_dir = Path(__file__).resolve().parent.parent
    default_report = base_dir / "results" / "report.md"
    default_analysis = base_dir / "results" / "analysis.json"

    parser = argparse.ArgumentParser(
        description="Commentary Evaluation Suite (Offline Grounding & Quality Harness)"
    )
    parser.add_argument(
        "--report",
        default=str(default_report),
        help=f"Path to report markdown file (default: {default_report}).",
    )
    parser.add_argument(
        "--analysis",
        default=str(default_analysis),
        help=f"Path to analysis JSON file (default: {default_analysis}).",
    )
    args = parser.parse_args(argv)

    report_file = Path(args.report)
    if not report_file.is_absolute():
        if not report_file.exists() and (base_dir / args.report).exists():
            report_file = (base_dir / args.report).resolve()
        else:
            report_file = (Path.cwd() / report_file).resolve()
    else:
        report_file = report_file.resolve()

    analysis_file = Path(args.analysis)
    if not analysis_file.is_absolute():
        if not analysis_file.exists() and (base_dir / args.analysis).exists():
            analysis_file = (base_dir / args.analysis).resolve()
        else:
            analysis_file = (Path.cwd() / analysis_file).resolve()
    else:
        analysis_file = analysis_file.resolve()

    if not report_file.exists() or not analysis_file.exists():
        missing = []
        if not report_file.exists():
            missing.append(f"Report file ({report_file})")
        if not analysis_file.exists():
            missing.append(f"Analysis file ({analysis_file})")
        print(f"Error: Missing input file(s): {', '.join(missing)}. Ensure inputs exist.", file=sys.stderr)
        return 1

    print("=" * 65)
    print("Commentary Evaluation Suite (Offline Grounding & Quality Harness)")
    print("=" * 65)
    result = evaluate_commentary_file(report_file, analysis_file)
    print(f"Total Score: {result['total_score']} / {result['max_score']} [{result['summary']}]")
    print("-" * 65)
    for name, c in result["checks"].items():
        status = "PASS" if c["passed"] else "FAIL"
        print(f"[{status}] {name:40s} | Score: {c['score']:4.1f} / {c['max_points']:4.1f}")
        for v in c["violations"]:
            print(f"       Violation: {v}")
    print("=" * 65)

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
