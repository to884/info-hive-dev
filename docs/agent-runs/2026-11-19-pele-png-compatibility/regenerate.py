"""保存した原稿を製品の書き出し処理に渡し、SVG の一致を確認する。"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

directory = Path(__file__).resolve().parent
root = directory.parents[2]
sys.path.insert(0, str(root / "info-hive-wiki/skills/info-hive/scripts"))
from wiki_browse_pele import render_sources

cases = json.loads((directory / "inputs.json").read_text(encoding="utf-8"))["cases"]
images, warnings = render_sources([item["mermaid"] for item in cases])
assert not warnings, warnings
for item in cases:
    assert item["rendered"] == (item["mermaid"] in images), item["id"]
    if item["rendered"]:
        for theme, data in zip(("light", "dark"), images[item["mermaid"]][:2]):
            saved = (directory / f"{item['id']}-{theme}.svg").read_bytes()
            if item["id"] == "gantt":
                # 「現在」のマーカーの位置は再生成した時刻に応じて動く。
                trees = [ET.fromstring(value) for value in (saved, data)]
                for tree in trees:
                    for parent in tree.iter():
                        for child in list(parent):
                            if child.get("class") == "pele-today":
                                parent.remove(child)
                assert ET.tostring(trees[0]) == ET.tostring(trees[1]), item["id"]
            else:
                assert saved == data, item["id"]
print(f"{len(images)} 原稿の明暗 SVG を照合した（gantt の現在時刻マーカーを除く）")
