from pathlib import Path


def test_container_honours_railway_runtime_port_on_public_edge() -> None:
    dockerfile = Path(__file__).parents[1] / "Dockerfile"
    source = dockerfile.read_text(encoding="utf-8")

    assert "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8002}" in source
    assert "--port 8002" not in source
