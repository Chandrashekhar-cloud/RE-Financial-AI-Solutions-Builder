<div align="center">

# RE Financial AI Solutions Builder

### AI-Powered Financial Intelligence with MCP & QuickBooks Online

Connecting AI assistants with financial systems through intelligent tools, financial analysis, and automated validation.

<br>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![MCP](https://img.shields.io/badge/Model_Context_Protocol-6E56CF?style=for-the-badge)
![MCP Server](https://img.shields.io/badge/MCP_Server-4B5563?style=for-the-badge)
![Claude](https://img.shields.io/badge/Claude_AI-D97757?style=for-the-badge)
![QuickBooks](https://img.shields.io/badge/QuickBooks_Online-2CA01C?style=for-the-badge&logo=intuit&logoColor=white)

<br>

[Project Report](Project_Report.pdf) · [Architecture](architecture.pdf) · [Getting Started](START_HERE.md)

</div>

---

## Overview

An AI-assisted financial analysis prototype combining **Claude Desktop, Model Context Protocol (MCP), a QuickBooks Online MCP server, and a Python-based financial analysis pipeline**.

The project demonstrates AI-to-tool communication, QuickBooks Sandbox report retrieval, deterministic financial calculations, trend analysis, anomaly checks, and automated evaluation.

## Key Features

| Feature | Description |
|---|---|
| **Claude + MCP** | Connect Claude Desktop to supported financial tools through MCP |
| **MCP Server** | Expose implemented QuickBooks capabilities through structured tool calls |
| **QuickBooks Integration** | Retrieve company information and a read-only Profit & Loss report in the configured Sandbox environment |
| **Financial Validation** | Check calculations and financial-data consistency |
| **Trend Analysis** | Compare financial performance across reporting periods |
| **Anomaly Detection** | Flag unusual financial patterns for review |
| **AI-Assisted Analysis** | Generate commentary grounded in structured analysis outputs |
| **Automated Testing** | Test the Python analysis workflow and MCP server |
| **Reporting** | Generate analysis outputs and evaluation evidence |

## Architecture

The project contains **two related but distinct workflows**. The MCP workflow demonstrates QuickBooks connectivity through Claude Desktop. The Python pipeline analyzes a workbook or saved/normalized report; it should not be interpreted as automatically receiving data from the MCP server unless a specific export/import step is configured.

```mermaid
flowchart TB
    subgraph MCP["Workflow A — QuickBooks MCP connection"]
        U["User"] <--> CD["Claude Desktop"]
        CD <--> MCP["Model Context Protocol"]
        MCP <--> QMS["QuickBooks Online MCP Server"]
        QMS <--> API["Authentication and API Client"]
        API <--> QB["QuickBooks Online Sandbox API"]
        QB --> EVID["Saved connection and report evidence"]
    end

    subgraph PY["Workflow B — Financial trend analysis"]
        INPUT["Workbook or saved/normalized financial report"]
        INPUT --> NORM["Data normalization"]
        NORM --> ENG["Deterministic Python calculation engine"]
        ENG --> VAL["Reconciliation and validation"]
        VAL --> OUT["analysis.json and report.md"]
        OUT --> SKILL["Claude Skill / grounded commentary"]
        SKILL --> FINAL["Insights and evaluation results"]
    end

    classDef client fill:#e8eaf6,stroke:#5c6bc0,color:#1a237e
    classDef integration fill:#e8f5e9,stroke:#43a047,color:#1b5e20
    classDef analysis fill:#fff3e0,stroke:#fb8c00,color:#7f3b00

    class U,CD,MCP client
    class QMS,API,QB,EVID integration
    class INPUT,NORM,ENG,VAL,OUT,SKILL,FINAL analysis
```

*The diagram separates the demonstrated MCP connection from the Python analysis pipeline. The documented AWS multi-tenant architecture is a proposed roadmap, not a deployed production service.*

## Technology Stack

| Technology | Role |
|---|---|
| Python | Financial analysis, validation, and reporting |
| TypeScript | MCP server implementation |
| Model Context Protocol (MCP) | Standardized communication between an AI client and tools |
| Claude Desktop | AI assistant interface for the MCP demonstration |
| QuickBooks Online Sandbox | Configured financial-system integration environment |
| Pytest | Python test suite |
| Jest | MCP server test suite |
| GitHub | Version control and project documentation |

## Project Structure

```text
RE-Financial-AI-Solutions-Builder/
├── README.md
├── START_HERE.md
├── Project_Report.pdf
├── architecture.pdf
├── abc-trend-analysis/
│   ├── scripts/
│   ├── tests/
│   ├── evals/
│   ├── docs/
│   ├── results/
│   └── requirements.txt
├── quickbooks-online-mcp-server/
│   ├── src/
│   ├── tests/
│   ├── scripts/
│   └── package.json
└── scripts/
```

| Component | Responsibility |
|---|---|
| `abc-trend-analysis/` | Financial analysis, normalization, validation, and reporting |
| `abc-trend-analysis/tests/` | Python tests |
| `abc-trend-analysis/evals/` | Golden-case and commentary evaluation workflows |
| `abc-trend-analysis/docs/` | Technical documentation and screenshots |
| `abc-trend-analysis/results/` | Generated analysis and evaluation artifacts |
| `quickbooks-online-mcp-server/` | QuickBooks MCP server integration |
| `quickbooks-online-mcp-server/src/` | MCP tools, handlers, API client, and server |
| `scripts/` | Project utilities and pipeline launchers |

## Testing & Verification

The attached project report records the following verification results. These are recorded results for the documented run and should not be interpreted as a guarantee that every test passes in every environment.

| Check | Recorded result |
|---|---:|
| Python tests | 119 passed |
| MCP server Jest tests | 639 passed across 35 suites |
| Golden evaluation | 9/9 cases; 110/110 recorded score |
| Commentary evaluation | 100/100 |
| Offline pipeline | Six stages passed |
| Financial reconciliation | 126/126 checks passed |

Test counts can change as the code and test suite evolve. If you update the repository after the submitted ZIP/report was created, keep the README and report explicit about which verification run each count describes.

## Documentation

| Resource | Description |
|---|---|
| [Project Report](Project_Report.pdf) | Implementation, methodology, and recorded verification |
| [Architecture Document](architecture.pdf) | Prototype architecture, security considerations, and proposed scaling roadmap |
| [Getting Started](START_HERE.md) | Project setup instructions |
| [Financial Analysis Documentation](abc-trend-analysis/README.md) | Analysis pipeline |
| [MCP Server Documentation](quickbooks-online-mcp-server/README.md) | QuickBooks MCP integration |
| [Screenshots](abc-trend-analysis/docs/screenshots/) | Demonstration evidence |
| [Evaluation Results](abc-trend-analysis/results/) | Analysis and evaluation artifacts |

## Getting Started

**Prerequisites:** Python, Node.js, npm, and credentials configured for any live QuickBooks workflow.

```bash
git clone https://github.com/Chandrashekhar-cloud/RE-Financial-AI-Solutions-Builder.git
cd RE-Financial-AI-Solutions-Builder
```

Follow [START_HERE.md](START_HERE.md) for the project-specific setup instructions.

Configure credentials locally and consult each component's documentation for dependencies and execution commands. Use the offline pipeline when you want to reproduce the financial analysis without changing QuickBooks Sandbox data.

Live QuickBooks workflows require valid credentials and appropriate access. Sandbox usage depends on the configured environment.

## Security & Scope

- Never commit `.env` files, OAuth tokens, API secrets, or private keys.
- Do not publish confidential financial statements or customer information.
- Review screenshots, reports, and generated data files before publishing.
- Use appropriately scoped credentials when connecting to QuickBooks Online.
- Confirm whether the configured QuickBooks environment is Sandbox or production before running operations.
- Read-only behavior depends on the implemented server safeguards and configured permissions; do not assume every available MCP operation is read-only.
- AWS multi-tenant hosting and isolation are proposed architecture, not deployed infrastructure.

## Author

**Chandrashekhar H S**

Computer Science Engineering | AI & ML

[GitHub Profile](https://github.com/Chandrashekhar-cloud)

---

<div align="center">

**AI · MCP · Claude · QuickBooks · Financial Intelligence**

*Connecting AI with real-world financial workflows.*

</div>
