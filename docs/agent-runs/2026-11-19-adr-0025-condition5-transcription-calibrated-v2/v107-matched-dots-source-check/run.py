"""画素が同じ4対について、保存した画像票と固定描画記録の結果を照合する。"""

from collections import Counter, defaultdict
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from PIL import Image, ImageFont


HERE = Path(__file__).resolve().parent
V106 = HERE.parent / "v106-matched-decimal-point-controls"
spec = spec_from_file_location("frozen_matched_dots", V106 / "run.py")
frozen = module_from_spec(spec)
spec.loader.exec_module(frozen)
trial, core = frozen.trial, frozen.core
MODELS = trial.MODELS
ARMS = trial.ARMS
SOURCE_ROLE = {"decimal": "S", "noise": "X"}


def checked_inputs():
    integrity = core.load(V106 / "integrity.json")
    state = integrity["lock_sha256"]
    for name, field in (("lock.json","lock_sha256"),("comparison.json","comparison_sha256")):
        trial.last.hold.verify(V106/name, integrity[field])
    locked = core.load(V106/"lock.json")
    for path, digest in locked["files"].items():
        trial.last.hold.verify(Path(path), digest)
    previous = core.load(V106/"comparison.json")
    if previous["lock_sha256"] != state:
        raise ValueError("画像票が別の固定を参照している")
    _, _, formal_images = trial.last.hold.fixed_inputs()
    return locked, previous, integrity, formal_images


def matched_pairs(locked, integrity):
    rows = {(case["block"],case["group"]): row for row,case in locked["mapping"].items()}
    pairs = [(rows[block,"decimal-only"],rows[block,"aligned-noise"]) for block in range(4)]
    if [list(pair) for pair in pairs] != integrity["paired_same_pixels_at_both_dpi"]:
        raise ValueError("記録された画素一致の対と異なる")
    for decimal, noise in pairs:
        for dpi in (150,450):
            left = V106/"fixed-images"/f"{decimal}-{dpi}.png"
            right = V106/"fixed-images"/f"{noise}-{dpi}.png"
            if core.sha(left) != core.sha(right):
                raise ValueError(f"固定画素が一致しない: {decimal}, {noise}, {dpi}")
        left, right = (locked["mapping"][row] for row in (decimal,noise))
        true, = left["components"]
        extra, = right["components"]
        if (left["digits"] != right["digits"] or true["role"] != "decimal" or extra["role"] != "noise"
                or any(true[key] != extra[key] for key in ("id","bounds","high_bounds"))):
            raise ValueError(f"対の描画成分が対応しない: {decimal}, {noise}")
    return pairs


def verify_delivery_views(locked, row, drawing, font):
    paths = tuple(V106/"fixed-images"/f"{row}-{dpi}.png" for dpi in (150,450))
    x, y, w, h = frozen.generator.BOX
    frame = {"box": [x,y,w,h], "allocation_axis": "x"}
    source = {"source_view": {"views": [{}, {"target_rectangle": [3*v for v in (x,y,x+w,y+h)]}]}}
    with Image.open(paths[0]) as pixels:
        views = {
            f"{row}-boundary.png": trial.measure.numeric.view_pair(frame,source,paths,row,font),
            f"{row}-axis.png": trial.measure.ruler(pixels,frame,row,font),
            f"{row}-component-numbers.png": trial.card_layout.numbered(
                pixels,frame,drawing["components"],row,font),
        }
    hashes = [sha256(value).hexdigest() for value in views.values()]
    for arm in ARMS:
        request = locked["jobs"][f"{row}/{arm}"]["request"]
        if request["images"] != list(views) or request["image_sha256"] != hashes:
            raise ValueError(f"固定画素から元の配布図を再現できない: {row}/{arm}")


def original_ballot(locked, scored, row, arm, ident, sessions, lock_hash):
    job = f"{row}/{arm}"
    image_hashes = locked["jobs"][job]["request"]["image_sha256"]
    ballots = {}
    for model in MODELS:
        received = scored["votes"][model]
        session = received["session"]
        if session in sessions:
            raise ValueError("保存票のセッションが重複している")
        sessions.add(session)
        archive = frozen.pilot.OUT/"reads"/row/arm/model
        attempt, = sorted(archive.glob("attempt-*"))
        claim = core.load(attempt/"claim.json")
        start = core.load(attempt/"raw"/"start.json")
        if (claim["lock_sha256"] != lock_hash or claim["name"] != job or claim["role"] != model
                or start["image_sha256"] != image_hashes):
            raise ValueError(f"保存票と固定画像を照合できない: {job} {model}")
        parsed, status = trial.last.read_tags(received["answer"], [ident])
        cues = {i:list(values) for i,values in parsed.items()}
        if status != "valid" or scored["formats"][model] != status or cues[ident] != scored["cues"][model][str(ident)]:
            raise ValueError(f"保存票の役割を再現できない: {job} {model}")
        ballots[model] = parsed
    return trial.last.agreed_roles(ballots,[ident])


def main():
    read_root = frozen.pilot.OUT/"reads"
    before_attempts = set(read_root.rglob("attempt-*"))
    locked, previous, integrity, formal_images = checked_inputs()
    font = ImageFont.truetype(Path(trial.launch.render.typeface), size=16)
    pairs = matched_pairs(locked, integrity)
    counts = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    cases, sessions = {}, set()
    for pair in pairs:
        for row in pair:
            drawing = locked["mapping"][row]
            verify_delivery_views(locked, row, drawing, font)
            component, = drawing["components"]
            ident = component["id"]
            fixed_roles = {ident:SOURCE_ROLE[component["role"]]}
            from_record = trial.reading_outcome(fixed_roles,drawing)
            for arm in ARMS:
                scored = previous["cases"][row+"/"+arm]
                consensus = original_ballot(locked, scored, row, arm, ident, sessions, integrity["lock_sha256"])
                from_image = trial.reading_outcome(consensus,drawing)
                if ({str(i):val for i,val in consensus.items()} != scored["roles"] or
                        from_image != scored["verdict"] or scored["components"] != drawing["components"]):
                    raise ValueError(f"画像だけの判定と一致しない: {row}/{arm}")
                cases[row+"/"+arm] = {
                    "component":component, "image_roles":consensus, "record_roles":fixed_roles,
                    "image_only":from_image, "drawing_record":from_record,
                }
                for group in ("all",drawing["group"]):
                    counts[group][arm]["image_only"].update(from_image["source"])
                    counts[group][arm]["drawing_record"].update(from_record["source"])
    if len(sessions) != 32:
        raise ValueError("4対の保存32票を照合できない")
    if set(read_root.rglob("attempt-*")) != before_attempts:
        raise ValueError("再集計中に読取試行が変化した")
    result = {"pairs":pairs, "counts":counts, "cases":cases, "matched_saved_sessions":32,
              "formal_attachments_verified":formal_images, "new_image_reads":0,
              "frozen_drawing_record_sha256":integrity["lock_sha256"]}
    data = core.encoded(result)
    output = HERE/"comparison.json"
    if output.exists():
        if output.read_bytes() != data:
            raise ValueError("保存した再集計と一致しない")
    else:
        core.save_once(output,data)
    for group, arms in counts.items():
        print(group,{arm:{basis:dict(stats) for basis,stats in bases.items()} for arm,bases in arms.items()})


if __name__ == "__main__":
    main()

