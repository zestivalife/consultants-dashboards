import copy, datetime as dt, importlib.util, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gate", ROOT / "scripts/validate_staging_release.py")
GATE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(GATE)
TOPOLOGY = json.loads((ROOT / "deploy/staging/topology.json").read_text())
BASE = json.loads((ROOT / "deploy/staging/release-manifest.json").read_text())
NOW = dt.datetime(2026, 11, 5, tzinfo=dt.timezone.utc)

def fp(char): return "sha256:" + char * 64

def manifest(enabled=True):
    value = copy.deepcopy(BASE); value["deployment_enabled"] = enabled
    value["images"] = []
    for index, service in enumerate(sorted(GATE.REQUIRED_SERVICES), 1):
        value["images"].append({
            "service": service,
            "source_sha": value["provider_sha"] if service == "fiteatsy-backend" else value["consumer_sha"],
            "registry_reference": f"ghcr.io/zestivalife/{service}@{fp(str(index))}",
            "digest": fp(str(index)), "dockerfile_sha256": fp("a"), "context_sha256": fp("b")
        })
    return value

def runtime():
    return {
        "database_identity": "staging-postgres-pending", "redis_identity": "staging-redis-pending",
        "production_fingerprints": [fp("f")],
        "effective": {"database": fp("1"), "redis": fp("2"), "signing_key": fp("3"), "service_endpoints": [fp("4")], "storage": fp("5"), "notifications": fp("6")}
    }

class Verifier:
    def __init__(self, value, *, ci=True, provenance=True, scan=True): self.value=value; self.ci=ci; self.provenance=provenance; self.scan=scan
    def registry_digest(self, reference):
        repository=reference.rsplit("@",1)[0]
        return next(x["digest"] for x in self.value["images"] if x["registry_reference"].rsplit("@",1)[0] == repository)
    def image_config(self, image):
        repository=image.rsplit("@",1)[0]
        service = next(x for x in self.value["images"] if x["registry_reference"].rsplit("@",1)[0] == repository)
        return {"config": {"Labels": {"org.opencontainers.image.revision": service["source_sha"]}}}
    def verify_image_signature(self, image): return True
    def verify_attestation(self, image, kind):
        repository=image.rsplit("@",1)[0]
        item = next(x for x in self.value["images"] if x["registry_reference"].rsplit("@",1)[0] == repository)
        subject = [{"digest": {"sha256": item["digest"].removeprefix("sha256:")}}]
        if kind == "slsaprovenance":
            if not self.provenance: return []
            return [{"subject": subject, "predicate": {"buildDefinition": {"externalParameters": {"source_sha": item["source_sha"], "dockerfile_sha256": item["dockerfile_sha256"], "context_sha256": item["context_sha256"]}}}}]
        return [{"subject": subject, "predicate": {"result": "pass"}}] if self.scan else []
    def ci_run(self, repository, run_id):
        sha = self.value["provider_sha"] if repository.endswith("Fiteatsy-mobile") else self.value["consumer_sha"]
        return {"head_sha": sha, "status": "completed", "conclusion": "success" if self.ci else "failure"}

def authorization(value, expires="2026-11-06T00:00:00Z"):
    return {"scope": "integrated-staging", "production_authorized": False, "manifest_sha256": GATE.canonical_sha256(value), "expires_at": expires}

def errors(value=None, *, topology=None, rt=None, verifier=None, auth=None, mode="DEPLOY_GATE"):
    value = value or manifest(); return GATE.validate(mode, topology or TOPOLOGY, value, rt if rt is not None else runtime(), verifier or Verifier(value), auth if auth is not None else authorization(value), NOW)

def test_operating_modes_are_separate_and_config_permits_missing_artifacts():
    assert GATE.validate("CONFIG_CHECK", TOPOLOGY, BASE) == []
    assert any("nine services" in x for x in GATE.validate("BUILD_ATTESTATION", TOPOLOGY, BASE, verifier=Verifier(manifest())))

def test_valid_externally_verified_deploy_gate_passes(): assert errors() == []

def test_rejects_invented_but_formatted_digest():
    value=manifest(); verifier=Verifier(copy.deepcopy(value)); value["images"][0]["digest"]=fp("e"); value["images"][0]["registry_reference"]=value["images"][0]["registry_reference"].rsplit("@",1)[0]+"@"+fp("e")
    assert any("invented or stale" in x for x in errors(value, verifier=verifier, auth=authorization(value)))

def test_rejects_falsified_ci_success():
    value=manifest(); assert any("CI result" in x for x in errors(value, verifier=Verifier(value, ci=False)))

def test_rejects_deployment_disabled_manifest():
    value=manifest(False); assert any("deployment_enabled=false" in x for x in errors(value, auth=authorization(value)))

def test_rejects_wrong_source_sha():
    value=manifest(); value["images"][0]["source_sha"]="0"*40
    assert any("wrong source SHA" in x for x in errors(value, verifier=Verifier(value), auth=authorization(value)))

def test_rejects_missing_provenance():
    value=manifest(); assert any("image provenance" in x for x in errors(value, verifier=Verifier(value, provenance=False)))

def test_rejects_production_database_redis_and_service_targets():
    value=manifest(); rt=runtime(); rt["effective"]["database"]=fp("f"); rt["effective"]["redis"]=fp("f"); rt["effective"]["service_endpoints"]=[fp("f")]
    found=errors(value, rt=rt); assert sum("production target" in x for x in found) == 3

def test_rejects_production_notification_credentials():
    value=manifest(); rt=runtime(); rt["effective"]["notifications"]=fp("f")
    assert any("notifications: production target" in x for x in errors(value, rt=rt))

def test_rejects_expired_or_mismatched_authorization():
    value=manifest(); expired=authorization(value, "2026-11-04T00:00:00Z"); expired["manifest_sha256"]=fp("0")
    found=errors(value, auth=expired); assert any("expired" in x for x in found) and any("manifest mismatch" in x for x in found)

def test_rejects_missing_service_image():
    value=manifest(); value["images"].pop()
    assert any("all nine services" in x for x in errors(value, verifier=Verifier(value), auth=authorization(value)))

def test_rejects_unscanned_image():
    value=manifest(); assert any("image is unscanned" in x for x in errors(value, verifier=Verifier(value, scan=False)))

def test_rejects_real_provider_and_public_unallowlisted_database():
    topology=copy.deepcopy(TOPOLOGY); topology["notifications"]["provider"]="twilio"; topology["data_services"]["postgres"]["public"]=True
    found=GATE.validate("CONFIG_CHECK", topology, BASE); assert any("notification providers" in x for x in found) and any("not allowlisted" in x for x in found)

def test_rejects_missing_or_shared_database_identity():
    topology=copy.deepcopy(TOPOLOGY); topology["data_services"]["redis"]["resource_id"]="staging-postgres-pending"
    assert any("shared database identities" in x for x in GATE.validate("CONFIG_CHECK", topology, BASE))

def test_runtime_fingerprinter_never_persists_raw_credentials(tmp_path):
    spec={"database_identity":"staging-postgres-pending","redis_identity":"staging-redis-pending","production_fingerprints":[],"environment_variables":{"database":["TEST_DATABASE_URL"],"redis":["TEST_REDIS_URL"],"signing_key":["TEST_SIGNING_KEY"],"service_endpoints":["TEST_SERVICE_URL"],"storage":["TEST_STORAGE_URL"],"notifications":["TEST_NOTIFICATION_URL"]}}
    spec_path=tmp_path/"spec.json"; output=tmp_path/"runtime.json"; spec_path.write_text(json.dumps(spec))
    env={**os.environ,"ISOLATION_FINGERPRINT_KEY":"k"*32,"TEST_DATABASE_URL":"postgres://production-secret","TEST_REDIS_URL":"redis://production-secret","TEST_SIGNING_KEY":"real-signing-secret","TEST_SERVICE_URL":"https://production-service","TEST_STORAGE_URL":"s3://production-bucket","TEST_NOTIFICATION_URL":"https://real-provider"}
    subprocess.run([sys.executable,str(ROOT/"scripts/fingerprint_runtime_config.py"),"--spec",str(spec_path),"--output",str(output)],env=env,check=True,capture_output=True,text=True)
    content=output.read_text(); assert "production-secret" not in content and "real-signing-secret" not in content and "production-service" not in content
