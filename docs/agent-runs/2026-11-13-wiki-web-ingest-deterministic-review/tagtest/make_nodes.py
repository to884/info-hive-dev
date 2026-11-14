# -*- coding: utf-8 -*-
"""基準の raw の段落を、設計案のタグ付きの文字列に変える（試作。Markdown から作る）。

使い方: python make_nodes.py <compare_raw.py のあるフォルダー> <出力の JSON> <raw.md>:<上限>:<守る語,…> ...
"""
import json
import re
import sys

sys.path.insert(0, sys.argv[1])
import compare_raw as c  # noqa: E402

out_path = sys.argv[2]
TOKEN = re.compile(r"\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|`([^`]+)`|(?<![\*\w])\*([^*\s][^*]*?)\*(?!\*)")


def tag(text, keep):
    side = {}
    n = {"L": 0, "S": 0, "E": 0, "K": 0, "T": 0}
    urls = {}

    def nxt(k):
        n[k] += 1
        return f"{k}{n[k]}"

    def terms(s):
        for t in sorted(keep, key=len, reverse=True):
            def rep(m):
                i = nxt("T")
                side[i] = m.group(0)
                return f"⟦{i}⟧"
            s = re.sub(r"(?<![\w⟦])" + re.escape(t) + r"(?![\w])", rep, s)
        return s

    def walk(s):
        out, pos = [], 0
        for m in TOKEN.finditer(s):
            out.append(terms(s[pos:m.start()]))
            if m.group(1) is not None:
                i = nxt("S")
                out.append(f"⟦{i}⟧{walk(m.group(1))}⟦/{i}⟧")
            elif m.group(2) is not None:
                i = nxt("L")
                urls[i] = m.group(3)
                out.append(f"⟦{i}⟧{walk(m.group(2))}⟦/{i}⟧")
            elif m.group(4) is not None:
                i = nxt("K")
                side[i] = m.group(4)
                out.append(f"⟦{i}⟧")
            else:
                i = nxt("E")
                out.append(f"⟦{i}⟧{walk(m.group(5))}⟦/{i}⟧")
            pos = m.end()
        out.append(terms(s[pos:]))
        return "".join(out)

    return walk(text), side, urls


nodes = {}
k = 0
for spec in sys.argv[3:]:
    path, limit, keep = spec.rsplit(":", 2)
    keep = [t for t in keep.split(",") if t]
    body = c.split_frontmatter(c.read(path))[1]
    count = 0
    for kind, t in c.blocks(body):
        if kind not in ("para", "list") or count >= int(limit):
            continue
        items = [re.sub(r"^\s*[-*+]\s+", "", l) for l in t.split("\n")] if kind == "list" else [t.replace("\n", " ")]
        for it in items:
            if len(it) < 40 or count >= int(limit):
                continue
            k += 1
            s, side, urls = tag(it, keep)
            nodes[f"n{k:04d}"] = {"text": s, "side": side, "urls": urls}
            count += 1
json.dump(nodes, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(nodes), "nodes", sum(s["text"].count("⟦") for s in nodes.values()), "tags")
