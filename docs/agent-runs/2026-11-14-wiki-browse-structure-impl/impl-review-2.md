## 判定

**却下。確信度：高。** OS の失敗注入も競合もない実行で、拒否対象を作ってから止まる反例と、新しい世代を公開したのに失敗扱いになる反例を再現した。前回の修正は、重なりの判定と例外の封じ込めを完了していない。

## 致命的・重大な欠陥

1. **重大：未作成の出力先では、データの場所との重なりを見落とす。9.1 の反例。**

   初期化済みの `C:\box\wiki` と、既存の `C:\box` を用意し、`C:\box\newdata` は存在しない状態にする。

   ```powershell
   $env:INFO_HIVE_DATA_DIR = 'C:\box\newdata'
   python wiki_browse.py build C:\box\wiki --out C:\box\newdata
   ```

   重なりの事前判定を通過し、次を作ってから「一覧がない」と拒否する。

   - `newdata\browse\build.lock`
   - `newdata.browse-work\.browse-work`
   - `newdata.browse-work\build.lock`

   `newdata` が既存で、`--out` が未作成の `newdata\browse` 自身の場合も同様だった。どちらも失敗注入・競合なしで、製品の `fs.build()` をメモリー上の入出力で実行して確認した。

   **根拠：** [_check_nesting():884](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:884) は、出力先が既存ディレクトリの場合だけ、出力先がデータの場所を含むか調べる。未作成なら判定せず、[build():930](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:930) が対象を作る。`responses.md` の「何も作る前に重なりを拒む」という説明と食い違う。

2. **重大：確定後の `Stop` が漏れ、新しい世代があるのに失敗で終わる。9.1 の反例。**

   次の配置にする。作業用には `.browse-work` を置き、`old-5` は世代の一覧を持たないディレクトリとする。

   ```text
   C:\box\site.browse-work\
     .browse-work
     old-5\wiki\SCHEMA.md
     old-5\wiki\a.md
   ```

   この `old-5\wiki` を Wiki のルートにし、`--out C:\box\site` へ書き出す。新しい世代の公開後、片付けが `old-5` を動かそうとする。守りが「Wiki のルートの祖先は動かさない」と `Stop` を出し、それが単位の外へ漏れる。

   メモリー上で確認した結果は、**`site\index.html` と一覧が公開済み、`fs.build()` は `Stop`、警告は空**だった。Wiki 自体は残るが、コマンドでは終了コード 1 になる。OS の失敗や競合は入れていない。

   **根拠：** [確定の点:1021](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:1021) の後で `_discard()` を呼ぶが、[その受け口:957](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:957) は `Unknown` と `Absent` しか受けない。設計7の「終了コードは単位の真実だけで決める」と食い違う。

   別の反例として、標準出力が閉じたストリームなら、公開後の知らせから `ValueError` が漏れることも確認した。新しい世代は存在し、警告は出なかった。[report():1070](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:1070) も、この例外を受けない。

3. **重大：終了処理は領分を再確認せず、リンク先の利用者ファイルを消す。状態変更の反例。**

   サーバーを通常どおり起動した後、**終了処理を開始する前に**、状態ディレクトリを退避し、その名前を利用者のディレクトリへのジャンクションに置き換える。リンク先には利用者の `server.json` を置く。その状態でアイドル終了させる。

   `serve_finish()` は状態ディレクトリの種類も目印も確認せず、保存してある名前の `server.json` を削除する。最後の名前は通常ファイルなので、最後のリンクをたどらない規則では防げない。途中の状態ディレクトリのリンクをたどる。

   メモリー上では **`C:\box\user\server.json` が削除され、警告なしでロックが解放された**。終了処理中に差し替える競合は不要である。これは固定初期状態の9.1とは別に、9.3の状態変更に対する反例である。

   **根拠：** [serve_finish():1171](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:1171) は `Guard` を作り直すだけで、`_enter_state()` を通らない。`Guard` はリンク先が Wiki 内かを調べるが、領分かどうかは調べない。設計7.1の「終了も、状態ディレクトリに触れる前に6.2の確かめを通す」と食い違う。

4. **重大：関係表で使う Markdown 解析の例外は、依然として中核全体を止める。例外注入の反例。**

   オントロジーと正常な `a.md`、`b.md` がある状態で、共有パーサー `wiki_pages._MD.parse` の `b.md` の解析だけを `ValueError` にする。`Core()` は関係表の組み立てから例外で終わり、正常な `a.md` も利用できない。

   **根拠：** [_relations():688](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:688) の `wiki_pages.extract_wikilinks()` は、ページ単位の受け口にも、関係表全体の受け口にも入っていない。呼び先は [wiki_pages.py:429](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:429) で共有パーサーを呼ぶ。

   新しい探索は [new_parser() の差し替え](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/tests/wiki/browse_read_sweep.py:178) だけなので、既に作成済みの `_MD` には届かない。前回重大3・4への対応が、この経路では未完了である。

   この反例は9.1ではない。PyYAMLが未導入のため、グラフの協働関数を最小の代役に置いて、製品コードから例外が漏れる経路を実行確認した。

## 崩れる前提

- **今ある祖先を識別すれば、未作成の出力先との重なりも判定できる。** 出力先自身も未作成なら、比較する分岐に入らない。
- **確定後の片付けで起きる失敗は `Unknown` と `Absent` だけである。** 書き込みの守り自身が `Stop` を出す。
- **起動時に領分だった名前は、終了時にも領分である。** 終了処理の前に、名前がリンクへ置き換わると崩れる。
- **Markdownの解析は、新しく作るパーサーだけが行う。** 関係表は、読み込み時に作成された共有パーサーも使う。

## 見落としと軽微な問題

- **軽微：未知の項目を接頭辞だけで消す。** 作業用に `tmp-not-a-number` と `old-not-a-number` を置くと、失敗のない書き出しが両方を消して0で終わった。領分内なので保護対象の侵害ではないが、設計6.2の「知らない項目は残す」とは食い違う。[対象選択:970](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:970)。

- **軽微：読む側の探索の比較対象が、同じ劣化処理で作られる。** `unreadable_gen` は入力を木から取り除いた結果ではなく、同じ実装にその入力の読み取り失敗を与えて作る。読み取り失敗時の意味付けが両側で同じように誤れば、この比較では見つからない。設計9.2が要求する比較とは異なる。[比較対象の生成:303](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/tests/wiki/browse_read_sweep.py:303)。

- **軽微：構文木の検査は、通常の `Path` の入出力をまだ見逃す。** `p.open()`、`p.rename(q)`、`p.stat(follow_symlinks=False)` の各写しに対して、`io_violations()` はすべて `[]` を返した。[検査:114](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/tests/wiki/test_browse_fs.py:114)。前回の `read_text()` の反例は塞がれたが、禁止する入出力全体を検出する検査にはなっていない。

## 検証した事実

- **食い違い：** 「拒む判定を何も作る前に済ませる」「確定後の失敗は終了コードを変えない」は、指摘1・2で崩れた。
- **部分的に一致：** 前回の本文解析の反例は、オントロジーがない構成ではページ単位に収まった。関係表の共有パーサーは指摘4の経路が残る。
- **一致：** Windowsの作成口には `FILE_FLAG_OPEN_REPARSE_POINT` と、開いたハンドルの属性検査がある。
- **実行結果：** 読み取りだけで動く `LayerContractTest` の2件と `ClassifyTest.test_absent_and_unknown` は成功した。
- **検証範囲：** Windows／Python 3.14.6。ファイルは変更していない。書き込み・削除の反例はメモリー上の入出力で確認した。実ディスクでの書き出し・リンク試験、全探索、実PyYAMLでの関係表の一連実行は未実施。

## 崩せなかった点

- `A/x` と `a/y` の出力先ディレクトリは、現在の `assign_names()` では同じ綴りにそろった。前回の具体的反例は崩せなかった。
- オントロジーがない構成では、本文解析に失敗したページに `render-error` が出て、正常なページは描けた。
- 指摘2でも、Wikiのルートと `SCHEMA.md` 自体は変更されなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
