"""二系統の原票から全文と点の位置を照合し、二つの監査を集計する。"""

import argparse
from collections import Counter
import re
from pathlib import Path

import numpy as np
from PIL import Image

from packets import HERE, OUT, load, module, old, sha
from readers import encoded, receive, save_once

v10 = module("v10_audit_resolver", HERE.parent / "v10-reference-audit/resolve.py")
SOURCE_TOOL = HERE / "source.py"
FONT_WIDTH = HERE.parent / "v11-visible-source-pilot/commands.py"
INK_TOOL = HERE.parent / "v11-visible-source-pilot/round_overlap.py"
small_round = module("round_visible_limits", INK_TOOL).marks
MARK, UNKNOWN = v10.MARK, v10.UNKNOWN
DELIVERY = OUT / "delivery"
READ, PACKS = DELIVERY / "received.json", DELIVERY / "packages.json"
START, REQUESTS = DELIVERY / "delivery-started.json", OUT / "source-requests.json"
PROOF = OUT / "source-commands.json"
NORMALIZE = v10.score.audit.normalize


def decoded(answer, partitions):
    if answer["status"] != "readable":
        return answer
    text = answer["text"]
    if not text.startswith("V|"):
        return {"status": "readable", "text": NORMALIZE(text)}
    parts = {}
    for term in text.split("|")[1:]:
        found = re.fullmatch(r"([A-I]):(.*)", term.strip())
        if found is None or found[1] in parts:
            return UNKNOWN
        parts[found[1]] = found[2]
    if not parts or parts.keys() != set(partitions):
        return UNKNOWN
    decoded = NORMALIZE("".join(parts[k] for k in reversed(partitions)))
    return {"status": "readable", "text": decoded} if decoded else UNKNOWN


def aligned(a, b, width):
    first, second = a["text"], b["text"]
    if a["status"] == b["status"] == "empty":
        return a, []
    if a["status"] != "readable" or b["status"] != "readable":
        return UNKNOWN, []
    token = lambda m: f"⟦{m.group(1)}⟧"
    if MARK.sub(token, first) != MARK.sub(token, second):
        return UNKNOWN, []
    if any(re.search(r"[⟦⟧]", rest) or v10.LITERAL_POINT.search(rest)
           for rest in (MARK.sub("", s) for s in (first, second))):
        return UNKNOWN, []
    first_hits, second_hits = MARK.findall(first), MARK.findall(second)
    if len(first_hits) != len(second_hits):
        return UNKNOWN, []
    positions = []
    for (a_kind, a1, a2), (b_kind, b1, b2) in zip(first_hits, second_hits):
        xa, xb, ya, yb = map(int, (a1, a2, b1, b2))
        if not (a_kind == b_kind and 0 <= xa <= xb <= width and 0 <= ya <= yb <= width
                and max(abs(xa - ya), abs(xb - yb)) <= 10):
            return UNKNOWN, []
        if a_kind == "round" and (xa != xb or ya != yb):
            return UNKNOWN, []
        positions.append((xa, xb, ya, yb))
    return a, positions


def png_checked(row, flags):
    path = old.CORPUS / "probe-v4/png" / (row["key"] + ".png")
    if sha(path) != flags["150_dpi"]:
        raise ValueError("点の所属と固定した描画画素が異なる")
    with Image.open(path) as image:
        return np.array(image.convert("L"))


def unverified_round(answer, row, flags, positions):
    if answer["status"] != "readable" or row["allocation_axis"] != "x":
        return False
    # 本文の先頭に印があっても、測定した丸と両票の位置が合わなければ保留する。
    first = MARK.match(answer["text"])
    left, top, width, height = row["box"]
    gray = png_checked(row, flags)
    for l, t, r, b in small_round(gray, (left, top, min(width, 24), height)):
        center = (l + r) / 2 - left
        if 9 <= max(r - l, b - t) <= 10 and abs(center) <= 12:
            placed = first and first[1] == "round" and positions and all(abs(center - n) <= 10 for n in positions[0])
            if not placed:
                return True
    return False


def cases():
    shipment, received, started = load(PACKS), load(READ), load(START)
    source = OUT / "selection.json"
    if (received["packages_sha256"] != sha(PACKS) or received["delivery_sha256"] != sha(START)
            or started["packages_sha256"] != sha(PACKS) or shipment["source_sha256"] != sha(source)
            or any(sha(Path(p)) != h for p, h in shipment["inputs"].items())):
        raise ValueError("固定した母集団・配布・受領のつながりが異なる")
    launches = {p.relative_to(DELIVERY).as_posix(): sha(p) for p in (DELIVERY / "launches").glob("*/*.json")}
    if received["launches"] != launches or len(launches) != 2 * len(shipment["packs"]):
        raise ValueError("正式に照合した着手記録が異なる")
    selected = load(source)
    rows = selected["selected"]
    items = {}
    sessions = set()
    for name, value in shipment["packs"].items():
        ballots = []
        for family, model in shipment["models"].items():
            target = DELIVERY / "reads" / name / family
            saved = received["votes"][name][family]
            files = {p.name: sha(p) for p in target.iterdir()} if target.exists() else {}
            if files != saved["files"]:
                raise ValueError("保存した原票が受領後に変化")
            proof = receive(target, family, model, value["request"], DELIVERY / "cards" / name, started["runtime"][family])
            if {k: v for k, v in proof.items() if k != "answers"} != {k: v for k, v in saved.items() if k != "files"}:
                raise ValueError("受領の内容を再現できない")
            if (session := proof.get("session")) is not None:
                if session in sessions:
                    raise ValueError("同じ読み手のセッションが二票にある")
                sessions.add(session)
            ballots.append(proof.get("answers", {}))
        for ident, mapping in value["mapping"].items():
            index = mapping["entry"]
            if index in items:
                raise ValueError("正式な行が二度配布された")
            row = rows[index]
            answer, positions = aligned(*(decoded(v.get(ident, UNKNOWN), mapping["partitions"]) for v in ballots), row["box"][2])
            assets = mapping["image_reference"]
            reason = "plain-unresolved"
            if unverified_round(answer, row, assets["sha"], positions):
                answer, reason = UNKNOWN, "unverified-small-round"
            items[index] = {"row": row, "answer": answer, "coordinates": positions, "assets": assets, "reason": reason}
    if set(items) != set(range(len(rows))) or len(sessions) != received["unique_sessions"]:
        raise ValueError("独立した受領の全行を確認できない")
    return list(items.values()), selected["summary"]


def prepare_source():
    todo, _ = cases()
    pages = sorted({c["row"]["key"] for c in todo if MARK.search(c["answer"]["text"])})
    save_once(REQUESTS, encoded({"pages": pages}))
    print(sha(REQUESTS), len(pages), "頁の出典を独立に照合", flush=True)


def checked_source(proof, request_path):
    old_source = HERE.parent / "v10-reference-audit/source_commands.py"
    original = HERE.parent / "dot-layout-v2/independent-pdf-commands.py"
    original_table = load(original.with_name("independent-pdf-commands-v2.json"))["adobe"]
    if (proof["request_sha256"] != sha(request_path) or proof["scope"] != "independent-audit-pdf-drawing-commands"
            or proof["table"]["sha256"] != original_table["sha256"] or proof["pypdf"] != "6.21.0"
            or proof["methods"] != {f.name: sha(f) for f in (SOURCE_TOOL, FONT_WIDTH, old_source, original)}
            or set(proof["evidence"]) != set(load(request_path)["pages"])):
        raise ValueError("出典を独立に取得した方法、原本または対象が異なる")


def collect():
    destination = HERE / "result.json"
    if destination.exists():
        raise FileExistsError("確定した監査を上書きしない")
    proof = load(PROOF)
    checked_source(proof, REQUESTS)
    entries, pre = cases()
    references, counts, attached = {}, Counter(), {}
    rows = [c["row"] for c in entries]
    for case in entries:
        row = case["row"]
        ident = v10.identity(row)
        answer, kind = v10.resolved(case, proof)
        if kind == "plain-unresolved":
            kind = case["reason"]
        references[ident] = answer
        counts["source-confirmed" if isinstance(kind, dict) else kind] += 1
        attached[f"{row['key']}/{row['line_index']}"] = {"answer": answer, "evidence": kind}
    result = v10.summarize(rows, pre, references)
    details = OUT / "reference-evidence.json"
    save_once(details, encoded(attached))
    overlap = {domain: {name: sum(bool(r[name]) for r in rows if domain in r["targets"])
                        for name in ("development_intake", "previously_audited")} for domain in result}
    save_once(destination, encoded({"scope": "independent-audit-once", "summary": result, "overlap": overlap,
                                    "all_quality_checks_pass": all(r["status"] == "pass" for r in result.values()),
                                    "sources": counts, "receipts_sha256": sha(READ), "source_sha256": sha(PROOF),
                                    "reference_sha256": sha(details)}))
    print({k: r["status"] for k, r in result.items()}, dict(counts), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("source-requests", "collect"))
    args = cli.parse_args()
    if args.action == "source-requests":
        prepare_source()
    else:
        collect()
