"""同じ固定画像で、点の所属を判定する旧・新指示を比較する。"""

import argparse
from collections import Counter, defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from PIL import ImageFont


HERE = Path(__file__).resolve().parent
V102 = HERE.parent / "v102-shape-position-separator-recheck"


def module(name, path):
    spec = spec_from_file_location(name, path)
    instance = module_from_spec(spec)
    spec.loader.exec_module(instance)
    return instance


last = module("prior_shape_prompt", V102 / "run.py")
generator = module("render_decimal_controls", HERE / "generate.py")
core, launch, pilot = last.core, last.launch, last.pilot
measure = last.previous.trial.measure
card_layout = last.previous.trial.prior
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v105-decimal-point-controls"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "receipts.json"
ARMS = ("old", "new")
MODELS = last.MODELS
NEW = (
    "添付の画像だけを見て、{row}の指定番号 {ids} の成分について、数字列の一部かを判定してください。"
    "150 DPIの位置と450 DPIの輪郭を見比べます。点の中心と下端を前後の数字の下端に対して見て、"
    "左右の数字からの間隔と、文字と同じ高さ・大きさ・輪郭に見える根拠を別々に確認します。"
    "一つの点しか見えなくても、黒い点が数字間にあるだけで所属を決めません。"
    "近くに点が複数ある場合は、どの点が両隣の数字と一つの列を作るかを見比べます。"
    "形と位置のどちらか一方だけで決まらず、文字の点と余分な点が同じように見える場合は判別不能にします。"
    "数字の意味、小数の桁数や記号の個数、表記の習慣を前提にしません。枠の所属と数字自体は判定しません。"
)
OUTPUT = "answersは1件" + last.PROMPT.split("answersは1件", 1)[1]


def snapshot():
    core.verify_methods()
    last.hold.fixed_inputs()
    images = HERE / "fixed-images"
    images.mkdir()
    cards = pilot.OUT / "cards"
    cards.mkdir(parents=True)
    font_file = Path(launch.render.typeface)
    font = ImageFont.truetype(font_file, size=16)
    pins = {Path(__file__), HERE / "generate.py", HERE / "protocol.md", V102 / "run.py",
            Path(pilot.__file__), font_file}
    pins.update(generator.WINDOWS_FONTS / filename for filename, _ in generator.BLOCKS)
    jobs, mapping = {}, {}
    for name, block, group in generator.schedule():
        digits, components, pixels = generator.render(block, group)
        paths = []
        for dpi, image in pixels.items():
            path = images / f"{name}-{dpi}.png"
            core.save_once(path, generator.png(image, dpi))
            paths.append(path)
        pins.update(paths)
        x, y, w, h = generator.BOX
        row = {"box": [x, y, w, h], "allocation_axis": "x"}
        layout = {"source_view": {"views": [{}, {"target_rectangle": [3*v for v in (x,y,x+w,y+h)]}]}}
        folder = cards / name
        folder.mkdir()
        views = {
            f"{name}-boundary.png": measure.numeric.view_pair(row, layout, paths, name, font),
            f"{name}-axis.png": measure.ruler(pixels[150], row, name, font),
            f"{name}-component-numbers.png": card_layout.numbered(pixels[150], row, components, name, font),
        }
        for filename, content in views.items():
            path = folder / filename
            core.save_once(path, content)
            pins.add(path)
        ids = [part["id"] for part in components]
        joined = "、".join(map(str, ids))
        for arm, prompt in (("old", last.PROMPT), ("new", NEW + OUTPUT)):
            jobs[f"{name}/{arm}"] = {
                "cards": str(folder),
                "request": {"ids": [name], "images": list(views),
                            "image_sha256": [core.sha(folder / v) for v in views],
                            "prompt": prompt.format(row=name, ids=joined)},
            }
        mapping[name] = {"group": group, "block": block, "digits": digits, "components": components}
    if Counter(row["group"] for row in mapping.values()) != dict.fromkeys(generator.GROUPS,4):
        raise ValueError("4種類が4枠ずつ固定されていない")
    pilot.SAMPLES = list(mapping)
    return {"jobs": jobs, "mapping": mapping, "files": {str(p): core.sha(p) for p in sorted(pins)}}


def reading_outcome(roles, row):
    chosen = [part["id"] for part in row["components"] if roles[part["id"]] == "S"]
    if "U" in roles.values() or len(chosen) > 1:
        return {"source": ["unresolved"], "text": ["unresolved"], "final": None, "adopted": None}
    by_kind = {part["role"]: part["id"] for part in row["components"]}
    expected = row["digits"]
    if "decimal" in by_kind:
        expected = expected[:2] + "." + expected[2:]
    final = row["digits"]
    if chosen:
        final = final[:2] + "." + final[2:]
    labels = []
    if "decimal" in by_kind and by_kind["decimal"] not in chosen:
        labels.append("omitted")
    if "noise" in by_kind and by_kind["noise"] in chosen:
        labels.append("extra")
    text = last.previous.trial.base.changes(core.ref, {"status":"readable", "text":final}, expected)
    return {"source": labels or ["same"], "text": text, "final": final, "adopted": chosen}


def checks():
    row = {"digits":"12345", "components":[{"id":6,"role":"decimal"},{"id":7,"role":"noise"}]}
    mistaken = reading_outcome({6:"X",7:"S"}, row)
    if mistaken["source"] != ["omitted","extra"] or mistaken["text"] != ["same"]:
        raise ValueError("字形は同じで採用元が誤る場合を区別できない")
    for roles in ({6:"S",7:"S"},{6:"S",7:"U"}):
        if reading_outcome(roles,row)["source"] != ["unresolved"]:
            raise ValueError("多点または未判読が確定する")


def score(args):
    checks()
    plan = core.load(pilot.LOCK)
    if core.sha(pilot.LOCK) != args.sha256 or any(
            core.sha(Path(path)) != digest for path,digest in plan["files"].items()):
        raise ValueError("固定した資料のハッシュと一致しない")
    _, _, attachments = last.hold.fixed_inputs()
    runtimes = pilot.audit.delivery.runtime({"gpt":args.codex,"claude":args.claude})
    sessions = set()
    axes = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    per_component = defaultdict(lambda: defaultdict(Counter))
    cases = {}
    for job_name, job in plan["jobs"].items():
        name, arm = job_name.split("/")
        row = plan["mapping"][name]
        ids = [part["id"] for part in row["components"]]
        votes, records, formats = {}, {}, {}
        for model in MODELS:
            history = pilot.outcome(args.sha256, job_name, model, job, runtimes[model])
            if not history or history[-1]["availability"] != "received":
                raise ValueError(f"新規票が揃わない: {job_name} {model}")
            record = history[-1]
            if record["session"] in sessions:
                raise ValueError("新規セッションが重複した")
            sessions.add(record["session"])
            raw = record["answers"][name]
            votes[model], formats[model] = last.read_tags(raw, ids)
            records[model] = {"answer":raw,"session":record["session"]}
        consensus = last.agreed_roles(votes, ids)
        verdict = reading_outcome(consensus, row)
        for group in ("all",row["group"]):
            for view in ("source","text"):
                axes[group][arm][view].update(verdict[view])
        for part in row["components"]:
            per_component[part["role"]][arm][consensus[part["id"]]] += 1
        cases[job_name] = {"group":row["group"], "formats":formats, "votes":records,
                           "cues":votes, "roles":consensus, "verdict":verdict,
                           "components":row["components"]}
    if len(sessions) != 64:
        raise ValueError("新規の64セッションが揃わない")
    result = {"scope":"development-only", "lock_sha256":args.sha256, "formal_attachments_verified":attachments,
              "independent_sessions":len(sessions), "counts":axes,
              "component_consensus":per_component, "cases":cases}
    core.save_once(HERE / "comparison.json", core.encoded(result))
    for g, arms in axes.items():
        print(g, {arm:dict(views["source"]) for arm,views in arms.items()}, flush=True)
    print(dict(per_component), flush=True)


if __name__ == "__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        cli = argparse.ArgumentParser(description=__doc__)
        cli.add_argument("action", choices=("compare",))
        cli.add_argument("--sha256", required=True)
        cli.add_argument("--codex", type=Path, required=True)
        cli.add_argument("--claude", type=Path, required=True)
        score(cli.parse_args())
    else:
        pilot.collect = last.previous.collect_receipts
        pilot.snapshot = snapshot
        pilot.main()

