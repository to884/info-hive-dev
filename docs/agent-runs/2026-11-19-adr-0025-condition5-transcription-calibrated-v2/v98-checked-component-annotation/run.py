"""v97の保存票だけで、本文と後置の番号の切り分けを再検証する。"""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ARCHIVE=HERE.parent/"v97-black-punctuation-lookalikes"
spec=spec_from_file_location("saved_black_stroke_votes",ARCHIVE/"run.py")
test=module_from_spec(spec)
spec.loader.exec_module(test)
core=test.core
old_trace=test.trace_old
ILL_FORMED_TAIL=re.compile(r"[0-9]+:[0-9?]+:[CDTHSU](?:\||$)")


def trace_checked(vote, known):
    if vote["status"]!="readable":
        return old_trace(vote,known)
    compact=core.ref.NORMALIZE(vote["text"])
    primary=compact.split("||",1)[0]
    if "|" in primary or ILL_FORMED_TAIL.search(primary):
        return core.ref.UNKNOWN,None
    return old_trace({**vote,"text":compact},known)


def regression():
    ids={6,7}
    for text in ("12,345||2:7:C","12,345 | | 2:7:C","12,345 ｜｜ 2:7:C"):
        answer, source=trace_checked({"status":"readable","text":text},ids)
        if answer["text"]!="12,345" or source!=[(2,",",7)]:
            raise ValueError("正しい本文と成分番号を切り分けられない")
    for text in ("12,345 | 2:7:C","12,345 2:7:C"):
        answer, source=trace_checked({"status":"readable","text":text},ids)
        if answer!=core.ref.UNKNOWN or source is not None:
            raise ValueError("形式が壊れた成分番号を本文として採点した")
    answer, origin=trace_checked({"status":"readable","text":"12:345||2:7:T"},ids)
    if answer["text"]!="12:345" or origin!=[(2,":",7)]:
        raise ValueError("本文中のコロンを成分の番号と取り違えた")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex",required=True,type=Path)
    parser.add_argument("--claude",required=True,type=Path)
    args=parser.parse_args()
    test.launch.configure()
    regression()
    args.sha256=core.sha(ARCHIVE/"lock.json")
    saved=core.load(ARCHIVE/"comparison.json")
    test.trace_old=trace_checked
    test.HERE=HERE
    test.score(args)
    audited=core.load(HERE/"comparison.json")
    differences=[k for k,value in audited["cases"].items() if saved["cases"][k]!=value]
    contract=core.load(test.pilot.LOCK)
    string_only={}
    point_like_old=[]
    for key,item in audited["cases"].items():
        if key.endswith("/old"):
            if any(core.ref.v10.LITERAL_POINT.search(item["final"][m]["text"]) for m in ("gpt","claude")):
                point_like_old.append(key)
            continue
        tag=key.split("/")[0]
        row=core.load(test.pilot.OUT/"display/selection.json")["selected"][contract["mapping"][tag]["entry"]]
        paired,_=core.ref.aligned(item["final"]["gpt"],item["final"]["claude"],row["box"][2])
        if paired!=item["final"]["pair"]:
            string_only[key]=paired
    if differences or saved["counts"]!=audited["counts"] or saved["adopted_components"]!=audited["adopted_components"]:
        raise ValueError(f"採点を再検査した結果が前回と異なる: {differences}")
    core.save_once(HERE/"recheck.json",core.encoded({"scope":"development-only-saved-v97-votes",
                   "original_lock_sha256":args.sha256,"original_comparison_sha256":core.sha(ARCHIVE/"comparison.json"),
                   "recheck_comparison_sha256":core.sha(HERE/"comparison.json"),
                   "changed_rows":differences,"old_literal_point_rows":point_like_old,
                   "new_string_only_pair_differences":string_only,"regression_examples":6}))
    print("形式の回帰6例と保存済み64票を再検査。今回の判定の変更",len(differences),flush=True)


if __name__=="__main__":
    main()
