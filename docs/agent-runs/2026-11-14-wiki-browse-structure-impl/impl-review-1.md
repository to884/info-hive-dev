## 判定

**却下。確信度：高。** 失敗注入も競合もない実行で、拒否すべき出力先を変更する反例と、自分で生成した世代を次回の書き出しで拒否する反例がある。

## 致命的・重大な欠陥

1. **重大：重なりを拒否する前に、拒否対象の出力先を変更する。**

   初期状態を次のようにする。

   - Wiki：`C:\box\wiki`。初期化済み。
   - 出力先：`C:\box\user`。利用者の `keep.txt` がある。
   - `INFO_HIVE_DATA_DIR=C:\box\user\data`。`data` はまだない。

   `build C:\box\wiki --out C:\box\user` を実行すると、先に `user\data\browse` を作り、その後で「browse のデータの場所と重なる」と拒否する。終了は失敗でも、利用者の出力先の木と更新時刻は変わっている。

   メモリー上の入出力の口で、製品の `fs.build()` を実行して確認した。失敗や競合は入れていない。また、出力先を Wiki 内にして、外部の `data_dir` を未作成にすると、拒否前に外部の領分を作り、9.1 の「砂場全体が変わらない」に反する。

   **根拠：** [wiki_browse_fs.py:894](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:894) で作成が先行し、重なりの拒否は [同:903](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:903)。[設計:464](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/docs/plans/wiki-browse-structure-2026-11-11.md:464) と食い違う。設計6.4自身も、根への進入を検査より先に置いており、この条件では9.1と両立しない。

2. **重大：大文字・小文字だけが違うディレクトリを、出力先が同一視すると、生成した世代が門を通らない。**

   大文字・小文字を区別する入力側に `A/x.md` と `a/y.md` を置き、区別しない出力先へ `--out` で書き出す。

   `assign_names(["A/x", "a/y"])` は、そのまま `A/x.html` と `a/y.html` を返す。一覧にはディレクトリ `A` と `a` が別々に載るが、出力先には一つのディレクトリしかできない。実際の列挙が `A` なら、2回目の書き出しは `A/y.html` を「一覧にない、または種類が違う」と拒否する。利用者による変更は不要である。

   大文字・小文字を同一視するメモリー上のファイル系で、製品コードの1回目が `0`、2回目が上記理由の `Stop` になることを確認した。実ディスクで入力側を区別ありに設定した再現は未実施。

   **根拠：** [wiki_browse_core.py:274](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:274) はファイル名の衝突を検出するが、ディレクトリどうしの衝突は検出しない。[wiki_browse_fs.py:763](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:763) が両方の綴りを一覧に残し、[同:800](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:800) が列挙された綴りと厳密に比較する。

3. **重大：1ページの Markdown 解析の例外が、中核全体を失敗させる。**

   正常な `a.md` と `b.md` の写しを作り、`b.md` の本文を解析する呼び出しだけに `ValueError` を入れると、`Core()` 自体が例外で終わる。そのページの「描けない」表示には到達しない。静的版は全体が失敗し、初回のサーバーなら正常な `a.md` も表示できない。

   実行して、`ValueError` が中核の組み立てから漏れることを確認した。これは**失敗注入時の欠陥であり、9.1の反例ではない**。

   **根拠：** [wiki_browse_core.py:551](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:551) の解析は囲まれていない。ページ単位の受け口は後段の [同:1127](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:1127) にしかない。[設計:507](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/docs/plans/wiki-browse-structure-2026-11-11.md:507) が求める解析への例外注入で、部分の失敗が全体を止める。

4. **重大：探索用の口が依存先の走査を捕捉せず、説明された探索になっていない。**

   `fs.X` を `browse_sweep.Injector()` にして、実際の `wiki/` に `fs.walk_inputs()` を実行した。入力は32件、実際の `os.scandir` は4回だったが、Injector が数えた呼び出しは **`['stat']` だけ**だった。

   ページと索引の走査は `wiki_pages` が直接OSを呼ぶため、この仕組みでは、その内部の「一覧を開く」「途中の項目を取り出す」などのN回目に失敗を入れられない。書き出しの探索も、描画済みの固定辞書 `FILES_N` を `fs.build()` に渡しており、入力走査と中核を通らない。

   **根拠：** [wiki_browse_fs.py:1220](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:1220)、[wiki_pages.py:198](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:198)、[browse_sweep.py:198](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/tests/wiki/browse_sweep.py:198)。依存先内部にも口から手を入れられるという [設計:236](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/docs/plans/wiki-browse-structure-2026-11-11.md:236) の説明と食い違う。

## 崩れる前提

- **領分を先に作っても、拒否対象には影響しない。** `data_dir` が拒否対象の出力先の下にあると崩れる。
- **出力ファイル名が衝突しなければ、世代の名前も一致する。** 出力先がディレクトリ名の大文字・小文字を同一視すると崩れる。
- **ページの失敗は描画時の受け口で処理できる。** 中核の組み立て中にもページごとの解析があるため崩れる。
- **`fs.X` を差し替えれば、依存先のOS呼び出しも数えられる。** `wiki_pages` の直接呼び出しには届かない。

## 見落としと軽微な問題

- **軽微：UTF-8のデコード失敗には「不完全」の印が付かない。** `b.md` を `b'\xff'` にすると、ページは除外され、`read_error / decode` の診断は出る。しかし `Snapshot.unreadable == []`、manifest の読めないページ数は `0`、正常なページの被リンクにも「不完全」が出ない。`unreadable` への追加を `error == "os"` に限定しているためである。[wiki_browse_core.py:175](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:175)。メモリー上の入力で確認済み。

- **軽微：再構築に失敗しても、印が同じなら「古い」を消す。** 読めないページを含む中核があり、署名取得は成功し、その後の再構築が `InputsUnknown` になる場合、`self.failed == "InputsUnknown"` でも `get()` は前の中核と `stale=None` を返した。[wiki_browse.py:355](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:355) が、署名一致時には失敗理由を捨てる。失敗注入で確認済み。

- **軽微：構文木の検査は、変数に入れた `Path` の入出力を見逃す。** `p = Path("x"); return p.read_text(encoding="utf-8")` に対して `io_violations()` は `[]` を返した。[test_browse_fs.py:107](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/tests/wiki/test_browse_fs.py:107)。層の外の入出力を禁止する検査として、通常の書き方が検出対象から漏れる。

## 検証した事実

- **一致（静的確認）：** Windowsの作成口には `FILE_FLAG_OPEN_REPARSE_POINT` があり、開いたハンドルの再解析点・ディレクトリ属性を拒否する。
- **一致（静的確認）：** `FileExistsError` 後の種類の再確認、`remove_record` のロック・owner・instance確認、POSIXの `0o700`／`0o600`、既定で空の `MUTANTS`、層外の `wiki_initialized` は、依頼元の説明どおりだった。
- **実行結果：** 読み取りだけで動く `LayerContractTest` の2件と `ClassifyTest.test_absent_and_unknown` の計3件は成功した。ただし、上記のAST検査の反例も通過する。
- **検証範囲：** Windows／Python 3.14.6。ファイルは変更していない。書き込みを伴う反例はメモリー上の入出力の口で確認した。実ディスクでの書き出し・リンク試験、全探索、PyYAMLを使う関係表の動作は**確かめられず**。

## 崩せなかった点

今回の静的確認とメモリー上の再現では、書き込みの口が Wiki のルートの下への作成を拒否する点は崩せなかった。指摘1でも、Wiki 内への作成自体は拒否されている。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
