"""v95と同じ固定画像で、旧・新の所属の指示に矛盾がない状態を比較する。"""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/"v95-controlled-numeric-boundary"
spec=spec_from_file_location("controlled_fixed_boundaries",BASE/"run.py")
base=module_from_spec(spec)
spec.loader.exec_module(base)
core, launch, pilot=base.core,base.launch,base.pilot
base_corpus=pilot.OUT
pilot.HERE=HERE
pilot.OUT=core.CORPUS/"reference-v96-explicit-numeric-boundary"
pilot.LOCK,pilot.RESULT=HERE/"lock.json",HERE/"transport-pair.json"
NEW_GUIDE=(
    "数字の所属は『固定150 DPI』の図で確かめ、450 DPIは字形の確認に使います。"
    "区切りの記号の上下の所属は判断せず、下端のすぐ外側の記号も形と成分番号を記録します。"
    "青い横線は表の目印です。本文の記号には含めません。"
)


def snapshot():
    core.verify_methods()
    locked=BASE/"lock.json"
    plan=core.load(locked)
    if any(core.sha(Path(p))!=d for p,d in plan["files"].items()):
        raise ValueError("元の固定または読み取り画像が変わっている")
    files=plan["files"].copy()
    output=pilot.OUT/"display/selection.json"
    source=base_corpus/"display/selection.json"
    output.parent.mkdir(parents=True)
    core.save_once(output,source.read_bytes())
    for p in (Path(__file__),HERE/"protocol.md",locked,output):
        files[str(p)]=core.sha(p)
    jobs={}
    for name,job in plan["jobs"].items():
        request=job["request"]
        if request["prompt"].count(base.GUIDE)!=1:
            raise ValueError("元の所属の補足が見つからない")
        prompt=request["prompt"]
        if name.endswith("/new"):
            prompt=prompt.replace(base.GUIDE,NEW_GUIDE,1)
        jobs[name]={**job,"request":{**request,"prompt":prompt}}
    pilot.SAMPLES=core.load(output)["selected"]
    return {"mapping":plan["mapping"],"jobs":jobs,"files":files}


if __name__=="__main__":
    launch.configure()
    if len(sys.argv)>1 and sys.argv[1]=="compare":
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument("command",choices=("compare",))
        parser.add_argument("--sha256",required=True)
        parser.add_argument("--codex",required=True,type=Path)
        parser.add_argument("--claude",required=True,type=Path)
        base.HERE=HERE
        base.score(parser.parse_args())
    else:
        pilot.snapshot=snapshot
        pilot.main()
