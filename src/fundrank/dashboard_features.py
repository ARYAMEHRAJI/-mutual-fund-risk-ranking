"""Small helper functions for optional dashboard features."""
from io import BytesIO

import numpy as np
import pandas as pd


def add_standalone_risk_score(data):
    """Create a 0-100 relative risk score; higher means more risk."""
    result = data.copy()
    volatility = pd.to_numeric(result.get("volatility"), errors="coerce")
    drawdown = pd.to_numeric(result.get("max_drawdown"), errors="coerce").abs()
    vol_pct = volatility.rank(pct=True) * 100
    dd_pct = drawdown.rank(pct=True) * 100
    result["risk_score"] = pd.concat([vol_pct, dd_pct], axis=1).mean(axis=1)
    return result


def equal_weight_portfolio(data, score_column, count=5):
    """Select the highest-ranked funds and assign a simple equal weight."""
    selected = data.dropna(subset=[score_column]).sort_values(score_column, ascending=False).head(count).copy()
    if selected.empty:
        return selected
    selected["portfolio_weight_pct"] = 100.0 / len(selected)
    return selected


def make_pdf_report(data, profile, date_label):
    """Build a compact English-language PDF table (portable built-in font)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=24, leftMargin=24)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Mutual Fund Risk &amp; Return Ranking Report", styles["Title"]),
        Paragraph(f"Risk profile: {profile} | Data date: {date_label}", styles["Normal"]),
        Spacer(1, 12),
    ]
    columns = [
        ("scheme_name", "Fund"), ("scheme_code", "Code"),
        (f"rank_{profile.lower()}", "Rank"), (f"composite_{profile.lower()}", "Score"),
        ("return_12m", "12M return"), ("volatility", "Volatility"),
        ("max_drawdown", "Max drawdown"), ("sharpe_ratio", "Sharpe"),
        ("sortino_ratio", "Sortino"),
    ]
    available = [(key, label) for key, label in columns if key in data.columns]
    rows = [[label for _, label in available]]
    for _, row in data.head(30).iterrows():
        values = []
        for key, _ in available:
            value = row.get(key, "")
            if pd.isna(value):
                values.append("-")
            elif key in {"return_12m", "volatility", "max_drawdown"}:
                values.append(f"{float(value):.1%}")
            elif key in {"composite_" + profile.lower()}:
                values.append(f"{float(value):.1f}")
            else:
                values.append(str(value)[:38])
        rows.append(values)
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243447")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([table, Spacer(1, 10), Paragraph(
        "Research and educational use only. This report is not investment advice or a guarantee of future returns.",
        styles["Italic"],
    )])
    doc.build(story)
    return output.getvalue()
