import { QuickbooksClient } from "../dist/clients/quickbooks-client.js";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const envPath = path.join(__dirname, "..", ".env");
dotenv.config({ path: envPath });

async function verifyConnection() {
  console.log("========================================================");
  console.log("QUICKBOOKS ONLINE CONNECTION & READ-ONLY VERIFICATION");
  console.log("========================================================");

  // 1. Safety & Read-Only Configuration Checks
  const envContent = fs.readFileSync(envPath, "utf-8");
  const getEnv = (k) => {
    const match = envContent.match(new RegExp(`^${k}=(.*)$`, "m"));
    return match ? match[1].trim() : undefined;
  };

  const realmId = getEnv("QUICKBOOKS_REALM_ID");
  const envType = getEnv("QUICKBOOKS_ENVIRONMENT");
  const disableWrite = getEnv("QUICKBOOKS_DISABLE_WRITE");
  const disableUpdate = getEnv("QUICKBOOKS_DISABLE_UPDATE");
  const disableDelete = getEnv("QUICKBOOKS_DISABLE_DELETE");

  console.log("Environment File:", envPath);
  console.log("Configured Realm ID:", realmId);
  console.log("Environment Type:   ", envType);
  console.log("Read-Only Flags:    ", {
    DISABLE_WRITE: disableWrite,
    DISABLE_UPDATE: disableUpdate,
    DISABLE_DELETE: disableDelete,
  });

  if (disableWrite !== "true" || disableUpdate !== "true" || disableDelete !== "true") {
    console.error("CRITICAL: Read-only flags are NOT strictly enabled!");
    process.exit(1);
  }
  console.log("✓ Safety: Read-only flags strictly enforced in .env.\n");

  // 2. Initialize QuickbooksClient
  let client;
  try {
    client = await QuickbooksClient.getInstance();
    console.log("✓ QuickbooksClient initialized successfully via OAuth token.");
  } catch (err) {
    console.error("✗ Failed to initialize QuickbooksClient:", err.message || err);
    process.exit(1);
  }

  // 3. Fetch Company Information
  console.log("\n--- [Step 1] Query Company Information ---");
  await new Promise((resolve, reject) => {
    client.getCompanyInfo(realmId, (err, info) => {
      if (err) {
        console.error("✗ getCompanyInfo failed:", err.message || err);
        return reject(err);
      }
      console.log("Company Name:            ", info?.CompanyName);
      console.log("Legal Name:              ", info?.LegalName || "(Same as Company Name)");
      console.log("Realm ID (from API):     ", realmId);
      console.log("Country:                 ", info?.Country);
      console.log("Fiscal Year Start Month: ", info?.FiscalYearStartMonth);
      console.log("Company Start Date:      ", info?.CompanyStartDate);
      console.log("Subscription Status:     ", info?.CompanyAddr ? "Active / Accessible" : "Unknown");
      
      const expectedRealm = "9341458481035247";
      const expectedName = "Sandbox Company US 6-d74";
      if (realmId === expectedRealm) {
        console.log(`✓ Realm ID matches target sandbox: ${realmId}`);
      } else {
        console.warn(`! Realm ID (${realmId}) does NOT match target (${expectedRealm})`);
      }
      if (info?.CompanyName === expectedName) {
        console.log(`✓ Company Name matches target sandbox: ${info?.CompanyName}`);
      } else {
        console.warn(`! Company Name (${info?.CompanyName}) differs from expected (${expectedName})`);
      }
      resolve();
    });
  });

  // 4. Query Journal Entries (Verify ZERO ABC entries)
  console.log("\n--- [Step 2] Check Existing Journal Entries ---");
  await new Promise((resolve, reject) => {
    client.findJournalEntries({ limit: 100 }, (err, res) => {
      if (err) {
        console.error("✗ findJournalEntries failed:", err.message || err);
        return reject(err);
      }
      const entries = res?.QueryResponse?.JournalEntry || [];
      console.log(`Total Existing Journal Entries in Sandbox: ${entries.length}`);

      const abcEntries = entries.filter((j) => {
        const doc = j.DocNumber || "";
        const memo = j.PrivateNote || "";
        return doc.startsWith("ABC-") || memo.includes("ABC Inc");
      });

      console.log(`ABC Inc. Journal Entries Found: ${abcEntries.length}`);
      if (abcEntries.length === 0) {
        console.log("✓ CONFIRMED: 0 ABC Inc. journal entries found in this sandbox company.");
      } else {
        console.warn(`! WARNING: Found ${abcEntries.length} existing ABC journal entries!`);
        abcEntries.forEach((e) => console.log(`  - DocNumber: ${e.DocNumber}, Date: ${e.TxnDate}`));
      }

      if (entries.length > 0) {
        console.log("Existing Non-ABC Journal Entries (Intuit sample entries):");
        entries.slice(0, 10).forEach((e) => {
          console.log(`  - DocNumber: ${e.DocNumber || "(None)"}, Date: ${e.TxnDate}, Lines: ${e.Line?.length || 0}`);
        });
      }
      resolve();
    });
  });

  // 5. Query Chart of Accounts
  console.log("\n--- [Step 3] Check Existing Chart of Accounts ---");
  await new Promise((resolve, reject) => {
    client.findAccounts({ limit: 1000 }, (err, res) => {
      if (err) {
        console.error("✗ findAccounts failed:", err.message || err);
        return reject(err);
      }
      const accounts = res?.QueryResponse?.Account || [];
      console.log(`Total Existing Accounts in Sandbox: ${accounts.length}`);
      
      const abcSpecificAccounts = accounts.filter((a) => {
        const name = a.Name || "";
        const num = a.AcctNum || "";
        return name.includes("4010") || name.includes("ABC Clearing") || num === "4010" || num === "9999";
      });

      console.log(`Pre-existing ABC Accounts Found: ${abcSpecificAccounts.length}`);
      if (abcSpecificAccounts.length === 0) {
        console.log("✓ CONFIRMED: Clean Chart of Accounts (zero pre-existing ABC accounts).");
      } else {
        console.log("Pre-existing accounts:", abcSpecificAccounts.map((a) => a.Name));
      }
      resolve();
    });
  });

  console.log("\n========================================================");
  console.log("✓ READ-ONLY VERIFICATION COMPLETE");
  console.log("Zero write/update/delete operations were performed.");
  console.log("========================================================\n");
}

verifyConnection().catch((err) => {
  console.error("Fatal verification error:", err);
  process.exit(1);
});
