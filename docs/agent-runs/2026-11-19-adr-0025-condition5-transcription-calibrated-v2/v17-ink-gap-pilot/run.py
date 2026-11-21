"""固定150/450 DPIの空白で区切った開発行を新規セッションで照合する。"""

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import io
import json
from pathlib import Path
import re
import sys

from PIL import Image, ImageFont

from ballot import entries, session_and_response
from geometry import clear_at_high_resolution, positions, segment_cards

HERE = Path(__file__).resolve().parent
STRUCTURED = HERE.parent / "v16-structured-readers-pilot/run.py"
OLD_TRIAL = HERE.parent / "v13-layout-generalization"
sys.path.insert(0, str(HERE.parent / "v10-reference-audit"))
import cards
import resolve

spec = importlib.util.spec_from_file_location("structured_reader", STRUCTURED)
structured = importlib.util.module_from_spec(spec)
spec.loader.exec_module(structured)

OUT = cards.CORPUS / "reference-v17-ink-gap-pilot"
OLD_OUT = cards.CORPUS / "reference-v13-layout-generalization"
LOCK = HERE / "lock.json"
readers, MODELS = structured.readers, structured.MODELS
load, sha, normalize = cards.load, cards.sha, resolve.score.audit.normalize
GUIDE = (
    "区画の追加画像は、文字が写っていない空白で分けました。元の枠に所属する字を先に確かめます。"
    "450 DPIの細部では、同じ字に見えても起筆や折れ、画の本数を見て、単語や番号として自然な形に修正しません。"
    "各区画の赤枠に所属する字を、元の行の自然な順に、そのまま転記します。隣の字の画を重ねて写しません。"
    "textを S|A:甲乙|B:丙丁 の形式にし、全区画を各一度含めます。空欄は A:、行を読めないときはunreadableです。"
)
H_POINT = (
    "形から符号を区別できない小さい丸い印は、中黒に見える場合も、行頭・行中で ⟦round:X-X⟧ と書きます。"
    "同様に字の区切りが分からない点の列は ⟦trail:X-Y⟧ にします。X、Yは元の行の150 DPI横座標で、5画素刻みの目盛りを使います。"
    "大きな黒丸など字形が明らかな符号をそのまま写します。"
)


def sheets(pictures, ident):
    """画像を縮めずに隣り合う最大三つの区画を一枚に置く。"""
    parts = [Image.open(io.BytesIO(pic)).convert("RGB") for pic in pictures.values()]
    panels = {}
    for n, batch in enumerate((parts[i:i + 3] for i in range(0, len(parts), 3)), 1):
        target = Image.new("RGB", (max(im.width for im in batch), sum(im.height for im in batch) + 8), "white")
        edge = 0
        for im in batch:
            target.paste(im, (0, edge))
            edge += im.height + 8
        buf = io.BytesIO()
        target.save(buf, "PNG")
        panels[f"{ident}-parts-{n:02d}.png"] = buf.getvalue()
    return panels


def material():
    origin = load(cards.PACKS)
    selected = load(cards.SOURCE)["selected"]
    refs = {a["entry"]: a["image_reference"] for v in origin["packs"].values() for a in v["mapping"].values()}
    past, receipts = load(OLD_TRIAL / "lock.json"), load(OLD_TRIAL / "result.json")
    if receipts["lock_sha256"] != sha(OLD_TRIAL / "lock.json"):
        raise ValueError("前回の開発試験と結果が異なる")
    finger = cards.base.FONTS / "meiryo.ttc"
    font = ImageFont.truetype(finger, size=17)
    specs, visuals = {}, {}
    for name, prior in past["packs"].items():
        i, req = prior["entry"], prior["request"]
        row, ref = selected[i], refs[i]
        if any(not t["known"] for t in row["targets"].values()):
            continue
        axis = row["allocation_axis"]
        image = cards.CORPUS / "probe-v4/png" / (row["key"] + ".png")
        if sha(image) != ref["sha"]["150_dpi"]:
            raise ValueError("固定150 DPIが違う")
        with Image.open(image) as low:
            bounds = positions(low, row["box"], axis)
        if not bounds:
            continue
        view = ref["source_view"]["views"][1]
        high_name = next(p["image"] for p in view["images"] if p["kind"] == "plain")
        high_path = cards.OUT / "source-assets" / high_name
        if sha(high_path) != origin["source_assets"][high_name]:
            raise ValueError("固定450 DPIの確認画像と異なる")
        ident, = req["ids"]
        labels = [chr(ord("A") + n) for n in range(len(bounds) - 1)]
        with Image.open(high_path) as high:
            rect = view["target_rectangle"]
            if not clear_at_high_resolution(high, rect, bounds, axis):
                continue
            details = sheets(segment_cards(high, rect, bounds, axis, labels, font), ident)
        images = {}
        for file, digest in zip(req["images"], req["image_sha256"], strict=True):
            data = (OLD_OUT / "cards" / name / file).read_bytes()
            if readers.sha(data) != digest:
                raise ValueError("以前の開発画像が変化")
            if len(req["images"]) + len(details) > 24 and "-extra-" in file:
                continue
            images[file] = data
        images.update(details)
        if len(images) > 24:
            raise ValueError("束の画像数が上限を超えた")
        parts = "、".join(labels)
        prompt = (
            "150 DPIで元の枠への所属、450 DPIで字形を確かめ、割当の軸と枠は元の表示のまま使ってください。"
            "文字を資料の意味から補わず、所属する字は全て転記します。" + GUIDE + (H_POINT if axis == "x" else "") +
            f"対象IDは {ident}、区画は {parts}。JSONだけを返します。形式は " +
            '{"answers":[{"id":"対象ID","status":"readable","text":"転記"}]}。判読できなければunreadable、textは?です。'
        )
        specs[name] = {"entry": i, "axis": axis, "parts": labels, "bounds": bounds,
                       "prior_outcome": receipts["rows"][name]["outcome"],
                       "request": {"ids": [ident], "images": list(images), "image_sha256": [readers.sha(x) for x in images.values()],
                                   "prompt": prompt}}
        visuals[name] = images
    pins = (Path(__file__), HERE / "ballot.py", HERE / "geometry.py", HERE / "protocol.md",
            STRUCTURED, OLD_TRIAL / "lock.json", OLD_TRIAL / "result.json", cards.PACKS, cards.SOURCE, finger)
    return {"inputs": {str(k): sha(k) for k in pins}, "packs": specs}, visuals


def translated(answers, ident, labels):
    item = answers[ident]
    if item["status"] != "readable":
        return item
    pane = item["text"].split("|")
    if not pane or pane[0] != "S":
        return resolve.UNKNOWN
    sections = {}
    for field in pane[1:]:
        token = re.fullmatch(r"([A-Z]):(.*)", field.strip())
        if token is None or token[1] in sections:
            return resolve.UNKNOWN
        sections[token[1]] = token[2]
    if set(sections) != set(labels):
        return resolve.UNKNOWN
    text = normalize("".join(sections[label] for label in labels))
    return {"status": "readable", "text": text} if text else resolve.UNKNOWN


def collect(plan):
    original = load(cards.SOURCE)["selected"]
    report, counts, sessions = {}, defaultdict(Counter), set()
    for name, entry in plan["packs"].items():
        req = entry["request"]
        ident, = req["ids"]
        paired = []
        for role, model in MODELS.items():
            root = OUT / "reads" / name / role
            raw = (root / "response.jsonl").read_bytes()
            recorded = load(root / "process.json")
            if recorded["response_sha256"] != readers.sha(raw) or recorded["returncode"]:
                paired.append(resolve.UNKNOWN)
                continue
            events = [json.loads(line, object_pairs_hook=readers.json_pairs) for line in raw.splitlines() if line.strip()]
            last = (root / "last-message.json").read_text(encoding="utf-8") if role == "gpt" else None
            session, data = session_and_response(events, role, model, last)
            if session in sessions:
                raise ValueError("独立した新しい会話が重複")
            sessions.add(session)
            paired.append(translated(entries(data, req["ids"]), ident, entry["parts"]))
        row = original[entry["entry"]]
        a, b = paired
        reference = {normalize(r["text"]) for r in row["targets"].values()}
        found = lambda text: resolve.MARK.sub(lambda m: f"⟦{m[1]}⟧", text)
        if a["status"] == "unreadable" or b["status"] == "unreadable" or found(a["text"]) != found(b["text"]):
            outcome = "unresolved"
        elif resolve.MARK.search(a["text"]):
            matches = zip(resolve.MARK.findall(a["text"]), resolve.MARK.findall(b["text"]), strict=True)
            close = all(u[0] == v[0] and max(abs(int(u[1]) - int(v[1])), abs(int(u[2]) - int(v[2]))) <= 10
                        for u, v in matches)
            outcome = "point-needs-proof" if close else "unresolved"
        elif {a["text"]} == reference:
            outcome = "agreed-existing-label"
        else:
            outcome = "agreed-different-label"
        report[name] = {"key": row["key"], "line_index": row["line_index"], "prior": entry["prior_outcome"], "outcome": outcome}
        counts[entry["prior_outcome"]][outcome] += 1
    readers.save_once(HERE / "result.json", readers.encoded({"scope": "development-only", "lock_sha256": sha(LOCK),
                                                              "counts": counts, "rows": report}))
    print(dict(counts), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "run"))
    p.add_argument("--sha256")
    p.add_argument("--codex", type=Path)
    p.add_argument("--claude", type=Path)
    args = p.parse_args()
    plan, images = material()
    if args.action == "prepare":
        OUT.mkdir()
        for name, files in images.items():
            folder = OUT / "cards" / name
            folder.mkdir(parents=True)
            for label, blob in files.items():
                readers.save_once(folder / label, blob)
        readers.save_once(LOCK, readers.encoded(plan))
        print(sha(LOCK), len(images), "行", flush=True)
        return
    if sha(LOCK) != args.sha256 or load(LOCK) != plan:
        raise ValueError("事前に固定した開発画像と違う")
    executables = {"gpt": args.codex.resolve(strict=True), "claude": args.claude.resolve(strict=True)}
    readers.save_once(OUT / "started.json", readers.encoded({"lock_sha256": sha(LOCK)}))
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(structured.read, role, model, executables[role], pack["request"], OUT / "cards" / name,
                            OUT / "reads" / name / role)
                for name, pack in plan["packs"].items() for role, model in MODELS.items()]
        for job in jobs:
            job.result()
    collect(plan)


if __name__ == "__main__":
    main()
