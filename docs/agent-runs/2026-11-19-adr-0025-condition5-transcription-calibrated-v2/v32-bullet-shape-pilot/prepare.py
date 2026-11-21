"""色付きの項目丸と単独の塗り点を、同じ添付で明示的に区別する。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v30-repeated-bullet-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("explicit_bullet_shape_transcription", BASE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
pilot = old.pilot
old.HERE = pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v32-bullet-shape-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
old.GUIDE = (
    "丸は、450 DPIの枠なしで、形、色、同じ行での繰り返しを確認します。"
    "青などの色付きで隣の字の半分ほどの大きさの塗り丸が、同じ行の中に複数並び、"
    "それぞれ独立した本文項目の直前にあると確かめた時に、その形を「●」と写します。"
    "黒い単独の塗り点は行の先頭や本文の中で字種が画像から決まらない場合、位置を ⟦round:X-X⟧ と書きます。"
    "形が塗り点で字種が決まらなければ、文中で中黒を置くのが自然に見える場合も座標を返します。"
    "単独の round は横座標で読んだ同じ中心値を2回書きます。"
    "箇条書きの位置にそろう上が白く下が黒い右向きの矢じりは「➢」です。図表の色見本は除きます。"
)


def snapshot():
    plan = old.snapshot()
    plan["files"][str(Path(__file__))] = pilot.audit.sha(Path(__file__))
    return plan


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
