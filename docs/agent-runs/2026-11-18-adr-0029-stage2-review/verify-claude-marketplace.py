"""使い捨ての設定で公開カタログから導入し、変更された全ファイルをタグと比べる。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[3]
plugin = root / "info-hive-wiki"
version = "0.33.0"
cli = shutil.which("claude")
assert cli, "Claude CLI がない"
with tempfile.TemporaryDirectory(prefix="wiki-0330-marketplace-") as tmp:
    base = Path(tmp)
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(base / "config"), "PYTHONUTF8": "1"}
    def run(args, cwd=base):
        r = subprocess.run(args, cwd=cwd, env=env, capture_output=True, encoding="utf-8", timeout=180)
        if r.returncode:
            raise RuntimeError(r.stdout + r.stderr)
        return r.stdout
    run([cli, "plugin", "marketplace", "add", "to884/info-hive-marketplace"])
    run([cli, "plugin", "install", "wiki@info-hive"])
    listed = json.loads(run([cli, "plugin", "list", "--json"]))
    installed = json.loads((base / "config/plugins/installed_plugins.json").read_text(encoding="utf-8"))
    entries = installed["plugins"]["wiki@info-hive"]
    entry = entries[0]
    dest = Path(entry["installPath"])
    for host in (".claude-plugin", ".codex-plugin"):
        assert json.loads((dest / host / "plugin.json").read_text(encoding="utf-8"))["version"] == version
    names = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=ACMR", "v0.32.0", "v" + version], cwd=plugin, encoding="utf-8").splitlines()
    checked = {}
    for name in names:
        expected = subprocess.check_output(["git", "show", "v" + version + ":" + name], cwd=plugin)
        actual = (dest / name).read_bytes()
        assert actual == expected, name
        checked[name] = hashlib.sha256(actual).hexdigest()
    sys.path.insert(0, str(dest / "skills/info-hive/scripts"))
    import wiki_pages
    wiki = base / "wiki"
    (wiki / "concepts").mkdir(parents=True)
    (wiki / "SCHEMA.md").write_text("# 試験\n", encoding="utf-8")
    article = wiki / "concepts/a.md"
    article.write_text("# 記事\n", encoding="utf-8")
    os.link(article, wiki / "concepts/b.md")
    walked = wiki_pages.walk_pages(wiki)
    assert walked.files == []
    assert sorted(walked.links) == [("concepts/a.md", "hardlink"), ("concepts/b.md", "hardlink")]
    # 配布された raw の境界も呼ぶ。リンクの先の本文を読み取らずに拒むことを確かめる。
    result = wiki_pages.resolve_raw({"type": "source", "raw": str(article)}, wiki / "sources/source.md", wiki, raw_roots=[wiki])
    assert result[0].state == "link", result
    report = {"version": version, "installed": True, "changed_files_sha256": checked, "hardlink_rejected": True, "raw_hardlink_rejected": True, "listed": listed}
    (root / "docs/agent-runs/2026-11-18-adr-0029-stage2-review/claude-marketplace.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Claude Code: {version}、変更 {len(checked)} ファイル一致、ハードリンク拒否: PASS")
