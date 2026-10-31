from pathlib import Path


SOURCE = (Path(__file__).parents[1] / "app" / "fiteatsy_connections.py").read_text()


def test_connection_details_returns_complete_care_ledger():
    start = SOURCE.index('async def connection_details(')
    end = SOURCE.index('@router.post("/api/v1/practice-operations/fiteatsy-connections/invitations/', start)
    handler = SOURCE[start:end]

    assert "external_fiteatsy_programmes" in handler
    assert "external_fiteatsy_plan_publications" in handler
    assert "external_fiteatsy_appointments" in handler
    assert '"plan_publications": plan_publications' in handler
    assert '"appointments": appointments' in handler


def test_every_connection_detail_child_query_is_tenant_and_consultant_scoped():
    start = SOURCE.index('async def connection_details(')
    end = SOURCE.index('@router.post("/api/v1/practice-operations/fiteatsy-connections/invitations/', start)
    handler = SOURCE[start:end]

    for table in (
        "external_fiteatsy_programmes",
        "external_fiteatsy_plan_publications",
        "external_fiteatsy_appointments",
    ):
        query = next(line for line in handler.splitlines() if table in line)
        assert "tenant_id=:tenant" in query
        assert "consultant_id=:consultant" in query
