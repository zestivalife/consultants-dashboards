from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts/build_railway_auth_package.py"
REVISION_SCRIPT = ROOT / "scripts/package_source_revision.sh"
SPEC = importlib.util.spec_from_file_location("railway_package", BUILDER_PATH)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


def run(*args: str, cwd: Path, check: bool = True, env: Optional[dict] = None):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True, env=env)


def initialise_repository(root: Path, include_service: bool = True) -> str:
    (root / "scripts").mkdir(parents=True)
    shutil.copy2(REVISION_SCRIPT, root / "scripts/package_source_revision.sh")
    (root / ".gitignore").write_text(".env\n.pytest_cache/\n", encoding="utf-8")
    if include_service:
        for relative in BUILDER.REQUIRED_FILES:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"fixture:{relative}\n", encoding="utf-8")
        (root / "services/auth-service/.env").write_text("SECRET=no\n", encoding="utf-8")
        (root / "services/auth-service/.pytest_cache").mkdir()
        (root / "services/auth-service/.pytest_cache/cache").write_text("no", encoding="utf-8")
    run("git", "init", cwd=root)
    run("git", "config", "user.email", "packaging@example.invalid", cwd=root)
    run("git", "config", "user.name", "Packaging Test", cwd=root)
    run("git", "add", "scripts", ".gitignore", cwd=root)
    if include_service:
        run("git", "add", "services/auth-service/Dockerfile", "services/auth-service/requirements.txt", "services/auth-service/release.sh", "services/auth-service/app/main.py", "services/auth-service/app/version.py", cwd=root)
    run("git", "commit", "-m", "fixture", cwd=root)
    return run("git", "rev-parse", "HEAD", cwd=root).stdout.strip()


class RevisionValidationTests(unittest.TestCase):
    def test_valid_checkout_revision_is_written_to_package_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            package = Path(temp) / "package"
            root.mkdir()
            revision = initialise_repository(root)
            (package / "services/auth-service").mkdir(parents=True)
            result = run(str(root / "scripts/package_source_revision.sh"), str(package), cwd=root)
            self.assertIn(revision, result.stdout)
            self.assertEqual((package / "services/auth-service/.source-revision").read_text().strip(), revision)
            self.assertFalse((root / "services/auth-service/.source-revision").exists())

    def test_missing_git_head_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            shutil.copy2(REVISION_SCRIPT, root / "scripts/package_source_revision.sh")
            package = root / "package/services/auth-service"
            package.mkdir(parents=True)
            result = run(str(root / "scripts/package_source_revision.sh"), str(root / "package"), cwd=root, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Git checkout root", result.stderr)

    def test_short_malformed_and_non_hex_revisions_are_rejected(self):
        for value in ("", "abc123", "g" * 40, "a" * 39, "a" * 41):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "scripts").mkdir()
                shutil.copy2(REVISION_SCRIPT, root / "scripts/package_source_revision.sh")
                (root / "package/services/auth-service").mkdir(parents=True)
                fake_bin = root / "bin"
                fake_bin.mkdir()
                fake_git = fake_bin / "git"
                fake_git.write_text(
                    "#!/bin/sh\ncase \"$*\" in *--show-toplevel*) printf '%s\\n' \"$(pwd)\";; *HEAD*commit*) printf '%s\\n' '"
                    + value
                    + "';; *) exit 1;; esac\n",
                    encoding="utf-8",
                )
                fake_git.chmod(0o755)
                env = os.environ.copy()
                env["PATH"] = f"{fake_bin}:{env['PATH']}"
                result = run(str(root / "scripts/package_source_revision.sh"), str(root / "package"), cwd=root, check=False, env=env)
                self.assertNotEqual(result.returncode, 0)


class PackageTests(unittest.TestCase):
    def test_clean_checkout_package_layout_archive_and_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            output = Path(temp) / "package"
            archive = Path(temp) / "package.tar.gz"
            root.mkdir()
            revision = initialise_repository(root)
            manifest = BUILDER.build(root, output, archive)
            self.assertEqual(manifest["source_revision"], revision)
            self.assertEqual(manifest["service_root"], "/services/auth-service")
            self.assertTrue((output / "services/auth-service/Dockerfile").is_file())
            self.assertEqual((output / "services/auth-service/.source-revision").read_text().strip(), revision)
            self.assertFalse((output / "services/auth-service/.env").exists())
            self.assertFalse((output / "services/auth-service/.pytest_cache").exists())
            with tarfile.open(archive, "r:gz") as packaged:
                names = packaged.getnames()
            self.assertIn("services/auth-service/Dockerfile", names)
            self.assertIn("services/auth-service/.source-revision", names)

    def test_archive_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            initialise_repository(root)
            digests = []
            for number in (1, 2):
                output = Path(temp) / f"package-{number}"
                archive = Path(temp) / f"package-{number}.tar.gz"
                BUILDER.build(root, output, archive)
                digests.append(hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertEqual(digests[0], digests[1])

    def test_missing_service_directory_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            initialise_repository(root, include_service=False)
            with self.assertRaisesRegex(RuntimeError, "source directory is missing"):
                BUILDER.build(root, Path(temp) / "package")

    def test_dirty_checkout_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            initialise_repository(root)
            (root / "services/auth-service/Dockerfile").write_text("dirty\n")
            with self.assertRaisesRegex(RuntimeError, "dirty Git checkout"):
                BUILDER.build(root, Path(temp) / "package")

    def test_nonempty_output_and_incorrect_provenance_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            revision = initialise_repository(root)
            output = Path(temp) / "package"
            output.mkdir()
            (output / "unexpected").write_text("x")
            with self.assertRaisesRegex(RuntimeError, "must not already contain"):
                BUILDER.build(root, output)
            shutil.rmtree(output)
            BUILDER.build(root, output)
            (output / "services/auth-service/.source-revision").write_text("0" * 40 + "\n")
            with self.assertRaisesRegex(RuntimeError, "does not match"):
                BUILDER.verify_layout(output, revision)


if __name__ == "__main__":
    unittest.main()
