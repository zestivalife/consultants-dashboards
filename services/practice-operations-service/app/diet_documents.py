"""Branded exports for immutable External Consultant diet-plan versions."""
from __future__ import annotations

from collections import OrderedDict
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate, Paragraph,
    PageBreak, Spacer, Table, TableStyle,
)

MEAL_LABELS = OrderedDict((key, label) for key, label in (
    ("EARLY_MORNING", "Early Morning"), ("BREAKFAST", "Breakfast"),
    ("MID_MORNING", "Mid Morning"), ("LUNCH", "Lunch"),
    ("EVENING_SNACK", "Evening Snack"), ("DINNER", "Dinner"),
    ("BEDTIME", "Bedtime"),
))
NAVY = colors.HexColor("#0B1F3A")
BLUE = colors.HexColor("#1D4ED8")
PALE = colors.HexColor("#EFF6FF")
MUTED = colors.HexColor("#52627A")
GRID = colors.HexColor("#D9E1EA")


def _text(value: Any, fallback: str = "Not provided") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _pdf_text(value: Any, fallback: str = "Not provided") -> str:
    """Escape dynamic text before passing it to ReportLab's XML-like Paragraph parser."""
    return escape(_text(value, fallback), quote=False)


def _number(value: Any, suffix: str = "") -> str:
    if value is None:
        return "Not available"
    number = float(value)
    rendered = str(int(number)) if number.is_integer() else f"{number:.2f}".rstrip("0").rstrip(".")
    return f"{rendered}{suffix}"


def _group_options(snapshot: dict[str, Any]) -> OrderedDict[str, list[dict[str, Any]]]:
    grouped: OrderedDict[str, list[dict[str, Any]]] = OrderedDict((key, []) for key in MEAL_LABELS)
    for option in snapshot.get("options") or []:
        head = str(option.get("mealHead") or "")
        grouped.setdefault(head, []).append(option)
    return OrderedDict((head, options) for head, options in grouped.items() if options)


def _component_summary(option: dict[str, Any]) -> str:
    parts = []
    for component in option.get("components") or []:
        name = _text(component.get("foodDisplayNameSnapshot") or component.get("componentName"), "Food")
        serving = _text(component.get("label") or component.get("servingDisplayNameSnapshot"), "")
        grams = _number(component.get("grams"), " g") if component.get("grams") is not None else ""
        quantity = serving or grams
        parts.append(f"{name} - {quantity}" if quantity else name)
    return " + ".join(parts) or _text(option.get("clientTitle") or option.get("humanServingSummary"), "Structured meal")


def _selected_totals(snapshot: dict[str, Any]) -> dict[str, float | None]:
    totals = {"kcal": 0.0, "protein": 0.0, "carbohydrate": 0.0, "fat": 0.0, "fibre": 0.0}
    present = {key: False for key in totals}
    for options in _group_options(snapshot).values():
        selected = next((item for item in options if item.get("selected") is True), options[0] if options else None)
        if not selected:
            continue
        nutrition = selected.get("nutrition") or {}
        aliases = {"carbohydrate": ("carbohydrate", "carbs"), "kcal": ("kcal",), "protein": ("protein",), "fat": ("fat",), "fibre": ("fibre",)}
        for key, keys in aliases.items():
            value = next((nutrition.get(candidate) for candidate in keys if nutrition.get(candidate) is not None), None)
            if value is not None:
                totals[key] += float(value)
                present[key] = True
    return {key: round(value, 2) if present[key] else None for key, value in totals.items()}


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GRID)
    canvas.line(18 * mm, 13 * mm, 192 * mm, 13 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 8 * mm, "Confidential nutrition plan - share only through authorised channels")
    canvas.drawRightString(192 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _logo(logo_path: str, width: float = 38 * mm) -> Image:
    image_width, image_height = ImageReader(logo_path).getSize()
    return Image(logo_path, width=width, height=width * image_height / image_width)


def build_diet_pdf(snapshot: dict[str, Any], logo_path: str | None = None) -> bytes:
    output = BytesIO()
    doc = BaseDocTemplate(output, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
                          title=_text(snapshot.get("title"), "Diet Plan"), author=_text(snapshot.get("branding", {}).get("practice_name"), "Consultant practice"))
    doc.addPageTemplates(PageTemplate(id="diet", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")], onPage=_footer))
    styles = getSampleStyleSheet()
    title = ParagraphStyle("DietTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=29, textColor=NAVY, alignment=TA_LEFT, spaceAfter=5 * mm)
    h1 = ParagraphStyle("DietH1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=4 * mm, spaceAfter=2.5 * mm)
    h2 = ParagraphStyle("DietH2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=BLUE, spaceBefore=3 * mm, spaceAfter=2 * mm)
    body = ParagraphStyle("DietBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=colors.HexColor("#172033"))
    small = ParagraphStyle("DietSmall", parent=body, fontSize=8, leading=11, textColor=MUTED)
    brand = snapshot.get("branding") or {}
    story = []
    if brand.get("brand_type") == "INTERNAL" and logo_path and Path(logo_path).exists():
        story.append(_logo(logo_path))
        story.append(Spacer(1, 2 * mm))
    else:
        story.append(Paragraph(_pdf_text(brand.get("practice_name"), "Registered consultant practice"), h2))
    story.extend([
        Paragraph("Nutrition Plan", title),
        Table([
            [Paragraph("Client", small), Paragraph(_pdf_text(snapshot.get("client_name")), body), Paragraph("Plan", small), Paragraph(_pdf_text(snapshot.get("title")), body)],
            [Paragraph("Consultant", small), Paragraph(_pdf_text(brand.get("consultant_name")), body), Paragraph("Version", small), Paragraph(_pdf_text(f"{snapshot.get('version')} - {_text(snapshot.get('status'))}"), body)],
            [Paragraph("Approved", small), Paragraph(_pdf_text(snapshot.get("approved_at"), "Not approved"), body), Paragraph("Reference", small), Paragraph(_pdf_text(snapshot.get("reference")), body)],
        ], colWidths=[24 * mm, 60 * mm, 24 * mm, 66 * mm], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALE), ("GRID", (0, 0), (-1, -1), .5, GRID),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])),
        Paragraph("Plan Goals and Targets", h1),
    ])
    targets = snapshot.get("targets") or {}
    target_rows = [["Energy", _number(targets.get("calories"), " kcal/day")], ["Protein", _number(targets.get("protein"), " g/day")],
                   ["Carbohydrate", _number(targets.get("carbohydrate"), " g/day")], ["Fat", _number(targets.get("fat"), " g/day")], ["Fibre", _number(targets.get("fibre"), " g/day")]]
    story.append(Table(target_rows, colWidths=[55 * mm, 55 * mm], style=TableStyle([
        ("GRID", (0, 0), (-1, -1), .5, GRID), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])))
    story.append(Paragraph("Targets are displayed from the exact saved plan version. They are not recalculated by this document.", small))
    warnings = snapshot.get("warnings") or []
    if warnings:
        story.append(Paragraph("Data Limitations", h2))
        for warning in warnings:
            story.append(Paragraph(f"- {_pdf_text(warning)}", body))
    story.append(PageBreak())
    story.append(Paragraph("Meal-wise Alternatives", title))
    for meal_head, options in _group_options(snapshot).items():
        rows = [[Paragraph("Option", small), Paragraph("Foods and quantities", small), Paragraph("Nutrition", small)]]
        for index, option in enumerate(options, 1):
            nutrition = option.get("nutrition") or {}
            nutrients = f"{_number(nutrition.get('kcal'), ' kcal')} | {_number(nutrition.get('protein'), ' g protein')}"
            if nutrition.get("carbohydrate", nutrition.get("carbs")) is not None:
                nutrients += f" | {_number(nutrition.get('carbohydrate', nutrition.get('carbs')), ' g carbs')}"
            rows.append([Paragraph(str(index), body), Paragraph(_pdf_text(_component_summary(option)), body), Paragraph(_pdf_text(nutrients), small)])
        story.append(KeepTogether([Paragraph(MEAL_LABELS.get(meal_head, meal_head.replace("_", " ").title()), h2),
                                   Table(rows, repeatRows=1, colWidths=[13 * mm, 109 * mm, 52 * mm], style=TableStyle([
                                       ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                       ("GRID", (0, 0), (-1, -1), .5, GRID), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                       ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                       ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                   ]))]))
    totals = _selected_totals(snapshot)
    story.extend([Spacer(1, 5 * mm), Paragraph("Selected Day and Guidance", title), Paragraph("Selected day totals", h1)])
    story.append(Table([["Energy", _number(totals["kcal"], " kcal")], ["Protein", _number(totals["protein"], " g")],
                        ["Carbohydrate", _number(totals["carbohydrate"], " g")], ["Fat", _number(totals["fat"], " g")], ["Fibre", _number(totals["fibre"], " g")]],
                       colWidths=[55 * mm, 55 * mm], style=TableStyle([("GRID", (0, 0), (-1, -1), .5, GRID), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)])))
    story.append(Paragraph("Totals use one selected option per meal. When no explicit selection is stored, the first alternative is used for the example only; mutually exclusive alternatives are never summed.", small))
    for heading, items in (("Eating-out Guidance", snapshot.get("eating_out_guidance")), ("Daily Habits", snapshot.get("daily_habits")),
                           ("Food Safety", snapshot.get("food_safety")), ("Follow-up", snapshot.get("follow_up"))):
        story.append(Paragraph(heading, h1))
        values = items or ["Follow the consultant's saved instructions and review the plan at the agreed follow-up."]
        for item in values:
            story.append(Paragraph(f"- {_pdf_text(item)}", body))
    story.append(Paragraph("Plan Basis and Limitations", h1))
    story.append(Paragraph("This document reproduces the authorised saved plan version and available governed nutrition snapshots. Missing values remain marked as unavailable. It does not replace medical diagnosis or emergency care.", body))
    doc.build(story)
    return output.getvalue()


def _shade(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def _set_cell_text(cell, value: str, *, bold: bool = False, white: bool = False, size: int = 9):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(value)
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(size)
    if white:
        run.font.color.rgb = RGBColor(255, 255, 255)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def _add_page_field(paragraph):
    paragraph.add_run("Page ")
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText"); instruction.set(qn("xml:space"), "preserve"); instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar"); separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, instruction, separate, end))


def build_diet_docx(snapshot: dict[str, Any], logo_path: str | None = None) -> bytes:
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(1.8)
    section.left_margin = section.right_margin = Cm(1.8)
    styles = document.styles
    styles["Normal"].font.name = "Arial"; styles["Normal"].font.size = Pt(10)
    styles["Title"].font.name = "Arial"; styles["Title"].font.size = Pt(24); styles["Title"].font.color.rgb = RGBColor(11, 31, 58)
    styles["Heading 1"].font.name = "Arial"; styles["Heading 1"].font.size = Pt(15); styles["Heading 1"].font.color.rgb = RGBColor(0, 0, 0)
    styles["Heading 2"].font.name = "Arial"; styles["Heading 2"].font.size = Pt(12); styles["Heading 2"].font.color.rgb = RGBColor(0, 0, 0)
    brand = snapshot.get("branding") or {}
    if brand.get("brand_type") == "INTERNAL" and logo_path and Path(logo_path).exists():
        document.add_paragraph().add_run().add_picture(logo_path, width=Inches(1.5))
    else:
        paragraph = document.add_paragraph()
        run = paragraph.add_run(_text(brand.get("practice_name"), "Registered consultant practice")); run.bold = True; run.font.size = Pt(12)
    document.add_heading("Nutrition Plan", 0)
    metadata = document.add_table(rows=3, cols=4); metadata.alignment = WD_TABLE_ALIGNMENT.CENTER
    values = (("Client", _text(snapshot.get("client_name")), "Plan", _text(snapshot.get("title"))),
              ("Consultant", _text(brand.get("consultant_name")), "Version", f"{snapshot.get('version')} - {_text(snapshot.get('status'))}"),
              ("Approved", _text(snapshot.get("approved_at"), "Not approved"), "Reference", _text(snapshot.get("reference"))))
    for row, row_values in zip(metadata.rows, values):
        for index, value in enumerate(row_values):
            _set_cell_text(row.cells[index], value, bold=index % 2 == 0)
            _shade(row.cells[index], "EFF6FF")
    document.add_heading("Plan Goals and Targets", 1)
    targets = snapshot.get("targets") or {}
    target_table = document.add_table(rows=0, cols=2); target_table.style = "Table Grid"
    for label, value in (("Energy", _number(targets.get("calories"), " kcal/day")), ("Protein", _number(targets.get("protein"), " g/day")),
                         ("Carbohydrate", _number(targets.get("carbohydrate"), " g/day")), ("Fat", _number(targets.get("fat"), " g/day")), ("Fibre", _number(targets.get("fibre"), " g/day"))):
        cells = target_table.add_row().cells; _set_cell_text(cells[0], label, bold=True); _set_cell_text(cells[1], value)
    document.add_paragraph("Targets are displayed from the exact saved plan version. They are not recalculated by this document.")
    if snapshot.get("warnings"):
        document.add_heading("Data Limitations", 2)
        for warning in snapshot["warnings"]:
            document.add_paragraph(_text(warning), style="List Bullet")
    document.add_section(WD_SECTION.NEW_PAGE)
    document.add_heading("Meal-wise Alternatives", 0)
    for meal_head, options in _group_options(snapshot).items():
        document.add_heading(MEAL_LABELS.get(meal_head, meal_head.replace("_", " ").title()), 2)
        table = document.add_table(rows=1, cols=3); table.style = "Table Grid"; table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        for cell, value in zip(table.rows[0].cells, ("Option", "Foods and quantities", "Nutrition")):
            _set_cell_text(cell, value, bold=True, white=True); _shade(cell, "0B1F3A")
        for index, option in enumerate(options, 1):
            nutrition = option.get("nutrition") or {}
            nutrients = f"{_number(nutrition.get('kcal'), ' kcal')} | {_number(nutrition.get('protein'), ' g protein')}"
            cells = table.add_row().cells
            _set_cell_text(cells[0], str(index)); _set_cell_text(cells[1], _component_summary(option)); _set_cell_text(cells[2], nutrients, size=8)
    document.add_section(WD_SECTION.NEW_PAGE)
    document.add_heading("Selected Day and Guidance", 0)
    totals = _selected_totals(snapshot)
    document.add_heading("Selected day totals", 1)
    totals_table = document.add_table(rows=0, cols=2); totals_table.style = "Table Grid"
    for label, value in (("Energy", _number(totals["kcal"], " kcal")), ("Protein", _number(totals["protein"], " g")),
                         ("Carbohydrate", _number(totals["carbohydrate"], " g")), ("Fat", _number(totals["fat"], " g")), ("Fibre", _number(totals["fibre"], " g"))):
        cells = totals_table.add_row().cells; _set_cell_text(cells[0], label, bold=True); _set_cell_text(cells[1], value)
    document.add_paragraph("Totals use one selected option per meal. Mutually exclusive alternatives are never summed.")
    for heading, items in (("Eating-out Guidance", snapshot.get("eating_out_guidance")), ("Daily Habits", snapshot.get("daily_habits")), ("Food Safety", snapshot.get("food_safety")), ("Follow-up", snapshot.get("follow_up"))):
        document.add_heading(heading, 1)
        for item in items or ["Follow the consultant's saved instructions and review the plan at the agreed follow-up."]:
            document.add_paragraph(_text(item), style="List Bullet")
    document.add_heading("Plan Basis and Limitations", 1)
    document.add_paragraph("This document reproduces the authorised saved plan version and available governed nutrition snapshots. Missing values remain marked as unavailable. It does not replace medical diagnosis or emergency care.")
    footer = document.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Confidential nutrition plan - share only through authorised channels | ")
    _add_page_field(footer)
    properties = document.core_properties
    properties.title = _text(snapshot.get("title"), "Diet Plan")
    properties.author = _text(brand.get("practice_name"), "Consultant practice")
    output = BytesIO(); document.save(output); return output.getvalue()
