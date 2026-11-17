"""公開リポジトリのスキルを一時的なプロジェクトに導入し、タグの全ファイルと比べる。"""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

root = Path(__file__).resolve().parents[3]
version = "0.31.0"
with tempfile.TemporaryDirectory(prefix="wiki-0310-skills-") as tmp:
    base = Path(tmp).resolve()
    result = subprocess.run([shutil.which("npx"), "--yes", "skills", "add", "to884/info-hive-wiki",
                             "--skill", "info-hive", "--agent", "codex", "--copy", "--yes", "--json"],
                            cwd=base, capture_output=True, encoding="utf-8", timeout=180)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    dest = base / ".agents/skills/info-hive"
    assert (dest / "SKILL.md").is_file(), result.stdout
    archive = subprocess.check_output(["git", "archive", "--format=zip", "v" + version], cwd=root / "info-hive-wiki")
    checked = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as tree:
        prefix = "skills/info-hive/"
        for name in tree.namelist():
            if not name.startswith(prefix) or name.endswith("/"):
                continue
            relative = name[len(prefix):]
            expected = tree.read(name)
            actual = (dest / relative).read_bytes()
            assert actual == expected, relative
            checked[relative] = hashlib.sha256(actual).hexdigest()
    report = {"version": version, "installed": True, "files_sha256": checked}
    (root / "docs/agent-runs/2026-11-17-adr-0029-stage1-review/skills-directory.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"skills add: {version}、全 {len(checked)} ファイル一致: PASS")
