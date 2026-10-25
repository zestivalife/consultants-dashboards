from pathlib import Path


SOURCE = (Path(__file__).parents[1] / "app" / "main.py").read_text()


def test_marketplace_core_profile_can_skip_optional_analytics_projection():
    route = SOURCE[SOURCE.index('@app.get("/api/v1/practice-operations/marketplace/profile")'):SOURCE.index('@app.get("/api/v1/practice-operations/marketplace/readiness")')]
    assert "include_analytics:bool=True" in route
    assert "if not include_analytics:" in route
    assert '"profile":dict(profile)' in route
    assert '"version":dict(version) if version else None' in route
    assert '"qualifications":qualifications' in route
    assert '"analytics":None' in route
