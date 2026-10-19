from pathlib import Path


SOURCE = Path(__file__).parents[1] / "app" / "main.py"


def test_client_packages_optional_client_filter_has_an_explicit_uuid_type() -> None:
    source = SOURCE.read_text()

    assert "CAST(:client AS uuid) IS NULL OR cp.client_id=CAST(:client AS uuid)" in source
