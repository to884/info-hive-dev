"""wiki プラグインの README と関連資料を静的 HTML に変換する。"""

import argparse
from html import escape
from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import unquote, urlsplit

from manual_presentation import decorate


PAGES = {
    "README.md": "index.html",
    "docs/agents.md": "agents.html",
    "docs/search.md": "search.html",
    "docs/graph.md": "graph.html",
    "docs/evolution.md": "evolution.html",
    "docs/decisions.md": "decisions.html",
    "docs/workflows.md": "workflows.html",
    "docs/upgrade.md": "upgrade.html",
    "UPSTREAM.md": "upstream.html",
}
RUNTIME = "skills/info-hive/scripts"
VENDOR = f"{RUNTIME}/_vendor"
BROWSE = f"{RUNTIME}/browse_assets"
RELATED = {
    "LICENSE": "licenses.html#project-license",
    f"{VENDOR}/README.md": "licenses.html#markdown-parser",
    f"{VENDOR}/licenses/": "licenses.html#markdown-parser-licenses",
    f"{BROWSE}/README.md": "licenses.html#browse-assets",
    f"{BROWSE}/licenses/": "licenses.html#browse-licenses",
    "docs/index.md": "index.html#toc",
    "docs/html/index.html": "index.html#toc",
    "docs/html/howto-upgrade-wiki.html": "howto-upgrade-wiki.html",
    "docs/commands.md": "commands.html",
    "docs/getting-started.md": "tutorial-first-wiki.html",
    # 利用者向けの MCP サーバーは HTML で編集し、配布するスキルの文体は別に保つ。
    "skills/info-hive/references/mcp-server.md": "mcp-server.html",
    "docs/commands.md#wikigraph-action": "commands.html#wikigraph",
    "docs/commands.md#wikiinit": "commands.html#wikiinit",
    "docs/commands.md#wikistats": "commands.html#wikistats",
    "https://docs.astral.sh/uv/getting-started/installation/": "howto-prepare.html#uv",
    "https://github.com/to884/info-hive-rag": "explanation-how-wiki-works.html#rag",
}

INSTALLATION_GUIDE = """
<p>Windows 11 の Claude デスクトップアプリで、Code タブから wiki を入れます。</p>
<ol>
  <li>Claude と、Git・uv・Python 3.12・Visual C++ ランタイムを用意します。</li>
  <li>Code タブで info-hive のマーケットプレイスを追加します。</li>
  <li>ディレクトリの Wiki を追加し、<code>/wiki:help</code> で導入を確かめます。</li>
</ol>
<p><a class="fui-Link" data-inline href="tutorial-install.html">Windows 11 の導入手順</a>は、VM で確認した構成と操作をもとにしています。</p>
<p>Codex や Claude Code の CLI を使う場合は、<a class="fui-Link" data-inline href="agents.html#インストールのコマンド例">エージェント別の導入方法</a>を参照できます。</p>
"""


def heading_id(source, slug):
    return f"readme-{slug}" if source == "README.md" else slug


def section_bounds(tokens, title):
    heading_indexes = [index for index, token in enumerate(tokens) if token.type == "heading_open" and token.tag == "h2"]
    headings = [tokens[index + 1].content for index in heading_indexes]
    if title not in headings:
        return None
    section = headings.index(title)
    end = heading_indexes[section + 1] if section + 1 < len(heading_indexes) else len(tokens)
    return heading_indexes[section], end


def markdown_tokens(parser, path, source):
    markdown = path.read_text(encoding="utf-8")
    markdown = re.sub(r"\A---\n.*?\n---\n", "", markdown, count=1, flags=re.S)
    markdown = re.sub(r"\A<!-- Adapted from:[^\n]*-->\n", "", markdown, count=1)
    tokens = parser.parse(markdown)
    if source == "README.md":
        development = section_bounds(tokens, "開発への参加")
        if development:
            start, end = development
            del tokens[start:end]
        installation = section_bounds(tokens, "インストール")
        if not installation:
            raise ValueError("README.md に「インストール」見出しがありません。")
        start, end = installation
        del tokens[start + 3:end]
    headings = {}
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        label = "".join(child.content for child in tokens[index + 1].children)
        slug = re.sub(r"[^\w\-\s]", "", label.lower()).replace(" ", "-")
        unique = slug
        suffix = 1
        while unique in headings:
            unique = f"{slug}-{suffix}"
            suffix += 1
        token.attrSet("id", heading_id(source, unique))
        token.attrSet("class", {
            "h1": "fui-Title1", "h2": "fui-Subtitle1", "h3": "fui-Subtitle2",
        }.get(token.tag, "fui-Body1Strong"))
        headings[unique] = (token.tag, label)
    return tokens, headings


def resolve_link(source, href, headings):
    if href in RELATED:
        return RELATED[href]
    url = urlsplit(href)
    if url.scheme or url.netloc:
        # 外部の参照名は残し、利用者向けの導線を HTML 内に保つ。
        return None
    path = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(url.path))) if url.path else source
    fragment = unquote(url.fragment)
    if path in PAGES and (not fragment or fragment in headings[path]):
        suffix = f"#{heading_id(path, fragment)}" if fragment else ""
        return PAGES[path] + suffix
    key = f"{path}#{fragment}" if fragment else path
    destination = RELATED.get(key) or RELATED.get(key + "/")
    if not destination and source == "README.md":
        raise ValueError(f"{source} のリンク先に対応する HTML がありません: {href}")
    return destination


def render(parser, tokens, source, headings):
    for token in tokens:
        if source == "README.md" and token.type in ("heading_open", "heading_close"):
            token.tag = "h" + str(min(int(token.tag[1:]) + 1, 6))
            if token.type == "heading_open":
                token.attrSet("class", {"h2": "fui-Subtitle1", "h3": "fui-Subtitle2"}.get(token.tag, "fui-Body1Strong"))
        if token.type in ("table_open", "thead_open", "tbody_open", "tr_open", "th_open", "td_open"):
            token.attrSet("class", {
                "table_open": "fui-Table", "thead_open": "fui-TableHeader",
                "tbody_open": "fui-TableBody", "tr_open": "fui-TableRow",
                "th_open": "fui-TableHeaderCell", "td_open": "fui-TableCell",
            }[token.type])
            token.attrs.pop("style", None)
            if token.type == "th_open":
                token.attrSet("scope", "col")
        if token.type != "inline":
            continue
        # Markdown のリンクには入れ子がない。リンク先のないラベルも元の強調やコードを保つ。
        for child in token.children:
            if child.type == "link_open":
                destination = resolve_link(source, child.attrGet("href"), headings)
                if destination:
                    child.attrSet("href", destination)
                    child.attrSet("class", "fui-Link")
                    child.attrSet("data-inline", "")
                else:
                    child.tag = "span"
                    child.attrs.clear()
            elif child.type == "link_close":
                child.tag = "a" if destination else "span"
    html = parser.renderer.render(tokens, parser.options, {})
    return html.replace(
        '<table class="fui-Table">',
        '<div class="table-scroll" role="region" aria-label="表" tabindex="0">\n<table class="fui-Table">',
    ).replace("</table>", "</table>\n</div>")


def replace_block(html, name, body):
    begin = f"<!-- {name}:start -->"
    end = f"<!-- {name}:end -->"
    before, old = html.split(begin, 1)
    _, after = old.split(end, 1)
    return f"{before}{begin}\n{body.rstrip()}\n      {end}{after}"


def related_page(title, body):
    return f"""<!doctype html>
<html lang="ja" data-theme="auto">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | info-hive</title>
  <link rel="stylesheet" href="assets/fluent2.css">
  <link rel="stylesheet" href="assets/manual.css">
  <link rel="stylesheet" href="assets/manual-print.css" media="print">
</head>
<body class="fui-FluentProvider">
  <a class="skip-link fui-Link" href="#main">本文へ移動</a>
  <header class="site-header">
    <div class="shell"><a class="site-name fui-Link" href="index.html">info-hive</a></div>
  </header>
  <div class="shell reading-layout">
    <nav class="contents" aria-label="目次">
      <a class="fui-Link" href="index.html#toc">文書の目次へ戻る</a>
    </nav>
    <main class="page-content readme-content" id="main" tabindex="-1">
{body.rstrip()}
    </main>
  </div>
</body>
</html>
"""


def license_text(files):
    sections = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        text = "\n".join(line.rstrip(" \t") for line in text.splitlines()).rstrip()
        sections.append(f"<h3>{escape(path.name)}</h3>\n<pre>{escape(text)}</pre>")
    return "\n".join(sections)


def render_licenses(parser, repo, headings):
    sections = ['<h1 class="fui-Title1">ライセンスと同梱物</h1>']
    sections.append('<h2 id="project-license">info-hive</h2>')
    sections.append(license_text([repo / "LICENSE"]))
    for source, slug, label in (
        (VENDOR, "markdown-parser", "Markdown 解析器"),
        (BROWSE, "browse", "閲覧画面"),
    ):
        path = f"{source}/README.md"
        tokens, _ = markdown_tokens(parser, repo / path, path)
        for token in tokens:
            if token.type in ("heading_open", "heading_close"):
                token.tag = "h" + str(min(int(token.tag[1:]) + 1, 6))
                if token.type == "heading_open":
                    token.attrSet("id", slug + "-" + token.attrGet("id"))
        tokens[0].attrSet("id", slug if slug == "markdown-parser" else "browse-assets")
        sections.append(render(parser, tokens, path, headings))
        sections.append(f'<h2 id="{slug}-licenses">{label}のライセンス</h2>')
        sections.append(license_text(sorted((repo / source / "licenses").iterdir())))
    return related_page("ライセンスと同梱物", "\n".join(sections))


def main():
    sys.stderr.reconfigure(encoding="utf-8")
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("plugin_root", type=Path, help="info-hive-wiki の作業ツリー")
    repo = cli.parse_args().plugin_root.resolve()
    output_dir = repo / "docs" / "html"
    sys.path.insert(0, str(repo / VENDOR))
    from markdown_it import MarkdownIt

    parser = MarkdownIt("commonmark", {"html": False}).enable("table")
    documents = {source: markdown_tokens(parser, repo / source, source) for source in PAGES}
    headings = {source: document[1] for source, document in documents.items()}
    generated = {}
    for source, output in PAGES.items():
        path = output_dir / output
        try:
            tokens = documents[source][0]
            if source == "README.md":
                start, _ = section_bounds(tokens, "インストール")
                start += 3
                body = render(parser, tokens[:start], source, headings) + INSTALLATION_GUIDE
                body += render(parser, tokens[start:], source, headings)
            else:
                body = render(parser, tokens, source, headings)
        except ValueError as error:
            cli.error(str(error))
        if source == "README.md":
            items = [
                f'  <li><a class="fui-Link" data-inline href="#{escape(heading_id(source, slug))}">{escape(label)}</a></li>'
                for slug, (tag, label) in headings[source].items()
                if tag == "h2"
            ]
            html = path.read_text(encoding="utf-8")
            html = replace_block(html, "readme-toc", "<ul>\n" + "\n".join(items) + "\n</ul>")
            html = replace_block(html, "readme-content", body)
        else:
            _, title = next(iter(headings[source].values()))
            html = related_page(title, body)
        generated[path] = html
    generated[output_dir / "licenses.html"] = render_licenses(parser, repo, headings)
    for path in output_dir.glob("*.html"):
        if path not in generated:
            generated[path] = path.read_text(encoding="utf-8")
    for path, html in generated.items():
        output = decorate(path.name, html)
        if not path.exists() or output != path.read_text(encoding="utf-8"):
            path.write_text(output, encoding="utf-8", newline="")


if __name__ == "__main__":
    main()
