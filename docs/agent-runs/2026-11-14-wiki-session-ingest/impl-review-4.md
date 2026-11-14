## 判定

**却下。確信度：高。** 秘密の値の一部と、除くべき差し込みの内容がrawに残り、`scan`も通過する反例を再現した。確認前に、秘密を含むファイル名で決定ファイルの作成へ進む経路もある。

## 致命的・重大な欠陥

1. **重大：重なる検出範囲を捨てるため、秘密の値の末尾が伏せ残る。**

   `origin.kind=human`の`user`本文を次の文字列にする。

   ```text
   password=sk-abcdefghijklmnop/SECONDSECRET
   ```

   抽出結果は次のとおりだった。

   ```text
   password=［伏せ字］/SECONDSECRET
   ```

   `RE_NAMED`は`sk-abcdefghijklmnop/SECONDSECRET`全体を秘密の値として認識する。しかし、先に`RE_PREFIX`が接頭辞側を登録するため、`take()`が重なる`RE_NAMED`の範囲全体を捨てる。再度の伏せ字でも、置換済みの`［`に阻まれて末尾を拾えない。

   このrawは自己検査を通った。書き込みをモックした`cmd_write()`も正しい承認ハッシュで終了コード0になり、全文を渡した`cmd_scan()`の`--path`経路も**終了コード0、`findings: []`**だった。

   検索文字列にも欠落がある。例えば`token=alice.smith@example.org`ではメール全体だけが登録され、メール規則が登録するはずのローカル部が失われる。`scan_text("alice.smith", …)`は検出しなかった。

   根拠：[wiki_session.py:333](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:333)の検出順序と338〜340行の重複排除、349〜352行の名前付き値とメールの処理。

2. **重大：先行する伏せ字が終了タグを消し、先頭の差し込みをrawに残す。**

   人の発言を次の本文にする。`--keep-reminders`は指定しない。

   ```text
   <system-reminder>NOSHOW_PRIVATE_CONTEXT
   The file contains -----BEGIN PRIVATE KEY-----</system-reminder>
   Question
   ```

   元の本文は`RE_REMINDERS`に一致し、差し込みを除去できる形である。しかし、先に実行されるPEM規則が開始ヘッダーから末尾までを伏せ、`</system-reminder>`も消す。その結果、差し込みの削除が働かず、次の本文が残った。

   ```text
   <system-reminder>NOSHOW_PRIVATE_CONTEXT
   The file contains ［伏せ字］
   ```

   警告は`leading_tag`だけで、`stripped_reminder`は出ない。このrawも自己検査、モックした`cmd_write()`、全文を読む`cmd_scan()`を通過した。`NOSHOW_PRIVATE_CONTEXT`単独の検査も検出0件だった。

   これは個人情報の規則による見落としではなく、既定で除くと指定された差し込みの内容を残す退行である。

   根拠：[wiki_session.py:437](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:437)の伏せ字とタグ判定の順序、131行のPEM規則の`\Z`。

3. **重大：後段では拒否する秘密入りスラッグを、確認前に決定ファイル名へ書く。**

   記録に`sk-abcdefghijklmnop`を含め、次の指定で`decide init`を呼ぶ。

   ```text
   --slug sk-abcdefghijklmnop
   ```

   本文のトークンは自動で伏せられる。一方、`decide init`は終了コード0となり、次の名前を`open(..., "xb")`へ渡した。

   ```text
   .wiki-cache/session/sk-abcdefghijklmnop-<乱数>.json
   ```

   同じ値は`check_slug_value()`では「自動の伏せ字の規則に当たる文字列」として拒否された。つまり、`show --meta`や`write`で止まる前に、秘密をファイル名へ出している。決定ファイルの**内容**を位置だけにしても、この経路は守れない。

   ファイル操作はモックし、実際の作成はしていない。作成先の名前と、作成処理まで到達することを確認した。

   根拠：[wiki_session.py:1511](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:1511)の構文だけのスラッグ検査と1523〜1526行のファイル作成。秘密の検査は1123〜1129行にある。

## 崩れる前提

- **先に検出した範囲と重なる規則は捨ててもよい。** 後の規則の範囲が広い場合、伏せる範囲と検索文字列の両方が欠ける。
- **伏せ字を先にかけても、除去対象の構造は判定できる。** PEM規則が終了タグを巻き込むと、元は除去できた差し込みを判定できなくなる。
- **題名とスラッグを最終確認時に検査すれば、保存先にも秘密は出ない。** S3の決定ファイル作成が、その検査より先に行われる。

## 見落としと軽微な問題

- **軽微：検出件数に対して二乗で増える比較がある。** `find_secrets()`の`take()`は、追加するたびに既存の全範囲を比較する。同じメールアドレスを並べた入力で、1,000件は約0.08秒、3,000件は約0.74秒、6,000件は約3.95秒だった。6,000件でも入力は108,000バイトである。根拠は338〜340行。
- 現在の試験には、規則の重複で広い範囲が捨てられるケース、伏せ字で差し込みの終了タグが失われるケース、決定ファイル名への秘密の流出を検査するケースがない。ディスク走査の`leaks()`も、ファイル内容だけを調べ、パスに含まれる文字列は調べていない（`tests/wiki/test_wiki_session.py:441`）。

## 検証した事実

- **食い違い：** 上記1・2では、伏せ残ったrawが自己検査と承認ハッシュの照合を通り、`scan --path`の処理も検出0件になった。ファイル読み書きはモックした。
- **一致：** 3回目の指摘に対応する、ツール値のヘッダーと後続本文、`--tools none`、ツール値内の鍵全体、`cwd`、コマンド引数のケースでは、鍵本体が伏せられ、各本体行を`scan`が検出した。`git_branch`でも同じ結果だった。
- **一致：** 読み取りだけで実行できる既存3試験が合格。生成器30例でも、除外対象の目印、参照実装との返答先、見出しとフェンスの対応に問題は出なかった。
- **未検証：** 実物982ファイルの全走査、旧実装で追加5試験が落ちること、実ファイルを作る試験、2プロセスの排他試験、Claude Code実機での読み取り専用の確認。
- リポジトリのファイルは変更していない。

## 崩せなかった点

- `redact_parts()`の切り分け自体は、区切りなし・空部品を含む100通りの分割で、PEM本体の伏せ残しや検索文字列の欠落を起こさなかった。
- 隣接する手動指定それぞれの検索文字列、半角カナと濁点のNFKC照合、CRLFを含む照合、許可1件による検出範囲全体の包含判定。
- 不正な承認ハッシュは書き込み関数を呼ぶ前に拒否された。13回に分けた`show`の出力は、連結するとrawと同じバイト列になった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
