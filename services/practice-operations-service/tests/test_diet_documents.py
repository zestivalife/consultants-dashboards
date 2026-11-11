from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.diet_documents import MEAL_LABELS, build_diet_docx, build_diet_pdf


def snapshot(brand_type="EXTERNAL"):
    options = []
    for meal_index, meal_head in enumerate(MEAL_LABELS):
        for option_index in range(2):
            options.append({
                "mealHead": meal_head,
                "selected": option_index == 1,
                "components": [{
                    "foodId": f"CF_{meal_index}_{option_index}",
                    "foodDisplayNameSnapshot": f"Governed food {meal_index}-{option_index}",
                    "servingDisplayNameSnapshot": "1 bowl",
                    "grams": 100 + option_index,
                }],
                "nutrition": {
                    "kcal": 100 + meal_index * 10 + option_index,
                    "protein": 10 + option_index,
                    "carbs": 15 + option_index,
                    "fat": 4 + option_index,
                    "fibre": None if meal_index == 0 else 2,
                },
            })
    return {
        "title": "Synthetic governed nutrition plan",
        "client_name": "Synthetic Client",
        "version": 3,
        "status": "APPROVED",
        "approved_at": "2026-11-11T09:00:00+05:30",
        "reference": "synthetic-plan:v3",
        "branding": {
            "brand_type": brand_type,
            "practice_name": "Synthetic Nutrition Practice",
            "consultant_name": "Synthetic Consultant",
        },
        "targets": {"calories": 4593, "protein": 150, "carbohydrate": 300, "fat": 80, "fibre": None},
        "options": options,
        "warnings": ["Fibre is unavailable for one governed option and was not estimated."],
        "daily_habits": ["Use the saved hydration guidance."],
    }


def test_pdf_contains_exact_version_branding_seven_meals_and_no_alternative_sum():
    payload = snapshot()
    content = build_diet_pdf(payload)
    assert content.startswith(b"%PDF")
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
    assert "Synthetic Nutrition Practice" in text
    assert "Synthetic Client" in text
    assert "3 - APPROVED" in text
    assert "4593 kcal/day" in text
    for meal_label in MEAL_LABELS.values():
        assert meal_label in text
    # Selected totals use option 2 from every meal: 101+111+...+161 = 917.
    assert "917 kcal" in text
    assert "1834 kcal" not in text
    assert "Not available" in text


def test_docx_is_editable_and_matches_exact_saved_content():
    payload = snapshot()
    document = Document(BytesIO(build_diet_docx(payload)))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    table_text = "\n".join(cell.text for table in document.tables for row in table.rows for cell in row.cells)
    combined = f"{text}\n{table_text}"
    assert "Synthetic Nutrition Practice" in combined
    assert "Synthetic Client" in combined
    assert "3 - APPROVED" in combined
    assert "4593 kcal/day" in combined
    assert "917 kcal" in combined
    for meal_label in MEAL_LABELS.values():
        assert meal_label in combined
    assert any("PAGE" in run._r.xml for section in document.sections for run in section.footer.paragraphs[0].runs)


def test_internal_brand_uses_official_asset_and_external_brand_does_not_require_logo():
    logo = Path(__file__).parents[1] / "app" / "assets" / "zestiva-logo.png"
    assert logo.is_file()
    internal = Document(BytesIO(build_diet_docx(snapshot("INTERNAL"), str(logo))))
    assert len(internal.inline_shapes) == 1
    external = Document(BytesIO(build_diet_docx(snapshot("EXTERNAL"), str(logo))))
    assert len(external.inline_shapes) == 0
    assert "Synthetic Nutrition Practice" in "\n".join(p.text for p in external.paragraphs)
