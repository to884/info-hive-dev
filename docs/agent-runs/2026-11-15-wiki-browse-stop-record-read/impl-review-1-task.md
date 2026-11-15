# 依頼: `/wiki:browse --stop` の記録の読み取りの直し（wiki 0.18.2 の予定）の敵対的レビュー

## 目的

Windows で、閲覧のサーバーの起動中や終了中に `wiki_browse.py stop` を動かすと、ときどき次の知らせで止まっていた（info-hive-dev の CI の `browse (windows-latest, 3.12)` の `tests/wiki/test_browse_server.py` の `ProcessTest.test_stop_while_starting_waits_for_record`。同じコードで通る回もある）。

```
確かめられないので、何も変えずに止める: open_read: PermissionError（...\data\browse\<id>.server\server.json）
```

この直しが、原因を構造で直しているか、設計の決まり（P1 から P8、とくに 3.1、3.2、7.1、9.2、9.5）を破っていないか、新しい欠陥を入れていないかを崩してほしい。場当たり的な直し（反例を 1 つずつ塞ぐ形）になっていれば、それも欠陥として挙げる。

## 確かめた原因（実測は `docs/agent-runs/2026-11-15-wiki-browse-stop-record-read/share_probe-results.md`）

1. `open_read` は `os.open`（CRT の `_wopen`）で、共有に `FILE_SHARE_DELETE` を付けない。サーバーの `os.replace` と `os.unlink` の途中（DELETE の権利のハンドルがある）に開くと共有違反になる。逆に、`stop` が開いているあいだは、サーバーの `os.unlink` が共有違反で失敗する。
2. 共有を付けても、名前が削除待ちのあいだ（`DeleteFileW` が削除の印を付けてから閉じるまで）は、どの共有でも開けない（エラー 5）。
3. 設計の 7.1 は「記録を読めない（分からない）とき: ロックがあれば『動いているが、届かない』として待ち、時間が切れたら知らせて失敗で終わる」と決めている。`serve_start` は従っていたが、`probe_server`（`stop` が使う）は `read_record` の `Unknown` をそのまま送出していた。

## 直したこと

- `wiki_browse_fs.py`
  - `_win_handle`（`CreateFileW` を共有 7 で呼ぶ）を切り出し、`_win_open` と新しい `_win_open_read` が使う。`Os.open_read` は、Windows では `_win_open_read`（`GENERIC_READ`、`OPEN_EXISTING`、リンクはたどる）を使う。対照 `read_without_share_delete` で `os.open` の形に戻る。
  - `_record_while_locked` を足し、`serve_start` と `probe_server` は、ロックが取られていて記録を読めなければ `('unreadable', Unknown)` を返す（`serve_start` は今まで `('reuse', None)` だった）。対照 `unreadable_record_fails` で、`probe_server` が 0.18.0 の形（送出）に戻る。
- `wiki_browse.py`
  - `serve` は `reuse` の記録だけで使い回し、`unreadable` なら待つ。時間が切れたら、読めなかった理由を書いて `Failed`。
  - `stop` の 1 つ目の待ちは、`running` で答えるサーバーの記録だけで止める要求を送り、`unreadable` なら待つ。時間が切れたら、読めなかった理由を書いて `Failed`。2 つ目の待ち（止める要求のあと）は、`not-running` になるまで待つ（`unreadable` も待つ）。
- 試験: `tests/wiki/test_browse_server.py` の `UnreadableRecordTest`（10 件。Windows だけのもの 5 件を含む）。置き換えと削除の途中のハンドル、削除待ちの記録、記録を開く口だけの `PermissionError` を、決まった順に作る。`tests/wiki/browse_sweep.py` の `probe()` を `unreadable` に合わせた。
- 設計: `docs/plans/wiki-browse-structure-2026-11-11.md` の 3.1（口の表と「それぞれの扱い」）、7.1（記録を読めないとき）、9.5（対照）、11（限界: Windows の記録の置き換え）。
- 版: `plugin.json` を 0.18.2 にし、CHANGELOG に書いた（0.18.1 は別の PR が使う予定）。

## 読むもの

- 差分: `docs/agent-runs/2026-11-15-wiki-browse-stop-record-read/impl-review-1.plugin.diff`（サブモジュール `info-hive-wiki`）と `impl-review-1.tests.diff`（試験と設計）
- 本体: `info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`
- 試験: `tests/wiki/test_browse_server.py`、`tests/wiki/test_browse_fs.py`（3.4 の構文木の検査 `io_violations`）、`tests/wiki/browse_sweep.py`
- 設計: `docs/plans/wiki-browse-structure-2026-11-11.md`（3、7、9、11）
- 実測: `docs/agent-runs/2026-11-15-wiki-browse-stop-record-read/share_probe-results.md`、`share_probe.py`

## とくに崩してほしい点

1. P1（分からないことを、ないこととして扱わない）と 9.2 の「どの場所でも」の行（「分からない」の失敗を入れて 0 で終わったなら、新しい警告がある）。`stop` と `serve` が、読めない記録を待って、あとで読めた記録で 0 で終わるとき、警告を出さない。これが基準を破るか。
2. `open_read` を `CreateFileW` にしたことで、入力（Wiki のページ、索引、オントロジー）の読み取りの振る舞いが変わらないか。リンクとジャンクションの先、ディレクトリ、長いパス、エラーの分け方（`winerror` を持つようになるので、123 と 1921 が「ない」になる）、ハンドルの漏れ、`msvcrt.open_osfhandle` の失敗。
3. `stop` が、別のインスタンスや別の Wiki のサーバーに止める要求を送る道ができていないか（持ち主の確かめと `instance` の照合、7.1）。
4. `serve_start` の戻り値を変えたことが、ほかの呼び出し元（`browse_sweep.py`、試験）や、使い回しの判定を壊していないか。
5. 試験が、直す前のコードで落ち、直したあとで通るだけでなく、競合の原因を本当に再現しているか。Windows の削除待ちを `SetFileInformationByHandle(FileDispositionInfo)` で作る形が、CI の Windows（windows-latest、Python 3.12）で決まって再現するか。試験のハンドルやスレッドが漏れて、ほかの試験を不安定にしないか。
6. 限界（11）に送った「`os.replace` の先が開かれていると、起動が失敗する」を、この直しに含めないことが妥当か。この直しが、それを悪くしていないか。
