"""目で確かめるための材料を作る。ページの画像を帯に切り、帯ごとに正解の行（番号と文字）の一覧を付ける。

使い方: python -X utf8 scripts/eyecheck_packets.py
corpus/public/eyecheck/<tag>-p<ページ>/band-<k>.png と band-<k>.txt を書く。行は、箱の中心がある帯に入れ、
帯の画像は、その帯の行の箱をすべて含むように広げる。正解から除いた行（garbled、empty）は載せない。
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

BENCH = Path(__file__).resolve().parent.parent
PUBLIC = BENCH / "corpus" / "public"
BAND = 420


def main() -> None:
    total = 0
    for path in sorted(PUBLIC.glob("*.truth.json")):
        truth = json.loads(path.read_bytes().decode("utf-8"))
        for page in truth["pages"]:
            key = f"{truth['name']}-p{page['page']:04d}"
            image = Image.open(PUBLIC / "eyecheck" / f"{key}.png")
            folder = PUBLIC / "eyecheck" / key
            folder.mkdir(exist_ok=True)
            bands: dict[int, list[dict]] = {}
            for line in page["lines"]:
                if line["excluded"]:
                    continue
                centre = (line["box"][1] + line["box"][3]) / 2
                bands.setdefault(int(centre // BAND), []).append(line)
            for k, lines in sorted(bands.items()):
                top = max(0, min(min(x["box"][1] for x in lines), k * BAND) - 8)
                bottom = min(image.height, max(max(x["box"][3] for x in lines), (k + 1) * BAND) + 8)
                image.crop((0, int(top), image.width, int(bottom))).save(folder / f"band-{k}.png")
                text = "\n".join(f"{x['id']}\t{'[縦] ' if x['vertical'] else ''}{x['text']}" for x in lines)
                (folder / f"band-{k}.txt").write_bytes((text + "\n").encode("utf-8"))
                total += len(lines)
            print(key, len(bands), "帯", sum(len(v) for v in bands.values()), "行")
    print("合計", total, "行")


if __name__ == "__main__":
    main()
