#!/usr/bin/env python3
"""Build a reproducible public package, or a credential-bearing private local package."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import stat
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "SmartTranslate.popclipext"
LEGACY = Path.home() / "Library/Application Support/PopClip/Extensions/InstantTranslate.popclipext"
PRIVATE = Path.home() / "Library/Application Support/PopClipSmartTranslate"
PREFS = Path.home() / "Library/Preferences/com.pilotmoon.popclip.plist"
FILES = ("Config.json", "main.js", "core.js", "prompts.json", "langs.json", "NOTICE.txt")


def build(local=False):
    if local and not (LEGACY / "access.json").is_file():
        raise SystemExit("未找到原 Instant Translate 凭据；未创建迁移包。可不加 --local 构建普通包。")
    if local:
        PRIVATE.mkdir(parents=True, exist_ok=True, mode=0o700)
        PRIVATE.chmod(0o700)
        output = PRIVATE / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    else:
        output = ROOT / "dist"
    output.mkdir(parents=True, exist_ok=True, mode=0o700 if local else 0o755)
    package = output / SOURCE.name
    if package.exists():
        shutil.rmtree(package)
    package.mkdir(mode=0o700 if local else 0o755)
    for name in FILES:
        shutil.copyfile(SOURCE / name, package / name)
    archive_files = list(FILES)
    if local:
        # Keep bundled credentials outside the repository and all public build directories.
        shutil.copyfile(LEGACY / "access.json", package / "access.json")
        local_module = ('const extension = require("./main.js");\n'
                        'extension.options.find(option => option.identifier === "engine").defaultValue = "original";\n')
        destination = None
        if PREFS.is_file():
            try:
                destination = plistlib.loads(PREFS.read_bytes()).get("extension#com.popclip.extension.instant-translate#destlang")
            except (OSError, plistlib.InvalidFileException, ValueError):
                pass
        languages = json.loads((package / "langs.json").read_text())["translation"]
        if destination in languages:
            local_module += ('extension.options.find(option => option.identifier === "destlang").defaultValue = '
                             + json.dumps(destination) + ';\n')
        local_module += 'module.exports = extension;\n'
        (package / "local.js").write_text(local_module)
        config = json.loads((package / "Config.json").read_text())
        config["module"] = "local.js"
        (package / "Config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
        archive_files += ["access.json", "local.js"]
        for name in archive_files:
            (package / name).chmod(0o600)
    archive = output / "SmartTranslate.popclipextz"
    temporary_archive = archive.with_suffix(".tmp")
    with zipfile.ZipFile(temporary_archive, "w", zipfile.ZIP_DEFLATED) as z:
        # Fixed metadata and an explicit allowlist make public packages reproducible and credential-free.
        for name in sorted(archive_files):
            info = zipfile.ZipInfo(SOURCE.name + "/" + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | (0o600 if local else 0o644)) << 16
            z.writestr(info, (package / name).read_bytes())
    temporary_archive.replace(archive)
    checksum = archive.with_suffix(".popclipextz.sha256")
    checksum.write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + "  " + archive.name + "\n")
    if local:
        archive.chmod(0o600)
        checksum.chmod(0o600)
    print("本机私有安装包（含原翻译凭据，不要分享）：" if local else "无凭据安装包：")
    print(archive)
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", action="store_true", help="在本机私有目录复用已安装 Instant Translate 的凭据和语言")
    build(parser.parse_args().local)
