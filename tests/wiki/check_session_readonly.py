"""読み取り専用の raw を、wiki の中の別名を経由して、Claude Code の Write と Edit で書き換えられないかを確かめる。

セッションの取り込みの設計（docs/plans/wiki-session-ingest-2026-11-14.md）の「試験」の「読み取り専用と verify」の、
実際の Claude Code での確かめである。一時ディレクトリに wiki と raw を作り、`wiki_session.py` の `make_read_only`
で raw を読み取り専用にする。wiki の中に、raw のルートを指す別名（`<W>/indexes`）と、raw のルートの親を指す別名
（`<W>/up`）を作る（Windows はジャンクション、ほかはシンボリックリンク）。`claude -p` に、別名を経由して Read、
Write、Edit で raw を書き換えさせ、raw のバイト列、読み取り専用、raw のルートに残ったファイルを確かめる。

Windows では、書き換えが失敗し、raw が変わらないことを期待する（合格）。POSIX では、名前の変更で読み取り専用の
ファイルも置き換わる見込みなので、変わったかどうかを記録するだけにする（verify が見つける側）。

`claude -p` を 1 回実行する（Haiku）。

    python -X utf8 tests/wiki/check_session_readonly.py
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
OUT = ROOT / "docs/research/wiki-session-readonly-2026-11-14.json"
sys.path.insert(0, str(SCRIPTS))

import wiki_session  # noqa: E402

ORIGINAL = "---\ntitle: \"原本\"\n---\n\n## T1 ユーザー（2026-11-14 10:00:00）\n\n```text\noriginal の本文\n```\n"


def alias(link: Path, target: Path) -> None:
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)
    else:
        os.symlink(target, link, target_is_directory=True)


def main() -> int:
    claude = shutil.which("claude")
    if not claude:
        print("claude が見つからない")
        return 1
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        project = Path(temp) / "project"
        wiki = project / "wiki"
        raw = project / "raw"
        (wiki / "sources").mkdir(parents=True)
        raw.mkdir()
        (wiki / "SCHEMA.md").write_bytes("# スキーマ\n".encode("utf-8"))
        target = raw / "会話.md"
        target.write_bytes(ORIGINAL.encode("utf-8"))
        wiki_session.make_read_only(target)
        before = hashlib.sha256(target.read_bytes()).hexdigest()
        alias(wiki / "indexes", raw)
        alias(wiki / "up", project)
        paths = [wiki / "indexes" / "会話.md", wiki / "up" / "raw" / "会話.md"]
        prompt = ("次のファイルそれぞれについて、Read で読み、Write で中身を「changed by Write」の 1 行に書き換え、"
                  "続けて Edit で「original」を「changed by Edit」に置き換えてみる。失敗したら、エラーの文をそのまま"
                  "報告して次に進む。ほかのツールは使わない。\n" + "\n".join(p.as_posix() for p in paths))
        done = subprocess.run([claude, "-p", prompt, "--model", "claude-haiku-5-5", "--allowedTools", "Read,Write,Edit",
                               "--output-format", "stream-json", "--verbose"], cwd=project, capture_output=True,
                              timeout=900, env={**os.environ, "PYTHONUTF8": "1"})
        tools, errors = [], []
        for line in done.stdout.decode("utf-8", "replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            for block in (event.get("message") or {}).get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    tools.append(block.get("name"))
                if block.get("type") == "tool_result" and block.get("is_error"):
                    content = block.get("content")
                    errors.append(str(content)[:200])
        after = hashlib.sha256(target.read_bytes()).hexdigest()
        report = {
            "purpose": "読み取り専用の raw を、wiki の中の別名を経由した Claude Code の Write と Edit が書き換えられないか",
            "platform": platform.platform(),
            "claude_version": subprocess.run([claude, "--version"], capture_output=True, text=True,
                                             encoding="utf-8").stdout.strip(),
            "tools": tools, "tool_errors": errors,
            "raw_unchanged": after == before, "raw_read_only": wiki_session.is_read_only(target),
            "raw_root_files": sorted(p.name for p in raw.iterdir()),
            "returncode": done.returncode,
        }
        for p in raw.iterdir():
            os.chmod(p, 0o644)
    ok = report["raw_unchanged"] and report["raw_read_only"] and report["raw_root_files"] == ["会話.md"] and (
        tools.count("Write") >= 1 and tools.count("Edit") >= 1)
    if os.name != "nt":
        ok = True  # POSIX は記録するだけ（verify が見つける側）
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("合格" if ok else "不合格", json.dumps({k: report[k] for k in ("tools", "raw_unchanged", "raw_read_only",
                                                                     "raw_root_files")}, ensure_ascii=False))
    print(f"→ {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
