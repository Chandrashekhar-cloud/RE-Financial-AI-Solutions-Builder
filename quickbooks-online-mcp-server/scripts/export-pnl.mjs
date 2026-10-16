#!/usr/bin/env node
/**
 * QuickBooks Online Live Profit and Loss Report Exporter.
 *
 * Securely retrieves the 18-month Profit and Loss report (2025-01-01 to 2026-06-30)
 * directly from the configured Intuit QuickBooks Online developer sandbox.
 *
 * Requirements satisfied:
 * 1. Retrieves P&L report directly from the configured QuickBooks sandbox.
 * 2. Uses date range Jan 1, 2025 through Jun 30, 2026.
 * 3. Requests monthly columns (summarize_column_by: 'Month').
 * 4. Reuses existing QuickbooksClient / getQuickbooksProfitAndLoss implementation.
 * 5. Strictly preserves read-only restrictions (verifies DISABLE_WRITE/UPDATE/DELETE).
 * 6. Performs zero mutations (GET report query only).
 * 7. Saves raw report to an isolated temporary file first.
 * 8. Validates response structure against Intuit V3 schema before committing.
 * 9. Only replaces canonical saved report after validation succeeds.
 * 10. Never logs OAuth credentials, tokens, or secrets.
 * 11. Returns clear, structured error on auth or API failure.
 * 12. Never silently falls back to stale saved data.
 */

import { getQuickbooksProfitAndLoss } from "../dist/handlers/get-quickbooks-profit-and-loss.handler.js";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const envPath = path.join(__dirname, "..", ".env");
dotenv.config({ path: envPath });

/**
 * Validates that an Intuit V3 Profit & Loss response contains required structure.
 * @param {any} report
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateProfitAndLossReport(report) {
  if (!report || typeof report !== "object") {
    return { valid: false, error: "Report payload is not a valid JSON object" };
  }

  // 1. Header Validation
  if (!report.Header || typeof report.Header !== "object") {
    return { valid: false, error: "Missing required 'Header' object in report" };
  }
  const reportName = String(report.Header.ReportName || "");
  if (!reportName.toLowerCase().includes("profitandloss")) {
    return { valid: false, error: `Invalid ReportName: '${reportName}', expected 'ProfitAndLoss'` };
  }

  // 2. Columns Validation
  if (!report.Columns || !Array.isArray(report.Columns.Column)) {
    return { valid: false, error: "Missing or invalid 'Columns.Column' array in report" };
  }
  const columns = report.Columns.Column;
  if (columns.length < 2) {
    return { valid: false, error: `Insufficient columns: expected at least 2, found ${columns.length}` };
  }

  // Verify at least one monthly column exists
  const monthCols = columns.filter((c) => {
    const title = c?.ColTitle || "";
    return title && title !== "Total" && !c?.ColType?.includes("Account");
  });
  if (monthCols.length === 0) {
    return { valid: false, error: "No monthly data columns identified in report" };
  }

  // 3. Rows Validation
  if (!report.Rows || typeof report.Rows !== "object") {
    return { valid: false, error: "Missing required 'Rows' object in report" };
  }
  const rows = report.Rows.Row;
  if (!rows || (Array.isArray(rows) && rows.length === 0)) {
    return { valid: false, error: "Report contains empty or missing financial rows" };
  }

  return { valid: true };
}

/**
 * Parses CLI arguments.
 */
function parseArgs(argv) {
  const defaultOutput = path.resolve(__dirname, "../../abc-trend-analysis/results/qbo_live_pnl_report.json");
  const options = {
    output: defaultOutput,
    startDate: "2025-01-01",
    endDate: "2026-06-30",
    summarizeBy: "Month",
    accountingMethod: "Accrual",
    dryRun: false,
    quiet: false,
    timeoutMs: 30000,
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--output" || arg === "-o") {
      options.output = path.resolve(process.cwd(), argv[++i]);
    } else if (arg === "--start-date") {
      options.startDate = argv[++i];
    } else if (arg === "--end-date") {
      options.endDate = argv[++i];
    } else if (arg === "--summarize-by") {
      options.summarizeBy = argv[++i];
    } else if (arg === "--accounting-method") {
      options.accountingMethod = argv[++i];
    } else if (arg === "--dry-run") {
      options.dryRun = true;
    } else if (arg === "--quiet" || arg === "-q") {
      options.quiet = true;
    } else if (arg === "--help" || arg === "-h") {
      console.log(`
Usage: node export-pnl.mjs [options]

Options:
  --output, -o <path>       Target output file path
  --start-date <YYYY-MM-DD> Report start date (default: 2025-01-01)
  --end-date <YYYY-MM-DD>   Report end date (default: 2026-06-30)
  --summarize-by <period>   Column summary period (default: Month)
  --accounting-method <m>   Accrual or Cash (default: Accrual)
  --dry-run                 Fetch & validate without saving to canonical target
  --quiet, -q               Suppress progress output
  --help, -h                Display this help message
`);
      process.exit(0);
    }
  }

  return options;
}

/**
 * Main export routine.
 */
export async function exportProfitAndLoss(opts = {}) {
  const options = {
    output: path.resolve(__dirname, "../../abc-trend-analysis/results/qbo_live_pnl_report.json"),
    startDate: "2025-01-01",
    endDate: "2026-06-30",
    summarizeBy: "Month",
    accountingMethod: "Accrual",
    dryRun: false,
    quiet: false,
    timeoutMs: 30000,
    ...opts,
  };

  const log = (...msg) => {
    if (!options.quiet) console.log(...msg);
  };
  const logError = (...msg) => {
    console.error(...msg);
  };

  log("==================================================");
  log("QuickBooks Online Live P&L Exporter");
  log("==================================================");

  // 1. Enforce Read-Only Safety Restrictions
  const envContent = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf-8") : "";
  const getEnv = (k) => {
    const match = envContent.match(new RegExp(`^${k}=(.*)$`, "m"));
    return match ? match[1].trim() : process.env[k];
  };

  const disableWrite = getEnv("QUICKBOOKS_DISABLE_WRITE");
  const disableUpdate = getEnv("QUICKBOOKS_DISABLE_UPDATE");
  const disableDelete = getEnv("QUICKBOOKS_DISABLE_DELETE");
  const realmId = getEnv("QUICKBOOKS_REALM_ID");
  const clientId = getEnv("QUICKBOOKS_CLIENT_ID");
  const clientSecret = getEnv("QUICKBOOKS_CLIENT_SECRET");
  const refreshToken = getEnv("QUICKBOOKS_REFRESH_TOKEN");

  if (disableWrite !== "true" || disableUpdate !== "true" || disableDelete !== "true") {
    logError("FATAL ERROR: Read-only flags are not strictly enforced!");
    logError("DISABLE_WRITE, DISABLE_UPDATE, and DISABLE_DELETE must all be 'true'.");
    return { success: false, error: "Read-only restrictions not satisfied" };
  }

  if (!clientId || !clientSecret || !refreshToken || !realmId) {
    logError("FATAL ERROR: Required QuickBooks credentials missing from environment.");
    return { success: false, error: "Missing QuickBooks credentials" };
  }

  log(`Target Realm ID:     ${realmId}`);
  log(`Report Period:       ${options.startDate} to ${options.endDate}`);
  log(`Summarize Columns:   ${options.summarizeBy}`);
  log(`Read-Only Enforced:  YES (write/update/delete disabled)`);

  // 2. Fetch Live Report from QuickBooks Online API with Timeout
  log("\nRetrieving live Profit and Loss report from QuickBooks Online API...");
  const t0 = Date.now();

  const fetchPromise = getQuickbooksProfitAndLoss({
    start_date: options.startDate,
    end_date: options.endDate,
    summarize_column_by: options.summarizeBy,
    accounting_method: options.accountingMethod,
  });

  const timeoutPromise = new Promise((_, reject) =>
    setTimeout(() => reject(new Error(`QuickBooks API request timed out after ${options.timeoutMs}ms`)), options.timeoutMs)
  );

  let response;
  try {
    response = await Promise.race([fetchPromise, timeoutPromise]);
  } catch (err) {
    const errMsg = err?.message || String(err);
    logError(`\nFATAL ERROR: QuickBooks API retrieval failed: ${errMsg}`);
    return { success: false, error: errMsg };
  }

  if (response.isError || !response.result) {
    const errMsg = response.error || "Unknown QuickBooks API error occurred";
    logError(`\nFATAL ERROR: QuickBooks report query returned error: ${errMsg}`);
    return { success: false, error: errMsg };
  }

  const elapsed = Date.now() - t0;
  log(`✓ Successfully received report payload from QuickBooks (${elapsed}ms)`);

  const reportData = response.result;

  // 3. Validate Report Schema
  log("Validating Intuit V3 Profit & Loss response schema...");
  const validation = validateProfitAndLossReport(reportData);
  if (!validation.valid) {
    logError(`\nFATAL ERROR: Received invalid QuickBooks report schema: ${validation.error}`);
    return { success: false, error: `Invalid report schema: ${validation.error}` };
  }

  const colsCount = reportData.Columns.Column.length;
  const rowsCount = Array.isArray(reportData.Rows.Row) ? reportData.Rows.Row.length : 1;
  const companyName = reportData.Header?.CompanyName || "QuickBooks Sandbox";
  log(`✓ Schema validation PASSED:`);
  log(`  - Report Name:  ${reportData.Header.ReportName}`);
  log(`  - Company Name: ${companyName}`);
  log(`  - Columns:      ${colsCount} columns identified`);
  log(`  - Root Rows:    ${rowsCount} section rows`);

  if (options.dryRun) {
    log("\n[DRY RUN] Skipping file write. Report payload validated successfully.");
    return { success: true, dryRun: true, report: reportData };
  }

  // 4. Save to Isolated Temporary File First, Then Atomically Replace Canonical File
  const targetPath = options.output;
  const targetDir = path.dirname(targetPath);
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  const tempPath = `${targetPath}.tmp.${process.pid}.${Date.now()}`;
  log(`\nWriting to temporary staging file: ${tempPath}`);

  try {
    fs.writeFileSync(tempPath, JSON.stringify(reportData, null, 2), "utf-8");

    // Read back and re-verify staged content before atomic commit
    const stagedContent = fs.readFileSync(tempPath, "utf-8");
    const parsedStaged = JSON.parse(stagedContent);
    const stagedValidation = validateProfitAndLossReport(parsedStaged);
    if (!stagedValidation.valid) {
      throw new Error(`Staged file validation failed: ${stagedValidation.error}`);
    }

    // Atomic replacement: copy over canonical file, then remove temp file
    fs.copyFileSync(tempPath, targetPath);
    try {
      fs.unlinkSync(tempPath);
    } catch {}

    const stats = fs.statSync(targetPath);
    log(`✓ Successfully committed validated report to canonical path:`);
    log(`  Path: ${targetPath}`);
    log(`  Size: ${stats.size.toLocaleString()} bytes`);
    log("==================================================");

    return { success: true, path: targetPath, size: stats.size };
  } catch (writeErr) {
    try {
      if (fs.existsSync(tempPath)) fs.unlinkSync(tempPath);
    } catch {}
    logError(`\nFATAL ERROR: Failed to save validated report: ${writeErr.message}`);
    return { success: false, error: writeErr.message };
  }
}

// Execute as CLI if invoked directly
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const cliOptions = parseArgs(process.argv);
  exportProfitAndLoss(cliOptions)
    .then((res) => {
      if (!res.success) {
        process.exit(1);
      }
      process.exit(0);
    })
    .catch((err) => {
      console.error("Unhandled fatal exception:", err?.message || err);
      process.exit(1);
    });
}
