"""uv で動く同梱のスクリプトの依存が、宣言した Python の範囲のすべての版で入ることを確かめる（ADR-0025）。

PEP 723 の `requires-python` は、どれも同じ範囲（`>=3.X,<3.Y`）でなければならない。範囲の各 minor の版で、
各スクリプトに `uv sync --script <script> --python 3.N` を実行し、1 つでも失敗したら終了コード 1 で止まる。
範囲に入れた版で依存の配布物（wheel）がないと、Python のない PC で uv がその版を取ったときに起動しない
（wiki 0.19.4 で、CPython 3.15 と onnxruntime 1.31.1）。宣言の上限を上げるときは、この確かめが通ってから上げる。

依存の配布物を取るので、ネットにつながる環境で動かす（CI では wiki-mcp.yml）。

    uv run --python 3.12 python -X utf8 tests/wiki/check_script_python_range.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
DECLARATION = re.compile(r'^# requires-python = "(.+)"$', re.MULTILINE)
RANGE = re.compile(r"^>=3\.(\d+),<3\.(\d+)$")


def declared_scripts() -> dict[str, str]:
    found = {}
    for path in sorted(SCRIPTS.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "# /// script" not in source:
            continue
        match = DECLARATION.search(source)
        found[path.name] = match.group(1) if match else ""
    return found


def main() -> int:
    found = declared_scripts()
    values = set(found.values())
    if len(values) != 1:
        print(f"PEP 723 の requires-python が、スクリプトによって違う: {found}", file=sys.stderr)
        return 1
    spec = values.pop()
    match = RANGE.match(spec)
    if not match:
        print(f"requires-python が >=3.X,<3.Y の形でない: {spec!r}", file=sys.stderr)
        return 1
    versions = [f"3.{minor}" for minor in range(int(match.group(1)), int(match.group(2)))]
    print(f"範囲 {spec}: {', '.join(versions)}、スクリプト {len(found)} 本", flush=True)
    failures = []
    for version in versions:
        for name in found:
            command = ["uv", "sync", "--quiet", "--script", str(SCRIPTS / name), "--python", version]
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
            status = "ok" if result.returncode == 0 else f"失敗（終了コード {result.returncode}）"
            print(f"{version} {name}: {status}", flush=True)
            if result.returncode != 0:
                failures.append((version, name, (result.stderr or result.stdout).strip()[-800:]))
    for version, name, detail in failures:
        print(f"\n== {version} {name}\n{detail}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
