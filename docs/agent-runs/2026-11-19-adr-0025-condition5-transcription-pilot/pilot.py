"""条件5の開発専用画像を固定し、独立した画像読みと対比較を実行する。"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unicodedata

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BENCH = ROOT / "docs/research/adr-0025-condition5-2026-11-16"
PRIVATE = BENCH / "corpus/transcription-pilot-2026-11-19"
NORMALIZER = ROOT / "info-hive-rag/scripts/rag_ocr_flags.py"
sys.path.insert(0, str(NORMALIZER.parent))
from rag_ocr_flags import normalize


FONTS = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
SHEETS = (
    ("）", "meiryo.ttc", (
        "＊予備部品を受け取る", "番号を照合＊して封をする", "現品を戻す＊",
        "＊温度計を棚に並べる", "付属品を戻し＊印を押す", "電源を切った＊",
        "＊伝票を付けて戻す", "黒い袋へ＊封入する", "在庫を補う＊",
    )),
    ("」", "yumin.ttf", (
        "＊絵に合う語を選ぶ", "緑＊白の旗を振る", "次の名前を書く＊",
        "＊旗を並べて数える", "木材＊金具を運ぶ", "午後の日差し＊",
        "＊文字の形を比べる", "紙＊布を使う", "最後まで読む＊",
    )),
    ("。", "YuGothM.ttc", (
        "＊橋を渡って北へ進む", "雨が止んだ＊道を戻る", "水場を探した＊",
        "＊右側の棚を確認する", "風が吹く＊舟を止める", "午後に届ける＊",
        "＊暗くなってから戻る", "池が見えた＊声がした", "窓を閉じた＊",
    )),
    ("】", "BIZ-UDMinchoM.ttc", (
        "＊講座の準備を進める", "概要＊会場の案内", "係員が札を配る＊",
        "＊配布物を照合する", "予備資料＊午後の部", "図を添えて掲示＊",
        "＊部屋の照明を消す", "展示図＊青い枠で囲む", "手順を確かめる＊",
    )),
)
PROMPT = """添付画像だけを見て、指定されたIDの行を転記してください。ツール、ファイル検索、OCRは使わないでください。
画像は原稿ごとに4枚です。各画像の上に固定150 DPI／450 DPIと、枠あり／枠なしの組を表示しています。各行について両解像度と枠の有無をすべて見比べてください。
所属軸はxです。固定150 DPIの画像で、字のインクの左右の長さの半分以上が枠内にあり、上下のインク中心が枠内にある字を含めます。字の識別には450 DPIと枠外に見える同じ字の部分も使えます。字が所属する場合は、部分的に枠外でもその字全体を転記します。
枠に属さない別の字を足さず、見えない文を文脈で補わず、画像の自然な順序で転記してください。句読点や同形に見える字を都合よくそろえないでください。
字の識別または所属が決められなければ行全体をunreadableとして本文を「?」に、字がないと決めた場合はemptyとして本文を空に、それ以外はreadableとして本文を書いてください。
"""
EXTRA = "提出前に連続記号の位置と個数を見直す。\n"
FORMAT = """回答はJSONオブジェクトのみです。形式は {"answers":[{"id":"画像のID","status":"readable","text":"行の本文"}]} です。各指定IDに1件ずつ回答してください。
対象ID: """
MODELS = ("gpt-6.2-sol", "gpt-6.2-astra")
FROZEN = (
    ROOT / "docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md",
    BENCH / "scripts/score_v2.py",
    BENCH / "scripts/score_v4.py",
    BENCH / "results/v9-fixed-revalidation.json",
    BENCH / "results/reference-audit-v9-result.json",
    NORMALIZER,
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(value, target, ensure_ascii=False, indent=2)
        target.write("\n")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ink_box(font, char, x, baseline):
    mask, (dx, dy) = font.getmask2(char, mode="L", anchor="ls")
    l, t, r, b = mask.getbbox()
    return x + dx + l, baseline + dy + t, x + dx + r, baseline + dy + b


def belongs(box, left, top, right, bottom):
    l, t, r, b = box
    return 2 * (min(r, right) - max(l, left)) >= r - l and 2 * top <= t + b < 2 * bottom


def images_for_sheet(sheet, fontname, mark, rows):
    image_paths = []
    for dpi in (150, 450):
        scale = dpi // 150
        for framed in (False, True):
            im = Image.new("RGB", (414 * scale, 314 * scale), "#faf9f5")
            draw = ImageDraw.Draw(im)
            label = ImageFont.truetype(FONTS / "meiryo.ttc", 11 * scale)
            draw.text((12 * scale, 6 * scale), f"{dpi} DPI | {'枠あり' if framed else '枠なし'}",
                      font=label, fill="#444444", anchor="lt")
            for index, row in enumerate(rows):
                y = 28 + 31 * index
                left, right = 63, 351
                size = (11, 14, 16)[(index + index // 3 + sheet) % 3]
                font = ImageFont.truetype(FONTS / fontname, size * scale)
                fg = ("#1c2023", "#253836", "#39352d", "#594e51")[sheet - 1]
                panel = ("#f1eee7", "#e9f1ed", "#f7f5ed", "#ececf4")[sheet - 1]
                draw.rectangle((left * scale, y * scale, right * scale, (y + 24) * scale),
                               fill=panel)
                if index % 3 == 1:
                    draw.line(((left + 2) * scale, (y + 22) * scale,
                               (right - 3) * scale, (y + 22) * scale),
                              fill="#a4acae", width=scale)
                if index % 3 == 2:
                    draw.rectangle(((right - 23) * scale, (y + 7) * scale,
                                    (right - 14) * scale, (y + 15) * scale),
                                   fill=("#8da298", "#d9b58b", "#b7a5c7", "#adb5d1")[sheet - 1])
                draw.text((13 * scale, (y + 6) * scale), row["id"], font=label,
                          fill="#34343e", anchor="lt")
                # 対象外の同種記号と、紙面端で切れた文字片を置く。
                side_font = ImageFont.truetype(FONTS / fontname, 15 * scale)
                roi = (left * scale, y * scale, right * scale, (y + 24) * scale)
                side_xy = ((right + 7) * scale, (y + 17) * scale)
                if belongs(ink_box(side_font, mark, *side_xy), *roi):
                    raise ValueError(f"枠外記号が所属した: {row['id']}")
                draw.text(side_xy, mark, font=side_font, fill=fg, anchor="ls")
                if index % 2 == 0:
                    fragment_xy = (-8 * scale, (y + 20) * scale)
                    if belongs(ink_box(side_font, "部", *fragment_xy), *roi):
                        raise ValueError(f"枠外の文字片が所属した: {row['id']}")
                    draw.text(fragment_xy, "部", font=side_font, fill=fg, anchor="ls")
                x = (left + (7, 27, 43, 18)[(index + sheet) % 4]) * scale
                baseline = (y + 19) * scale
                run = row["gold"]
                for i, char in enumerate(run):
                    box = ink_box(font, char, x, baseline)
                    if not belongs(box, *roi) or not (
                        roi[0] < box[0] < box[2] < (right - 30) * scale
                        and roi[1] < box[1] < box[3] < (y + 22) * scale
                    ):
                        raise ValueError(f"字のインクが意図した枠内にない: {row['id']}")
                    draw.text((x, baseline), char, font=font, fill=fg, anchor="ls")
                    advance = font.getlength(char)
                    if char == mark and run[i + 1:i + 2] == mark:
                        # 連続記号の一部は間隔を詰めるが、インクは接触させない。
                        gap = (1, 2, 4)[(index + sheet) % 3] * scale
                        advance = min(advance, box[2] - box[0] + gap)
                    x += round(advance)
                if framed:
                    draw.rectangle((left * scale, y * scale, right * scale, (y + 24) * scale),
                                   outline="#af3c64", width=scale)
            if dpi == 150:
                im = im.resize((im.width * 3, im.height * 3), Image.Resampling.NEAREST)
            name = f"sheet-{sheet:02d}-{dpi}-{'frame' if framed else 'plain'}.png"
            im.save(PRIVATE / name, dpi=(450, 450))
            image_paths.append(name)
    return image_paths


def frozen_hashes():
    return {str(path.relative_to(ROOT)): sha(path) for path in FROZEN}


def prepare():
    PRIVATE.mkdir(parents=True)
    rng = random.Random(250519)
    ids = rng.sample(range(100, 999), 36)
    rows = []
    images = {}
    for sheet, (mark, fontname, lines) in enumerate(SHEETS, 1):
        sheet_rows = []
        # 3つの位置それぞれで個数を均衡させ、位置ごとの並びは別々に決める。
        counts_by_position = [rng.sample(range(3), 3) for _ in range(3)]
        for index, line in enumerate(lines):
            count = counts_by_position[index % 3][index // 3]
            gold = line.replace("＊", mark * count)
            row_id = f"R{ids.pop()}"
            sheet_rows.append({"id": row_id, "sheet": sheet, "mark": mark,
                               "marks": count, "gold": gold})
        images[str(sheet)] = images_for_sheet(sheet, fontname, mark, sheet_rows)
        rows.extend(sheet_rows)
    write_json(PRIVATE / "gold.json", rows)
    all_ids = [row["id"] for row in rows]
    prompts = {}
    for arm in ("old", "new"):
        path = PRIVATE / f"{arm}-prompt.txt"
        path.write_text(prompt_for(arm, all_ids), encoding="utf-8", newline="\n")
        prompts[path.name] = sha(path)
    manifest = {
        "fixed_at": utc_now(), "rows": len(rows), "gold_sha256": sha(PRIVATE / "gold.json"),
        "protocol_sha256": sha(HERE / "protocol.md"), "code_sha256": sha(Path(__file__)),
        "official_input_sha256": frozen_hashes(), "initial_models": MODELS,
        "third_model_by_sheet": {str(i): MODELS[(i - 1) % 2] for i in range(1, len(SHEETS) + 1)},
        "image_order_by_sheet": images, "first_prompt_sha256": prompts,
        "image_sha256": {name: sha(PRIVATE / name) for names in images.values() for name in names},
    }
    write_json(HERE / "lock.json", manifest)
    print("固定", sha(HERE / "lock.json"), f"{len(rows)}行、{sum(map(len, images.values()))}画像",
          flush=True)


def prompt_for(arm, ids):
    return PROMPT + (EXTRA if arm == "new" else "") + FORMAT + "、".join(ids) + "\n"


def check_lock(expected):
    if sha(HERE / "lock.json") != expected:
        raise ValueError("指定された固定記録のSHAと異なる")
    lock = load(HERE / "lock.json")
    if (lock["code_sha256"] != sha(Path(__file__))
            or lock["protocol_sha256"] != sha(HERE / "protocol.md")
            or lock["official_input_sha256"] != frozen_hashes()
            or lock["gold_sha256"] != sha(PRIVATE / "gold.json")):
        raise ValueError("固定後にコード、計画、公式入力または正解が変化")
    for name, expected_sha in (lock["image_sha256"] | lock["first_prompt_sha256"]).items():
        if sha(PRIVATE / name) != expected_sha:
            raise ValueError(f"固定後に入力が変化: {name}")
    rows = load(PRIVATE / "gold.json")
    ids = [row["id"] for row in rows]
    if len(set(ids)) != 36 or Counter(row["marks"] for row in rows) != {0: 12, 1: 12, 2: 12}:
        raise ValueError("固定した行数または対象記号数が異なる")
    for arm in ("old", "new"):
        if (PRIVATE / f"{arm}-prompt.txt").read_text(encoding="utf-8") != prompt_for(arm, ids):
            raise ValueError("提示する指示が固定した指示と異なる")
    return lock, rows


def parse_response(stdout, ids):
    events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    if any(event["item"]["type"] not in {"reasoning", "agent_message"}
           for event in events if event["type"].startswith("item.")):
        raise ValueError("画像への回答以外の操作を検出")
    items = [event["item"] for event in events if event["type"] == "item.completed"]
    sessions = [event["thread_id"] for event in events if event["type"] == "thread.started"]
    completed = [event["usage"] for event in events if event["type"] == "turn.completed"]
    messages = [item["text"] for item in items if item["type"] == "agent_message"]
    if len(sessions) != 1 or len(completed) != 1 or not messages:
        raise ValueError("読み取り完了のイベントが欠落")
    answer = messages[-1].strip()
    if answer.startswith("```json\n") and answer.endswith("\n```"):
        answer = answer.removeprefix("```json\n").removesuffix("\n```")
    obj = json.loads(answer)
    if set(obj) != {"answers"} or not isinstance(obj["answers"], list):
        raise ValueError("転記のJSON形式が異なる")
    values = {}
    for row in obj["answers"]:
        if set(row) != {"id", "status", "text"} or not isinstance(row["text"], str):
            raise ValueError("行の回答形式が異なる")
        row_id, status, value = row["id"], row["status"], row["text"]
        if row_id in values or not (
            (status == "unreadable" and value == "?")
            or (status == "empty" and value == "")
            or (status == "readable" and normalize(value) and "\n" not in value)
        ):
            raise ValueError("回答の重複または状態と本文の不整合")
        values[row_id] = None if status == "unreadable" else normalize(value)
    if values.keys() != set(ids):
        raise ValueError("転記の対象IDが依頼と異なる")
    return sessions[0], completed[0], values


def read_images(exe, lock, rows, arm, read, model):
    ids = [row["id"] for row in rows]
    sheets = dict.fromkeys(str(row["sheet"]) for row in rows)
    names = [name for sheet in sheets for name in lock["image_order_by_sheet"][sheet]]
    prompt = prompt_for(arm, ids).encode("utf-8")
    env = os.environ.copy()
    for key in ("CODEX_WINDOWS_REGISTERED_CORE", "CODEX_WINDOWS_SANDBOX_PACKAGE_FAMILY"):
        env.pop(key, None)
    prefix = f"{arm}-read{read}-{model}"
    with tempfile.TemporaryDirectory(prefix="region-read-") as directory:
        command = [
            str(exe), "exec", "--json", "--ephemeral", "--skip-git-repo-check",
            "--ignore-user-config", "--disable", "memories", "--disable", "plugins",
            "--disable", "shell_tool", "-c", 'web_search="disabled"',
            "-s", "read-only", "-c", 'approval_policy="never"', "-c",
            'model_reasoning_effort="medium"', "-m", model, "-C", directory,
            *(f"--image={PRIVATE / name}" for name in names), "-",
        ]
        write_json(PRIVATE / f"{prefix}-request.json", {
            "model": model, "ids": ids, "started": utc_now(), "prompt": prompt.decode("utf-8"),
            "images": names, "image_sha256": [lock["image_sha256"][name] for name in names],
        })
        failed = []
        for attempt in (1, 2):
            try:
                proc = subprocess.run(command, input=prompt, capture_output=True, env=env,
                                      cwd=directory, timeout=900)
                (PRIVATE / f"{prefix}-{attempt}.jsonl").write_bytes(proc.stdout)
                (PRIVATE / f"{prefix}-{attempt}.stderr").write_bytes(proc.stderr)
                if proc.returncode:
                    raise ValueError(f"CLI終了コード {proc.returncode}")
                session, usage, values = parse_response(proc.stdout.decode("utf-8"), ids)
            except (ValueError, TypeError, KeyError, OSError, subprocess.TimeoutExpired) as error:
                failed.append(f"{type(error).__name__}: {error}")
                print(f"{prefix} 試行{attempt}: {failed[-1]}", flush=True)
                continue
            receipt = {
                "arm": arm, "read": read, "model": model, "session": session,
                "attempt": attempt, "failures": failed, "finished": utc_now(),
                "rows": len(values), "unreadable": sum(value is None for value in values.values()),
                "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
                "image_sha256": [lock["image_sha256"][name] for name in names],
                "response_sha256": sha(PRIVATE / f"{prefix}-{attempt}.jsonl"), "usage": usage,
            }
            write_json(PRIVATE / f"{prefix}-answers.json", values)
            write_json(PRIVATE / f"{prefix}-receipt.json", receipt)
            print(f"{prefix} {len(values)}行（判読不能票 {receipt['unreadable']}）", flush=True)
            return values, receipt
    raise RuntimeError(f"{prefix} 受領失敗: {failed}")


def consensus(votes):
    for first, second in itertools.combinations(votes, 2):
        if first is not None and first == second:
            return first
    return None


def metrics(rows, values):
    result = dict.fromkeys(("rows", "exact", "wrong", "unknown", "missing_marks",
                            "missing_rows", "extra_marks", "extra_mark_rows",
                            "extra_chars", "extra_char_rows"), 0)
    result["rows"] = len(rows)
    for row in rows:
        value = values[row["id"]]
        if value is None:
            result["unknown"] += 1
            continue
        gold = normalize(row["gold"])
        result["exact" if value == gold else "wrong"] += 1
        mark = normalize(row["mark"])
        missing = max(0, gold.count(mark) - value.count(mark))
        extras = Counter(value) - Counter(gold)
        extra_marks = sum(n for char, n in extras.items() if unicodedata.category(char)[0] in "PS")
        result["missing_marks"] += missing
        result["missing_rows"] += bool(missing)
        result["extra_marks"] += extra_marks
        result["extra_mark_rows"] += bool(extra_marks)
        result["extra_chars"] += extras.total()
        result["extra_char_rows"] += bool(extras)
    return result


def paired(rows, old, new):
    shared = [row for row in rows if old[row["id"]] is not None and new[row["id"]] is not None]
    transitions = Counter()
    for row in rows:
        gold = normalize(row["gold"])
        before, after = (old[row["id"]], new[row["id"]])
        start = "unknown" if before is None else "exact" if before == gold else "wrong"
        end = "unknown" if after is None else "exact" if after == gold else "wrong"
        transitions[f"{start}_to_{end}"] += 1
    return {
        "all": {"old": metrics(rows, old), "new": metrics(rows, new)},
        "joint_known": {"old": metrics(shared, old), "new": metrics(shared, new)},
        "transitions": dict(sorted(transitions.items())),
    }


def summarize(rows, prelim, final, third_ids):
    gold_by_sheet = {str(sheet): [row for row in rows if row["sheet"] == sheet]
                     for sheet in range(1, len(SHEETS) + 1)}
    report = paired(rows, final["old"], final["new"])
    report["by_sheet"] = {sheet: paired(group, final["old"], final["new"])
                          for sheet, group in gold_by_sheet.items()}
    report["by_target_count"] = {
        str(n): paired([row for row in rows if row["marks"] == n], final["old"], final["new"])
        for n in (0, 1, 2)
    }
    report["by_initial_reader"] = {MODELS[i]: paired(rows, prelim["old"][i], prelim["new"][i])
                                   for i in (0, 1)}
    report["third_read_rows"] = {arm: len(ids) for arm, ids in third_ids.items()}
    before, after = (report["joint_known"][arm] for arm in ("old", "new"))
    extra_keys = ("extra_marks", "extra_mark_rows", "extra_chars", "extra_char_rows")
    report["criterion"] = {
        "missing_marks_decreased": after["missing_marks"] < before["missing_marks"],
        "missing_marks_decreased_in_two_sheets": sum(
            group["joint_known"]["new"]["missing_marks"] < group["joint_known"]["old"]["missing_marks"]
            for group in report["by_sheet"].values()
        ) >= 2,
        "extra_transcription_did_not_increase": all(after[k] <= before[k] for k in extra_keys),
        "unknown_did_not_increase": report["all"]["new"]["unknown"] <= report["all"]["old"]["unknown"],
        "no_known_to_unknown": not any(report["transitions"].get(key, 0)
                                       for key in ("exact_to_unknown", "wrong_to_unknown")),
        "exact_matches_did_not_decrease": after["exact"] >= before["exact"],
    }
    report["supports_replication"] = all(report["criterion"].values())
    return report


def run(exe, expected):
    lock, rows = check_lock(expected)
    arms = ("old", "new")
    receipts = []
    prelim = {arm: [] for arm in arms}
    with ThreadPoolExecutor(max_workers=4) as pool:
        initial = {(arm, read): pool.submit(read_images, exe, lock, rows, arm, read, MODELS[read - 1])
                   for read in (1, 2) for arm in arms}
        for (arm, _), future in initial.items():
            answers, receipt = future.result()
            prelim[arm].append(answers)
            receipts.append(receipt)
        check_lock(expected)
        pending = {
            arm: [row for row in rows if consensus([vote[row["id"]] for vote in prelim[arm]]) is None]
            for arm in arms
        }
        write_json(PRIVATE / "third-selection.json",
                   {arm: [row["id"] for row in pending[arm]] for arm in arms})
        futures = {}
        for arm, group in pending.items():
            for model in MODELS:
                subset = [row for row in group if lock["third_model_by_sheet"][str(row["sheet"])] == model]
                if subset:
                    futures[arm, model] = pool.submit(read_images, exe, lock, subset, arm, 3, model)
        final = {}
        for arm in arms:
            third = {}
            for model in MODELS:
                if (arm, model) in futures:
                    answers, receipt = futures[arm, model].result()
                    third.update(answers)
                    receipts.append(receipt)
            final[arm] = {}
            for row in rows:
                row_id = row["id"]
                votes = [first[row_id] for first in prelim[arm]]
                if row_id in third:
                    votes.append(third[row_id])
                final[arm][row_id] = consensus(votes)
    if len({receipt["session"] for receipt in receipts}) != len(receipts):
        raise ValueError("読み手のセッションが重複")
    check_lock(expected)
    result = summarize(rows, prelim, final, pending)
    result.update(finished=utc_now(), lock_sha256=expected, receipts=receipts)
    write_json(HERE / "result.json", result)
    print(json.dumps({"all": result["all"], "third": result["third_read_rows"],
                      "criterion": result["criterion"]}, ensure_ascii=False), flush=True)


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
