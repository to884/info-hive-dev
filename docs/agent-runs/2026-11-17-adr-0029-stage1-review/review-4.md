## 判定

**却下。確信度：高。** wiki の記事をリンクの検査なしで読む経路が残っている。また、Windows では実行パスの大文字・小文字の違いだけで CLI の警告が消える。段階 1 の I2・I4 を満たしていない。

## 致命的・重大な欠陥

1. **重大・発生度 B：`read_user_file()` は、リンクで指定された wiki の根の実体側を保護しない。**

   `C:/view/wiki` を `C:/store/wiki` へのジャンクションとし、実体側の `concepts/p.md` をハードリンクにする。次の指定では、その記事を直接読む。

   ```text
   wiki_decide.py shortlist C:/store/wiki/concepts/p.md --wiki C:/view/wiki --no-embed
   ```

   所属判定は、渡された根の綴りだけとの前方一致である。実体側のパスを wiki 外と扱い、末尾の `path.read_text()` に進む。ADR が指定する「書いたままの根と、解決した根の両方」と一致しない。

   根拠：[wiki_pages.py:520](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:520)、[wiki_decide.py:508](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py:508)。

   モック実行では、正規の `article_path()` が `link` とする入力を、根の別名を渡した `read_user_file()` は読み、読む口の呼び出しは **0 回**だった。

2. **重大・発生度 B：wiki を受け取るコマンドでも、別のファイル引数からリンクの記事を読める。**

   `W/concepts/p.md` がハードリンクの場合、字幕検証に次を渡す。

   ```text
   --wiki W --page concepts/regular.md=W/concepts/p.md
   ```

   `cmd_verify()` は wiki を知っているが、`parse_page_args()` は右辺を直接 `read_text()` する。後続のページ配置の検査より前に、拒むべき本文を読んでいる。

   同様に、`wiki_evolve.py propose` の `--candidate W/concepts/p.md` は、根拠ページの `article_path()` より前に `read_bytes()` される。

   根拠：[wiki_youtube.py:606](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:606)、[wiki_youtube.py:620](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:620)、[wiki_evolve.py:218](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:218)。

   両経路で、読む口を呼ぶ前の読み取りをモックで確認した。分類表は前者を `USER_FILE`、後者を関数全体で `GATEWAY` とするため、この欠陥があっても通る。

3. **重大・発生度 D：評価ループの `WORK_COPY` 分類には、写す前の元コーパスの読み取りが含まれている。**

   スイートの `corpus` を利用者の wiki にし、`test` 課題の `sources` にハードリンクの記事を指定する。この配置を禁止する検査はない。

   `run()` は `test_keys` を作る際、その記事を直接読む。コーパスのコピーはその後である。`inside()` はハードリンクを拒まない。また、コピー元を読む `tree()` も、シンボリックリンクだけを拒み、ハードリンクの本文を読む。

   根拠：[wiki_evolve_loop.py:513](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:513)、[wiki_evolve_loop.py:528](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:528)、[wiki_evolve.py:109](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:109)。

   モック実行で、元コーパスへの読み取り時点の `copy_tree()` 呼び出し数が **0 回**であることを確認した。「利用者の wiki ではない作業用の写し」という分類と食い違う。

4. **重大・発生度 B：Windows では、スクリプトのパスを小文字で指定すると警告が消える。**

   `_CLI` の判定は、`sys.argv[0]` と `wiki_pages.__file__` のディレクトリを、大小文字を区別する文字列として比較する。一方、呼び出し元は `Path(__file__).resolve().parent` を import の探索先に入れる。

   この環境では、同じスクリプトについて次になった。

   ```text
   abspath(argv0): c:\works\...\wiki_stats.py
   resolve():     C:\Works\...\wiki_stats.py
   ```

   小文字の実行パスを与えてモジュールを評価すると、`_CLI=False` となり、リンク拒否を通知しても標準エラーは空だった。通常形式の統計は `link_warnings` を描画しないため、記事が警告なしで集計から消える。

   根拠：[wiki_pages.py:160](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:160)、[wiki_stats.py:209](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_stats.py:209)。プラグインのディレクトリをジャンクション経由で実行した場合にも、同じ比較が崩れる。

## 崩れる前提

- **wiki の根には比較すべき綴りが一つしかない。** 許可された根のリンクと実体側のパスを混在させると崩れる。
- **利用者が渡すファイルは wiki 外にある。** 字幕検証の右辺や改善候補に、既存の wiki 記事を指定すると崩れる。
- **評価ループの読み取りはコピー内で行われる。** コピー前の `test_keys` 作成と、コピー元のハッシュ計算で崩れる。
- **関数内に読む口の呼び出しが一つあれば、その関数の読み取りを保護できる。** `propose()` の候補読み取りが反例になる。
- **実行ファイルと import 元のディレクトリの文字列は一致する。** Windows の大小文字やジャンクションで崩れる。

## 見落としと軽微な問題

- **軽微：`test_walk.py` の索引モデルが、ハードリンクの `indexes` をシンボリックリンク扱いする。**  
  `{"wiki":{"indexes":("hlink","ext/file")},"ext":{"file":"text"}}` に対する `model_index()` は、`[("indexes","symlink")]` を返した。実装と追加試験は、この配置を記事でも道でもないものとして扱う。`expected_calls()` も同じタプル判定で早期終了する。根拠：[test_walk.py:365](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_walk.py:365)、[test_walk.py:421](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_walk.py:421)。

- **軽微：読み取り箇所の全件分類という主張に検出漏れがある。**  
  検出する `open()` は裸の関数呼び出しだけで、`Path.open()` は対象外である。現に `wiki_index.sha256_file()` の `path.open("rb")` は分類表に現れない。この箇所自体はモデルファイルの読み取りだが、「新しい読み取りは分類しないと落ちる」という保証は成立しない。根拠：[test_wiki_links.py:653](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_wiki_links.py:653)、[wiki_index.py:97](C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:97)。

## 検証した事実

- `ReadSiteInventoryTests`、`ServerFilesTests`、`PortTests` の計 **6 試験は通過**した。上記の読み取り漏れは、この通過と両立する。
- ファイルを作らないモック実行で、根の別名、字幕検証の入力、改善候補、コピー前のコーパスへの読み取りを確認した。
- Windows の実際のパス処理で大小文字の差を確認し、その条件で `_CLI=False`、警告出力なしになることを確認した。
- リポジトリのファイルは変更していない。実リンクを作る統合試験と、試験全体の実行は行っていない。

## 崩せなかった点

- `article_path()` 単体では、`..`、絶対パス、ドライブ指定、空の要素、ストリーム指定など **7 種類**を、OS を呼ぶ前に拒否した。
- 現在の静的 import の到達範囲に対する `SERVER_FILES` の不足は崩せなかった。
- 読んだ範囲では、`link_kind()` の名前の代理ビットとハードリンク数の条件そのものは崩せなかった。

使用した MCP サーバー：なし  
使用した Agent Skills：なし
