# -*- coding: utf-8 -*-
"""設計案のタグの照合（多重集合、入れ子、閉じ、空の中身）を試作して、fill.json を調べる。

使い方: python check_fill.py <nodes.json> <fill.json>
"""
import json
import re
import sys
from collections import Counter

TAG = re.compile(r"⟦(/?)([A-Z]+\d+|BR)⟧")
PAIRED = {"L", "S", "E"}


def parse(s):
    """タグの木を読む。返り値: (単独のタグの Counter, 対のタグの Counter, 親の対応 dict, 誤り)"""
    singles, pairs, parent, errs = Counter(), Counter(), {}, []
    stack, start = [], {}
    for m in TAG.finditer(s):
        close, name = m.group(1) == "/", m.group(2)
        kind = re.match(r"[A-Z]+", name).group(0)
        if kind in PAIRED:
            if not close:
                parent.setdefault(name, stack[-1] if stack else None)
                stack.append(name)
                start[name] = m.end()
                pairs[name] += 1
            else:
                if not stack or stack[-1] != name:
                    errs.append(f"閉じの順が違う {name}")
                    if name in stack:
                        stack.remove(name)
                else:
                    stack.pop()
                if not s[start.get(name, m.start()):m.start()].strip():
                    errs.append(f"中身が空 {name}")
        else:
            singles[name] += 1
            parent[name] = stack[-1] if stack else None
    if stack:
        errs.append(f"閉じていない {stack}")
    return singles, pairs, parent, errs


nodes = json.load(open(sys.argv[1], encoding="utf-8"))
fill = json.load(open(sys.argv[2], encoding="utf-8"))["nodes"]
bad = 0
for nid, node in nodes.items():
    if nid not in fill:
        print(nid, "訳文がない")
        bad += 1
        continue
    a, b = parse(node["text"]), parse(fill[nid])
    errs = list(b[3])
    if a[0] != b[0]:
        errs.append(f"単独のタグ {dict(a[0])} -> {dict(b[0])}")
    if a[1] != b[1]:
        errs.append(f"対のタグ {dict(a[1])} -> {dict(b[1])}")
    if a[2] != b[2]:
        errs.append(f"入れ子 {a[2]} -> {b[2]}")
    md = re.findall(r"\*\*|\]\(|`", fill[nid])
    if md:
        errs.append(f"Markdown の記法 {md}")
    if errs:
        bad += 1
        print(nid, errs)
        print("   原文:", node["text"][:200])
        print("   訳文:", fill[nid][:200])
print(f"誤り {bad} / {len(nodes)}")
