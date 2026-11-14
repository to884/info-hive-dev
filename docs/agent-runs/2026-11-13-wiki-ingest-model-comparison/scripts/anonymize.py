# -*- coding: utf-8 -*-
"""目隠しの評価のために、raw からモデル名の手がかりを消して別名で書き出す。

使い方: python anonymize.py <入力の raw/xxx.md> <出力のパス>
- frontmatter の translated_by を "" にする
- 画像の補足の先頭の「> <表示名> 補足:」を「> 補足:」にする
- 本文に Haiku、Sonnet、Opus、Claude の語が残れば警告する
"""
import re
import sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
text = src.read_bytes().decode("utf-8").replace("\r\n", "\n")
text = re.sub(r'^translated_by:.*$', 'translated_by: ""', text, count=1, flags=re.M)
text = re.sub(r"^>\s*[^>\n]*?補足[:：]", "> 補足:", text, flags=re.M)
left = re.findall(r"(Haiku|Sonnet|Opus|Claude)[^\n]{0,30}", text)
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_bytes(text.encode("utf-8"))
if left:
    sys.stderr.buffer.write(("警告: モデル名らしい語が残っている: %r\n" % left).encode("utf-8"))
