## 判定

**却下。確信度：中。** raw の根のリンクを許す規則と、`resolve_raw()` の先行判定が衝突する反例が残る。以下は設計の静的な反例であり、未実装の関数を実行した結果ではない。

## 致命的・重大な欠陥

### 1. 重大・発生度 B：`raw:` が根のディレクトリ自体を指すと、許可された根のリンクを拒む

**主張：** 根を明示していても、候補そのものへの無条件の `is_link()` が、根のリンクを違反として扱う。

**反例：**

```text
wiki                    C:/data/wiki
明示した raw の根       C:/data/raw
C:/data/raw             D:/archive/raw へのディレクトリリンク
D:/archive/raw/part.txt  通常ファイル、リンク数1
```

既存の source ページが、複数部分からなる原本のディレクトリを参照しているとする。

```yaml
type: source
raw: C:/data/raw
```

`rag_job_id` はない。raw の根は引数と記録の両方に入っているものとする。

1. 160行では、絶対パスなので候補は `C:/data/raw` 一つになる。
2. 161行の段階(2)は、外の原本でない候補そのものに `is_link()` を当てる。
3. 候補はディレクトリリンクなので、根であることにかかわらず `link` になる。
4. lint は許可された根を `links` に出し、依存収集は `complete=False` となり、書く段も停止する。

**根拠・照合結果：食い違い。**

- [設計書29行](C:/Works/info-hive-dev/.claude/worktrees/wiki-links-review-14/docs/plans/wiki-links-2026-11-16.md:29)と [ADR の I7](C:/Works/info-hive-dev/.claude/worktrees/wiki-links-review-14/docs/adr/0029-wiki-and-raw-hold-no-links.md:58)は、raw の根そのもののリンクを許す。
- [設計書161行](C:/Works/info-hive-dev/.claude/worktrees/wiki-links-review-14/docs/plans/wiki-links-2026-11-16.md:161)には、候補が既知の根そのものだった場合の除外がない。
- [118行](C:/Works/info-hive-dev/.claude/worktrees/wiki-links-review-14/docs/plans/wiki-links-2026-11-16.md:118)の `find_links(path)` も、渡された `path` 自体からリンクを調べる契約である。
- [283行の試験要求](C:/Works/info-hive-dev/.claude/worktrees/wiki-links-review-14/docs/plans/wiki-links-2026-11-16.md:283)は、明示された raw の根のリンクを挙げないことを要求する。
- 指定版の `wiki_lint.py:213–240` は、ディレクトリの `raw:` を受け付ける。関数を抽出した読み取り実行でも、実在ディレクトリへの参照を受け付けた。

過去の「raw の根を誤って推定する」指摘とは異なる。今回は**正しい根を明示しても、参照先がその根と同じ場合に拒む**。特殊なタイミングや作為的な違反配置は必要ない。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| raw の候補そのものは、常に根より下の検査対象である | ディレクトリの `raw:` が、raw の根そのものを指す |
| すべての候補に先行して `is_link()` を当てても、根の例外は維持できる | 候補と既知の根が一致し、その根が許可されたリンクである |

## 見落としと軽微な問題

- **軽微：過去の根の途中を検査するかが、節によって異なる。** [161行](C:/Works/info-hive-dev/.claude/worktrees/wiki-links-review-14/docs/plans/wiki-links-2026-11-16.md:161)は、記録された過去の根から候補までの途中も検査する。一方、[108行](C:/Works/info-hive-dev/.claude/worktrees/wiki-links-review-14/docs/plans/wiki-links-2026-11-16.md:108)と [308行](C:/Works/info-hive-dev/.claude/worktrees/wiki-links-review-14/docs/plans/wiki-links-2026-11-16.md:308)は、現在の根の外では途中を検査しないと一律に説明している。記録済みの過去の根について、検査範囲と `summary` の内容が一致しない。

- **軽微：ディレクトリのハッシュの並び順が一意にならない名前がある。** [165行](C:/Works/info-hive-dev/.claude/worktrees/wiki-links-review-14/docs/plans/wiki-links-2026-11-16.md:165)は、相対パスを NFC の順で並べる。しかし、`が.txt` と `か\u3099.txt` を別ファイルとして持つ配置では、正規化後の並べ替えキーが同じになる。内容が異なる二つの項目について、列挙順を逆にすると異なるハッシュになることをメモリ上で確認した。同じディレクトリがハッシュ不一致の `missing` になる余地がある。実ファイルによる再現はしていない。

## 検証した事実

| 確認対象 | 結果 |
| --- | --- |
| 対象 worktree の HEAD | **一致。** `d109b61143e1baf0ebda2390d3e47e1c04df3a7f` |
| 既存の走査と `_stat_entry()` | **一致。** 指定版はディレクトリリンクを飛ばし、ジャンクションへ降り、Markdown の属性に `os.stat()` を使う |
| `missing_raw()` の213〜241行 | **一致。** 三つの基準による存在検査で、ディレクトリも受け付ける |
| `raw_ref_of()` の1250〜1256行 | **一致。** 入力された wiki の綴りの親を基準にする |
| `list_index()` の957〜979行 | **一致。** 設計が挙げる直接読み取りが存在する |
| raw の記録と管理領域の関係 | **一致。** 書く段393行は、`.wiki-cache` 直下の管理領域以外の項目を検査対象にしない |
| rag の `pdf_path()` | **一致。** 指定版は `resolve(strict=True)` の結果を返す |
| wiki 指定版からローカル `origin/main` のスクリプト差分 | **一致。** PDF 関連2ファイルの追加だけ |
| 新 resolver・書き込み部品の通し動作 | **確かめられず。** 指定版には未実装 |

ファイル変更、リンク作成、属性変更は行っていない。

## 崩せなかった点

- `raw-roots.d/` を `apply/` の外へ移したことで、前回の `unknown_in_cache` の反例は成立しなかった。
- 過去の raw の**ファイル自体**がリンクの場合、9版目の順序は内容照合より先に拒み、拒否を `missing` に落とさない。
- 本文の読み取り・解釈失敗を完全性に含める条件と、日誌の一時ハードリンクを完全性確認前に片付ける順序から、以前と同じ反例は導けなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
