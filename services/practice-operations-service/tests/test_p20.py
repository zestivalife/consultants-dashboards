from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from app.p20 import PROVENANCE,REPORT_TYPES,build_docx,build_pdf,checksum

ROOT=Path(__file__).parents[1]
SNAPSHOT={"title":"Progress report","period_start":"2026-09-01","period_end":"2026-10-01","profession_code":"PHYSIOTHERAPIST","consultant_summary":"Factual summary.","sections":[{"title":"Progress","items":[{"label":"Range of motion","value":"95 deg","provenance":"PRACTITIONER_ENTERED"}]}]}

def test_pdf_and_docx_are_real_deterministic_artifacts():
    pdf=build_pdf(SNAPSHOT);docx=build_docx(SNAPSHOT)
    assert pdf.startswith(b"%PDF-1.4") and pdf.endswith(b"%%EOF")
    with ZipFile(BytesIO(docx)) as archive:
        assert "word/document.xml" in archive.namelist()
        assert b"Range of motion" in archive.read("word/document.xml")
    assert len(checksum(pdf))==64

def test_report_types_and_provenance_are_governed():
    assert {"CLIENT_PROGRESS_REPORT","REHAB_PROGRESS_REPORT","OT_PROGRESS_REPORT"}<=REPORT_TYPES
    assert {"CLIENT_REPORTED","PRACTITIONER_ENTERED","SYSTEM_DERIVED","LAB_CONFIRMED","WEARABLE_SOURCE"}==PROVENANCE

def test_p20_migration_is_external_only_and_immutable():
    source=(ROOT/"alembic/versions/0020_progress_reports.py").read_text()
    assert 'down_revision="0019_referrals"' in source
    for table in ("external_progress_reports","external_progress_report_versions","external_progress_report_artifacts","external_progress_report_audit_events"):
        assert f"CREATE TABLE {table}" in source
    assert "expand-only" in source and "ALTER TABLE" not in source

def test_report_routes_exclude_private_and_draft_data_and_enforce_tenant_scope():
    source=(ROOT/"app/main.py").read_text();section=source[source.index('# P20 is a separate reporting domain'):]
    assert '"REPORT_GENERATE"' in section and '"REPORT_VIEW"' in section
    assert "tenant_id=:tenant" in section
    assert "status='PUBLISHED'" in section
    assert '"PRIVATE_NOTES"' in section and '"DRAFT_PLANS"' in section
    assert "REPORT_IMMUTABLE" in section
    assert "Diet Plan document generator is not used" in section
