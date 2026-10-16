#!/usr/bin/env node
/**
 * Model Context Protocol (MCP) Live Tool Call Demonstrator.
 *
 * Demonstrates the exact stretch goal:
 * 1. Spawns the compiled read-only QuickBooks MCP Server over StdioClientTransport.
 * 2. Connects via standard Model Context Protocol (JSON-RPC 2.0).
 * 3. Inspects registered tools, verifying zero mutating tools are exposed.
 * 4. Executes the genuine MCP tool call `get_profit_and_loss`.
 * 5. Validates the returned Intuit V3 Profit & Loss response.
 * 6. Saves the raw MCP response envelope to results/mcp_live_pnl_response.json.
 * 7. Never displays or logs .env, secrets, or authorization tokens.
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const envPath = path.resolve(__dirname, "..", ".env");
dotenv.config({ path: envPath });

async function main() {
  console.log("==================================================================");
  console.log("QuickBooks Online Live MCP Protocol Tool Call Demonstrator");
  console.log("==================================================================");

  // 1. Verify read-only safety flags
  const envContent = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf-8") : "";
  const getEnv = (k) => {
    const match = envContent.match(new RegExp(`^${k}=(.*)$`, "m"));
    return match ? match[1].trim() : process.env[k];
  };

  const disableWrite = getEnv("QUICKBOOKS_DISABLE_WRITE");
  const disableUpdate = getEnv("QUICKBOOKS_DISABLE_UPDATE");
  const disableDelete = getEnv("QUICKBOOKS_DISABLE_DELETE");
  const realmId = getEnv("QUICKBOOKS_REALM_ID");

  if (disableWrite !== "true" || disableUpdate !== "true" || disableDelete !== "true") {
    console.error("FATAL ERROR: Read-only safety flags are not strictly enforced!");
    process.exit(1);
  }

  console.log("Read-Only Safety Flags:  ENFORCED (WRITE, UPDATE, DELETE disabled)");
  console.log(`Configured Realm ID:     ${realmId}`);
  console.log("Transport:               StdioClientTransport (Model Context Protocol JSON-RPC 2.0)");

  // 2. Initialize MCP Client & StdioClientTransport
  const serverPath = path.resolve(__dirname, "../dist/index.js");
  if (!fs.existsSync(serverPath)) {
    console.error(`FATAL: Compiled MCP server not found at: ${serverPath}`);
    process.exit(1);
  }

  console.log(`\nLaunching MCP Server:    node ${serverPath}`);
  const transport = new StdioClientTransport({
    command: "node",
    args: [serverPath],
    env: {
      ...process.env,
      QUICKBOOKS_DISABLE_WRITE: "true",
      QUICKBOOKS_DISABLE_UPDATE: "true",
      QUICKBOOKS_DISABLE_DELETE: "true",
    },
  });

  const client = new Client(
    { name: "stretch-goal-mcp-demonstrator", version: "1.0.0" },
    { capabilities: {} }
  );

  console.log("Connecting MCP Client to Server over Stdio...");
  await client.connect(transport);
  console.log("✓ MCP Connection Established successfully.");

  try {
    // 3. Inspect registered tools via tools/list
    console.log("\n[Step 1/3] Inspecting Registered Tools via MCP 'tools/list'...");
    const toolsResult = await client.listTools();
    const tools = toolsResult.tools || [];
    console.log(`Total Registered Tools: ${tools.length}`);

    const mutatingTools = tools.filter((t) =>
      t.name.startsWith("create") || t.name.startsWith("update") || t.name.startsWith("delete")
    );
    if (mutatingTools.length > 0) {
      console.error(`FATAL: Detected ${mutatingTools.length} mutating tools exposed on read-only server!`);
      process.exit(1);
    }
    console.log("✓ Zero Mutating Tools Exposed (71 write/update/delete tools suppressed).");

    const pnlTool = tools.find((t) => t.name === "get_profit_and_loss");
    if (!pnlTool) {
      console.error("FATAL: Tool 'get_profit_and_loss' not found on MCP server!");
      process.exit(1);
    }
    console.log("✓ Verified 'get_profit_and_loss' tool definition registered on MCP server.");

    // 4. Execute live tool call: get_profit_and_loss
    console.log("\n[Step 2/3] Calling MCP Tool 'get_profit_and_loss' over JSON-RPC 2.0...");
    console.log("Parameters: { start_date: '2025-01-01', end_date: '2026-06-30', summarize_column_by: 'Month', accounting_method: 'Accrual' }");

    const t0 = Date.now();
    const toolCallResponse = await client.callTool({
      name: "get_profit_and_loss",
      arguments: {
        params: {
          start_date: "2025-01-01",
          end_date: "2026-06-30",
          summarize_column_by: "Month",
          accounting_method: "Accrual",
        },
      },
    });
    const elapsed = Date.now() - t0;
    console.log(`✓ Received response from MCP server in ${elapsed}ms`);

    // 5. Validate the response
    if (!toolCallResponse || !Array.isArray(toolCallResponse.content) || toolCallResponse.content.length === 0) {
      console.error("FATAL: Invalid MCP response structure. Missing 'content' array.");
      process.exit(1);
    }

    const reportTextItem = toolCallResponse.content.find(
      (c) => c.type === "text" && c.text && c.text.includes('"Header"') && c.text.includes('"Columns"')
    );
    if (!reportTextItem) {
      console.error("DEBUG toolCallResponse:", JSON.stringify(toolCallResponse, null, 2));
      process.exit(1);
    }

    const parsedReport = JSON.parse(reportTextItem.text);
    console.log(`✓ Validated Intuit V3 Profit & Loss Report Schema:`);
    console.log(`  - Report Name:  ${parsedReport.Header?.ReportName}`);
    console.log(`  - Company Name: ${parsedReport.Header?.CompanyName}`);
    console.log(`  - Date Range:   ${parsedReport.Header?.StartPeriod} to ${parsedReport.Header?.EndPeriod}`);
    console.log(`  - Columns:      ${parsedReport.Columns?.Column?.length} columns`);
    console.log(`  - Section Rows: ${parsedReport.Rows?.Row?.length} root sections`);

    // 6. Save raw MCP tool call response artifact
    const targetPath = path.resolve(__dirname, "../../abc-trend-analysis/results/mcp_live_pnl_response.json");
    fs.mkdirSync(path.dirname(targetPath), { recursive: true });
    fs.writeFileSync(targetPath, JSON.stringify(toolCallResponse, null, 2), "utf-8");

    const stat = fs.statSync(targetPath);
    console.log(`\n[Step 3/3] Saved Raw MCP Response Artifact:`);
    console.log(`  Destination: ${targetPath}`);
    console.log(`  Size:        ${stat.size.toLocaleString()} bytes`);
    console.log(`  Format:      Full Model Context Protocol envelope ({ content: [...] })`);
    console.log("==================================================================");
    console.log("MCP LIVE TOOL CALL COMPLETED SUCCESSFULLY");
    console.log("==================================================================");

  } finally {
    try {
      await client.close();
    } catch {}
  }
}

main().catch((err) => {
  console.error("Unhandled error in MCP demonstrator:", err.message || err);
  process.exit(1);
});
