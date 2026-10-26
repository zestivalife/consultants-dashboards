from pathlib import Path

from app.document_storage import new_credential_evidence_key
from app.marketplace import QualificationEvidencePrepare
from pydantic import ValidationError
import pytest

ROOT = Path(__file__).parents[1]


def test_credential_upload_contract_supports_common_safe_formats_up_to_ten_megabytes():
    for filename, content_type in (("degree.jpeg", "image/jpeg"), ("degree.png", "image/png"), ("degree.webp", "image/webp"), ("degree.pdf", "application/pdf")):
        valid = QualificationEvidencePrepare(filename=filename, content_type=content_type, size_bytes=10 * 1024 * 1024)
        assert valid.size_bytes == 10485760
    with pytest.raises(ValidationError):
        QualificationEvidencePrepare(filename="degree.exe", content_type="application/octet-stream", size_bytes=10)
    with pytest.raises(ValidationError):
        QualificationEvidencePrepare(filename="degree.jpg", content_type="image/jpeg", size_bytes=10485761)


def test_credential_objects_have_a_separate_private_prefix():
    key = new_credential_evidence_key("tenant-a", "profile-a", "qualification-a", "degree.JPG")
    assert key.startswith("external-marketplace-credentials/tenant-a/profile-a/qualification-a/")
    assert key.endswith(".jpg")


def test_marketplace_routes_keep_private_evidence_optional_for_manual_verification():
    main = (ROOT / "app/main.py").read_text()
    assert 'qualifications/{qualification_id}/evidence-upload' in main
    assert 'qualifications/{qualification_id}/evidence-finalise' in main
    assert 'admin/marketplace/qualifications/{qualification_id}/evidence' in main
    assert 'QUALIFICATION_EVIDENCE_REQUIRED' not in main
    assert "verify_uploaded_object" in main
    assert '"image/jpeg","image/png","image/webp","application/pdf"' in main
    assert "PRACTITIONER_PRIVATE" in main
    assert "public\":False" in main
