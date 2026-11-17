"""Codex CLI でのプラグイン導入と MCP の実機試験。モデルは呼ばない。

    python -X utf8 -B tests/wiki/check_codex_plugin.py [--out <結果.json>]
    python -X utf8 -B tests/wiki/check_codex_plugin.py --marketplace to884/info-hive-marketplace --expected-version 0.29.0

一時的な CODEX_HOME、カタログ、wiki、MCP のデータディレクトリを使う。
通常の Codex 設定を変えず、既存の wiki のサーバーを止めない。
Codex CLI 0.166.0 以降と uv、MCP の依存パッケージを取得できる環境が必要である。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from mcp_stdio import StdioClient

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "info-hive-wiki"
EXPECTED_TOOLS = {"query", "get_page", "list_index", "lint", "stats", "graph", "index_chunks"}


def check(cli: str, base: Path, marketplace: str | None = None, expected_version: str | None = None) -> dict:
    home = base / "codex-home"
    home.mkdir()
    catalog_root = base / "日本語 カタログ"
    catalog_path = catalog_root / ".agents/plugins/marketplace.json"
    catalog_path.parent.mkdir(parents=True)
    source = catalog_root / "日本語 プラグイン"
    shutil.copytree(PLUGIN, source, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
    catalog_path.write_text(json.dumps({
        "name": "info-hive-smoke",
        "interface": {"displayName": "info-hive smoke"},
        "plugins": [{"name": "wiki", "source": {"source": "local", "path": "./日本語 プラグイン"},
                     "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}}],
    }, ensure_ascii=False), encoding="utf-8")
    runtime = base / "wiki-runtime"
    env = {**os.environ, "CODEX_HOME": str(home), "PYTHONUTF8": "1", "RUST_LOG": "info",
           "INFO_HIVE_DATA_DIR": str(runtime), "INFO_HIVE_MCP_IDLE_SECONDS": "3"}
    project = base / "利用者の プロジェクト"
    wiki = project / "wiki"
    (wiki / "concepts").mkdir(parents=True)
    (wiki / "SCHEMA.md").write_text("# 試験用の wiki\n", encoding="utf-8")
    (wiki / "index.md").write_text("# 索引\n\n- [[検索の試験]]: 日本語の検索の試験\n", encoding="utf-8")
    (wiki / "log.md").write_text("# ログ\n", encoding="utf-8")
    (wiki / "concepts/検索の試験.md").write_text(
        '---\ntitle: "検索の試験"\ntype: "concept"\ntags: ["試験"]\nsources: []\nupdated: 2026-11-17\n'
        '---\n\n# 検索の試験\n\nCodex から日本語の wiki を検索できる。\n', encoding="utf-8")
    before = {p.relative_to(wiki): p.read_bytes() for p in wiki.rglob("*") if p.is_file()}

    def command(*args: str) -> dict:
        result = subprocess.run([cli, "--no-daemon", *args], cwd=project, env=env,
                                capture_output=True, encoding="utf-8", timeout=60)
        if result.returncode:
            raise RuntimeError(f"Codex CLI が失敗: {result.stderr}")
        return json.loads(result.stdout)

    registered = command("plugin", "marketplace", "add", marketplace or str(catalog_root), "--json")
    marketplace_name = registered["marketplaceName"]
    plugin_id = "wiki@" + marketplace_name
    if marketplace:
        catalog_path = Path(registered["installedRoot"]) / ".agents/plugins/marketplace.json"
    installed = command("plugin", "add", plugin_id, "--json")
    installed_path = Path(installed["installedPath"])
    manifest = json.loads((installed_path / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == installed["version"]
    if expected_version:
        assert installed["version"] == expected_version, installed
    client = StdioClient([cli, "app-server"], env=env)
    report = {"version": installed["version"], "installed": True,
              "marketplace": marketplace or "local-fixture", "plugin_id": plugin_id}
    if marketplace:
        # 公開先から取得した、今回変えた配布物をリリースのタグと照らす。
        import hashlib
        checked = {}
        for relative in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "skills/info-hive/SKILL.md",
                         "skills/info-hive/scripts/wiki_codex.py", "skills/info-hive/scripts/wiki_codex_session.py",
                         "skills/info-hive/scripts/wiki_session.py", "skills/info-hive/references/codex.md"):
            original = subprocess.check_output(
                ["git", "show", f"v{installed['version']}:{relative}"], cwd=PLUGIN)
            actual = (installed_path / relative).read_bytes()
            assert actual == original, relative
            checked[relative] = hashlib.sha256(actual).hexdigest()
        report["release_files_sha256"] = checked
    try:
        init = client.request("initialize", {"clientInfo": {"name": "info-hive-smoke", "version": "0"},
                                            "capabilities": {"experimentalApi": True}}, timeout=30)
        client.send({"method": "initialized"})
        report["client"] = init["userAgent"]
        detail = client.request("plugin/read", {"marketplacePath": str(catalog_path), "pluginName": "wiki"}, timeout=30)
        assert detail["plugin"]["mcpServers"] == ["wiki"], detail
        inventory = client.request("skills/list", {"cwds": [str(project)], "forceReload": True}, timeout=30)
        skill_names = [s["name"] for entry in inventory["data"] for s in entry["skills"]
                       if s.get("pluginId") == plugin_id]
        assert "wiki:info-hive" in skill_names, skill_names
        report["skills"] = skill_names
        status = client.request("mcpServerStatus/list", {"serverName": "wiki"}, timeout=600)
        server = next(s for s in status["data"] if s["name"] == "wiki")
        assert server["toolsError"] is None, server["toolsError"]
        assert EXPECTED_TOOLS <= server["tools"].keys(), server["tools"].keys()
        report["tools"] = sorted(server["tools"])
        # 実際に隔離先で起動したことを確認してからツールを呼ぶ。
        assert (runtime / "server.json").is_file(), "MCP に隔離用の環境変数が届いていない"
        thread = client.request("thread/start", {"cwd": str(project), "ephemeral": True}, timeout=30)
        thread_id = thread["thread"]["id"]
        for tool, arguments in [("stats", {"wiki": str(wiki)}),
                                ("query", {"wiki": str(wiki), "query": "日本語 検索", "top": 3})]:
            result = client.request("mcpServer/tool/call", {"server": "wiki", "threadId": thread_id,
                                                           "tool": tool, "arguments": arguments}, timeout=60)
            assert not result.get("isError"), result
            data = result.get("structuredContent")
            if data is None:
                data = json.loads(result["content"][0]["text"])
            if tool == "stats":
                assert data["pages"] == 1, data
            else:
                assert any(row["slug"] == "検索の試験" for row in data["results"]), data
            report[tool] = data
        after = {p.relative_to(wiki): p.read_bytes() for p in wiki.rglob("*") if p.is_file()}
        assert before == after, "読むツールが wiki を変更した"
        report["wiki_unchanged"] = True
    finally:
        client.close(timeout=5)
        # 接続を閉じたあと、隔離したサーバーの短いアイドル終了を待つ。
        deadline = time.monotonic() + 20
        while (runtime / "server.json").exists() and time.monotonic() < deadline:
            time.sleep(0.2)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--marketplace", help="ローカルの素材の代わりに導入する配布カタログ")
    parser.add_argument("--expected-version", help="導入した版がこの値と同じであることを確かめる")
    args = parser.parse_args()
    cli = shutil.which("codex")
    if not cli:
        parser.error("Codex CLI が PATH にない")
    temporary = tempfile.TemporaryDirectory(prefix="info-hive-codex-")
    folder = Path(temporary.name)
    try:
        report = check(cli, folder, args.marketplace, args.expected_version)
        # 後片付けだけが失敗しても、完了した検証の証拠を失わない。
        output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(output, encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k not in {"query", "stats"}}, ensure_ascii=False))
    finally:
        primary_error = sys.exc_info()[0] is not None
        assert folder.resolve().parent == Path(tempfile.gettempdir()).resolve()
        assert folder.name.startswith("info-hive-codex-")
        # Windows では子の終了後も Git の一時ファイルが短時間開いていることがある。
        deadline = time.monotonic() + 30
        while True:
            try:
                temporary.cleanup()
                break
            except PermissionError as exc:
                if time.monotonic() >= deadline:
                    if not primary_error:
                        raise
                    print(f"一時ディレクトリを削除できなかった: {folder}: {exc}", file=sys.stderr)
                    break  # 検証の元の例外を、後片付けの例外で上書きしない。
                time.sleep(0.2)


if __name__ == "__main__":
    main()
