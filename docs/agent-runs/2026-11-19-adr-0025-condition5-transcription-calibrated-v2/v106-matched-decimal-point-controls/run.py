"""字形と同じ点を独立に描いた対照で、保存した旧・新の指示を比較する。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
V105 = HERE.parent / "v105-decimal-point-controls"


def module(name, path):
    spec = spec_from_file_location(name, path)
    instance = module_from_spec(spec)
    spec.loader.exec_module(instance)
    return instance


trial = module("original_decimal_trials", V105 / "run.py")
generator = module("matched_point_images", HERE / "generate.py")
trial.HERE = HERE
trial.generator = generator
pilot, core = trial.pilot, trial.core
pilot.HERE = HERE
pilot.OUT = core.CORPUS / "reference-v106-matched-decimal-point-controls"
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "receipts.json"
old_snapshot, old_checks, old_outcome = trial.snapshot, trial.checks, pilot.outcome


def snapshot():
    old_checks()
    plan = old_snapshot()
    pins = (Path(__file__), Path(core.__file__), Path(core.ref.__file__),
            Path(trial.last.previous.trial.base.__file__), V105 / "lock.json")
    plan["files"].update({str(path): core.sha(path) for path in pins})
    originals = {}
    for row, item in plan["mapping"].items():
        originals[item["block"],item["group"]] = row
    for block in range(len(generator.BLOCKS)):
        real = originals[block,"decimal-only"]
        noise = originals[block,"aligned-noise"]
        for dpi in (150,450):
            a = HERE / "fixed-images" / f"{real}-{dpi}.png"
            b = HERE / "fixed-images" / f"{noise}-{dpi}.png"
            if a.read_bytes() != b.read_bytes():
                raise ValueError("同じ位置の字形と黒点の画素が一致しない")
    return plan


def one_read(*args, **kwargs):
    history = old_outcome(*args, **kwargs)
    if sum(record["availability"] == "received" for record in history) > 1:
        raise ValueError("一つの条件で回答済みの読取が二回以上ある")
    return history


def checks():
    old_checks()
    source = trial.reading_outcome
    only_decimal = {"digits":"12345","components":[{"id":6,"role":"decimal"}]}
    only_noise = {"digits":"12345","components":[{"id":6,"role":"noise"}]}
    if source({6:"X"},only_decimal)["source"] != ["omitted"]:
        raise ValueError("本物の点の脱落を数えられない")
    if source({6:"S"},only_noise)["source"] != ["extra"]:
        raise ValueError("余分な点の過剰転記を数えられない")
    if source({6:"X"},only_noise)["source"] != ["same"]:
        raise ValueError("黒点の正しい棄却を数えられない")


if __name__ == "__main__":
    trial.launch.configure()
    trial.checks = checks
    pilot.outcome = one_read
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        cli = trial.argparse.ArgumentParser(description=__doc__)
        cli.add_argument("action", choices=("compare",))
        cli.add_argument("--sha256", required=True)
        cli.add_argument("--codex", required=True, type=Path)
        cli.add_argument("--claude", required=True, type=Path)
        trial.score(cli.parse_args())
    else:
        pilot.collect = trial.last.previous.collect_receipts
        pilot.snapshot = snapshot
        pilot.main()

