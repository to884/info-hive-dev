## 判定

**却下。確信度：高。** `resolved` になった raw を保護根へ加える規則が、正常なディレクトリ参照でも書く段を停止させる。また、追加したハッシュ照合とリンク拒否の順序・結果契約が閉じていない。

以下は設計の静的な反例であり、未実装の関数を実行した結果ではない。

## 致命的・重大な欠陥

### 1. 重大：ディレクトリを指す `raw:` から、その親を保護根に加えると、正常な兄弟配置を拒む

**主張：** 162行の「`resolved` になったものの親の和」は、ファイルとディレクトリを区別していない。書く段の既存契約と食い違う。

**反例：**

```text
wiki           C:/data/wiki
raw の根       C:/data/raw
source ページ  C:/data/wiki/sources/book.md

type: source
raw: ../raw
```

リンクは一つもない。既存ページなので、`raw_sha256`、`session_id`、`url` は持たないものとする。ほかの基準から作る候補は存在しない。

1. `resolve_raw()` は `C:/data/raw` を一意のディレクトリとして解決する。
2. 162行に従うと、その**親の `C:/data`** が保護根に加わる。
3. 書く段の根の重なり検査では、保護根 `C:/data` が wiki を包含する。
4. `begin` が `raw_overlap` で停止する。raw 以外の記事を編集する計画でも同じになる。

**根拠・照合結果：食い違い。**

- [対象設計162行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:162)は、解決先の親を無条件に加える。
- [書く段の設計673行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md:673)は、外部 raw が**ファイルなら親、ディレクトリならそれ自身**を加える。
- [同679行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md:679)は、保護根と wiki が包含関係にあれば拒む。
- 指定版 `2452f59` の `wiki_lint.py:213–240` はディレクトリの raw を受け付ける。関数を抽出した読み取り実行でも、実在するディレクトリを `raw:` に渡すと `missing_raw()` は `[]` を返した。

同じ162行には、wiki 内の raw を外部の保護根と区別しない問題もある。既存契約では、wiki 内の raw は[681行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md:681)の個別パス保護に入り、wiki と重なる保護根にはしない。

### 2. 重大：ハッシュ照合でリンク先を読むか、照合から落ちたリンクを検査対象から失う

**主張：** ハッシュ照合をリンク検査より前に置く契約になっている。逆順に読むとしても、拒んだ候補を lint の `links` へ届ける契約がない。

**反例：**

```text
raw の根                   C:/data/raw
C:/data/raw/a.md            C:/outside/b.md へのシンボリックリンク

source ページ:
type: source
raw: C:/data/raw/a.md
raw_sha256: <保存時のハッシュ H>
```

rag の外部原本ではない。登録後に通常ファイルがリンクへ置き換わった状態とする。

- **リンク先のハッシュが H と一致する場合：** 161行の照合にはリンク先のバイト列を読む必要がある。その後、107行でリンクを検出しても、I2 の「読まず、たどらず」には既に反している。
- **リンク先のハッシュが H と異なる場合：** 161行は候補を捨て、`missing` にする。107行の raw 検査は「`resolve_raw()` で解けた先」にしか当たらないので、このリンクは `links` に載らない。

137行の読む口を先に適用して拒む解釈でも、159行の resolver の結果と107行の lint の接続に、**拒んだ raw 候補を `links` として返す経路**が定義されていない。

**根拠・照合結果：設計内の契約が未接続。**

- [161行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:161)：候補のハッシュを照合し、不一致の候補を捨て、残らなければ `missing`。
- [107行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:107)：raw のリンク検査は解決できた先に適用。
- [25行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:25)：raw の記事も「1つに解けた先」で定義しているため、候補から落ちたリンクを拾えない。
- [ADR の I2・I4](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md:53)は、リンクを読まないことと、拒否を通常の不在に変えないことを要求する。

ハッシュを採用する決定への反対ではない。追加した照合処理が、既存の拒否境界を通る具体的な契約になっていないという指摘である。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 解決した raw の親を保護根にすればよい | raw 自体がディレクトリ、または wiki 内の原本である |
| 候補の内容を確かめてからリンクを検査できる | ハッシュ・身元確認が、拒むべきリンク先の読み取りを必要とする |
| 解決できた raw だけ検査すれば、raw のリンクを通知できる | リンク候補がハッシュ不一致や読み取り拒否で解決結果から落ちる |

## 見落としと軽微な問題

- **軽微・仕様不足：ディレクトリと複数値のハッシュが未定義。** [164行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:164)は全 source ページに「raw のバイト列」の SHA-256 を要求するが、ディレクトリのバイト列や、複数の `raw:` とハッシュの対応を定めていない。指定版の `missing_raw()` はディレクトリと raw の配列を受け付ける。新しい保存・照合の振る舞いは確かめられない。
- **軽微：追加試験が、記録を書く側を検証していない。** [165行](C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-links-2026-11-16.md:165)は、記録に既にある根による拒否を試す。一方、各 raw 書き手による根の追記、追記失敗、並行追記、raw 保存途中の停止についての試験は記載されていない。記録を保護の根拠にした今回の変更を、この試験だけでは検証できない。

## 検証した事実

| 確認対象 | 結果 |
| --- | --- |
| 指定コミット | **一致。** wiki `2452f594…`、rag `c59d05e2…` |
| 現行 `missing_raw()` | **一致。** 三つの基準による存在検査。ディレクトリ・複数値を受け付ける |
| `raw_ref_of()` | **一致。** 渡された wiki の綴りの親を基準にする |
| `list_index()` の直接読み取り | **一致。** 指定された957〜979行に存在する |
| rag の `pdf_path()` と `result.raw` | **一致。** パスを解決し、解決済みパスを返す |
| 指定版からローカル `origin/main` のスクリプト差分 | **一致。** PDF 関連2ファイルの追加だけ |
| 新 resolver・書き込み部品 | **確かめられず。** 指定版には未実装 |
| Windows の特殊なリパースポイント・OneDrive の観察 | **今回の実測なし** |

ファイル変更、リンク作成、属性変更は行っていない。

## 崩せなかった点

- 新規ページのハッシュが正しく記録されている場合、同じ `session_id` の別内容をハッシュ一致として選ぶ反例は成立しなかった。
- 本文の読み取り・解釈失敗を完全性に含める条件から、前回と同じ依存の取りこぼしは導けなかった。
- 日誌の一時ハードリンクを完全性判定より前に片付ける順序から、前回と同じ復旧不能は導けなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
