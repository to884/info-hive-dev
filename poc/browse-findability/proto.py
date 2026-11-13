"""browse の索引とサイドバーの試作（A 分類の木、B 絞り込める一覧、C 検索が主役）を作る。

今の版（wiki_browse.py build）で書き出したフォルダーから、記事の本文（#_main の中身）を借り、
元の Wiki の frontmatter と索引の行から、試作の画面とデータを作る。配布対象ではない。

使い方: python -X utf8 proto.py <元の Wiki> <書き出したフォルダー> <出力先> [--name <表示名>]
出力先の下に a/、b/、c/ を作り直す。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "base-uri 'none'; form-action 'none'")
TYPE_LABELS = {"source": "ソース", "entity": "エンティティ", "concept": "コンセプト", "synthesis": "シンセシス"}
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
VARIANTS = {"a": "A. 分類の木", "b": "B. 絞り込める一覧", "c": "C. 検索が主役", "d": "D. 木と絞り込める一覧"}


def read(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def split_fm(text: str) -> tuple:
    m = re.match(r"---\n(.*?)\n---\n?", text, flags=re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        v = v.strip()
        if not k or not v:
            continue
        if v.startswith("["):
            try:
                meta[k.strip()] = [str(x) for x in json.loads(v)]
            except ValueError:
                meta[k.strip()] = [x.strip(' "') for x in v.strip("[]").split(",") if x.strip()]
        else:
            meta[k.strip()] = v.strip('"')
    return meta, text[m.end():]


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def js_data(name: str, value) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    text = text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return f"window.{name}={text};\n"


# --- 元の Wiki と書き出しを読む ---

def load_pages(wiki: Path, exported: Path) -> dict:
    pages = {}
    for f in sorted(exported.rglob("*.html")):
        rel = f.relative_to(exported).as_posix()
        if rel == "index.html" or rel.startswith(("assets/", "data/")):
            continue
        src = read(f)
        m = re.search(r'data-page-id="([^"]+)"', src)
        if not m:
            continue
        pid = html.unescape(m.group(1))
        main = re.search(r'<main id="_main">\n(.*)</main>', src, flags=re.S).group(1)
        body = re.search(r'<div id="_body">\n(.*?)</div>\n</article>', src, flags=re.S).group(1)
        heads = [strip_tags(h) for lv, h in re.findall(r"<h([2-6])[^>]*>(.*?)</h\1>", body)]
        lead = ""
        pm = re.search(r"<p>(.*?)</p>", body, flags=re.S)
        if pm:
            lead = re.split(r"(?<=。)", strip_tags(pm.group(1)).replace("\n", ""))[0].rstrip("。")
        md = wiki / (pid + ".md")
        meta, _ = split_fm(read(md)) if md.exists() else ({}, "")
        root = re.search(r'data-root="([^"]*)"', src).group(1)
        pages[pid] = {"i": pid, "p": rel, "t": meta.get("title") or pid.rsplit("/", 1)[-1],
                      "y": meta.get("type", ""), "g": meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
                      "u": meta.get("updated", ""), "h": heads, "lead": lead, "s": "", "main": main, "root": root}
    return pages


def resolve(target: str, pages: dict) -> "str | None":
    target = target.strip()
    if target in pages:
        return target
    hits = [pid for pid in pages if pid.rsplit("/", 1)[-1] == target]
    return hits[0] if len(hits) == 1 else None


def load_groups(wiki: Path, pages: dict) -> list:
    """索引のファイルから、グループの木を作る。試作の規則:
    - 索引のファイルの最初の h1 は、そのファイルのグループの名前にまとめ、入れ子を 1 段減らす。
    - index.md が indexes/ への行だけなら、index.md をグループにせず、その順と行の文字で、分割した索引を並べる。
    - 要約は、索引の行の、最初の wikilink のあとの文字。なければ frontmatter の summary、なければ本文の最初の文。
    """
    files = []
    if (wiki / "index.md").exists():
        files.append(("index", wiki / "index.md"))
    for f in sorted((wiki / "indexes").glob("*.md")) if (wiki / "indexes").exists() else []:
        files.append(("indexes/" + f.stem, f))
    counter = [0]

    def new(title, summary=""):
        counter[0] += 1
        return {"id": f"_g{counter[0]}", "title": title, "summary": summary, "items": [], "children": []}

    by_file, order_refs = {}, []
    for key, f in files:
        meta, body = split_fm(read(f))
        lines = body.splitlines()
        h1 = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), None)
        top = new(meta.get("title") or h1 or f.stem)
        stack, only_refs, any_item = [(1, top)], True, False
        for ln in lines:
            hm = re.match(r"(#{1,6})\s+(.*)", ln)
            if hm:
                level = len(hm.group(1))
                if level == 1:
                    continue
                while len(stack) > 1 and stack[-1][0] >= level:
                    stack.pop()
                g = new(hm.group(2).strip())
                stack[-1][1]["children"].append(g)
                stack.append((level, g))
                continue
            im = re.match(r"\s*[-*+]\s+(.*)", ln)
            if not im:
                continue
            lm = WIKILINK.search(im.group(1))
            if not lm:
                continue
            any_item = True
            summary = im.group(1)[lm.end():].strip().lstrip(":：—-– ").strip()
            target = lm.group(1).strip()
            if target.startswith("indexes/"):
                order_refs.append((target, summary))
                stack[-1][1]["items"].append({"state": "group", "ref": target, "t": lm.group(2) or target})
                continue
            only_refs = False
            pid = resolve(target, pages)
            if pid:
                if summary and not pages[pid]["s"]:
                    pages[pid]["s"] = summary
                stack[-1][1]["items"].append({"state": "resolved", "i": pid})
            else:
                stack[-1][1]["items"].append({"state": "unresolved", "t": lm.group(2) or target})
        by_file[key] = (top, only_refs and any_item)

    groups = []
    index_top, index_only_refs = by_file.get("index", (None, False))
    if index_top is not None and not index_only_refs:
        # index.md の h1 だけの包みは外し、その下の見出しをいちばん上のグループにする
        if not index_top["items"] and index_top["children"]:
            groups.extend(index_top["children"])
        else:
            groups.append(index_top)
    placed = set()
    for ref, summary in order_refs:
        if ref in by_file and ref not in placed:
            g = by_file[ref][0]
            g["summary"] = g["summary"] or summary
            groups.append(g)
            placed.add(ref)
    for key, (g, _o) in by_file.items():
        if key != "index" and key not in placed:
            groups.append(g)
    # グループへの行の名前を、そのグループの名前にする
    title_of = {k: v[0]["title"] for k, v in by_file.items()}
    id_of = {k: v[0]["id"] for k, v in by_file.items()}
    for g in walk(groups):
        for it in g["items"]:
            if it["state"] == "group":
                it["t"] = title_of.get(it["ref"], it["t"])
                it["g"] = id_of.get(it["ref"])
    listed = {it["i"] for g in walk(groups) for it in g["items"] if it["state"] == "resolved"}
    rest = [pid for pid in sorted(pages) if pid not in listed]
    if rest:
        g = new("索引にないページ", "index.md と indexes/ に載っていないページ。種類ごとに並べる")
        by_type = {}
        for pid in rest:
            by_type.setdefault(pages[pid]["y"], []).append(pid)
        for t in sorted(by_type):
            sub = new(TYPE_LABELS.get(t, t or "種類なし"))
            sub["items"] = [{"state": "resolved", "i": pid} for pid in by_type[t]]
            g["children"].append(sub)
        groups.append(g)
    for p in pages.values():
        if not p["s"]:
            p["s"] = p["lead"]
            p["s_from"] = "lead"
    # 件数と、グループの道（ページの所属）
    path_of = {}

    def count(g, trail):
        ids = {it["i"] for it in g["items"] if it["state"] == "resolved"}
        for it in g["items"]:
            if it["state"] == "resolved":
                path_of.setdefault(it["i"], trail + [g["title"]])
        for c in g["children"]:
            ids |= count(c, trail + [g["title"]])
        g["count"] = len(ids)
        return ids

    for g in groups:
        count(g, [])
    for pid, p in pages.items():
        p["gp"] = [t for t in path_of.get(pid, []) if t]
    return groups


def walk(groups):
    for g in groups:
        yield g
        yield from walk(g["children"])


# --- 描く ---

def esc(s) -> str:
    return html.escape(str(s))


def href(from_root: str, path: str) -> str:
    return from_root + "/".join(urllib.parse.quote(x) for x in path.split("/"))


def head(variant: str, root: str, title: str, name: str) -> str:
    return (f'<!doctype html>\n<html lang="ja" data-root="{root}" data-variant="{variant}">\n<head>\n'
            f'<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
            f'<meta name="referrer" content="no-referrer">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{esc(title)} · {esc(name)}</title>\n"
            f'<link rel="stylesheet" href="{root}assets/proto.css">\n</head>\n<body class="v-{variant}">\n'
            f'<nav id="_nav" aria-label="サイト">'
            f'<p id="_scope" class="scope scope-project">{esc(name)}</p>'
            f'<a class="nav-home" href="{root}index.html">索引</a>'
            f'<div id="_navbody"></div></nav>\n<main id="_main">\n')


def tail(root: str) -> str:
    return (f"</main>\n<script src=\"{root}data/nav.js\"></script>\n"
            f"<script src=\"{root}data/search.js\"></script>\n<script src=\"{root}assets/proto.js\"></script>\n"
            f"</body>\n</html>\n")


def badge(t: str) -> str:
    return f'<span class="badge t-{esc(t or "none")}">{esc(TYPE_LABELS.get(t, t or "種類なし"))}</span>'


def row_html(p: dict, root: str, cls="ix-row", extra="") -> str:
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p["g"])
    summ = f'<p class="ix-summary">{esc(p["s"])}</p>' if p["s"] else ""
    date = f'<time datetime="{esc(p["u"])}">{esc(p["u"])}</time>' if p["u"] else ""
    return (f'<li class="{cls}"{extra}><div class="ix-line"><a class="ix-title" href="{esc(href(root, p["p"]))}">'
            f'{esc(p["t"])}</a>{badge(p["y"])}{date}</div>{summ}'
            f'{"<div class=ix-tags>" + tags + "</div>" if tags else ""}</li>')


def index_a(groups, pages, root) -> str:
    total = len(pages)
    toc = "".join(f'<a class="toc-chip" href="#{g["id"]}">{esc(g["title"])}<span class="count">{g["count"]}</span></a>'
                  for g in groups)

    def section(g, depth):
        h = "h2" if depth == 0 else "h3"
        items = []
        for it in g["items"]:
            if it["state"] == "resolved":
                items.append(row_html(pages[it["i"]], root))
            elif it["state"] == "group":
                items.append(f'<li class="ix-row ix-grouplink"><a class="ix-title" href="#{esc(it.get("g") or "")}">'
                             f'{esc(it["t"])}</a></li>')
            else:
                items.append(f'<li class="ix-row"><span class="unresolved">{esc(it["t"])}</span>'
                             f'<span class="state">ページがない</span></li>')
        summary = f'<p class="group-summary">{esc(g["summary"])}</p>' if g["summary"] else ""
        lst = f'<ul class="ix-list">{"".join(items)}</ul>' if items else ""
        kids = "".join(section(c, depth + 1) for c in g["children"])
        return (f'<section class="ix-group depth-{depth}" id="{g["id"]}"><{h}>{esc(g["title"])}'
                f'<span class="count">{g["count"]}</span></{h}>{summary}{lst}{kids}</section>')

    return (f'<header class="ix-head"><h1>索引</h1><p class="ix-stats">{total} ページ · {len(groups)} グループ</p>'
            f'</header><nav class="ix-toc" aria-label="グループ">{toc}</nav>'
            + "".join(section(g, 0) for g in groups))


def index_b(groups, pages, root) -> str:
    order = []
    for g in groups:
        for gg in walk([g]):
            for it in gg["items"]:
                if it["state"] == "resolved" and it["i"] not in order:
                    order.append(it["i"])
    for pid in pages:
        if pid not in order:
            order.append(pid)
    # ページを含むグループの ID（どの深さも）。木のグループで一覧を絞るのに使う
    groups_of = {}

    def mark(g, trail):
        trail = trail + [g["id"]]
        for it in g["items"]:
            if it["state"] == "resolved":
                groups_of.setdefault(it["i"], set()).update(trail)
        for c in g["children"]:
            mark(c, trail)

    for g in groups:
        mark(g, [])
    rows = []
    for n, pid in enumerate(order):
        p = pages[pid]
        gp = " › ".join(p["gp"])
        extra = (f' data-type="{esc(p["y"])}" data-tags="{esc(chr(31).join(p["g"]))}" data-updated="{esc(p["u"])}"'
                 f' data-title="{esc(p["t"])}" data-order="{n}"'
                 f' data-groups="{esc(" ".join(sorted(groups_of.get(pid, ()))))}"')
        r = row_html(p, root, "fx-row", extra)
        if gp:
            r = r.replace('<div class="ix-line">', f'<div class="fx-path">{esc(gp)}</div><div class="ix-line">', 1)
        rows.append(r)
    return (f'<header class="ix-head"><h1>索引</h1><p class="ix-stats">{len(pages)} ページ</p></header>'
            f'<div id="_filters" class="fx-bar"></div>'
            f'<p id="_count" class="fx-count" aria-live="polite">{len(pages)} 件</p>'
            f'<ul id="_list" class="fx-list">{"".join(rows)}</ul>')


def index_c(groups, pages, root) -> str:
    recent = sorted((p for p in pages.values() if p["u"]), key=lambda p: (p["u"], p["t"]), reverse=True)[:8]
    cards = []
    for g in groups:
        subs = " · ".join(esc(c["title"]) for c in g["children"][:5])
        cards.append(f'<a class="card" href="#{g["id"]}"><strong>{esc(g["title"])}</strong>'
                     f'<span class="card-count">{g["count"]} ページ</span>'
                     f'{"<span class=card-sub>" + subs + "</span>" if subs else ""}</a>')

    def compact(g, depth):
        items = "".join(f'<li><a href="{esc(href(root, pages[it["i"]]["p"]))}">{esc(pages[it["i"]]["t"])}</a></li>'
                        for it in g["items"] if it["state"] == "resolved")
        kids = "".join(compact(c, depth + 1) for c in g["children"])
        inner = (f'<ul class="compact">{items}</ul>' if items else "") + kids
        if depth == 0:
            return (f'<details class="all-group" id="{g["id"]}"><summary>{esc(g["title"])}'
                    f'<span class="count">{g["count"]}</span></summary>{inner}</details>')
        return f'<div class="all-sub"><h4>{esc(g["title"])}<span class="count">{g["count"]}</span></h4>{inner}</div>'

    return (f'<div class="hero"><h1>索引</h1><p class="ix-stats">{len(pages)} ページから探す</p>'
            f'<div id="_herosearch"></div><noscript><p class="state">検索には JavaScript が要る。下の一覧から探せる。</p>'
            f'</noscript></div>'
            f'<section id="_results" class="results" hidden></section>'
            f'<div id="_browse"><section class="recent"><h2>最近更新したページ</h2>'
            f'<ul class="ix-list">{"".join(row_html(p, root) for p in recent)}</ul></section>'
            f'<section><h2>グループ</h2><div class="card-grid">{"".join(cards)}</div></section>'
            f'<section><h2>すべてのページ</h2>{"".join(compact(g, 0) for g in groups)}</section></div>')


def nav_data(groups, pages) -> dict:
    def conv(g):
        items = []
        for it in g["items"]:
            if it["state"] == "resolved":
                p = pages[it["i"]]
                items.append({"state": "resolved", "i": p["i"], "p": p["p"], "t": p["t"]})
            elif it["state"] == "group":
                items.append({"state": "group", "g": it.get("g"), "t": it["t"]})
            else:
                items.append({"state": "unresolved", "t": it["t"]})
        return {"id": g["id"], "title": g["title"], "count": g["count"], "items": items,
                "children": [conv(c) for c in g["children"]]}
    return {"groups": [conv(g) for g in groups]}


def search_data(pages) -> dict:
    return {"fields": ["p", "i", "t", "s", "y", "g", "h", "u", "gp"],
            "rows": [[p["p"], p["i"], p["t"], p["s"], p["y"], p["g"], p["h"], p["u"], p["gp"]]
                     for p in sorted(pages.values(), key=lambda p: p["i"])]}


def build(variant: str, wiki: Path, exported: Path, out: Path, name: str) -> None:
    pages = load_pages(wiki, exported)
    groups = load_groups(wiki, pages)
    if out.exists():
        shutil.rmtree(out)
    for f in ("proto.css", "proto.js"):
        write(out / "assets" / f, read(HERE / "assets" / f))
    write(out / "data" / "nav.js", js_data("PROTO_NAV", nav_data(groups, pages)))
    write(out / "data" / "search.js", js_data("WIKI_SEARCH", search_data(pages)))
    body = {"a": index_a, "b": index_b, "c": index_c, "d": index_b}[variant](groups, pages, "")
    write(out / "index.html", head(variant, "", "索引", name) + body + "\n" + tail(""))
    for p in pages.values():
        write(out / p["p"], head(variant, p["root"], p["t"], name) + p["main"] + tail(p["root"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wiki")
    ap.add_argument("exported")
    ap.add_argument("out")
    ap.add_argument("--name", default="プロジェクトの wiki")
    args = ap.parse_args()
    for v in VARIANTS:
        build(v, Path(args.wiki), Path(args.exported), Path(args.out) / v, args.name)
    print("作った:", ", ".join(str(Path(args.out) / v) for v in VARIANTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
