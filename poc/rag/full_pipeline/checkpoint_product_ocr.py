"""product_ocr.py の処理を強制終了し、再開しても保存済みのページが変わらないことを確かめる。OS は止めない。

  stop    保存済みのページ（page-*.json）の SHA-256 と更新日時を記録し、親プロセスだけを強制終了する。
          子プロセス（文書の抽出と OCR）が、親の消失を見て自分で終わることも確かめる。
  verify  再開のあとで、別の処理が動いていて、記録したページが 1 つも書き換わらず、
          再開のあとに保存したページがあり、どれも製品の形で読めることを確かめる。

試験のあいだ、同じ data_dir にほかの書き手（MCP の取り込みなど）がいないことを前提にする。
再開のあとのページは更新日時で見分けるので、ほかの書き手のページも数えてしまうためである。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import psutil

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2]))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0, str(HERE.parent))
from product_ocr import Layout, now, write_json  # noqa: E402


def saved(layout: Layout) -> dict:
    result = {}
    for path in (layout.data_dir / "extracted").glob("*/*/page-*.json"):
        info = path.stat()
        result[path.relative_to(layout.data_dir).as_posix()] = [hashlib.sha256(path.read_bytes()).hexdigest(),
                                                                info.st_mtime_ns]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["stop", "verify"])
    parser.add_argument("--workspace", type=Path, default=POC_DATA / "full-ocr-v050-20261109")
    args = parser.parse_args()
    layout = Layout(args.workspace)
    snapshot = layout.root / "interrupt-snapshot.json"
    result_path = layout.root / "interrupt-result.json"
    if args.stage == "stop":
        owner = psutil.Process(int(layout.pid.read_text(encoding="utf-8")))
        children = owner.children(recursive=True)
        before = saved(layout)
        write_json(snapshot, {"saved": before, "owner": owner.pid, "children": [child.pid for child in children]})
        owner.kill()
        _, alive = psutil.wait_procs([owner, *children], timeout=30)
        write_json(result_path, {"stopped_at": now(), "killed": "runner_only", "descendants": len(children),
                                 "descendants_left": [process.pid for process in alive],
                                 "saved_pages_before_interrupt": len(before), "os_power_cut": False, "resumed": False})
        print(json.dumps({"saved_pages": len(before), "descendants": len(children),
                          "descendants_left": len(alive)}, ensure_ascii=False))
        if alive:
            raise SystemExit("子プロセスが残りました。")
    else:
        recorded = json.loads(snapshot.read_text(encoding="utf-8"))
        before = recorded["saved"]
        record = json.loads(result_path.read_text(encoding="utf-8"))
        # スナップショットのあと、強制終了までにも保存は進む。再開を確かめるには、再開した処理が動いていて、
        # 強制終了のあとに保存したページがあることを見る。
        runner = int(layout.pid.read_text(encoding="utf-8")) if layout.pid.exists() else None
        if runner is None or runner == recorded["owner"] or not psutil.pid_exists(runner):
            raise SystemExit("再開した処理が動いていません。")
        stopped = psutil.Process(runner).create_time()
        after = saved(layout)
        changed = [key for key, value in before.items() if after.get(key) != value]
        resumed = [key for key, value in after.items() if key not in before and value[1] / 1e9 > stopped]
        broken = []
        for key in resumed:
            page = json.loads((layout.data_dir / key).read_text(encoding="utf-8"))
            if list(page) != ["page", "text", "quality", "ocr", "ocr_empty"]:
                broken.append(key)
        record.update({"verified_at": now(), "resumed": bool(resumed) and not broken, "resumed_runner": runner,
                       "saved_pages_after_resume": len(after), "pages_saved_by_resumed_runner": len(resumed),
                       "pages_not_in_product_form": len(broken),
                       "saved_pages_changed_or_missing": len(changed), "examples": (changed + broken)[:10]})
        write_json(result_path, record)
        print(json.dumps({key: record[key] for key in ["saved_pages_before_interrupt", "saved_pages_after_resume",
                                                       "pages_saved_by_resumed_runner", "pages_not_in_product_form",
                                                       "saved_pages_changed_or_missing"]}, ensure_ascii=False))
        if changed or broken or not resumed:
            raise SystemExit("再開の確かめに失敗しました。")


if __name__ == "__main__":
    main()
