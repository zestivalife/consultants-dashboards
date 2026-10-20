from pathlib import Path
import pytest
from pydantic import ValidationError
from app.marketplace import ConsultantContactSave, ProfilePhotoPrepare

ROOT=Path(__file__).parents[1]

def test_contact_contract_requires_country_and_national_number():
    value=ConsultantContactSave(country_iso2="IN",national_number="9876543210")
    assert value.country_iso2=="IN"
    with pytest.raises(ValidationError):ConsultantContactSave(country_iso2="I",national_number="1")

def test_photo_contract_accepts_only_governed_image_types_and_size():
    assert ProfilePhotoPrepare(filename="profile.jpg",content_type="image/jpeg",size_bytes=1024).size_bytes==1024
    with pytest.raises(ValidationError):ProfilePhotoPrepare(filename="profile.pdf",content_type="application/pdf",size_bytes=1024)
    with pytest.raises(ValidationError):ProfilePhotoPrepare(filename="large.png",content_type="image/png",size_bytes=5*1024*1024+1)

def test_migration_is_external_only_and_additive():
    migration=(ROOT/"alembic/versions/0050_external_profile_contact_photo.py").read_text()
    assert "down_revision='0049_global_search_activity'" in migration
    assert "external_consultant_contact_profiles" in migration
    assert "external_consultant_profile_photos" in migration
    for frozen in ["internal_","diet_plan","common_food","biomarker_observation"]:assert frozen not in migration.lower()

def test_routes_parse_e164_and_complete_object_storage_lifecycle():
    main=(ROOT/"app/main.py").read_text()
    for proof in ["phonenumbers.is_valid_number","PhoneNumberFormat.E164","signed_upload","verify_uploaded_object","signed_view"]:assert proof in main
    assert '@app.put("/api/v1/practice-operations/marketplace/contact")' in main
    assert '@app.post("/api/v1/practice-operations/marketplace/profile/photo-finalise")' in main
