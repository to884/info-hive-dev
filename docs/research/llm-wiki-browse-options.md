# LLM Wiki の閲覧手段：設計選択肢の発散と収束

作成日：2026年11月3日（日本時間）
対象：info-hive に追加する閲覧コマンド（仮称 `/wiki:browse`）
位置づけ：`llm-wiki-product-concept-and-requirements-ja.md`（以下「要件定義書」）の D-03（VS Code + Foam）と、info-hive の移植方針 G（ホスト型 wiki は提供しない）への入力
手法：brainstorm-diverge-converge（発散 → クラスタ → 収束）
改訂：2026年11月3日、候補の事実を一次資料（公式文書、公式リポジトリ、PyPI など）で確かめ、採点と記述を更新した

本書の記述は次の区分に従う。

| 区分 | 意味 |
| --- | --- |
| 確定 | 依頼で示された要件（ローカル PC で動く、将来の拡張性、日本語で表示が崩れない）と、ユーザーの決定（2026年11月3日）。決定は「常駐サーバーも検討対象に含める」「Node.js の利用も許容する」「拡張先として日本語の全文検索、グラフとバックリンク、RAG 検索との統合、複数 Wiki の横断表示の 4 つを重視する」の 3 つ |
| 検証環境 | この PC の条件（第2.2節）。製品の仕様ではなく、PoC の判定にだけ使う |
| 提案 | 本書の採点にもとづく推奨。採用は未確定 |
| 推定 | 公開値がなく、仕組みやほかの値から見積もった値 |
| 要確認 | 実測またはユーザーの判断が必要な事項 |

ライセンス、対応状況、版は第9節の出典に対応する。公開値が見つからなかったものは「未確認」と書いた。

---

## 1. 結論の要約

1. **推奨は「必要なときだけ起動するローカル専用サーバー」である（構成 B）。** `/wiki:browse` が Python のサーバーを 127.0.0.1 で起動し、既定のブラウザで開く。Markdown はリクエストのたびに HTML に変換し、ファイルには書き出さない。一定時間操作がなければサーバーは自分で終了する。採点した 6 つの軸のすべてで、この構成に入る選択肢が 1 位になった（第6.2節）。Claude Code は終了時にバックグラウンドの処理を止めるので、サーバーはセッションの間だけ動くものとして設計する。
2. **Markdown の変換は markdown-it-py に任せ、wikilink の解決は既存のスクリプトと同じ規則を使う。** info-hive の `wiki_lint.py` と `wiki_search.py` には、NFC 正規化、大文字小文字の区別、`[[dir/slug]]`、`[[slug#見出し]]`、`[[slug|別名]]` を扱う `resolve_link()` がすでにある。閲覧画面が別の規則でリンクを解決すると、lint では通るのに画面ではリンク切れになる、といった食い違いが起きる。描画側は既存の関数を共通モジュールに切り出して使う。
3. **静的サイト生成器（Quartz、MkDocs など）をそのまま使う構成は次点にした。** 画面の完成度は高い。一方で、frontmatter の日本語の別名キー（`タイトル` など）、型付きグラフ、`wiki_search.py` の検索結果は解釈できない。合わせるには生成器側の改造が要る。Material for MkDocs は 2025年11月の 9.7.0 を最後に新機能の追加を止め、修正だけを2027年5月5日まで続けると告知している。最新の 9.8.0 は Python 3.11 以上を要求する。Quartz は2026年3月に v5.0.0 になり、設定の形式が変わった。
4. **全文検索は、ブラウザ側の検索ライブラリではなく `wiki_search.py` をサーバー経由で呼ぶ。** `/wiki:query` と同じ BM25 と埋め込みの検索になり、日本語の bigram 分割もそのまま使える。将来 PDF の RAG 検索を加えるときも、同じ API に検索元を加えればよい。Pagefind などの静的索引も、索引をブラウザが取得する仕組みなので `file://` では動かず、サーバーが要る。Pagefind で日本語を索引に入れるには、別配布の extended 版も要る。
5. **静的 HTML の書き出し（構成 A）は、同じ変換部品で出せる副機能にする。** サーバーを立てられない環境や、ほかの人に渡すときに使う。この場合、検索とグラフの機能は縮小する。
6. **日本語の表示崩れは、ブラウザ任せにせず CSS と URL の規則で防ぐ。** `lang="ja"`、OS 標準の日本語フォントの並び、`line-break: strict` などの禁則指定、URL の NFC 正規化と UTF-8 のパーセントエンコードを既定にする。フォント名やポート番号は既定値として扱い、仕様には書かない。
7. **閲覧専用にし、編集は VS Code と Foam に残す。** 要件定義書の D-03 と F-G01 を置き換えるのではなく、読むための補助として位置づける。書き込みの API を持たないので、S-07（リンクを自動実行しない）とも矛盾しない。
8. **方針 G の解釈を ADR に残す。** 上流のホスト型 wiki は Cloudflare Workers 上で外部に公開するサーバーだった。127.0.0.1 だけで待ち受けるサーバーはこれに当たらない、という解釈を本書の前提にした（第3.3節）。

推奨構成の実装は 3 段階に分ける（第7.2節）。最初の段階では、ページの表示、ナビゲーション、メタデータ、被リンク、未解決リンクの表示までを作る。

---

## 2. 問題定義と評価基準

### 2.1 問題

info-hive が作る Wiki は、YAML の frontmatter を持つ Markdown のファイル群で、ページどうしは `[[slug]]` 形式の wikilink でつながる。VS Code やテキストエディタで読むと、frontmatter がそのまま見え、wikilink はクリックできず、被リンクもわからない。整形した表示でページを読み、リンクをたどれるようにしたい。

**判断対象**：`/wiki:browse` のようなコマンドで、どの経路・どの部品を使って Wiki を表示するか。PoC で作る構成を 1 つに絞り、次点を 1 つ残す。

### 2.2 制約と前提

| 項目 | 内容 | 区分 |
| --- | --- | --- |
| 動作場所 | ローカル PC で動く。Wiki の内容を PC の外に送らない。オフラインで全機能が動く | 確定 |
| 日本語 | 本文、見出し、ファイル名、slug、frontmatter の日本語の別名キーで表示が崩れない | 確定 |
| 拡張性 | 日本語の全文検索、グラフとバックリンク、RAG 検索との統合、複数 Wiki の横断表示に伸ばせる | 確定（4 方向は2026年11月3日に決定） |
| サーバー | 127.0.0.1 で待ち受けるサーバーは、一時的なものも常駐するものも検討対象に含める | 確定（2026年11月3日） |
| 実行環境の依存 | Node.js を使う案も検討対象に含める。依存が増えることは採点で減点する | 確定（2026年11月3日） |
| プラグインの実行環境 | 現状は Python 3.10 以上と uv だけで動く。依存はスクリプトごとに PEP 723 で固定する | 確定（info-hive の README） |
| 正本 | Markdown が正本で、索引やエクスポートは再生成できる派生データ | 確定（要件定義書 D-01〜D-04、第3.3節） |
| 閲覧と編集 | 人が読み書きする環境は VS Code + Foam。閲覧コマンドはその補助 | 確定（D-03）。補助という位置づけは提案 |
| 安全性 | YAML は安全な方式で読み込み、リンクは自動実行しない | 確定（S-07） |
| 対応 OS | 未決（要件定義書 O-11）。info-hive の CI は ubuntu-latest と windows-latest で動く | 要確認 |
| PC 固有の値 | フォント名、ポート番号、保存先などは既定値と設定で扱い、仕様にしない | 確定（2026年11月2〜3日） |
| 商用利用 | 商用で利用する。同梱する部品は商用で使えるライセンスに限る | 確定（2026年11月2日） |

#### 検証環境（この PC）

| 項目 | 値 | 確認の方法 |
| --- | --- | --- |
| OS | Windows 11 | ユーザー（2026年11月2日） |
| Python | 3.14.6 | コマンドで確認（2026年11月3日） |
| uv | 0.12.2 | コマンドで確認（2026年11月3日） |
| Node.js | v24.15.0（npm 12.0.2） | コマンドで確認（2026年11月3日） |
| VS Code と Foam | 未確認（`code --version` が版を返さなかった） | 要確認 |
| Claude Code | desktop アプリ（ブラウザペインあり）を使っている | 本書の作成に使ったセッション |

### 2.3 評価基準

各選択肢を 1〜10 点で採点し、重みを掛けて合計する（満点 180）。

| 基準 | 重み | 定義 |
| --- | --- | --- |
| ローカル完結 | 3 | データが PC の外に出ない。オフラインで動く。CDN を使わない。待ち受けの範囲が狭い |
| 日本語の正しさ | 3 | フォント、禁則と折り返し、日本語のファイル名・slug・見出しへのリンク、日本語の別名キー、検索での日本語の分割 |
| 拡張性 | 3 | 日本語検索、グラフとバックリンク、RAG 統合、複数 Wiki の 4 方向へ伸ばしやすいか |
| 依存の軽さ | 2 | Python と uv だけで動けば高い。追加のバイナリ、Node.js、別アプリの導入で下げる |
| Windows 対応 | 2 | Windows でそのまま動くか。cp932、パスの長さ、大文字小文字を区別しないファイルシステムへの耐性。macOS と Linux でも動けば加点 |
| ライセンス | 2 | MIT、Apache-2.0、BSD、OFL、MPL は同梱できる。GPL と AGPL は同梱できず、別プロセスとして呼ぶ場合だけ残す |
| 利用者体験 | 2 | 起動までの手数、ページ間の移動のしやすさ。CLI の利用者と desktop アプリの利用者の両方で使えるか |
| 保守性 | 1 | 更新が続いているか、開発元の体制、保守のみの状態でないか |

その軸の性能に影響しない基準は 5 点（中立）とした。

### 2.4 必須条件による除外

採点の前に、次の候補を外した。番号は第4節の通し番号である。

| 除外した候補 | 理由 |
| --- | --- |
| 18 エクスプローラで WIKI_ROOT を開くだけ | 整形した表示にならず、問題を解決しない |
| 19 ブラウザの Markdown 表示拡張 | 一般的な拡張は wikilink と frontmatter を解釈しない（推定）。ブラウザごとに導入も要る |
| 22 LAN の他の PC からも見られる共有サーバー | 0.0.0.0 で待ち受けると Wiki が PC の外から読める。ローカル完結に反する |
| 46 既存の Wiki エンジン（Wiki.js、BookStack など）へ取り込む | 内容がデータベースに移り、Markdown が正本でなくなる。データベースとサーバーの運用も要る |
| 66 Google Fonts からフォントを読み込む | 外部への通信が発生し、オフラインで動かない |
| 94 ブラウザ上で編集して Markdown に書き戻す | 閲覧の範囲を超える。編集は D-03 の Foam で行う。将来の検討として保留にした |

ライセンスで外した候補はない。pandoc は GPL なので同梱はせず、利用者が別に入れたものを呼ぶ場合に限って採点に残した。

### 2.5 推奨構成の部品のライセンス

| 部品 | ライセンス | 商用利用 | 備考 |
| --- | --- | --- | --- |
| markdown-it-py 4.2.0、mdit-py-plugins 0.6.1 | MIT | 可 | 新たに依存に加える。どちらも Python 3.10 以上で動く |
| cytoscape.js | MIT | 可 | 第 2 段階で同梱する。CDN からは読まない |
| Python 標準ライブラリ（`http.server`、`webbrowser`） | PSF | 可 | |
| `wiki_search.py` と既存の依存（fastembed、sqlite-vec） | info-hive 既存 | 可 | 新たな依存ではない |
| Noto Sans JP（任意） | SIL OFL 1.1 | 可 | 同梱する場合は著作権表示とライセンス文を添える |

---

## 3. 前提の整理

### 3.1 Wiki の構造と再利用できる部品

| 要素 | 内容 | 閲覧画面での扱い |
| --- | --- | --- |
| 配置 | `WIKI_ROOT`（プロジェクトの `wiki/` か `~/wiki/`）の下に `sources/`、`entities/`、`concepts/`、`synthesis/`、`graph/`、`indexes/`。上位に `SCHEMA.md`、`index.md`、`log.md` | `index.md` と `indexes/<type>.md` を左のナビゲーションにする |
| frontmatter | `type`、`title`、`tags`、`sources`、`created`、`updated`。任意で `graph:`。日本語の別名キー（`タイトル`、`種類` など）も使える | `wiki_text.py` の `canonical_meta()` で英語のキーにそろえてから、ページ上部のメタ欄に描く。タグは同じファイルの関数で NFKC にそろえる |
| wikilink | `[[slug]]`、`[[dir/slug]]`、`[[slug#見出し]]`、`[[slug|別名]]`。`.md` 付きも許す。NFC にそろえ、大文字小文字を区別する | `resolve_link()`（`wiki_lint.py` と `wiki_search.py` にある）を共通化して使う |
| 被リンク | `wiki_search.py --backlinks` と `--top-linked` で取れる | 同じ処理を関数として呼び、各ページの末尾に一覧を出す |
| 型付きグラフ | `graph/nodes.jsonl`、`edges.jsonl`、`graph.sqlite`、`graph.graphml` をページから再生成する | ページごとの関係表と、全体のグラフ表示に使う |
| 検索 | `wiki_search.py` が BM25 と埋め込みのハイブリッド検索を行う。かなと漢字は bigram に分け、既定の埋め込みモデルは multilingual-e5-small | 検索 API の裏側にそのまま使う |
| キャッシュ | `<WIKI_ROOT>/.wiki-cache/` は `init_wiki.py` が `.gitignore` を置く | 書き出しを行う場合の置き場所の候補 |

### 3.2 規模の仮定

`index.md` は約 150 ページで種類ごとのファイルに分割される（info-hive の README）。Wiki のページ数の上限は決まっていない。本書では、1 つの Wiki が数十〜数千ページ、全体で数 MB〜数十 MB の Markdown になると仮定した（推定）。PDF 100GB 規模の RAG 索引は別の仕組みで扱い、閲覧画面が直接読むのは Wiki のページと検索結果だけとする。

### 3.3 方針 G の解釈

info-hive は、移植元の llm-wiki-plugin にあった「ホスト型 wiki」を削った（`info-hive/UPSTREAM.md`）。移植元の CHANGELOG によれば、これは Cloudflare Workers の上で動き、トークンで認証し、`/ui/<wiki>/` で読み取り専用のリーダー（フォルダツリー、検索、描画したページ、被リンク、履歴、差分）を提供するものだった。

本書は、方針 G が禁じたのは「PC の外に公開して、外部のサービス上に Wiki を置くこと」だと解釈した。127.0.0.1 だけで待ち受け、PC の外からは接続できないサーバーはこれに当たらない。ユーザーは2026年11月3日に、常駐サーバーを含めて検討対象にすることを決めた。この解釈は ADR として `docs/adr/` に残すことを提案する（第7.1節）。

移植元のリーダーが備えていた機能は、閲覧画面に求められる機能の目安として第7.2節の段階計画に使った。

---

## 4. 発散：選択肢の全リスト

判断を保留して列挙した。必須条件に反しそうな案や、実現の見込みが低い案も含めた。末尾の「S」は既存の方法の延長にある安全な案、「W」は前提を外したワイルドな案である。

### 配信・表示の経路

1. 静的 HTML 一式を書き出し、既定のブラウザで `file://` として開く（S）
2. 全ページを 1 つの HTML ファイルに埋め込み、JavaScript でページを切り替える（S）
3. 必要なときだけ起動する、127.0.0.1 限定の HTTP サーバー。空いているポートを使い、操作がなければ終了する（S）
4. 常駐する 127.0.0.1 限定のサーバー。ファイルの変更を監視して表示を更新する（S）
5. VS Code の Markdown プレビューと Foam を開くよう案内するだけ。D-03 の延長で、比較の基準にする（S）
6. Foam のグラフ表示コマンドへ誘導するだけ（S）
7. VS Code の拡張機能（Webview）を新しく作る（W）
8. Obsidian の保管庫として開く。`obsidian://` で引き渡す（S）
9. Claude desktop のブラウザペインで、ローカルサーバーの URL を開く（S）
10. Claude desktop の mod（チャットの横に常に出るペイン）として表示する（W）
11. ターミナルに整形して出す（rich）（S）
12. Textual の TUI で、目次とリンク移動を備えた閲覧画面を作る（W）
13. PDF に書き出す。Edge や Chrome のヘッドレス印刷、または WeasyPrint を使う（S）
14. DOCX に書き出す（S）
15. EPUB に書き出し、電子書籍リーダーで読む（W）
16. pywebview で専用のウィンドウを開く（W）
17. Streamlit、NiceGUI、Gradio などの Python 製 Web UI で作る（W）
18. エクスプローラや Finder で WIKI_ROOT を開くだけ（S）
19. ブラウザの Markdown 表示拡張で `.md` を直接開く（S）
20. MCP サーバーのリソースとして公開し、クライアント側に表示させる（W）
21. Claude がその場で HTML を生成して見せる（W）
22. LAN の他の PC からも見られる共有サーバー（0.0.0.0 で待ち受ける）（W）

### 変換エンジン

23. markdown-it-py と mdit-py-plugins（front_matter、anchors）に、自前の wikilink 規則を加える（S）
24. Python-Markdown と pymdown-extensions。標準の WikiLinks 拡張は `|` や `#` を扱えないので置き換える（S）
25. mistune 3 にプラグインを加える（S）
26. marko など、ほかの CommonMark 実装（S）
27. 標準ライブラリだけで書いた最小の変換器。見出し、段落、リスト、コード、表に限る（S）
28. Jinja2 で自前のテンプレートを組む（S）
29. MkDocs と Material for MkDocs に、mkdocs-obsidian-bridge や ezlinks で wikilink の解決を加える（S）
30. Zensical（Material for MkDocs の後継。MkDocs の設定を読める）（W）
31. Sphinx と MyST-Parser（S）
32. Pelican（S）
33. comrak など Rust 製パーサーの Python バインディング（S）
34. Quartz（2026年3月から v5）。Obsidian 互換で、グラフ、被リンク、検索を内蔵する（S）
35. VitePress（移植元がドキュメントサイトに使っていた）（S）
36. Docsify。ビルドせず、ブラウザが Markdown を取得して描く（S）
37. Docusaurus（S）
38. Eleventy（S）
39. Astro Starlight（S）
40. ブラウザ側で marked.js や markdown-it（JavaScript 版）を動かし、生の `.md` を描く（S）
41. mdBook（S）
42. Zola（S）
43. Hugo（S）
44. pandoc の `wikilinks_title_after_pipe` 拡張と Lua フィルタ（S）
45. obsidian-export で wikilink を通常のリンクに直してから、任意のエンジンに渡す（W）
46. 既存の Wiki エンジン（Wiki.js、BookStack など）へ取り込む（W）
47. `info-hive/docs/porting-plan.html` のような、手書きの HTML と CSS の流儀にそろえる（S）

### リンク、メタデータ、グラフの描画

48. `resolve_link()` を共通モジュールに切り出し、描画でも lint と同じ規則でリンクを解決する（S）
49. `canonical_meta()` で日本語の別名キーをそろえ、ページ上部にメタ欄を描く（S）
50. 各ページの末尾に被リンクの一覧を出す（S）
51. `graph/` の出力から、ページごとの型付き関係を表で描く（S）
52. 全体のグラフを cytoscape.js で描く。ファイルは同梱する（S）
53. 全体のグラフを vis-network で描く（S）
54. 全体のグラフを d3-force で自前に描く（S）
55. GraphML を Gephi など外部のツールに渡すだけ（S）
56. 3D のグラフ（3d-force-graph）（W）
57. `index.md` と `indexes/<type>.md` を左のナビゲーションにする（S）
58. 未解決のリンクを赤で示し、lint の結果とそろえる（S）
59. `sources:` の原資料を `file://` のリンクで示し、クリックしたときだけ開く（S）
60. Mermaid の図を、同梱した mermaid.js で描く（S）
61. `log.md` を時系列の画面にする（S）
62. 日本語の見出しに ID を付け、`[[slug#見出し]]` を解決する（S）
63. 別の Wiki への相対 Markdown リンク（要件定義書 第4.2節）も解決する（S）

### 日本語の表示と検索

64. OS 標準の日本語フォントを並べたフォントスタック（S）
65. Noto Sans JP を同梱する（S）
66. Google Fonts からフォントを読み込む（S）
67. CSS で禁則と折り返しを指定する。`line-break: strict`、`overflow-wrap: anywhere`、`word-break: normal`（S）
68. `text-autospace` と `word-break: auto-phrase` を、対応するブラウザでだけ適用する（W）
69. `<html lang="ja">` を必ず付ける（S）
70. URL は NFC にそろえ、UTF-8 でパーセントエンコードする（S）
71. Pagefind で静的な検索索引を作る（S）
72. lunr.js と lunr-languages の日本語（TinySegmenter）（S）
73. MiniSearch や FlexSearch に、文字 bigram の分割を与える（S）
74. Python の標準ライブラリで bigram の JSON 索引を作り、小さな JavaScript で検索する（S）
75. `wiki_search.py`（BM25 と埋め込み）をサーバー経由で呼ぶ（S）
76. ブラウザの `Intl.Segmenter` で検索語を分かち書きする（S）
77. 縦書きで表示する（`writing-mode: vertical-rl`）（W）
78. ルビの記法を拡張する（W）

### プラグインへの組み込み

79. `/wiki:browse [slug|検索語]` から `uv run --script wiki_browse.py` を呼び、URL を開く（S）
80. 書き出し先を `<WIKI_ROOT>/.wiki-cache/html/` にする（S）
81. 書き出し先を OS のユーザーキャッシュ（Windows では `%LOCALAPPDATA%`）にする（S）
82. ファイルに書き出さず、サーバーがリクエストのたびに変換する（S）
83. 書き出し先を `WIKI_ROOT/site/` にして Git で管理する（S）
84. 内容のハッシュで、変わったページだけを変換し直す（S）
85. lint や graph extract の後に、hooks で再生成する（W）
86. Global Wiki と Project Wiki を 1 つの画面で切り替える（S）
87. 設定は環境変数（`INFO_HIVE_BROWSE_*`）とコマンドの引数で行う（S）
88. NTFS が大文字小文字を区別しないことによる衝突を検出する（S）
89. `/wiki:query` の回答に、根拠のページを開く URL を添える（S）
90. 閲覧専用にし、編集は VS Code と Foam に任せる（S）
91. 起動したサーバーのプロセス ID とポートを記録し、2 回目以降は再利用する（S）

### 将来の発想

92. ページ上のボタンから、Claude Code に要約や追記を頼む（W）
93. `git log` から「最近変わったページ」の要約ページを作る（W）
94. ブラウザ上で編集し、Markdown に書き戻す（W）
95. Marp でスライドにする（W）
96. Anki のカードに書き出す（W）

合計 96 件（うち W は 22 件）。

---

## 5. クラスタ：7 つのテーマ

| クラスタ | 含む選択肢 | このクラスタで決めること |
| --- | --- | --- |
| C1 配信・表示の経路 | 1〜22 | Wiki をどこに、どの仕組みで表示するか。方針 G との線引き |
| C2 変換エンジン | 23〜47 | Markdown を何で HTML にするか。実行環境の依存をどこまで増やすか |
| C3 リンク、メタデータ、グラフ | 48〜63 | 既存スクリプトと規則をどう共有するか。グラフをどこまで描くか |
| C4 日本語の表示 | 64〜70、77、78 | フォント、CSS、URL の方針 |
| C5 全文検索 | 71〜76 | 検索をどの層に置くか |
| C6 プラグインへの組み込み | 79〜91 | コマンドの形、書き出し先、再生成、複数 Wiki |
| C7 将来の発想 | 92〜96 | 採点せず、保留として記録する |

クラスタをまたぐ選択肢：

- 36（Docsify）と 40（ブラウザ側で描く）は、ブラウザが Markdown を取得するので、C1 のサーバー（3、4）が前提になる
- 71（Pagefind）と 74（JSON 索引）も、ブラウザが索引ファイルを取得するので、`file://` では動かない
- 75（`wiki_search.py`）は、C1 のサーバー（3、4）がある場合だけ成り立つ
- 9（desktop のブラウザペイン）は、3 または 4 のサーバーを別の画面で開くだけで、表示経路としては 3、4 を前提にする
- 48 は C2 のどのエンジンを選んでも必要で、エンジンの選択とは独立している

---

## 6. 収束：評価と選定

### 6.1 採点の進め方

- 互いに置き換え可能な選択肢を、次の 6 軸に分けて採点した。表示経路（C1）、変換エンジン（C2）、グラフの描画（C3 の一部）、フォント（C4 の一部）、検索の層（C5）、書き出し先（C6 の一部）である。
- 同じ系統の選択肢は代表だけを採点した。
  - 表示経路：単一の HTML（2）は静的 HTML（1）で、TUI（12）はターミナル（11）で、Python 製 Web UI（17）はローカルサーバー（3）で、DOCX と EPUB（14、15）は PDF（13）で代えた。mod のペイン（10）と MCP リソース（20）は、desktop のペイン（9）と同じく別の画面にサーバーの内容を出す方式なので、9 で代えた。
  - 変換エンジン：Node.js 製の静的サイト生成器は、wikilink とグラフを内蔵する Quartz（34）を代表にした（35、37、38、39 は Quartz 以上の点にならないと判断）。単一バイナリの生成器は mdBook（41）を代表にした（42、43）。Sphinx（31）と Pelican（32）は文書サイトやブログ向けで、MkDocs（29）を代表にした。Python のほかのパーサー（26、33）は 23〜25 と同じ扱いになる。
- 補助的な手段（27、28、40、45、47、48〜50、57〜63、67〜70、76〜79、84〜91）は、どの構成でも採れるので採点せず、第6.5節の構成に組み込んだ。
- C7（92〜96）は採点せず、第6.6節の保留に入れた。
- ほとんどの点数は公開値ではなく、仕組みとライセンス、対応状況の調査（第9節）から判断した。極端な点（1〜3、9〜10）には根拠を書いた。

### 6.2 軸別の採点

基準の略号：局＝ローカル完結（×3）、日＝日本語の正しさ（×3）、拡＝拡張性（×3）、依＝依存の軽さ（×2）、W＝Windows 対応（×2）、ラ＝ライセンス（×2）、体＝利用者体験（×2）、保＝保守性（×1）。

#### 表示経路

| 順位 | No. | 選択肢 | 局 | 日 | 拡 | 依 | W | ラ | 体 | 保 | 加重合計 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3 | 必要なときだけ起動するローカルサーバー | 8 | 8 | 9 | 9 | 8 | 10 | 7 | 7 | 150 |
| 2 | 1 | 静的 HTML を `file://` で開く | 9 | 8 | 5 | 9 | 9 | 10 | 7 | 8 | 144 |
| 3 | 4 | 常駐するローカルサーバー | 8 | 8 | 10 | 6 | 7 | 10 | 6 | 6 | 142 |
| 4 | 16 | pywebview の専用ウィンドウ | 10 | 8 | 8 | 4 | 8 | 9 | 7 | 6 | 140 |
| 4 | 7 | VS Code の拡張機能 | 10 | 8 | 7 | 5 | 9 | 9 | 7 | 5 | 140 |
| 6 | 9 | desktop のブラウザペイン | 8 | 8 | 8 | 8 | 8 | 9 | 6 | 5 | 139 |
| 7 | 5 | VS Code と Foam へ案内する | 10 | 7 | 4 | 8 | 9 | 8 | 5 | 8 | 131 |
| 8 | 8 | Obsidian で開く | 9 | 8 | 6 | 4 | 9 | 6 | 6 | 8 | 127 |
| 9 | 11 | ターミナルに整形して出す | 10 | 5 | 3 | 8 | 6 | 9 | 4 | 8 | 116 |
| 9 | 21 | Claude がその場で生成する | 3 | 7 | 5 | 10 | 9 | 10 | 4 | 5 | 116 |
| 11 | 13 | PDF に書き出す | 9 | 6 | 2 | 5 | 7 | 8 | 4 | 7 | 106 |

- 3 と 4 の局が 8 なのは、ポートを開くので、同じ PC のほかのプロセスから接続できるためである。第6.8節の対策で補う。
- 3 の拡が 9 なのは、検索 API、RAG の結果、複数 Wiki の切り替えをサーバー側に加えられるためである。4 はファイル変更の監視まで持つので 10 にした。
- 1 の拡が 5 なのは、`file://` で開いたページから、ブラウザが別のローカルファイルの取得を許さないためである。MDN によれば、`file://` のページの出所は不透明なもの（opaque origin）として扱われるのが一般的で、Firefox も 68 から同じフォルダのファイルを読めなくした。検索索引を別ファイルで持てず、`wiki_search.py` も呼べない。
- 3 の依が 9 なのは、`http.server` と `webbrowser` が標準ライブラリにあるためである。
- 4 の依と体が 6 なのは、Claude Code から起動したバックグラウンドの処理が、Claude Code の終了時に止められるためである。公式文書によれば、macOS と Linux では setsid で切り離したプロセスも止められる。セッションをまたいで常駐させるには、OS の自動起動などの別の起動経路を利用者に用意してもらう必要がある。Windows での扱いは公式文書に書かれていない（要確認）。
- 16 の依が 4 なのは、Windows では pythonnet と .NET Framework 4.0 以上が、Chromium 系の描画には WebView2 ランタイムが要り、Linux では Qt か GTK のどちらかを利用者が選んで入れる必要があるためである。
- 21 の局が 3 なのは、Wiki の本文をモデルに渡して HTML を作るため、表示のたびに内容が PC の外へ出るためである。
- 11 の日が 5 なのは、rich は全角文字の幅を 2 として数えるが、幅の決まらない文字の扱いや表の罫線のそろい方が、端末とフォントに左右されるためである。
- 13 の拡が 2 なのは、リンクをたどる、検索する、といった操作がほとんどできないためである。
- 8 のラが 6 なのは、Obsidian は2025年2月20日から商用を含むすべての用途で無料になったが、ソースが公開されておらず、プラグインに同梱できないためである。体が 6 なのは、`obsidian://open?path=` で開けるのが登録済みの保管庫の中のファイルで、最初に利用者が Wiki のフォルダを保管庫として登録する必要があるためである。未登録のフォルダを開けるかは未確認である。

**選定：No.3。** 2 位の 1 とは 6 点、3 位の 4 とは 8 点の差がある。1 は同じ変換部品で書き出せるので、副機能として残す。4 の常駐は、Claude Code の終了とともにサーバーが止まるので、`/wiki:browse` だけでは実現できない。既定は「必要なときに起動し、操作がなければ終了」にし、常駐させる方法は利用者の要望が出てから検討する（第6.9節）。9 は 3 の URL を desktop のペインで開く使い方で、追加の実装はほぼ要らない。公式文書によれば、ブラウザペインは 127.0.0.1 などのローカルの URL を開ける。

#### 変換エンジン

| 順位 | No. | 選択肢 | 局 | 日 | 拡 | 依 | W | ラ | 体 | 保 | 加重合計 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 23 | markdown-it-py | 10 | 8 | 9 | 8 | 9 | 10 | 7 | 8 | 157 |
| 2 | 25 | mistune 3 | 10 | 7 | 7 | 9 | 9 | 9 | 7 | 5 | 145 |
| 3 | 24 | Python-Markdown | 10 | 7 | 7 | 7 | 9 | 9 | 7 | 8 | 144 |
| 4 | 34 | Quartz（v5） | 9 | 6 | 7 | 3 | 7 | 9 | 9 | 7 | 129 |
| 5 | 36 | Docsify | 8 | 6 | 5 | 8 | 9 | 9 | 6 | 7 | 128 |
| 6 | 30 | Zensical | 9 | 6 | 6 | 6 | 7 | 9 | 8 | 4 | 127 |
| 7 | 29 | MkDocs と Material for MkDocs | 9 | 6 | 6 | 5 | 8 | 9 | 8 | 2 | 125 |
| 8 | 44 | pandoc（別プロセス） | 10 | 7 | 4 | 5 | 9 | 5 | 5 | 9 | 120 |
| 9 | 41 | mdBook | 9 | 5 | 4 | 6 | 8 | 8 | 6 | 8 | 118 |

- 23 の拡が 9 なのは、トークン列を経由して描画するので、wikilink、見出し ID、メタ欄などの規則を後から加えやすいためである。markdown-it-py 4.2.0（2026年5月7日）と mdit-py-plugins 0.6.1 はどちらも MIT で、Python 3.10 以上で動く。mdit-py-plugins には front_matter と anchors のプラグインがあるが、wikilink のプラグインはない。PyPI でも、Python 版の wikilink プラグインで広く使われているものは見つからなかった。front_matter は YAML の中身を解析しないので、pyyaml の安全な読み込みと組み合わせる。注意点として、引数なしの `MarkdownIt()` は commonmark の設定になり、生の HTML をそのまま出力する。公式の安全性の文書は、信頼できない入力には `js-default` の設定を勧めている。
- 24 の依が 7 なのは、最新の 3.11 系が Python 3.11 以上を要求し、info-hive の前提（3.10 以上）で使うには旧版に固定する必要があるためである。日が 7 なのは、標準の WikiLinks 拡張の正規表現が `[\w0-9_ -]+` で、`|`、`#`、`/` を含むリンクに一致しないためである。置き換えが要る。
- 25 の保が 5 なのは、開発の中心が 1 人で、作者が後継の Markdown パーサー（Wenmode）を公開しているためである。mistune 自体の更新は続いている（3.4.0、2026年10月19日）。wikilink と front matter のプラグインはない。
- 34 の依が 3 なのは、Node.js 22 以上と npm 10.9.2 以上が要り（v5 の package.json）、Quartz のリポジトリを複製して使う形だからである。体が 9 なのは、グラフ、被リンク、ポップアップ、検索が最初から揃っているためである。日が 6 なのは次の 3 点による。検索は FlexSearch で、日本語は 1 文字ずつのトークンとして照合する（v4 のソースで確認。v5 は未確認）。wikilink の照合は大文字小文字を区別せず、区別する info-hive の規則と食い違う。frontmatter の日本語の別名キーも解釈しない。v5 にはフォントを手元に置く設定があり、外部への通信なしで動かせる。
- 36 の保が 7 なのは、v5.1.0（2026年10月30日）が出ていて更新が続いているためである。wikilink のプラグインは見つからなかった。
- 30 の日が 6 なのは、v0.0.52 から日本語の検索に対応した（言語に応じた分割）ためである。依が 6 なのは Python 3.11 以上を要求するためで、保が 4 なのは最新の v0.0.74（2026年10月30日）でもアルファ版であるためである。wikilink に対応するかは未確認である。
- 29 の保が 2 なのは、Material for MkDocs が 9.7.0（2025年11月11日）を最後に新機能の追加を止め、重大な不具合と安全性の修正だけを2027年5月5日まで続けると告知しているためである。Material のブログによれば、MkDocs 2.0 はプラグインの仕組みをなくし、既存のプロジェクトを移す手段もない。Material は MkDocs 2.0 では動かない。依が 5 なのは、最新の 9.8.0 が Python 3.11 以上を要求するためである。日が 6 なのは、日本語の分割をブラウザ側の TinySegmenter で行い、過去に日本語で索引が初期化できない不具合が報告されているためである。フォントの既定は Google Fonts から読み込むので、無効にする設定が要る。
- 44 のラが 5 なのは、GPL v2 以降で同梱できず、利用者に別途導入してもらう必要があるためである。保が 9 なのは、長く保守され（最新は 3.13）、wikilink の拡張が 3.0 から本体にあるためである。
- 41 の日が 5 なのは、検索が空白で語を区切る前提で作られ、日本語で検索できない問題が未解決のまま残っているためである。拡が 4 なのは、`SUMMARY.md` で章立てを決める本の形式で、Wiki のようにページが網状につながる構造に合わないためである。wikilink のプリプロセッサはいくつかあるが、多くは2021〜2022年から更新されていない。

**選定：No.23。** 2 位との差は 12 点ある。画面の部品（ナビゲーション、検索欄、グラフ）は自前で作ることになるが、その分 frontmatter の日本語キー、型付きグラフ、既存の検索との統合を info-hive の規則に合わせられる。

#### グラフの描画

| 順位 | No. | 選択肢 | 局 | 日 | 拡 | 依 | W | ラ | 体 | 保 | 加重合計 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 52 | cytoscape.js | 9 | 8 | 9 | 8 | 9 | 10 | 8 | 8 | 156 |
| 2 | 54 | d3-force で自前に描く | 9 | 8 | 9 | 8 | 9 | 10 | 7 | 8 | 154 |
| 3 | 53 | vis-network | 9 | 8 | 8 | 8 | 9 | 10 | 8 | 6 | 151 |
| 4 | 51 | ページごとの関係表 | 10 | 9 | 4 | 10 | 10 | 10 | 5 | 9 | 148 |
| 5 | 6 | Foam のグラフに任せる | 10 | 8 | 3 | 8 | 9 | 9 | 6 | 7 | 134 |
| 6 | 56 | 3D のグラフ | 9 | 6 | 6 | 7 | 8 | 9 | 5 | 6 | 127 |
| 7 | 55 | GraphML を外部ツールへ | 10 | 6 | 3 | 4 | 8 | 7 | 3 | 7 | 108 |

- 51 の依、W、ラが 10 なのは、HTML の表を出すだけで、追加の部品が要らないためである。拡が 4 なのは、全体のつながりを見渡せないためである。
- 52 のラが 10 なのは MIT であるためで、53 も Apache-2.0 と MIT のどちらかを選べる。52 と 53 はキャンバスに描くので、日本語のラベルのフォントを JavaScript 側でも指定する必要がある（推定）。
- 6 の拡が 3 なのは、Foam のグラフはリンクのつながりだけを描き、info-hive の型付きの関係（`graph:` ブロックと `edges.jsonl`）を区別しないためである。
- 55 の体が 3 なのは、Gephi など別のアプリの導入と操作が要るためである。

**選定：No.51 と No.52 の 2 段階。** 52 が 1 位だが、2 位の 54 とは 2 点差で、ほぼ並んでいる。最初の段階では、追加の部品が要らない 51 でページごとの関係を出す。第 2 段階で 52 を同梱し、全体のグラフを描く。54 は表現の自由度が高いが、同じ機能まで自前で作る量が多い。

#### フォント

| 順位 | No. | 選択肢 | 局 | 日 | 拡 | 依 | W | ラ | 体 | 保 | 加重合計 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 64 | OS 標準の日本語フォントを並べる | 10 | 8 | 7 | 10 | 9 | 10 | 8 | 10 | 159 |
| 2 | 65 | Noto Sans JP を同梱する | 10 | 9 | 7 | 8 | 9 | 9 | 8 | 8 | 154 |

- 64 の日が 8 なのは、Windows と macOS には日本語フォントが標準で入っているが、Linux では入っていない場合があるためである。65 は OS によらず同じ字形になるので 9 にした。
- 65 の依が 8 なのは、フォントファイルが数 MB になり、サブセットにすると珍しい漢字が欠けるおそれがあるためである（推定）。

**選定：No.64。** Linux を正式に対応させると決まった場合（O-11）、65 を任意の設定として加える。

#### 検索の層

| 順位 | No. | 選択肢 | 局 | 日 | 拡 | 依 | W | ラ | 体 | 保 | 加重合計 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 75 | `wiki_search.py` をサーバー経由で呼ぶ | 10 | 8 | 10 | 8 | 8 | 10 | 7 | 9 | 159 |
| 2 | 71 | Pagefind | 9 | 9 | 6 | 6 | 8 | 10 | 8 | 8 | 144 |
| 3 | 74 | 標準ライブラリで bigram の JSON 索引を作る | 10 | 7 | 5 | 10 | 9 | 10 | 6 | 7 | 143 |
| 4 | 73 | MiniSearch や FlexSearch に bigram を与える | 9 | 7 | 5 | 8 | 9 | 9 | 7 | 7 | 136 |
| 5 | 72 | lunr.js と TinySegmenter | 9 | 5 | 4 | 8 | 9 | 7 | 6 | 5 | 119 |

- 75 の拡が 10 なのは、`/wiki:query` と同じ検索結果になり、RAG の検索元や複数の Wiki を同じ API に加えられるためである。日が 8 なのは、かなと漢字の bigram 分割、日本語の被覆率のしきい値、多言語の埋め込みモデルがすでに入っているためである。体が 7 なのは、最初の検索で埋め込みモデルの読み込みに時間がかかるためである（推定）。
- 71 の日が 9 なのは、extended 版が日本語を ICU4X で分割して索引に入れ（v1.6.0、2026年11月1日）、検索語もブラウザの `Intl.Segmenter` で分割する（v1.5.0 から）ためである。依が 6 なのは、日本語には extended 版のバイナリが要り、`pagefind[extended]` で取得する必要があるためである。索引をブラウザが取得するので、`file://` では動かずサーバーが要る点は 74 と同じである。
- 73 は、MiniSearch（MIT、7.2.0）が独自の分割関数を `tokenize` に渡せることを文書に書いている。FlexSearch（Apache-2.0）は CJK 用の設定を持つ。
- 72 のラが 7 なのは、lunr-languages が MPL 1.1 であるためである。更新は続いている（1.24.0、2026年11月1日）が、日本語の分割は TinySegmenter のままで、精度は低い（推定）。

**選定：No.75。** 2 位と 15 点の差がある。74 は、静的 HTML を書き出す副機能で、検索索引をページに埋め込む方法として使う（`file://` でも動くよう、別ファイルにせず HTML に含める）。

#### 書き出し先

| 順位 | No. | 選択肢 | 局 | 日 | 拡 | 依 | W | ラ | 体 | 保 | 加重合計 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 82 | 書き出さず、リクエストのたびに変換する | 10 | 8 | 8 | 10 | 9 | 10 | 7 | 8 | 158 |
| 2 | 81 | OS のユーザーキャッシュ | 10 | 8 | 8 | 10 | 9 | 10 | 6 | 8 | 156 |
| 3 | 80 | `<WIKI_ROOT>/.wiki-cache/html/` | 10 | 8 | 7 | 10 | 7 | 10 | 8 | 9 | 154 |
| 4 | 83 | `WIKI_ROOT/site/` を Git で管理する | 10 | 8 | 6 | 10 | 7 | 10 | 6 | 5 | 143 |

- 82 の W が 9 なのは、ファイルを書かないので、Windows のパスの長さや、大文字小文字を区別しないファイル名の衝突が問題にならないためである。
- 80 の W が 7 なのは、Wiki が OneDrive などの同期フォルダにあると、生成した HTML まで同期されるためである。
- 83 の保が 5 なのは、生成物の差分が履歴に混ざり、Markdown を正本とする原則とも衝突するためである。

**選定：No.82。** 静的 HTML を書き出す副機能を使うときは、81 を既定の書き出し先にし、引数で変えられるようにする。82、81、80 の差は 4 点以内で、どれを選んでも大きな問題はない。

### 6.3 感度分析

重みを変えたときに、各軸の 1 位が入れ替わるかを確かめた。

| 変更 | 表示経路 | エンジン | グラフ | フォント | 検索 | 書き出し先 |
| --- | --- | --- | --- | --- | --- | --- |
| 基準の重み | 3（150） | 23（157） | 52（156） | 64（159） | 75（159） | 82（158） |
| 拡張性を 3 から 2 に下げる | 3（141） | 23（148） | 52（147） | 64（152） | 75（149） | 82（150） |
| 依存の軽さを 2 から 3 に上げる | 3（159） | 23（165） | 52（164） | 64（169） | 75（167） | 82（168） |
| 利用者体験を 2 から 3 に上げる | 3（157） | 23（164） | 52（164） | 64（167） | 75（166） | 82（165） |
| ローカル完結を 3 から 1 に下げる | 3（134） | 23（137） | 52（138） | 64（139） | 75（139） | 82（138） |
| Node.js を許容しない | 3 | 23 | 52 | 64 | 75 | 82 |

どの変更でも 1 位は変わらなかった。差が小さいのは次の 2 か所である。

- **表示経路の 3、1、4（8 点の範囲）**：拡張性の重みを 2 に下げると、3 と 1 の差は 2 点に縮む。1 は拡張性が低いので、その重みが下がると差が詰まる。それでも順位は変わらない。4（常駐）は依存の軽さと利用者体験が低いので、どの重みでも 3 を上回らない。
- **グラフの 52 と 54（2 点差）**：差は利用者体験の 1 点だけから来ており、体験の重みを上げると差は 3 点に広がる。自前で描く量の差も考えると、52 を選ぶ判断は変わらない。

Node.js を許容しない場合に外れるのは 34（Quartz）だけで、どの軸の 1 位にも影響しない。Pagefind は pip で取得でき、cytoscape.js はファイルを同梱するだけなので、Node.js は要らない。

### 6.4 要件定義書・移植方針との差分

| 項目 | 現在の記述 | 本書の提案 | 扱い |
| --- | --- | --- | --- |
| D-03 VS Code + Foam | 人が読む・編集する環境 | 編集は Foam のまま。閲覧の補助として `/wiki:browse` を加える | D-03 に補助の位置づけを追記する案 |
| F-G01 Foam でリンク・被リンク・グラフを閲覧 | Foam が唯一の閲覧手段 | 閲覧画面でも被リンクと型付きグラフを出す。Foam の画面は残す | F-G01 は変えず、閲覧画面の要件を別に加える |
| O-08 Graph の初期範囲 | Foam での閲覧が基本 | 型付きの関係をページごとの表で出す（第 1 段階） | O-08 の判断材料にする |
| O-11 対応 OS | 未決 | 標準ライブラリと markdown-it-py だけで動くので、OS によらない構成にした | 変更なし |
| 第3.3節 派生データ | 索引とエクスポートは再生成できる | 既定ではファイルを書き出さない。書き出す場合もユーザーキャッシュに置く | 整合する |
| 移植方針 G | ホスト型 wiki は提供しない | 127.0.0.1 だけで待ち受けるサーバーは対象外と解釈する | ADR で解釈を残す |
| `marketplace.json` | 「9 本の /wiki:* コマンド」 | コマンドを追加すると 10 本になる | 実装時に更新する |

### 6.5 候補構成の比較

| 項目 | 構成 A：静的 HTML | 構成 B：ローカルサーバー（推奨） | 構成 C：既製の静的サイト生成器 |
| --- | --- | --- | --- |
| 部品 | 23、48〜51、57、58、62、64、67〜70、74、81、1 | 23、48〜51、52（第 2 段階）、57、58、62、64、67〜70、75、82、3、9 | Quartz v5（34）または MkDocs と Material（29）、その開発用サーバー |
| 実行環境の依存 | Python、uv、markdown-it-py | 構成 A と同じ。検索には既存の fastembed と sqlite-vec を使う | Node.js 22 以上と npm（Quartz）、または MkDocs 一式 |
| 日本語 | CSS と URL の規則は B と同じ。検索は bigram の簡易検索 | CSS と URL の規則に加え、`wiki_search.py` の日本語処理を使える | 生成器の既定に従う。日本語の別名キーは解釈しない |
| 日本語の全文検索 | 簡易（74） | `/wiki:query` と同じ検索（75） | 生成器の検索（日本語の精度は未確認） |
| グラフと被リンク | 被リンクと関係表 | 被リンク、関係表、全体のグラフ | 被リンクとリンクのグラフ（型付きの関係は描けない） |
| RAG との統合 | できない | 検索 API に検索元を加える | 生成器の改造が要る |
| 複数 Wiki | Wiki ごとに書き出す | 1 つのサーバーで切り替える | Wiki ごとにサイトを作る |
| 起動から最初の表示まで | 1,000 ページで数秒〜十数秒（推定） | 1,000 ページで数秒以内（推定）。最初の検索は埋め込みモデルの読み込みで数秒〜十数秒（推定） | 1,000 ページのビルドで数十秒（推定） |
| 実装の量 | Python 600〜900 行と CSS（推定） | Python 1,000〜1,500 行と JavaScript、CSS 300〜500 行（推定） | 変換と設定のスクリプト 200〜400 行。ただし日本語キーと型付きグラフは生成器の改造が別に要る（推定） |
| 主なリスク | `file://` の制約で機能が限られる | 自前の画面を保守する負担。ポートを開くことへの対策。サーバーは Claude Code のセッションの間だけ動く | 生成器の変化への依存。Quartz は v5 で設定の形式が変わり、Material は保守のみの状態にある |

### 6.6 推奨、次点、保留

**推奨：構成 B。** 6 つの軸のすべてで 1 位の選択肢がこの構成に入る。拡張の 4 方向（日本語検索、グラフ、RAG、複数 Wiki）をすべてサーバー側に加えられる。新しく加える依存は markdown-it-py（と第 2 段階の cytoscape.js）だけである。構成 A は B の変換部品で作れるので、`--static` のような副機能として B に含める。

**次点：構成 C（Quartz）。** Node.js を許容したので候補に残る。グラフ、被リンク、ポップアップが最初から揃い、画面の完成度は最も高い。PoC で B の画面の作り込みが想定より重かった場合に、比較のため試す。その場合も、日本語の別名キーをそろえる前処理と、`wiki_search.py` との連携は自前で書く必要がある。wikilink の照合で大文字小文字を区別しない点も、info-hive の規則に合わせる必要がある。

**保留：**

- 16 pywebview と 7 VS Code の拡張機能：専用の画面は作れるが、配布物と依存が増える。B が動いてから、需要があれば検討する。
- 10 desktop の mod：Claude desktop の利用者にしか届かない。B の URL を 9 のブラウザペインで開けば、ほぼ同じ体験になる。
- 13、14、15 PDF、DOCX、EPUB：ほかの人に渡す用途が出たら、B の HTML を印刷する形で加える。
- 92 ページ上から Claude Code に頼む：閲覧画面からエージェントを呼ぶ経路は、安全性の設計が別に要る。
- 94 ブラウザ上での編集：D-03 と範囲が重なる。
- 93、95、96：Wiki の運用が定着してから検討する。

### 6.7 日本語の扱い

| 項目 | 推奨 | 理由 |
| --- | --- | --- |
| 言語の指定 | `<html lang="ja">` を必ず付ける | ブラウザが日本語のフォントと禁則を選ぶ手がかりになる |
| フォント | OS 標準の日本語フォントを並べる（例：Windows は Yu Gothic UI と Meiryo、macOS は Hiragino Sans、Linux は Noto Sans CJK JP）。等幅は欧文の等幅フォントの後に日本語のゴシックを置く | 外部から読み込まない。フォント名は既定値で、仕様にはしない |
| 禁則と折り返し | `line-break: strict`、`word-break: normal`、`overflow-wrap: anywhere` | 行頭の句読点や閉じ括弧を避けつつ、長い URL やコードがはみ出さないようにする。`word-break: break-all` は日本語の語の途中でも折れるので使わない。`line-break: strict` は Chrome 25、Firefox 69、Safari 8 から使える |
| 和欧間の空き | `text-autospace` を対応するブラウザでだけ適用する | Chrome と Edge は 140、Safari は 18.4、Firefox は 145 から対応する。Chrome が対応する値は `normal` と `no-autospace` だけである。対応しないブラウザでは無視される |
| 文節での改行 | `word-break: auto-phrase` は既定にしない | 実験的な機能で、対応するのは Chrome と Edge の 119 以降だけである。Firefox は対応せず、Safari は試験版だけで動く。Chrome が対応する言語は日本語だけである。見出しにだけ試す余地はある |
| URL | ページの rel_path を NFC にそろえ、UTF-8 でパーセントエンコードする | macOS が NFD で保存したファイル名とも一致させる。既存のリンク解決と同じ正規化 |
| 見出し ID | 日本語のまま NFC にそろえ、重複したら連番を付ける。mdit-py-plugins の anchors に独自の slug 関数を渡して実現する | `[[slug#見出し]]` の解決規則と合わせる。anchors の既定の slug は小文字化と記号の削除を行うので、そのままでは規則が食い違う |
| 大文字小文字 | 経路の解決はページの一覧で行い、ファイルシステムに問い合わせない | Wiki は大文字小文字を区別し、NTFS は区別しない。その差で別のページが開くのを防ぐ |
| frontmatter | `canonical_meta()` で日本語の別名キーを英語にそろえてから描く。タグは NFKC にそろえる | lint や検索と同じ解釈にする |
| 文字コード | ファイルは UTF-8 を明示して読む。標準出力には ASCII の URL だけを出す | Windows の既定（cp932）で文字化けやエラーが起きないようにする |
| グラフのラベル | cytoscape.js のラベルにも CSS と同じフォントの並びを指定する | キャンバスに描くので、CSS のフォント指定はラベルに適用されない（推定） |

### 6.8 セキュリティ

| 対策 | 内容 |
| --- | --- |
| 待ち受けの範囲 | 127.0.0.1 だけで待ち受ける。ポートは既定で OS に空きを選ばせる |
| 起動ごとのトークン | 推測できない文字列を URL に含め、持たない要求は拒否する。同じ PC のほかの利用者や、ブラウザで開いた別のページからの要求を防ぐ |
| Host ヘッダーの確認 | `127.0.0.1` と `localhost` 以外の Host を拒否し、DNS リバインディングを防ぐ |
| 返すファイルの範囲 | ページの一覧にある rel_path だけを返す。任意のパスを解決せず、ディレクトリの一覧も出さない |
| 生の HTML | Markdown に書かれた生の HTML はエスケープする。markdown-it-py は引数なしだと生の HTML を出力するので、`js-default` の設定を使うか、html オプションの無効化を明示する |
| 外部への通信 | Content-Security-Policy で、同じ出所以外からの読み込みを禁じる。ローカル完結を仕組みで守る |
| 書き込み | 書き込みの API を作らない |
| 原資料へのリンク | `sources:` の原資料はパスを表示し、コピーできるようにする。Firefox は http のページから `file://` へのリンクを既定で開かない（Mozilla の管理者向け文書）。Chrome と Edge も開かないと報告されている（公式文書は未確認）。OS にファイルを開かせる API は S-07 と衝突するので作らない |
| サーバーの実装 | `http.server` は Python の公式文書で本番には勧められず、基本的な安全確認しか行わないとされている。コマンドラインから起動すると既定ですべてのインターフェースで待ち受け、`SimpleHTTPRequestHandler` はシンボリックリンクをたどってフォルダの外のファイルも返す。既製のハンドラは使わず、`ThreadingHTTPServer`（3.7 以降）に 127.0.0.1 を明示して渡し、自前のハンドラで上の対策を行う |
| 終了 | 操作がない状態が続いたら終了する。`/wiki:browse --stop` でも止められる |

### 6.9 起動と再生成

- `/wiki:browse` は、サーバーを別のプロセスとして切り離して起動し、URL を表示してすぐに戻る。Claude Code のコマンドが終わるまで待たされないようにするためである。切り離し方は OS で違う。Windows では `subprocess` の `DETACHED_PROCESS`、`CREATE_NEW_PROCESS_GROUP`、`CREATE_NO_WINDOW` を組み合わせ、POSIX では `start_new_session=True` を使う。
- Claude Code は終了時にバックグラウンドの処理を止め、macOS と Linux では setsid で切り離したプロセスも止める（公式文書）。サーバーはセッションの間だけ動くものとして設計し、セッションが終わったら止まってよいものとする。
- 起動したサーバーのプロセス ID、ポート、トークンをユーザーキャッシュに記録する。2 回目以降の呼び出しでは、生きているサーバーを再利用し、指定したページの URL だけを開く。
- ページの変換結果はメモリに置き、ファイルの更新時刻が変わったページだけを変換し直す。被リンクとグラフは、どれかのページが変わったときに作り直す。
- 常駐させる場合は、Claude Code ではなく OS の自動起動から起動し、無操作での終了を無効にする設定を加える。ファイルの監視は、まず要求のたびに更新時刻を確かめる方式にし、外部ライブラリを使った監視は必要になってから加える。
- 複数の Wiki は、URL に Wiki の識別子を含めて切り替える（例：`/w/<wiki-id>/<rel_path>`）。別の Wiki への相対リンクは、起動時に渡した Wiki の中にあれば解決し、なければ外部の参照として示す。
- Claude desktop を使っている場合は、Claude が URL をブラウザペインで開ける。公式文書によれば、ブラウザペインは 127.0.0.1 などのローカルの URL を開ける。CLI の利用者は既定のブラウザで開く。どちらでもない環境（SSH 先など）では、URL を表示するだけにする。

---

## 7. 次のステップ

### 7.1 先に決める事項（ユーザーの判断）

| 事項 | 選択肢 | 影響 |
| --- | --- | --- |
| 構成 | **提案**：構成 B（構成 A を副機能として含む）／構成 C（Quartz）を先に試す | 実装の量と、画面の完成度 |
| 方針 G の解釈 | **決定済み**：ローカルサーバーを検討対象に含める。ADR に残すかを決める | 移植方針と要件定義書の記述 |
| 起動の既定 | 必要なときだけ起動し、無操作で終了／常駐 | 常駐の場合、Claude Code の終了とともに止まらないよう、OS の自動起動から起動する仕組みが要る |
| D-03 の改訂 | 閲覧の補助として `/wiki:browse` を追記する／しない | 要件定義書の D-03、F-G01、AC-D02 |
| 対応 OS | Windows だけ／Windows・macOS・Linux（O-11） | Linux を含めると、Noto Sans JP の同梱（65）を検討する |
| 段階の順序 | 第7.2節の順／検索を先に作る | 最初に使えるようになる機能 |

### 7.2 PoC の手順

1. **共通部品を切り出す（info-hive 側）。** `resolve_link()` と wikilink の正規表現を共通モジュールに移し、`wiki_lint.py` と `wiki_search.py` から呼ぶ。既存のテスト（`test_link_resolution.py`）がそのまま通ることを確かめる。
2. **第 1 段階：読む画面を作る。** `/wiki:browse [slug|検索語]` を加える。ページの表示、`index.md` からのナビゲーション、メタ欄、被リンク、ページごとの関係表、未解決リンクの表示、日本語の CSS、第6.8節の安全対策を入れる。
3. **第 2 段階：探す画面を作る。** 検索 API（`wiki_search.py` の `--json` と同じ形の結果）と検索欄、cytoscape.js による全体のグラフ、`/wiki:query` の回答に添える URL を加える。
4. **第 3 段階：広げる。** 複数 Wiki の切り替え、静的 HTML の書き出し（構成 A）、PDF の RAG の検索結果から元のページや原資料の参照先へ移る導線を加える。RAG は `docs/research/japanese-pdf-local-rag-options.md` の構成が決まってから行う。
5. **結果を設計書に反映する。** 方針 G の解釈と構成の選定を ADR として `docs/adr/` に残し、要件定義書の D-03 と O-08 を更新する。

第 1 段階と第 2 段階の合格の目安は次のとおりとする（提案）。

| 計測項目 | 合格の目安 |
| --- | --- |
| 日本語のページ | `eval/retrieval/ja/corpus/wiki/` の全ページが開け、日本語のファイル名と `[[slug#見出し]]` のリンクで移動できる |
| リンクの解決 | 未解決リンクの一覧が、同じ Wiki に対する `wiki_lint.py` の結果と一致する |
| 禁則と折り返し | 行頭に句読点や閉じ括弧が来ない。長い URL やコードが本文の幅からはみ出さない |
| 起動の速さ | 1,000 ページの合成 Wiki で、コマンドの実行から最初のページの表示まで 5 秒以内 |
| 外部への通信 | ブラウザの開発者ツールで、127.0.0.1 以外への要求が 0 件 |
| 安全性 | 127.0.0.1 以外からの接続、トークンのない要求、ページの一覧にないパス（`../` を含む）への要求を拒否する |
| OS | CI の windows-latest と ubuntu-latest で、起動と終了のテストが通る |
| 依存 | Python と uv だけで動く。Node.js を要しない |

コマンドを追加するときは、次のファイルもあわせて更新する。

- `info-hive/.claude-plugin/marketplace.json`（「9 本の /wiki:* コマンド」の本数）
- `info-hive/docs/commands.md`、`info-hive/README.md`、`info-hive/skills/info-hive/SKILL.md`
- `info-hive/CHANGELOG.md`
- `info-hive/eval/check_encoding.py`（`webbrowser` などのモジュールの検査対象）

---

## 8. 本書で確認できなかったこと

改訂時に一次資料で確かめた結果、残った未確認の事項は次のとおりである。

- Quartz v5 の検索の実装。日本語を 1 文字ずつ照合する方式は v4 のソースで確かめた
- Quartz の日本語のファイル名での wikilink の解決
- Zensical が wikilink に対応するかどうか
- Docsify が `file://` で動かないことの公式の記述。公式文書はサーバーでの起動だけを案内している
- Chrome と Edge が、http のページから `file://` へのリンクを開かないことの公式の記述
- Pagefind が `file://` で動かないことの公式の記述。索引の取得に失敗する報告（issue #482）はある
- Claude Code の終了時に、Windows で切り離したプロセスも止められるかどうか
- `obsidian://open?path=` で未登録のフォルダを保管庫として開けるかどうか
- Foam が VS Code 標準のプレビューで wikilink をリンクとして描くかどうか（文書の該当ページを取得できなかった）
- VS Code の CLI や `vscode://` の URI から Markdown のプレビューを直接開く公式の方法。調べた範囲では存在しない
- MkDocs 2.0 の仕様。根拠は Material for MkDocs のブログで、MkDocs の公式の発表は確かめていない
- 検証環境の VS Code と Foam の有無
- 第6.5節の起動時間と実装の量（いずれも推定で、PoC で測る）

---

## 9. 参照資料

確認日はすべて2026年11月3日。

### 変換エンジンと静的サイト生成器

- mdit-py-plugins（Arch Linux のパッケージ、ライセンス）：https://archlinux.org/packages/extra-testing/any/python-mdit_py_plugins
- mdit-py-plugins（Anaconda、版の一覧）：https://anaconda.org/anaconda/mdit-py-plugins
- Python-Markdown の WikiLinks 拡張のソース：https://sources.debian.org/data/main/p/python-markdown/3.7-2/markdown/extensions/wikilinks.py
- mistune（GitHub）：https://github.com/lepture/mistune 、パッケージのメタデータ：https://codegraph.jelmer.uk/mistune/3.1.4-1/README.rst
- Material for MkDocs の検索プラグイン：https://squidfunk.github.io/mkdocs-material/plugins/search
- MkDocs の日本語検索の修正（PR #2178）：https://github.com/mkdocs/mkdocs/pull/2178
- Material for MkDocs の日本語検索の不具合報告（#1854）：https://github.com/squidfunk/mkdocs-material/issues/1854
- Material for MkDocs が保守のみになったことの記述：https://pydevtools.com/handbook/reference/mkdocs-material/ 、https://github.com/BHoM/documentation/issues/132
- Zensical（ライセンスと概要）：https://awesome.ecosyste.ms/projects/github.com%2Fzensical%2Fzensical 、https://www.linuxlinks.com/zensical-modern-static-site-generator/
- mkdocs-obsidian-bridge：https://github.com/GooRoo/mkdocs-obsidian-bridge
- mkdocs-ezlinks-plugin：https://awesome.ecosyste.ms/projects/github.com%2Forbikm%2Fmkdocs-ezlinks-plugin
- Quartz（リポジトリとライセンス）：https://github.com/jackyzha0/quartz 、Node.js の要件：https://git.mak-sim.ru/maksim/quartz/src/branch/v4/docs/index.md
- Docsify：https://awesome.ecosyste.ms/projects/github.com%2Fdocsifyjs%2Fdocsify
- mdBook（ライセンス）：https://github.com/azerupi/mdBook
- pandoc の wikilinks 拡張のテスト：https://hackage.haskell.org/package/pandoc-3.8/src/test/command/wikilinks_title_after_pipe.md

### 検索

- Pagefind のリリースノート（CJK の分割、Python パッケージ）：https://fatihky.github.io/clhub/npm/pagefind/compare 、0.7.0：https://fatihky.github.io/clhub/npm/pagefind/0.7.0
- Pagefind の版とライセンス：https://www.jsdelivr.com/package/npm/@pagefind/linux-x64
- Pagefind を `file://` で使えないことを示す例：https://code.ornl.gov/nix/nixpkgs/-/commit/0a35428c2ee657265aa1ba198664296eded41176
- `file://` で検索データを読めない一般的な例：https://www.helpndoc.com/documentation/html/GoogleChromeshowsanerrorwhensear.html
- MiniSearch に CJK の分割を与えた例：https://github.com/campfirein/byterover-cli/pull/712
- `Intl.Segmenter`（MDN の写し）：https://www.cs.unb.ca/~bremner/teaching/cs2613/books/mdn/Reference/Global_Objects/Intl/Segmenter

### グラフ

- cytoscape.js のライセンス：https://central.sonatype.com/artifact/org.mvnpm/cytoscape
- vis-network のライセンス：https://github.com/visjs/vis-network

### 日本語の表示

- `word-break`（MDN）：https://developer.mozilla.org/en-US/docs/Web/CSS/word-break
- `word-break: auto-phrase` の対応状況：https://web-platform-dx.github.io/web-features-explorer/features/word-break-auto-phrase
- `text-autospace` の対応状況：https://caniuse.com/mdn-css_properties_text-autospace 、https://web-platform-dx.github.io/web-features-explorer/features/text-autospace
- Noto Sans JP のライセンス：https://launchpad.net/debian/sid/+source/fonts-noto-cjk/+copyright 、https://github.com/w3labkr/noto-cjk

### 実行環境と周辺のツール

- Python `http.server` の注意書き：https://docs.python.org/3.11/library/http.server.html
- Claude Code desktop（プレビューと `.claude/launch.json`）：https://code.claude.com/docs/en/desktop
- VS Code の Markdown プレビュー：https://vscode-docs-arc.readthedocs.io/en/latest/languages/markdown/
- Foam：https://awesome.ecosyste.ms/projects/github.com%2Ffoambubble%2Ffoam
- Obsidian のライセンス（2025年2月20日から仕事でも無料）：https://obsidian.md/blog/free-for-work/ 、https://obsidian.md/license
- pywebview の WebView2 対応（#521）：https://github.com/r0x0r/pywebview/issues/521
- Textual の MarkdownViewer：https://textual.textualize.io/widgets/markdown_viewer/

### 改訂時に確かめた一次資料

確認日はすべて2026年11月3日。

- markdown-it-py（PyPI）：https://pypi.org/project/markdown-it-py/ 、既定の設定：https://raw.githubusercontent.com/executablebooks/markdown-it-py/master/markdown_it/presets/default.py 、安全性：https://markdown-it-py.readthedocs.io/en/latest/security.html
- mdit-py-plugins（PyPI）：https://pypi.org/pypi/mdit-py-plugins/json 、プラグインの一覧：https://mdit-py-plugins.readthedocs.io/en/latest/ 、anchors：https://raw.githubusercontent.com/executablebooks/mdit-py-plugins/master/mdit_py_plugins/anchors/index.py
- Python-Markdown（PyPI）：https://pypi.org/pypi/markdown/json 、ライセンス：https://raw.githubusercontent.com/Python-Markdown/markdown/master/LICENSE.md 、WikiLinks：https://python-markdown.github.io/extensions/wikilinks/
- mistune（PyPI）：https://pypi.org/project/mistune/ 、プラグイン：https://mistune.lepture.com/en/latest/plugins.html
- pandoc のライセンス：https://raw.githubusercontent.com/jgm/pandoc/main/COPYRIGHT 、3.0 のリリース：https://github.com/jgm/pandoc/releases/tag/3.0
- pywebview（PyPI）：https://pypi.org/project/pywebview/ 、導入：https://pywebview.flowrl.com/guide/installation.html
- Textual のライセンス：https://raw.githubusercontent.com/Textualize/textual/main/LICENSE 、rich の文字幅：https://raw.githubusercontent.com/Textualize/rich/master/rich/cells.py
- Quartz の package.json（v5）：https://raw.githubusercontent.com/jackyzha0/quartz/v5/package.json 、検索：https://quartz.jzhao.xyz/features/full-text-search 、wikilink：https://quartz.jzhao.xyz/features/wikilinks 、設定：https://quartz.jzhao.xyz/configuration
- Material for MkDocs の保守の告知：https://squidfunk.github.io/mkdocs-material/blog/2025/11/11/insiders-now-free-for-everyone/ 、MkDocs 2.0：https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0 、変更履歴：https://squidfunk.github.io/mkdocs-material/changelog/
- Zensical（PyPI）：https://pypi.org/pypi/zensical/json 、日本語の検索（v0.0.52）：https://github.com/zensical/zensical/releases/tag/v0.0.52 、互換性：https://zensical.org/compatibility/
- mdBook の日本語の検索の問題：https://github.com/rust-lang/mdBook/issues/2052
- Obsidian URI：https://obsidian.md/help/Extending+Obsidian/Obsidian+URI
- Pagefind の多言語対応：https://pagefind.app/docs/multilingual/ 、Python API：https://pagefind.app/docs/py-api/ 、リリース：https://github.com/CloudCannon/pagefind/releases 、`file://` での失敗の報告：https://github.com/CloudCannon/pagefind/issues/482
- Firefox の `file://` へのリンクの制限：https://firefox-admin-docs.mozilla.org/reference/policies/localfilelinks/
- 同一出所ポリシーと `file://`（MDN）：https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy 、Firefox 68 の修正：https://www.mozilla.org/en-US/security/advisories/mfsa2019-21/
- Chrome の日本語向けの CSS 機能：https://developer.chrome.com/blog/css-i18n-features
- VS Code のコマンドライン：https://code.visualstudio.com/docs/editor/command-line 、Markdown：https://code.visualstudio.com/docs/languages/markdown
- Python `subprocess`：https://docs.python.org/3/library/subprocess.html 、`http.server`：https://docs.python.org/3/library/http.server.html 、`webbrowser`：https://docs.python.org/3/library/webbrowser.html
- Claude Code のバックグラウンドの処理：https://code.claude.com/docs/en/interactive-mode

### リポジトリ内の資料

- 要件定義書：`llm-wiki-product-concept-and-requirements-ja.md`（D-03、F-G01、S-07、O-08、O-11、第3.3節、第4.2節）
- 移植方針と削除した機能：`info-hive/UPSTREAM.md`、`info-hive/CHANGELOG.md`
- 既存の部品：`info-hive/skills/info-hive/scripts/wiki_text.py`、`wiki_lint.py`、`wiki_search.py`、`init_wiki.py`
- PDF の RAG の設計選択肢：`docs/research/japanese-pdf-local-rag-options.md`

---

## 10. ルーブリックによる自己採点

`.claude/skills/brainstorm-diverge-converge/resources/evaluators/rubric_brainstorm_diverge_converge.json` の 10 基準で採点した。

| 基準 | 点 | 根拠 |
| --- | --- | --- |
| 発散の量 | 5 | 96 件（50 件以上） |
| 発散の多様性 | 5 | 表示経路、変換エンジン、リンクとグラフ、日本語、検索、組み込みの 6 系統。Python、Node.js、単一バイナリ、別アプリ、LLM の各方式を含む |
| 発散の創造性 | 4 | W の案が 22 件（mod のペイン、MCP リソース、LLM による生成、3D グラフ、Anki など）。既存の方法の延長が多い |
| クラスタの質 | 4 | 7 つのクラスタに、それぞれ決めることを書いた。C4 は番号が連続していない |
| クラスタの範囲 | 4 | 4〜8 の範囲で重なりが少ない。C7 は採点しない保留の集まり |
| 評価基準の明確さ | 5 | 8 基準に重みと定義を付け、依頼の 3 要件とユーザーの決定から重みを決めた |
| 採点の厳密さ | 4 | 全候補を全基準で採点し、極端な点に根拠を書き、感度分析を行った。ライセンス、版、対応状況は一次資料で確かめた。多くの点数は実測でなく判断である |
| 選定の質 | 5 | 各軸で 1 位を選んだ理由と、2 段階にした軸の理由、構成の比較、次点と保留を書いた |
| 実行可能性 | 4 | 段階ごとの作業と合格の目安を示した。担当者と期日は決めていない |
| 過程の健全さ | 5 | 発散では除外せず、必須条件による除外は第2.4節で行った |
| 平均 | 4.5 | |
