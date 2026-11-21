"""元PDFの描画命令を抽出し、間接参照のフォント幅を解決する。"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
FONT_WIDTH = HERE.parent / "v11-visible-source-pilot/commands.py"
spec = importlib.util.spec_from_file_location("font_widths", FONT_WIDTH)
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)
source = support.old


def collect(request, destination):
    source.cid_width = support.cid_width
    source.raw.font_mapping = support.font_mapping
    with tempfile.TemporaryDirectory(prefix="adr0025-v14-source-") as directory:
        archive = Path(directory) / "commands.json"
        source.run(request, archive)
        proof = json.loads(archive.read_text(encoding="utf-8"))
    for file in (Path(__file__), FONT_WIDTH):
        proof["methods"][file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
    with destination.open("x", encoding="utf-8") as output:
        json.dump(proof, output, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--request", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    collect(args.request, args.out)
