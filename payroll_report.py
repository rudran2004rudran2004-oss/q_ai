import io
import os
import random
from datetime import datetime

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────────────────────────────────────

DARK_BLUE  = colors.HexColor("#1a3c6e")
MID_BLUE   = colors.HexColor("#2d6abf")
LIGHT_BLUE = colors.HexColor("#dce8f8")
WHITE      = colors.white
GREY_BG    = colors.HexColor("#f5f7fa")
GREY_TEXT  = colors.HexColor("#555555")

STATUS_COLORS = {
    "Completed":  colors.HexColor("#1a7a3c"),
    "Processing": colors.HexColor("#b87000"),
    "Pending":    colors.HexColor("#a01010"),
}

LEVELS = {
    "Executive": ["CEO", "CTO", "CFO", "Chief Strategy Officer"],
    "Senior":    ["VP of Engineering", "VP of Marketing",
                  "Director of Finance", "Head of Product"],
    "Mid":       ["Project Manager", "Team Lead",
                  "Senior Analyst", "Senior Developer"],
    "Junior":    ["Analyst", "Developer", "QA Engineer", "Marketing Associate"],
    "Entry":     ["Intern", "Trainee", "Support Assistant", "Junior Developer"],
}


# ─────────────────────────────────────────────────────────────────────────────
# 1.  DATA EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_latest_csv_payroll(upload_dir="uploads"):
    """
    Reads the most-recently-modified CSV from *upload_dir*.

    Returns:
        dict  – report data on success
        dict  – {"error": "<message>"} on failure
    """
    # ── find latest CSV ──────────────────────────────────────────────────────
    try:
        files = [f for f in os.listdir(upload_dir) if f.endswith(".csv")]
    except FileNotFoundError:
        return {"error": f"Upload directory '{upload_dir}' does not exist."}

    if not files:
        return {"error": f"No CSV files found in '{upload_dir}'."}

    latest_file = max(
        files, key=lambda f: os.path.getmtime(os.path.join(upload_dir, f))
    )
    filepath = os.path.join(upload_dir, latest_file)
    print(f"📂 Reading: {filepath}")

    # ── load & clean ─────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except Exception as e:
        return {"error": f"Failed to read CSV: {e}"}

    df["gross_salary"] = (
        df["gross_salary"].astype(str)
        .str.replace(r"[^\d]", "", regex=True)
        .astype(int)
    )

    # ── categorise employees by level ─────────────────────────────────────────
    role_to_level = {r: lvl for lvl, roles in LEVELS.items() for r in roles}
    df["level"] = df["role"].map(role_to_level).fillna("Other")

    # ── aggregate stats ───────────────────────────────────────────────────────
    total_employees = len(df)
    total_payroll   = int(df["gross_salary"].sum())

    level_stats = (
        df.groupby("level")["gross_salary"]
        .agg(count="count", total_salary="sum")
        .reindex(list(LEVELS.keys()), fill_value=0)
    )

    # ── sample rows for the detail table ─────────────────────────────────────
    SAMPLE = min(1000, total_employees)
    sample_df = df.sample(n=SAMPLE, random_state=42)[
        ["EmployeeID", "level", "gross_salary"]
    ].copy()
    sample_df["status"] = [
        random.choice(["Completed", "Processing", "Pending"])
        for _ in range(SAMPLE)
    ]

    return {
        "timestamp":       datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S"),
        "source_file":     latest_file,
        "total_employees": total_employees,
        "total_payroll":   total_payroll,
        "level_stats":     level_stats,
        "sample_df":       sample_df,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2.  INTERNAL TABLE BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle", parent=base["Title"],
            fontSize=22, textColor=WHITE, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"],
            fontSize=10, textColor=colors.HexColor("#c8d8f0"), spaceAfter=0,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"],
            fontSize=13, textColor=DARK_BLUE, spaceBefore=14, spaceAfter=6,
        ),
        "normal": ParagraphStyle(
            "Body", parent=base["Normal"], fontSize=9, textColor=GREY_TEXT,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["Normal"], fontSize=8, textColor=GREY_TEXT,
        ),
    }


def _header_table(data, s):
    t = Table([[
        Paragraph("Quantum Payroll Report", s["title"]),
        Paragraph(
            f"Generated: {data['timestamp']}<br/>Source: {data['source_file']}",
            s["subtitle"]
        ),
    ]], colWidths=["60%", "40%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK_BLUE),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("TOPPADDING",    (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("ALIGN",         (1, 0), (1, 0),  "RIGHT"),
    ]))
    return t


def _summary_table(data, s):
    cells = [
        ["Total\nEmployees", f"{data['total_employees']:,}"],
        ["Total\nPayroll",   f"\u20b9{data['total_payroll']:,}"],
        ["Levels\nTracked",  str(len(data["level_stats"]))],
        ["Sample\nRows",     f"{len(data['sample_df']):,}"],
        ["Report\nDate",     data["timestamp"][:10]],
    ]
    t = Table(
        [
            [Paragraph(f"<b>{c[0]}</b>", s["small"]) for c in cells],
            [Paragraph(
                f'<font size="14" color="{MID_BLUE.hexval()}"><b>{c[1]}</b></font>',
                s["normal"]
             ) for c in cells],
        ],
        colWidths=["20%"] * 5,
        rowHeights=[22, 32],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GREY_BG),
        ("BACKGROUND",    (0, 0), (-1, 0),  LIGHT_BLUE),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#c0cfe0")),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.HexColor("#c0cfe0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _department_table(data, s):
    rows = [[
        Paragraph("<b>Level</b>",             s["small"]),
        Paragraph("<b>Employees</b>",         s["small"]),
        Paragraph("<b>Total Salary (Rs.)</b>",s["small"]),
        Paragraph("<b>Avg Salary (Rs.)</b>",  s["small"]),
    ]]
    for lvl, row in data["level_stats"].iterrows():
        cnt = int(row["count"])
        tot = int(row["total_salary"])
        rows.append([
            Paragraph(lvl,         s["normal"]),
            Paragraph(f"{cnt:,}",  s["normal"]),
            Paragraph(f"{tot:,}",  s["normal"]),
            Paragraph(f"{int(tot/cnt) if cnt else 0:,}", s["normal"]),
        ])
    t = Table(rows, colWidths=["25%"] * 4)
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  DARK_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#c0cfe0")),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.HexColor("#c0cfe0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), GREY_BG))
    t.setStyle(TableStyle(cmds))
    return t


def _detail_table(data, s):
    rows = [[
        Paragraph("<b>Employee ID</b>",  s["small"]),
        Paragraph("<b>Level</b>",        s["small"]),
        Paragraph("<b>Gross Salary</b>", s["small"]),
        Paragraph("<b>Status</b>",       s["small"]),
    ]]
    for _, r in data["sample_df"].iterrows():
        sc = STATUS_COLORS.get(r["status"], GREY_TEXT)
        rows.append([
            Paragraph(str(r["EmployeeID"]),               s["small"]),
            Paragraph(str(r["level"]),                    s["small"]),
            Paragraph(f"\u20b9{int(r['gross_salary']):,}", s["small"]),
            Paragraph(
                f'<font color="{sc.hexval()}"><b>{r["status"]}</b></font>',
                s["small"]
            ),
        ])
    t = Table(rows, colWidths=["30%", "20%", "25%", "25%"], repeatRows=1)
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  DARK_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#c0cfe0")),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#dde5f0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), GREY_BG))
    t.setStyle(TableStyle(cmds))
    return t


# ─────────────────────────────────────────────────────────────────────────────
# 3.  PUBLIC FUNCTION  ← the only thing your Flask app needs to call
# ─────────────────────────────────────────────────────────────────────────────

def build_payroll_pdf(upload_dir="uploads"):
    """
    Extracts data from the latest CSV in *upload_dir* and builds the
    Quantum Payroll PDF entirely in memory.

    Returns:
        (io.BytesIO, str)  – (pdf_buffer, suggested_filename)  on success
        (None, str)        – (None, error_message)             on failure
    """
    data = extract_latest_csv_payroll(upload_dir)

    if "error" in data:
        return None, data["error"]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm,
    )

    s = _styles()
    story = [
        _header_table(data, s),
        Spacer(1, 0.5*cm),
        Paragraph("Summary Statistics", s["h2"]),
        _summary_table(data, s),
        Spacer(1, 0.5*cm),
        Paragraph("Department / Level Breakdown", s["h2"]),
        _department_table(data, s),
        Spacer(1, 0.5*cm),
        PageBreak(),
        Paragraph(
            f"Employee Detail (sample of {len(data['sample_df']):,} records)",
            s["h2"]
        ),
        _detail_table(data, s),
    ]

    doc.build(story)
    buffer.seek(0)

    filename = f"Quantum_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return buffer, filename
