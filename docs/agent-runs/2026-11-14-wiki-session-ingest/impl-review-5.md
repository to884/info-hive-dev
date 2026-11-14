## 判定

**却下。確信度：高。** 自動で伏せた秘密を題名・スラッグへ戻せる経路と、終端のない秘密鍵の一部がrawに残り、`scan`も通過する反例を再現した。

## 致命的・重大な欠陥

### 1. 重大：自動で伏せた値を、題名・スラッグの検査が拒否しない

人の発言を次にする。

```text
password=SECONDSECRET
```

本文は`password=［伏せ字］`になり、検索文字列にも`SECONDSECRET`が登録される。しかし、次の指定は両方とも検査を通った。

```text
--title SECONDSECRET
--slug secondsecret
```

`show --meta`は終了コード0。そこで得たハッシュを渡した`cmd_write()`も、ファイル操作をモックした検証で終了コード0となり、書き込み関数には次の内容が渡った。

```yaml
title: "SECONDSECRET"
```

行き先にも`secondsecret.md`が使われる。

原因は、`check_no_secret()`が自動規則への再一致と**手動指定の元の文字列だけ**を調べ、`ex.redactions.needles`を調べないこと。名前付き値から切り出した秘密は、単独では自動規則に一致しない。

raw全体を`scan_text()`へ渡せば題名の秘密を検出するが、S6ではrawを検査せず、S10の対象もwikiに書いたファイルである。後段の検査ではrawへの出力を防げない。

根拠：[`check_no_secret()`](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:1146)、[`cmd_write()`](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:1643)。設計8節の「題名とスラッグに、伏せた区間の文字列が入っていれば拒む」と**食い違う**。

### 2. 重大：終端のない秘密鍵では、短い最終行が伏せ残り、検索対象にも入らない

人の発言を次にする。終了行は付けない。

```text
-----BEGIN PRIVATE KEY-----
QUFBQUFBQUFBQUFB
QkJCQkJCQkJCQkJC
QUJDRA==
```

抽出結果は次になった。

```text
［伏せ字］
QUJDRA==
```

新しい`RE_PEM`の代替分岐は、各本体行に16文字以上を要求する。Base64の最終行がそれより短いと、その直前で鍵の範囲を打ち切る。残った`QUJDRA==`は8文字なので、`scan`の短い検索文字列を省く条件には該当しないが、そもそも検索文字列に登録されない。

このrawは自己検査を通り、正しい承認ハッシュでのモックした`cmd_write()`も終了コード0となった。raw全文を読むモックした`cmd_scan --path`も次の結果だった。

```json
{"findings": [], "skipped_short": 0}
```

同じ打ち切りは別の境界でも起きる。アシスタントの`text`に開始ヘッダーを置き、次の`Grep.pattern`に本体を置いて終了行を省くと、検出用の文に挿入されたツール名`Grep`で範囲が切れ、本体がツール要約に残った。この本体単独の`scan`も検出0件だった。

根拠：[`RE_PEM`](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:131)、[`find_secrets()`](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:350)、[`claude_body()`](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:852)。今回の終端なしPEMの変更による伏せ残りである。

## 崩れる前提

- **秘密を単独で再検査しても、元の文と同じ規則に一致する。** `password=SECONDSECRET`から切り出した`SECONDSECRET`では、秘密と判断するための名前と区切りが失われる。
- **終端のない鍵の本体行は、すべて16文字以上である。** 短い最終行で崩れる。
- **検出用に挿入するツール名は、鍵の継続判定に影響しない。** 終端なしPEMでは、その名前が本体の連続を切る。
- **範囲の和集合を効率化すれば、`find_secrets()`全体も件数の対数倍になる。** 正規表現による終端探索が別に残っている。

## 見落としと軽微な問題

- **軽微：終端のないPEMヘッダーの反復で、検出時間が二乗で増える。**  
  `"-----BEGIN PRIVATE KEY-----\nnot_key\n"`を反復すると、500件で約0.049秒、1,000件で0.201秒、2,000件で0.722秒、4,000件で2.928秒だった。4,000件でも144,000文字である。各開始位置から、存在しない終了ヘッダーを末尾まで探し直す。根拠は`RE_PEM`の最初の分岐と350行。1124行の速度試験はメールだけなので、この経路を検査しない。

- **軽微：外部のrawルートでは、途中のリンク検査が省かれる。**  
  `wiki=C:\project\wiki`、`raw_root=C:\outside\redirect\raw`で、`redirect`がジャンクションの場合、`check_destination()`はrawルート自身しか検査しない。リンク判定をモックした検証では通過し、同じ配置を`C:\project\redirect\raw`にすると拒否された。実ジャンクションへの書き込みは未検証。根拠は[`check_destination()`](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/skills/info-hive/scripts/wiki_session.py:1181)。設計9節の途中の階層も拒む記述と食い違う。

- **軽微：再開時のS2とS3がつながっていない。**  
  S2は既存の決定ファイルを識別して続用できると説明するが、S3は無条件に`decide init`して、その返したパスを使う。記載順に実行すると、新しい空の`spans`と`drop`へ切り替わる。既存の決定を保持して再開する分岐が明記されていない。根拠は[`ingest.md`のS2・S3](/C:/Works/info-hive-dev/.claude/worktrees/wiki-session-ingest-a98aa3/info-hive-wiki/commands/ingest.md:36)。CLI側の既存決定の再利用自体は通った。

## 検証した事実

- **一致：** 4回目の重複範囲の例では、`SECONDSECRET`の末尾は残らず、メールのローカル部も検索対象に残った。
- **一致：** 4回目の差し込みの例では、内容が除去され、`stripped_reminder`が出た。
- **一致：** 秘密の接頭辞を含むスラッグは、`decide init`が`mkdir`・`open`を呼ぶ前に拒否した。ファイル名は16進16桁の乱数だけになっている。
- **一致：** 読み取りだけで動く既存3試験が合格。生成器30例でも、除外対象の目印、参照実装との返答先、見出しとフェンスの対応に不一致は出なかった。
- **確かめられず：** 実物982ファイルの結果、旧実装で追加試験が落ちること、実ファイルでの排他・読み取り専用の動作は追試していない。
- リポジトリのファイルは変更していない。今回の書き込み経路の検証では、ファイル操作をモックした。

## 崩せなかった点

- 元の文で見つけた範囲を和集合にし、重なった規則の検索文字列も残す処理。
- 元の文で差し込みを判定してから伏せ字を当てる処理。
- 隣接する手動指定それぞれの検索、半角カナと濁点のNFKC照合、複数の許可の和集合による除外の拒否。
- 不正な承認ハッシュは、書き込み関数へ到達する前に拒否された。
- 同じ土台・設定での既存決定ファイルの再利用と、決定からの設定の復元。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
