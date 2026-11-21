"""旧指示で難度を較正し、較正外の画像で旧・新を比較する。"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
from pathlib import Path
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
REPLICATION = HERE.parent / "2026-11-19-adr-0025-condition5-transcription-replication/replicate.py"
spec = importlib.util.spec_from_file_location("replication", REPLICATION)
rep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rep)
base = rep.base
ROOT = base.BENCH / "corpus/transcription-calibrated-2026-11-19"
W, H, SCALE, PAPER = 320, 338, 3, 240
CONTRAST = {1: (43, 44, 4), 2: (27, 30, 6), 3: (16, 17, 8),
            4: (9, 11, 10), 5: (5, 7, 12), 6: (4, 5, 14)}
SEEDS = {"calibration": 30911, "reserve": 41191, "comparison": 59003}
VOCABULARY = (
    ("棚の右端", "中央の板", "添付の順", "控えの段", "受付の欄", "当日の束",
     "倉庫の箱", "日付の列", "右側の図", "連絡の札", "裏面の袋", "照合の印",
     "西側の鍵", "予備の台", "封筒の番号", "貸出の帳"),
    ("交換の済", "月末の表", "該当の番号", "機材の型", "回収の順", "路線の札",
     "前便の欄", "確認の束", "表示の向き", "入場の印", "会場の鍵", "荷物の棚",
     "工具の袋", "予告の区", "登録の帳", "北口の列"),
    ("記録を写す", "次週の図", "伝票の色", "指定の棚", "改訂の頁", "水位の欄",
     "冬用の箱", "車両の鍵", "本日の版", "貸与の簿", "新規の列", "廃止の表",
     "届出の番号", "対象の札", "資料の順", "点検の印"),
)
VERTICAL = (
    ("議案", "繰越", "承認", "期日", "舞台", "転記", "微風", "遠景",
     "棟内", "簿冊", "到達", "級別", "所轄", "時刻", "軽便", "進捗",
     "弱電", "踏切", "草稿", "運賃", "得点", "瞬時", "運航", "難路"),
    ("探訪", "投票", "新旧", "館内", "事務", "照会", "標本", "予告",
     "転送", "画材", "返納", "受付", "読本", "配送", "局内", "給水",
     "表示", "倉庫", "夜間", "整理", "講習", "乗車", "台数", "抽出"),
    ("通信", "観測", "設営", "合図", "比較", "当番", "書類", "紙面",
     "復路", "列車", "再編", "修繕", "講義", "資料", "路線", "入室",
     "西口", "入口", "待機", "連絡", "予備", "概要", "電源", "貸出"),
)
BASE_PROMPT = rep.BASE_PROMPT.replace("各画像に所属軸xまたはyを示します。",
                                      "各IDの横に、その行の所属軸xまたはyを示します。")


def prompt(arm, ids):
    return BASE_PROMPT + (base.EXTRA if arm == "new" else "") + base.FORMAT + "、".join(ids) + "\n"


def source_hashes():
    return {p.name: base.sha(p) for p in (Path(__file__), HERE / "protocol.md", REPLICATION,
                                          rep.PREVIOUS, rep.DIAGNOSIS)}


def paper(seed, grain):
    rng = random.Random(seed)
    # 150 DPIの紙目と、450 DPIにも残る細かい濃淡。
    cells = Image.frombytes("L", (W, H), bytes(128 + rng.randint(-grain, grain) for _ in range(W * H)))
    cells = cells.resize((W * SCALE, H * SCALE), Image.Resampling.BILINEAR)
    return cells


def ink(tone):
    return (PAPER - tone,) * 3


def put(row, char, font, size, x, y, owned, width=None, height=None, contrast=116, blur=0, feature=None):
    mask = rep.glyph(char, font, size, width, height)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    row.fg = ink(contrast)
    row.put(char, mask, x, y, owned, feature)


def horizontal(image, y, sheet, case, text, level, rng):
    bracket_font = "meiryo.ttc" if sheet % 2 else "BIZ-UDMinchoM.ttc"
    mark = "）" if sheet % 2 else "】"
    right = rng.randrange(231, 277)
    region = (54, y + 3, right, y + 27)
    row = rep.Row(image, region, "x", ink(110))
    ghost, _, grain = CONTRAST[level]
    d = ImageDraw.Draw(image)
    for offset in (0, 1):
        d.line(rep.px((right - 29 + offset, y + 8 + 6 * offset,
                       right + 6, y + 8 + 6 * offset)), fill=ink(grain), width=2)
    if case == "edge":
        mark = "。"
        overlap = (1, 2, 1, 3)[sheet - 1]
        left_mark = right - overlap
        put(row, mark, "YuGothM.ttc", 9, left_mark, y + 17, overlap >= 2, 3, 3,
            contrast=50, feature="terminal_stop")
        body_end = left_mark - 1
    else:
        count = int(case[0])
        end = right - rng.choice((1, 2))
        left_mark = end - (5 * count + max(0, count - 1))
        for n in range(count):
            small = count == 2 and n == 1
            strength = (max(3, round(ghost * (0.72 if case == "2b" else 1)))
                        if small else 110)
            put(row, mark, bracket_font, 11, left_mark + 6 * n, y + 9, True,
                5, 11, contrast=strength, blur=(0.6 + 0.48 * level) if small else 0,
                feature="faint_close" if small else "strong_close")
        put(row, mark, bracket_font, 11, right + 2, y + 9, False, 5, 11, contrast=56)
        body_end = left_mark - 1
    for char in reversed(text):
        mask = rep.glyph(char, bracket_font, 10)
        body_end -= mask.width // SCALE
        row.fg = ink(104)
        row.put(char, mask, body_end, y + 19 - mask.height // SCALE, True)
        body_end -= 1
    return row, mark


def vertical(image, y, sheet, case, words, level, rng):
    family = "yumin.ttf"
    left = rng.randrange(151, 207)
    right = left + (19 if case == "v1" else 25)
    bottom = y + (27 if case == "v2" else 23)
    row = rep.Row(image, (left, y + 6, right, bottom), "y", ink(110))
    strength = CONTRAST[level][1]
    for col, text in enumerate(words):
        x = left + 17 - 10 * col
        expected_center = case != "v1" or col == 1
        for i, char in enumerate(text):
            # 右列と左列の高さをずらし、裁ち切れと淡い複雑な字を混ぜる。
            top = y + 7 + 12 * i + (2 if col else 0)
            amount = strength + (8 if i == 0 else 0) + (7 if case == "v0" and col else 0)
            if case == "v2" and col == 1 and i == 0:
                amount = 95
            owned = expected_center and min(top + 9, bottom) - top >= 5
            put(row, char, family, 11, x, top, owned, 8, 9, contrast=amount,
                blur=(level * 0.62 if amount < 90 else 0), feature="vertical_column")
    put(row, "欄", family, 10, right + 3, y + 11, False, 8, 9, contrast=50)
    return row, "。"


def render(folder, phase, sheet, level, ids):
    phase_index = ("calibration", "reserve", "comparison").index(phase)
    rng = random.Random(SEEDS[phase] + sheet * 1009 + level)
    cases = ["0", "1", "2a", "2b", "edge", "v0", "v1", "v2"]
    rng.shuffle(cases)
    image = Image.new("RGB", (W * SCALE, H * SCALE), (PAPER,) * 3)
    annotations, rows = [], []
    for i, (case, row_id) in enumerate(zip(cases, ids)):
        y = 26 + 37 * i
        if case.startswith("v"):
            vi = (sheet - 1) * 6 + 2 * int(case[-1])
            row, mark = vertical(image, y, sheet, case, VERTICAL[phase_index][vi:vi + 2], level, rng)
        else:
            j = ("0", "1", "2a", "2b").index(case) if case != "edge" else sheet % 4
            words = VOCABULARY[phase_index][(sheet - 1) * 4 + j]
            text = ("文末" + words + "を記入") if case == "edge" else words
            row, mark = horizontal(image, y, sheet, case, text, level, rng)
        gold = row.text()
        rows.append({"id": row_id, "sheet": sheet, "mark": mark, "marks": gold.count(mark),
                     "gold": gold, "case": case, "level": level, "geometry": row.geometry})
        annotations.append((row_id, row.axis, y, row.region))
    grain = paper(SEEDS[phase] + sheet * 317, CONTRAST[level][2])
    image = ImageChops.add(image, Image.merge("RGB", (grain, grain, grain)), offset=-128)
    files = []
    for dpi, raster in ((150, image.resize((W, H), Image.Resampling.BOX)), (450, image)):
        s = 1 if dpi == 150 else SCALE
        for framed in (False, True):
            panel = raster.copy()
            labels = ImageDraw.Draw(panel, "RGBA")
            face = ImageFont.truetype(base.FONTS / "meiryo.ttc", 10 * s)
            labels.text((11 * s, 6 * s), f"{dpi} DPI | {'枠あり' if framed else '枠なし'}",
                        fill="#3b3742", font=face)
            for row_id, axis, y, (l, t, r, b) in annotations:
                labels.text((11 * s, (y + 9) * s), f"{row_id} {axis}", fill="#3b3742", font=face)
                if framed:
                    outside = ((l - 1) * s, (t - 1) * s, (r + 1) * s - 1, (b + 1) * s - 1)
                    labels.rectangle(outside, outline=(179, 45, 104, 112), width=s)
            if dpi == 150:
                panel = panel.resize((W * SCALE, H * SCALE), Image.Resampling.NEAREST)
            name = f"sheet-{sheet:02d}-{dpi}-{'frame' if framed else 'plain'}.png"
            panel.save(folder / name)
            files.append(name)
    return files, rows


def gating(stats):
    return stats["repeat_missing_rows"] >= 1 and stats["unknown"] >= 1 and stats["exact"] >= 2


def paths(phase):
    return HERE / f"{phase}-lock.json", HERE / f"{phase}-result.json", ROOT / phase


def decision():
    first = HERE / "calibration-result.json"
    for phase in ("calibration", "reserve"):
        _, p, _ = paths(phase)
        if p.exists():
            report = base.load(p)
            lock, _, _ = check(phase, report["lock_sha256"])
            good = [int(level) for level, row in report["by_level"].items() if gating(row)]
            chosen = min(good, default=None)
            if report["selected_level"] != chosen or lock["phase"] != phase:
                raise ValueError("較正の採用結果が再現しない")
            if chosen is not None:
                return {"level": chosen, "phase": phase, "result_sha256": base.sha(p)}
    if not first.exists():
        raise ValueError("旧指示の較正結果がない")
    return None


def prepare(phase):
    lock_path, _, folder = paths(phase)
    selection = None
    if phase == "comparison":
        selection = decision()
        if selection is None:
            raise ValueError("較正基準を通過した難度がない")
        levels = [selection["level"]] * 4
    else:
        if phase == "reserve" and (not paths("calibration")[1].exists() or decision() is not None):
            raise ValueError("予備較正の条件を満たさない")
        levels = (1, 2, 3, 4) if phase == "calibration" else (3, 4, 5, 6)
    folder.mkdir(parents=True)
    rng = random.Random(SEEDS[phase])
    phase_id = {"calibration": "C", "reserve": "R", "comparison": "K"}[phase]
    ids = [f"{phase_id}{n}" for n in rng.sample(range(100, 999), 32)]
    image_map, truth = {}, []
    for sheet, level in enumerate(levels, 1):
        files, rows = render(folder, phase, sheet, level, ids[(sheet - 1) * 8:sheet * 8])
        image_map[str(sheet)] = files
        truth.extend(rows)
    base.write_json(folder / "gold.json", truth)
    for prior in ("calibration", "reserve") if selection else ():
        _, prior_result, other = paths(prior)
        if not prior_result.exists():
            continue
        # 原稿の本文を入れ替え、画像も画素単位で較正用とは異なる。
        previous = base.load(other / "gold.json")
        if set(ids) & {r["id"] for r in previous}:
            raise ValueError("較正用IDと重なる")
        if ({r["gold"] for r in truth} & {r["gold"] for r in previous}) - {""}:
            raise ValueError("較正用と転記本文が重なる")
        if {base.sha(folder / n) for files in image_map.values() for n in files} & {
            base.sha(n) for n in other.glob("*.png")
        }:
            raise ValueError("較正用と画像が重なる")
    for arm in ("old", "new") if selection else ("old",):
        (folder / f"{arm}-prompt.txt").write_bytes(prompt(arm, ids).encode("utf-8"))
    hashes = {f.name: base.sha(f) for f in folder.iterdir()}
    base.write_json(lock_path, {
        "phase": phase, "fixed_at": base.utc_now(), "source_sha256": source_hashes(),
        "official_input_sha256": base.frozen_hashes(), "input_sha256": hashes,
        "image_sha256": {n: hashes[n] for files in image_map.values() for n in files},
        "image_order_by_sheet": image_map, "selection": selection, "levels": levels,
        "models": base.MODELS, "third_model_by_sheet": {str(i): base.MODELS[(i-1) % 2] for i in range(1, 5)},
    })
    print("固定", phase, base.sha(lock_path), "32行、16画像", flush=True)


def check(phase, expected):
    path, _, folder = paths(phase)
    if base.sha(path) != expected:
        raise ValueError("固定SHAが異なる")
    lock = base.load(path)
    if lock["source_sha256"] != source_hashes() or lock["official_input_sha256"] != base.frozen_hashes():
        raise ValueError("コード、手順または正式評価入力が変化")
    if lock["selection"] and lock["selection"] != decision():
        raise ValueError("採用した較正結果が変化")
    for name, digest in lock["input_sha256"].items():
        if base.sha(folder / name) != digest:
            raise ValueError(f"固定入力が変化: {name}")
    rows = base.load(folder / "gold.json")
    ids = [r["id"] for r in rows]
    for arm in ("old", "new") if lock["selection"] else ("old",):
        if prompt(arm, ids).encode("utf-8") != (folder / f"{arm}-prompt.txt").read_bytes():
            raise ValueError("固定指示と一致しない")
    if len(set(ids)) != 32:
        raise ValueError("ID数が違う")
    return lock, rows, folder


def run(phase, expected, exe):
    lock, rows, folder = check(phase, expected)
    base.PRIVATE = folder
    base.prompt_for = prompt
    base.metrics = rep.metrics
    _, result_path, _ = paths(phase)
    arms = ("old", "new") if phase == "comparison" else ("old",)
    receipts = []
    votes = {arm: [] for arm in arms}
    with ThreadPoolExecutor(max_workers=4) as pool:
        first = {(arm, n): pool.submit(base.read_images, exe, lock, rows, arm, n, model)
                 for n, model in enumerate(base.MODELS, 1) for arm in arms}
        for (arm, _), job in first.items():
            answer, receipt = job.result()
            votes[arm].append(answer)
            receipts.append(receipt)
        check(phase, expected)
        pending = {arm: [r for r in rows if base.consensus([v[r["id"]] for v in votes[arm]]) is None]
                   for arm in arms}
        base.write_json(folder / "third-selection.json", {a: [r["id"] for r in g] for a, g in pending.items()})
        jobs = {}
        for arm, group in pending.items():
            for model in base.MODELS:
                portion = [r for r in group if lock["third_model_by_sheet"][str(r["sheet"])] == model]
                if portion:
                    jobs[arm, model] = pool.submit(base.read_images, exe, lock, portion, arm, 3, model)
        third = {arm: {} for arm in arms}
        for (arm, _), job in jobs.items():
            answer, receipt = job.result()
            third[arm].update(answer)
            receipts.append(receipt)
    final = {}
    for arm in arms:
        final[arm] = {i: base.consensus([v[i] for v in votes[arm]] + [third[arm].get(i)])
                      for i in (r["id"] for r in rows)}
    check(phase, expected)
    if len({r["session"] for r in receipts}) != len(receipts):
        raise ValueError("読取セッションが重複")
    result = {
        "finished": base.utc_now(), "phase": phase, "lock_sha256": expected,
        "selection": lock["selection"], "receipts": receipts,
        "third_read_rows": {arm: len(group) for arm, group in pending.items()},
        "row_outcomes": [{"id": r["id"], "case": r["case"], "sheet": r["sheet"], "level": r["level"],
                          **{a: rep.metrics([r], final[a]) for a in arms}} for r in rows],
    }
    if phase == "comparison":
        result.update(base.paired(rows, final["old"], final["new"]))
        groups = {"repeat_and_controls": [r for r in rows if r["case"] in {"0", "1", "2a", "2b"}],
                  "repeat_two": [r for r in rows if r["case"] in {"2a", "2b"}],
                  "edge": [r for r in rows if r["case"] == "edge"],
                  "vertical": [r for r in rows if r["case"].startswith("v")]}
        result["by_case"] = {k: base.paired(group, final["old"], final["new"]) for k, group in groups.items()}
        result["by_sheet"] = {str(i): base.paired([r for r in rows if r["sheet"] == i], final["old"], final["new"])
                              for i in range(1, 5)}
        result["by_initial_reader"] = {model: base.paired(rows, votes["old"][i], votes["new"][i])
                                       for i, model in enumerate(base.MODELS)}
        output = {k: result[k] for k in ("all", "joint_known", "transitions", "third_read_rows")}
    else:
        result["by_level"] = {}
        for level in lock["levels"]:
            group = [r for r in rows if r["level"] == level]
            stats = rep.metrics(group, final["old"])
            target = rep.metrics([r for r in group if r["case"] in {"2a", "2b"}], final["old"])
            stats["repeat_missing_rows"] = target["missing_rows"]
            stats["repeat_missing_marks"] = target["missing_marks"]
            result["by_level"][str(level)] = stats
        result["selected_level"] = min((int(k) for k, stats in result["by_level"].items() if gating(stats)),
                                       default=None)
        output = {k: result[k] for k in ("by_level", "selected_level", "third_read_rows")}
    base.write_json(result_path, result)
    print(output, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("calibration", "reserve", "comparison"))
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("prepare")
    reading = commands.add_parser("run")
    reading.add_argument("--codex", required=True, type=Path)
    reading.add_argument("--lock-sha256", required=True)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.phase)
    else:
        run(args.phase, args.lock_sha256, args.codex.resolve())
