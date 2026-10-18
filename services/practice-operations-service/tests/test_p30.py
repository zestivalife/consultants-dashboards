from app.p30 import ALLOWED_EXPORT_SECTIONS, EXCLUDED_BY_DEFAULT, export_checksum, validate_export_sections

def test_export_allowlist_and_private_note_boundary():
    assert validate_export_sections(["CONSENTS","DOCUMENTS"]) == ["CONSENTS","DOCUMENTS"]
    assert "PRIVATE_NOTES" not in ALLOWED_EXPORT_SECTIONS
    assert "PRIVATE_NOTES" in EXCLUDED_BY_DEFAULT
    try: validate_export_sections(["PRIVATE_NOTES"])
    except ValueError: pass
    else: raise AssertionError("private notes must not be exportable")

def test_export_checksum_is_deterministic():
    assert export_checksum({"b":2,"a":1}) == export_checksum({"a":1,"b":2})

def test_p30_schema_and_tenant_scoping():
    from pathlib import Path
    root=Path(__file__).parents[1]
    migration=(root/"alembic/versions/0030_compliance_audit.py").read_text()
    main=(root/"app/main.py").read_text()
    assert "external_data_export_requests" in migration
    assert "private_notes_included=FALSE" in migration
    assert "external_compliance_audit_events" in migration
    assert "tenant_id=:tenant" in main
    assert "legal_compliance_certification\":False" in main
    assert "external_session_notes" not in main[main.index("queries={",main.index("export_client_data")):main.index("for section in sections",main.index("export_client_data"))]
