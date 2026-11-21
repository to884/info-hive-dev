"""二票の全文と位置を照合し、同形の記号だけを別の出典で補う。"""

from collections import Counter
import re

import numpy as np
from PIL import Image

from cards import HERE, OUT, CORPUS, PACKS, SOURCE, load, score, sha
from point_ink import groups
from readers import encoded, receive, save_once
from runner import START
from audit_selection_v9 import identity, summarize

MARK = re.compile(r"⟦(round|trail):([0-9]+)-([0-9]+)⟧")
LITERAL_POINT = re.compile(r"[•·∙…‥⋯]|[.・]{2,}|^・")
RECEIVED = HERE / "received.json"
REQUESTS = OUT / "source-requests.json"
PROOF = OUT / "source-commands.json"
UNKNOWN = {"status": "unreadable", "text": "?"}


def image_agreement():
    archived = load(RECEIVED)
    if archived["packages_sha256"] != sha(PACKS) or archived["delivery_sha256"] != sha(START):
        raise ValueError("受領と監査の配布が違う")
    runtime = load(START)["runtime"]
    packs, selection = load(PACKS), load(SOURCE)
    if packs["source_sha256"] != sha(SOURCE):
        raise ValueError("配布と抽出した対象が違う")
    cases = {}
    for name, item in packs["packs"].items():
        opinions = []
        for family, model in packs["models"].items():
            directory = OUT / "reads" / name / family
            stamp = archived["votes"][name][family]
            files = {p.name: sha(p) for p in directory.iterdir()} if directory.exists() else {}
            if files != stamp["files"]:
                raise ValueError("監査の原票が受領後に変化")
            reconstructed = receive(directory, family, model, item["request"], OUT / "cards" / name, runtime[family])
            if {k: v for k, v in reconstructed.items() if k != "answers"} != {k: v for k, v in stamp.items() if k != "files"}:
                raise ValueError("監査の原票と受領の結び付きが違う")
            opinions.append(reconstructed.get("answers", {}))
        for ident, mapping in item["mapping"].items():
            index = mapping["entry"]
            row = selection["selected"][index]
            if index in cases:
                raise ValueError("同じ監査行が複数の束にある")
            a, b = (by.get(ident, UNKNOWN) for by in opinions)
            pa, pb = score.audit.normalize(a["text"]), score.audit.normalize(b["text"])
            ma, mb = MARK.findall(pa), MARK.findall(pb)
            skeleton = lambda value: MARK.sub(lambda item: f"⟦{item.group(1)}⟧", value)
            same = (a["status"] == b["status"] != "unreadable" and skeleton(pa) == skeleton(pb)
                    and len(ma) == len(mb))
            coordinates = []
            if same and any(LITERAL_POINT.search(MARK.sub("", item["text"])) for item in (a, b)):
                same = False
            if same:
                for (left_shape, a1, b1), (right_shape, a2, b2) in zip(ma, mb, strict=True):
                    xa, xb, ya, yb = map(int, (a1, b1, a2, b2))
                    if (left_shape != right_shape or not 0 <= xa <= xb <= row["box"][2]
                            or not 0 <= ya <= yb <= row["box"][2] or abs(xa - ya) > 10 or abs(xb - yb) > 10
                            or (left_shape == "round" and (xa != xb or ya != yb))):
                        same = False
                        break
                    coordinates.append((xa, xb, ya, yb))
            cases[index] = {"answer": {"status": a["status"], "text": pa} if same else UNKNOWN,
                            "row": row, "assets": mapping["image_reference"],
                            "coordinates": coordinates}
    if set(cases) != set(range(len(selection["selected"]))):
        raise ValueError("監査の全行を確認できない")
    return cases, selection["summary"]


def prepare_source():
    cases, _ = image_agreement()
    pages = sorted({r["row"]["key"] for r in cases.values()
                    if r["answer"]["status"] == "readable" and MARK.search(r["answer"]["text"])})
    save_once(REQUESTS, encoded({"pages": pages}))
    print(sha(REQUESTS), len(pages), "頁の出典照合が必要", flush=True)


def source_for(shape, points, ops, flags, row_box=None):
    """実測した点の位置と、対応を説明できる一意の命令を結び付ける。"""
    origin = np.asarray(flags["150_origin"])
    transform = np.asarray(flags["150_matrix"])
    inverse = np.linalg.inv(transform)
    first = points[0]
    x, y = (first[0] + first[2]) / 2, (first[1] + first[3]) / 2
    output = []
    nearby = 0
    for op in ops:
        if op["text_rendering_mode"] in (3, 7):
            continue
        font = op["matrix"]
        px, py = transform @ (np.asarray(font[-2:]) - origin)
        font_width, font_height = np.abs(transform @ np.asarray([font[0], font[3]]))
        if abs(font[1]) > 1e-5 or abs(font[2]) > 1e-5:
            continue
        em_x, em_y = font_width * op["font_size"], font_height * op["font_size"]
        if not 5 <= em_x <= 100 or not 5 <= em_y <= 100 or not -.64 * em_y <= y - py <= .08 * em_y:
            continue
        # 描画命令は小数、固定枠は整数画素なので境界の半画素だけ認める。
        if row_box is not None and not row_box[1] - .5 <= py < row_box[1] + row_box[3] + .5:
            continue
        if not -2 <= x - px <= (1.35 if shape == "trail" else .75) * em_x:
            continue
        nearby += 1
        if not op["visible_fill_proven"]:
            continue
        if op["clips"]:
            corners = [origin + inverse @ np.asarray(p) for a, b, c, d in points for p in ((a, b), (a, d), (c, b), (c, d))]
            if any(not (l <= p[0] <= r and t <= p[1] <= b) for l, t, r, b in op["clips"] for p in corners):
                continue
        explicit = op["explicit_point_codepoints"]
        entry = None
        if (shape == "trail" and len(points) == 3 * op["ellipsis_cid_668"]
                and op["collection"] == ["Adobe", "Japan1"] and op["leading_cid"] == 1 and not explicit):
            entry = ("2026", op["ellipsis_cid_668"])
        elif (shape == "trail" and explicit == {"30FB": len(points)}
              and (op["leading_explicit_unicode"] == "30FB" or op["leading_cid"] == 1)):
            entry = ("30FB", len(points))
        elif shape == "round" and op["leading_explicit_unicode"] in ("2022", "30FB") and explicit == {op["leading_explicit_unicode"]: 1}:
            entry = (op["leading_explicit_unicode"], 1)
        if entry is None:
            continue
        anchors = op["positioned_points"]
        if not anchors or len(anchors) != entry[1]:
            continue
        if op["collection"] == ["Adobe", "Japan1"]:
            registered = {638: "30FB", 668: "2026"}
            if any(cid in registered and code not in (None, "FFFD", registered[cid]) for cid, code, _, _ in anchors):
                continue
        divisions = 3 if entry[0] == "2026" else 1
        if any((cid != 668 or code not in (None, "FFFD", "2026")) if divisions == 3 else (code != entry[0])
               for cid, code, _, _ in anchors):
            continue
        nominal = [font_width * (before + width * j / divisions)
                   for _, _, before, width in anchors for j in range(divisions)]
        physical = [(a + c) / 2 for a, _, c, _ in points]
        slack = physical[0] - px - nominal[0]
        if (not -2 <= slack <= font_width * anchors[0][3] / divisions + 2
                or any(abs((p - physical[0]) - (q - nominal[0])) > 2.0
                       for p, q in zip(physical, nominal, strict=True))):
            continue
        output.append((entry, op, px, py))
    return output[0] if nearby == 1 and len(output) == 1 else None


def resolved(case, proof):
    answer, row = case["answer"], case["row"]
    if answer["status"] != "readable":
        return answer, "plain-unresolved" if answer["status"] == "unreadable" else "image-empty"
    phrase = answer["text"]
    markers = list(MARK.finditer(phrase))
    if LITERAL_POINT.search(MARK.sub("", phrase)):
        return UNKNOWN, "possible-point-without-position"
    if not markers:
        return (UNKNOWN, "invalid-marker") if "⟦" in phrase or "⟧" in phrase else (answer, "image-only")
    if "⟦" in MARK.sub("", phrase) or "⟧" in MARK.sub("", phrase) or row["allocation_axis"] != "x":
        return UNKNOWN, "unsupported-mark-reference"
    flags = case["assets"]["sha"]
    pdf = proof["evidence"].get(row["key"])
    if not pdf or pdf["pdf_sha256"] != flags["pdf_sha256"] or "unsupported" in pdf:
        return UNKNOWN, "source-unavailable"
    png = CORPUS / "probe-v4/png" / (row["key"] + ".png")
    if sha(png) != flags["150_dpi"]:
        raise ValueError("補助の画素と監査で固定した150 DPIが違う")
    with Image.open(png) as image:
        zones = groups(np.asarray(image.convert("L")), row["box"])
    result, evidence, used_points = [], [], set()
    offset = 0
    if len(markers) != len(case["coordinates"]):
        return UNKNOWN, "missing-point-coordinates"
    for mark, (start_a, stop_a, start_b, stop_b) in zip(markers, case["coordinates"], strict=True):
        shape = mark.group(1)
        selected = []
        for dots in zones.get(shape, []):
            first = (dots[0][0] + dots[0][2]) / 2 - row["box"][0]
            last = (dots[-1][0] + dots[-1][2]) / 2 - row["box"][0]
            if max(abs(first - start_a), abs(first - start_b), abs(last - stop_a), abs(last - stop_b)) > 10:
                continue
            if set(dots) & used_points:
                continue
            match = source_for(shape, dots, pdf["commands"], flags, row["box"])
            if match:
                selected.append((dots, match))
        if len(selected) != 1:
            return UNKNOWN, "source-location-not-proven"
        dots, ((codepoint, n), op, x, y) = selected[0]
        used_points.update(dots)
        result.extend((phrase[offset:mark.start()], chr(int(codepoint, 16)) * n))
        offset = mark.end()
        evidence.append({"codepoint": codepoint, "physical_points": len(dots), "bounds": dots,
                         "source_origin_px": [float(x), float(y)], "source": op})
    result.append(phrase[offset:])
    value = {"status": "readable", "text": score.audit.normalize("".join(result))}
    return value, {"source-confirmed": evidence}


def collect():
    destination = HERE / "result.json"
    if destination.exists():
        raise FileExistsError("監査結果を上書きしない")
    proof = load(PROOF)
    if proof["request_sha256"] != sha(REQUESTS) or proof["scope"] != "independent-audit-pdf-drawing-commands":
        raise ValueError("出典を別に読んだ正式な記録が違う")
    p = HERE.parent / "dot-layout-v2"
    expected_methods = {src.name: sha(src) for src in (HERE / "source_commands.py", p / "independent-pdf-commands.py")}
    requested = set(load(REQUESTS)["pages"])
    if (proof["methods"] != expected_methods or proof["pypdf"] != "6.21.0"
            or proof["table"]["sha256"] != load(p / "independent-pdf-commands-v2.json")["adobe"]["sha256"]
            or set(proof["evidence"]) != requested):
        raise ValueError("出典の取得方法、一次表または対象が異なる")
    cases, summary = image_agreement()
    rows, references, states, attached = [], {}, Counter(), {}
    for item in cases.values():
        row = item["row"]
        ident = identity(row)
        value, state = resolved(item, proof)
        states["source-confirmed" if isinstance(state, dict) else state] += 1
        rows.append(row)
        references[ident] = value
        attached[row["key"] + "/" + str(row["line_index"])] = {"answer": value, "evidence": state}
    result = summarize(rows, summary, references)
    archive = OUT / "reference-evidence.json"
    save_once(archive, encoded(attached))
    overlap = {domain: {name: sum(bool(r[name]) for r in rows if domain in r["targets"])
                        for name in ("development_intake", "previously_audited")} for domain in ("region", "image")}
    save_once(destination, encoded({"scope": "independent-audit-once", "summary": result,
                                    "all_quality_checks_pass": all(v["status"] == "pass" for v in result.values()),
                                    "overlap": overlap, "reference_sources": states, "receipts_sha256": sha(RECEIVED),
                                    "source_sha256": sha(PROOF), "detailed_reference_sha256": sha(archive)}))
    print({k: v["status"] for k, v in result.items()}, dict(states), flush=True)


if __name__ == "__main__":
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("source-requests", "collect"))
    args = cli.parse_args()
    if args.action == "source-requests":
        prepare_source()
    else:
        collect()
