"""
RE Financial Services — AI Solutions Builder Placement
Task 4 Architecture Note: Professional LaTeX-Style Single-Page Technical Architecture Note.

Visual Qualities & Design Philosophy:
  1. Professional LaTeX academic publication typography (Times-Roman serif, bold numbered section headings).
  2. Balanced margins, clean whitespace, zero overcrowding, zero neon/dark clutter.
  3. Booktabs-style tables with thin horizontal rules, consistent padding, and no vertical borders.
  4. Minimalist architecture flow diagram communicating the pipeline stages at a glance.
  5. Subtle shaded callout box for architectural verification, security boundaries, and sign-off.
  6. EXACTLY ONE PAGE (A4) guaranteed with zero overflow.

Required Content Coverage (100% Comprehensive & Technically Credible):
  - Section 1: System Structure, Core Components & Memory Model (Files, skills, artifacts, and stateless state).
  - Section 2: Security Accuracy & Execution Environment (Registration-time mutation suppression, vault migration).
  - Section 3: Hosting Model: Prototype vs. Enterprise Cloud (Local workstation vs. Proposed AWS Architecture).
  - Section 4: Ten-Client Scaling & Multi-Tenant Isolation (Bottlenecks, 6 isolation boundaries, memory contract).
  - Section 5: Architectural Verification & Compliance Sign-Off (95 pytest tests, 110/110 golden evals, 100/100 commentary).
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.shapes import Drawing, Polygon, Line
import pypdf

OUTPUT_PDF = os.path.join(os.path.dirname(__file__), "architecture.pdf")

# LaTeX classic monochrome / dark slate palette
C_BLACK    = colors.HexColor("#111111")
C_MUTED    = colors.HexColor("#444444")
C_RULE     = colors.HexColor("#222222")
C_RULE_LT  = colors.HexColor("#888888")
C_BG_BOX   = colors.HexColor("#F8F9FA")
C_BOX_BRD  = colors.HexColor("#CCCCCC")

def build_pdf():
    # A4 Dimensions: 595.276 x 841.890 pt
    # Margins: Left=28, Right=28, Top=18, Bottom=15 -> Usable width: 539.276 pt, Usable height: 808.89 pt
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=28, rightMargin=28,
        topMargin=18, bottomMargin=15,
    )
    W = 595.276 - 56  # 539.276 pt

    # LaTeX Typography: Times-Roman (Serif), Times-Bold, Courier (Monospace)
    def sty(name, font="Times-Roman", size=8.2, leading=10.0, color=C_BLACK, spaceAfter=0, leftIndent=0, align=0):
        return ParagraphStyle(
            name, fontName=font, fontSize=size, leading=leading,
            textColor=color, spaceAfter=spaceAfter, leftIndent=leftIndent, alignment=align
        )

    S_HDR_TOP = sty("HdrTop", font="Times-Bold", size=7.5, leading=8.8, color=C_MUTED, align=1)
    S_TITLE   = sty("Title",  font="Times-Bold", size=13.0, leading=15.0, color=C_BLACK, align=1)
    S_SUB     = sty("Sub",    font="Times-Italic", size=8.0, leading=9.5, color=C_MUTED, align=1)
    S_META    = sty("Meta",   font="Times-Roman", size=7.3, leading=8.5, color=C_MUTED, align=1)

    S_SEC_NUM = sty("SecNum", font="Times-Bold", size=8.6, leading=10.2, color=C_BLACK, spaceAfter=1.0)
    S_BODY    = sty("Body",   font="Times-Roman", size=7.4, leading=9.0, color=C_BLACK, spaceAfter=1.2)

    # Diagram box styles
    S_DIA_NUM = sty("DiaNum", font="Times-Bold", size=7.0, leading=8.0, color=C_MUTED, align=1)
    S_DIA_HDR = sty("DiaHdr", font="Times-Bold", size=7.8, leading=9.0, color=C_BLACK, align=1)
    S_DIA_SUB = sty("DiaSub", font="Times-Roman", size=6.8, leading=7.8, color=C_MUTED, align=1)

    # Table styles
    S_TBL_TH  = sty("TblTh",  font="Times-Bold", size=7.3, leading=8.5, color=C_BLACK)
    S_TBL_TD  = sty("TblTd",  font="Times-Roman", size=7.0, leading=8.3, color=C_BLACK)
    S_TBL_TDB = sty("TblTdB", font="Times-Bold", size=7.0, leading=8.3, color=C_BLACK)
    S_TBL_CODE= sty("TblCode",font="Courier", size=6.6, leading=7.8, color=C_BLACK)

    S_BOX_TXT = sty("BoxTxt", font="Times-Roman", size=7.1, leading=8.5, color=C_BLACK)
    S_FOOT    = sty("Foot",   font="Times-Roman", size=7.0, leading=8.2, color=C_MUTED)

    story = []

    # 1. LATEX HEADER BLOCK
    story.append(Paragraph("RE FINANCIAL SERVICES &bull; TECHNICAL ARCHITECTURE SPECIFICATION", S_HDR_TOP))
    story.append(Spacer(1, 1.0))
    story.append(Paragraph("Financial Trend Analysis &amp; Accounting Intelligence Platform", S_TITLE))
    story.append(Spacer(1, 0.8))
    story.append(Paragraph("Architecture Note: Implemented Calculation Engine, LLM Grounding, Read-Only MCP Bridge &amp; Production Roadmap", S_SUB))
    story.append(Spacer(1, 0.8))
    story.append(Paragraph("<b>Task 4 Architecture Note</b> &bull; Author: Chandrashekhar H S &bull; Status: Working Prototype (Automated Pipeline) &bull; Verified: 99 Tests, 110/110 Evals", S_META))
    story.append(Spacer(1, 2.0))
    story.append(HRFlowable(width="100%", thickness=0.8, color=C_RULE, spaceBefore=0, spaceAfter=2.5))

    # 2. SECTION 1: SYSTEM OVERVIEW & ARCHITECTURE FLOW DIAGRAM
    story.append(Paragraph("1. Project Structure: Files, Skills &amp; Memory Model", S_SEC_NUM))
    story.append(Paragraph(
        "The platform ingests client workbooks or live QuickBooks data and produces validated FP&amp;A trend analyses. "
        "The architecture enforces strict separation between deterministic arithmetic and AI reasoning: "
        "the Python calculation engine calculates all financial metrics and creates structured outputs (<code>results/analysis.json</code>); "
        "the Claude Skill (<code>.claude/skills/monthly-trend-analysis/SKILL.md</code>) uses those results to explain trends, variance drivers, and anomalies without recalculating figures in text. "
        "The unified launcher (<code>scripts/run_pipeline.py [--offline]</code>) orchestrates the 6-stage flow: "
        "<i>Pre-flight Safety &rarr; Data Normalization &rarr; Engine Math &rarr; Artifact Verification &rarr; Golden Evals &rarr; Commentary Grounding</i>.",
        S_BODY
    ))

    # Clean LaTeX-Style Minimalist Architecture Flowchart
    def make_arrow(w=10, h=22):
        d = Drawing(w, h)
        cy = h / 2
        d.add(Line(1.0, cy, w - 3.5, cy, strokeColor=C_RULE_LT, strokeWidth=0.8))
        d.add(Polygon([w - 4.5, cy - 3.0, w - 0.5, cy, w - 4.5, cy + 3.0], fillColor=C_RULE_LT, strokeColor=None))
        return d

    bw = (W - 30) / 4  # 127.32 pt each
    d_b1 = [
        Paragraph("STAGE 1 &bull; INGESTION", S_DIA_NUM),
        Paragraph("Normalization Adapter", S_DIA_HDR),
        Paragraph("Auto-sorts reversed dates;<br/><code>scripts/adapters/qbo_adapter.py</code>", S_DIA_SUB)
    ]
    d_b2 = [
        Paragraph("STAGE 2 &bull; MATH", S_DIA_NUM),
        Paragraph("Deterministic Engine", S_DIA_HDR),
        Paragraph("Decimal cents arithmetic;<br/><code>scripts/engine.py</code> subtotal check", S_DIA_SUB)
    ]
    d_b3 = [
        Paragraph("STAGE 3 &bull; ARTIFACTS", S_DIA_NUM),
        Paragraph("Reporter &amp; Artifacts", S_DIA_HDR),
        Paragraph("<code>results/analysis.json</code><br/><code>results/report.md</code> via reporter", S_DIA_SUB)
    ]
    d_b4 = [
        Paragraph("STAGE 4 &bull; REASONING", S_DIA_NUM),
        Paragraph("Claude Skill &amp; Evals", S_DIA_HDR),
        Paragraph("10 never-rules; <code>evals/</code> suite<br/>(9 golden cases, 4 guardrails)", S_DIA_SUB)
    ]

    dia_table = Table(
        [[d_b1, make_arrow(10, 24), d_b2, make_arrow(10, 24), d_b3, make_arrow(10, 24), d_b4]],
        colWidths=[bw, 10, bw, 10, bw, 10, bw],
        spaceBefore=1.0, spaceAfter=2.5
    )
    dia_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), C_BG_BOX),
        ("BACKGROUND",    (2, 0), (2, 0), C_BG_BOX),
        ("BACKGROUND",    (4, 0), (4, 0), C_BG_BOX),
        ("BACKGROUND",    (6, 0), (6, 0), C_BG_BOX),
        ("BOX",           (0, 0), (0, 0), 0.5, C_BOX_BRD),
        ("BOX",           (2, 0), (2, 0), 0.5, C_BOX_BRD),
        ("BOX",           (4, 0), (4, 0), 0.5, C_BOX_BRD),
        ("BOX",           (6, 0), (6, 0), 0.5, C_BOX_BRD),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2.0),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(dia_table)

    # Clean Booktabs-style Pipeline Stage Summary Table
    pipe_data = [
        [
            Paragraph("Stage", S_TBL_TH),
            Paragraph("Component &amp; Source File", S_TBL_TH),
            Paragraph("Deterministic Responsibility &amp; Accounting Method", S_TBL_TH),
            Paragraph("Verified Artifact &amp; Guarantee", S_TBL_TH)
        ],
        [
            Paragraph("1. Ingestion", S_TBL_TDB),
            Paragraph("<code>openpyxl</code> / <code>qbo_adapter.py</code>", S_TBL_CODE),
            Paragraph("Auto-detects and re-orders reversed columns; normalizes QBO V3 P&amp;L JSON into standard 18-month schema.", S_TBL_TD),
            Paragraph("Chronological period matrix; 16/18 exact matches (2 differ by 3 pre-existing sample txns).", S_TBL_TD)
        ],
        [
            Paragraph("2. Core Math", S_TBL_TDB),
            Paragraph("<code>scripts/engine.py</code>", S_TBL_CODE),
            Paragraph("Python <code>Decimal(ROUND_HALF_UP)</code> cents arithmetic. Backward component matching isolates multi-tier subtotals without double-counting.", S_TBL_TD),
            Paragraph("126/126 checks reconcile (100%); zero floating-point drift; strict 12-consecutive-month TTM gating.", S_TBL_TD)
        ],
        [
            Paragraph("3. Artifacts", S_TBL_TDB),
            Paragraph("<code>scripts/reporter.py</code>", S_TBL_CODE),
            Paragraph("Bridges Dec 2025 -$1.244M tax credit to Normalized Core Operating Loss (-$381k). Derives periods dynamically; neutral headings for profitable firms.", S_TBL_TD),
            Paragraph("<code>analysis.json</code> (contract of truth) &amp; <code>report.md</code> with 10-point CFO close checklist.", S_TBL_TD)
        ],
        [
            Paragraph("4. Reasoning", S_TBL_TDB),
            Paragraph("Claude Skill (<code>SKILL.md</code>)", S_TBL_CODE),
            Paragraph("Governed by 10 negative never-rules; grounds strictly on <code>analysis.json</code> without recalculating figures; surfaces anomalies for human controller review.", S_TBL_TD),
            Paragraph("CFO-ready executive briefing; evaluated by <code>evals/</code> harness (9 golden cases, 4 guardrails).", S_TBL_TD)
        ]
    ]
    pipe_table = Table(pipe_data, colWidths=[55, 120, 214.28, 150], spaceBefore=0.5, spaceAfter=2.5)
    pipe_table.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0), 0.8, C_RULE),       # \toprule
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, C_RULE_LT),    # \midrule
        ("LINEBELOW",     (0, -1), (-1, -1), 0.8, C_RULE),    # \bottomrule
        ("TOPPADDING",    (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2.5),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(pipe_table)

    # 3. TWO-COLUMN CORE ARCHITECTURE
    COL_W = (W - 10) / 2  # 264.64 pt

    L = []
    R = []

    # ── LEFT COLUMN: SEC 2 & 3 ──
    L.append(Paragraph("2. Credential Security &amp; Execution Environment", S_SEC_NUM))
    L.append(Paragraph(
        "<b>Working Prototype (Today):</b> "
        "QuickBooks OAuth 2.0 credentials load into process memory from gitignored <code>.env</code> files. "
        "The official TypeScript MCP server enforces <b>registration-time mutation suppression</b>: "
        "at server startup, tool registration logic filters out any tool matching recognized mutation prefixes "
        "(<code>create_*</code>, <code>update_*</code>, <code>delete_*</code>), leaving exactly 71 read-only tools registered (out of 142 total). "
        "A pre-flight gate in <code>run_pipeline.py</code> halts execution if mutation disable flags are not explicitly true. "
        "<i>Security limitation:</i> Environment flags suppress tool registration at startup; complete defense-in-depth requires "
        "appropriate QuickBooks OAuth app permissions and independent validation of exposed tools.",
        S_BODY
    ))
    L.append(Paragraph(
        "<b>Production Vault Architecture (Proposed):</b> "
        "Secrets migrate to <b>AWS Secrets Manager</b> partitioned per tenant (<code>/tenants/{tenant_id}/qbo_credentials</code>) "
        "with <b>AWS KMS</b> envelope encryption. IAM roles grant access strictly to the authenticated tenant secret. "
        "Refresh tokens rotate on each exchange; distributed <b>Redis</b> locks serialize refresh across concurrent workers to eliminate race conditions.",
        S_BODY
    ))
    L.append(Spacer(1, 1.2))

    L.append(Paragraph("3. Hosting Model: Prototype vs. Enterprise Cloud", S_SEC_NUM))
    L.append(Paragraph(
        "<b>Current Working Prototype:</b> Operates locally on developer workstation across Python 3.10+ and Node.js 18+. "
        "Claude Desktop runs locally, spawning the MCP server via stdio JSON-RPC. Local output files and configuration. "
        "QuickBooks sandbox integration verified with balanced journal entries. "
        "<i>Fitness:</i> Highly effective for development, rapid offline testing, and interactive demonstrations without cloud hosting overhead. "
        "Synchronous stdout/stderr telemetry; stateless CLI fails fast with exit code 1; recovery via re-execution.",
        S_BODY
    ))
    L.append(Paragraph(
        "<b>Proposed Production Architecture (AWS):</b> "
        "Supports centralized multi-user operation, access controls, observability, and scaling (proposed design, not deployed):<br/>"
        "&bull;&nbsp;<b>Compute:</b> Stateless containerized tasks on <b>AWS ECS Fargate</b> in private VPC subnets.<br/>"
        "&bull;&nbsp;<b>Ingress:</b> <b>AWS API Gateway</b> terminates TLS 1.3, verifies OIDC JWTs, and enforces token-bucket rate limits.<br/>"
        "&bull;&nbsp;<b>Queue &amp; Storage:</b> <b>Amazon SQS</b> buffers jobs; artifacts persist in encrypted <b>Amazon S3</b>.<br/>"
        "&bull;&nbsp;<b>Observability:</b> Centralized JSON logs in <b>Amazon CloudWatch</b> with P99 latency and error alarms.",
        S_BODY
    ))

    # ── RIGHT COLUMN: SEC 4 ──
    R.append(Paragraph("4. Multi-Tenant Isolation Strategy (10 Clients)", S_SEC_NUM))
    R.append(Paragraph(
        "<b>Ten-Client Scaling Bottlenecks:</b> "
        "The prototype uses single-tenant filesystem paths (<code>results/analysis.json</code>) and a single active <code>.env</code> configuration. "
        "At ten concurrent clients, file collisions, OAuth refresh token race conditions, cross-tenant prompt leakage, "
        "and Intuit rate limits (500 req/min, 10 concurrent per realm) break single-tenant execution.",
        S_BODY
    ))

    # Booktabs table comparing 10-client isolation
    iso_data = [
        [
            Paragraph("Isolation Domain", S_TBL_TH),
            Paragraph("Prototype (Today)", S_TBL_TH),
            Paragraph("Proposed 10-Tenant Cloud Blueprint", S_TBL_TH)
        ],
        [
            Paragraph("Tenant Ingress", S_TBL_TDB),
            Paragraph("Single CLI invocation; developer sandbox.", S_TBL_TD),
            Paragraph("Enterprise OIDC JWT (Okta/Azure AD); Gateway validates token server-side, derives tenant ID; strips client headers.", S_TBL_TD)
        ],
        [
            Paragraph("Data Storage", S_TBL_TDB),
            Paragraph("Local directory; manual path arguments.", S_TBL_TD),
            Paragraph("Amazon S3 partitioned by <code>s3://bucket/{tenant_id}/analyses/</code> with scoped IAM session policies.", S_TBL_TD)
        ],
        [
            Paragraph("Database / State", S_TBL_TDB),
            Paragraph("Single-file JSON output; SQLite cache.", S_TBL_TD),
            Paragraph("PostgreSQL with Row-Level Security (RLS) enforcing <code>tenant_id = current_setting('app.current_tenant')</code> (proposed).", S_TBL_TD)
        ],
        [
            Paragraph("Secrets &amp; Tokens", S_TBL_TDB),
            Paragraph("Single <code>.env</code> file on workstation.", S_TBL_TD),
            Paragraph("AWS Secrets Manager: <code>/tenants/{tenant_id}/qbo_credentials</code>; isolated IAM roles; token refresh concurrency locks.", S_TBL_TD)
        ],
        [
            Paragraph("LLM Context", S_TBL_TDB),
            Paragraph("Claude Desktop local session context.", S_TBL_TD),
            Paragraph("Ephemeral, stateless agent tasks; loads only client workbook &amp; <code>analysis.json</code>; zero shared prompt/cache context.", S_TBL_TD)
        ],
        [
            Paragraph("Operations", S_TBL_TDB),
            Paragraph("Synchronous console output; fail-fast.", S_TBL_TD),
            Paragraph("Per-tenant rate limits &amp; DLQ queues; tenant-safe correlation IDs; zero financial/token logging; failure isolation.", S_TBL_TD)
        ]
    ]
    iso_table = Table(iso_data, colWidths=[52, 88, 124.64], spaceBefore=0.5, spaceAfter=1.2)
    iso_table.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0), 0.8, C_RULE),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, C_RULE_LT),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.8, C_RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 1.8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 1.8),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    R.append(iso_table)
    R.append(Paragraph(
        "<i>Memory Model Contract:</i> The prototype retains no persistent cross-session conversational memory by design. "
        "Analysis state is stored in structured artifacts (<code>analysis.json</code>, <code>report.md</code>) and configuration. "
        "Client-specific folders provide local operational separation during development, but local folder segregation alone does NOT provide enterprise security isolation.",
        S_BODY
    ))

    two_col = Table([[L, R]], colWidths=[COL_W, COL_W], spaceBefore=0, spaceAfter=2.0)
    two_col.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (0, 0), 0),
        ("RIGHTPADDING",  (0, 0), (0, 0), 4),
        ("LEFTPADDING",   (1, 0), (1, 0), 4),
        ("RIGHTPADDING",  (1, 0), (1, 0), 0),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(two_col)

    # 4. SECTION 5: VERIFICATION SUMMARY & SIGN-OFF BOX
    story.append(Paragraph("5. Architectural Verification &amp; Compliance Sign-Off", S_SEC_NUM))
    callout_p = Paragraph(
        "<b>Verified Implementation Metrics (Prototype Today):</b> "
        "&bull;&nbsp;<b>Pytest Test Suite:</b> <b>99 passed</b> in 18.54s (100% pass rate across engine, CLI, mutation, adapter, and reconciliation suites). "
        "&bull;&nbsp;<b>Golden Evaluation Harness:</b> <b>110.0 / 110.0</b> (100.0% score across 9 golden cases, +0.0 delta vs. baseline, zero regressions). "
        "&bull;&nbsp;<b>Commentary Evaluation Suite:</b> <b>100.0 / 100.0</b> across all 4 guardrail categories (Numerical Grounding, Unsupported Causal Claims, Anomaly Interpretation, Missing Information Disclosure). "
        "&bull;&nbsp;<b>QBO Ingestion Stretch Goal:</b> QuickBooks sandbox integration verified; tenant-specific identifiers are kept out of documentation. 18 balanced journal entries seeded; 16/18 months match Excel baseline exactly. "
        "<b>Scope Boundary:</b> This document certifies the working prototype implementation and specifies the enterprise AWS multi-tenant cloud roadmap. Proposed cloud infrastructure is planned, not deployed.",
        S_BOX_TXT
    )
    callout_tbl = Table([[callout_p]], colWidths=[W], spaceBefore=0, spaceAfter=2.0)
    callout_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_BG_BOX),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BOX_BRD),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4.0),
    ]))
    story.append(callout_tbl)

    # 5. LATEX RUNNING FOOTER
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_RULE_LT, spaceBefore=0, spaceAfter=1.2))
    foot_tbl = Table([
        [
            Paragraph("RE Financial Services &bull; AI Solutions Builder Placement &bull; Task 4: Technical Architecture Specification", S_FOOT),
            Paragraph("Page 1 of 1", ParagraphStyle("FR", parent=S_FOOT, alignment=2))
        ]
    ], colWidths=[W * 0.85, W * 0.15], spaceBefore=0, spaceAfter=0)
    foot_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(foot_tbl)

    doc.build(story)
    print(f"Generated: {OUTPUT_PDF}")

    reader = pypdf.PdfReader(OUTPUT_PDF)
    pages = len(reader.pages)
    print(f"Verified Page Count: {pages}")
    assert pages == 1, f"Expected exactly 1 page, got {pages}"

    return pages

if __name__ == "__main__":
    pages = build_pdf()
    sys.exit(0 if pages == 1 else 1)
