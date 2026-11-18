"""公開カタログから隔離設定へ導入し、タグと実際の動作を照合する。モデルは呼ばない。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "info-hive-wiki"
sys.path.insert(0, str(ROOT / "tests/wiki"))
import bench_prompt_hook as bench
import check_codex_plugin

VERSION = "0.33.0"
MARKETPLACE = "to884/info-hive-marketplace"


def git(*args):
    return subprocess.check_output(["git", "-C", str(PLUGIN), *args])


def run(argv, env, cwd, timeout=180):
    result = subprocess.run(argv, env=env, cwd=cwd, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace") + result.stdout.decode("utf-8", "replace"))
    return result.stdout


def compare(installed):
    paths = git("diff", "--name-only", "--diff-filter=ACMRT", "v0.32.0", f"v{VERSION}").decode("utf-8").splitlines()
    hashes = {}
    for relative in paths:
        actual = (installed / relative).read_bytes()
        assert actual == git("show", f"v{VERSION}:{relative}"), relative
        hashes[relative] = hashlib.sha256(actual).hexdigest()
    return hashes


def claude(base):
    config, project = base / "claude-home", base / "project"
    config.mkdir()
    bench.synthetic_wiki(project / "wiki", 5)
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config), CLAUDE_CODE_DISABLE_AUTO_MEMORY="1",
               DISABLE_AUTOUPDATER="1", INFO_HIVE_PROMPT_CONTEXT="1", INFO_HIVE_PROMPT_CONTEXT_USER_WIKI="0",
               CLAUDE_PLUGIN_DATA=str(base / "hook-data"))
    env.pop("RUST_LOG", None)
    cli = shutil.which("claude")
    assert cli
    run([cli, "plugin", "marketplace", "add", MARKETPLACE, "--json"], env, project)
    run([cli, "plugin", "install", "wiki@info-hive", "--scope", "user", "--json"], env, project)
    registry = json.loads((config / "plugins/installed_plugins.json").read_text(encoding="utf-8"))
    entry, = registry["plugins"]["wiki@info-hive"]
    installed = Path(entry["installPath"])
    assert json.loads((installed / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"] == VERSION
    hashes = compare(installed)
    hooks = json.loads((installed / "hooks/hooks.json").read_text(encoding="utf-8"))
    command = hooks["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"].replace("${CLAUDE_PLUGIN_ROOT}", installed.as_posix())
    payload = json.dumps({"cwd": str(project), "prompt": "[[page-0000]] [[page-0001]] の手順を確認して",
                          "session_id": "marketplace-smoke", "hook_event_name": "UserPromptSubmit"}).encode("utf-8")
    argv = [bench.bash_path(), "-c", command]
    first = subprocess.run(argv, input=payload, env=env, cwd=project, capture_output=True, timeout=10)
    assert first.returncode == 0 and not first.stderr and bench.valid_candidate_output(first.stdout), first
    context = json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "model=sonnet" in context and "effort=low" in context
    second = subprocess.run(argv, input=payload, env=env, cwd=project, capture_output=True, timeout=10)
    assert second.returncode == 0 and not second.stdout and not second.stderr, second
    disabled = subprocess.run(argv, input=payload, env=dict(env, INFO_HIVE_PROMPT_CONTEXT="0"), cwd=project,
                              capture_output=True, timeout=10)
    assert disabled.returncode == 0 and not disabled.stdout and not disabled.stderr, disabled
    return {"version": VERSION, "marketplace": MARKETPLACE, "installed": True,
            "release_files_sha256": hashes, "candidate_pages": 2, "repeat_suppressed": True,
            "disabled_silent": True, "reader": {"model": "sonnet", "effort": "low"}}


def codex(base):
    report = check_codex_plugin.check(shutil.which("codex"), base, MARKETPLACE, VERSION)
    manifests = [p for p in (base / "codex-home").rglob("plugin.json")
                 if p.parent.name == ".codex-plugin" and json.loads(p.read_text(encoding="utf-8")).get("name") == "wiki"]
    installed, = manifests
    report["release_files_sha256"] = compare(installed.parent.parent)
    return report


def skill(base):
    project = base / "project"
    project.mkdir()
    cli = shutil.which("npx")
    assert cli
    run([cli, "--yes", "skills", "add", "to884/info-hive-wiki", "--skill", "info-hive", "--agent", "codex", "--yes"],
        dict(os.environ, CI="1", NO_COLOR="1"), project, timeout=240)
    installed = project / ".agents/skills/info-hive"
    hashes = {}
    for full in git("ls-tree", "-r", "--name-only", f"v{VERSION}", "skills/info-hive").decode("utf-8").splitlines():
        relative = Path(full).relative_to("skills/info-hive")
        actual = (installed / relative).read_bytes()
        assert actual == git("show", f"v{VERSION}:{full}"), full
        hashes[relative.as_posix()] = hashlib.sha256(actual).hexdigest()
    return {"source": "to884/info-hive-wiki", "tag": f"v{VERSION}", "installed": True, "files_sha256": hashes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("claude", "codex", "skill"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    temporary = tempfile.TemporaryDirectory(prefix="info-hive-0330-" + args.mode + "-")
    base = Path(temporary.name)
    try:
        report = globals()[args.mode](base)
    finally:
        assert base.resolve().parent == Path(tempfile.gettempdir()).resolve()
        assert base.name.startswith("info-hive-0330-")
        deadline = time.monotonic() + 30
        while True:
            try:
                temporary.cleanup()
                break
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.2)
    report["temporary_deleted"] = not base.exists()
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"mode": args.mode, "installed": report["installed"], "temporary_deleted": report["temporary_deleted"]}))


if __name__ == "__main__":
    main()
