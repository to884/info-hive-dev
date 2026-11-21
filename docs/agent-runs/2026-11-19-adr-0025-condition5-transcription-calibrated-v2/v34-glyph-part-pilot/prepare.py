"""よく似た字を部品で独立に記録し、固定した一対一の対応で本文に戻す。"""

import importlib.util
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v31-kanpo-glyph-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("glyph_parts_transcription", BASE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
pilot = old.pilot
old.HERE = pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v34-glyph-part-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
old.GUIDE = (
    "次の部品が枠内に見えたときは、字の変換で普通の字体に変わらないよう、指定の印を本文のその位置に書きます。"
    "山の右側が上に立の形、下に可なら ⟦glyph:yama-ritsu-ka⟧、大と可なら ⟦glyph:yama-dai-ka⟧。"
    "台（ムと口）の左にしんにょうが回る形は ⟦glyph:road-tai⟧、三水なら ⟦glyph:water-tai⟧。"
    "しんにょうの内側が𠂤なら ⟦glyph:road-tai-stack⟧、卣なら ⟦glyph:road-you⟧。"
    "草冠の下が與なら ⟦glyph:grass-yo⟧、同じ字で草冠がなければ ⟦glyph:bare-yo⟧。"
    "記号の位置は、元の字の場所です。例の部品が見えないときは見える文字を普通に写します。"
    "一つの縦列を上から下へ追います。左右の別列に入る字は枠への所属を確かめます。"
    "枠の終わりに罫線や空白しか見えない場合は、直前の字で返答を終えます。"
)
CODES = {"yama-ritsu-ka": "﨑", "yama-dai-ka": "崎",
         "road-tai": "迨", "water-tai": "治", "road-tai-stack": "追", "road-you": "逌",
         "grass-yo": "藇", "bare-yo": "與"}
MARK = re.compile(r"⟦glyph:([a-z-]+)⟧")
initial_decode = pilot.reference.decoded


def decoded(value, partitions):
    text = value["text"]
    tags = [m[1] for m in MARK.finditer(text)]
    if any(n not in CODES for n in tags) or "⟦glyph:" in MARK.sub("", text):
        return pilot.reference.UNKNOWN
    return initial_decode({**value, "text": MARK.sub(lambda m: CODES[m[1]], text)}, partitions)


def snapshot():
    plan = old.snapshot()
    plan["files"][str(Path(__file__))] = pilot.audit.sha(Path(__file__))
    return plan


if __name__ == "__main__":
    pilot.reference.decoded = decoded
    pilot.snapshot = snapshot
    pilot.main()
