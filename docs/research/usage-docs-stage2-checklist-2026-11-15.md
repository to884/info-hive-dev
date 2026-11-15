# 利用者向け文書の段階 2 の確認表（2026-11-15）

| 項目 | 内容 |
| --- | --- |
| 状態 | 確認の前。作者が新しい Windows 11 の環境で実行し、結果を返す |
| 関連 | [利用者向け文書の計画](../plans/usage-docs-2026-11-15.md)（6 版。段階 2、2-1〜2-5）、[ADR-0022](../adr/0022-usage-docs-are-html-in-plugin-docs.md) |
| 対象の版 | wiki 0.19.3（`info-hive-wiki` の fb2de97）。確認 3 で入った版が違ったら、`00-versions.txt` に入った版を書き、エージェントに伝える（下の「版について」） |

## 版について

この表は、wiki 0.16.0 で書き、0.19.3 で読み直した。0.16.0 から 0.19.3 までに変わったのは、閲覧（`/wiki:browse`。0.17.0 で作りを直し、0.18.0 で画面を Fluent 2 にした）、URL の取り込みの raw の段（0.18.1）、経験の記録（`wiki_evolve.py`。0.19.2）である。MCP サーバーの起動、`/wiki:init`、`/wiki:help`、ローカルのファイルの取り込み、`/wiki:query`、`/wiki:lint` の定義とスクリプトは変わっていない。表に書いたパスと名前（プラグインの置き場所、`--ensure`、e5 と ruri のキャッシュ、ruri のフォルダー `ruri-v3-130m-onnx-cbd305d`）も、0.19.3 のコードで同じであることを確かめた。

計画の「段階 1 で作者が決めたこと」の 2 で W2 を待たせていた条件（browse の 0.17.0 と Fluent 2 の画面）は、0.18.0 でそろった。そのため、W2 は確認 5 で W1 に続けて通す。

マーケットプレイスは `info-hive-wiki` の main を配るので、実行する日に、0.19.3 より新しい版が入ることがある。そのときも、この表のとおりに進めてよい。入った版を `00-versions.txt` に書き、記録を渡すときにエージェントに伝える。エージェントが、0.19.3 からの変更が結果に関わるかを確かめる。確認 10 の C4（更新を試す）のほかは、確認の途中で版を上げない（確認 3 から確認 10 まで、同じ S1 を使う）。

## この表の使い方

計画の段階 2 で確かめることを、実行する順に並べた。確認は作者が行う。デスクトップアプリへのサインイン、VM の用意、Cowork の操作は、エージェントにはできないためである。

- 各確認の「写すもの」を、記録のフォルダー（下の「用意するもの」）に、確認の番号を付けたファイルで残す（`03-deps.txt`、`05-run1/` など）。画面は、スクリーンショットで残してよい。
- 「判定」の欄に書いたことが分からなかったときは、分からなかったと書く。推測で埋めない。
- 手順がうまくいかなかったときは、そこで止めずに、起きたこと（表示、エラーの文）を写して次の確認に進む。ただし、プラグインが入らなかった（確認 2）ときは、そのあとの確認はできない。
- 確かめ終えたら、記録のフォルダーをエージェントに渡す。エージェントが `docs/research/usage-docs-facts-<日付>.md` にまとめる。

## 用意するもの

- **環境**: 開発用の PC ではない、新しい Windows 11 の VM。Cowork（確認 8）は PC の上の VM を使うので、入れ子の仮想化を有効にしておく。スナップショットを取れること。
- **アカウント**: Claude のアカウント（デスクトップアプリへのサインイン用）。GitHub のアカウントと SSH の鍵は、VM に置かない（確認 2 で、鍵がない状態を確かめるため）。
- **ネットワーク**: ふつうのインターネットの接続。社内のプロキシ（Zscaler など）の内側での確認（確認 9）は、その環境があるときだけ行う。
- **記録のフォルダー**: VM の外に置く。確認 4 の終わりと確認 5〜10 の始めで、VM をスナップショットに戻すので、VM の中に置いた記録はそのたびに消える。ホストと共有するフォルダー（VM のソフトの共有フォルダーの機能）か、ネットワークのドライブを使い、VM の中からは `R:\stage2-records\` のようなドライブで開けるようにする（この表では、この場所を `<記録>` と書く）。VM の外に置けないときは、スナップショットに戻す前に、毎回 `<記録>` の中身を VM の外へ写す。どちらの方法にしたかを `00-versions.txt` に書く。
- **大きさを計る PowerShell の関数**: 各確認で使う。PowerShell を開くたびに、次を貼り付けて実行する。

```powershell
function Measure-InfoHive {
  $paths = [ordered]@{
    "uv のキャッシュ"   = (& uv cache dir 2>$null)
    "ruri（models）"    = "$env:LOCALAPPDATA\info-hive\models"
    "e5（fastembed）"   = "$env:USERPROFILE\.cache\info-hive\fastembed"
  }
  "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), "計測"
  foreach ($k in $paths.Keys) {
    $p = $paths[$k]
    if ($p -and (Test-Path $p)) {
      $sum = (Get-ChildItem -LiteralPath $p -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
      "{0}: {1:N1} MB  ({2})" -f $k, ($sum / 1MB), $p
    } else {
      "{0}: なし  ({1})" -f $k, $p
    }
  }
}
```

uv を入れる前は、「uv のキャッシュ」は「なし」と出る。

## 確認 0. 素の状態（S0）を作る

1. Windows 11 を入れ、更新を済ませる。
2. Claude のデスクトップアプリを入れ、サインインする。ほかには何も入れない（git、uv、Python、エディターを含む）。
3. デスクトップアプリの版を記録する（アプリの「バージョン情報」など）。
4. スナップショットを取り、名前を `S0` にする。

写すもの: `00-versions.txt`（Windows の版、デスクトップアプリの版。確認 3 のあとで、入った wiki の版を足す）

## 確認 1. git の有無（計画 2-1）

S0 で、PowerShell を開いて次を実行する。

```powershell
where.exe git
where.exe python
python --version
where.exe uv
Test-Path "$env:USERPROFILE\.ssh"
```

続けて、デスクトップアプリの Code タブで、新しいセッションを開き、次のように頼む（Code タブの Claude Code が自分の git を持っているかを見る）。

> `git --version` を実行して、出力をそのまま見せてください。

写すもの: `01-git.txt`（上のコマンドの出力と、Code タブでの `git --version` の結果。ツールの呼び出しの欄の出力を写す）

判定:

- PowerShell と Code タブの両方で git がないなら、デスクトップアプリに git は同梱されていない。次の 1-2 で入れる。
- `python` が「Microsoft Store から入手」の案内を出すか、何も出さずに終わるなら、それは Windows の別名だけである（確認 4 で使う）。

### 1-2. Git for Windows と uv を入れる（C1 の手順の候補）

git がなければ、PowerShell で入れる。どちらの方法で入れたかを記録する。

```powershell
winget install --id Git.Git -e --source winget
```

uv を、公式の手順で入れる。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

入れたら、デスクトップアプリを終了して起動し直す（アプリは PowerShell のプロファイルを読まないので、ユーザーの環境変数の PATH を読み直させる）。PowerShell も開き直し、次を実行する。

```powershell
git --version
uv --version
uv sync --help | Select-String "UV_SYSTEM_CERTS|UV_NATIVE_TLS"
```

写すもの: `01-install.txt`（入れたときの出力、`git --version`、`uv --version`、最後のコマンドの出力）

判定: 最後のコマンドに `UV_SYSTEM_CERTS` が出れば、この uv は `UV_SYSTEM_CERTS` を読む（計画 2-1。C2 の手順の確かめになる）。

## 確認 2. SSH の鍵なしで、プラグインを入れられるか（計画 2-2）

始める前に、PowerShell で `Measure-InfoHive` を実行し、時刻と大きさを `03-deps.txt` に写す（確認 3 の始まり）。

1. PowerShell で `ssh -T git@github.com` を実行し、出力を写す（鍵がないので失敗するはずである）。初めての接続でホストの確認を聞かれたら、`no` と答える。
2. Code タブで、プラグインのマーケットプレイスを追加する。まず GUI で試す（プロンプト欄の「+」の Add plugins、Plugins の Browse plugins と Manage plugins、サイドバーの Customize など）。追加するのは `to884/info-hive-marketplace` である。
3. GUI で追加できなければ、Code タブのプロンプト欄に次を順に入力する。

   ```text
   /plugin marketplace add to884/info-hive-marketplace
   /plugin install wiki@info-hive
   ```

4. 入らなかったら、表示を写したうえで、PowerShell で次を実行し、デスクトップアプリを起動し直して、2 または 3 をやり直す。

   ```powershell
   [Environment]::SetEnvironmentVariable("CLAUDE_CODE_PLUGIN_PREFER_HTTPS", "1", "User")
   ```

5. 入った時刻を記録する。

写すもの: `02-install-plugin.txt` と画面（`ssh -T` の出力。使った方法が GUI か `/plugin` か。それぞれの画面と表示。`CLAUDE_CODE_PLUGIN_PREFER_HTTPS` が要ったか）

判定: 鍵なしで、何もせずに入れば、認証のハウツーは要らない。`CLAUDE_CODE_PLUGIN_PREFER_HTTPS` が要ったなら、C1 と C2 に書く。

## 確認 3. MCP サーバーの依存の大きさと時間、S1 を作る（計画 2-3）

プラグインを入れると、Claude Code が MCP サーバーを起動しようとし、依存（約 1 GB）を取り始めることがある。終わったかを、次のコマンドで確かめる。`<版>` は、`%USERPROFILE%\.claude\plugins\cache\info-hive\wiki\` の下にあるフォルダーの名前（`0.19.3` など）である。この名前を、入った wiki の版として `00-versions.txt` に足す。

```powershell
Get-ChildItem "$env:USERPROFILE\.claude\plugins\cache\info-hive\wiki" -Name
$launch = "$env:USERPROFILE\.claude\plugins\cache\info-hive\wiki\<版>\skills\info-hive\scripts\wiki_mcp_launch.py"
Measure-Command { uv run --quiet --script $launch --ensure | Out-Host }
$LASTEXITCODE
Measure-InfoHive
```

- `--ensure` は、依存がそろうまで待ち、サーバーが動いていれば、トークンを除いた `server.json` の中身を出して終わる。終了コード 0 は「依存がそろい、サーバーが動いている」ことを示す。Claude Code の側がつながったことは示さない（それは確認 7 で見る）。
- 初めてのときは数分かかる。

写すもの: `03-deps.txt`（確認 2 の前の `Measure-InfoHive`、上のコマンドの出力すべて、入れた時刻から `--ensure` が終わった時刻まで）

ここまで済んだら、デスクトップアプリを終了してから、スナップショットを取る。名前は `S1-wiki-<版>`（`S1-wiki-0.19.3` など）にする。`/wiki:init` や、wiki の検索はしない。e5 と ruri のモデルを取ってしまうと、確認 5 が初めての取得にならなくなる。

## 確認 4. `python` と `/wiki:help`（計画 2-1、C1 の目印）

S1 で、Code タブの新しいセッションを開き、次を入力する。

```text
/wiki:help
```

`/wiki:help` は、MCP サーバーを使わず、`python` で `wiki_help.py` を直接動かす（`commands/help.md:11`）。そのため、ここで `python` の扱いが分かる。

写すもの: `04-help.txt`（返答の全文と、ツールの呼び出しの欄の実行したコマンドとその出力）

判定:

- 11 本のコマンドが並べば、C1 の目印が出た。
- `python` が見つからない、または Microsoft Store の案内が出たなら、`python` を直接呼ぶコマンドは、Python を入れないと動かない。どう失敗したか（エージェントが別の方法で動かしたか、止まったか）を写す。
- 終わったら、S1 に戻す。

## 確認 5. W1 と W2 を 3 回通す（計画 2-5）

各回の始めに、S1 のスナップショットに戻す。新しいフォルダーで始めるだけでは、PC で共有するモデルのキャッシュが残るので足りない。3 回とも、同じ手順と同じ言葉で行う。手順 1〜12 が W1、手順 13〜17 が W2 である。W2 は、W1 に続けて、同じセッションで行う。記録は `05-run1/`、`05-run2/`、`05-run3/` に分ける。

1. エクスプローラーで `%USERPROFILE%\info-hive-practice` を作る（空のフォルダー）。
2. Code タブで、このフォルダーを作業のフォルダーにして、新しいセッションを開く。
3. PowerShell で `Measure-InfoHive` を実行して写す（e5 の計測の始まり）。
4. Code タブに次を入力する。

   ```text
   /wiki:init
   ```

5. エージェントがまとめて質問してきたら、次のとおりに答える（計画 2-7）。

   > プロジェクトの wiki にしてください。場所は、このフォルダーの wiki/ と raw/ です。モデルのキャッシュは既定の場所にしてください。グラフ層は後回しにします。エージェントとの連携は、このフォルダーの CLAUDE.md に追記してください。

6. 追記の内容を示されて承認を求められたら、承認する。
7. 終わったら、ツールの呼び出しの欄を開き、`setup_wiki.py` の出力の JSON を探して写す。PowerShell で `Measure-InfoHive` を実行して写す（e5 の計測の終わり）。
8. 付録 A の「味噌」を、`%USERPROFILE%\info-hive-practice\raw\味噌.md` に、UTF-8 で保存する。
9. Code タブに次を入力する。

   ```text
   /wiki:ingest raw/味噌.md
   ```

10. エージェントが要点を示して反応を求めてきたら、付録 B の W1 の言葉を返す。そのあと承認を求められたら、承認する。
11. Code タブに次を入力する。

    ```text
    /wiki:query 味噌の原料は？
    ```

12. エクスプローラーで、`wiki/sources/`、`wiki/index.md`、`wiki/log.md` を開く。
13. 付録 A の「醤油」を、`%USERPROFILE%\info-hive-practice\raw\醤油.md` に、UTF-8 で保存する。
14. Code タブに次を入力する。

    ```text
    /wiki:ingest raw/醤油.md
    ```

    反応を求められたら、付録 B の W2 の言葉を返す。そのあと承認を求められたら、承認する。
15. Code タブに次を入力する。

    ```text
    /wiki:browse
    ```

    デスクトップアプリでは、閲覧の画面はブラウザのペインで開く（`commands/browse.md` の手順 2）。開かなければ、返答に示された URL を開くよう頼み、そのことを `notes.txt` に書く。開いた画面で、次を見る。
    - 索引のページの全ページの一覧に、「味噌」と「醤油」の要約の行があるか
    - 「麹」のページを開き、被リンクに、2 つの要約のページが並ぶか
16. Code タブに次を入力する。

    ```text
    /wiki:lint
    ```

17. エクスプローラーで、もう一度 `wiki/sources/`、`wiki/index.md`、`wiki/log.md` を開く。

写すもの（各回）:

- `init-json.txt`: 手順 7 の JSON（ツールの呼び出しの欄から）と、ツールの呼び出しの欄の画面。この欄を開いて読めたかも書く
- `sizes.txt`: 手順 3 と 7 の `Measure-InfoHive` と時刻
- `files.txt`: 手順 12 の結果。`wiki/sources/` のファイル名の一覧、`wiki/index.md` の全文、`wiki/log.md` の全文
- `query.txt`: 手順 11 の返答の全文と、ツールの呼び出しの欄（MCP のツール `query` が呼ばれたか）
- `CLAUDE.md`: 手順 6 で追記された `CLAUDE.md` の全文
- `browse.txt` と画面: 手順 15 の、ツールの呼び出しの欄の `wiki_browse.py serve` の出力の最初の 1 行（`url`、`reused`、`page`、`scope` を持つ JSON）と、索引のページと「麹」のページの画面
- `lint.txt`: 手順 16 の、ツールの呼び出しの欄の構造の lint の結果と、返答の全文。`/wiki:lint` は、MCP のツール `lint`（`mcp__plugin_wiki_wiki__lint`）が使えればそれを呼び、使えなければ `wiki_lint.py` を動かす（`commands/lint.md` の手順 2）。どちらが呼ばれたかも書く
- `files-w2.txt`: 手順 17 の結果（`files.txt` と同じ形）
- `notes.txt`: 途中で聞かれたこと、うまくいかなかったこと

判定（3 回とも出たものだけを、文書の目印にする）:

- W1
  - 手順 7 の JSON が `"status": "ready"` を示すか
  - `wiki/sources/味噌.md` ができたか（エージェントがスラッグを付け直していないか）
  - `wiki/log.md` の末尾に `## [<今日の日付>] ingest | ` で始まる行が 1 つ増えたか
  - `wiki/index.md` に `[[味噌` で始まるリンクの行があるか
  - 手順 11 の答えに `[[` で始まる出典が 1 つ以上付くか
- W2
  - `wiki/sources/醤油.md` ができたか
  - `wiki/log.md` の `## [<今日の日付>] ingest | ` で始まる行が、W1 のときより 1 つ増えたか
  - `wiki/index.md` に `[[醤油` で始まるリンクの行があるか
  - 手順 15 の JSON の `url` が `http://127.0.0.1:` で始まり、`scope` が `"project"` か
  - 手順 16 の構造の lint の結果（MCP のツール `lint` と `wiki_lint.py --json` は同じ形を返す）の `summary` で、調べたページの数（`total_pages`）が 2 以上で、`broken_links`、`orphans`、`read_errors` がどれも 0 か
- 案内のとおりになるかの確かめ（目印にはしない）
  - 付録 B の言葉のとおり、「麹」のページができ、W2 で醤油のことが書き足されたか
  - 手順 15 で、「麹」のページの被リンクに、2 つの要約のページが並んだか

## 確認 6. ruri の大きさと時間（計画 2-3）

確認 5 とは別の回にする。S1 に戻し、確認 5 の手順 1〜9 を行う（`/wiki:ingest` まで）。そのあと次を行う。

1. PowerShell で `Measure-InfoHive` を実行して写す（ruri の計測の始まり）。
2. Code タブで、次のように頼む。

   > wiki の MCP のツール `query` で「味噌」を検索して、結果をそのまま見せてください。

3. ツールの呼び出しの欄で、MCP のツール `query` が呼ばれたことを確かめる。
4. PowerShell で、次のファイルができるまで、ときどき確かめる。できた時刻を記録する。

   ```powershell
   Test-Path "$env:LOCALAPPDATA\info-hive\models\ruri-v3-130m-onnx-cbd305d\verified.json"
   ```

5. できたら、`Measure-InfoHive` を実行して写す（ruri の計測の終わり）。

写すもの: `06-ruri.txt`（手順 1 と 5 の `Measure-InfoHive`、手順 2 の返答と、ツールの呼び出しの欄、`verified.json` ができた時刻）

## 確認 7. MCP の接続と再接続（計画 2-4）

S1 か、確認 5 のあとの状態で行う。

1. Code タブで、MCP サーバーがつながっていることを、どこで見られるかを探す（`/mcp` を入力する、設定の画面を見る、など）。見つかった場所と画面を写す。
2. `/mcp` が使えるなら、wiki のサーバーを選び、Reconnect を押せるかを確かめる。`/mcp reconnect all` も試す。
3. 使えないなら、使えないことを写す。

写すもの: `07-mcp.txt` と画面

判定: 見られる場所が分かれば、C1 の目印に「MCP サーバーがつながっている」を足すかを決められる。再接続の方法が分かれば、C3 に書く。

## 確認 8. Cowork（C6）

S1 に戻してから行う。

1. Cowork を開き、Customize の Plugins の Add から Add marketplace を選び、`to884/info-hive-marketplace` を追加して、`wiki` を入れる。画面を写す。
2. 新しいフォルダー `%USERPROFILE%\info-hive-cowork` を作り、その中に `CLAUDE.md` を作って、次の 1 行だけを書く。

   ```text
   この CLAUDE.md を読んだら、答えの最初に「合言葉: みそ」と書いてください。
   ```

3. Cowork で、このフォルダーを接続し、「こんにちは」とだけ送る。答えの最初に合言葉があるかを写す（Cowork が接続したフォルダーの `CLAUDE.md` を読むかを見る）。
4. Cowork で `/wiki:init` を入力し、確認 5 の手順 5 と同じに答える。ツールの呼び出しの欄で、`setup_wiki.py` が動いたか、`"status": "ready"` が出たかを写す。
5. Cowork で次のように頼み、MCP のツールが使えるかを見る。

   > wiki の MCP のツール `stats` を呼んで、結果をそのまま見せてください。

写すもの: `08-cowork.txt` と画面（各手順の結果。uv がないなどで止まったときは、その表示）

## 確認 9. 社内のプロキシの内側（計画 2-1。その環境があるときだけ）

S1 に戻し、プロキシの内側のネットワークにつないでから行う。

S1 では依存を取り終えているので、そのまま `--ensure` を実行しても、uv はキャッシュを使い、プロキシを通る通信も証明書の検証も起きないことがある。それでは、設定の前と後のどちらが成功しても、設定が効いたかは分からない。そこで、設定の前と後のそれぞれを、空のキャッシュとデータの置き場所から始める。`tests/wiki/test_uv_tls.py` と `tests/wiki/check_first_run_mcp.py` も、同じに `UV_CACHE_DIR` と `INFO_HIVE_DATA_DIR` を空の一時ディレクトリにして確かめている。

1. `uv --version` と、確認 1-2 の最後のコマンドの出力を写す。
2. 設定の前: 新しい PowerShell で次を実行する。`<版>` は確認 3 と同じである。

   ```powershell
   Remove-Item Env:UV_SYSTEM_CERTS, Env:UV_NATIVE_TLS -ErrorAction SilentlyContinue
   $run = Join-Path $env:TEMP ("proxy-before-" + (Get-Date -Format "yyyyMMddHHmmss"))
   $env:UV_CACHE_DIR = "$run\uv-cache"
   $env:INFO_HIVE_DATA_DIR = "$run\data"
   $launch = "$env:USERPROFILE\.claude\plugins\cache\info-hive\wiki\<版>\skills\info-hive\scripts\wiki_mcp_launch.py"
   uv run --quiet --script $launch --ensure
   $LASTEXITCODE
   (Get-ChildItem -LiteralPath "$run\uv-cache" -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB
   Get-ChildItem -LiteralPath "$run\data" -Recurse -Filter *.log | ForEach-Object { "== $($_.FullName)"; Get-Content $_.FullName -Encoding UTF8 }
   ```

   最後の 2 つのコマンドで、空のキャッシュに依存を取ってきたこと（大きさが 0 から増えたこと）と、起動処理のログ（証明書の検証に失敗して、OS の証明書ストアでやり直したか）を見る。
3. 設定の後: `UV_SYSTEM_CERTS` をユーザーの環境変数に設定し、デスクトップアプリと PowerShell を開き直す。新しい PowerShell で、2 のコマンドを、`proxy-before-` を `proxy-after-` に変え、1 行目の `Remove-Item` を除いて実行する（空の別のディレクトリから始めるため）。

   ```powershell
   [Environment]::SetEnvironmentVariable("UV_SYSTEM_CERTS", "true", "User")
   ```

写すもの: `09-proxy.txt`（各手順の出力、終了コード、キャッシュの大きさ、ログの中身）

判定: 2 と 3 のどちらでも、キャッシュの大きさが 0 から増えていれば、プロキシを通る取得が起きている。そのうえで、2 で失敗するか、ログに OS の証明書ストアでのやり直しが出て、3 では設定どおり 1 回で通れば、`UV_SYSTEM_CERTS` が効いている。キャッシュが増えていなければ、その回は通信が起きておらず、判定に使えない。

## 確認 10. ハウツーの手順（C2〜C5、W3〜W5）

確認 5 のあとの状態で行う。モデルの取得を含まないので、新しいフォルダーと新しいセッションで足りる。実行できなかったものは、できなかったと書く（その手順は文書で未確認と書く）。

| ハウツー | 行うこと | 写すもの |
| --- | --- | --- |
| C2 | 確認 1-2 と 9 の結果を使う | なし |
| C3 | `%LOCALAPPDATA%\info-hive\logs\` の中のファイルの一覧。確認 3 の `--ensure` | `10-C3.txt` |
| C4 | Code タブで、マーケットプレイスとプラグインの更新を試す（GUI か、`/plugin marketplace update info-hive`、`/plugin update wiki@info-hive`、`/reload-plugins`）。新しい版がなければ「更新はない」と出るかを見る | `10-C4.txt` と画面 |
| W3 | 新しいセッションで `/wiki:init --user` を実行し、グローバルな指示への追記の提案を承認する。`%USERPROFILE%\info-hive\` にできたものと、追記された指示のファイルの場所と中身 | `10-W3.txt` |
| W4 | 確認 5 の wiki で、`/wiki:ingest <URL>` を試す。URL は、内容が変わりにくい公開のページにする（どのページにしたかを書く）。raw はエージェント `wiki:web-raw` が作る（`references/web-raw.md`）。ツールの呼び出しの欄で、`wiki:web-raw` が呼ばれたか、最後の `wiki_rawcheck.py check --finish --json` の出力（`ok`、`work_dir_removed`）を探す。この検査はエージェント `wiki:web-raw` の中で動くので、欄に出ないことがある。出なければ、出なかったと書く | `10-W4.txt`（返答の全文、見つかった `--json` の出力、できた `raw/` のファイルの名前） |
| W5 | 確認 5 の wiki で `/wiki:upgrade` を実行する | `10-W5.txt` |

## 付録 A. 練習用のソース

文書に載せる予定の文章である。段階 2 では、このまま保存して使う。内容は一般的な事実だけにしてあり、文書に載せる前に出典で確かめる。

### 味噌.md

```markdown
# 味噌

味噌は、大豆を主な原料にした、日本の発酵調味料である。

蒸すか煮るかしてやわらかくした大豆をつぶし、麹と塩を混ぜて仕込む。これを数か月から数年おいて、発酵させ、熟成させる。

麹は、米、麦、大豆などの穀物に麹菌を育てたものである。どの麹を使うかで、米味噌、麦味噌、豆味噌に分けられる。

熟成の期間が長いほど、色は濃くなる。塩の量と麹の量の割合で、味が甘口にも辛口にもなる。
```

### 醤油.md

```markdown
# 醤油

醤油は、大豆と小麦を主な原料にした、日本の発酵調味料である。

蒸した大豆と、炒って砕いた小麦を混ぜ、麹菌を育てて麹を作る。この麹に食塩水を加えて「もろみ」にし、数か月から 1 年ほどかけて、発酵させ、熟成させる。熟成したもろみを搾った液体が、醤油になる。

味噌と同じく、原料に大豆、麹、塩を使う。味噌は麹と大豆を固まりのまま熟成させるが、醤油はもろみを搾って液体にする。

日本農林規格（JAS）は、醤油を、濃口、淡口、たまり、再仕込み、白の 5 種類に分けている。
```

## 付録 B. 取り込みの途中で返す言葉

取り込みの手順の「要点を話し合う」で、エージェントが要点を示して反応を求めてきたら、次のとおりに返す（計画 2-5）。

| 回 | 返す言葉 |
| --- | --- |
| W1（味噌） | 「麹」のページを作ってください。 |
| W2（醤油） | 「麹」のページに、醤油のことも書き足してください。 |
