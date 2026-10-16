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

An AI-assisted financial analysis solution integrating **Claude Desktop, Model Context Protocol (MCP), a QuickBooks Online MCP server, and Python-based financial processing**.

The project demonstrates structured AI-to-tool communication, financial data retrieval, numerical validation, trend analysis, anomaly detection, and automated evaluation.

## Key Features

| Feature | Description |
|---|---|
| **Claude + MCP** | Connect Claude Desktop to supported financial tools through MCP |
| **MCP Server** | Expose QuickBooks capabilities through structured tool calls |
| **QuickBooks Integration** | Retrieve company information and Profit & Loss reports |
| **Sandbox Support** | Support development and testing against the configured sandbox environment, where implemented |
| **Financial Validation** | Check calculations and financial data consistency |
| **Trend Analysis** | Compare financial performance across reporting periods |
| **Anomaly Detection** | Identify unusual financial patterns |
| **AI-Assisted Analysis** | Support financial interpretation through configured LLM workflows |
| **Automated Testing** | Validate application logic and supported workflows |
| **Reporting** | Generate analysis outputs and evaluation evidence |

## Architecture

```mermaid
flowchart TD
    U["User"] <--> C["Claude Desktop"]
    C <--> M["Model Context Protocol (MCP)"]
    M <--> S["QuickBooks Online MCP Server"]
    S <--> A["Authentication and API Client"]
    A <--> Q["QuickBooks Online API / Configured Sandbox"]

    Q -. "Financial data, where configured" .-> P["Python Financial Analysis Pipeline"]
    P --> N["Data Normalization"]
    N --> V["Numerical Validation"]
    V --> T["Trend and Anomaly Analysis"]
    T --> R["Reports and Insights"]

    classDef ai fill:#e8eaf6,stroke:#5c6bc0,color:#1a237e
    classDef integration fill:#e8f5e9,stroke:#43a047,color:#1b5e20
    classDef analysis fill:#fff3e0,stroke:#fb8c00,color:#e65100

    class U,C,M ai
    class S,A,Q integration
    class P,N,V,T,R analysis
```

*The MCP integration and financial analysis pipeline are distinct components. The diagram illustrates the major components; the exact data flow depends on the configured workflow.*

## Technology Stack

<div align="center">

| Technology | Role |
|---|---|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) | Financial analysis, validation, and reporting |
| ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white) | MCP server implementation |
| ![MCP](https://img.shields.io/badge/MCP-6E56CF?style=flat-square) | Standardized communication between AI clients and tools |
| ![Claude](https://img.shields.io/badge/Claude-D97757?style=flat-square) | AI assistant interface |
| ![QuickBooks](https://img.shields.io/badge/QuickBooks-2CA01C?style=flat-square&logo=intuit&logoColor=white) | Financial system integration |
| ![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white) | Python testing |
| ![Jest](https://img.shields.io/badge/Jest-C21325?style=flat-square&logo=jest&logoColor=white) | MCP server testing |
| ![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white) | Version control |

</div>

## Project Structure

```text
RE-Financial-AI-Solutions-Builder/
├── README.md
├── START_HERE.md
├── Project_Report.pdf
├── architecture.pdf
│
├── abc-trend-analysis/
│   ├── scripts/
│   ├── tests/
│   ├── evals/
│   ├── docs/
│   ├── results/
│   └── requirements.txt
│
├── quickbooks-online-mcp-server/
│   ├── src/
│   ├── tests/
│   ├── scripts/
│   └── package.json
│
└── scripts/
```

| Component | Responsibility |
|---|---|
| `abc-trend-analysis/` | Financial analysis, normalization, validation, and reporting |
| `tests/` | Automated tests |
| `evals/` | Evaluation cases and validation workflows |
| `docs/` | Technical documentation and screenshots |
| `results/` | Generated analysis and evaluation outputs |
| `quickbooks-online-mcp-server/` | QuickBooks MCP server integration |
| `quickbooks-online-mcp-server/src/` | MCP tools, handlers, API client, and server |
| `scripts/` | Project utilities and report generation |

## Testing & Verification

The recorded verification run reported **779 passing automated checks**.

| Test Suite | Reported Result |
|---|---:|
| Python tests | 131 passed |
| MCP server Jest tests | 639 passed |
| Financial schema tests | 9 passed |
| **Total** | **779 passed** |

These figures describe the recorded verification run, not 779 live API integration tests or a code-coverage percentage. Verify the counts against the latest test results before publishing.

## Documentation

| Resource | Description |
|---|---|
| [Project Report](Project_Report.pdf) | Implementation, methodology, and verification |
| [Architecture Document](architecture.pdf) | System architecture and component relationships |
| [Getting Started](START_HERE.md) | Project setup instructions |
| [Financial Analysis Documentation](abc-trend-analysis/README.md) | Analysis pipeline |
| [MCP Server Documentation](quickbooks-online-mcp-server/README.md) | QuickBooks MCP integration |
| [Screenshots](abc-trend-analysis/docs/screenshots/) | Demonstration evidence |
| [Evaluation Results](abc-trend-analysis/results/) | Analysis and evaluation artifacts |

## Getting Started

**Prerequisites:** Python, Node.js, npm, and the required credentials for live QuickBooks integration.

Clone the repository:

```bash
git clone https://github.com/Chandrashekhar-cloud/RE-Financial-AI-Solutions-Builder.git
cd RE-Financial-AI-Solutions-Builder
```

Follow [START_HERE.md](START_HERE.md) for the project-specific setup instructions.

Configure credentials locally and consult each component's documentation for dependencies and execution commands.

Live QuickBooks workflows require valid credentials and appropriate access. Sandbox usage depends on the project's configured environment.

## Security

- Never commit `.env` files, OAuth tokens, API secrets, or private keys.
- Do not publish confidential financial statements or customer information.
- Review screenshots, reports, and generated data files before publishing.
- Use appropriately scoped credentials when connecting to QuickBooks Online.
- Verify whether the configured QuickBooks environment is a sandbox or a production company before running operations.

**Note:** The MCP server supports a broader range of QuickBooks operations than the read-only Profit & Loss demonstration. Available operations depend on the implemented tools and configured permissions.

## Author

**Chandrashekhar H S**

Computer Science Engineering | AI & ML

[GitHub Profile](https://github.com/Chandrashekhar-cloud)

---

<div align="center">

**AI · MCP · Claude · QuickBooks · Financial Intelligence**

*Connecting AI with real-world financial workflows.*

</div>
