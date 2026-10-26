from pathlib import Path

from app.document_storage import InvalidDocument, new_credential_evidence_key, verify_jpeg_object
from app.marketplace import QualificationEvidencePrepare
from pydantic import ValidationError
import pytest

ROOT = Path(__file__).parents[1]


def test_credential_upload_contract_is_jpeg_only_and_one_megabyte():
    valid = QualificationEvidencePrepare(filename="degree.jpeg", content_type="image/jpeg", size_bytes=1024 * 1024)
    assert valid.size_bytes == 1048576
    with pytest.raises(ValidationError):
        QualificationEvidencePrepare(filename="degree.png", content_type="image/png", size_bytes=10)
    with pytest.raises(ValidationError):
        QualificationEvidencePrepare(filename="degree.jpg", content_type="image/jpeg", size_bytes=1048577)


def test_credential_objects_have_a_separate_private_prefix():
    key = new_credential_evidence_key("tenant-a", "profile-a", "qualification-a", "degree.JPG")
    assert key.startswith("external-marketplace-credentials/tenant-a/profile-a/qualification-a/")
    assert key.endswith(".jpg")


def test_marketplace_routes_require_private_evidence_before_verification():
    main = (ROOT / "app/main.py").read_text()
    assert 'qualifications/{qualification_id}/evidence-upload' in main
    assert 'qualifications/{qualification_id}/evidence-finalise' in main
    assert 'admin/marketplace/qualifications/{qualification_id}/evidence' in main
    assert 'QUALIFICATION_EVIDENCE_REQUIRED' in main
    assert "verify_jpeg_object" in main
    assert "PRACTITIONER_PRIVATE" in main
    assert "public\":False" in main

