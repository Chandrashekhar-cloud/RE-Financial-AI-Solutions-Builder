"""Data models for financial trend analysis."""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AnomalyCategory(str, Enum):
    ACCOUNTING_ANOMALY = "ACCOUNTING_ANOMALY"
    REVERSAL = "REVERSAL"
    MISCLASSIFICATION = "MISCLASSIFICATION"
    RECONCILIATION_DISCREPANCY = "RECONCILIATION_DISCREPANCY"
    LIMITATION = "LIMITATION"
    MISSING_PERIOD = "MISSING_PERIOD"


@dataclass
class MonthPeriod:
    year: int
    month: int  # 1-12
    label: str  # e.g., 'Jan 2025'
    raw_col_header: str
    col_index: int

    @property
    def key(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def __lt__(self, other: "MonthPeriod") -> bool:
        return (self.year, self.month) < (other.year, other.month)


@dataclass
class AnomalyFlag:
    account: str
    period: str  # YYYY-MM or 'All'
    amount: Optional[str]  # string representation of Decimal
    severity: Severity
    category: AnomalyCategory
    description: str
    impact: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account": self.account,
            "period": self.period,
            "amount": self.amount,
            "severity": self.severity.value,
            "category": self.category.value,
            "description": self.description,
            "impact": self.impact,
            "recommendation": self.recommendation,
        }


@dataclass
class ReconciliationCheck:
    metric: str
    period: str
    reported_value: str
    calculated_value: str
    difference: str
    is_valid: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "period": self.period,
            "reported_value": self.reported_value,
            "calculated_value": self.calculated_value,
            "difference": self.difference,
            "is_valid": self.is_valid,
        }


@dataclass
class LineItemData:
    account_name: str
    category: str  # 'Revenue', 'COGS', 'S&M Payroll', 'Marketing', 'Operating Expenses', etc.
    is_subtotal: bool
    is_total: bool
    subtotal_components: List[str] = field(default_factory=list)
    values: Dict[str, str] = field(default_factory=dict)  # period_key -> decimal_string
    mom_diff: Dict[str, Optional[str]] = field(default_factory=dict)
    mom_pct: Dict[str, Optional[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_name": self.account_name,
            "category": self.category,
            "is_subtotal": self.is_subtotal,
            "is_total": self.is_total,
            "subtotal_components": self.subtotal_components,
            "values": self.values,
            "mom_diff": self.mom_diff,
            "mom_pct": self.mom_pct,
        }


@dataclass
class MonthlySummary:
    period: str
    label: str
    revenue: str
    cogs: str
    gross_profit: str
    gross_margin_pct: Optional[str]
    total_opex: str
    operating_income: str
    net_income: str
    # Normalized operational metrics (excluding Dec 2025 tax benefit/SBC and interest items)
    normalized_core_opex: str = "0.00"
    normalized_operating_income: str = "0.00"
    revenue_mom_diff: Optional[str] = None
    revenue_mom_pct: Optional[str] = None
    gp_mom_diff: Optional[str] = None
    gp_mom_pct: Optional[str] = None
    opex_mom_diff: Optional[str] = None
    opex_mom_pct: Optional[str] = None
    oi_mom_diff: Optional[str] = None
    oi_mom_pct: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CategorySummary:
    category: str
    values: Dict[str, str]
    mom_diff: Dict[str, Optional[str]]
    mom_pct: Dict[str, Optional[str]]
    ttm_values: Dict[str, Optional[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TTMWindow:
    end_period: str
    start_period: str
    months_included: List[str]
    is_valid: bool
    revenue: str
    cogs: str
    gross_profit: str
    gross_margin_pct: Optional[str]
    total_opex: str
    operating_income: str
    net_income: str
    normalized_core_opex: str = "0.00"
    normalized_operating_income: str = "0.00"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FinancialAnalysisResult:
    company_name: str
    statement_name: str
    as_of_date: str
    periods_analyzed: List[Dict[str, Any]]
    months_were_reversed: bool
    missing_period_gaps: List[Dict[str, str]]
    monthly_summaries: List[MonthlySummary]
    category_summaries: List[CategorySummary]
    line_items: List[LineItemData]
    ttm_windows: List[TTMWindow]
    reconciliation_checks: List[ReconciliationCheck]
    anomalies: List[AnomalyFlag]
    metadata: Dict[str, Any]
    unmapped_accounts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {
                **self.metadata,
                "company_name": self.company_name,
                "statement_name": self.statement_name,
                "as_of_date": self.as_of_date,
                "total_periods_found": len(self.periods_analyzed),
                "periods_chronological": [p["key"] for p in self.periods_analyzed],
                "months_were_reversed_in_source": self.months_were_reversed,
                "has_missing_period_gaps": len(self.missing_period_gaps) > 0,
                "missing_period_gaps": self.missing_period_gaps,
                "total_valid_ttm_windows": len([w for w in self.ttm_windows if w.is_valid]),
                "unmapped_accounts_count": len(self.unmapped_accounts),
                "unmapped_accounts": self.unmapped_accounts,
            },
            "monthly_summaries": [s.to_dict() for s in self.monthly_summaries],
            "category_summaries": [c.to_dict() for c in self.category_summaries],
            "ttm_windows": [w.to_dict() for w in self.ttm_windows],
            "line_items": [li.to_dict() for li in self.line_items],
            "reconciliation_checks": [rc.to_dict() for rc in self.reconciliation_checks],
            "anomalies_and_flags": [a.to_dict() for a in self.anomalies],
            "unmapped_accounts": self.unmapped_accounts,
        }
