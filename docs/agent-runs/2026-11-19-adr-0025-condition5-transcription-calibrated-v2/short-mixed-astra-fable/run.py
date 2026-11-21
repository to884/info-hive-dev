"""同じ短い枠と指示のまま、AstraとFableで別の画像二読を試す。"""

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "short-mixed-axis-pilot/run.py"
spec = importlib.util.spec_from_file_location("short_mixed", SOURCE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
base, reads = old.base, old.pilot
OUT, LOCK = old.OUT.parent / HERE.name, HERE / "lock.json"
MODELS = {"sol": "gpt-6.2-astra", "opus": "claude-fable-5-2"}


def checked():
    cards, labels, original = old.material()
    if original != base.load(old.LOCK):
        raise ValueError("配布する画像、対象あるいは指示が先行の固定と異なる")
    pins = (Path(__file__), HERE / "protocol.md", SOURCE, old.LOCK, Path(reads.__file__),
            Path(reads.opus.__file__), Path(base.__file__))
    lock = {**original, "models": MODELS, "previous_lock_sha256": base.sha(old.LOCK),
            "second_pair_inputs": {str(p): base.sha(p) for p in pins}}
    return cards, labels, lock


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--claude", type=Path)
    parser.add_argument("--lock-sha256")
    args = parser.parse_args()
    cards, targets, fixed = checked()
    if args.action == "prepare":
        if OUT.exists() or LOCK.exists():
            raise FileExistsError("新しい二票の固定済み資料がある")
        for name, images in cards.items():
            place = OUT / "cards" / name
            place.mkdir(parents=True)
            for i, data in images.items():
                (place / i).write_bytes(data)
        base.write_json(LOCK, fixed)
        print(base.sha(LOCK), flush=True)
    else:
        old.OUT, old.LOCK, old.HERE, reads.MODELS = OUT, LOCK, HERE, MODELS
        old.run(args, cards, targets, fixed)
