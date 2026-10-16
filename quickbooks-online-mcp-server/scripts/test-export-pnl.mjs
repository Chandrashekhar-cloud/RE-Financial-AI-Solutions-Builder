/**
 * Unit tests for export-pnl.mjs schema validation and safety rules.
 *
 * Runs without network dependencies using node:assert.
 */

import assert from "node:assert";
import { validateProfitAndLossReport } from "./export-pnl.mjs";

console.log("Running export-pnl schema validation unit tests...");

// 1. Valid Intuit V3 P&L report
const validReport = {
  Header: {
    ReportName: "ProfitAndLoss",
    StartPeriod: "2025-01-01",
    EndPeriod: "2026-06-30",
  },
  Columns: {
    Column: [
      { ColTitle: "", ColType: "Account" },
      { ColTitle: "Jan 2025", ColType: "Money" },
      { ColTitle: "Feb 2025", ColType: "Money" },
      { ColTitle: "Total", ColType: "Money" },
    ],
  },
  Rows: {
    Row: [
      { type: "Section", group: "Income" },
      { type: "Section", group: "Expenses" },
    ],
  },
};

const v1 = validateProfitAndLossReport(validReport);
assert.strictEqual(v1.valid, true, "Valid report must pass validation");
console.log("✓ Valid report passed");

// 2. Non-object report
const v2 = validateProfitAndLossReport(null);
assert.strictEqual(v2.valid, false);
assert.match(v2.error, /not a valid JSON object/);
console.log("✓ Non-object rejection passed");

// 3. Missing Header
const v3 = validateProfitAndLossReport({ Columns: {}, Rows: {} });
assert.strictEqual(v3.valid, false);
assert.match(v3.error, /Missing required 'Header'/);
console.log("✓ Missing Header rejection passed");

// 4. Invalid ReportName
const v4 = validateProfitAndLossReport({
  Header: { ReportName: "BalanceSheet" },
  Columns: validReport.Columns,
  Rows: validReport.Rows,
});
assert.strictEqual(v4.valid, false);
assert.match(v4.error, /Invalid ReportName/);
console.log("✓ Invalid ReportName rejection passed");

// 5. Missing Columns
const v5 = validateProfitAndLossReport({
  Header: { ReportName: "ProfitAndLoss" },
  Rows: validReport.Rows,
});
assert.strictEqual(v5.valid, false);
assert.match(v5.error, /Missing or invalid 'Columns.Column'/);
console.log("✓ Missing Columns rejection passed");

// 6. Insufficient Columns (< 2)
const v6 = validateProfitAndLossReport({
  Header: { ReportName: "ProfitAndLoss" },
  Columns: { Column: [{ ColTitle: "", ColType: "Account" }] },
  Rows: validReport.Rows,
});
assert.strictEqual(v6.valid, false);
assert.match(v6.error, /Insufficient columns/);
console.log("✓ Insufficient columns rejection passed");

// 7. No monthly data columns (only Account and Total)
const v7 = validateProfitAndLossReport({
  Header: { ReportName: "ProfitAndLoss" },
  Columns: {
    Column: [
      { ColTitle: "", ColType: "Account" },
      { ColTitle: "Total", ColType: "Money" },
    ],
  },
  Rows: validReport.Rows,
});
assert.strictEqual(v7.valid, false);
assert.match(v7.error, /No monthly data columns identified/);
console.log("✓ Missing monthly columns rejection passed");

// 8. Missing Rows
const v8 = validateProfitAndLossReport({
  Header: { ReportName: "ProfitAndLoss" },
  Columns: validReport.Columns,
});
assert.strictEqual(v8.valid, false);
assert.match(v8.error, /Missing required 'Rows'/);
console.log("✓ Missing Rows rejection passed");

// 9. Empty Rows array
const v9 = validateProfitAndLossReport({
  Header: { ReportName: "ProfitAndLoss" },
  Columns: validReport.Columns,
  Rows: { Row: [] },
});
assert.strictEqual(v9.valid, false);
assert.match(v9.error, /contains empty or missing financial rows/);
console.log("✓ Empty Rows rejection passed");

console.log("\nAll 9 schema validation unit tests PASSED successfully.");
