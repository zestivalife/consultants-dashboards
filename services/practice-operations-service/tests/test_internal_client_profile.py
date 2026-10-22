from pathlib import Path
import pytest

from app.internal_client_profile import bmi, merge_enrichment, projection, validate_enrichment, waist_hip_ratio

ROOT = Path(__file__).parents[1]


def test_measurement_derivations_are_canonical():
    assert bmi(170, 70) == 24.2
    assert bmi(None, 70) is None
    assert waist_hip_ratio(80, 100) == 0.8
    assert waist_hip_ratio(80, 0) is None


def test_validation_limits_goals_and_allowlists_fields():
    assert validate_enrichment({"goals":["Better sleep","Improve energy"]})["goals"] == ["Better sleep","Improve energy"]
    with pytest.raises(ValueError, match="maximum of three"):
        validate_enrichment({"goals":["a","b","c","d"]})
    with pytest.raises(ValueError, match="Unsupported enrichment"):
        validate_enrichment({"consent":True})


def test_explicit_clear_is_preserved_and_projection_is_derived():
    values=validate_enrichment({"medical_history_narrative":"", "measurements":{"height_cm":200,"weight_kg":100,"waist_cm":80,"hip_cm":100,"recorded_at":"2026-10-22T10:00:00+00:00"}})
    assert values["medical_history_narrative"] == ""
    result=projection(values,3,{"source":"INTERNAL_ENRICHMENT"})
    assert result["derived"] == {"bmi":25.0,"waist_hip_ratio":0.8}


def test_additive_migration_and_api_are_internal_tenant_scoped_and_audited():
    migration=(ROOT/"alembic/versions/0052_internal_client_profile_enrichments.py").read_text()
    source=(ROOT/"app/main.py").read_text()
    gateway=(ROOT.parents[1]/"api-gateway/app/routers/proxy.py").read_text()
    assert "internal_client_profile_enrichments" in migration
    assert "PRIMARY KEY (tenant_id, client_id)" in migration
    assert "audit_history JSONB" in migration
    assert "audit_history=audit_history ||" in source
    assert 'ctx.get("tenant_type") != "ZESTIVA_INTERNAL"' in source
    assert "WHERE tenant_id=:tenant AND client_id=:client" in source
    assert "INTERNAL_PROFILE_PREFIX" in gateway
    assert "/v1/consultants/clients/{client_id}/workspace" in gateway
    assert "/v1/external/clients" not in source


def test_concurrency_and_partial_merge_contracts_are_explicit():
    source=(ROOT/"app/main.py").read_text()
    assert "AND version=:version" in source
    merged=merge_enrichment({"measurements":{"height_cm":170,"weight_kg":70},"goals":["A"]},{"measurements":{"weight_kg":71,"recorded_at":"2026-10-22T10:00:00Z"}})
    assert merged["measurements"]["height_cm"] == 170
    assert merged["measurements"]["weight_kg"] == 71
    assert merged["goals"] == ["A"]
    assert "merged_values=merge_enrichment" in source
    assert source.count('"STALE_WRITE"') >= 2
