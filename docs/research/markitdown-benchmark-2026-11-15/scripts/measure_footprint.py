"""抽出の依存を、Python 3.12 の空の環境に 1 つずつ入れ、site-packages の大きさとパッケージの一覧を測る。

使い方: python measure_footprint.py <作業用のディレクトリ>   footprint.json を書く
uv が要る。作業用のディレクトリには、仮想環境を作る（終わったら消してよい）。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
SPECS = ["markitdown==0.1.9", "markitdown[docx,pdf,pptx,xls,xlsx]==0.1.9", "pdfminer.six==20260107",
         "pypdfium2==5.15.2"]


def _size(folder: Path) -> int:
    return sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())


def main() -> None:
    work = Path(sys.argv[1]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    found = []
    for spec in SPECS:
        env = work / re.sub(r"[^a-z0-9]+", "_", spec.lower())
        subprocess.run(["uv", "venv", "-q", "-p", "3.12", str(env)], check=True)
        python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        subprocess.run(["uv", "pip", "install", "-q", "-p", str(python), spec], check=True)
        site = next(env.rglob("site-packages"))
        listed = subprocess.run(["uv", "pip", "list", "-p", str(python), "--format", "json"],
                                check=True, capture_output=True).stdout.decode("utf-8")
        packages = {p["name"]: p["version"] for p in json.loads(listed)}
        found.append({"spec": spec, "site_packages_mb": round(_size(site) / 2**20, 1),
                      "packages": len(packages), "list": packages})
        print(f"{spec}: {found[-1]['site_packages_mb']} MB, {len(packages)} packages", flush=True)
    (BENCH / "footprint.json").write_bytes(json.dumps(found, ensure_ascii=False, indent=2).encode("utf-8"))


if __name__ == "__main__":
    main()
