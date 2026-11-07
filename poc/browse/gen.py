# /// script
# requires-python = ">=3.10"
# dependencies = ["markdown-it-py==3.0.0"]
# ///
"""ADR-0010 の中核と静的 HTML の生成器の試作。配布対象ではない。

wiki 0.6.0（36a4089）の lint の collect_pages、clean_link_target、resolve_link をそのまま使い、
画面の契約（相対リンク、classic な <script src>、共有の nav.js、data/*.js、CSP）どおりに書き出す。

使い方: uv run --script gen.py <wiki のルート> <出力先> [--raw basename|full|none] [--name-limit 200]
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse
from collections import defaultdict
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "out" / "wiki-src" / "skills" / "info-hive" / "scripts"))

import wiki_lint  # noqa: E402
from markdown_it import MarkdownIt  # noqa: E402

PROTOCOL_VERSION = 1
WIKILINK_FULL_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "base-uri 'none'; form-action 'none'")
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
WINDOWS_BAD = set('<>:"\\|?*')


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


SUFFIX_RE = re.compile(r"~[0-9a-f]{8}$")


class NameCollision(Exception):
    """接尾辞を付けても出力のパスが重なった。上書きせずに生成を止める。"""


def safe_component(part: str, key: str, limit: int, is_dir: bool) -> str:
    """1 つの名前の要素を、どの OS でも作れる名前にする。読める名前を残し、必要なときだけ接尾辞を付ける。

    key は、この要素までの識別子（ディレクトリならそのディレクトリのパス、ページなら識別子）。
    接尾辞をこの key だけから決めるので、ほかのページを足しても名前は変わらない。
    """
    changed = False
    out = []
    for ch in part:
        if ch in WINDOWS_BAD or ord(ch) < 0x20:
            out.append("_")
            changed = True
        else:
            out.append(ch)
    name = "".join(out)
    if name.rstrip(" .") != name:
        name = name.rstrip(" .")
        changed = True
    if name.split(".")[0].rstrip(" ").upper() in WINDOWS_RESERVED:
        # 接尾辞は末尾に付くので、最初の . より前が予約名のままになる。先頭に _ を付ける。
        name = "_" + name
        changed = True
    if SUFFIX_RE.search(name):
        # 元の名前が接尾辞の形で終わるときも付ける。付けた名前と元の名前が重ならないようにする。
        changed = True
    if is_dir and name.lower().endswith(".html"):
        # ページ foo の出力 foo.html と、ディレクトリ foo.html が同じ場所を取り合わないようにする。
        changed = True
    # .html と接尾辞（~ と 8 桁）を足しても上限に収まるようにする。上限は UTF-8 のバイト数で数える。
    budget = limit - len(".html") - 9
    if len(name.encode("utf-8")) > budget:
        name = name.encode("utf-8")[:budget].decode("utf-8", errors="ignore")
        changed = True
    if changed:
        name = f"{name}~{short_hash(key)}"
    return name


def export_name(page_id: str, limit: int) -> str:
    """ページの識別子（NFC の POSIX の相対パスから .md を除いたもの）から、出力のパスを決める唯一の関数。"""
    parts = page_id.split("/")
    out = [safe_component(p, "/".join(parts[:i + 1]) + ("/" if i < len(parts) - 1 else ""), limit,
                          is_dir=i < len(parts) - 1)
           for i, p in enumerate(parts)]
    return "/".join(out) + ".html"


def check_unique(names: dict) -> None:
    """出力のパスが、大文字と小文字を同一視しても重ならず、ファイルとディレクトリが同じ場所を取らないことを確かめる。"""
    files = defaultdict(list)
    dirs = set()
    for pid, name in names.items():
        files[name.casefold()].append(pid)
        parts = name.casefold().split("/")
        dirs.update("/".join(parts[:i]) for i in range(1, len(parts)))
    dup = {k: v for k, v in files.items() if len(v) > 1}
    clash = sorted(set(files) & dirs)
    if dup or clash:
        raise NameCollision(json.dumps({"same_file": dup, "file_and_dir": clash}, ensure_ascii=False))


def heading_id(text: str, used: dict) -> str:
    base = nfc(text).strip().lower()
    base = re.sub(r"[\s]+", "-", base)
    base = re.sub(r"[!-,./:-@\[-^`{-~]", "", base) or "section"
    n = used.get(base, 0)
    used[base] = n + 1
    return base if n == 0 else f"{base}-{n}"


def rel_href(from_path: str, to_path: str) -> str:
    """出力のパスどうしの相対の href。名前の要素ごとにパーセントエンコードする。"""
    src = PurePosixPath(from_path).parent.parts
    dst = PurePosixPath(to_path).parts
    common = 0
    while common < min(len(src), len(dst) - 1) and src[common] == dst[common]:
        common += 1
    up = [".."] * (len(src) - common)
    rest = list(dst[common:])
    return "/".join(urllib.parse.quote(p, safe="") if p != ".." else p for p in up + rest) or "."


def root_prefix(path: str) -> str:
    depth = len(PurePosixPath(path).parts) - 1
    return "../" * depth


def js_data(name: str, value) -> str:
    """<script src> で読む data/*.js。</script>、U+2028、U+2029 をエスケープする。"""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    text = text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return f"window.{name}={text};\n"


class Core:
    def __init__(self, root: Path, name_limit: int):
        self.root = root
        self.name_limit = name_limit
        raw_pages = [p for p in wiki_lint.collect_pages(root) if "read_error" not in p]
        self.pages = {}
        for p in sorted(raw_pages, key=lambda x: x["rel_path"]):
            pid = p["rel_path"][:-3] if p["rel_path"].lower().endswith(".md") else p["rel_path"]
            self.pages[pid] = p
        self.slug_ids = defaultdict(list)
        self.by_path = {}
        for pid, p in self.pages.items():
            self.slug_ids[p["slug"]].append(pid)
            self.by_path[pid] = p["slug"]
        self.out_name = self._names()
        self.md = MarkdownIt("commonmark", {"html": False}).enable("table")
        self.headings = {pid: self._headings(self.md, p["body"]) for pid, p in self.pages.items()}

    def _names(self) -> dict:
        names = {pid: export_name(pid, self.name_limit) for pid in self.pages}
        # 大文字と小文字だけが違う出力は、NTFS と APFS で同じファイルになる。衝突した全員に接尾辞を付ける。
        folded = defaultdict(list)
        for pid, name in names.items():
            folded[name.casefold()].append(pid)
        self.case_collisions = [sorted(g) for g in folded.values() if len(g) > 1]
        for group in self.case_collisions:
            for pid in group:
                names[pid] = names[pid][:-5] + f"~{short_hash(pid)}.html"
        check_unique(names)
        return names

    @staticmethod
    def _headings(md: MarkdownIt, body: str) -> list:
        """見出しを、描くときと同じ markdown-it の解析から取る（ATX と Setext の両方）。"""
        used = {}
        found = []
        tokens = md.parse(body)
        for i, tok in enumerate(tokens):
            if tok.type == "heading_open":
                text = nfc(tokens[i + 1].content)
                found.append((text, heading_id(text, used)))
        return found

    def resolve(self, raw: str) -> dict:
        """wikilink を {state, id, anchor} にする。state は resolved、unresolved、ambiguous。"""
        target = wiki_lint.clean_link_target(raw)
        anchor = nfc(raw.split("#", 1)[1]).strip() if "#" in raw else None
        slug = wiki_lint.resolve_link(raw, self.by_path, set(self.slug_ids))
        if slug is None:
            return {"state": "unresolved", "target": target}
        if "/" in target:
            pid = target
        else:
            ids = self.slug_ids[slug]
            if len(ids) > 1:
                return {"state": "ambiguous", "target": target, "candidates": ids}
            pid = ids[0]
        result = {"state": "resolved", "id": pid}
        if anchor:
            match = next((hid for text, hid in self.headings[pid] if text == anchor), None)
            result["anchor"] = match
            if match is None:
                result["missing_heading"] = anchor
        return result


def render_markdown(md: MarkdownIt, body: str, heading_ids: list) -> str:
    tokens = md.parse(body)
    i = 0
    for tok in tokens:
        if tok.type == "heading_open" and i < len(heading_ids):
            tok.attrSet("id", heading_ids[i][1])
            i += 1
    return md.renderer.render(tokens, md.options, {})


def build(root: Path, out: Path, raw_mode: str, name_limit: int) -> dict:
    started = time.perf_counter()
    core = Core(root, name_limit)
    md = core.md
    generation = hashlib.sha256(
        "".join(f"{pid}\0{p['body']}" for pid, p in core.pages.items()).encode("utf-8")).hexdigest()[:16]
    out.mkdir(parents=True, exist_ok=True)

    links = {}
    inbound = defaultdict(set)
    diagnostics = []
    for pid, p in core.pages.items():
        resolved = []
        for m in WIKILINK_FULL_RE.finditer(p["body"]):
            r = core.resolve(m.group(1))
            r["raw"] = m.group(0)
            r["label"] = (m.group(2) or m.group(1)).strip()
            resolved.append(r)
            if r["state"] == "resolved":
                if r["id"] != pid:
                    inbound[r["id"]].add(pid)
                if r.get("missing_heading"):
                    diagnostics.append({"page": pid, "kind": "missing_heading", "link": m.group(1)})
            else:
                diagnostics.append({"page": pid, "kind": r["state"], "link": m.group(1)})
        links[pid] = resolved

    def title(pid):
        return str(core.pages[pid]["meta"].get("title") or core.pages[pid]["slug"])

    nav = {"protocol_version": PROTOCOL_VERSION, "generation": generation,
           "pages": [[core.out_name[pid], title(pid), str(core.pages[pid]["meta"].get("type") or "")]
                     for pid in core.pages]}
    search = {"generation": generation, "rows": []}
    for pid, p in core.pages.items():
        meta = p["meta"]
        tags = meta.get("tags") or []
        search["rows"].append([core.out_name[pid], title(pid), str(meta.get("summary") or ""),
                               [str(t) for t in tags] if isinstance(tags, list) else [str(tags)],
                               [h for h, _ in core.headings[pid]]])
    capabilities = {"protocol_version": PROTOCOL_VERSION, "generation": generation,
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "search": "embedded", "rag": False, "multi_wiki": False, "live_reload": False,
                    "raw": raw_mode}

    (out / "data").mkdir(exist_ok=True)
    (out / "nav.js").write_text(js_data("WIKI_NAV", nav), encoding="utf-8", newline="\n")
    (out / "data" / "search.js").write_text(js_data("WIKI_SEARCH", search), encoding="utf-8", newline="\n")
    (out / "data" / "capabilities.js").write_text(js_data("WIKI_CAPABILITIES", capabilities), encoding="utf-8",
                                                    newline="\n")
    (out / "data" / "diagnostics.js").write_text(js_data("WIKI_DIAGNOSTICS", diagnostics), encoding="utf-8",
                                                   newline="\n")
    for asset in ("app.js", "style.css"):
        (out / asset).write_bytes((HERE / "static" / asset).read_bytes())

    for pid, p in core.pages.items():
        path = core.out_name[pid]
        counter = iter(range(len(links[pid])))
        placeholders = {}

        def swap(m):
            n = next(counter)
            key = f"\ue000{n}\ue001"
            placeholders[key] = links[pid][n]
            return key

        body = WIKILINK_FULL_RE.sub(swap, p["body"])
        body_html = render_markdown(md, body, core.headings[pid])
        for key, r in placeholders.items():
            label = html.escape(r["label"])
            if r["state"] == "resolved":
                href = rel_href(path, core.out_name[r["id"]]) + (f"#{urllib.parse.quote(r['anchor'])}" if r.get("anchor") else "")
                cls = "wl" + (" wl-missing-heading" if r.get("missing_heading") else "")
                rep = f'<a class="{cls}" href="{html.escape(href)}">{label}</a>'
            elif r["state"] == "ambiguous":
                rep = f'<span class="wl wl-ambiguous" title="候補: {html.escape(", ".join(r["candidates"]))}">{label}</span>'
            else:
                rep = f'<span class="wl wl-unresolved" title="未作成のページ">{label}</span>'
            body_html = body_html.replace(key, rep)
        page_html = render_page(core, pid, path, body_html, inbound[pid], links[pid], raw_mode, title)
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_html, encoding="utf-8", newline="\n")

    (out / "index.html").write_text(render_index(core, title), encoding="utf-8", newline="\n")
    elapsed = time.perf_counter() - started
    nav_bytes = (out / "nav.js").stat().st_size
    search_bytes = (out / "data" / "search.js").stat().st_size
    item_sizes = [len(json.dumps(item, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) + 1
                  for item in nav["pages"]]
    report = {
        "wiki": root.as_posix(), "pages": len(core.pages), "seconds": round(elapsed, 3),
        "nav_js_bytes": nav_bytes, "search_js_bytes": search_bytes,
        "nav_item_bytes": {"mean": round(sum(item_sizes) / max(1, len(item_sizes)), 1),
                           "max": max(item_sizes, default=0), "min": min(item_sizes, default=0)},
        "longest_component_bytes": max((len(part.encode("utf-8")) for n in core.out_name.values()
                                        for part in n.split("/")), default=0),
        "renamed": {pid: name for pid, name in core.out_name.items() if name != pid + ".html"},
        "case_collisions": core.case_collisions, "diagnostics": diagnostics,
    }
    # 生成の記録は Wiki の絶対パスを含むので、出力（持ち運ぶ生成物）の中には置かず、隣に書く。
    stale = out / "data" / "build-report.json"
    if stale.exists():
        stale.unlink()
    report["absolute_path_leaks"] = scan_leaks(out, [root.as_posix(), str(root)])
    Path(str(out) + ".build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                     encoding="utf-8", newline="\n")
    return report


def scan_leaks(out: Path, needles: list) -> list:
    """出力の中に、Wiki のルートの絶対パスが残っていないかを調べる。"""
    found = []
    for path in out.rglob("*"):
        if path.is_file():
            text = path.read_bytes().decode("utf-8", errors="replace")
            for n in needles:
                if n and (n in text or n.replace("/", r"\/") in text):
                    found.append(path.relative_to(out).as_posix())
                    break
    return sorted(found)


def head(prefix: str, title: str) -> str:
    return f"""<!doctype html>
<html lang="ja" data-root="{prefix}">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
<nav id="nav"><noscript><a href="{prefix}index.html">索引へ</a></noscript></nav>
<main>
"""


def tail(prefix: str) -> str:
    return f"""</main>
<script src="{prefix}nav.js"></script>
<script src="{prefix}data/capabilities.js"></script>
<script src="{prefix}app.js"></script>
</body>
</html>
"""


def render_raw(raw: str, sha: str | None, mode: str) -> str:
    if mode == "none":
        return ""
    is_abs = bool(re.match(r"^([A-Za-z]:/|/)", raw))
    if not is_abs:
        return f"<code>{html.escape(raw)}</code>"
    if mode == "full":
        href = "file:///" + urllib.parse.quote(raw.lstrip("/"), safe="/:")
        return f'<a class="raw" href="{html.escape(href)}">{html.escape(raw)}</a>'
    base = PurePosixPath(raw).name
    tail_sha = f"（SHA-256 {html.escape(sha[:12])}…）" if sha else ""
    return f"<code>{html.escape(base)}</code>{tail_sha}"


def render_page(core: Core, pid, path, body_html, inbound, links, raw_mode, title) -> str:
    prefix = root_prefix(path)
    meta = core.pages[pid]["meta"]
    rows = []
    for key in ("type", "tags", "summary", "updated"):
        if meta.get(key):
            value = meta[key]
            value = "、".join(map(str, value)) if isinstance(value, list) else str(value)
            rows.append(f"<tr><th>{key}</th><td>{html.escape(value)}</td></tr>")
    if meta.get("raw"):
        rows.append(f"<tr><th>raw</th><td>{render_raw(str(meta['raw']), meta.get('raw_sha256'), raw_mode)}</td></tr>")
    back = "".join(f'<li><a href="{html.escape(rel_href(path, core.out_name[b]))}">{html.escape(title(b))}</a></li>'
                   for b in sorted(inbound))
    unresolved = [l for l in links if l["state"] != "resolved" or l.get("missing_heading")]
    diag = "".join(f"<li>{html.escape(l['raw'])}: {html.escape(l['state'] if l['state'] != 'resolved' else 'missing_heading')}</li>"
                   for l in unresolved)
    return (head(prefix, title(pid))
            + f'<article data-page-id="{html.escape(pid)}">\n<table class="meta">{"".join(rows)}</table>\n{body_html}</article>\n'
            + f'<section id="backlinks"><h2>被リンク</h2><ul>{back}</ul></section>\n'
            + (f'<section id="diagnostics"><h2>診断</h2><ul>{diag}</ul></section>\n' if diag else "")
            + tail(prefix))


def render_index(core: Core, title) -> str:
    items = "".join(f'<li><a href="{html.escape(rel_href("index.html", core.out_name[pid]))}">{html.escape(title(pid))}</a></li>'
                    for pid in core.pages)
    return head("", "索引") + f"<h1>索引</h1><ul id=\"all-pages\">{items}</ul>\n" + tail("")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wiki")
    parser.add_argument("out")
    parser.add_argument("--raw", choices=["basename", "full", "none"], default="basename")
    parser.add_argument("--name-limit", type=int, default=200)
    args = parser.parse_args(argv)
    report = build(Path(args.wiki).resolve(), Path(args.out).resolve(), args.raw, args.name_limit)
    summary = {k: v for k, v in report.items() if k not in ("diagnostics", "renamed")}
    summary["renamed"] = len(report["renamed"])
    summary["diagnostics"] = len(report["diagnostics"])
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
