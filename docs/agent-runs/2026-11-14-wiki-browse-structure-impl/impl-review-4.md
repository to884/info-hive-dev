## 判定

**却下。確信度：高。** 失敗・競合を入れずに、サーバー起動が既存の書き出しを更新不能にする反例を確認した。公開後の終了コードと、停止後の記録削除にも契約違反が残る。

## 致命的・重大な欠陥

### 1. 重大：データ領域の根が既存世代そのものだと、起動が入れ子の検査を抜ける

初期化済みの `C:\box\wiki` について、次の順で実行する。

1. `INFO_HIVE_DATA_DIR=C:\box\base-data` として、`--out C:\box\browse` に書き出す。
2. `INFO_HIVE_DATA_DIR=C:\box` に変え、同じ Wiki のサーバーを起動して終了する。
3. データ領域を元に戻し、再び `--out C:\box\browse` に書き出す。

2は既存世代の中に `<wiki_key>.server/` を作る。終了後も目印とロックが残るため、3は「一覧にない、または種類が違う」で止まる。

**検証結果：食い違い。** ファイルの口だけをメモリー上の代役にし、製品の `fs.build()`、`serve_start()`、`serve_finish()` を実行した。

```text
INITIAL_BUILD 0 GATE ('generation', None, 1)
SERVE_START started WARNINGS []
GATE_AFTER_SERVE ('foreign', '一覧にない、または種類が違う: key.server', 1)
REBUILD Stop
```

**根拠：** [wiki_browse_fs.py の `_check_not_nested()`](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:902) は、対象が既存ディレクトリなら915行で親から調べ、対象自身の目印を見ない。起動側の `_enter_state()` は1177行で `browse_root` だけを検査し、1182行で作る状態ディレクトリには入れ子の検査を行わない。設計6.1の禁止が、失敗のない実行で破れる。

### 2. 重大：標準エラーへの警告が失敗すると、公開済みでも終了コード120になる

標準エラーをパイプにつなぎ、読み手を閉じる。入力に Wiki の絶対パスを含めるなどして、公開後に警告を出させる。

`say()` は書き込み失敗を受けるが、バッファーに残った警告を Python が終了時に再フラッシュする。`_final_flush()` は標準出力しか処理しない。

**検証結果：食い違い。** 実際の子プロセスと閉じた標準エラーのパイプで、製品の `main()` → `build()` → `fs.build()` を実行した。入力取得とファイル入出力には代役を使った。

```text
PUBLIC_MAIN_RETURNED 0 OUT_GATE ('generation', None, 1)
FULL_PUBLIC_BUILD_WITH_CLOSED_STDERR_EXIT 120
```

新しい世代が門を通り、`main()` が0を返しても、プロセスは120で終了する。

**根拠：** [wiki_browse.py の `say()`](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:78) と824行の `_final_flush()`。設計7は、確定後の**標準エラーへの警告**の失敗も終了コードを変えないと明記している。これは失敗を入れた経路であり、9.1の反例ではない。

### 3. 重大：停止確認後の記録削除で、領分の確認失敗が警告にならない

サーバーの停止を確認した後、`remove_record()` が状態ディレクトリを再確認する際に、例えば一覧取得の `PermissionError` が起きる場合である。

`_enter_state()` と `lock_held()` は警告に変える `try` の外にあるため、失敗がコマンドの出口まで伝わる。サーバーは停止済みでも、終了コード1となる。

**検証結果：食い違い。** 通信と稼働確認を代役にし、製品の `main()` → `stop()` → `remove_record()` を実行した。稼働確認を `running` → `not-running` とし、その後の `_enter_state()` に `Unknown` を入れると、次を返した。

```text
終了コード: 1
確かめられないので、何も変えずに止める: scandir_open: PermissionError
```

**根拠：** [wiki_browse_fs.py の `remove_record()`](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:1282) の1289〜1292行と、[wiki_browse.py の停止後の処理](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:774)。設計7.1と関数自身の説明にある「記録を消せなければ警告して続ける」と食い違う。これも9.1の反例ではない。

## 崩れる前提

- **領分の根の祖先を検査すれば、その下に作る状態ディレクトリの入れ子も検出できる。** 根そのものが既存世代だと崩れる。
- **標準出力の最終フラッシュを処理すれば、通知失敗による終了コード120を防げる。** 標準エラーに未送信の警告が残ると崩れる。
- **記録の読み取りと削除を囲めば、停止後の片付け失敗をすべて警告にできる。** その前の領分確認やロック確認で失敗すると崩れる。

## 見落としと軽微な問題

**軽微：構文木検査は、直接の `os.read()`、`os.write()` を見逃す。**

中核のソースに次を加えた写しに対し、`io_violations()` は `[]` を返した。

```python
def leak(fd):
    return os.read(fd, 1024)
```

`os.write(fd, data)` でも同じだった。[検査](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/tests/wiki/test_browse_fs.py:109) が参照する禁止属性に、これらが含まれない。設計3.4の検出範囲の欠落である。

また、前回対応の試験は、入れ子では `site/data/browse`、フラッシュでは標準出力を対象としており、今回の「根そのものの一致」と標準エラーは通らない。

## 検証した事実

- **一致：** `LayerContractTest` の2件と `ClassifyTest.test_absent_and_unknown` は成功した。
- **一致：** `_semantic()` は、前回不足していた各ページのHTML、アンカー、見出し欠落を比較対象に含めている。
- **一致：** `responses.md` に記載された、キャッシュキーを綴りそのままの文字列にする変更は実装されている。
- **食い違い：** 「browseが作るどの場所にも入れ子の決まりを当てる」「最後のフラッシュで終了コード120を防ぐ」という対応の一般化は、上記1・2で崩れた。
- **検証範囲：** Windows／Python 3.14.6。ファイル変更なし。全探索、実ディスクへの書き出し、実サーバーの通信、Linux、実PyYAMLによる関係表の一連の検証は未実施。

## 崩せなかった点

- 読めないページを除いた結果は、確認した小さな入力では、そのページを取り除いた結果と、HTML・リンク解決を含めて一致した。読み取りの印も残った。
- frontmatterの解釈に `ValueError` を入れても、当該入力を外して中核の組み立ては完了した。
- `serve_finish()` が状態ディレクトリに触れる前に `_enter_state()` を通ることは、コード上で確認できた。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
