## 判定

**却下。確信度：高。** 通常の `raw: ~/...` で静的書き出しが失敗する反例と、描画不能な新世代へ切り替わったまま旧世代へ戻らない反例を確認した。`shutdown_requested` の処理にも、設計との食い違いがある。

## 致命的・重大な欠陥

### 1. 【重大】`raw: ~/...` を含む Wiki を、既定の設定で静的書き出しできない

次のページが反例になる。原本の存在は、この不具合の成立に関係しない。

```yaml
---
type: source
raw: "~/papers/x.pdf"
---
# A
```

`build <WIKI_ROOT>` の既定は `raw=link` である。描画では、`file_url()` が `~` をホームの絶対パスへ展開する一方、利用者の内容として記録するのは展開前の `~/papers/x.pdf` だけである。

そのため、公開前の検査が、生成した `file:///…/papers/x.pdf` に含まれるホームのパスを「生成器が混入させた絶対パス」と誤判定する。実関数をメモリ上で実行した結果は次のとおりだった。

```text
find_leaks(..., [str(Path.home())], recorder)
→ (["a.html"], [])
```

`build()` はこの結果を受けて生成を失敗させる。設計 §3.8 が認める `~` 始まりの原本と、§5 の「選択した raw の絶対パスは通す」という例外が両立していない。

根拠：[wiki_browse_core.py:373](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:373)、[同:860](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:860)、[同:1105](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:1105)、[wiki_browse.py:248](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:248)。

### 2. 【重大】描画で失敗する新世代を採用し、以降のページ要求が応答を返さなくなる

再現手順：

1. 正常な `a.md` を一度閲覧し、旧中核を保持させる。
2. `a.md` に次を加える。

   ```yaml
   raw: "http://["
   ```

3. `a.html` を再要求する。

この値は lint の URL 判定を通る。新しい `Core` の構築も成功するため、`BrowseState.get()` は新中核へ切り替え、`failed=None` にする。

しかし、実際の描画では `classify_raw()` の `urlparse()` が `ValueError: Invalid IPv6 URL` を送出する。`Handler._view()` は描画の例外を捕捉しない。

実関数のメモリ上の実行では、次を確認した。

```text
1 回目の要求: ValueError / 応答の送信なし
2 回目の要求: ValueError / 応答の送信なし
current_generation: new
failed: None
take_snapshot の呼び出し: 合計 1 回
```

入力の印が変わらないので、以降も同じ描画不能な中核を使い続ける。「古い」の表示も、503 も返らず、旧中核も使われない。実サーバーでは例外が標準ライブラリの要求処理へ伝播し、接続が閉じられる。標準エラーにも、スクリプトの絶対パスを含むトレースバックが出る経路になる。

根拠：[wiki_browse_core.py:356](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:356)、[同:853](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:853)、[wiki_browse.py:386](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:386)、[同:489](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:489)。

### 3. 【重大】保護対象との重なりを検出しても、操作口経由では安全終了しない

次の状態で成立する。

1. サーバーを起動し、正常な中核を作る。
2. Wiki に、状態ディレクトリの `.browse-server` を指すページのシンボリックリンクを加える。
3. 操作トークンで `GET …/control/locate/a` を送る。

写しには Wiki 外の入力として `.browse-server` が入り、状態ディレクトリとの重なりが検出される。`get()` は `shutdown_requested=True` にする。

しかし、終了要求を実行する処理は `_view()` にしかない。`_control()` の `locate` はフラグを確認せず、返された旧中核で名前を解決して応答する。メモリ上で確認した結果は次のとおりだった。

```text
shutdown_requested: True
locate の応答: 200 / resolved
request_shutdown の呼び出し: 0 回
```

さらに、閲覧口から重なりを検出して終了する場合も、終了処理はこのフラグを見ず、通常どおり `server.json` を削除する。保護対象が `.browse-server` なら、`Guard` は別ファイルの `server.json` の削除を許す。

設計 §6.1 の「記録に触れずに終了する」が、どちらの経路でも成立していない。Wiki の実ファイルを破壊したという指摘ではなく、要求された安全終了の欠落である。

根拠：[wiki_browse.py:380](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:380)、[同:476](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:476)、[同:502](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:502)、[同:684](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:684)。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| 利用者が書いた `raw` の値を記録すれば、出力に含まれる同じパスも許可できる | `~` が描画時に絶対パスへ展開される |
| `Core` の構築が成功すれば、各ページの描画も成功する | `raw` の URL 解釈が描画時に例外を送出する |
| 中核の失敗は `BrowseState.get()` が捕捉する | 失敗が `get()` の後の `render()` で起きる |
| `shutdown_requested` を設定すれば終了する | 中核を呼んだ要求が `control/locate` である |
| 保護の `Guard` だけで「記録に触れない」終了も実現できる | 保護対象が状態ディレクトリ内の別ファイルである |
| 2 方式の比較で結果が一致すれば、被リンクや関係表を検証できる | 比較対象の結果が両方とも空である |

## 見落としと軽微な問題

- **【軽微】再試行を抑制している間、失敗理由が「組み立て中」に変わる。** 最初の失敗は `"failed"` を返すが、直後の要求は `self.failed` の `"RuntimeError"` などを返す。`_view()` は `"failed"` 以外を「組み立てている」と表示する。実関数で `failed → RuntimeError` を確認した。根拠：[wiki_browse.py:376](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:376)、[同:488](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:488)。

- **【軽微】一部の HTTP エラーが共通の防御と応答規則を通らない。** `PATCH` は設計の 405 ではなく、標準ライブラリの 501 になる。構文不正の要求では、閲覧トークンを含む要求行が 400 の応答へ反映される。どちらにも CSP、`Referrer-Policy` が付かなかった。実際の要求パーサーへメモリ上のバイト列を渡して確認した。未知のトークンを取得できたという意味ではない。根拠：[wiki_browse.py:409](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:409)、[同:517](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:517)。

- **【軽微】見出しの鍵が、表示された文字と一致しない場合がある。** `## [X](target)` は `X（target）` と表示されるが、見出しの鍵は `x` である。表示された見出し全体を指定するリンクは `missing_heading` になる。設計 §3.4 の「本文と同じに描いた表示文字」から鍵を作る規則と異なる。根拠：[wiki_browse_core.py:318](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:318)、[同:777](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:777)。

- **試験の見落とし：被リンクと関係表の方式間比較が空の結果で成立している。** 比較するのは `steps.links` のページだが、そのページを指す本文リンクも、そのページの関係も fixture にない。被リンクの存在する移動先は比較対象から外れる。したがって、被リンクを常に空にしても、この比較では検出できない。関係表も非空の行の一致を確かめていない。根拠：[browse.test.mjs:44](/C:/Works/info-hive-dev/tests/wiki/browse/browse.test.mjs:44)、[同:224](/C:/Works/info-hive-dev/tests/wiki/browse/browse.test.mjs:224)。

- **試験の見落とし：設計に列挙された競合・復帰の一部が実装されていない。** 編集が組み立てに割り込む場合、複数要求で組み立てが重ならないこと、データの世代不一致、`shutdown_requested`、索引・オントロジーの読み取り失敗からの復帰、起動途中の停止、同時の二つの停止を確かめる試験は見当たらない。待ち時間の試験も、HTTP 応答の「古い」表示や初回503ではなく、`state.get(wait=0.3)` の戻り値を確認している。根拠：[test_browse_server.py:151](/C:/Works/info-hive-dev/tests/wiki/test_browse_server.py:151)、[同:199](/C:/Works/info-hive-dev/tests/wiki/test_browse_server.py:199)。

## 検証した事実

今回の実行環境は **Windows／Python 3.14.6**。ファイルを作らない試験とメモリ上の検証を実施した。Python 3.12、Linux、実サーバープロセス、ブラウザの試験は再実行していない。

| 主張 | 結果 |
|---|---|
| 出力名の試験 | **一致。** `NamesTest` の5件が成功 |
| 日本語コーパスの未解決リンクが lint と一致する | **一致。** 27ページで確認。リンクの抜き出しも一致し、全31出力をメモリ上で描画できた |
| 1回目の「衝突した非表示ページのリンクが消える」指摘への対応 | **一致。** `x.md`／`x.MD` の衝突でも `missing` が未解決一覧に残った |
| 1回目の「最初の警告で別のパスの検査をやめる」指摘への対応 | **一致。** 元の反例は漏洩として検出された |
| 1回目の属性変更への対応 | **コード上は一致。** 再帰削除から属性変更がなくなっている。NTFS上の実行は未確認 |
| 1回目の空出力先への復旧への対応 | **一致。** メモリ上の分岐検証で、旧世代を削除せず空出力先へ戻した |
| 1回目の誤ったオントロジーへの対応 | **捕捉範囲の追加は確認。** 今回は PyYAML がなく、実行結果は確かめられず |
| CI が両OSでPython試験、Chromiumの2方式、起動速度試験を指定している | **設定上は一致。** 実際のCI結果は確かめられず |
| 版と案内文書 | **一致。** `plugin.json` と変更履歴は0.10.0。README、コマンド一覧、SKILL.mdにbrowseの記載がある |
| 既存スクリプトの振る舞いが不変 | **確かめられず。** 提供環境でGitの比較ができず、既存試験も再実行していない |

## 崩せなかった点

- コード追跡では、閲覧トークンから操作口へ入る経路を示せなかった。
- パスのデコード後の `..`、空要素、`\`、NUL の拒否と、既知名の照合を越えて任意ファイルを取得する経路は示せなかった。
- Wiki 内への書き込みや、削除時にジャンクションをたどって Wiki を消す、新たな具体的経路は示せなかった。
- `stop` がインスタンスの不一致を無視して、別のサーバーへ停止を送る経路は示せなかった。実プロセスでの競合試験は未実施。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
