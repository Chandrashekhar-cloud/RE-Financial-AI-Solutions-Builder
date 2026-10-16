<div align="center">

RE Financial AI Solutions Builder
AI-Powered Financial Intelligence with MCP & QuickBooks Online

Transform financial data into actionable insights through AI-assisted analysis, financial validation, trend detection, and intelligent reporting.

<br>









<br>

Project Report · Architecture Document · Source Code

</div>

📌 Overview

RE Financial AI Solutions Builder is an AI-assisted financial analysis project that integrates Model Context Protocol (MCP) with QuickBooks Online and a Python-based financial analysis pipeline.

The project demonstrates how an AI assistant can interact with financial systems through structured tools, retrieve company and Profit and Loss information, and support financial analysis through data normalization, numerical validation, trend analysis, anomaly detection, and reporting.

It combines financial-system integration with software engineering practices, automated testing, evaluation workflows, and technical documentation.

🎯 Project Objectives
Connect an AI assistant to financial-system capabilities through MCP.
Retrieve company information and financial reports from QuickBooks Online.
Process and normalize financial statement data.
Validate financial calculations and identify inconsistencies.
Analyze financial trends and flag potential anomalies.
Support financial interpretation through AI-assisted commentary where implemented.
Evaluate reliability using automated tests and structured validation.
✨ Key Features

<table> <tr> <td width="50%" valign="top">

🔌 MCP Integration

Connect Claude Desktop to QuickBooks capabilities through an MCP server.

💼 Financial Data Retrieval

Retrieve company information and Profit and Loss reports using the implemented QuickBooks integration.

🧮 Numerical Validation

Validate financial data, check calculations, and identify inconsistencies in supported workflows.

📊 Trend Analysis

Compare financial results across periods and identify significant movements.

</td> <td width="50%" valign="top">

🚨 Anomaly Detection

Identify unusual financial patterns using the implemented analysis and validation logic.

🤖 AI-Assisted Commentary

Generate financial explanations and commentary through supported LLM-assisted workflows.

🧪 Automated Testing

Use Python tests, MCP server tests, and evaluation cases to verify project behavior.

📄 Evidence & Reporting

Maintain technical documentation, generated reports, evaluation results, and demonstration screenshots.

</td> </tr> </table>

🏗️ System Architecture

The project combines an MCP-based financial-system integration with a financial analysis and evaluation pipeline.

flowchart TB
    U([User])

    subgraph AI["AI Interaction Layer"]
        C["Claude Desktop"]
        M["MCP Client / Protocol"]
    end

    subgraph Integration["Financial Integration Layer"]
        S["QuickBooks Online MCP Server"]
        A["Authentication & API Client"]
        Q[("QuickBooks Online API")]
    end

    subgraph Analysis["Financial Analysis Pipeline"]
        P["Python Analysis Pipeline"]
        N["Data Normalization"]
        V["Numerical Validation"]
        T["Trend & Anomaly Analysis"]
        L["LLM-Assisted Commentary"]
    end

    subgraph Outputs["Outputs & Verification"]
        R["Financial Reports"]
        E["Evaluation Results"]
        D["Documentation & Evidence"]
    end

    U --> C
    C <--> M
    M <--> S
    S --> A
    A <--> Q

    Q --> P
    P --> N
    N --> V
    V --> T
    T --> L

    L --> R
    V --> E
    T --> E
    R --> D
    E --> D

    classDef user fill:#e8f0fe,stroke:#4285f4,color:#202124
    classDef integration fill:#e8f5e9,stroke:#34a853,color:#202124
    classDef analysis fill:#fff3e0,stroke:#fb8c00,color:#202124
    classDef output fill:#f3e5f5,stroke:#8e24aa,color:#202124

    class U,C,M user
    class S,A,Q integration
    class P,N,V,T,L analysis
    class R,E,D output

The diagram represents the major project components. Exact execution paths depend on the workflow being run; the financial analysis pipeline and MCP integration are distinct components rather than a single always-running service.

🔄 How It Works
User request: The user asks Claude Desktop for company or financial information.
MCP communication: Claude uses the MCP protocol to discover and invoke an available tool.
Financial integration: The QuickBooks MCP server handles the relevant request and communicates with QuickBooks Online through its API client.
Data processing: Financial data is processed through the applicable normalization, analysis, and validation workflows.
Financial intelligence: Supported analysis components identify trends, flag anomalies, and produce AI-assisted commentary where configured.
Results: Reports, evaluation outputs, and supporting evidence make the results available for review.
🛠️ Technology Stack

<div align="center">

Technology	Purpose

	Financial analysis, validation, evaluation, and reporting

	QuickBooks MCP server implementation

	Structured communication between AI clients and tools

	Financial data integration

	AI assistant interface for supported workflows

	Python automated testing

	MCP server automated testing

	Version control

	Source control and project collaboration

</div>

Additional libraries, dependencies, and integrations are documented in the relevant requirements.txt, package.json, and project documentation files.

📂 Repository Structure
RE-Financial-AI-Solutions-Builder/
│
├── README.md
├── START_HERE.md
├── Project_Report.pdf
├── architecture.pdf
│
├── abc-trend-analysis/
│   ├── scripts/
│   │   ├── adapters/
│   │   ├── tools/
│   │   ├── engine.py
│   │   ├── models.py
│   │   ├── reporter.py
│   │   └── run_pipeline.py
│   │
│   ├── tests/
│   ├── evals/
│   ├── docs/
│   │   └── screenshots/
│   ├── results/
│   └── requirements.txt
│
├── quickbooks-online-mcp-server/
│   ├── src/
│   │   ├── clients/
│   │   ├── handlers/
│   │   ├── server/
│   │   └── tools/
│   │
│   ├── tests/
│   ├── scripts/
│   └── package.json
│
└── scripts/
    ├── generate_final_report.py
    └── run_pipeline.py

This is a simplified overview. Refer to the repository for the complete source tree.

📁 Component Responsibilities
Component	Responsibility
abc-trend-analysis/	Financial analysis, normalization, validation, evaluation, and reporting
abc-trend-analysis/scripts/	Analysis pipeline, processing logic, and reporting utilities
abc-trend-analysis/tests/	Automated tests for the financial analysis components
abc-trend-analysis/evals/	Evaluation cases, numerical validation, and commentary evaluation
abc-trend-analysis/docs/	Technical documentation and demonstration evidence
abc-trend-analysis/results/	Generated analysis outputs and evaluation artifacts
quickbooks-online-mcp-server/	QuickBooks Online MCP integration
quickbooks-online-mcp-server/src/	MCP tools, handlers, API client, and server implementation
quickbooks-online-mcp-server/tests/	Automated tests for MCP server components
scripts/	Root-level report-generation and pipeline utilities
🧪 Testing & Evaluation

Testing and evaluation are important parts of this project because financial outputs must be checked for correctness, not simply generated.

The verification workflow covers the following areas:

Python tests: Analysis logic, data processing, validation, and pipeline behavior.
MCP server tests: Tool handlers, client behavior, and supported QuickBooks operations.
Financial validation: Numerical checks and financial statement consistency.
Evaluation cases: Representative inputs, including missing data and unusual financial patterns.
Integration verification: Checks of supported QuickBooks connection and data-retrieval workflows.
Evidence review: Inspection of generated reports, screenshots, and saved results.
Verification Snapshot

The recorded final verification reported 779 passing automated checks:

Test category	Reported result
Python tests	131 passed
MCP server Jest tests	639 passed
Financial P&L schema tests	9 passed
Total	779 passed

These figures reflect the recorded verification run. They should not be interpreted as 779 live QuickBooks integration tests or as a measure of code coverage.

See the project test suites and evaluation artifacts for the underlying evidence.

📑 Documentation & Evidence

The repository includes documentation to help reviewers understand the implementation and verify its behavior.

Resource	Description
Project Report	Project objectives, implementation, workflow, testing, and conclusions
Architecture Document	System architecture, component relationships, and data flow
Getting Started	Entry point for exploring the project
Financial Analysis README	Financial analysis component documentation
MCP Server README	QuickBooks MCP server documentation
Architecture Notes	Financial analysis architecture
Connection Documentation	Connection and integration information
Evaluation Documentation	Evaluation methodology and evidence
Screenshots	Saved implementation and demonstration evidence
Evaluation Results	Generated analysis and evaluation artifacts
🚀 Getting Started
Prerequisites

Before running the project, ensure you have the relevant tools installed:

Python compatible with the project's dependencies.
Node.js and npm for the TypeScript MCP server.
Git.
Claude Desktop or another compatible MCP client.
QuickBooks Online access and the required application credentials for live integration.
Any required LLM API credentials for configured AI-assisted evaluation workflows.
1. Clone the Repository
git clone https://github.com/Chandrashekhar-cloud/RE-Financial-AI-Solutions-Builder.git
cd RE-Financial-AI-Solutions-Builder
2. Explore the Documentation

Start with:

START_HERE.md
README.md
Project_Report.pdf
architecture.pdf
3. Configure the Financial Analysis Component

Navigate to the analysis directory:

cd abc-trend-analysis

Create and activate a Python virtual environment using the instructions appropriate for your operating system.

Install the project's dependencies:

pip install -r requirements.txt

Review the component README and configuration before running any pipeline commands.

4. Configure the MCP Server

Navigate to:

quickbooks-online-mcp-server/

Install dependencies:

npm ci

Review its README for the correct build, authentication, and execution instructions.

Configure your own QuickBooks credentials and required environment variables locally. Use the actual configuration instructions provided by the project rather than copying another user's credentials.

5. Run Tests

For the Python component, follow its documented test instructions. A typical command is:

python -m pytest

For the MCP server, use the scripts defined in its package.json. For example, if a test script is configured:

npm test

Check the available scripts before running commands that may not be defined in your installed version.

Note: Live QuickBooks workflows require valid configuration and appropriate access. Offline tests and mock-based tests may run without a live QuickBooks connection.

🔐 Security & Responsible Data Handling

Financial integrations require careful handling of credentials and business data.

Never commit .env files, OAuth tokens, refresh tokens, API secrets, or private keys.
Use local environment variables and the documented authentication process.
Keep the real tokens.json file out of version control.
Do not publish confidential financial statements, customer information, or private business reports.
Review screenshots and generated JSON, Markdown, Excel, and PDF artifacts before making the repository public.
Use synthetic or sanitized data for public demonstrations whenever possible.
Review permissions and the actual operations supported by the MCP server before using it with a production accounting system.

Important: The MCP server supports a broader range of QuickBooks operations than the read-only Profit and Loss demonstration. The specific operations available depend on the implemented tools and configured permissions.

💡 Engineering Principles Demonstrated

This project brings together several practical software engineering concepts:

Tool-based AI integration: Connecting an AI client to external systems through a structured protocol.
API integration: Interacting with an accounting platform through an application server.
Data engineering: Transforming and normalizing financial information for analysis.
Financial correctness: Checking numerical consistency and validating generated outputs.
Testing and evaluation: Combining automated tests with structured evaluation cases.
Observability through evidence: Retaining reports and screenshots that help reviewers inspect system behavior.
Documentation: Making a multi-component project easier to understand, reproduce, and evaluate.
🔮 Future Improvements

Potential extensions include:

Expanded financial analysis across additional accounting reports.
More comprehensive financial anomaly detection.
Improved reconciliation and data-quality diagnostics.
Expanded evaluation coverage for edge cases.
Better automated reporting and visualization.
Stronger integration testing across the complete workflow.
Additional access controls, audit logging, and production-readiness checks.

These are potential improvements, not claims that the features have already been implemented.

👨‍💻 Author

Chandrashekhar H S

Computer Science Engineering | AI & ML

Interested in AI engineering, backend systems, cloud infrastructure, automation, and reliable software systems.

GitHub: @Chandrashekhar-cloud

<div align="center">

Built to connect AI with real-world financial workflows.

RE Financial AI Solutions Builder

View Repository · Read Project Report · Explore Architecture

</div>
