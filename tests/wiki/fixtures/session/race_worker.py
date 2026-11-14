"""raw の排他の試験の駆動。2 つのプロセスで同時に動かし、回ごとにファイルで足並みをそろえてから、違うバイト列を
同じスラッグに wiki_session.write_raw() で書く。結果（回ごとの raw_state）を JSON で標準出力に出す。

    python race_worker.py <scripts> <base> <wiki> <raw> <who: 0|1> <reps> <exclusive|replace>

replace は対照で、公開を os.replace（上書きする）に差し替える。
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def main() -> int:
    scripts, base, wiki, raw, who, reps, mode = sys.argv[1:8]
    sys.path.insert(0, scripts)
    import wiki_session as ws
    if mode == "replace":
        ws.publish_exclusive = os.replace
    base, wiki, raw = Path(base), Path(wiki), Path(raw)
    who, reps = int(who), int(reps)
    sync = base / "sync"
    sync.mkdir(exist_ok=True)
    states = []
    for i in range(reps):
        (sync / f"{i}-{who}").write_bytes(b"")
        deadline = time.monotonic() + 30
        while not (sync / f"{i}-{1 - who}").exists():
            if time.monotonic() > deadline:
                print(json.dumps({"error": f"相手を待てなかった: {i}"}))
                return 1
        state, _path = ws.write_raw(wiki, raw, f"r{i}", f"版 {who} の {i}\n".encode("utf-8"))
        states.append(state)
    print(json.dumps(states))
    return 0


if __name__ == "__main__":
    sys.exit(main())
