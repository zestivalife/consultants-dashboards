from pathlib import Path


def test_container_binds_to_railway_private_ipv6_network() -> None:
    dockerfile = Path(__file__).parents[1] / "Dockerfile"
    source = dockerfile.read_text(encoding="utf-8")

    assert "uvicorn app.main:app --host :: --port ${PORT:-8002}" in source
    assert "uvicorn app.main:app --host 0.0.0.0" not in source
