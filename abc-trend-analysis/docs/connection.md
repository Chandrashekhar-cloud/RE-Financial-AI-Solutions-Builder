# QuickBooks Online MCP Connection Architecture
**RE Financial Services — AI Solutions Builder Assignment (Task 1 & Task 3)**

---

## 1. Chosen Approach vs. Rejected Alternatives

To connect Claude to QuickBooks Online securely and reliably, three potential architectures were evaluated:

| Architecture Option | Technical Evaluation & Trade-Offs | Architectural Decision |
| :--- | :--- | :--- |
| **Option A: Official Intuit MCP Server (TypeScript / Node.js)** | • Native Model Context Protocol (JSON-RPC over stdio).<br>• Official Intuit OAuth 2.0 SDK with automated token lifecycle management.<br>• Standardized schemas for queries, reports, and accounts.<br>• Native runtime flag suppression for mutation safety. | **CHOSEN** |
| **Option B: Custom Ad-Hoc Python REST Wrapper** | • High maintenance burden as Intuit V3/V4 REST endpoints evolve.<br>• Requires implementing bespoke OAuth token refresh, state storage, and MCP protocol serialization from scratch.<br>• Risk of subtle protocol incompatibilities with Claude Desktop/Code. | **REJECTED** |
| **Option C: Third-Party Middleware / Cloud Brokers** | • Introduces external proprietary vendor dependency.<br>• Opaque credential storage (credentials reside on third-party servers).<br>• Vendor lock-in, recurring SaaS licensing fees, and compliance risks. | **REJECTED** |

### Defense of Chosen Method
The **official Intuit Model Context Protocol (MCP) server** (`quickbooks-online-mcp-server`) was selected because it provides native compatibility with Claude Desktop and Claude Code via JSON-RPC, adheres to Intuit's official OAuth 2.0 security protocols, and permits direct local process execution without routing client financial data through intermediate third-party brokers.

---

## 2. OAuth 2.0 Configuration & Localhost Callback

QuickBooks Online requires OAuth 2.0 3-legged authorization for API and MCP access. The connection was established using an Intuit Developer App configured as follows:

1. **Intuit Developer Portal App:**
   - App Type: QuickBooks Online Accounting.
   - Target Scope: `com.intuit.quickbooks.accounting` (Accounting read/write API access).
   - Redirect URI: `http://localhost:8000/callback` (Standard local loopback for OAuth flow).
2. **Authorization Handshake:**
   - The user authorizes the Intuit app via the standard Intuit OAuth consent page in the browser.
   - Upon authorization, Intuit redirects to `http://localhost:8000/callback` with an authorization code and `realmId`.
   - The local helper exchanges the authorization code for an initial Bearer Access Token (60-minute expiry) and Refresh Token (100-day rolling expiry, 5-year maximum).
3. **Dedicated Developer Sandbox:**
   - Sandbox Company: `Sandbox Company US 6d74`
   - Realm ID: `9341458481035247`
   - Target Environment: `sandbox` (`https://sandbox-quickbooks.api.intuit.com/v3/company/`)

---

## 3. Credential Storage & Safe Submission Boundary

### Credential Protection Outside the Submission Package
* **Source Control Exclusion:** All `.env` files, token storage caches, and credential backups are strictly excluded from git tracking via `.gitignore` and omitted from all submission ZIP packages.
* **Template Distribution:** A sanitized [`.env.example`](../.env.example) template provides variable names and placeholder values without exposing active secrets.
* **No Hardcoded Secrets:** Client IDs, Client Secrets, Access Tokens, and Refresh Tokens are never checked into source code or printed in documentation.

### Read-Only Safety Flags for Claude Desktop MCP
The MCP server enforces runtime tool suppression flags configured in the host environment:

```ini
QUICKBOOKS_DISABLE_WRITE=true
QUICKBOOKS_DISABLE_UPDATE=true
QUICKBOOKS_DISABLE_DELETE=true
```

* When enabled, the registration guard withholds tools whose names match the recognized `create_`, `create-`, `update_`, `update-`, `delete_`, and `delete-` prefixes.
* The three safety flags are configured in Claude Desktop. Read-only company-information and Profit & Loss queries were successfully demonstrated without performing write operations.
* **Security limitation:** These flags provide a prototype-level safeguard. Complete mutation prevention requires auditing all exposed tool implementations and independently validating OAuth permissions.

---

## 4. Distinct Role of the Sandbox Importer & Ingestion Architecture

A critical design boundary exists between the read-only Claude Desktop MCP connection and the developer sandbox data ingestion:

* **Claude Desktop MCP Server:** Strictly read-only query bridge for Claude to inspect live accounting entities. Claude Desktop **does not** import Excel data through MCP.
* **Dedicated Sandbox Importer (`scripts/tools/seed_qbo_sandbox.py`):** An independent, idempotent Python administrative tool built specifically for the Task 3 stretch goal. It directly invokes Intuit's REST API using secure token exchange to ingest the 18-month ABC Inc dataset:
  - 86 planned accounts mapped and verified (82 custom accounts created, 4 matched pre-existing accounts). Reused on subsequent runs with 0 duplicates.
  - 18 balanced monthly Journal Entries (`ABC-2025-01` through `ABC-2026-06`), QBO IDs `145` through `162`.
  - Exact cent-level balance validation ($0.00 difference).
  - Pre-flight duplicate check by exact `DocNumber` before each POST operation.
  - 45-second timeout and 3-attempt exponential backoff for network resilience.
* **QuickBooks Report Adapter (`scripts/adapters/qbo_adapter.py`):** Normalizes the Intuit V3 ProfitAndLoss report API JSON into the canonical schema consumed by `scripts/engine.py`; 16 of 18 months match Excel exactly; the other 2 differ only by 3 pre-existing Intuit sandbox sample transactions ($300.00 and $391.25).

---

## 5. Team Hosting Architecture (Local Prototype vs. Cloud Production)

### Current Working Prototype (Developer Workstation)
* **Runtime:** Node.js stdio subprocess spawned locally by Claude Desktop.
* **Environment:** Developer sandbox (`QUICKBOOKS_ENVIRONMENT=sandbox`).
* **Scope:** Single developer laptop, single sandbox company realm.

### Proposed Production Team Hosting Architecture
In an accounting firm operating across the US and India, running MCP on individual laptops creates security vulnerabilities, credential proliferation, and synchronization issues. The production architecture deploys:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                            CLAUDE ENTERPRISE CLIENTS                              │
│       US Fractional CFOs (Okta SSO)             India Close Teams (Azure AD SSO)  │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │ Mutual TLS (mTLS) + OAuth 2.0 Bearer
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                       CENTRALIZED API GATEWAY & ROUTER                            │
│  • AWS Application Load Balancer / Cloudflare Access                              │
│  • Authenticates team members via Corporate Identity Provider (SAML/OIDC)         │
│  • Validates signed JWT claims; sets/overwrites verified X-Tenant-ID downstream   │
│  • Never trusts client-supplied tenant headers without cryptographic verification │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                   CONTAINERIZED MCP MICROSERVICES (AWS ECS)                       │
│  • Auto-scaling ECS Fargate task cluster running containerized Intuit MCP Server  │
│  • Stateless containers running in private VPC subnets with zero public IPs       │
│  • Strict read-only configuration injected at container start                     │
└───────────────────┬─────────────────────────────────────────────┬─────────────────┘
                    │ IAM Task Role                               │ Tenant Scoped
                    ▼                                             ▼
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│       CENTRAL SECRET MANAGER         │     │        TENANT DATA ISOLATION         │
│ • AWS Secrets Manager / Vault        │     │ • PostgreSQL with Row-Level Security │
│ • Client OAuth credentials partitioned│     │ • Client-scoped S3 buckets           │
│ • Automated 100-day token rotation   │     │ • Dedicated RealmID session binding  │
└──────────────────────────────────────┘     └──────────────────────────────────────┘
```

1. **Containerized Execution:** Deploy the Intuit MCP server as a containerized service on **AWS ECS Fargate** behind an Application Load Balancer in private subnets.
2. **Central Secret Management:** Store OAuth Client IDs, Client Secrets, and refresh tokens in **AWS Secrets Manager** with KMS encryption. Secrets are injected at runtime via IAM Task Roles; no `.env` files exist in container filesystems.
3. **Enterprise MCP Gateway & Authenticated Routing:** Team members authenticate via enterprise SSO (Okta / Azure AD). Claude connects over mutual TLS (mTLS). The gateway validates signed JWT claims, extracts the authorized tenant identity, and injects/overwrites the downstream `X-Tenant-ID` header. Client-supplied headers are never trusted without cryptographic signature verification.
4. **Audit Logging & Least Privilege:** All MCP tool calls are recorded to AWS CloudTrail / CloudWatch with caller identity, timestamp, tenant ID, and tool arguments for compliance.

---

## 6. Limitations of Current Prototype

1. **Single-Tenant Local Execution:** The current setup operates as a local stdio process for one developer. Multi-tenant session multiplexing requires the containerized cloud architecture.
2. **Token Lifecycle Management:** Intuit OAuth access tokens expire after 60 minutes; refresh tokens rotate on use; 100-day rolling expiry, 5-year maximum. In the local prototype, refresh token persistence is managed in local storage, whereas production requires a distributed token broker (Redis / Secrets Manager).
3. **API Rate Limiting:** Intuit imposes a 500 requests/min and 10 concurrent per company (realm) limit. Concurrent team closes require queue-based rate throttling.
4. **Sandbox Sample Transactions:** Intuit developer sandboxes include pre-seeded sample data. In `Sandbox Company US 6d74`, pre-existing sample records (Bill ID `90` in May 2026 and Invoice IDs `10` / `95` in June 2026) exist on the company-wide ledger. 16/18 periods match Excel exactly; 7 variances traced to pre-existing sandbox sample data. The ABC Inc dataset is isolated via dedicated Journal Entries (`ABC-2025-*` and `ABC-2026-*`).

---

## 7. Connection Verification & Sandbox Evidence

The QuickBooks Online sandbox connection was successfully verified via Claude connected to the local Intuit MCP server. The tool `get_company_info` was invoked in read-only mode to retrieve company metadata and subscription details without performing any mutation operations.

### Verification Screenshots
The live Claude-MCP execution screenshots are archived under [`docs/screenshots/`](screenshots/):

* [`mcp-server-running.png`](screenshots/mcp-server-running.png) — Claude Desktop connected to `quickbooks-online-mcp-server` over stdio.
* [`quickbooks-company-info.png`](screenshots/quickbooks-company-info.png) — Successful execution of read-only `get_company_info` tool call.
* [`quickbooks-company-info-details.png`](screenshots/quickbooks-company-info-details.png) — Full JSON response from sandbox company verifying company metadata and active developer subscription.
* [`intuit-app-overview.png`](screenshots/intuit-app-overview.png) — Intuit Developer Portal app dashboard displaying OAuth 2.0 configuration.
