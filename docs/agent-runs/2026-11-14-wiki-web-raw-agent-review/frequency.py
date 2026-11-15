# 実際の取り込みの記録 4 件で、レビューの指摘の条件が実際に起きたかを数える
import json
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
sys.path.insert(0, str(repo / "tests" / "wiki"))
import check_web_raw_agent as c  # noqa: E402

SEPS = {"U+2028": chr(0x2028), "U+2029": chr(0x2029), "U+0085": chr(0x85)}
runs_dir = repo / "docs" / "agent-runs" / "2026-11-14-wiki-web-raw-agent-review"
total = {}


def add(key, n=1):
    total[key] = total.get(key, 0) + n


for name in ("trial-cqrs.json", "trial-bloom.json", "trial-0161-cqrs.json", "trial-0181-cqrs.json"):
    session = json.loads((runs_dir / name).read_bytes().decode("utf-8"))["session"]
    main, subs = c.find_transcripts(session)
    raw_bytes = main.read_bytes() + b"".join(p.read_bytes() for p in subs)
    text_all = raw_bytes.decode("utf-8")
    seps = {k: text_all.count(v) for k, v in SEPS.items()}
    lines_total = sum(len([ln for ln in p.read_bytes().split(b"\n") if ln.strip()]) for p in [main, *subs])
    split_diff = sum(len(p.read_bytes().decode("utf-8").splitlines()) - len(p.read_bytes().split(b"\n"))
                     for p in [main, *subs])
    bash = finish = combined = multi_runs = prefixed = is_error = text_runs = 0
    for p in subs:
        evs = c.events(c.read_jsonl(p))
        results = c.results_of(evs)
        for t in c.tools_of(evs):
            if t["name"] not in ("Bash", "PowerShell"):
                continue
            bash += 1
            cmd = str(t["input"].get("command", ""))
            if not c.names_finish(cmd):
                continue
            finish += 1
            if re.search(r"&&|\|\||;|\n", cmd):
                combined += 1
            r = results.get(t["id"])
            if r is None:
                continue
            is_error += r["is_error"]
            found = c.check_runs(r["text"])
            multi_runs += len(found) > 1
            text_runs += sum(1 for x in found if x["json"] is None)
            for start, _, _ in c.check_json_spans(r["text"]):
                if start > 0 and r["text"][start - 1] != "\n":
                    prefixed += 1
    print(f"{name}: 行 {lines_total}、splitlines との差 {split_diff}、区切りの文字 {seps}、"
          f"エージェントの Bash {bash}、finish {finish}（複数のコマンド {combined}、誤りの結果 {is_error}、"
          f"1 つの結果に 2 回以上 {multi_runs}、文字の出力の回 {text_runs}、行の途中からの JSON {prefixed}）")
