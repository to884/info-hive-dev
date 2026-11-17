## 判定

**却下。確信度：高。** 前ターンの3件と第5回の5件の元の反例は閉じているが、一覧取得の失敗を空のコーパスとして扱う退行と、POSIX で指定とは別のファイルを読む欠陥が残る。

## 致命的・重大な欠陥

### 1. 重大・発生度 B：一覧できないコーパスが、通知なしで空のコーパスになる

次の状態で `evaluate` または評価ループの `run` を実行する。

```text
W/SCHEMA.md
W/concepts/suite.json       corpus に "corpus" を指定
W/concepts/corpus/         属性取得は成功するが、一覧取得は PermissionError
```

新しい事前検査は `tree(corpus, corpus_root)` である。しかし `tree()` の `os.walk()` には `onerror` がなく、一覧取得の `OSError` が内部で捨てられる。ディレクトリの属性検査が成功すれば、結果は `{}`、通知は空になる。途中のディレクトリだけ一覧できない場合も、その部分が黙って欠ける。

**モック検証で確認した結果：**

```text
tree                  → {}
通知                  → []
evaluate / run        → 事前検査を通過して契約検査に到達
copy_tree             → {}
コピー先 mkdir の要求 → 1回
ファイルコピーの要求  → 0回
```

実際の `os.walk` に対して `os.scandir` の `PermissionError` を注入した。書き込みはモック化し、評価全体は実行していない。同じ失敗を `walk_pages()` に与える対照では、`unlistable` と通知が残った。

前版の `require_readable_articles()` は走査の `unlistable` を検出して止めていた。今回それを `tree()` に置き換えたことで、**「調べられない」が空の集合に変わる**。段階1の I4 に反する。

根拠：

- 失敗を捨てる走査：[wiki_evolve.py:115](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:115)
- 空の結果をコピー結果として返す：[wiki_evolve.py:131](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:131)
- `evaluate` の事前検査：[wiki_evolve.py:379](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:379)
- `run` の事前検査：[wiki_evolve_loop.py:512](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:512)

### 2. 重大・発生度 D：POSIX のファイル名に含まれる `\` を区切りに変え、別ファイルの本文を採用する

POSIX 上に次の二つを置く。1行目の `\` は、ファイル名に含まれる1文字である。

```text
/W/concepts/a\b.md     指定する候補。内容 ORIGINAL
/W/concepts/a/b.md     別ファイル。内容 DECOY
```

`read_user_bytes(Path("/W/concepts/a\\b.md"), Path("/W"))` は、指定したファイルではなく後者を読む。

`_article_rel()` が元の名前を渡しても、`article_path()` が `\` を `/` に変換する。その変換後のパスを `user_file_path()` が返し、読み取りに使うためである。

**POSIX のパス処理とファイル属性を差し替えたモック検証：**

```text
記事判定       → True
属性検査の末尾 → /W/concepts/a/b.md
実際の読取先   → /W/concepts/a/b.md
返却バイト列   → DECOY
通知           → []
```

元の `a\b.md` をハードリンクとして設定しても、その属性検査には到達しなかった。POSIX 実機でファイルを作った実測ではない。

`propose()` の単一候補もこの入口を使うため、指定した候補と異なるバイト列を提案に採用する経路になる。ここはコードからの推論であり、提案の書き込みは実行していない。

根拠：

- 名前の変換：[wiki_pages.py:496](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:496)
- 変換後のパスを返す：[wiki_pages.py:547](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:547)
- そのパスのバイト列を読む：[wiki_pages.py:567](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:567)
- 単一候補の読み取り：[wiki_evolve.py:225](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:225)

この配置は[ファイル名規約](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/references/page-conventions.md:101)には違反するため、発生度は D とした。ただし実装は命名違反をエラーにせず、記事として受け付けて別ファイルを採用する。前ターンのコロンの反例は閉じたが、「検査と読み取りが指定された同じファイルを扱う」という保証は閉じていない。

## 崩れる前提

- **ディレクトリの属性を検査すれば、その下も検査できたことになる。** 属性取得と一覧取得の権限は別であり、後者だけ失敗すると崩れる。
- **`tree()` が正常終了すれば、入力の一覧は完全である。** `os.walk()` が列挙エラーを捨てるため成立しない。
- **`\` を `/` に変えても入力の意味は変わらない。** POSIX では `\` はファイル名の文字になり、異なるファイルを指す。
- **共通の読む口を通れば、元の入力を検査したことになる。** 読む口自身がディスク上の名前を変換すると成立しない。

## 見落としと軽微な問題

**軽微：コーパスの検査を `tree()` に移した部分に、一覧取得失敗の回帰試験がない。**

今回追加された部分木の試験は、ハードリンクを拒むか、誤った根を渡すと検出できるかを確認している。一方、列挙失敗の探索は `walk_pages`／`walk_index_files` を対象とするため、新しい `tree()` の走査には及ばない。

根拠：[test_wiki_links.py:799](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_wiki_links.py:799)、[test_wiki_links.py:812](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_wiki_links.py:812)、[test_walk.py:866](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_walk.py:866)。

前ターンの「根の別名と外向きリンク」「コーパスと wiki の根の不一致」「誤った根を渡す対照」の不足は、現在の試験では閉じている。上記は別の不足である。

## 検証した事実

### 前ターンの3件

| 指摘 | 現在の判定と根拠 |
|---|---|
| 重大1：根の別名と外向きジャンクションによる迂回 | **閉鎖。** 祖先の解決が既知の根で止まり、残りの要素を検査する。文字列・バイト列の両入口で、本文読み取り前の拒否と通知をモック確認した。[wiki_pages.py:596](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:596) |
| 重大2：部分コーパスを別の根として扱う | **閉鎖。** `source_wiki_root()` が元の根を返す。`concepts/corpus/assets/p.md` は拒否し、`assets/corpus/assets/p.md` は対象外のまま通すことをモック確認した。`run` の `test_keys` とコピーにも同じ根が渡る。[wiki_pages.py:608](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:608)、[wiki_evolve_loop.py:511](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:511) |
| 重大3：POSIX のコロン名が無検査読み取りに流れる | **閉鎖。** POSIX 条件では属性検査に進み、ハードリンクを拒否する。記事なのに入力検証を通らなかった場合も、無検査読み取りへ戻らない。[wiki_pages.py:501](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:501)、[wiki_pages.py:551](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:551) |

### 第5回の5件

| 指摘 | 現在の判定と根拠 |
|---|---|
| 重大1：ディレクトリ候補・元コーパスの未保護の読み取り | **元の反例は閉鎖。** 候補と元スキルのコピーに `args.wiki`、元コーパスに選択した根が渡る。apply／rollback の元スキルの検査にも根が届く。ただし今回の重大1・2は別途残る。[wiki_evolve.py:241](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:241)、[wiki_evolve.py:391](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:391)、[wiki_evolve.py:482](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:482) |
| 重大2：記事でない assets 等を拒否 | **閉鎖。** 所属と記事判定を分け、対象外の入力を通す。除外領域内のコーパスも元の根を引き継ぐ。[wiki_pages.py:540](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:540) |
| 重大3：途中の `..` を畳む | **閉鎖。** 絶対化前の拒否を文字列・バイト列の両入口で確認した。[wiki_pages.py:523](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:523) |
| 軽微1：indexes のハードリンクの呼び出しモデル | **閉鎖。** `hlink` では早期終了せず `scandir` を期待する。該当する木もエラー注入の探索対象に含まれる。[test_walk.py:420](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_walk.py:420)、[test_walk.py:860](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_walk.py:860) |
| 軽微2：読む口の名前だけで保護済みとする試験 | **閉鎖。** 静的棚卸しの限界を明記し、入口の実行試験と、根の引き渡し欠落・誤った根の対照を分離している。[test_wiki_links.py:636](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_wiki_links.py:636)、[test_wiki_links.py:812](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_wiki_links.py:812)、[test_wiki_links.py:861](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_wiki_links.py:861) |

検証範囲は次のとおり。

- 継続レビューの入力28ファイルは、保存された SHA-256 とすべて一致した。前ターンから変わったのは、CHANGELOG、`wiki_pages.py`、評価の2スクリプト、`test_wiki_links.py` の5ファイルだった。
- 静的棚卸し・依存閉包・走査の呼び出し制約の6試験は通過した。
- ファイル生成を省いた設定で、既存の `..`、POSIX 条件のコロン、大小文字変換の3テストメソッドも通過した。これらは実ファイルの統合試験ではない。
- 依頼元の159件の unittest と統合チェック2本は再実行していない。実ジャンクション、POSIX 実ファイル名、実 ACL による今回の再実測も行っていない。
- リポジトリ、利用者の wiki、原本は変更していない。

## 崩せなかった点

- 既知の根に到達した後、配下の外向きリンクを解決せずに拒否する処理。
- 部分コーパスで元の wiki の記事判定を引き継ぎ、除外領域を新たな記事領域にしない処理。
- リンクのディレクトリを `os.walk` に渡す前に拒否する処理。
- `..` の絶対化前の拒否と、今回修正されたコロン名の検査。
- `link_kind()` の分類条件と、遅延 import を含む `SERVER_FILES` の依存閉包。

使用した MCP サーバー：なし  
使用した Agent Skills：なし
