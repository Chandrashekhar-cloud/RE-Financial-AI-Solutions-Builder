"""Command-line interface for financial trend analysis.

Reads financial statement workbooks, runs the deterministic calculation engine,
and generates both machine-readable analysis.json and human-readable report.md.
"""

import argparse
import json
import sys
from pathlib import Path

from .engine import FinancialCalculationEngine
from .reporter import FinancialReportGenerator


def get_default_input_path() -> str:
    """Return the default input workbook path (relative to CWD).

    The workbook is expected at data/ABC Inc - Financial Statements.xlsx
    relative to the abc-trend-analysis/ project directory.
    """
    return "data/ABC Inc - Financial Statements.xlsx"


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Run reusable monthly financial trend analysis on Excel financial statements."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=get_default_input_path(),
        help="Path to input Excel financial statements workbook (defaults to original company workbook).",
    )
    parser.add_argument(
        "--qbo-json",
        type=str,
        default=None,
        help="Optional path to QuickBooks Online ProfitAndLoss API JSON report. If provided, normalizes QBO JSON via QBOReportAdapter before running analysis.",
    )
    parser.add_argument(
        "--sheet",
        "-s",
        type=str,
        default=None,
        help="Optional name of worksheet to analyze (defaults to auto-detect Income Statement).",
    )
    parser.add_argument(
        "--output-json",
        "-j",
        type=str,
        default="results/analysis.json",
        help="Path where machine-readable analysis.json will be saved.",
    )
    parser.add_argument(
        "--output-report",
        "-r",
        type=str,
        default="results/report.md",
        help="Path where human-readable report.md will be saved.",
    )
    parser.add_argument(
        "--baseline",
        "-b",
        type=str,
        default=None,
        help="Optional path to baseline reference (Excel workbook or analysis.json) to perform cross-dataset comparative diffing against.",
    )
    parser.add_argument(
        "--thresholds",
        "-t",
        type=str,
        default=None,
        help="Optional path to custom anomaly thresholds JSON configuration file.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress console output.",
    )
    return parser.parse_args(args)


def main(args=None):
    opts = parse_args(args)

    if opts.qbo_json:
        qbo_path = Path(opts.qbo_json)
        if not qbo_path.exists():
            print(f"Error: QBO JSON report file not found at: {qbo_path}", file=sys.stderr)
            return 1

        if not opts.quiet:
            print(f"==================================================")
            print(f"RE Financial Services - Monthly Trend Analysis Engine")
            print(f"==================================================")
            print(f"Loading QuickBooks P&L JSON: {qbo_path}")

        try:
            from .adapters.qbo_adapter import QBOReportAdapter
            adapter = QBOReportAdapter(qbo_path, thresholds_path=opts.thresholds)
            result = adapter.run_analysis()
        except (json.JSONDecodeError, ValueError) as err:
            print(f"Error: Failed to parse QBO JSON report or configuration: {err}", file=sys.stderr)
            return 1
        except FileNotFoundError as err:
            print(f"Error: File not found: {err}", file=sys.stderr)
            return 1
        except Exception as err:
            print(f"Error: Failed to process QBO JSON report: {err}", file=sys.stderr)
            return 1
    else:
        input_path = Path(opts.input)
        if not input_path.exists():
            print(f"Error: Input workbook not found at: {input_path}", file=sys.stderr)
            return 1

        if not opts.quiet:
            print(f"==================================================")
            print(f"RE Financial Services - Monthly Trend Analysis Engine")
            print(f"==================================================")
            print(f"Loading workbook: {input_path}")

        try:
            # 1. Run Calculation Engine
            engine = FinancialCalculationEngine(str(input_path), sheet_name=opts.sheet, thresholds_path=opts.thresholds)
            result = engine.run_analysis()
        except FileNotFoundError as err:
            print(f"Error: File not found: {err}", file=sys.stderr)
            return 1
        except ValueError as err:
            print(f"Error: Configuration or data error: {err}", file=sys.stderr)
            return 1

    # 2. Optional Baseline Comparison
    baseline_comparison = None
    if opts.baseline:
        base_path = Path(opts.baseline)
        if not base_path.exists():
            print(f"Error: Baseline reference not found at: {base_path}", file=sys.stderr)
            return 1

        try:
            from .comparator import compare_financial_results
            if base_path.suffix.lower() == ".json":
                with open(base_path, "r", encoding="utf-8") as f:
                    base_data = json.load(f)
                baseline_comparison = compare_financial_results(
                    result,
                    base_data,
                    target_name=str(opts.qbo_json or opts.input),
                    baseline_name=str(base_path),
                )
            else:
                base_engine = FinancialCalculationEngine(str(base_path), thresholds_path=opts.thresholds)
                base_res = base_engine.run_analysis()
                baseline_comparison = compare_financial_results(
                    result,
                    base_res,
                    target_name=str(opts.qbo_json or opts.input),
                    baseline_name=str(base_path),
                )
        except Exception as err:
            print(f"Error: Failed to perform baseline comparison: {err}", file=sys.stderr)
            return 1

    # 3. Output machine-readable JSON
    json_path = Path(opts.output_json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    result_dict = result.to_dict()
    if baseline_comparison:
        result_dict["baseline_comparison"] = baseline_comparison

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)

    # 4. Output human-readable Report
    report_gen = FinancialReportGenerator(result, baseline_comparison=baseline_comparison)
    markdown_report = report_gen.generate_markdown()
    report_path = Path(opts.output_report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(markdown_report)

    if not opts.quiet:
        total_checks = len(result.reconciliation_checks)
        passed_checks = sum(1 for rc in result.reconciliation_checks if rc.is_valid)
        failed_checks = total_checks - passed_checks
        pass_pct = (passed_checks / total_checks * 100) if total_checks > 0 else 0.0

        print(f"Successfully processed {len(result.periods_analyzed)} monthly periods.")
        print(f"Months reversed in source: {result.months_were_reversed}")
        print(f"Valid TTM windows calculated: {len([w for w in result.ttm_windows if w.is_valid])}")
        print(f"Total audit flags / anomalies identified: {len(result.anomalies)}")

        if failed_checks == 0 and total_checks > 0:
            print(f"Integrity check status: 100% reconciled ({passed_checks}/{total_checks} checks passed)")
        else:
            print(f"Integrity check status: {failed_checks} discrepancy/discrepancies detected ({passed_checks}/{total_checks} checks passed, {pass_pct:.1f}% accuracy)")

        if baseline_comparison:
            print(f"Baseline comparison: {baseline_comparison['periods_with_zero_drift']}/{baseline_comparison['periods_compared']} periods with $0.00 drift ({baseline_comparison['total_variances_found']} variances detected)")

        print(f"Saved machine-readable JSON: {json_path}")
        print(f"Saved human-readable Report: {report_path}")
        print(f"==================================================")

    return 0


if __name__ == "__main__":
    sys.exit(main())
