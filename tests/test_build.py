"""Check release isolation and reproducibility with fake credentials, never the user's files."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import plistlib
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

PROJECT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build", PROJECT / "scripts/build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        source = self.root / "SmartTranslate.popclipext"
        shutil.copytree(PROJECT / "SmartTranslate.popclipext", source)
        legacy = self.root / "old-extension"
        legacy.mkdir()
        (legacy / "access.json").write_text('{"access":"FAKE-LEGACY-CREDENTIAL"}')
        (source / "access.json").write_text('{"access":"FAKE-ACCIDENTAL-CREDENTIAL"}')
        (source / "local.js").write_text('throw new Error("Do not publish this");')
        self.prefs = self.root / "preferences.plist"
        self.prefs.write_bytes(plistlib.dumps({"extension#com.popclip.extension.instant-translate#destlang": "ja"}))
        for key, value in {"ROOT": self.root, "SOURCE": source, "LEGACY": legacy,
                           "PRIVATE": self.root / "private", "PREFS": self.prefs}.items():
            patcher = patch.object(builder, key, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def build(self, local=False):
        with contextlib.redirect_stdout(io.StringIO()):
            return builder.build(local)

    def test_public_package_allowlist_and_reproducible_checksum(self):
        archive = self.build()
        first = archive.read_bytes()
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(set(z.namelist()), {"SmartTranslate.popclipext/" + name for name in builder.FILES})
            self.assertNotIn(b"FAKE-", b"".join(z.read(name) for name in z.namelist()))
        self.assertEqual(self.build().read_bytes(), first)
        self.assertEqual(archive.with_suffix(".popclipextz.sha256").read_text().split()[0], hashlib.sha256(first).hexdigest())

    def test_private_migration_preserves_engine_language_and_permissions(self):
        archive = self.build(local=True)
        self.assertNotIn("dist", archive.parts)
        self.assertEqual(stat.S_IMODE(archive.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(archive.parent.stat().st_mode), 0o700)
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(json.loads(z.read("SmartTranslate.popclipext/access.json"))["access"], "FAKE-LEGACY-CREDENTIAL")
            local = z.read("SmartTranslate.popclipext/local.js").decode()
            self.assertIn('defaultValue = "original"', local)
            self.assertIn('defaultValue = "ja"', local)
            self.assertEqual(json.loads(z.read("SmartTranslate.popclipext/Config.json"))["module"], "local.js")
        self.assertFalse((self.root / "dist").exists())

    def test_bad_preferences_do_not_change_local_engine_default(self):
        self.prefs.write_bytes(b"not a plist")
        archive = self.build(local=True)
        with zipfile.ZipFile(archive) as z:
            self.assertIn('defaultValue = "original"', z.read("SmartTranslate.popclipext/local.js").decode())

    def test_missing_legacy_access_fails_without_creating_a_package(self):
        (builder.LEGACY / "access.json").unlink()
        with self.assertRaises(SystemExit):
            self.build(local=True)
        self.assertFalse(builder.PRIVATE.exists())


if __name__ == "__main__":
    unittest.main()
