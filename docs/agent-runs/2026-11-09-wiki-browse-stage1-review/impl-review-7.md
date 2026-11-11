## 判定

**却下。確信度：高。** 入力から除外する `raw/` などの読み取り権限によって、閲覧の起動・更新・停止まで失敗する反例を確認した。過去の列挙エラー対策で、無関係なディレクトリへの依存が残っている。

## 致命的・重大な欠陥

### 1. 【重大】除外対象ディレクトリが読めないと、起動・更新・停止が失敗する

次の配置で、`raw/` の一覧を取得できない状態にする。

```text
wiki/
  concepts/a.md    # 読める
  raw/            # 一覧取得を拒否
```

`signature()` は最上位の `raw/` を走査しない。一方、`list_inputs()` が呼ぶ `check_enumerable()` は、除外対象を剪定せず、`os.walk(root, onerror=fail)` で全体を走査する。

このため、次が起きる。

- `build` と `serve` は、入力の保護対象を調べる段階で失敗する。
- 起動済みでも、ページを編集すると再構築が失敗し、旧内容の表示が続く。
- `stop` も `_prepare_state()` で同じ列挙を行うため、動いているサーバーに停止要求を送れない。

ファイルを書かず、実際の `os.walk()` に対する列挙結果と権限エラーを注入して確認した。

```text
signature_unchanged: true
list_inputs: EnumerationError
_prepare_state: EnumerationError
```

根拠：[除外なしの走査と入力列挙](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:83)、[signature の除外](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:117)、[起動準備](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:670)、[停止処理](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:790)。

既存の除外試験は `signature()` だけを確認しているため、この食い違いを検出しない。[該当試験](/C:/Works/info-hive-dev/tests/wiki/test_browse.py:234)

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| Wiki 配下の全ディレクトリを列挙できる必要がある | 入力ではない `raw/`、`assets/`、`.wiki-cache/` などに権限制限がある |
| `control/locate` が wikilink と同じ入力表記を受け付ける | 行き先に `\` や先頭の `/` がある |
| 選択した中核と、共有状態の生成日時は同じ世代に属する | 中核の取得後、描画前に別要求の再構築が完了する |

## 見落としと軽微な問題

### 【軽微】`--page` の解決が wikilink と一致しない

`concepts/a.md` がある場合、実際の中核と HTTP の振り分け処理で次を確認した。

| 行き先 | `Core.resolve()` | `control/locate` |
|---|---|---|
| `concepts/a` | resolved | 200／resolved |
| `concepts\a` | resolved | 404 |
| `/concepts/a` | resolved | 404 |

`_locate()` が符号化した行き先を、サーバーがデコードしてからパス全体の検査に通すためである。CLI では `unavailable` となり、指定ページではなく索引が開く。

根拠：[パスの検査](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:489)、[行き先の送信](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:686)、[wikilink の正規化](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:217)。

### 【軽微】manifest の世代と生成日時が別世代になる

`_view()` は取得済みの中核 `c` と、後から読む `app.state.generated_at` を組み合わせる。この間に別要求が再構築すると、旧世代に新世代の日時が付く。

その実行順をメモリ上で再現し、実際の描画から次を得た。

```json
{"generation":"gen-A","generated_at":"TIME-B"}
```

根拠：[中核と生成日時の更新](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:396)、[共有状態から日時を読む描画](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:528)。

## 検証した事実

ローカル検証は Windows／Python 3.14.6。関係表の検証には、既存環境の PyYAML 6.0.3 を読み込んだ。ファイルは変更していない。

| 確認事項 | 結果 |
|---|---|
| 過去6回の修正と対応表 | コード上は一致。今回の重大欠陥は、列挙失敗対策の走査範囲に残る問題 |
| 保護対象の `stat` 失敗 | `Refused` になることを確認 |
| 誤った YAML 日付・`node_types: []` | 中核全体を止めず、関係表の状態に反映することを確認 |
| `sources: [true]` | `true.md` への関係になり、未解決診断が出ないことを確認 |
| 出力名の `NamesTest` | 5件成功 |
| 日本語コーパス27ページと lint | 未解決リンク・リンク抽出が一致。31出力をメモリ上で生成 |
| Markdown の組合せ1,200件 | 描画例外は発生せず |
| CI の両OS実行 | **実行結果まで確認**。最新runでは両OSとも Python・Chromiumの2方式・起動速度試験が成功 |
| 起動速度 | 最新CIの中央値は Ubuntu 1.530秒、Windows 3.182秒 |
| 既存スクリプトの振る舞い不変 | **確かめられず**。既存の全回帰試験は再実行していない |

CI の根拠：[Ubuntu のジョブ](https://github.com/to884/info-hive-dev/actions/runs/42987094417/job/130410742653)、[Windows のジョブ](https://github.com/to884/info-hive-dev/actions/runs/42987094417/job/130410743159)。

## 崩せなかった点

実際の HTTP ハンドラーをメモリ上の接続で通した範囲では、次を越えられなかった。

- Host 不一致は421、誤トークンと閲覧トークンによる停止は404になった。
- 符号化した `..`、`\`、NUL、不正UTF-8、空要素、`.`、未知名は404になった。
- 確認した応答にはCSPが付き、Wikiルートや操作トークンは混入しなかった。
- 要求パスから任意ファイルを読む経路、閲覧トークンで操作口に到達する経路は示せなかった。

使用した MCP サーバー: GitHub  
使用した Agent Skills: なし
