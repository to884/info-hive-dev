# 試験用の wiki を QC_WIKI_BASE に作り、条件ごとの MCP のデータの置き場所を用意する
#
# 1. init_wiki.py で wiki を初期化する（SCHEMA.md とテンプレート、CLI の検索の環境）
# 2. fixture/wiki のページ、index.md、log.md を写す
# 3. グラフをコンパイルし、CLI の検索のキャッシュを作る
# 4. data/ready にモデルを写し、data/broken に空のモデルのファイルと verified.json を置き、data/preparing は空にする
# 使い方: python build_fixture.py [--force]
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import FIXTURE, data_dir, plugin_dir, wiki_base, wiki_digest, wiki_root  # noqa: E402

MODEL_FOLDER = "ruri-v3-130m-onnx-cbd305d"
ORIGINATED = """
  # --- この wiki に固有の述語。 ---
  originated:
    subject_types: [person]
    object_types: [concept]
    requires_evidence: true
    description: |
      その考えを最初に言い出した人。
"""


def run(cmd, **kw):
    print("$", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, env={**os.environ, "PYTHONUTF8": "1"}, **kw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="既にある試験用の wiki を消して作り直す")
    args = ap.parse_args()
    base, root, scripts = wiki_base(), wiki_root(), plugin_dir() / "skills" / "info-hive" / "scripts"
    if base.exists():
        if not args.force:
            sys.exit(f"既にある: {base}（作り直すなら --force）")
        shutil.rmtree(base)
    base.mkdir(parents=True)

    run([sys.executable, scripts / "init_wiki.py", base])
    for src in sorted(FIXTURE.rglob("*.md")):
        dst = root / src.relative_to(FIXTURE)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
    # 分野に固有の述語を足す（テンプレートの predicates は最後のキーなので、末尾に足せばその下に入る）
    ontology = root / "graph" / "ontology.yaml"
    ontology.write_bytes(ontology.read_bytes().rstrip(b"\r\n") + ORIGINATED.encode("utf-8"))
    run(["uv", "run", "--quiet", "--script", scripts / "wiki_graph_extract.py", root])
    run(["uv", "run", "--quiet", "--script", scripts / "wiki_search.py", "設定ファイル", "--wiki", root,
         "--top", "1", "--cache", "--json"], stdout=subprocess.DEVNULL)

    local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    model = local / "info-hive" / "models" / MODEL_FOLDER
    if not (model / "verified.json").is_file():
        sys.exit(f"写すモデルがない: {model}（一度 wiki の MCP を使ってモデルを取得してから実行する）")
    shutil.copytree(model, data_dir("ready") / "models" / MODEL_FOLDER, ignore=shutil.ignore_patterns(".cache"))
    broken = data_dir("broken") / "models" / MODEL_FOLDER
    expected = json.loads((model / "verified.json").read_text(encoding="utf-8"))
    for name in expected:
        (broken / name).parent.mkdir(parents=True, exist_ok=True)
        (broken / name).write_bytes(b"")
    (broken / "verified.json").write_bytes((model / "verified.json").read_bytes())
    data_dir("preparing").mkdir(parents=True, exist_ok=True)

    print("wiki:", root)
    print("digest:", wiki_digest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
