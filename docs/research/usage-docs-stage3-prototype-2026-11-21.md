# 利用者向け文書の試作（2026-11-21）

試作の対象は、`info-hive-wiki` 0.39.1 の W1「はじめての wiki を作る」と、入口 P0 の図。W1 の本文は [段階 2 の検証記録](usage-docs-facts-2026-11-20.md#確認-5-のチュートリアル-3-回) に基づく。HTML はプラグインの `codex/usage-docs-prototype` worktree の `docs/`、PDF は `C:\stage2-records\autotest\stage3-wiki-prototype.pdf` に置いた。

## 試作で確認したこと

| 対象 | 確認結果 |
| --- | --- |
| PC とスマートフォンの幅 | Chromium で明色・暗色の 1,280 px と明色の 320 px。目次の 4 項目が対応する節に移動し、横スクロールが出ない。入口と W1 の相互リンク、キーボードで最初に選べる「本文へ移動」も確認した。 |
| PDF | Vivliostyle CLI 11.5.0、Vivliostyle.js 2.46.0 で A4 の 3 ページ。1 ページ目は P0 の図、2 ページ目は W1 の目次と手順 1・2、3 ページ目は手順 3・4。文書内リンク 8 件と外部リンク 2 件、日本語の書体の埋め込み、`/wiki:ingest raw/味噌.md` の文字列の抽出を確認した。暗色を指定した Chromium の印刷でも、白地に暗い文字で出力した。 |
| 試作の前後リンク | P0 から W1 の準備を開ける。W1 の次のリンクには、既存の 0.39.1 の取り込みと点検の文書を使う。製品版の C1 と W2 の HTML は計画の段階 4 で作る。 |

印刷用 CSS で節とコードブロックの余白を調整し、本文やナビゲーションがわずかに残るページをなくした。コードの印刷には日本語と英数字を含む BIZ UDGothic を使い、混在するコマンドから余分な空白が抽出される現象を解消した。[Vivliostyle CLI の組版手順](https://docs.vivliostyle.org/en/cli/getting-started/)

## Diátaxis とレビュー

W1 は Code タブでプラグインの導入を終えた初めての利用者向けのチュートリアル。プロジェクトの wiki を作って練習用の原本を取り込み、出典のある答えを得るまでを 1 本の手順にした。障害の診断は既存の文書にリンクした。P0 は資料・wiki のページ・出典付きの答えの関係を示して W1 に案内する入口。W1 の HTML にある原本は、3 回使った確認表の原本と文字列で一致した。改訂後の HTML を最初から読んで VM で実行する試験と、Code のブラウザペインでの HTML の表示は未確認。

Opus 5.5（effort high）の初回レビューは、開始条件、メモ帳が付ける拡張子、暗色環境での印刷の 3 点を重大とした。導入前提と検証版を明記し、古い導入リンクを準備へのリンクに置き換えた。保存時のファイルの種類と文字コード、エクスプローラーでの見分け方を追記した。印刷時に明色トークンを適用し、暗色からの印刷を再検証した。紙を前提とした外部 URL の欄外表記は、今回は PDF のクリックできるリンクで確認した。原文と再検証の結果は `C:\stage2-records\autotest\stage3-opus-review.md`、`stage3-html-check.txt`、`stage3-pdf-check.txt` にある。

練習用の味噌の文章は 3 回の試行で使った原文を掲載した。公開時には熟成期間以外にも色に影響する条件があること、米・麦・豆の組み合わせで調合味噌もあることを踏まえて、例文の範囲を見直す。[農林水産省の伝統食図鑑](https://www.maff.go.jp/j/keikaku/syokubunka/traditional-foods/bunrui/shouyu-miso.html) [みそ健康づくり委員会の資料](https://miso.or.jp/museum/pdf/new_learn_about_miso.pdf)

## 公開前に決めること

| 項目 | 案と影響 |
| --- | --- |
| PDF | 試作に使った Vivliostyle を採用する案。組版コマンドと CLI の版を固定し、日本語の書体がある環境で出力を確認する。PDF の配布場所は HTML の公開方法と合わせて決める。 |
| HTML の公開先 | GitHub Pages の `/vX.Y.Z/` に公開版ごとの HTML と CSS を置く案なら、古い版からも対応する文書を開ける。`wiki_help.py` は公開済みの版の HTML を対応する Pages の URL に変換する。旧版の Markdown リンクは従来の GitHub のタグを使う。リリース時にタグと同じコミットから配置し、HTML、CSS、`/wiki:help` のリンクを照合する。 |
| HTML の公開先の別案 | GitHub Pages から最新の文書だけを配る案なら、公開が単純になる。古いプラグインの `/wiki:help` も新しい手順を開くため、ADR-0022 の版の対応を見直す。最新 URL への書き換えとリリース時の表示を確認する。 |

GitHub Pages にはブランチと GitHub Actions のどちらからでも公開できる。版ごとの配置を作る案では Actions の公開用成果物に各版をまとめる。[GitHub Pages の公開元](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

## HTML の導線を確認した結果

入口、チュートリアル、ハウツー、リファレンス、解説の 14 ページを `docs/` の相対リンクでつないだ。Chromium で 131 件のリンクが同じディレクトリ内の HTML に到達することと、12 本のコマンド書式が wiki 0.39.1 の定義と一致することを確認した。練習用の原文 2 件は段階 2 の確認表と一致した。結果は `C:\stage2-records\autotest\html-manual-check.txt` に残した。

Opus 5.5（effort high）の指摘を受け、VM の Claude 6.6395 の Code タブでマーケットプレイスの追加画面とディレクトリを開いた。「リポジトリから追加」、「URL」欄、「info-hive」の一覧を確認して導入手順を修正した。導入済みの状態で画面を観測したため、6.6395 での再インストールは行っていない。`winget` のパッケージ ID は取得できることを確認した。Claude と uv は段階 2 では別の方法で入れた。スクリーンショットは `C:\stage2-records\autotest\html-guide-code-marketplace-dialog.jpg` と `html-guide-code-directory.jpg` にある。

## 左の目次と README の表示

入口の左に README の見出しと各ガイドの目次を置き、右の先頭に wiki プラグインの README を HTML に変換して載せた。狭い画面では目次を本文の上に置く。 `tools/docs/render_readme.py` はプラグイン同梱の markdown-it-py を使い、既存の README から生成する。

Opus 5.5（effort medium）の指摘を受け、ワークフロー、旧版からのアップグレード、MCP サーバーは対応する Markdown の本文をそれぞれ HTML に変換した。README の見出し ID に接頭辞を付け、本文内のローカルリンクに対応する HTML がない場合に生成を停止する。Chromium で 320〜1,440 px の配置、目次、キーボード操作、README の見出し・表・コマンド例を確認した。25 ページのリンク 214 件がすべて HTML 内で到達し、再生成で差分が出ないことを確認した。結果は `C:\stage2-records\autotest\html-readme-check.txt` と `html-manual-check.txt` にある。

## 図解と導入先を入口に置く

`big-pics-little-words` を使い、右側の先頭で「資料を入れる → wiki に整理する → 質問に答える」を図解した。左の目次を保ち、README は図の下から読める。旧 `docs/index.md` は HTML への案内にした。

Windows の導入手順は、段階 2 の記録に合わせて Claude の公式 MSIX、Astral の uv インストーラー、Code タブのマーケットプレイスの順に案内する。自動化用の起動方法や非対話オプションは、読者向けの対話手順に置き換えた。HTML 更新後の VM での再インストールは行っていない。PC とスマートフォンの幅で目次と図を表示し、文書リンクがすべて HTML 内で開くことを確認した。

入口では「Claude デスクトップ（Windows）」と「Codex CLI」を別の導入先として示す。Codex CLI はエージェント別の HTML の該当節へ直接進める。uv の準備も同じ HTML 文書群で完結する。Opus 5.5（effort medium）のレビューを受け、Windows の uv のコマンドも共通の準備ページに載せた。生成器は `tools/docs/render_readme.py` として開発リポジトリに置き、再生成で `#codex-cli` と uv へのリンクが変わらないことを確認した。

## HTML の配置

利用者向け HTML と表示用アセットは `info-hive-wiki/docs/html/` にまとめた。入口は `docs/html/index.html`。このフォルダーのコピーでも Chromium から 25 ページを表示し、文書リンク 221 件をたどれることを確認した。README、旧 `docs/index.md`、開発側の生成器は新しい配置を使う。[ADR-0022](../adr/0022-usage-docs-are-html-in-plugin-docs.md)
