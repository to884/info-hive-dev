## 判定

**却下。確信度：高。** 表示上の訂正印や語の境界を見落とす反例と、照合できなかったページを除いて過大な confidence を成功として返す反例を再現した。重大な欠陥は3件ある。

## 致命的・重大な欠陥

1. **【重大】wikilink を表示される文字へ変換しておらず、前回と同じすり抜けが残る。**

   raw を `uploaded`・200行とし、L1 に `15`、L2 に `5`、L3 に `50` を置く。親ページは `confidence: "high"` とする。

   次の本文と定義は、検査を通った。

   ```markdown
   [[1]]5〔訂正 L1-1〕

   ## 字幕の訂正と留保

   - L1-1: 字幕 `15` を `5` に訂正（根拠 caption:L2）
   ```

   閲覧側の表示文字列は `15〔訂正 L1-1〕` で、数値は訂正されていない。しかし照合側は `[[1]]5` を読み、`5` の前を数字ではなく `]` と判定する。`[[x|1]]5〔訂正 L1-1〕` でも通る。

   また、本文を次にすると、**定義なしでも通った**。

   ```markdown
   50〔[[訂正]] L1-1〕
   ```

   閲覧側は `50〔訂正 L1-1〕` と表示するが、照合側は印も `bad_mark` も検出しない。`50〔訂[[正]] L1-1〕` でも同じだった。リンク先のページは存在する状態にできるため、リンク切れに依存する反例ではない。

   実測は、前者が重み1、後者が重み0。どちらも **verify 終了コード0、`findings: []`、confidence `high`、`unknown_words: {}`、lint の `caption_corrections: []`**。

   根拠：[wiki_captions.py:574](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:574) は text トークンをそのまま連結する。一方、閲覧側の [wiki_browse_core.py:412](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:412) は wikilink を表示名へ変換する。ADR 101行目の、表示される文字で境界を見て印内のリンクを誤りにする規則と食い違う。

2. **【重大】複数 raw のページを検出しても、対象 raw への絞り込みで指摘が消える。**

   次の状態で再現した。

   - `raw/a.md` と `raw/b.md` は、それぞれ `uploaded`・200行。
   - `sources/a.md` と `sources/b.md` は、それぞれの raw を参照する正常な親ページ。confidence は `high`。
   - `sources/a-2.md` は、A の字幕 `15` を `50` に訂正する印と、`model:x` の定義を持つ。
   - 子ページの `raw` を `["raw/a.md", "raw/b.md"]` にする。

   子が A だけを参照する状態では、A の重みは3、confidence は `medium` となり、親の `high` に `confidence_mismatch` が出る。

   配列に B を加えると、全体検査では `several_video_raws` などを報告する。しかし、そのページは `summaries` から外れるため、`only_raw="raw/a.md"` の関係ページにも入らない。ページに付いた指摘がすべて捨てられ、子の定義も数えられない。

   **A に対する verify は終了コード0、指摘なし、重み0、confidence `high`** になった。正常な親ページがあるため、今回追加した `no_summary` も出ない。

   根拠：[wiki_captions.py:969](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:969) の複数 raw の除外と、[同ファイル:1141](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1141) の指摘の絞り込み。ADR 112行目の「照らせない形を黙って除かない」に食い違う。

3. **【重大】ディレクトリを列挙できない場合は、引き続き訂正を黙って除外する。**

   親 `sources/a.md` は `uploaded`・200行の raw を参照し、confidence を `high` とする。子 `sources/split/a-2.md` に、同じ raw を参照する `model` の訂正を1件置く。

   子のあるディレクトリの一覧取得だけを `PermissionError` にして比較した。

   | ディレクトリの一覧取得 | verify | 計算した confidence | 重み |
   | --- | --- | --- | --- |
   | 成功 | 終了コード1、`confidence_mismatch` | `medium` | 3 |
   | `PermissionError` | **終了コード0、指摘なし** | **`high`** | **0** |

   実際の走査処理は `unlistable: ["sources/split"]` を返していた。しかし `iter_page_files` がその情報を捨てるため、`load_pages` の読み取り例外処理まで到達しない。lint の `caption_corrections` も空になった。

   根拠：[wiki_captions.py:1192](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1192) が使う [wiki_pages.py:324](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:324) は、明記されているとおり走査の知らせを捨てる。ディレクトリの拒否を記録する処理は [wiki_pages.py:245](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:245) にある。

## 崩れる前提

- **同じ Markdown パーサーを使えば、同じ表示文字列を得られる。** 閲覧側が後処理で wikilink を表示名へ変えるため崩れる。
- **正常に分類できた要約ページから、対象 raw に関わるすべての指摘を選べる。** 複数 raw を持つため分類から外したページで崩れる。
- **列挙されたファイルの読み取り失敗を報告すれば、不完全な読み取りを検出できる。** ディレクトリの列挙や項目の判別に失敗し、ファイルが一覧に入らない場合に崩れる。

## 見落としと軽微な問題

**【軽微】区間を一つも持たない raw を `parse_raw` が受理する。**

生成した raw の、最初の `## 区間 …` 以降をすべて削り、frontmatter と先頭見出しだけを残すと、`parse_raw` は `count=0`、`sections=0` で受理した。正常な親ページを添えた `check_pages` も指摘なしで、confidence `high`、疑いの率 `None` を返した。

生成器は必ず一つ以上の区間を作るため、「生成器と同じ形だけを受け入れる」という説明には一致しない。ただし、字幕から生成処理を通じてこの状態を作る経路は示せていない。

根拠：[wiki_captions.py:340](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:340) は、区間の記録が空でも再構成結果の一致だけで受理する。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 試験は44件 | 一致。収集件数は44件 |
| ファイルを書かない既存4クラス | 20件成功 |
| `**1**5`、通常のリンク、コード直後の数字の境界 | 修正と一致。`mark_tail` を検出 |
| `〔**訂正** …〕`、`〔訂**正** …〕` | 修正と一致。`bad_mark` を検出 |
| 個別ファイルの `PermissionError` | 修正と一致。`unreadable_page` を検出 |
| 複数 raw のページを黙って除かない | 全体検査では一致。対象 raw に絞る verify では食い違い |
| raw 末尾へのフェンスや「字幕はない」の追加を拒否 | 該当する既存試験が成功 |
| 固定した yt-dlp による実取得、実ファイルの公開・競合 | 確かめていない |

反例はファイル操作をメモリ上の素材に差し替え、実際の解析・照合・verify・lint を通して検証した。全44件の実行は一時ファイルを作るため行っていない。リポジトリのファイルは変更していない。

## 崩せなかった点

- 字幕の改行、偽の行番号、見出し、バッククォート列による、生成処理を通じた raw の構造の偽造。
- 今回修正した通常の強調・Markdown リンク・コードをまたぐ語と印の検出。
- 個別ページを読めない場合の、`only_raw` によらないエラー報告。
- 通常形のトラック情報での自動翻訳の除外、自動字幕の統合、曖昧な候補での停止。
- confidence の計算式そのもの。今回の水増しは、計算対象から印や定義が落ちる経路だった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
