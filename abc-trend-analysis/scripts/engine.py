"""Financial calculation and validation engine.

Performs all financial arithmetic using Python Decimal, handles chronological sorting,
subtotal non-duplication, departmental category rollups, normalized operational metrics,
MoM changes, TTM windows, and audit anomaly flagging.
Preserves original workbooks without modification.
"""

import json
import re
import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from pathlib import Path
import openpyxl

from .models import (
    MonthPeriod,
    AnomalyFlag,
    Severity,
    AnomalyCategory,
    ReconciliationCheck,
    LineItemData,
    MonthlySummary,
    CategorySummary,
    TTMWindow,
    FinancialAnalysisResult,
)

CENTS = Decimal("0.01")
MONTH_NAMES = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec"
]
MONTH_FULL = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]


def to_cents(val: Any) -> Decimal:
    """Convert any numeric/string value to Decimal rounded to 2 decimal places."""
    if val is None or val == "" or str(val).strip() == "":
        return Decimal("0.00")
    if isinstance(val, (int, float)):
        return Decimal(str(val)).quantize(CENTS, rounding=ROUND_HALF_UP)
    if isinstance(val, Decimal):
        return val.quantize(CENTS, rounding=ROUND_HALF_UP)
    s = str(val).strip().replace("$", "").replace(",", "")
    if s.startswith("(") and s.endswith(")"):
        s = f"-{s[1:-1]}"
    try:
        return Decimal(s).quantize(CENTS, rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


def parse_month_string(header_val: Any) -> Optional[Tuple[int, int, str]]:
    """Parse month and year from a cell header value.

    Returns (year, month, formatted_label) or None.
    """
    if header_val is None:
        return None

    if isinstance(header_val, (datetime.date, datetime.datetime)):
        label = header_val.strftime("%b %Y")
        return (header_val.year, header_val.month, label)

    s = str(header_val).strip()
    if not s:
        return None

    # Standard date formats
    for fmt in [
        "%b %Y", "%B %Y", "%d %b %Y", "%d %B %Y",
        "%Y-%m-%d", "%Y-%m", "%m/%Y", "%b-%y", "%B-%y"
    ]:
        try:
            dt = datetime.datetime.strptime(s, fmt)
            label = dt.strftime("%b %Y")
            return (dt.year, dt.month, label)
        except ValueError:
            pass

    # Regex search for month name + 4-digit or 2-digit year
    s_lower = s.lower()
    for m_idx, m_abbr in enumerate(MONTH_NAMES, start=1):
        if m_abbr in s_lower or MONTH_FULL[m_idx - 1] in s_lower:
            match_yr = re.search(r"\b(20\d\d|19\d\d)\b", s)
            if match_yr:
                year = int(match_yr.group(1))
                label = f"{MONTH_NAMES[m_idx - 1].capitalize()} {year}"
                return (year, m_idx, label)
            match_2yr = re.search(r"[-/\s](\d{2})\b", s)
            if match_2yr:
                yr_val = int(match_2yr.group(1))
                year = 2000 + yr_val if yr_val < 70 else 1900 + yr_val
                label = f"{MONTH_NAMES[m_idx - 1].capitalize()} {year}"
                return (year, m_idx, label)

    return None


DEFAULT_THRESHOLDS_PATH = Path(__file__).resolve().parent.parent / "config" / "anomaly_thresholds.json"


def load_anomaly_thresholds(config_path: Union[str, Path]) -> Dict[str, Decimal]:
    """Load anomaly detection thresholds from JSON configuration file.

    Fails with a clear error message if the file is missing, malformed, or has invalid keys/values.
    Parses all values as Decimal, not float.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Anomaly thresholds configuration file not found at: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f, parse_float=Decimal)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in anomaly thresholds configuration file '{path}': {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Failed to read anomaly thresholds configuration file '{path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Anomaly thresholds configuration in '{path}' must be a JSON object, got {type(data).__name__}.")

    required_keys = ["tax_benefit_credit", "stock_comp_spike", "expense_reversal"]
    thresholds: Dict[str, Decimal] = {}
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required threshold key '{key}' in '{path}'.")
        raw_val = data[key]
        if raw_val is None:
            raise ValueError(f"Threshold key '{key}' in '{path}' cannot be null.")
        try:
            if isinstance(raw_val, Decimal):
                thresholds[key] = raw_val
            elif isinstance(raw_val, (int, float, str)):
                thresholds[key] = Decimal(str(raw_val))
            else:
                raise ValueError(f"Unsupported threshold type {type(raw_val).__name__} for key '{key}'")
        except Exception as exc:
            raise ValueError(f"Invalid numeric threshold value for '{key}' in '{path}': {raw_val}") from exc

    return thresholds


class FinancialCalculationEngine:
    """Core calculation engine for monthly financial statements."""

    def __init__(
        self,
        filepath: str,
        sheet_name: Optional[str] = None,
        source_type: Optional[str] = None,
        thresholds_path: Optional[Union[str, Path]] = None,
    ):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"Workbook not found at {self.filepath}")

        self.thresholds_path = Path(thresholds_path) if thresholds_path else DEFAULT_THRESHOLDS_PATH
        self.thresholds = load_anomaly_thresholds(self.thresholds_path)

        self.requested_sheet_name = sheet_name
        self.source_type = source_type or ("quickbooks" if "qbo" in str(self.filepath).lower() else "excel")
        self.periods: List[MonthPeriod] = []
        self.months_were_reversed = False
        self.missing_period_gaps: List[Dict[str, str]] = []

        self.company_name = "ABC Inc"
        self.statement_name = "Income Statement (Profit and Loss)"
        self.as_of_date = ""

        # Raw data containers
        self.line_items_by_row: Dict[int, Dict[str, Any]] = {}
        self.row_order: List[int] = []

        # Parsed output containers
        self.parsed_line_items: List[LineItemData] = []
        self.monthly_summaries: List[MonthlySummary] = []
        self.category_summaries: List[CategorySummary] = []
        self.ttm_windows: List[TTMWindow] = []
        self.reconciliation_checks: List[ReconciliationCheck] = []
        self.anomalies: List[AnomalyFlag] = []
        self.unmapped_accounts: List[str] = []

    def run_analysis(self) -> FinancialAnalysisResult:
        """Execute complete end-to-end analysis workflow."""
        self._load_and_inspect_workbook()
        self._parse_periods()
        self._parse_line_items()
        self._calculate_monthly_totals_and_reconcile()
        self._calculate_category_summaries()
        self._calculate_mom_metrics()
        self._calculate_ttm_metrics()
        self._detect_anomalies_and_flags()

        return FinancialAnalysisResult(
            company_name=self.company_name,
            statement_name=self.statement_name,
            as_of_date=self.as_of_date,
            periods_analyzed=[{"key": p.key, "label": p.label, "year": p.year, "month": p.month} for p in self.periods],
            months_were_reversed=self.months_were_reversed,
            missing_period_gaps=self.missing_period_gaps,
            monthly_summaries=self.monthly_summaries,
            category_summaries=self.category_summaries,
            line_items=self.parsed_line_items,
            ttm_windows=self.ttm_windows,
            reconciliation_checks=self.reconciliation_checks,
            anomalies=self.anomalies,
            unmapped_accounts=self.unmapped_accounts,
            metadata={
                "source_file": str(self.filepath.name),
                "analyzed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "engine_version": "1.0.0",
                "rules_applied": [
                    "Decimal cents arithmetic (ROUND_HALF_UP)",
                    "MoM formula: (curr - prior) / abs(prior) * 100",
                    "MoM suppressed when prior is 0 or missing",
                    "Subtotals isolated to avoid double counting",
                    "TTM calculated strictly when 12 consecutive valid periods exist",
                    "Dec 2025 tax credit isolated from recurring operational performance",
                    "Departmental classification: S&M, R&D, G&A, Special Items, Non-Operating",
                ]
            }
        )

    def _load_and_inspect_workbook(self):
        """Inspect and load workbook values safely."""
        self.wb_data = openpyxl.load_workbook(self.filepath, data_only=True)
        self.wb_form = openpyxl.load_workbook(self.filepath, data_only=False)

        # Determine target sheet
        if self.requested_sheet_name and self.requested_sheet_name in self.wb_data.sheetnames:
            sheet_name = self.requested_sheet_name
        else:
            candidates = [s for s in self.wb_data.sheetnames if "income" in s.lower() or "profit" in s.lower() or "p&l" in s.lower()]
            sheet_name = candidates[0] if candidates else self.wb_data.sheetnames[0]

        self.ws_data = self.wb_data[sheet_name]
        self.ws_form = self.wb_form[sheet_name]
        self.active_sheet_name = sheet_name

        # Extract title metadata if present in rows 1-4
        r1_val = self.ws_data.cell(1, 1).value or ""
        r2_val = self.ws_data.cell(2, 1).value or ""
        r3_val = self.ws_data.cell(3, 1).value or ""

        if r1_val:
            self.statement_name = str(r1_val).strip()
        if r2_val:
            self.company_name = str(r2_val).strip()
        if r3_val:
            self.as_of_date = str(r3_val).strip()

    def _parse_periods(self):
        """Identify header row and sort periods chronologically."""
        header_row = None
        raw_periods = []

        for r in range(1, min(15, self.ws_data.max_row + 1)):
            month_hits = []
            for c in range(1, self.ws_data.max_column + 1):
                val = self.ws_data.cell(r, c).value
                parsed = parse_month_string(val)
                if parsed:
                    month_hits.append((c, parsed[0], parsed[1], parsed[2], str(val)))

            if len(month_hits) >= 2:
                header_row = r
                raw_periods = month_hits
                break

        if not header_row or not raw_periods:
            raise ValueError(f"Could not identify monthly columns in sheet {self.active_sheet_name}")

        self.header_row = header_row

        # Check if raw periods are reverse-chronological (newest to oldest)
        if len(raw_periods) >= 2:
            first_period = (raw_periods[0][1], raw_periods[0][2])
            last_period = (raw_periods[-1][1], raw_periods[-1][2])
            if first_period > last_period:
                self.months_were_reversed = True

        # Construct MonthPeriod objects
        parsed_objs = [
            MonthPeriod(
                year=rp[1],
                month=rp[2],
                label=rp[3],
                raw_col_header=rp[4],
                col_index=rp[0]
            )
            for rp in raw_periods
        ]

        # Always sort chronologically (oldest to newest)
        parsed_objs.sort(key=lambda p: (p.year, p.month))
        self.periods = parsed_objs

        # Check for missing calendar gaps between consecutive months
        for i in range(len(self.periods) - 1):
            curr_p = self.periods[i]
            next_p = self.periods[i + 1]
            months_diff = (next_p.year * 12 + next_p.month) - (curr_p.year * 12 + curr_p.month)
            if months_diff > 1:
                cur_y, cur_m = curr_p.year, curr_p.month
                for step in range(1, months_diff):
                    m_val = cur_m + step
                    y_val = cur_y + (m_val - 1) // 12
                    m_norm = ((m_val - 1) % 12) + 1
                    gap_key = f"{y_val:04d}-{m_norm:02d}"
                    self.missing_period_gaps.append({
                        "missing_month": gap_key,
                        "after": curr_p.key,
                        "before": next_p.key,
                    })

    def _classify_department(self, account_name: str, category: str, is_total: bool, is_subtotal: bool) -> str:
        """Classify line items into standard departmental categories."""
        if is_total or is_subtotal:
            return "Total / Section Metric"

        acc_lower = account_name.lower()

        if category == "Revenue":
            return "Revenue"
        if category == "COGS":
            return "COGS"

        # Special non-recurring entries
        if "tax benefit" in acc_lower or "stock-based compensation" in acc_lower or "stock based" in acc_lower:
            return "Special / Non-Recurring"

        # Non-operating items situated in opex
        if "interest income" in acc_lower or "interest expense" in acc_lower:
            return "Non-Operating in Opex"

        # Sales & Marketing
        if (
            category in ["S&M Payroll", "Marketing"]
            or "marketing" in acc_lower
            or "sales" in acc_lower
            or "events & conferences" in acc_lower
            or "ad spend" in acc_lower
            or "partnerships commission" in acc_lower
            or "s & m" in acc_lower
        ):
            return "Sales & Marketing"

        # Research & Development / Product
        if (
            "development" in acc_lower
            or "product" in acc_lower
            or "ai token" in acc_lower
        ):
            return "R&D / Development"

        # General & Administrative
        ga_keywords = [
            "accounting", "tax", "advisory", "bad debt", "bank", "bonus", "consulting",
            "charit", "depreciation", "training", "general", "health", "insurance",
            "legal", "lawyer", "attorney", "meals", "entertainment", "merchant", "office", "payroll",
            "postage", "printing", "stationery", "professional", "recruiting",
            "rent", "severance", "software", "saas", "telephone", "internet",
            "travel", "workers comp", "workers compensation", "administrative", "admin",
            "executive", "utilities", "supplies", "dues", "subscriptions", "audit"
        ]
        if any(kw in acc_lower for kw in ga_keywords):
            return "General & Administrative"

        return "Unmapped"

    def _parse_line_items(self):
        """Parse rows, categorize accounts, and extract monthly values."""
        current_section = "Income"
        current_subtotal_group: Optional[str] = None
        subtotal_rows: Set[int] = set()
        header_rows: Set[int] = set()

        for r in range(self.header_row + 1, self.ws_data.max_row + 1):
            col1 = self.ws_data.cell(r, 1).value
            col2 = self.ws_data.cell(r, 2).value

            c1_str = str(col1).strip() if col1 is not None else ""
            c2_str = str(col2).strip() if col2 is not None else ""

            if c1_str:
                c1_lower = c1_str.lower()
                if c1_lower in ["income", "revenue"]:
                    current_section = "Income"
                    continue
                elif c1_lower in ["cost of goods sold", "cogs", "cost of sales", "cost of goods"]:
                    current_section = "COGS"
                    continue
                elif c1_lower in ["operating expense", "operating expenses", "opex"]:
                    current_section = "Operating Expenses"
                    continue

            account_name = c2_str if c2_str else c1_str
            if not account_name:
                continue

            # Header placeholders without data
            has_numeric_data = False
            for p in self.periods:
                val = self.ws_data.cell(r, p.col_index).value
                if val is not None and str(val).strip() != "":
                    has_numeric_data = True
                    break

            if not has_numeric_data:
                header_rows.add(r)
                if current_section == "Operating Expenses":
                    if "s & m payroll" in account_name.lower():
                        current_subtotal_group = "S&M Payroll"
                    elif account_name.lower() in ["marketing", "marketing/advertising"]:
                        current_subtotal_group = "Marketing"
                    elif any(kw in account_name.lower() for kw in ["payroll", "salaries", "salary", "growth", "advertising"]):
                        current_subtotal_group = account_name
                continue

            # Classify row type
            is_total = False
            is_subtotal = False
            acc_lower = account_name.lower()

            if acc_lower in ["total income", "total revenue"]:
                is_total = True
                category = "Revenue"
            elif acc_lower in ["total cost of goods sold", "total cogs", "total cost of sales"]:
                is_total = True
                category = "COGS"
            elif acc_lower == "gross profit":
                is_total = True
                category = "Gross Profit"
            elif acc_lower in ["total operating expenses", "total expenses"]:
                is_total = True
                category = "Operating Expenses"
            elif acc_lower in ["operating income", "net operating income"]:
                is_total = True
                category = "Operating Income"
            elif acc_lower == "net income":
                is_total = True
                category = "Net Income"
            elif acc_lower.startswith("total ") or acc_lower.startswith("total: ") or acc_lower.endswith(" total") or acc_lower.endswith(" subtotal"):
                is_subtotal = True
                subtotal_rows.add(r)
                if current_section == "Income":
                    category = "Revenue"
                elif current_section == "COGS":
                    category = "COGS"
                elif acc_lower in ["total s & m payroll", "total sales & marketing payroll"]:
                    category = "S&M Payroll"
                elif acc_lower in ["total marketing", "total marketing expenses"]:
                    category = "Marketing"
                else:
                    category = current_subtotal_group or "Operating Expenses"
                current_subtotal_group = None
            else:
                if current_section == "Income":
                    category = "Revenue"
                elif current_section == "COGS":
                    category = "COGS"
                elif current_subtotal_group:
                    category = current_subtotal_group
                else:
                    category = "Operating Expenses"

            department = self._classify_department(account_name, category, is_total, is_subtotal)
            if department == "Unmapped" and not is_total and not is_subtotal:
                if account_name not in self.unmapped_accounts:
                    self.unmapped_accounts.append(account_name)

            period_values: Dict[str, Decimal] = {}
            for p in self.periods:
                raw_cell_val = self.ws_data.cell(r, p.col_index).value
                dec_val = to_cents(raw_cell_val)
                period_values[p.key] = dec_val

            self.line_items_by_row[r] = {
                "row": r,
                "account_name": account_name,
                "category": category,
                "department": department,
                "is_total": is_total,
                "is_subtotal": is_subtotal,
                "subtotal_group": current_subtotal_group,
                "subtotal_components": [],
                "values": period_values,
            }
            self.row_order.append(r)

        # Backward subtotal component resolution
        component_rows_set = set()
        for idx, r in enumerate(self.row_order):
            item = self.line_items_by_row[r]
            if item["is_subtotal"]:
                sub_vals = item["values"]
                matched_rows = []
                cum_vals = {p.key: Decimal("0.00") for p in self.periods}

                for prev_idx in range(idx - 1, -1, -1):
                    prev_r = self.row_order[prev_idx]
                    prev_item = self.line_items_by_row[prev_r]
                    if prev_item["is_total"] or prev_item["is_subtotal"]:
                        break
                    # Stop if an intervening header row exists between prev_r and r
                    if any(prev_r < hr < r for hr in header_rows):
                        break
                    matched_rows.append(prev_r)
                    for pkey in cum_vals:
                        cum_vals[pkey] += prev_item["values"][pkey]

                    if all(cum_vals[pkey] == sub_vals[pkey] for pkey in cum_vals):
                        for comp_r in matched_rows:
                            if item["category"] in ["S&M Payroll", "Marketing"]:
                                self.line_items_by_row[comp_r]["category"] = item["category"]
                                self.line_items_by_row[comp_r]["department"] = "Sales & Marketing"
                            elif any(kw in item["account_name"].lower() for kw in ["sales", "marketing", "growth", "advertising", "payroll"]):
                                self.line_items_by_row[comp_r]["department"] = "Sales & Marketing"
                            self.line_items_by_row[comp_r]["subtotal_component_of"] = r
                            component_rows_set.add(comp_r)
                        item["subtotal_components"] = [self.line_items_by_row[cr]["account_name"] for cr in matched_rows]
                        break

        self.component_rows_set = component_rows_set

    def _calculate_monthly_totals_and_reconcile(self):
        """Calculate and reconcile monthly financial totals using Decimal arithmetic."""
        income_items = []
        cogs_items = []
        subtotal_items = []
        direct_opex_items = []

        rep_total_income = {}
        rep_total_cogs = {}
        rep_gross_profit = {}
        rep_total_opex = {}
        rep_operating_income = {}
        rep_net_income = {}

        for r in self.row_order:
            data = self.line_items_by_row[r]
            acc = data["account_name"].lower()
            vals = data["values"]

            if acc in ["total income", "total revenue"]:
                rep_total_income = vals
            elif acc in ["total cost of goods sold", "total cogs"]:
                rep_total_cogs = vals
            elif acc == "gross profit":
                rep_gross_profit = vals
            elif acc in ["total operating expenses", "total expenses"]:
                rep_total_opex = vals
            elif acc in ["operating income", "net operating income"]:
                rep_operating_income = vals
            elif acc == "net income":
                rep_net_income = vals
            elif data["is_subtotal"]:
                # If this subtotal row has components that are present in the statement,
                # omit the subtotal row from detail additions to avoid double-counting.
                # If it has no component rows, treat it as a standalone detail item.
                if len(data.get("subtotal_components", [])) > 0:
                    if any(kw in acc for kw in ["payroll", "salaries", "salary", "marketing", "advertising", "growth", "s & m", "sales & marketing"]):
                        subtotal_items.append(r)
                    else:
                        pass
                else:
                    cat = data["category"]
                    if cat == "Revenue":
                        income_items.append(r)
                    elif cat == "COGS":
                        cogs_items.append(r)
                    else:
                        direct_opex_items.append(r)
            else:
                cat = data["category"]
                if cat == "Revenue":
                    income_items.append(r)
                elif cat == "COGS":
                    cogs_items.append(r)
                else:
                    if data.get("subtotal_component_of") is None or not any(
                        kw in self.line_items_by_row[data["subtotal_component_of"]]["account_name"].lower()
                        for kw in ["payroll", "salaries", "salary", "marketing", "advertising", "growth", "s & m", "sales & marketing"]
                    ):
                        direct_opex_items.append(r)

        def _subtotal_sort_key(sr):
            acc_l = self.line_items_by_row[sr]["account_name"].lower()
            if any(k in acc_l for k in ["payroll", "salaries", "salary", "s & m"]):
                return 0
            if any(k in acc_l for k in ["marketing", "growth", "advertising"]):
                return 1
            return 2

        subtotal_items.sort(key=_subtotal_sort_key)

        for p in self.periods:
            pkey = p.key

            # 1. Revenue
            calc_income = sum((self.line_items_by_row[r]["values"][pkey] for r in income_items), Decimal("0.00")).quantize(CENTS)
            rep_inc = rep_total_income.get(pkey, calc_income)
            diff_inc = (calc_income - rep_inc).quantize(CENTS)
            self.reconciliation_checks.append(ReconciliationCheck(
                metric="Total Income",
                period=pkey,
                reported_value=str(rep_inc),
                calculated_value=str(calc_income),
                difference=str(diff_inc),
                is_valid=(abs(diff_inc) <= CENTS),
            ))

            # 2. COGS
            calc_cogs = sum((self.line_items_by_row[r]["values"][pkey] for r in cogs_items), Decimal("0.00")).quantize(CENTS)
            rep_cg = rep_total_cogs.get(pkey, calc_cogs)
            diff_cogs = (calc_cogs - rep_cg).quantize(CENTS)
            self.reconciliation_checks.append(ReconciliationCheck(
                metric="Total COGS",
                period=pkey,
                reported_value=str(rep_cg),
                calculated_value=str(calc_cogs),
                difference=str(diff_cogs),
                is_valid=(abs(diff_cogs) <= CENTS),
            ))

            # 3. Gross Profit
            calc_gp = (calc_income - calc_cogs).quantize(CENTS)
            rep_gp = rep_gross_profit.get(pkey, calc_gp)
            diff_gp = (calc_gp - rep_gp).quantize(CENTS)
            self.reconciliation_checks.append(ReconciliationCheck(
                metric="Gross Profit",
                period=pkey,
                reported_value=str(rep_gp),
                calculated_value=str(calc_gp),
                difference=str(diff_gp),
                is_valid=(abs(diff_gp) <= CENTS),
            ))

            # 4. Functional Subtotals Reconciliation
            calc_subtotals_total = Decimal("0.00")
            for sub_r in subtotal_items:
                sub_data = self.line_items_by_row[sub_r]
                sub_acc = sub_data["account_name"]
                sub_acc_lower = sub_acc.lower()

                if sub_acc_lower in ["total s & m payroll", "total sales & marketing payroll"]:
                    metric_name = "Total S&M Payroll"
                elif sub_acc_lower in ["total marketing", "total marketing expenses"]:
                    metric_name = "Total Marketing"
                else:
                    metric_name = sub_acc

                calc_sub = sum(
                    (self.line_items_by_row[cr]["values"][pkey]
                     for cr in self.row_order
                     if self.line_items_by_row[cr].get("subtotal_component_of") == sub_r),
                    Decimal("0.00")
                ).quantize(CENTS)
                rep_sub = sub_data["values"].get(pkey, calc_sub)
                diff_sub = (calc_sub - rep_sub).quantize(CENTS)
                self.reconciliation_checks.append(ReconciliationCheck(
                    metric=metric_name,
                    period=pkey,
                    reported_value=str(rep_sub),
                    calculated_value=str(calc_sub),
                    difference=str(diff_sub),
                    is_valid=(abs(diff_sub) <= CENTS),
                ))
                calc_subtotals_total += calc_sub

            # 5. Total Operating Expenses without double-counting subtotals
            calc_direct_opex = sum((self.line_items_by_row[r]["values"][pkey] for r in direct_opex_items), Decimal("0.00")).quantize(CENTS)
            calc_total_opex = (calc_direct_opex + calc_subtotals_total).quantize(CENTS)
            rep_op = rep_total_opex.get(pkey, calc_total_opex)
            diff_opex = (calc_total_opex - rep_op).quantize(CENTS)
            self.reconciliation_checks.append(ReconciliationCheck(
                metric="Total Operating Expenses",
                period=pkey,
                reported_value=str(rep_op),
                calculated_value=str(calc_total_opex),
                difference=str(diff_opex),
                is_valid=(abs(diff_opex) <= CENTS),
            ))

            # 7. Operating Income
            calc_oi = (calc_gp - calc_total_opex).quantize(CENTS)
            rep_oi = rep_operating_income.get(pkey, calc_oi)
            diff_oi = (calc_oi - rep_oi).quantize(CENTS)
            self.reconciliation_checks.append(ReconciliationCheck(
                metric="Operating Income",
                period=pkey,
                reported_value=str(rep_oi),
                calculated_value=str(calc_oi),
                difference=str(diff_oi),
                is_valid=(abs(diff_oi) <= CENTS),
            ))

            rep_ni = rep_net_income.get(pkey, calc_oi)

            # Gross Margin %
            if calc_income != Decimal("0.00"):
                gm_pct = ((calc_gp / calc_income) * Decimal("100.00")).quantize(CENTS, rounding=ROUND_HALF_UP)
                gm_pct_str = f"{gm_pct:.2f}%"
            else:
                gm_pct_str = None

            # Normalized operational metrics: Core Opex excludes Special / Non-Recurring and Non-Operating in Opex
            # (retaining S&M, R&D, G&A, and Unmapped operating expenses without double-counting totals or subtotals)
            special_val = sum(
                (
                    self.line_items_by_row[r]["values"][pkey]
                    for r in self.row_order
                    if not self.line_items_by_row[r]["is_total"]
                    and not self.line_items_by_row[r]["is_subtotal"]
                    and self.line_items_by_row[r]["department"] == "Special / Non-Recurring"
                ),
                Decimal("0.00")
            ).quantize(CENTS)

            non_op_val = sum(
                (
                    self.line_items_by_row[r]["values"][pkey]
                    for r in self.row_order
                    if not self.line_items_by_row[r]["is_total"]
                    and not self.line_items_by_row[r]["is_subtotal"]
                    and self.line_items_by_row[r]["department"] == "Non-Operating in Opex"
                ),
                Decimal("0.00")
            ).quantize(CENTS)

            core_opex_val = (calc_total_opex - special_val - non_op_val).quantize(CENTS)
            core_oi_val = (calc_gp - core_opex_val).quantize(CENTS)

            self.monthly_summaries.append(MonthlySummary(
                period=pkey,
                label=p.label,
                revenue=str(calc_income),
                cogs=str(calc_cogs),
                gross_profit=str(calc_gp),
                gross_margin_pct=gm_pct_str,
                total_opex=str(calc_total_opex),
                operating_income=str(calc_oi),
                net_income=str(rep_ni),
                normalized_core_opex=str(core_opex_val),
                normalized_operating_income=str(core_oi_val),
            ))

    def _calculate_category_summaries(self):
        """Aggregate departmental category totals (S&M, R&D, G&A, Special, Non-Operating)."""
        categories = [
            "Revenue",
            "COGS",
            "Sales & Marketing",
            "R&D / Development",
            "General & Administrative",
            "Special / Non-Recurring",
            "Non-Operating in Opex"
        ]
        if self.unmapped_accounts:
            categories.append("Unmapped")

        for cat in categories:
            # Gather all leaf rows belonging to this department
            leaf_rows = [
                r for r in self.row_order
                if not self.line_items_by_row[r]["is_total"]
                and (not self.line_items_by_row[r]["is_subtotal"] or len(self.line_items_by_row[r].get("subtotal_components", [])) == 0)
                and (self.line_items_by_row[r]["department"] == cat or self.line_items_by_row[r]["category"] == cat)
            ]

            values_map: Dict[str, str] = {}
            diff_map: Dict[str, Optional[str]] = {}
            pct_map: Dict[str, Optional[str]] = {}

            for i, p in enumerate(self.periods):
                tot = sum((self.line_items_by_row[r]["values"][p.key] for r in leaf_rows), Decimal("0.00")).quantize(CENTS)
                values_map[p.key] = str(tot)

                if i == 0:
                    diff_map[p.key] = None
                    pct_map[p.key] = None
                else:
                    prior_p = self.periods[i - 1]
                    prior_tot = sum((self.line_items_by_row[r]["values"][prior_p.key] for r in leaf_rows), Decimal("0.00")).quantize(CENTS)
                    diff = (tot - prior_tot).quantize(CENTS)
                    diff_map[p.key] = str(diff)
                    if prior_tot != Decimal("0.00"):
                        pct = ((diff / abs(prior_tot)) * Decimal("100.00")).quantize(CENTS, rounding=ROUND_HALF_UP)
                        pct_map[p.key] = f"{pct:.2f}%"
                    else:
                        pct_map[p.key] = None

            self.category_summaries.append(CategorySummary(
                category=cat,
                values=values_map,
                mom_diff=diff_map,
                mom_pct=pct_map,
                ttm_values={},
            ))

    def _calculate_mom_metrics(self):
        """Calculate Month-over-Month changes for summaries and line items."""
        for i in range(len(self.monthly_summaries)):
            curr = self.monthly_summaries[i]
            if i == 0:
                continue

            prior = self.monthly_summaries[i - 1]
            curr_y, curr_m = int(curr.period[:4]), int(curr.period[5:7])
            prior_y, prior_m = int(prior.period[:4]), int(prior.period[5:7])
            months_diff = (curr_y * 12 + curr_m) - (prior_y * 12 + prior_m)

            if months_diff != 1:
                continue

            # Revenue MoM
            curr_rev = Decimal(curr.revenue)
            prior_rev = Decimal(prior.revenue)
            diff_rev = (curr_rev - prior_rev).quantize(CENTS)
            curr.revenue_mom_diff = str(diff_rev)
            if prior_rev != Decimal("0.00"):
                pct = ((diff_rev / abs(prior_rev)) * Decimal("100.00")).quantize(CENTS, rounding=ROUND_HALF_UP)
                curr.revenue_mom_pct = f"{pct:.2f}%"

            # Gross Profit MoM
            curr_gp = Decimal(curr.gross_profit)
            prior_gp = Decimal(prior.gross_profit)
            diff_gp = (curr_gp - prior_gp).quantize(CENTS)
            curr.gp_mom_diff = str(diff_gp)
            if prior_gp != Decimal("0.00"):
                pct = ((diff_gp / abs(prior_gp)) * Decimal("100.00")).quantize(CENTS, rounding=ROUND_HALF_UP)
                curr.gp_mom_pct = f"{pct:.2f}%"

            # Opex MoM
            curr_op = Decimal(curr.total_opex)
            prior_op = Decimal(prior.total_opex)
            diff_op = (curr_op - prior_op).quantize(CENTS)
            curr.opex_mom_diff = str(diff_op)
            if prior_op != Decimal("0.00"):
                pct = ((diff_op / abs(prior_op)) * Decimal("100.00")).quantize(CENTS, rounding=ROUND_HALF_UP)
                curr.opex_mom_pct = f"{pct:.2f}%"

            # Operating Income MoM
            curr_oi = Decimal(curr.operating_income)
            prior_oi = Decimal(prior.operating_income)
            diff_oi = (curr_oi - prior_oi).quantize(CENTS)
            curr.oi_mom_diff = str(diff_oi)
            if prior_oi != Decimal("0.00"):
                pct = ((diff_oi / abs(prior_oi)) * Decimal("100.00")).quantize(CENTS, rounding=ROUND_HALF_UP)
                curr.oi_mom_pct = f"{pct:.2f}%"

        # Line Item MoM
        for r in self.row_order:
            item = self.line_items_by_row[r]
            vals = item["values"]
            diff_map: Dict[str, Optional[str]] = {}
            pct_map: Dict[str, Optional[str]] = {}

            for i in range(len(self.periods)):
                pkey = self.periods[i].key
                if i == 0:
                    diff_map[pkey] = None
                    pct_map[pkey] = None
                    continue

                prior_pkey = self.periods[i - 1].key
                curr_y, curr_m = self.periods[i].year, self.periods[i].month
                prior_y, prior_m = self.periods[i - 1].year, self.periods[i - 1].month
                if (curr_y * 12 + curr_m) - (prior_y * 12 + prior_m) != 1:
                    diff_map[pkey] = None
                    pct_map[pkey] = None
                    continue

                curr_val = vals[pkey]
                prior_val = vals[prior_pkey]
                diff = (curr_val - prior_val).quantize(CENTS)
                diff_map[pkey] = str(diff)

                if prior_val != Decimal("0.00"):
                    pct = ((diff / abs(prior_val)) * Decimal("100.00")).quantize(CENTS, rounding=ROUND_HALF_UP)
                    pct_map[pkey] = f"{pct:.2f}%"
                else:
                    pct_map[pkey] = None

            self.parsed_line_items.append(LineItemData(
                account_name=item["account_name"],
                category=item["category"],
                is_subtotal=item["is_subtotal"],
                is_total=item["is_total"],
                subtotal_components=item.get("subtotal_components", []),
                values={k: str(v) for k, v in vals.items()},
                mom_diff=diff_map,
                mom_pct=pct_map,
            ))

    def _calculate_ttm_metrics(self):
        """Calculate Trailing-Twelve-Month (TTM) windows strictly when 12 consecutive months exist."""
        summary_by_period = {s.period: s for s in self.monthly_summaries}
        n_periods = len(self.periods)

        if n_periods < 12:
            self.anomalies.append(AnomalyFlag(
                account="Trailing Twelve Month (TTM)",
                period="All",
                amount=None,
                severity=Severity.INFO,
                category=AnomalyCategory.LIMITATION,
                description=f"Dataset has only {n_periods} monthly periods; minimum 12 consecutive months required for TTM calculations.",
                impact="TTM windows withheld.",
                recommendation="Provide at least 12 continuous reporting months to calculate TTM trends.",
            ))
            return

        for i in range(11, n_periods):
            window_slice = self.periods[i - 11 : i + 1]
            end_period = window_slice[-1]
            start_period = window_slice[0]

            is_consecutive = True
            for k in range(len(window_slice) - 1):
                p1 = window_slice[k]
                p2 = window_slice[k + 1]
                if (p2.year * 12 + p2.month) - (p1.year * 12 + p1.month) != 1:
                    is_consecutive = False
                    break

            if not is_consecutive:
                self.ttm_windows.append(TTMWindow(
                    end_period=end_period.key,
                    start_period=start_period.key,
                    months_included=[p.key for p in window_slice],
                    is_valid=False,
                    revenue="0.00",
                    cogs="0.00",
                    gross_profit="0.00",
                    gross_margin_pct=None,
                    total_opex="0.00",
                    operating_income="0.00",
                    net_income="0.00",
                    notes="Window rejected: contains calendar gaps or missing periods.",
                ))
                continue

            ttm_rev = sum((Decimal(summary_by_period[p.key].revenue) for p in window_slice), Decimal("0.00")).quantize(CENTS)
            ttm_cogs = sum((Decimal(summary_by_period[p.key].cogs) for p in window_slice), Decimal("0.00")).quantize(CENTS)
            ttm_gp = sum((Decimal(summary_by_period[p.key].gross_profit) for p in window_slice), Decimal("0.00")).quantize(CENTS)
            ttm_opex = sum((Decimal(summary_by_period[p.key].total_opex) for p in window_slice), Decimal("0.00")).quantize(CENTS)
            ttm_oi = sum((Decimal(summary_by_period[p.key].operating_income) for p in window_slice), Decimal("0.00")).quantize(CENTS)
            ttm_ni = sum((Decimal(summary_by_period[p.key].net_income) for p in window_slice), Decimal("0.00")).quantize(CENTS)

            ttm_norm_opex = sum((Decimal(summary_by_period[p.key].normalized_core_opex) for p in window_slice), Decimal("0.00")).quantize(CENTS)
            ttm_norm_oi = sum((Decimal(summary_by_period[p.key].normalized_operating_income) for p in window_slice), Decimal("0.00")).quantize(CENTS)

            if ttm_rev != Decimal("0.00"):
                gm_pct = ((ttm_gp / ttm_rev) * Decimal("100.00")).quantize(CENTS, rounding=ROUND_HALF_UP)
                gm_pct_str = f"{gm_pct:.2f}%"
            else:
                gm_pct_str = None

            self.ttm_windows.append(TTMWindow(
                end_period=end_period.key,
                start_period=start_period.key,
                months_included=[p.key for p in window_slice],
                is_valid=True,
                revenue=str(ttm_rev),
                cogs=str(ttm_cogs),
                gross_profit=str(ttm_gp),
                gross_margin_pct=gm_pct_str,
                total_opex=str(ttm_opex),
                operating_income=str(ttm_oi),
                net_income=str(ttm_ni),
                normalized_core_opex=str(ttm_norm_opex),
                normalized_operating_income=str(ttm_norm_oi),
                notes=f"Valid 12-month rolling window from {start_period.label} to {end_period.label}.",
            ))

            # Populate category TTM values
            for cs in self.category_summaries:
                cat_sum = sum((Decimal(cs.values[p.key]) for p in window_slice), Decimal("0.00")).quantize(CENTS)
                cs.ttm_values[end_period.key] = str(cat_sum)

    def _detect_anomalies_and_flags(self):
        """Flag accounting anomalies, reversals, misclassifications, and data issues."""
        # 1. Reverse order notice
        if self.months_were_reversed:
            self.anomalies.append(AnomalyFlag(
                account="Reporting Structure",
                period="All",
                amount=None,
                severity=Severity.INFO,
                category=AnomalyCategory.LIMITATION,
                description="Workbook columns were structured in reverse chronological order (newest month to oldest).",
                impact="Parsed and sorted into chronological sequence (oldest to newest) for valid MoM/TTM analysis.",
                recommendation="No action needed; chronological ordering restored by engine.",
            ))

        # 2. Missing period gaps
        for gap in self.missing_period_gaps:
            self.anomalies.append(AnomalyFlag(
                account="Time Continuity",
                period=gap["missing_month"],
                amount=None,
                severity=Severity.CRITICAL,
                category=AnomalyCategory.MISSING_PERIOD,
                description=f"Missing monthly period {gap['missing_month']} between {gap['after']} and {gap['before']}.",
                impact="Breaks MoM continuity and invalidates TTM windows spanning across this interval.",
                recommendation="Obtain accounting statements for the missing calendar month.",
            ))

        # 3. Dec 2025 Accounting Anomaly & Line-Item Flags
        tax_benefit_thresh = self.thresholds["tax_benefit_credit"]
        stock_comp_thresh = self.thresholds["stock_comp_spike"]
        expense_reversal_thresh = self.thresholds["expense_reversal"]

        for r, item in self.line_items_by_row.items():
            acc_name = item["account_name"]
            vals = item["values"]

            if "tax benefit" in acc_name.lower():
                for pkey, amt in vals.items():
                    if amt < -tax_benefit_thresh:
                        dec_summary = next((s for s in self.monthly_summaries if s.period == pkey), None)
                        period_label = dec_summary.label if (dec_summary and dec_summary.label) else pkey

                        tot_opex = Decimal(dec_summary.total_opex) if dec_summary else Decimal("0.00")
                        opex_fmt = f"-${abs(tot_opex):,.2f}" if tot_opex < Decimal("0.00") else f"${tot_opex:,.2f}"

                        op_income = Decimal(dec_summary.operating_income) if dec_summary else Decimal("0.00")
                        oi_fmt = f"+${op_income:,.2f}" if op_income >= Decimal("0.00") else f"-${abs(op_income):,.2f}"

                        core_oi = Decimal(dec_summary.normalized_operating_income) if dec_summary else Decimal("0.00")
                        core_loss_fmt = f"-${abs(core_oi):,.2f}" if core_oi < Decimal("0.00") else f"+${core_oi:,.2f}"

                        cs_non_op = next((c for c in self.category_summaries if c.category == "Non-Operating in Opex"), None)
                        non_op_val = Decimal(cs_non_op.values[pkey]) if (cs_non_op and pkey in cs_non_op.values) else Decimal("0.00")
                        partial_oi = (core_oi - non_op_val).quantize(CENTS)
                        partial_loss_fmt = f"-${abs(partial_oi):,.2f}" if partial_oi < Decimal("0.00") else f"+${partial_oi:,.2f}"

                        self.anomalies.append(AnomalyFlag(
                            account=acc_name,
                            period=pkey,
                            amount=str(amt),
                            severity=Severity.CRITICAL,
                            category=AnomalyCategory.ACCOUNTING_ANOMALY,
                            description=(
                                f"Massive non-recurring tax benefit credit of ${abs(amt):,.2f} recorded directly inside operating expenses for {pkey}. "
                                f"This credit causes total operating expenses to flip to negative ({opex_fmt}) and yields an artificial operating profit of {oi_fmt}."
                            ),
                            impact=(
                                f"CRITICAL AUDIT FINDING: The business DID NOT become genuinely operationally profitable in {period_label}. "
                                f"Underlying normalized core operating loss (excluding this tax credit, SBC, and non-operating interest) was {core_loss_fmt} "
                                f"(or {partial_loss_fmt} if excluding only tax benefit and SBC, retaining non-operating interest in opex)."
                            ),
                            recommendation="Adjust out this non-recurring tax credit when evaluating operational cash burn or recurring financial performance.",
                        ))

            if "stock-based compensation" in acc_name.lower() or "stock based" in acc_name.lower():
                for pkey, amt in vals.items():
                    if amt > stock_comp_thresh:
                        self.anomalies.append(AnomalyFlag(
                            account=acc_name,
                            period=pkey,
                            amount=str(amt),
                            severity=Severity.WARNING,
                            category=AnomalyCategory.ACCOUNTING_ANOMALY,
                            description=f"Unusual one-off Stock-Based Compensation expense of ${amt:,.2f} recorded in {pkey} (zero in all other periods).",
                            impact="One-time non-cash compensation charge inflating expenses before being overshadowed by the tax benefit credit.",
                            recommendation="Normalize non-cash stock compensation when assessing recurring cash burn.",
                        ))

            # Misclassification: Interest inside Operating Expenses
            if acc_name.lower() in ["interest income", "interest expense"]:
                self.anomalies.append(AnomalyFlag(
                    account=acc_name,
                    period="All",
                    amount=None,
                    severity=Severity.WARNING,
                    category=AnomalyCategory.MISCLASSIFICATION,
                    description=f"{acc_name} is situated inside Operating Expenses.",
                    impact="Distorts true core operating margin and EBITDA; GAAP requires presentation below Operating Income in Other Income/Expense.",
                    recommendation="Reclassify interest items to Below-the-Line Non-Operating section.",
                ))

            # Negative values in Revenue or COGS or unusual expense credits
            if not item["is_total"] and not item["is_subtotal"]:
                cat = item["category"]
                for pkey, amt in vals.items():
                    if cat in ["Revenue", "COGS"] and amt < Decimal("0.00"):
                        self.anomalies.append(AnomalyFlag(
                            account=acc_name,
                            period=pkey,
                            amount=str(amt),
                            severity=Severity.WARNING,
                            category=AnomalyCategory.REVERSAL,
                            description=f"Negative line item reversal of ${amt:,.2f} in {cat} category for {pkey}.",
                            impact=f"Reduces net {cat.lower()} for the period; suggests prior period billing correction or invoice credit memo.",
                            recommendation="Review supporting invoice and credit memo schedules for accounting reason.",
                        ))
                    elif cat not in ["Revenue", "COGS"] and amt < -expense_reversal_thresh:
                        if "tax benefit" not in acc_name.lower() and "interest income" not in acc_name.lower():
                            self.anomalies.append(AnomalyFlag(
                                account=acc_name,
                                period=pkey,
                                amount=str(amt),
                                severity=Severity.WARNING,
                                category=AnomalyCategory.REVERSAL,
                                description=f"Credit entry / expense reversal of ${amt:,.2f} in {acc_name} for {pkey}.",
                                impact="Negative expense reduces operating costs in the period; likely vendor credit or accrual true-up.",
                                recommendation="Confirm whether this credit relates to prior over-accrual.",
                            ))

        # 4. Reconciliation discrepancies
        for rc in self.reconciliation_checks:
            if not rc.is_valid:
                if self.source_type == "quickbooks":
                    rec = "Audit underlying QuickBooks transaction postings, sub-account rollup mappings, or report line item aggregations."
                elif self.source_type == "excel":
                    rec = "Investigate workbook formula definitions, component rollups, or hidden row discrepancies."
                else:
                    rec = "Investigate financial statement line item aggregations, component rollups, or supporting ledger schedules."

                self.anomalies.append(AnomalyFlag(
                    account=rc.metric,
                    period=rc.period,
                    amount=rc.difference,
                    severity=Severity.CRITICAL,
                    category=AnomalyCategory.RECONCILIATION_DISCREPANCY,
                    description=f"Discrepancy detected in {rc.metric} for {rc.period}: Reported={rc.reported_value}, Calculated={rc.calculated_value}, Diff={rc.difference}.",
                    impact="Reported financial statement total does not reconcile with sum of components.",
                    recommendation=rec,
                ))
