from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.nutrition_foundation import (
    AssessmentSource,
    ClinicalDocumentLink,
    NutritionAssessmentCreate,
    assessment_fingerprint,
    measurement_calculations,
)

ROOT = Path(__file__).parents[1]


def source(kind, identifier, version="1", **kwargs):
    return AssessmentSource(source_type=kind, source_id=identifier, source_version=version, **kwargs)


def test_simulated_and_unconfirmed_biomarkers_fail_closed():
    with pytest.raises(ValidationError, match="Simulated clinical values"):
        source("BIOMARKER", "obs-1", status="CONFIRMED", data={"canonical_biomarker_id":"hba1c","value":6.1,"unit":"%","source_report_reference":"report-1"}, provenance={"type":"SIMULATED"})
    with pytest.raises(ValidationError, match="Only confirmed biomarkers"):
        source("BIOMARKER", "obs-2", status="EXTRACTED", data={"canonical_biomarker_id":"hba1c","value":6.1,"unit":"%","source_report_reference":"report-1"})


def test_confirmed_biomarker_retains_traceable_source():
    row=source("BIOMARKER","obs-3",status="CONFIRMED",observed_at=datetime(2026,10,1,tzinfo=timezone.utc),data={"canonical_biomarker_id":"hba1c","value":6.1,"unit":"%","source_report_reference":"report-1"},provenance={"confirmed_by":"consultant-1"})
    assert row.data["source_report_reference"] == "report-1"


def test_considerations_require_real_source_observations_and_review_starts_unreviewed():
    with pytest.raises(ValidationError, match="must reference assessment source"):
        NutritionAssessmentCreate(
            consent_state="CONFIRMED",
            sources=[source("CLIENT_INTAKE", "intake-1")],
            nutrition_considerations=[{"code":"LOW_FIBRE_CONTEXT","summary":"Review intake context with the client","source_observation_ids":["missing-source"]}],
        )
    value=NutritionAssessmentCreate(
        consent_state="CONFIRMED",
        sources=[source("CLIENT_INTAKE", "intake-1")],
        nutrition_considerations=[{"code":"LOW_FIBRE_CONTEXT","summary":"Review intake context with the client","source_observation_ids":["intake-1"]}],
    )
    assert value.professional_review_state == "NOT_REVIEWED"


def test_measurement_calculations_are_versioned_and_never_treat_missing_as_zero():
    current=source("MEASUREMENT","measurement-2","2",observed_at=datetime(2026,10,2,tzinfo=timezone.utc),data={"height_cm":170,"weight_kg":70,"waist_cm":80,"hip_cm":100})
    previous=source("MEASUREMENT","measurement-1","1",observed_at=datetime(2026,9,1,tzinfo=timezone.utc),data={"weight_kg":72})
    result=measurement_calculations([previous,current])
    assert result["bmi"] == {"value":24.2,"unit":"kg/m2","version":"bmi.metric.v1"}
    assert result["waist_hip_ratio"]["value"] == 0.8
    assert result["weight_change"]["value"] == -2.0
    empty=measurement_calculations([])
    assert empty["bmi"]["value"] is None and empty["weight_change"]["value"] is None


def test_assessment_fingerprint_is_deterministic_and_source_version_sensitive():
    one=source("CLIENT_INTAKE","intake","1")
    calculations=measurement_calculations([])
    assert assessment_fingerprint("client-1",[one],calculations)==assessment_fingerprint("client-1",[one],calculations)
    assert assessment_fingerprint("client-1",[one],calculations)!=assessment_fingerprint("client-1",[source("CLIENT_INTAKE","intake","2")],calculations)


def test_document_lineage_never_claims_an_unavailable_source_exists():
    with pytest.raises(ValidationError, match="contradict"):
        ClinicalDocumentLink(document_reference="doc",source_available=False,source_status="AVAILABLE")
    value=ClinicalDocumentLink(document_reference="doc",source_available=False,source_status="HISTORICAL_SOURCE_UNAVAILABLE",observation_references=["obs-1"])
    assert value.observation_references == ["obs-1"]


def test_additive_migration_and_external_api_contracts():
    migration=(ROOT/"alembic/versions/0054_external_nutrition_foundation.py").read_text()
    app=(ROOT/"app/main.py").read_text()
    assert 'down_revision = "0053_external_profile"' in migration
    for table in ("external_nutrition_assessments","external_nutrition_assessment_versions","external_nutrition_assessment_inputs","external_diet_plan_assessment_links","external_clinical_document_links","external_nutrition_staleness_events"):
        assert f"CREATE TABLE {table}" in migration
    assert "internal_" not in migration.lower()
    assert "fiteatsy" not in migration.lower()
    for route in ("nutrition-assessment\")","nutrition-assessments\",status_code=201)","diet-plan-assessment-links","clinical-document-links"):
        assert route in app
    assert app.count("denied=await _nutrition_scope(request,db,ctx)") >= 7
    assert "ASSESSMENT_INPUTS_UNCHANGED" in app
    assert "NUTRITION_ASSESSMENT_REQUIRED" in app
