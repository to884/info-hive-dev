"""旧指示で較正し、枠外の代替と地色の埋没を抑えた画像で比較する。"""

import argparse
import importlib.util
import itertools
import math
from pathlib import Path
import random

from PIL import ImageFilter

HERE = Path(__file__).resolve().parent
FIRST = HERE.parent / "2026-11-19-adr-0025-condition5-transcription-calibrated/calibrated.py"
spec = importlib.util.spec_from_file_location("trial", FIRST)
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)
base, rep = trial.base, trial.rep
trial.HERE = HERE
trial.ROOT = base.BENCH / "corpus/transcription-calibrated-v2-2026-11-19"
trial.SEEDS = {"calibration": 87965, "reserve": 93337, "comparison": 84289}
GRAIN = 3
trial.CONTRAST = {i: (close, vert, GRAIN) for i, (close, vert) in enumerate(
    ((28, 33), (19, 24), (13, 17), (9, 13), (6, 10), (5, 8)), 1
)}
trial.VOCABULARY = tuple(tuple(a + b for a, b in itertools.product(heads, tails))
                         for heads, tails in (
    (("卓上", "上段", "裏口", "回覧"), ("の札", "の紙", "の箱", "の鍵")),
    (("水路", "南棟", "届出", "返却"), ("の欄", "の図", "の束", "の袋")),
    (("想定", "見取", "測定", "改訂"), ("の順", "の版", "の印", "の台")),
))
trial.VERTICAL = tuple(tuple(s.split()) for s in (
    "当直 点呼 設計 寄稿 巡回 便覧 測定 許可 変更 監材 予算 報知 報奨 検索 豊穣 補給 文庫 銀行 人員 織物 整備 判型 取引 立案",
    "表紙 室温 推敲 配分 教材 施工 受渡 板紙 季節 図柄 出荷 川幅 地域 備蓄 折返 書架 青果 判定 交通 代表 草案 電卓 裁断 営業",
    "索引 衛生 先発 授与 動力 救護 封緘 清書 中央 受講 記念 法令 増設 臨時 検温 物資 案内 論説 回答 研磨 第三 成果 組合 根拠",
))
EDGE_TEXT = (
    ("用紙を縦に置く", "決裁順を守る", "定規を手前に引く", "反対側へ回す"),
    ("数値を照合する", "奥の部屋を調べる", "留め具を緩める", "下段へ記す"),
    ("十字の位置を測る", "早朝に搬入する", "表面を乾かす", "数値を足す"),
)
ADDRESS = ("calibration", "reserve", "comparison")


def source_hashes():
    files = (Path(__file__), FIRST, HERE / "protocol.md", trial.REPLICATION, rep.PREVIOUS, rep.DIAGNOSIS)
    return {p.name: base.sha(p) for p in files}


def put(row, char, font, size, x, y, owned, width=None, height=None, contrast=116, blur=0, feature=None):
    mask = rep.glyph(char, font, size, width, height)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    if owned:
        pixels = sorted(mask.getdata(), reverse=True)
        floor = math.ceil(3 * GRAIN / math.sqrt(3))
        alpha = pixels[7] / 255
        if not alpha:
            raise ValueError("8画素の字形がない")
        contrast = max(contrast, math.ceil(floor / alpha))
        if contrast > 125 or round(alpha * contrast) < floor:
            raise ValueError("前景の濃度を確保できない")
    row.fg = trial.ink(contrast)
    row.put(char, mask, x, y, owned, feature)
    if feature:
        row.geometry[-1]["foreground_gray_delta"] = contrast


def horizontal(image, y, sheet, case, text, level, rng):
    face, mark = "meiryo.ttc", "）"
    right = rng.randrange(232, 268)
    row = rep.Row(image, (53, y + 3, right, y + 27), "x", trial.ink(110))
    if case == "edge":
        mark = "。"
        put(row, mark, face, 9, right - 1, y + 18, False, 3, 3,
            contrast=47, feature="terminal_stop")
        body_end = right - 2
    else:
        count = int(case[0])
        end = right - rng.choice((1, 2))
        gap = 1 if level <= 2 else 0
        position = end - (5 * count + max(count - 1, 0) * gap)
        for n in range(count):
            faint = count == 2 and n == 1
            contrast = trial.CONTRAST[level][0] if case == "2a" else round(trial.CONTRAST[level][0] * .72)
            put(row, mark, face, 11, position + (5 + gap) * n, y + 9, True, 5, 11,
                contrast=contrast if faint else 110, blur=(.65 + .47 * level) if faint else 0,
                feature="faint_close" if faint else "strong_close")
        outside = "＋" if count == 2 else mark
        if count == 2 and base.normalize(outside) == base.normalize(mark):
            raise ValueError("枠外の記号で脱落が隠れる")
        put(row, outside, face, 11, right + 3, y + 9, False, 5, 11, contrast=62,
            feature="outside_close")
        body_end = position - 1
    for char in reversed(text):
        mask = rep.glyph(char, face, 10)
        body_end -= mask.width // trial.SCALE
        put(row, char, face, 10, body_end, y + 19 - mask.height // trial.SCALE, True)
        body_end -= 1
    return row, mark


def render(folder, phase, sheet, level, ids):
    # 前の画像生成器で画像形式だけを共用し、句点の本文は専用に割り当てる。
    def render_horizontal(image, y, sheet, case, text, level, rng):
        if case == "edge":
            text = EDGE_TEXT[ADDRESS.index(phase)][sheet - 1]
        return horizontal(image, y, sheet, case, text, level, rng)

    trial.horizontal = render_horizontal
    return trial.render(folder, phase, sheet, level, ids)


def prepare(phase):
    path, _, folder = trial.paths(phase)
    selection = trial.decision() if phase in ("comparison", "reserve") else None
    if phase == "comparison" and selection is None:
        raise ValueError("較正を通過した設定がない")
    if phase == "reserve" and selection is not None:
        raise ValueError("較正を通過したため予備は不要")
    levels = {"calibration": [1, 2, 3, 4], "reserve": [3, 4, 5, 6],
              "comparison": [selection["level"]] * 4 if selection else []}[phase]
    folder.mkdir(parents=True)
    ids = [f"{'TRJ'[ADDRESS.index(phase)]}{i}" for i in random.Random(trial.SEEDS[phase]).sample(range(100, 999), 32)]
    image_map, gold = {}, []
    for sheet, level in enumerate(levels, 1):
        files, rows = render(folder, phase, sheet, level, ids[(sheet - 1)*8:sheet*8])
        image_map[str(sheet)] = files
        gold.extend(rows)
    base.write_json(folder / "gold.json", gold)
    if phase == "comparison":
        for prior in ("calibration", "reserve"):
            _, prev_result, other = trial.paths(prior)
            if not prev_result.exists():
                continue
            before = base.load(other / "gold.json")
            if set(ids) & {r["id"] for r in before} or {r["gold"] for r in gold} & {r["gold"] for r in before}:
                raise ValueError("較正と比較のIDまたは本文が重なる")
            if {base.sha(p) for p in folder.glob("*.png")} & {base.sha(p) for p in other.glob("*.png")}:
                raise ValueError("較正と比較の画像が重なる")
    for arm in ("old", "new") if selection else ("old",):
        (folder / f"{arm}-prompt.txt").write_bytes(trial.prompt(arm, ids).encode("utf-8"))
    hashes = {p.name: base.sha(p) for p in folder.iterdir()}
    base.write_json(path, {
        "phase": phase, "fixed_at": base.utc_now(), "levels": levels, "selection": selection,
        "source_sha256": source_hashes(), "official_input_sha256": base.frozen_hashes(),
        "input_sha256": hashes, "image_order_by_sheet": image_map,
        "image_sha256": {n: hashes[n] for names in image_map.values() for n in names},
        "models": base.MODELS, "third_model_by_sheet": dict.fromkeys(image_map, base.MODELS[1]),
    })
    print("固定", phase, base.sha(path), "32行、16画像", flush=True)


trial.put = put
trial.source_hashes = source_hashes
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=ADDRESS)
    children = parser.add_subparsers(dest="action", required=True)
    children.add_parser("prepare")
    run = children.add_parser("run")
    run.add_argument("--codex", type=Path, required=True)
    run.add_argument("--lock-sha256", required=True)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.phase)
    else:
        trial.run(args.phase, args.lock_sha256, args.codex.resolve())
