from pathlib import Path


SOURCE = Path(__file__).parents[1] / "app" / "main.py"


def test_nullable_query_filters_have_explicit_database_types() -> None:
    source = SOURCE.read_text()

    assert "CAST(:appointment AS uuid) IS NULL" in source
    assert "CAST(:client AS text) IS NULL OR cp.client_id=CAST(:client AS text)" in source
    assert "CAST(:client AS text) IS NULL OR a.client_id=CAST(:client AS text)" in source
    assert "CAST(:status AS text) IS NULL" in source
    assert "CAST(:search AS text) IS NULL" in source
    assert "CAST(:scope AS text) IS NULL" in source
    assert "CAST(:type AS text) IS NULL" in source
    assert "CAST(:active AS boolean) IS NULL" in source
    assert "CAST(:state AS text) IS NULL" in source


def test_no_untyped_nullable_filter_remains() -> None:
    source = SOURCE.read_text()

    assert ":client IS NULL" not in source
    assert ":status IS NULL" not in source
    assert ":search IS NULL" not in source
    assert ":scope IS NULL" not in source
    assert ":type IS NULL" not in source
    assert ":active IS NULL" not in source
    assert ":state IS NULL" not in source
    assert ":priority IS NULL" not in source
