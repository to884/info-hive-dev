"""旧監査の別表示による開発用の画像二読。"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v10-reference-audit"))
import cards
import readers

LOAD, SHA = cards.load, cards.sha
NORMALIZE = cards.score.audit.normalize
OUT = cards.CORPUS / "reference-v11-ordered-image-pilot"
LOCK = HERE / "lock.json"
SEED = "adr0025-v11-ordered-image-20261120"
MODELS = cards.MODELS
INTRO = (
    "150 DPIの枠で所属を判定し、450 DPIの枠あり・なしで字形を確認してください。"
    "割当軸xは字全体の左右のインク長さの半分以上と上下のインク中心が枠内、軸yはその逆です。"
    "離れた筆画も同じ字ならその字の全体を考えます。図形や所属しない隣の字を除き、形を意味から補わないでください。"
    "元画像の周囲の印と枠は区別してください。"
)
PARTS = (
    "所属する文字を列または横の並びごとに分けます。横座標の目盛りは枠内の左を0とします。"
    "各列の字を上から下へ転記し、列のインク中心のおよその横座標を整数で付けます。短い横書きは文字を左から右へ写します。"
    "縦書きなら回答のtextを V|28:甲|12:乙丙 の形式にします。28、12は例の横座標です。列を並べる順は問いません。"
    "一列の中に横書きの小さなまとまりがある場合は、字形の自然な順にそのまとまりを写します。"
    "横書きと確かめたときは H|本文 とします。割当の軸だけから縦・横を決めません。"
)
VERTICAL = (
    "末尾の『450 DPI 細部』では元の縦の向きのまま字を大きく示します。"
    "番号の順に上から字を追い、重なる部分を一度だけ転記します。繰り返しでも各字の点と横画を個別に確認してください。"
    "textには一つの全文を入れます。"
)
FORMAT = (
    "分からない字・所属・列が残る場合はstatusをunreadable、textを?としてください。"
    "字が一つもなければstatusをempty、textを空文字にします。転記できたときはstatusをreadableにします。"
    'JSONだけを返してください。形式は {"answers":[{"id":"対象ID","status":"readable","text":"転記"}]} です。対象IDは '
)


def selection():
    old = cards.HERE
    diagnosis = LOAD(old / "diagnosis.json")
    result = LOAD(old / "result.json")
    if diagnosis["audit_sha256"] != SHA(old / "result.json"):
        raise ValueError("監査の確定結果と診断が異なる")
    evidence = cards.OUT / "reference-evidence.json"
    if result["detailed_reference_sha256"] != SHA(evidence):
        raise ValueError("既存の参照と証跡が異なる")
    known = LOAD(evidence)
    rows = LOAD(cards.SOURCE)["selected"]
    index = {(r["key"], r["line_index"]): i for i, r in enumerate(rows)}
    picked = {}
    for r in diagnosis["cases"]:
        if not r["key"].startswith("kanpo"):
            continue
        if r["axis"] == "x" and r["diagnosis"] == "reading-order":
            picked[index[r["key"], r["line_index"]]] = "columns"
        if r["axis"] == "y" and r["outcome"] == "mismatch" and r["height"] >= 300:
            picked[index[r["key"], r["line_index"]]] = "vertical"
    if Counter(picked.values()) != {"columns": 6, "vertical": 2}:
        raise ValueError("事前に記録した開発対象と異なる")
    done = set(picked)
    for kind in ("columns", "vertical"):
        pages = {rows[i]["key"] for i, category in picked.items() if category == kind}
        domain = "image" if kind == "columns" else "region"
        pool = []
        for i, row in enumerate(rows):
            width, height = row["box"][2:]
            v = row["targets"].get(domain)
            shape = row["allocation_axis"] == "x" and 16 <= width <= 120 and 12 <= height <= 35 if kind == "columns" else (
                row["allocation_axis"] == "y" and width <= 26 and height >= 300)
            ref = known[f"{row['key']}/{row['line_index']}"]["answer"]
            if (row["key"] in pages and shape and i not in done and v and v["known"]
                    and ref["status"] == "readable" and NORMALIZE(v["text"]) == NORMALIZE(ref["text"])):
                pool.append(i)
        take = sorted(pool, key=lambda i: hashlib.sha256(f"{SEED}/{kind}/{i}".encode()).digest())[:2]
        if len(take) != 2:
            raise ValueError(f"同じ寸法帯の対照が足りない: {kind}")
        for i in take:
            picked[i] = kind + "-control"
        done.update(take)
    return rows, picked


def spans(total):
    cursor = 0
    while cursor < total:
        end = min(total, cursor + 360)
        yield cursor, end
        if end == total:
            break
        cursor = end - 66


def details(asset, ident, vertical, font):
    view = asset["views"][1]
    opened = []
    for kind in ("plain", "framed"):
        item = next(x for x in view["images"] if x["kind"] == kind)
        path = cards.OUT / "source-assets" / item["image"]
        if SHA(path) != LOAD(cards.PACKS)["source_assets"][item["image"]]:
            raise ValueError("拡大する固定画像が異なる")
        with Image.open(path) as image:
            opened.append(image.convert("RGB"))
    x0, y0, x1, y1 = view["target_rectangle"]
    left, top, right, bottom = math.floor(x0), math.floor(y0), math.ceil(x1), math.ceil(y1)
    total = bottom - top if vertical else right - left
    images = {}
    for ordinal, (a,b) in enumerate(spans(total), 1):
        x, y = (left, top + a) if vertical else (left + a, top)
        r, s = (right, top + b) if vertical else (left + b, bottom)
        bounds = max(0, x-52), max(0,y-36), min(opened[0].width,r+52), min(opened[0].height,s+36)
        parts = [pic.crop(bounds) for pic in opened]
        width, height = parts[0].width*2, parts[0].height*2
        panel = Image.new("RGB", (max(295,2*width+24), height+51), "white")
        title = ImageDraw.Draw(panel)
        title.text((4,2), f"{ident}   450 DPI 細部 {ordinal}", font=font, fill="#222222")
        for i,pixels in enumerate(parts):
            x = 5 + i*(width+12)
            title.text((x,25), "枠なし" if i == 0 else "枠あり", font=font, fill="#222222")
            view_pixels = pixels.resize((width,height), Image.Resampling.NEAREST)
            panel.paste(view_pixels,(x,48))
        buffer = io.BytesIO()
        panel.save(buffer, "PNG")
        images[f"{ident}-extra-{ordinal:02d}.png"] = buffer.getvalue()
    return images


def material():
    rows, selected = selection()
    origin = LOAD(cards.PACKS)
    font_path = cards.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(font_path, size=17)
    by_index = {m["entry"]: (name, label, m, p["request"]) for name,p in origin["packs"].items() for label,m in p["mapping"].items()}
    prepared, all_images = {}, {}
    for n,(i, kind) in enumerate(sorted(selected.items())):
        arm, selected_id, mapping, request = by_index[i]
        fixed = {}
        for filename, digest in zip(request["images"], request["image_sha256"], strict=True):
            if filename.startswith(selected_id + "-"):
                blob = (cards.OUT / "cards" / arm / filename).read_bytes()
                if readers.sha(blob) != digest:
                    raise ValueError("元の配布画像が変化")
                fixed[filename] = blob
        if not fixed:
            raise ValueError("元の配布画像がない")
        vertical = kind.startswith("vertical")
        extra = details(mapping["image_reference"]["source_view"], selected_id, vertical, font)
        pack = f"pack-{n:02d}"
        blobs = fixed | extra
        if len(blobs) > 24:
            raise ValueError("1行に配る画像が24枚を超える")
        prepared[pack] = {"entry":i,"kind":kind, "request":{
            "ids":[selected_id],"images":list(blobs),"image_sha256":[readers.sha(b) for b in blobs.values()],
            "prompt": INTRO + (VERTICAL if vertical else PARTS) + FORMAT + selected_id + "。"}}
        all_images[pack] = blobs
    paths = (Path(__file__), HERE / "protocol.md", cards.PACKS, cards.SOURCE, cards.HERE / "diagnosis.json",
             cards.HERE / "result.json", cards.OUT / "reference-evidence.json", Path(cards.__file__), Path(readers.__file__), font_path)
    return {"inputs":{str(p):SHA(p) for p in paths}, "models":MODELS,"packs":prepared}, all_images


def decode(answer, kind, width):
    if answer is None or answer["status"] == "unreadable":
        return None
    if answer["status"] == "empty":
        return "empty", (), ""
    value = answer["text"]
    if kind.startswith("vertical"):
        return "vertical", (), NORMALIZE(value)
    if value.startswith("H|"):
        return "horizontal", (), NORMALIZE(value[2:])
    fields = value.split("|")
    if len(fields) < 2 or fields[0] != "V":
        return None
    positions = {}
    for field in fields[1:]:
        token = re.fullmatch(r"(\d+):(.+)",field.strip())
        if not token:
            return None
        x, body = int(token[1]), NORMALIZE(token[2])
        if x in positions or not 0 <= x <= width or not body:
            return None
        positions[x] = body
    return "columns", tuple(sorted(positions, reverse=True)), "".join(positions[x] for x in sorted(positions, reverse=True))


def execute(args, manifest, images):
    if SHA(LOCK) != args.lock_sha256 or LOAD(LOCK) != manifest:
        raise ValueError("開発試験の固定が異なる")
    paths = {"gpt": args.codex, "claude": args.claude}
    runtime = {k: {"path":str(v.resolve()), "sha256":SHA(v.resolve()),
                   "version":subprocess.check_output([str(v.resolve()),"--version"]).decode("utf-8").strip(),
                   "reader_sha256":SHA(Path(readers.__file__))} for k,v in paths.items()}
    for name, assets in images.items():
        if any((OUT / "cards" / name / label).read_bytes() != b for label,b in assets.items()):
            raise ValueError("配布する開発画像が変化")
    readers.save_once(OUT / "started.json", readers.encoded({"lock_sha256":args.lock_sha256,"runtime":runtime}))
    with ThreadPoolExecutor(max_workers=6) as pool:
        working = {pool.submit(readers.read,runtime[role],role,model,pack["request"],OUT / "cards" / n,
                               OUT / "reads" / n / role):(n,role) for n, pack in manifest["packs"].items()
                   for role,model in MODELS.items()}
        votes = {working[task]:task.result() for task in as_completed(working)}
    sessions = [r.get("session") for r in votes.values() if r.get("session") is not None]
    if len(sessions) != len(set(sessions)):
        raise ValueError("読み手のセッションが重複")
    rows = LOAD(cards.SOURCE)["selected"]
    old = LOAD(cards.OUT / "reference-evidence.json")
    output, counts = {}, {}
    for name, pack in manifest["packs"].items():
        row, kind = rows[pack["entry"]], pack["kind"]
        ident, = pack["request"]["ids"]
        a,b = (decode(votes[name,role].get("answers",{}).get(ident),kind,row["box"][2]) for role in MODELS)
        ref = old[f"{row['key']}/{row['line_index']}"]["answer"]
        domain = "image" if kind.startswith("columns") else "region"
        target = NORMALIZE(row["targets"][domain]["text"])
        if a is None or b is None:
            outcome = "unresolved"
        elif a[0] != b[0] or a[2] != b[2] or len(a[1]) != len(b[1]) or any(abs(x-y)>4 for x,y in zip(a[1],b[1])):
            outcome = "disagree"
        elif a[2] == target:
            outcome = "agreed-existing-label"
        elif ref["status"] != "unreadable" and a[2] == NORMALIZE(ref["text"]):
            outcome = "agreed-earlier-reference"
        else:
            outcome = "agreed-new-difference"
        output[name] = {"key":row["key"],"line_index":row["line_index"],"kind":kind,"outcome":outcome,
                        "sessions":{role:{k:v for k,v in votes[name,role].items() if k!="answers"} for role in MODELS}}
        counts.setdefault(kind, Counter())[outcome] += 1
    readers.save_once(HERE / "result.json", readers.encoded({"lock_sha256":args.lock_sha256,"counts":counts,"rows":output}))
    print(json.dumps(counts,ensure_ascii=False), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("prepare","run"))
    cli.add_argument("--codex",type=Path)
    cli.add_argument("--claude",type=Path)
    cli.add_argument("--lock-sha256")
    args = cli.parse_args()
    manifest, images = material()
    if args.action == "prepare":
        if OUT.exists() or LOCK.exists():
            raise FileExistsError("開発試験を再固定しない")
        for name, assets in images.items():
            dst = OUT / "cards" / name
            dst.mkdir(parents=True)
            for f,b in assets.items():
                (dst/f).write_bytes(b)
        readers.save_once(LOCK, readers.encoded(manifest))
        print(SHA(LOCK),len(manifest["packs"]), "行", flush=True)
    else:
        execute(args, manifest, images)
