#!/usr/bin/env python3
"""Execute exact extension sources in the installed PopClip JavaScript test harness.

PopClip 2024.3's runjs harness does not resolve package imports, so inline the local
modules for this test only. Axios and URL still come from the real PopClip runtime.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
APP = "/Applications/PopClip.app/Contents/MacOS/PopClip"


def run(package, live=False):
    definitions = []
    for filename in ("core.js", "main.js", "prompts.json", "langs.json"):
        source = (package / filename).read_text()
        if filename.endswith(".json"):
            source = "module.exports = " + source + ";"
        definitions.append(json.dumps("./" + filename) + ": function(require, module, exports, popclip) {\n" + source + "\n}")
    if live:
        # Credential stays inside a mode-0600 file in a temporary mode-0700 local directory.
        # Only the existing Microsoft endpoint receives it. No raw transport errors are printed.
        access = json.loads((package / "access.json").read_text())
        definitions.append('"./access.json": function(require, module) { module.exports = ' + json.dumps(access) + '; }')
        entry = '''
const main = require("./main.js");
return main.action({text:"The GPU processes data in parallel."}, {engine:"original", destlang:"zh-Hans"})
  .then(result => {
    if (typeof result !== "string" || !result.trim()) throw new Error("No translation returned by extension entrypoint");
    print("PASS Microsoft live translation: " + result);
  }).catch(() => { print("FAIL Microsoft live translation: extension entrypoint did not return a translation"); });
'''
    else:
        entry = (ROOT / "tests/native-runtime.js").read_text()
    bundled = 'const builtinRequire = require;\nconst factories = {\n' + ',\n'.join(definitions) + '''
};
const cache = {};
// The command-line harness has no selected text or click-modifier context.
const testPopclip = {modifiers:{option:false}, showText: message => print("FAIL action: " + message)};
function localRequire(name) {
  if (!factories[name]) return builtinRequire(name);
  if (!cache[name]) {
    const module = {exports:{}};
    cache[name] = module;
    factories[name](localRequire, module, module.exports, testPopclip);
  }
  return cache[name].exports;
}
return (async function(require) {
''' + entry + '\n})(localRequire);\n'
    with tempfile.TemporaryDirectory(prefix="popclip-runtime-") as temp:
        script = Path(temp) / "test.js"
        script.write_text(bundled)
        script.chmod(0o600)
        result = subprocess.run([APP, "runjs", "test.js"], cwd=temp, capture_output=True, text=True, timeout=90)
    # All test output is synthetic, or the translation of the public sample sentence above.
    output = result.stdout + result.stderr
    for line in output.splitlines():
        if "PASS " in line or "FAIL " in line or "Done:" in line:
            print(line)
    expected = "PASS Microsoft live translation:" if live else "PASS native PopClip runtime;"
    if result.returncode or expected not in output:
        raise SystemExit("Native test did not pass (exit=" + str(result.returncode) + ").")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=ROOT / "SmartTranslate.popclipext")
    parser.add_argument("--live-microsoft", action="store_true")
    args = parser.parse_args()
    run(args.package, args.live_microsoft)
