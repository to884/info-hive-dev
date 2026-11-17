"""公開カタログから隔離導入し、タグの全変更ファイルと概要の保存・表示を確かめる。"""
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

REPO = Path(__file__).resolve().parents[3]
PLUGIN = REPO / "info-hive-wiki"
SMOKE = r'''
import hashlib,json,sys
from pathlib import Path
scripts,wiki=map(Path,sys.argv[1:])
sys.path.insert(0,str(scripts))
import wiki_overview as ov
import wiki_browse as browse
browse._load()
import wiki_browse_core as core
wiki.mkdir()
(wiki/'SCHEMA.md').write_bytes(b'# schema\n')
source=wiki/'concepts'/'sample.md'
source.parent.mkdir()
source.write_bytes('# 元のページ\n\n本文。\n'.encode('utf-8'))
begin=ov.begin(wiki)
Path(begin['request_path']).write_bytes(json.dumps({'format':2,'action':'create','page':'sample'}).encode('utf-8'))
ready=ov.prepare(wiki)
draft=Path(ready['draft_dir'])
(draft/'overview.md').write_bytes('### 保存した概要\n\n![図](#fig-flow)\n'.encode('utf-8'))
svg=b'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="120"><text x="20" y="40">overview</text></svg>\n'
(draft/'flow.svg').write_bytes(svg)
assert ov.check(wiki,ready['work_id'])=={'status':'ok'}
written=ov.write(wiki,ready['work_id'])
before={p.relative_to(wiki).as_posix():p.read_bytes() for p in wiki.rglob('*') if p.is_file()}
built=core.Core(core.take_snapshot(wiki))
html=built.body_html('concepts/sample')
assert '</h1>\n<details class="wiki-overview' in html
assert 'data-overview-state="fresh" open' in html
saved=ov.embedded_figures((wiki/written['sidecar']).read_bytes())['flow']
assert saved.rstrip(b'\n')==svg.rstrip(b'\n')
assert list(built.overview_assets.values())==[saved]
assert len(built.drawn)==1
after={p.relative_to(wiki).as_posix():p.read_bytes() for p in wiki.rglob('*') if p.is_file()}
assert before==after
assert source.read_bytes()=='# 元のページ\n\n本文。\n'.encode('utf-8')
source.write_bytes('# 更新したページ\n\n本文。\n'.encode('utf-8'))
built=core.Core(core.take_snapshot(wiki))
html=built.body_html('concepts/sample')
assert 'data-overview-state="stale"' in html
assert 'data-overview-state="stale" open' not in html
assert ov.inspect_wiki(wiki)['overviews'][0]['state']=='stale'
print(json.dumps({'written':written['status'],'fresh':True,'stale_closed':True,'svg_sha256':hashlib.sha256(saved).hexdigest(),'browse_unchanged':True}))
'''


def run(args, *, env=None, cwd=None):
    result = subprocess.run(args, env=env, cwd=cwd or REPO, capture_output=True, encoding="utf-8", timeout=600)
    if result.returncode:
        raise RuntimeError(f"{args[:3]}: {result.stderr[-2000:]}")
    return result.stdout


def verify(host, version, tag, changed, out):
    cli = shutil.which("claude" if host == "claude" else "codex")
    assert cli
    base = Path(tempfile.mkdtemp(prefix=f"overview-marketplace-{host}-"))
    report = {}
    try:
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
               "INFO_HIVE_DATA_DIR": str(base / "runtime")}
        home = base / "home"
        home.mkdir()
        env["CLAUDE_CONFIG_DIR" if host == "claude" else "CODEX_HOME"] = str(home)
        report["client"] = run([cli, "--version"], env=env).strip()
        if host == "claude":
            run([cli, "plugin", "marketplace", "add", "to884/info-hive-marketplace"], env=env)
            run([cli, "plugin", "install", "wiki@info-hive"], env=env)
            installed = json.loads(run([cli, "plugin", "list", "--json"], env=env))
            entry = next(p for p in installed if p.get("id") == "wiki@info-hive")
            assert entry["enabled"] and entry["version"] == version, entry
            path = Path(entry["installPath"])
        else:
            run([cli, "--no-daemon", "plugin", "marketplace", "add", "to884/info-hive-marketplace", "--json"], env=env)
            entry = json.loads(run([cli, "--no-daemon", "plugin", "add", "wiki@info-hive", "--json"], env=env))
            assert entry["version"] == version, entry
            path = Path(entry["installedPath"])
        for manifest in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            assert json.loads((path / manifest).read_text(encoding="utf-8"))["version"] == version
        hashes = {}
        for rel in changed:
            original = subprocess.check_output(["git", "show", f"{tag}:{rel}"], cwd=PLUGIN)
            actual = (path / rel).read_bytes()
            assert actual == original, rel
            hashes[rel] = hashlib.sha256(actual).hexdigest()
        smoke = run(["uv", "run", "--python", "3.12", "--with", "pyyaml==6.0.3", "python", "-X", "utf8", "-B",
                     "-c", SMOKE, str(path / "skills/info-hive/scripts"), str(base / "wiki")], env=env)
        report.update(version=version, marketplace="to884/info-hive-marketplace", installed=True,
                      release_files_sha256=hashes, overview_smoke=json.loads(smoke))
    finally:
        # この実行で作った一時領域だけを消す。Git の読み取り専用ファイルにも対応する。
        assert base.resolve().parent == Path(tempfile.gettempdir()).resolve()
        assert base.name.startswith("overview-marketplace-")
        def writable(fn, path, exc):
            os.chmod(path, 0o700)
            fn(path)
        shutil.rmtree(base, onerror=writable)
    report["temporary_directory_removed"] = not base.exists()
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"host":host,"version":version,"files":len(changed),"ok":True}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="0.32.0")
    parser.add_argument("--previous", default="v0.31.1")
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="both")
    args = parser.parse_args()
    tag = "v" + args.version
    changed = run(["git", "diff", "--name-only", "--diff-filter=ACMR", args.previous, tag], cwd=PLUGIN).splitlines()
    assert changed
    for host in ("claude", "codex") if args.host == "both" else (args.host,):
        verify(host, args.version, tag, changed, Path(__file__).with_name(f"{host}-marketplace.json"))


if __name__ == "__main__":
    main()
