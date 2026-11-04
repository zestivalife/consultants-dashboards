from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_shared_database_services_use_distinct_alembic_version_tables():
    expected = {
        "assessment-service": "assessment_service_alembic_version",
        "nutrition-service": "nutrition_service_alembic_version",
        "scoring-engine-service": "scoring_engine_service_alembic_version",
        "profile-service": "profile_service_alembic_version",
        "practice-operations-service": "practice_operations_alembic_version",
    }

    for service, version_table in expected.items():
        source = (ROOT / service / "alembic" / "env.py").read_text()
        assert version_table in source
        assert source.count("version_table=") >= 2

    assert len(set(expected.values())) == len(expected)


def test_recovered_service_migration_heads_remain_unchanged():
    assessment = (ROOT / "assessment-service/alembic/versions/0001_assessment_tables.py").read_text()
    nutrition = (ROOT / "nutrition-service/alembic/versions/0001_nutrition_tables.py").read_text()
    scoring_1 = (ROOT / "scoring-engine-service/alembic/versions/0001_scoring_tables.py").read_text()
    scoring_2 = (ROOT / "scoring-engine-service/alembic/versions/0002_add_score_metadata.py").read_text()
    scoring_3 = (ROOT / "scoring-engine-service/alembic/versions/0003_normalize_version_defaults.py").read_text()

    assert 'revision: str = "0001"' in assessment
    assert 'down_revision: Union[str, None] = None' in assessment
    assert 'revision: str = "0001"' in nutrition
    assert 'down_revision: Union[str, None] = None' in nutrition
    assert 'revision: str = "0001"' in scoring_1
    assert 'down_revision: Union[str, None] = None' in scoring_1
    assert 'revision: str = "0002"' in scoring_2
    assert 'down_revision: Union[str, None] = "0001"' in scoring_2
    assert 'revision: str = "0003"' in scoring_3
    assert 'down_revision: Union[str, None] = "0002"' in scoring_3
