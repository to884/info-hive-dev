## 判定

**却下。確信度：高。** 6版目で加えた身元確認でも、同じセッションの別の raw を誤って選べる。また、実在する raw を `missing` としてよいという説明は、書く段の作業用領域を守る契約と食い違う。

以下は設計から導いた静的反例である。未実装の resolver や書く段の実行結果ではない。

## 致命的・重大な欠陥

### 1. 重大：`session_id` の一致では、参照した raw と同じ版か確かめられない

**主張：** 同じセッションから作った異なる raw を、161行の身元確認が区別できない。前回の「無関係なファイルを選ぶ」問題は、異なる `session_id` の場合にしか閉じていない。

**反例：**

```text
C:/view/wiki                 → D:/store/wiki へのディレクトリリンク
C:/view/raw/session.md       raw A：session_id=S、12ターン
D:/store/raw/session.md      raw B：session_id=S、2ターン
```

両方とも通常ファイルである。A と B は、同じセッションを異なる `--before` や伏せ字の決定で取り込んだ結果とする。

1. A を保存したときの source ページには、`session_id: S`、`raw: raw/session.md` を書く。本文には A の `T12` を根拠として記す。
2. 後日、wiki を `D:/store/wiki` で渡す。
3. resolver が列挙する候補には B だけが存在する。
4. B の `session_id` は一致するので、161行の契約では B が `resolved` になる。
5. 問い合わせは、参照した A ではなく、`T12` すら存在しない B を原本として読める。

同じ URL の異なる取得版にも、URL だけによる確認では同型の問題がある。

**根拠・照合結果：食い違い。**

- [対象設計161行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:161)は、セッション raw の身元を `session_id` だけで確認する。
- [165行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:165)の追加試験も、別ファイルの `session_id` が異なる場合だけを扱う。
- 指定版 `2452f59` の [wiki_session.py:31](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:31)には、抽出結果を変える `--before`、`--tools` などがある。[1052行](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:1052)では、`session_id` と別に `source_sha256`、`cut_before`、抽出設定を raw に記録する。
- 指定版から `frontmatter_fields()` を抽出したメモリ上の確認でも、**同じ `session_id`、異なる `source_sha256`・`cut_before`・ターン数**を持つ出力が成立した。

保存時の綴りを再び問題にした指摘ではない。今回の欠陥は、その欠落を補うために新設した「身元」が、raw の版を識別しないことである。

### 2. 重大：「wiki の外の raw は守りに要らない」は、作業用領域への書き込みに対して成立しない

**主張：** 書く段が守るのは wiki 内の行き先だけではない。実在する外部 raw を保護集合から落とすと、`K` やデータの場所と raw の重なりを検出できない。

**反例：**

```text
C:/view/wiki                 → D:/store/wiki
C:/view/raw/session.md       保存した raw A
D:/store/raw/session.md      存在しない

source ページ:
    session_id: S
    raw: raw/session.md

INFO_HIVE_DATA_DIR = C:/view/raw
今回の raw_root = D:/new-raw
raw-roots.json に過去の根の記録はない
```

書く段を導入する前の取り込みで A を保存しており、今回が最初の `begin` とする。Git の無視設定など、ほかの拒否条件には当たらない配置とする。

1. `D:/store/wiki` を渡すと、保存時の基準 `C:/view` は候補に入らず、A は `missing` になる。
2. 149・162行に従えば、依存収集を完全として扱える。
3. A の親 `C:/view/raw` が、守る raw のルートから落ちる。
4. `begin` は `data_dir()/apply/work/…`、つまり **過去の raw の根の中**に作業用フォルダーを作れる。
5. 本来必要な `raw_overlap` の拒否が発生しない。

**根拠・照合結果：既存設計と食い違い。**

- [対象設計162行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:162)は、wiki の親を基準にした raw は wiki の外なので、守りに要らないと説明する。
- しかし、[書く段の設計673行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md:673)は、**wiki の外の raw からも、その親を保護対象のルートに加える**。
- [同679行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md:679)は、そのルートと `K`、`data_dir()` の重なりを、`begin` が作業用フォルダーを作る前から拒む。
- [同667行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md:667)は、「`INFO_HIVE_DATA_DIR` で作業用領域を過去の raw の中に置く」配置を、まさにこの検査で止めると明記する。

この反例で確認できるのは、raw 内への作業用データの書き込みを許す契約違反である。既存 raw のバイト列が必ず上書きされる、とは主張しない。

前回の解決失敗の再掲ではなく、**6版目が解決失敗を許容する根拠として加えた説明が、維持するとした原本保護を覆っていない**という指摘である。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| `session_id` が一致すれば、そのページが参照した raw である | 同じセッションを異なる範囲や伏せ字の決定で取り込む |
| URL が一致すれば、参照した Web raw である | 同じ URL を別の日時・設定で取得する |
| wiki の外の raw は、書く段の保護に不要である | `K` または `INFO_HIVE_DATA_DIR` が、その raw の親と重なる |
| 身元確認後の `missing` は、守る実体が存在しないことを意味する | 保存時の基準が候補集合から欠けている |

## 見落としと軽微な問題

**軽微：旧 `missing_raw()` との一致試験は、身元確認の追加とも両立しない。**

[対象設計165行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:165)は、非セッション・根のリンクなし・全候補を確認可能、という条件で旧結果との一致を要求する。しかし、次の場合もその条件を満たす。

```text
source ページ：url=A、raw=存在する絶対パス
raw の frontmatter：url=B
```

旧関数は存在だけを調べるので「ないものの一覧」は空になる。161行の新契約は、身元不一致で候補を捨て、`missing` にする。根のリンクと権限エラーを除外しても、一致しない。

指定版の `wiki_lint.py:213–240` に、URL の照合がないことを確認した。

## 検証した事実

| 確認対象 | 結果 |
| --- | --- |
| 指定コミット | **一致。** wiki `2452f594…`、rag `c59d05e2…` を確認 |
| セッション raw の生成基準 | **一致。** `raw_ref_of()` は入力された wiki の綴りの親を使う |
| セッション raw の身元 | **不十分。** 同じ `session_id` で抽出範囲・内容の異なる raw が成立する |
| Web raw の URL キー | **確認済み。** `wiki_fetch.py:1451` は `url`、1461行は必要時に `final_url` を書く |
| 旧 `missing_raw()` | **一致。** 三つの基準による存在検査であり、身元は調べない |
| 外部 raw の保護範囲 | **食い違い。** 書く段は `K` とデータの場所との重なりも拒む |
| 指定 wiki 版からローカル `origin/main` のスクリプト差分 | **一致。** PDF 関連2ファイルの追加だけ |
| 新 resolver・書き込み部品の動作 | **確かめられず。** 指定版には未実装 |

ファイル変更、リンク作成、属性変更は行っていない。実行確認は、指定版から抽出した関数へのメモリ上の入力に限る。

## 崩せなかった点

- 本文の読み取り・文字コード・frontmatter の解釈失敗を完全性に含める条件から、以前と同じ取りこぼしは導けなかった。
- 日誌の一時ハードリンクを完全性判定より前に片付ける変更から、以前と同じ復旧不能は導けなかった。
- MCP の索引を書けない場合をツールの失敗とする契約から、以前の「継続先がない」という矛盾は導けなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
