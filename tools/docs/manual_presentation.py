"""利用者向け HTML に概要図とコード例の補助を加える。"""

from html import escape
import re


OVERVIEWS = {
    "index.html": ("groups", (
        ("資料を取り込む", "PDF・Web・会話"),
        ("根拠を探す", "検索・出典・関連ページ"),
        ("wiki を保つ", "点検・更新・経験の記録"),
    )),
    "tutorial-install.html": ("flow", (
        ("事前準備", "Claude と必要なツール"),
        ("Wiki を追加", "Code のマーケットプレイス"),
        ("導入を確認", "/wiki:help で一覧を表示"),
    )),
    "tutorial-first-wiki.html": ("flow", (
        ("wiki を作る", "練習フォルダーで初期化"),
        ("味噌を取り込む", "原本から要約を作る"),
        ("質問する", "出典のある答えを確認"),
    )),
    "tutorial-second-source.html": ("flow", (
        ("醤油を取り込む", "2 本目の資料を追加"),
        ("つながりを見る", "麹から両方の資料へ"),
        ("wiki を点検", "リンク切れや孤立を確認"),
    )),
    "howto-prepare.html": ("groups", (
        ("コマンドを確認", "Git・uv・Python"),
        ("uv を入れる", "使う OS の手順を選ぶ"),
        ("通信を整える", "組織の証明書を使う"),
    )),
    "howto-troubleshoot.html": ("flow", (
        ("接続を確認", "/mcp から再接続"),
        ("起動を診断", "終了コードとログを見る"),
        ("環境を直す", "Python・DLL・証明書"),
    )),
    "howto-update.html": ("flow", (
        ("マーケットプレイス", "アップデートを確認"),
        ("Wiki プラグイン", "導入済みの版を確認"),
        ("手元の wiki", "必要に応じてアップグレード"),
    )),
    "howto-cowork.html": ("flow", (
        ("Wiki を入れる", "Cowork のプラグイン"),
        ("フォルダーを選ぶ", "ローカルの資料を開く"),
        ("接続を確かめる", "ページ数を確認"),
    )),
    "howto-user-wiki.html": ("flow", (
        ("保存先を作る", "/wiki:init --user"),
        ("場所を伝える", "アプリの指示に追記"),
        ("別の作業から使う", "同じ wiki を参照"),
    )),
    "howto-web-page.html": ("flow", (
        ("URL を指定", "取り込みを依頼"),
        ("本文を保存", "Markdown の原本を作る"),
        ("変更を承認", "原本と要約を確認"),
    )),
    "commands.html": ("groups", (
        ("作る・取り込む", "init・ingest"),
        ("調べる・点検する", "query・browse・lint など"),
        ("保つ・改善する", "upgrade・learn・evolve"),
    )),
    "explanation-how-wiki-works.html": ("flow", (
        ("原本", "raw/ に保管"),
        ("wiki のページ", "要約・出典・リンク"),
        ("質問と答え", "索引や検索で根拠を探す"),
    )),
    "workflows.html": ("groups", (
        ("取り込む", "資料からページを作る"),
        ("質問する", "ページから根拠を探す"),
        ("点検する", "構造と内容を確認"),
    )),
    "search.html": ("flow", (
        ("検索語", "対象や期間を絞る"),
        ("照合", "語彙と意味の結果を統合"),
        ("根拠", "一致した節を見つける"),
    )),
    "graph.html": ("flow", (
        ("ページの関係", "種類と根拠を記録"),
        ("グラフを作る", "点検して抽出"),
        ("関係を調べる", "つながりや経路を確認"),
    )),
    "evolution.html": ("flow", (
        ("経験を記録", "learn で検証結果を残す"),
        ("改善案を評価", "evolve で比較する"),
        ("結果を判断", "承認して適用、必要なら復旧"),
    )),
    "upgrade.html": ("flow", (
        ("対象を確認", "移植元の版と保存先"),
        ("更新を実行", "必要なファイルを追加"),
        ("差分を確認", "既存の規約を確認して反映"),
    )),
    "mcp-server.html": ("flow", (
        ("アプリから依頼", "Claude Code や Codex"),
        ("ローカルで処理", "検索・索引・構造点検"),
        ("結果を返す", "根拠候補・統計・関係"),
    )),
}

SUMMARY_START = "<!-- page-summary:start -->"
SUMMARY_END = "<!-- page-summary:end -->"
CODE_SCRIPT = '<script defer src="assets/manual-code.js"></script>'


def overview_html(kind, steps):
    tag = "ol" if kind == "flow" else "ul"
    entries = "\n".join(
        f"    <li><strong>{escape(title)}</strong><span>{escape(detail)}</span></li>"
        for title, detail in steps
    )
    return (
        f'<figure class="page-summary page-summary-{kind}">\n'
        f'  <{tag} role="list" aria-label="概要">\n{entries}\n  </{tag}>\n'
        '</figure>'
    )


def decorate(page, html):
    overview = OVERVIEWS.get(page)
    if overview:
        html = re.sub(
            rf"\n[ \t]*{SUMMARY_START}.*?{SUMMARY_END}",
            "", html, count=1, flags=re.S,
        )
        heading = (
            r'<h3\b[^>]*\bid="readme-できること"[^>]*>[^\n]*</h3>'
            if page == "index.html" else r"<h1\b[^>]*>[^\n]*</h1>"
        )
        fragment = overview_html(*overview)
        html, replaced = re.subn(
            heading,
            lambda match: f"{match[0]}\n{SUMMARY_START}\n{fragment}\n{SUMMARY_END}",
            html, count=1,
        )
        if replaced != 1:
            raise ValueError(f"{page} に概要図を置く見出しがありません。")
    if re.search(r"<pre\b[^>]*>\s*<code\b", html) and CODE_SCRIPT not in html:
        html = html.replace("</head>", f"  {CODE_SCRIPT}\n</head>", 1)
    return html
