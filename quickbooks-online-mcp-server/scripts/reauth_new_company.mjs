import OAuthClient from "intuit-oauth";
import http from "http";
import crypto from "crypto";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";
import open from "open";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const envPath = path.join(__dirname, "..", ".env");
dotenv.config({ path: envPath });

const clientId = process.env.QUICKBOOKS_CLIENT_ID;
const clientSecret = process.env.QUICKBOOKS_CLIENT_SECRET;
const port = 8000;

if (!clientId || !clientSecret) {
  console.error("Missing CLIENT_ID or CLIENT_SECRET in .env");
  process.exit(1);
}

const oauthClient = new OAuthClient({
  clientId,
  clientSecret,
  environment: "sandbox",
  redirectUri: `http://localhost:${port}/callback`,
});

const expectedState = crypto.randomBytes(24).toString("hex");

const server = http.createServer(async (req, res) => {
  if (!req.url?.startsWith("/callback")) {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not Found. Waiting for QuickBooks OAuth callback at /callback");
    return;
  }

  const callbackUrl = new URL(req.url, `http://localhost:${port}`);
  const incomingState = callbackUrl.searchParams.get("state");
  const incomingRealmId = callbackUrl.searchParams.get("realmId");

  if (incomingState !== expectedState) {
    res.writeHead(400, { "Content-Type": "text/plain" });
    res.end("Invalid state parameter.");
    return;
  }

  try {
    const response = await oauthClient.createToken(req.url);
    const tokenObj = oauthClient.getToken();
    const newRealmId = incomingRealmId || tokenObj.realmId || response?.token?.realmId;
    const newRefreshToken = tokenObj.refresh_token || response?.token?.refresh_token;

    if (!newRefreshToken) {
      throw new Error("No refresh token received in OAuth response.");
    }

    // Ensure original configuration is backed up before modification
    const backupPath = path.join(__dirname, "..", ".env.c2f2.bak");
    if (!fs.existsSync(backupPath)) {
      fs.copyFileSync(envPath, backupPath);
      console.log("✓ Created backup of original configuration at .env.c2f2.bak");
    }

    // Update .env safely without printing tokens
    const envContent = fs.readFileSync(envPath, "utf-8");
    const envLines = envContent.split("\n");

    const updateEnvVar = (name, value) => {
      const idx = envLines.findIndex((line) => line.startsWith(`${name}=`));
      if (idx !== -1) {
        envLines[idx] = `${name}=${value}`;
      } else {
        envLines.push(`${name}=${value}`);
      }
    };

    updateEnvVar("QUICKBOOKS_REALM_ID", newRealmId);
    updateEnvVar("QUICKBOOKS_REFRESH_TOKEN", newRefreshToken);
    // Explicitly enforce read-only safety flags
    updateEnvVar("QUICKBOOKS_DISABLE_WRITE", "true");
    updateEnvVar("QUICKBOOKS_DISABLE_UPDATE", "true");
    updateEnvVar("QUICKBOOKS_DISABLE_DELETE", "true");

    fs.writeFileSync(envPath, envLines.join("\n"), { mode: 0o600 });

    const isTargetRealm = newRealmId === "9341458481035247";

    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(`
      <html>
        <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 15vh; background-color: #0f172a; color: #f8fafc;">
          <h2 style="color: #10B981;">✓ Successfully Connected to QuickBooks Sandbox!</h2>
          <p>Connected Realm ID: <b>${newRealmId}</b></p>
          <p style="color: ${isTargetRealm ? '#10B981' : '#F59E0B'}; font-weight: bold;">
            ${isTargetRealm ? '✓ Verified Target: Sandbox Company US 6-d74' : '⚠ Connected Realm differs from 9341458481035247'}
          </p>
          <p style="color: #94A3B8;">Tokens updated securely in .env with read-only flags preserved. You may close this tab.</p>
        </body>
      </html>
    `);

    console.log("\n========================================================");
    console.log("✓ OAuth authorization successful!");
    console.log(`Connected Realm ID: ${newRealmId}`);
    if (isTargetRealm) {
      console.log("✓ Verified Target: Sandbox Company US 6-d74 (9341458481035247)");
    } else {
      console.log(`⚠ Warning: Connected to Realm ID ${newRealmId} instead of 9341458481035247`);
    }
    console.log("Configuration updated safely in .env (read-only flags enforced, secrets never exposed).");
    console.log("========================================================\n");

    setTimeout(() => {
      server.close();
      process.exit(0);
    }, 1500);
  } catch (err) {
    console.error("\n✗ Token exchange failed:", err.message || err);
    res.writeHead(500, { "Content-Type": "text/plain" });
    res.end("Authentication failed. Please check console.");
    setTimeout(() => {
      server.close();
      process.exit(1);
    }, 1500);
  }
});

server.listen(port, "::", async () => {
  const authUri = oauthClient
    .authorizeUri({
      scope: [OAuthClient.scopes.Accounting],
      state: expectedState,
    })
    .toString();

  console.log("========================================================");
  console.log("QuickBooks Sandbox Authorization Server Active");
  console.log("Listening on http://localhost:8000/callback");
  console.log("========================================================");
  console.log("Authorization URL:\n");
  console.log(authUri);
  console.log("\nWaiting for browser callback...");
  console.log("Please select 'Sandbox Company US 6-d74' when prompted.");
  console.log("========================================================\n");

  try {
    await open(authUri);
  } catch {
    // fallback
  }
});
