"""同じ物理位置を示した開発の二票の符号を、固定画素と元の描画で確かめる。"""

import argparse
from collections import Counter
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as previous

audit = previous.module("next_independent_method", HERE.parent / "v27-reference-audit/run.py")
proof = previous.module("next_source_reference", audit.HERE / "source.py")
old_source = previous.module("prior_pdf_source", previous.HERE / "source.py")
ellipsis = previous.module("ellipsis_cid_reproduction", HERE.parent / "v25-ellipsis-source-pilot/run.py")
background = previous.module("background_cid_reproduction", HERE.parent / "v28-colored-point-source-pilot/run.py")
routes = {"old_source": old_source, "ellipsis": ellipsis, "trail": ellipsis.trail,
          "trace": ellipsis.trace, "background": background}
load, save, encoded, sha = previous.load, previous.save_once, previous.encoded, previous.sha
STAGES = {"33": HERE, "32": HERE.parent / "v32-bullet-shape-pilot"}


def cases(stage, root):
    result, lock = stage / "result.json", stage / "lock.json"
    plan = load(lock)
    data = load(result)
    if (data["lock_sha256"] != sha(lock) or data["scope"] != "development-only"
            or set(data["cases"]) != set(plan["jobs"])
            or any(sha(Path(p)) != h for p, h in plan["files"].items())):
        raise ValueError("開発の二票は先に固定した依頼と異なる")
    rows = load(root / "display/selection.json")["selected"]
    frames = []
    for name, finding in data["cases"].items():
        if finding["pair_result"] != "both-location-needs-source":
            continue
        job = plan["jobs"][name]
        canonical = Path(job["cards"])
        raw_files = canonical.parent.parent / "packages.json"
        delivery = load(raw_files)
        item, = job["request"]["ids"]
        pinned = delivery["packs"][canonical.name]["mapping"][item]["image_reference"]
        if any(sha(canonical / p) != digest for p, digest in
               zip(job["request"]["images"], job["request"]["image_sha256"], strict=True)):
            raise ValueError("独立の二読に渡した画像のハッシュが異なる")
        row = rows[plan["mapping"][name.split("/")[0]]["entry"]]
        if (finding["page"], finding["line_index"]) != (row["key"], row["line_index"]):
            raise ValueError("合意の参照が同じ画像と結び付かない")
        vote = finding["readings"]
        frames.append((name, {"row": row, "assets": pinned, "answer": vote["pair"],
                              "coordinates": vote["coordinates"]}, finding["expected"]))
    return data, frames


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("stage", choices=STAGES)
    args = cli.parse_args()
    stage = STAGES[args.stage]
    root = audit.CORPUS / ("reference-" + stage.name)
    final = stage / "source-comparison.json"
    if final.exists():
        raise FileExistsError("開発用の出典確認は確定済み")
    previous.verify_before_source()
    data, rows = cases(stage, root)
    request, archive = (root / f"compare-{leaf}.json" for leaf in ("requests", "archive"))
    expected = encoded({"pages": sorted({c["row"]["key"] for _, c, _ in rows})})
    if not request.exists():
        save(request, expected)
    elif request.read_bytes() != expected:
        raise ValueError("出典確認を依頼する点を変えられない")
    if not archive.exists():
        old_source.initial.collect(request, archive)
    source = load(archive)
    previous.ref.checked_source(source, request)
    catalog, loaded = previous.packets.old.lookup()[1], {}
    findings = {k: {"result": c["pair_result"]} for k, c in data["cases"].items()}
    for name, case, prior in rows:
        resolved, evidence = previous.ref.v10.resolved(case, source)
        if resolved["status"] == "unreadable" and evidence in ("source-location-not-proven", "source-unavailable"):
            substitute = proof.fallback(audit, case, source, catalog, loaded, routes)
            if substitute:
                resolved, evidence = substitute
        if resolved["status"] == "unreadable":
            result = "insufficient-source"
        elif prior == resolved["text"]:
            result = "same"
        elif resolved["text"] in prior:
            result = "omitted"
        elif prior in resolved["text"]:
            result = "extra"
        else:
            result = "different"
        tag = case["row"]["key"], case["row"]["line_index"]
        print(tag, result, flush=True)
        findings[name] = {"result": result, "detail": evidence, "text": resolved["text"]}
    summary = Counter(c["result"] for c in findings.values())
    files = (Path(__file__), stage / "result.json", stage / "lock.json", archive,
             audit.HERE / "source.py", Path(ellipsis.__file__), Path(background.__file__))
    save(final, encoded({"scope": "development-only", "cases": findings, "counts": summary,
                         "inputs": {str(p): sha(p) for p in files}}))
    print(dict(summary), flush=True)


if __name__ == "__main__":
    main()
