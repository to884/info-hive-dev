"""実例の幾何を再現した合成画像で、前の画像転記比較を追試する。"""

import argparse
from collections import Counter
from functools import lru_cache
import importlib.util
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "2026-11-19-adr-0025-condition5-transcription-pilot/pilot.py"
spec = importlib.util.spec_from_file_location("first_pilot", PREVIOUS)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
PRIVATE = base.BENCH / "corpus/transcription-replication-2026-11-19"
DIAGNOSIS = base.ROOT / "docs/research/adr-0025-condition5-reference-audit-rootcause-v9-2026-11-19.md"

GROUPS = (
    ("）", "meiryo.ttc", ("返却を確認する", "記号（箱の番号", "期限（別紙（控え",
                          "用具（小型", "雨具（貸出（予備", "異常なしの記録")),
    ("】", "BIZ-UDMinchoM.ttc", ("【注記【交換済", "夕方の記録", "【係の注意",
                                 "【摘要欄", "差分を照合する", "【内訳【夜間")),
    ("。", "YuGothM.ttc", ("水路を越えた", "先に図を読んだ", "報告書を閉じた",
                          "袋から出した", "机にそろえた", "窓を開けた")),
    ("。", "yumin.ttf", ()),
)
BASE_PROMPT = base.PROMPT.replace(
    "所属軸はxです。固定150 DPIの画像で、字のインクの左右の長さの半分以上が枠内にあり、上下のインク中心が枠内にある字を含めます。",
    "各画像に所属軸xまたはyを示します。固定150 DPIで、軸xは字のインクの左右の長さの半分以上が枠内で上下のインク中心も枠内、"
    "軸yは上下の長さの半分以上が枠内で左右のインク中心も枠内にある字を含めます。枠線の内側の縁が箱の端です。",
)
SCALE = 3
WIDTH = 362
HEIGHT = 318
original_metrics = base.metrics
original_summarize = base.summarize


def px(box):
    return tuple(v * SCALE for v in box)


@lru_cache
def font(fontname, size):
    return ImageFont.truetype(base.FONTS / fontname, size * SCALE)


@lru_cache
def glyph(char, fontname, size, w=None, h=None):
    face = font(fontname, size)
    l, t, r, b = face.getbbox(char)
    mask = Image.new("L", (r - l, b - t))
    ImageDraw.Draw(mask).text((-l, -t), char, font=face, fill=255)
    mask = mask.crop(mask.getbbox())
    w = w or (mask.width + 2) // SCALE
    h = h or (mask.height + 2) // SCALE
    mask = mask.resize((w * SCALE, h * SCALE), Image.Resampling.BICUBIC)
    low = mask.resize((w, h), Image.Resampling.BOX)
    if low.getbbox() != (0, 0, w, h):
        raise ValueError(f"字の150 DPIインク寸法が設計と異なる: {char}")
    return mask


def ink_mask_components(mask):
    """8連結で、低解像度でも近接字がつながらないことを確かめる。"""
    low = mask.resize((mask.width // SCALE, mask.height // SCALE), Image.Resampling.BOX)
    pending = {(x, y) for x in range(low.width) for y in range(low.height) if low.getpixel((x, y)) >= 24}
    result = []
    while pending:
        todo = [pending.pop()]
        component = set(todo)
        while todo:
            x, y = todo.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbor = x + dx, y + dy
                    if neighbor in pending:
                        pending.remove(neighbor)
                        component.add(neighbor)
                        todo.append(neighbor)
        result.append(component)
    return result


class Row:
    def __init__(self, image, region, axis, fg):
        self.image = image
        self.region = region
        self.axis = axis
        self.fg = fg
        self.included = []
        self.geometry = []

    def put(self, char, mask, x, y, owned, feature=None):
        r, b = x + mask.width // SCALE, y + mask.height // SCALE
        left, top, right, bottom = self.region
        if self.axis == "x":
            overlap = max(0, min(r, right) - max(x, left))
            span = r - x
            centered = 2 * top <= y + b < 2 * bottom
        else:
            overlap = max(0, min(b, bottom) - max(y, top))
            span = b - y
            centered = 2 * left <= x + r < 2 * right
        if (2 * overlap >= span and centered) != owned:
            raise ValueError(f"想定と150 DPIの所属が異なる: {self.axis}, {overlap}/{span}, {centered}")
        self.image.paste(self.fg, px((x, y, r, b)), mask)
        if owned:
            self.included.append((x, y, char))
        if feature:
            self.geometry.append({"feature": feature, "overlap": overlap, "span": span,
                                  "cross_axis_center_inside": centered, "owned": owned})

    def text(self):
        order = (lambda g: (g[0], g[1])) if self.axis == "x" else (lambda g: (-g[0], g[1]))
        return "".join(g[2] for g in sorted(self.included, key=order))


def horizontal(image, sheet, i, y):
    mark, family, lines = GROUPS[sheet - 1]
    left, right = 64, (275, 288, 302)[i % 3]
    region = (left, y + 7, right, y + 34)
    fg = (("#252628", "#535052", "#6f6865") if sheet < 3
          else ("#313238", "#4d494d", "#5a5253"))[(i + sheet) % 3]
    row = Row(image, region, "x", fg)
    draw = ImageDraw.Draw(image)
    if i % 2 == 1:
        draw.line(px((left + 2, y + 31, right + 12, y + 31)), fill="#b0afb0", width=SCALE)
    if sheet == 2 and i % 3 != 2:
        draw.rectangle(px((left + 11, y + 16, left + 15, y + 20)), fill="#7690a6")
        draw.rectangle(px((left + 18, y + 16, left + 22, y + 20)), fill="#c3927e")
    size = (12, 11, 10)[(i + sheet) % 3]
    if sheet < 3:
        counts = (0, 1, 2, 1, 2, 0) if sheet == 1 else (2, 0, 1, 1, 0, 2)
        count = counts[i]
        close = glyph(mark, family, size, 5, (8, 10, 11)[i % 3])
        if len(ink_mask_components(close)) != 1:
            raise ValueError(f"閉じ記号の150 DPIインクが単一成分でない: {sheet}/{i}")
        gap = (1, 2, 1, 2, 1, 1)[i]
        end = right - (1, 3, 2)[i % 3]
        punctuation_left = end - (5 * count + max(0, count - 1) * gap)
        for n in range(count):
            row.put(mark, close, punctuation_left + n * (5 + gap), y + 15, True, "narrow_close")
        if sheet == 2 or i in (0, 3, 4):
            row.put(mark, close, right + (1, 2)[i % 2], y + 15, False, "outside_close")
        body_end = punctuation_left - (1, 2)[i % 2]
    else:
        overlap = (1, 2, 0, 1, 3, 2)[i]
        point_x = right - overlap
        point = glyph(mark, family, size, 3, 3)
        row.put(mark, point, point_x, y + 24, overlap >= 2, "terminal_stop")
        body_end = point_x - (1, 2)[i % 2]
    for char in reversed(lines[i]):
        body = glyph(char, family, size)
        body_end -= body.width // SCALE
        row.put(char, body, body_end, y + 24 - body.height // SCALE, True)
        body_end -= 1
    if sheet == 3:
        row.put("校", glyph("校", family, 9), right + 7, y + 14, False)
    return row


def vertical(image, i, y):
    family = GROUPS[3][1]
    left, right = (203, 246) if i < 3 else (193, (234, 226, 235)[i - 3])
    region = (left, y + 8, right, y + 31)
    row = Row(image, region, "y", ("#363033", "#62595a", "#504c56")[i % 3])
    if i < 3:
        head, tail = (("音", "が"), ("閉", "じ"), ("飛", "ぶ"))[i]
        row.put(head, glyph(head, family, 11, 10, 10), 224, y + 11, True)
        row.put("考", glyph("考", family, 10, 10, 11), 248, y + 17, False)
        tail_mask = glyph(tail, family, 14, 12, 15)
        overlap = (7, 8, 7)[i]
        components = ink_mask_components(tail_mask)
        if len(components) < 2 or not any(all(yy < overlap for xx, yy in comp)
                                          for comp in components):
            raise ValueError(f"末尾字が一部だけ枠内の対照にならない: {tail}")
        row.put(tail, tail_mask, 223, region[3] - overlap, overlap >= 8, "split_tail")
    else:
        # 字の高さを一定にして、所属と右から左への読み順を独立に検査する。
        columns = (("路標", "地図"), ("参照", "索引"), ("受付", "案内"))[i - 3]
        for column, text in enumerate(columns):
            x = (224 if i == 4 else 220) - 15 * column
            for j, char in enumerate(text):
                yy = y + 9 + 13 * j + (3 if i == 5 and column == 1 else 0)
                owned = not (i == 4 and column == 0)
                row.put(char, glyph(char, family, 11, 10, 10), x, yy, owned, "vertical_neighbor")
        row.put("外", glyph("外", family, 10, 9, 9), 245, y + 12, False)
    return row


def sheet_images(sheet, ids):
    background = ("#f6f3ec", "#f0eeeb", "#f8f6f1", "#edeaf0")[sheet - 1]
    plain = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), background)
    built, rows = [], []
    mark = GROUPS[sheet - 1][0]
    axis = "x" if sheet < 4 else "y"
    for index, row_id in enumerate(ids):
        y = 28 + 46 * index
        row = horizontal(plain, sheet, index, y) if axis == "x" else vertical(plain, index, y)
        built.append((y, row))
        gold = row.text()
        rows.append({"id": row_id, "sheet": sheet, "mark": mark, "gold": gold,
                     "marks": gold.count(mark), "geometry": row.geometry})
    raw_150 = plain.resize((WIDTH, HEIGHT), Image.Resampling.BOX)
    image_names = []
    for dpi, source in ((150, raw_150), (450, plain)):
        s = 1 if dpi == 150 else SCALE
        for framed in (False, True):
            image = source.copy()
            draw = ImageDraw.Draw(image, "RGBA")
            label = ImageFont.truetype(base.FONTS / "meiryo.ttc", 10 * s)
            title = f"{dpi} DPI | {'枠あり' if framed else '枠なし'} | 所属軸 {axis}"
            draw.text((13 * s, 6 * s), title, fill="#413e44", font=label)
            for (y, row), info in zip(built, rows):
                draw.text((12 * s, (y + 16) * s), info["id"], fill="#3c3943", font=label)
                if framed:
                    l, t, r, b = row.region
                    outside = ((l - 1) * s, (t - 1) * s, (r + 1) * s - 1, (b + 1) * s - 1)
                    draw.rectangle(outside, outline=(179, 45, 104, 130), width=s)
            if dpi == 150:
                image = image.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.Resampling.NEAREST)
            name = f"sheet-{sheet:02d}-{dpi}-{'frame' if framed else 'plain'}.png"
            image.save(PRIVATE / name)
            image_names.append(name)
    return image_names, rows


def prompt(arm, ids):
    return BASE_PROMPT + (base.EXTRA if arm == "new" else "") + base.FORMAT + "、".join(ids) + "\n"


def source_hashes():
    return {path.name: base.sha(path) for path in (Path(__file__), PREVIOUS, HERE / "protocol.md", DIAGNOSIS)}


def prepare():
    PRIVATE.mkdir(parents=True)
    numbers = random.Random(251119).sample(range(100, 999), 24)
    image_map, all_rows = {}, []
    for i in range(1, 5):
        ids = [f"R{n}" for n in numbers[(i - 1) * 6:i * 6]]
        images, rows = sheet_images(i, ids)
        image_map[str(i)] = images
        all_rows.extend(rows)
    base.write_json(PRIVATE / "gold.json", all_rows)
    inputs = {}
    for arm in ("old", "new"):
        name = f"{arm}-prompt.txt"
        (PRIVATE / name).write_bytes(prompt(arm, [r["id"] for r in all_rows]).encode("utf-8"))
        inputs[name] = base.sha(PRIVATE / name)
    for names in image_map.values():
        inputs.update({name: base.sha(PRIVATE / name) for name in names})
    inputs["gold.json"] = base.sha(PRIVATE / "gold.json")
    base.write_json(HERE / "lock.json", {
        "fixed_at": base.utc_now(), "rows": 24, "source_sha256": source_hashes(),
        "official_input_sha256": base.frozen_hashes(), "private_input_sha256": inputs,
        "image_sha256": {name: inputs[name] for names in image_map.values() for name in names},
        "image_order_by_sheet": image_map, "initial_models": base.MODELS,
        "third_model_by_sheet": {str(i): base.MODELS[(i - 1) % 2] for i in range(1, 5)},
    })
    print("固定", base.sha(HERE / "lock.json"), "24行、16画像", flush=True)


def check_lock(expected):
    path = HERE / "lock.json"
    if base.sha(path) != expected:
        raise ValueError("指定の固定記録SHAと異なる")
    lock = base.load(path)
    if source_hashes() != lock["source_sha256"] or base.frozen_hashes() != lock["official_input_sha256"]:
        raise ValueError("計画、実行コード、診断または正式評価入力が変化")
    for name, digest in lock["private_input_sha256"].items():
        if base.sha(PRIVATE / name) != digest:
            raise ValueError(f"固定した入力が変化: {name}")
    rows = base.load(PRIVATE / "gold.json")
    ids = [r["id"] for r in rows]
    if len(set(ids)) != lock["rows"] or any(
        (PRIVATE / f"{arm}-prompt.txt").read_bytes() != prompt(arm, ids).encode("utf-8")
        for arm in ("old", "new")
    ):
        raise ValueError("対象IDか提示指示が異なる")
    return lock, rows


def metrics(rows, values):
    result = original_metrics(rows, values)
    missing = [(Counter(base.normalize(r["gold"])) - Counter(values[r["id"]])).total()
               for r in rows if values[r["id"]] is not None]
    result.update(missing_chars=sum(missing), missing_char_rows=sum(n > 0 for n in missing))
    return result


def summarize(rows, prelim, final, third_ids):
    result = original_summarize(rows, prelim, final, third_ids)
    result["by_failure_type"] = {
        group: base.paired([r for r in rows if r["sheet"] in sheets], final["old"], final["new"])
        for group, sheets in (("repeated_close", (1, 2)), ("boundary_stop", (3,)),
                              ("vertical_split", (4,)))
    }
    result["row_outcomes"] = [
        {"id": row["id"], "sheet": row["sheet"], "target_count": row["marks"],
         "geometry": row["geometry"],
         **{arm: metrics([row], final[arm]) for arm in ("old", "new")}}
        for row in rows
    ]
    return result


def run(exe, expected):
    # 読み手起動・受領形式・二読と第三読の進行は、固定済みの前回コードを使う。
    base.HERE = HERE
    base.PRIVATE = PRIVATE
    base.prompt_for = prompt
    base.check_lock = check_lock
    base.metrics = metrics
    base.summarize = summarize
    base.run(exe, expected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("prepare")
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--codex", required=True, type=Path)
    run_parser.add_argument("--lock-sha256", required=True)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        run(args.codex.resolve(), args.lock_sha256)
