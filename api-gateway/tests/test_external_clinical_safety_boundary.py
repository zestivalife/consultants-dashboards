from pathlib import Path


def test_external_legacy_simulated_report_route_is_fail_closed():
    source=Path("app/routers/proxy.py").read_text()
    assert 'LEGACY_SIMULATED_REPORT_PATH = "/api/v1/profile/upload-report"' in source
    assert 'EXTERNAL_TENANT_TYPES = {"INDEPENDENT_CONSULTANT", "PRACTICE", "CLINIC"}' in source
    assert '"CLINICAL_EXTRACTION_UNAVAILABLE"' in source
    assert 'mutation_performed=False' in source


def test_shared_profile_service_and_internal_authority_are_not_modified_by_the_boundary():
    source=Path("app/routers/proxy.py").read_text()
    assert "tenant_type in EXTERNAL_TENANT_TYPES" in source
    assert 'INTERNAL_PROFILE_PREFIX = "/api/v1/practice-operations/internal-client-profiles"' in source

