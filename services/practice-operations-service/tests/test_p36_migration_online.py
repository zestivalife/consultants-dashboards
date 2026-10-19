from pathlib import Path


def test_booking_policy_json_uses_driver_sql_for_online_migration():
    source = (Path(__file__).parents[1] / "alembic/versions/0036_marketplace_booking_conversion.py").read_text()
    assert "op.get_bind().exec_driver_sql" in source
    assert "request_enrolment_enabled" in source
