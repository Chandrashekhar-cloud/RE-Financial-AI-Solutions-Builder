"""
Generate the official 2-Page Executive Final Project Report for:
RE Financial Services — AI Solutions Builder Placement
Author: Chandrashekhar H S (chandrashekharhs653@gmail.com)

Features:
- Exactly 2 A4 pages.
- Professional modern typography & clean layout.
- Covers Tasks 1 through 4 with evidence locations, verification steps, and walkthrough table.
- Exact Phase 3 Task 1 instructions.
- Includes Task 2 heading, description, workflow, and deliverables.
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
import pypdf

OUTPUT_PDF = r"D:\RE-Financial-AI-Assignment\Project_Report.pdf"

# Palette
C_PRIMARY   = colors.HexColor("#0F2942")  # Deep Navy
C_SECONDARY = colors.HexColor("#1E3A8A")  # Slate Blue
C_TEXT      = colors.HexColor("#1A202C")  # Dark Charcoal
C_MUTED     = colors.HexColor("#4A5568")  # Slate Muted
C_LIGHT_BG  = colors.HexColor("#F0F4F9")  # Soft Cool Slate
C_BOX_BRD   = colors.HexColor("#CBD5E1")  # Border Slate
C_RULE      = colors.HexColor("#0F2942")
C_RULE_LT   = colors.HexColor("#CBD5E1")
C_ACCENT_BG = colors.HexColor("#EBF3FA")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(C_MUTED)
        
        # Header (pages 1 & 2)
        self.drawString(32, 815, "RE FINANCIAL SERVICES")
        self.drawRightString(595.276 - 32, 815, "AI SOLUTIONS BUILDER")
        
        # Top Rule
        self.setStrokeColor(C_RULE_LT)
        self.setLineWidth(0.6)
        self.line(32, 810, 595.276 - 32, 810)

        # Bottom Rule
        self.line(32, 34, 595.276 - 32, 34)

        # Footer
        self.setFont("Helvetica", 7.5)
        self.drawString(32, 24, "Chandrashekhar H S | chandrashekharhs653@gmail.com")
        self.drawRightString(595.276 - 32, 24, f"Project Report • Page {self._pageNumber} of {total_pages}")
        self.restoreState()


def build_report():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=32,
        rightMargin=32,
        topMargin=38,
        bottomMargin=38,
    )
    W = 595.276 - 64  # 531.276 pt usable width

    def sty(name, font="Helvetica", size=7.8, leading=9.8, color=C_TEXT, spaceAfter=0, spaceBefore=0, align=0):
        return ParagraphStyle(
            name, fontName=font, fontSize=size, leading=leading,
            textColor=color, spaceAfter=spaceAfter, spaceBefore=spaceBefore, alignment=align
        )

    # Styles
    S_TITLE    = sty("DocTitle", font="Helvetica-Bold", size=17.0, leading=19.5, color=C_PRIMARY, align=1)
    S_SUBTITLE = sty("DocSub",   font="Helvetica", size=9.5, leading=12.0, color=C_SECONDARY, align=1)
    S_AUTHOR   = sty("DocAuth",  font="Helvetica", size=8.0, leading=10.0, color=C_MUTED, align=1)

    S_SEC_HDR  = sty("SecHdr",   font="Helvetica-Bold", size=9.8, leading=11.5, color=C_PRIMARY, spaceBefore=4.0, spaceAfter=1.0)
    S_SEC_SUB  = sty("SecSub",   font="Helvetica-Oblique", size=7.5, leading=9.0, color=C_MUTED, spaceAfter=2.0)
    
    S_BODY     = sty("Body",     font="Helvetica", size=7.3, leading=9.2, color=C_TEXT, spaceAfter=2.0)
    S_BODY_B   = sty("BodyB",    font="Helvetica-Bold", size=7.3, leading=9.2, color=C_TEXT)

    S_CALLOUT  = sty("Callout",  font="Helvetica", size=7.3, leading=9.3, color=C_TEXT)
    S_CALL_SM  = sty("CallSm",   font="Helvetica", size=7.0, leading=8.8, color=C_TEXT)

    S_BADGE_N  = sty("BadgeN",   font="Helvetica-Bold", size=14.0, leading=15.0, color=C_PRIMARY, align=1)
    S_BADGE_L  = sty("BadgeL",   font="Helvetica", size=7.2, leading=8.5, color=C_MUTED, align=1)

    S_TBL_TH   = sty("TblTh",    font="Helvetica-Bold", size=7.2, leading=8.6, color=C_PRIMARY)
    S_TBL_TD   = sty("TblTd",    font="Helvetica", size=7.0, leading=8.5, color=C_TEXT)
    S_TBL_TDB  = sty("TblTdB",   font="Helvetica-Bold", size=7.0, leading=8.5, color=C_TEXT)
    S_TBL_CODE = sty("TblCode",  font="Courier", size=6.7, leading=8.0, color=C_SECONDARY)

    story = []

    # =========================================================================
    # PAGE 1: OVERVIEW, METRICS, TASK 1, TASK 2
    # =========================================================================
    
    # Title Block
    story.append(Paragraph("AI Solutions Builder", S_TITLE))
    story.append(Spacer(1, 1.5))
    story.append(Paragraph("Project Report | Tasks 1–4", S_SUBTITLE))
    story.append(Spacer(1, 1.0))
    story.append(Paragraph("Chandrashekhar H S | chandrashekharhs653@gmail.com", S_AUTHOR))
    story.append(Spacer(1, 4.0))

    # Project Overview Box
    p_overview = Paragraph(
        "<b>Project overview.</b> A working financial-analysis prototype combining QuickBooks Online Sandbox connectivity through Claude Desktop and MCP, "
        "a reusable monthly trend-analysis skill, deterministic Python calculations, automated evaluation and numerical validation, and a documented ten-client architecture.",
        S_CALLOUT
    )
    tbl_overview = Table([[p_overview]], colWidths=[W])
    tbl_overview.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT_BG),
        ("BOX",           (0, 0), (-1, -1), 0.6, C_BOX_BRD),
        ("TOPPADDING",    (0, 0), (-1, -1), 4.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6.0),
    ]))
    story.append(tbl_overview)
    story.append(Spacer(1, 4.0))

    # Metric Badges (131 Python tests, 639 MCP tests, 9/9 Golden cases, 18 Months analyzed)
    b_w = W / 4
    badges_data = [
        [
            Paragraph("131", S_BADGE_N),
            Paragraph("639", S_BADGE_N),
            Paragraph("9/9", S_BADGE_N),
            Paragraph("18", S_BADGE_N),
        ],
        [
            Paragraph("Python tests", S_BADGE_L),
            Paragraph("MCP tests", S_BADGE_L),
            Paragraph("golden cases", S_BADGE_L),
            Paragraph("months analyzed", S_BADGE_L),
        ]
    ]
    tbl_badges = Table(badges_data, colWidths=[b_w, b_w, b_w, b_w])
    tbl_badges.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 1.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(tbl_badges)
    story.append(Spacer(1, 4.0))

    # -------------------------------------------------------------------------
    # TASK 1 SECTION
    # -------------------------------------------------------------------------
    story.append(Paragraph("Task 1 | QuickBooks Sandbox + Claude Desktop MCP", S_SEC_HDR))
    story.append(Paragraph("Connection, tool invocation and financial-report retrieval", S_SEC_SUB))
    story.append(HRFlowable(width="100%", thickness=0.6, color=C_PRIMARY, spaceBefore=0, spaceAfter=3.0))

    story.append(Paragraph(
        "Claude Desktop is connected to a local QuickBooks MCP server configured for the Sandbox environment. "
        "Company-information and financial-report tools were used to demonstrate the connection and retrieve a read-only Profit &amp; Loss report.",
        S_BODY
    ))

    t1_deliverables = [
        [Paragraph("MCP source", S_TBL_TDB), Paragraph("quickbooks-online-mcp-server/", S_TBL_CODE)],
        [Paragraph("Connection notes &amp; evidence", S_TBL_TDB), Paragraph("abc-trend-analysis/docs/ and abc-trend-analysis/results/", S_TBL_CODE)],
        [Paragraph("Screenshots", S_TBL_TDB), Paragraph("abc-trend-analysis/docs/screenshots/", S_TBL_CODE)],
    ]
    tbl_t1 = Table(t1_deliverables, colWidths=[150, W - 150])
    tbl_t1.setStyle(TableStyle([
        ("LINEBELOW",     (0, 0), (-1, -1), 0.4, C_RULE_LT),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2.0),
    ]))
    story.append(tbl_t1)
    story.append(Spacer(1, 3.0))

    # Exact Phase 3 text
    story.append(Paragraph("<b>Verification &amp; Evidence (about 2 minutes)</b>", S_BODY))
    t1_verif_text = (
        "<b>1. Connection evidence:</b> Inspect the screenshots in <code>abc-trend-analysis/docs/screenshots/</code> showing the Claude Desktop MCP setup and connection status.<br/>"
        "<b>2. Workflow evidence:</b> Review the saved artifacts under <code>abc-trend-analysis/docs/</code> and <code>abc-trend-analysis/results/</code> that document company-information retrieval and the read-only Profit &amp; Loss workflow.<br/>"
        "<b>3. Implementation evidence:</b> Inspect the QuickBooks MCP source, including tool registration and the configured read-only safeguards, to understand how the integration works.<br/>"
        "These submitted artifacts allow independent review without access to the author's personal Claude Desktop account. "
        "During a live review, the author can share their screen and demonstrate the connection. "
        "Reviewers who wish to reproduce the connection independently must configure their own Claude Desktop environment with their own authorized Sandbox credentials. "
        "No import or write operation is required for this demonstration."
    )
    story.append(Paragraph(t1_verif_text, S_BODY))
    story.append(Spacer(1, 4.0))

    # -------------------------------------------------------------------------
    # TASK 2 SECTION
    # -------------------------------------------------------------------------
    story.append(Paragraph("Task 2 | Reusable Financial Trend Analysis Skill", S_SEC_HDR))
    story.append(Paragraph("Deterministic calculation engine, accounting anomaly handling, and CFO review", S_SEC_SUB))
    story.append(HRFlowable(width="100%", thickness=0.6, color=C_PRIMARY, spaceBefore=0, spaceAfter=3.0))

    story.append(Paragraph(
        "A reusable Claude skill interprets structured financial statements processed by a deterministic Python calculation engine. "
        "The engine applies Decimal cents arithmetic, subtotal isolation, and rolling 12-month TTM gating, while the skill contextualizes "
        "variance drivers, isolates the December 2025 non-operating tax credit anomaly (-$1.244M), and formats an actionable CFO Month-End Close Checklist.",
        S_BODY
    ))

    # Workflow diagram banner
    p_workflow = Paragraph(
        "<b>Workflow:</b> Excel workbook / saved report &rarr; Python engine &rarr; <code>results/analysis.json</code> &rarr; <code>results/report.md</code> &rarr; skill-guided commentary &amp; validation",
        S_CALLOUT
    )
    tbl_wf = Table([[p_workflow]], colWidths=[W])
    tbl_wf.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT_BG),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BOX_BRD),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5.0),
    ]))
    story.append(tbl_wf)
    story.append(Spacer(1, 3.0))

    t2_deliverables = [
        [Paragraph("Reusable skill", S_TBL_TDB), Paragraph("abc-trend-analysis/.claude/skills/monthly-trend-analysis/SKILL.md", S_TBL_CODE)],
        [Paragraph("Calculation engine", S_TBL_TDB), Paragraph("abc-trend-analysis/scripts/engine.py", S_TBL_CODE)],
        [Paragraph("Source workbook", S_TBL_TDB), Paragraph("abc-trend-analysis/data/ (18-month baseline)", S_TBL_CODE)],
        [Paragraph("Generated results", S_TBL_TDB), Paragraph("abc-trend-analysis/results/analysis.json and report.md", S_TBL_CODE)],
    ]
    tbl_t2 = Table(t2_deliverables, colWidths=[150, W - 150])
    tbl_t2.setStyle(TableStyle([
        ("LINEBELOW",     (0, 0), (-1, -1), 0.4, C_RULE_LT),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2.0),
    ]))
    story.append(tbl_t2)
    story.append(Spacer(1, 3.0))

    story.append(Paragraph(
        "<b>How to verify:</b> Read the skill instructions, inspect <code>scripts/engine.py</code>, trace structured metrics in "
        "<code>results/analysis.json</code> to the workbook, and review <code>results/report.md</code>. Run the offline pipeline to reproduce the analysis without changing Sandbox data.",
        S_BODY
    ))

    # =========================================================================
    # PAGE 2: TASK 3, TASK 4, REVIEWER WALKTHROUGH, SUMMARY
    # =========================================================================
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # TASK 3 SECTION
    # -------------------------------------------------------------------------
    story.append(Paragraph("Task 3 | Golden Cases, Regression Tests and Numerical Validation", S_SEC_HDR))
    story.append(Paragraph("Repeatable checks for correctness, financial interpretation and grounded output", S_SEC_SUB))
    story.append(HRFlowable(width="100%", thickness=0.6, color=C_PRIMARY, spaceBefore=0, spaceAfter=3.0))

    story.append(Paragraph(
        "Nine golden cases cover month ordering, accounting anomalies, TTM eligibility, negative reversals, missing periods, inconsistent totals, "
        "and cross-company generalization. Evaluation scripts compare results against expected cases. Commentary checks assess numerical "
        "grounding, unsupported causal claims, material anomaly interpretation, and missing-information disclosure. The numerical validator "
        "checks claims against generated analysis and labels them VERIFIED, INVALID, or UNVERIFIED.",
        S_BODY
    ))

    t3_deliverables = [
        [Paragraph("Golden cases", S_TBL_TDB), Paragraph("abc-trend-analysis/evals/eval_cases.json and evals/fixtures/", S_TBL_CODE)],
        [Paragraph("Evaluation scripts", S_TBL_TDB), Paragraph("evals/run_evals.py; evals/eval_commentary.py", S_TBL_CODE)],
        [Paragraph("Numerical validation", S_TBL_TDB), Paragraph("evals/numerical_validator.py; evals/llm_inference.py", S_TBL_CODE)],
        [Paragraph("Automated tests", S_TBL_TDB), Paragraph("abc-trend-analysis/tests/ (131 automated pytest tests)", S_TBL_CODE)],
    ]
    tbl_t3 = Table(t3_deliverables, colWidths=[150, W - 150])
    tbl_t3.setStyle(TableStyle([
        ("LINEBELOW",     (0, 0), (-1, -1), 0.4, C_RULE_LT),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2.0),
    ]))
    story.append(tbl_t3)
    story.append(Spacer(1, 3.0))

    # Reproduction commands table
    repro_data = [
        [Paragraph("Command (run from <code>abc-trend-analysis/</code>)", S_TBL_TH), Paragraph("Verifies", S_TBL_TH)],
        [
            Paragraph("<code>pytest</code>", S_TBL_CODE),
            Paragraph("Python unit, pipeline, adapter, evaluation, and validator tests (131 passed freshly verified).", S_TBL_TD)
        ],
        [
            Paragraph("<code>python -m evals.run_evals</code>", S_TBL_CODE),
            Paragraph("Golden-case regression (9/9 cases passed; 110/110 baseline score, 0 regressions).", S_TBL_TD)
        ],
        [
            Paragraph("<code>python scripts/run_pipeline.py --offline</code>", S_TBL_CODE),
            Paragraph("Six offline pipeline stages in the recorded run (reconciliation, artifacts, evals).", S_TBL_TD)
        ],
    ]
    tbl_repro = Table(repro_data, colWidths=[200, W - 200])
    tbl_repro.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_LIGHT_BG),
        ("LINEABOVE",     (0, 0), (-1, 0), 0.6, C_RULE),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, C_RULE_LT),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.6, C_RULE_LT),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3.0),
    ]))
    story.append(tbl_repro)
    story.append(Spacer(1, 3.0))

    # Recorded verification results callout box
    p_verif_res = Paragraph(
        "<b>Verified execution results:</b> 131 Python tests passed; 639 MCP tests passed across 35 suites; 9/9 golden cases passed (110.0/110.0); "
        "commentary evaluation 100/100; six offline pipeline stages passed; financial reconciliation 126/126 checks passed (100%).",
        S_CALLOUT
    )
    tbl_vbox = Table([[p_verif_res]], colWidths=[W])
    tbl_vbox.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT_BG),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BOX_BRD),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5.0),
    ]))
    story.append(tbl_vbox)
    story.append(Spacer(1, 4.0))

    # -------------------------------------------------------------------------
    # TASK 4 SECTION
    # -------------------------------------------------------------------------
    story.append(Paragraph("Task 4 | Architecture and Ten-Client Scaling", S_SEC_HDR))
    story.append(Paragraph("A documented design for client isolation and service growth", S_SEC_SUB))
    story.append(HRFlowable(width="100%", thickness=0.6, color=C_PRIMARY, spaceBefore=0, spaceAfter=3.0))

    story.append(Paragraph(
        "The architecture note describes a target ten-client design covering tenant identity, authorization, client-scoped credentials and storage, "
        "context separation, and operational monitoring. It provides a design path for evolving the prototype into a multi-client service with consistent isolation controls.",
        S_BODY
    ))

    p_arch_files = Paragraph(
        "<b>Architecture files:</b> <code>abc-trend-analysis/docs/architecture.pdf</code> and <code>abc-trend-analysis/docs/architecture.md</code>. "
        "A copy of <code>architecture.pdf</code> is also provided at the submission root.",
        S_CALLOUT
    )
    tbl_afiles = Table([[p_arch_files]], colWidths=[W])
    tbl_afiles.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT_BG),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BOX_BRD),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5.0),
    ]))
    story.append(tbl_afiles)
    story.append(Spacer(1, 2.5))

    story.append(Paragraph(
        "<b>How to verify:</b> Open the one-page architecture PDF, follow the component/data flow, and read the Markdown companion for tenant identity, "
        "authorization, data storage, and credential separation.",
        S_BODY
    ))
    story.append(Spacer(1, 3.5))

    # -------------------------------------------------------------------------
    # REVIEWER WALKTHROUGH
    # -------------------------------------------------------------------------
    story.append(Paragraph("Reviewer Walkthrough", S_SEC_HDR))
    story.append(Paragraph("A concise, evidence-led order for the demonstration", S_SEC_SUB))
    story.append(HRFlowable(width="100%", thickness=0.6, color=C_PRIMARY, spaceBefore=0, spaceAfter=3.0))

    walk_data = [
        [Paragraph("Stage", S_TBL_TH), Paragraph("Show", S_TBL_TH), Paragraph("Demonstrates", S_TBL_TH)],
        [
            Paragraph("Task 1", S_TBL_TDB),
            Paragraph("MCP status, company-info tool, Profit &amp; Loss report and saved evidence.", S_TBL_TD),
            Paragraph("Sandbox connection and tool invocation.", S_TBL_TD)
        ],
        [
            Paragraph("Task 2", S_TBL_TDB),
            Paragraph("<code>SKILL.md</code>, <code>engine.py</code>, workbook and generated results.", S_TBL_TD),
            Paragraph("Reusable workflow and traceable calculations.", S_TBL_TD)
        ],
        [
            Paragraph("Task 3", S_TBL_TDB),
            Paragraph("Test suite, golden-case fixture and numerical validator.", S_TBL_TD),
            Paragraph("Regression coverage and numerical grounding.", S_TBL_TD)
        ],
        [
            Paragraph("Task 4", S_TBL_TDB),
            Paragraph("Architecture PDF and Markdown companion.", S_TBL_TD),
            Paragraph("Ten-client design and tenant-isolation approach.", S_TBL_TD)
        ],
    ]
    tbl_walk = Table(walk_data, colWidths=[55, 260, W - 315])
    tbl_walk.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_LIGHT_BG),
        ("LINEABOVE",     (0, 0), (-1, 0), 0.6, C_RULE),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, C_RULE_LT),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.6, C_RULE_LT),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3.0),
    ]))
    story.append(tbl_walk)
    story.append(Spacer(1, 3.5))

    # Submission Summary Callout Box
    p_summary = Paragraph(
        "<b>Submission summary.</b> Tasks 1–4 are documented with implementation details, file locations, reviewer verification steps, and recorded test "
        "results. The reviewer can inspect the Sandbox workflow, reproduce the financial analysis, rerun evaluations, and review the proposed ten-client architecture.",
        S_CALLOUT
    )
    tbl_summary = Table([[p_summary]], colWidths=[W])
    tbl_summary.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT_BG),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BOX_BRD),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5.0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5.0),
    ]))
    story.append(tbl_summary)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated: {OUTPUT_PDF}")

    reader = pypdf.PdfReader(OUTPUT_PDF)
    pages = len(reader.pages)
    print(f"Verified Page Count: {pages}")
    assert pages == 2, f"Expected exactly 2 pages, got {pages}"
    return pages

if __name__ == "__main__":
    build_report()
