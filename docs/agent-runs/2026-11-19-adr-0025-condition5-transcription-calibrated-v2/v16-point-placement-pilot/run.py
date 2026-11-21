"""行頭と行中の小さな点を、保存した独立の二票と隔離描画で照合する。"""

import importlib.util
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
TRIAL = HERE.parent / "v12-readable-regions-pilot"
VISUAL = HERE.parent / "v11-visible-source-pilot"
sys.path[:0] = [str(VISUAL), str(HERE.parent / "v10-reference-audit")]
import isolate_round as isolation
from point_ink import groups
import resolve

load, sha, corpus = resolve.load, resolve.sha, resolve.CORPUS
TARGET = "disaster-p0162", 48
OUT = corpus / "reference-v16-point-placement-pilot"


def image_ballots():
    private = corpus / "reference-v12-readable-regions-pilot"
    initial, receipt, lock = load(private / "started.json"), load(TRIAL / "result.json"), load(TRIAL / "lock.json")
    if {initial["lock_sha256"], receipt["lock_sha256"]} != {sha(TRIAL / "lock.json")}:
        raise ValueError("開発の画像と受領の固定が異なる")
    name, case = next((k, v) for k, v in receipt["rows"].items() if (v["key"], v["line_index"]) == TARGET)
    config = lock["packs"][name]
    request = config["request"]
    ident, = request["ids"]
    reads = {}
    for role, model in lock["models"].items():
        answer = resolve.receive(private / "reads" / name / role, role, model, request, private / "cards" / name,
                                 initial["runtime"][role])
        if {k: v for k, v in answer.items() if k != "answers"} != case["receipts"][role]:
            raise ValueError("保存票を再現できない")
        row = answer["answers"][ident]
        if row["status"] != "readable":
            raise ValueError("周囲の本文を二系統から得られない")
        reads[role] = resolve.score.audit.normalize(row["text"])
    a, b = reads.values()
    shape = lambda m: f"⟦{m.group(1)}⟧"
    if resolve.MARK.sub(shape, a) != resolve.MARK.sub(shape, b):
        raise ValueError("本文と点の形が二票で割れた")
    found = []
    for l, r in zip(resolve.MARK.findall(a), resolve.MARK.findall(b), strict=True):
        if l[0] != r[0] or l[0] != "round":
            raise ValueError("丸印と判断した二票がそろわない")
        xx = [int(x) for x in (*l[1:], *r[1:])]
        if max(xx) - min(xx) > 10 or xx[0] != xx[1] or xx[2] != xx[3]:
            raise ValueError("点を置いた位置が一致しない")
        found.append(xx)
    if len(found) != 2:
        raise ValueError("行頭と行中の2点がそろわない")
    entry = config["entry"]
    row = load(resolve.SOURCE)["selected"][entry]
    if (row["key"], row["line_index"]) != TARGET:
        raise ValueError("開発で対象にした行が異なる")
    return a, found, row


def glyphs(chosen, flags, box):
    origin, trans = np.asarray(flags["150_origin"]), np.asarray(flags["150_matrix"])
    l, t, r, b = box
    x, y = (l + r) / 2, (t + b) / 2
    possibilities = set()
    for op in chosen:
        if not op["visible_fill_proven"]:
            continue
        frame = op["matrix"]
        if abs(frame[1]) > 1e-5 or abs(frame[2]) > 1e-5:
            continue
        px, py = trans @ (np.asarray(frame[-2:]) - origin)
        fx, fy = np.abs(trans @ np.asarray([frame[0], frame[3]]))
        if not -.64 * fy * op["font_size"] <= y - py <= .08 * fy * op["font_size"]:
            continue
        for cid, code, offset, width in op["positioned_points"]:
            if -1 <= x - px - fx * offset <= fx * width + 1:
                if code not in {"2022", "30FB"} or (op["collection"] == ["Adobe", "Japan1"] and cid == 638 and code != "30FB"):
                    raise ValueError("許可した丸印の符号と対応しない")
                possibilities.add((op["font"], op["embedded_sha256"], tuple(op["collection"]), cid, code))
    only, = possibilities
    return only


def isolate(source, number, box, fixed, flags):
    l, t, r, b = box
    window = np.s_[t - 1:b + 1, l - 1:r + 1]
    full_pdf, operators = isolation.rewrite(source, number)
    target = fixed[window]
    if not np.array_equal(isolation.layer.render_pixels(full_pdf, 0)[window], target):
        raise ValueError("隔離前の開発PDFで固定画素を再現できない")
    blank_pdf, _ = isolation.rewrite(source, number, set())
    blank = isolation.layer.render_pixels(blank_pdf, 0)[window]
    if np.min(blank) < 254:
        raise ValueError("点と同じ場所に文字以外の描画がある")

    def render(selected):
        subset, seen = isolation.rewrite(source, number, set(selected))
        if operators != seen:
            raise ValueError("描画命令が変化")
        return subset, isolation.layer.render_pixels(subset, 0)[window]

    pending = [operators]
    contributors = []
    while pending:
        batch = pending.pop()
        if np.array_equal(render(batch)[1], blank):
            continue
        if len(batch) == 1:
            contributors.append(batch[0])
        else:
            n = len(batch) // 2
            pending.extend((batch[:n], batch[n:]))
    positive, pixels = render(contributors)
    _, negative = render(set(operators) - set(contributors))
    if not np.array_equal(pixels, target) or not np.array_equal(negative, blank):
        raise ValueError("選んだ命令だけで点を再現できない")
    font, font_sha, collection, cid, code = glyphs(isolation.painted_points(positive), flags, box)
    return {"codepoint": code, "cid": cid, "font": font, "to_unicode_sha256": font_sha, "collection": collection,
            "box": box, "operators": contributors, "fixed_window_sha256": isolation.layer.sha(target.tobytes()),
            "isolation_sha256": isolation.layer.sha(positive), "others_have_no_ink": True}


def main():
    model_text, positions, row = image_ballots()
    key, line = TARGET
    flags = load(resolve.PACKS)["sources"][key]
    catalog = isolation.commands.old.raw
    cand = next(load(path) for path in (corpus / "public").glob("*.truth.json") if load(path)["name"] == "disaster")
    assert any(f"{cand['name']}-p{r['page']:04d}" == key for r in cand["pages"])
    data = (corpus / cand["file"]).read_bytes()
    png = corpus / "probe-v4/png" / (key + ".png")
    if catalog.sha(data) != flags["pdf_sha256"] or sha(png) != flags["150_dpi"]:
        raise ValueError("固定PDFとPNGが異なる")
    with Image.open(png) as image:
        fixed = np.array(image.convert("RGB"))
        gray = np.array(image.convert("L"))
    page = int(key.rsplit("-p", 1)[1])
    bounds = [b[0] for b in groups(gray, row["box"]).get("round", [])]
    selected = []
    for readings in positions:
        box, = (b for b in bounds if max(abs((b[0] + b[2]) / 2 - row["box"][0] - x) for x in readings) <= 10)
        selected.append(box)
    if not np.array_equal(isolation.layer.render_pixels(data, page - 1), fixed) or len(set(selected)) != 2:
        raise ValueError("元PDFの固定画素か、点の重複の検査に失敗")
    evidence = [isolate(data, page, box, fixed, flags) for box in selected]
    markers = iter(evidence)
    answer = resolve.MARK.sub(lambda _: chr(int(next(markers)["codepoint"], 16)), model_text)
    expected = resolve.score.audit.normalize(row["targets"]["region"]["text"])
    OUT.mkdir()
    record = {"scope": "development-only", "page": key, "line_index": line,
              "same_as_existing_label": answer == expected, "evidence": evidence,
              "fixed_pdf_sha256": flags["pdf_sha256"], "fixed_150_sha256": flags["150_dpi"]}
    resolve.save_once(OUT / "result.json", resolve.encoded(record))
    print([r["codepoint"] for r in evidence], "既存正解と一致:", record["same_as_existing_label"], flush=True)


if __name__ == "__main__":
    main()
