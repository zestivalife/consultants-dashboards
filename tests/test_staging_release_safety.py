import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_guard", ROOT / "scripts/validate_staging_release.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
TOPOLOGY = json.loads((ROOT / "deploy/staging/topology.json").read_text())
MANIFEST = json.loads((ROOT / "deploy/staging/release-manifest.json").read_text())


def complete_manifest():
    result = copy.deepcopy(MANIFEST)
    result["images"] = [
        {
            "service": service,
            "source_sha": result["provider_sha"] if service == "fiteatsy-backend" else result["consumer_sha"],
            "digest": "sha256:" + (str(index % 10) * 64),
            "tested": True,
        }
        for index, service in enumerate(sorted(MODULE.REQUIRED_SERVICES), 1)
    ]
    return result


def test_complete_exact_sha_digest_manifest_passes():
    assert MODULE.validate(TOPOLOGY, complete_manifest()) == []


def test_manifest_rejects_sha_digest_mismatch():
    manifest = complete_manifest()
    manifest["images"][0]["source_sha"] = "0" * 40
    assert any("source SHA" in error for error in MODULE.validate(TOPOLOGY, manifest))


def test_manifest_rejects_mutable_or_missing_image_evidence():
    manifest = complete_manifest()
    manifest["images"][0]["digest"] = "latest"
    manifest["images"][1]["tested"] = False
    errors = MODULE.validate(TOPOLOGY, manifest)
    assert any("immutable digest" in error for error in errors)
    assert any("has not passed tests" in error for error in errors)


def test_topology_rejects_production_database_and_notifications():
    topology = copy.deepcopy(TOPOLOGY)
    topology["data_services"]["postgres"]["host"] = "postgres-production.railway.internal"
    topology["safety"]["notification_mode"] = "live"
    errors = MODULE.validate(topology, complete_manifest())
    assert any("host is not staging-isolated" in error for error in errors)
    assert any("sink mode" in error for error in errors)


def test_build_pending_manifest_is_not_deployable():
    assert any("images are required" in error for error in MODULE.validate(TOPOLOGY, MANIFEST))
