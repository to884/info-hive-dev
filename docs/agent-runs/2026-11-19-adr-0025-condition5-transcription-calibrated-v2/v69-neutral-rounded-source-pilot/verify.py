"""画像の二票が合意した一点に限り、元の縦組の描画命令を照らす。"""

from pathlib import Path

from pypdf.errors import PdfReadError


def collect(core, private, work, lock, branches, inputs):
    plan = core.load(lock)
    archive = core.load(work / "comparison.json")
    if (archive["lock_sha256"] != core.sha(lock) or set(archive["cases"]) != set(plan["jobs"])
            or any(core.sha(Path(p)) != h for p, h in plan["files"].items())):
        raise ValueError("事前固定した照合と新規の画像票を結べない")
    delivery = private / "display/new/delivery"
    asset_hashes = core.load(delivery / "packages.json")["source_assets"]
    rows = core.load(private / "display/selection.json")["selected"]
    catalog = core.previous.packets.old.lookup()[1]
    outcomes = {}
    for name, case in archive["cases"].items():
        row_info = plan["mapping"][name.split("/")[0]]["arms"]["new"]
        row, answer, places = rows[row_info["entry"]], case["answers"]["pair"], case["coordinates"]
        key, line = row["key"], row["line_index"]
        result = {"page": key, "line_index": line, "image": case["outcomes"]["pair"]}
        outcomes[name] = result
        kinds = core.ref.MARK.findall(answer["text"])
        if len(kinds) != 1 or kinds[0][0] != "round" or len(places) != 1:
            result["source"] = "no-aligned-ambiguous-round"
            continue
        assets = row_info["image_reference"]
        high = assets["source_view"]["views"][1]
        small = next(i["image"] for i in high["images"] if i["kind"] == "plain")
        hi = delivery / "source-assets" / small
        low = core.CORPUS / "probe-v4/png" / (key + ".png")
        relative, expected, page = catalog[key]
        pdf = (core.CORPUS / relative).read_bytes()
        if (core.sha(hi) != asset_hashes[small] or core.sha(low) != assets["sha"]["150_dpi"]
                or branches.trace.sha(pdf) != expected or expected != assets["sha"]["pdf_sha256"]):
            raise ValueError("PDFまたは固定画像の来歴が異なる")
        item = {"row": row, "assets": assets, "answer": answer, "coordinates": places}
        try:
            checked = branches.prove(item, hi, asset_hashes[small], low, pdf, expected, page)
        except (PdfReadError, ValueError, KeyError, IndexError, TypeError, AttributeError, OverflowError) as error:
            result.update(source="unresolved-source", reason=type(error).__name__, detail=str(error))
            continue
        if checked:
            observed, proof = checked
            result.update(source="confirmed", text=observed["text"], evidence=proof)
        else:
            result["source"] = "unresolved-source"
    files = (*inputs, work / "comparison.json", delivery / "packages.json", lock)
    core.save_once(work / "source-result.json", core.encoded({"scope": "development-only", "cases": outcomes,
                   "inputs": {str(p): core.sha(p) for p in files}}))
    print([(c["page"], c["line_index"], c["image"], c["source"]) for c in outcomes.values()], flush=True)
