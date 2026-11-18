---
url: "https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting"
title: "Troubleshooting thinking"
fetched_at: "2026-11-18T22:03:42+09:00"
source_sha256: "584c0f498455cdadd48e2eadff99890baef629ac0b92b2cfe508b5963ae14486"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# 推論のトラブルシューティング

推論の問題を診断して対処します。設定に起因する 400 エラー、空または欠落した推論ブロック、max_tokens による停止、キャッシュミスを扱います。

この機能にデータ保持なし（Zero Data Retention、ZDR）がどう適用されるかは、[API とデータ保持](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)を参照してください。

このページでは、推論の設定や、返された推論ブロックを後続のリクエストで送り返すときに起きる問題を扱います。最初の節では、各モデルが受理する推論設定と拒否する設定を示します。以降の節は観測できる症状ごとに並べてあり、エラーメッセージや予期しない応答から原因と対処法を調べられます。推論の仕組みについては[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)を参照してください。

## モデル別の推論の対応状況、既定値、拒否される設定

推論の設定に関するエラーの多くは、リクエストの `thinking.type` の値とモデルの対応が合わない場合に起きます。ほとんどのモデルでは `thinking: {type: "adaptive"}` で推論が動き、多くは既定で有効です。一部の旧モデルでは、`thinking: {type: "enabled", budget_tokens: N}` で指定する旧方式の手動モードである[拡張推論](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)を使います。

Claude 4.6 のモデルでは、`thinking.type: "enabled"` と `budget_tokens` を使う拡張推論は非推奨ですが、リクエストは引き続き成功します。Claude 4.7 以降のモデルでは拡張推論に対応せず、指定すると 400 エラーになります。推論に対応する Claude 4.5 以前のモデルでは、拡張推論だけを使えます。Claude Mythos Preview は両方のモードに対応します。両方に対応するモデルでは[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking)を使います。

表は、各モデルが対応する推論、既定の挙動、400 エラーで拒否される `thinking.type` の値を示します。拒否欄にない値は受理されます。`"between_tools"` を受理するのは Claude Sonnet 5.5 だけです。このモデルでは `"disabled"` の代わりにこの値を使います。

| モデル | 推論の種類 | 既定の挙動 | 400 エラーになる値 |
|---|---|---|---|
| Claude Fable 5.2 | 適応型だけを使える | 常に有効 | `"enabled"`, `"disabled"` |
| Claude Mythos 5.2 | 適応型だけを使える | 常に有効 | `"enabled"`, `"disabled"` |
| Claude Fable 5.1 | 適応型だけを使える | 常に有効 | `"enabled"`, `"disabled"` |
| Claude Mythos 5.1 | 適応型だけを使える | 常に有効 | `"enabled"`, `"disabled"` |
| Claude Fable 5 | 適応型だけを使える | 常に有効 | `"enabled"`, `"disabled"` |
| Claude Mythos 5 | 適応型だけを使える | 常に有効 | `"enabled"`, `"disabled"` |
| Claude Mythos Preview | 適応型と拡張推論 | 常に有効 | `"disabled"` |
| Claude Opus 5.5 | 適応型だけを使える | 常に有効 | `"enabled"`, `"disabled"` |
| Claude Opus 5 | 適応型だけを使える | 既定で有効 | `"enabled"`, `"disabled"`（注 2） |
| Claude Opus 4.8 | 適応型だけを使える | 既定で無効 | `"enabled"` |
| Claude Opus 4.7 | 適応型だけを使える | 既定で無効 | `"enabled"` |
| Claude Sonnet 5.5 | 適応型と `between_tools`（注 3） | 既定で有効 | `"enabled"`, `"disabled"` |
| Claude Sonnet 5 | 適応型だけを使える | 既定で有効 | `"enabled"` |
| Claude Haiku 5.5 | 適応型だけを使える | 既定で有効 | `"enabled"`, `"disabled"`（注 2） |
| Claude Opus 4.6 | 適応型と拡張推論（非推奨、注 1） | 既定で無効 | 該当なし |
| Claude Sonnet 4.6 | 適応型と拡張推論（非推奨、注 1） | 既定で無効 | 該当なし |
| Claude Opus 4.5 | 拡張推論だけを使える | 既定で無効 | `"adaptive"` |
| Claude Haiku 4.5 | 拡張推論だけを使える | 既定で無効 | `"adaptive"` |
| Claude Sonnet 4.5 | 拡張推論だけを使える | 既定で無効 | `"adaptive"` |

*注 1。これらのモデルでは `enabled` と `budget_tokens` を引き続き使えますが、非推奨です。適応型推論を使います。*  
*注 2。Claude Opus 5 と Claude Haiku 5.5 は、[effort](https://platform.claude.com/docs/en/build-with-claude/effort) が `high` 以下なら `"disabled"` を受理します。effort が `xhigh` や `max` の場合、この組み合わせは 400 エラーになります。Claude Opus 5 ではリクエストごとにこの制約が適用されます。Claude Haiku 5.5 では、メッセージ単位の effort が適用中の段階と異なる場合も 400 エラーになります。*  
*注 3。Claude Sonnet 5.5 は、effort が `high` 以下なら `"between_tools"` を受理します。effort が `xhigh` や `max` の場合や、メッセージ単位の effort が適用中の段階と異なる場合は 400 エラーになります。*

「常に有効」（`Always on`）のモデルでは推論を無効にできません。「既定で有効」（`On`）のモデルでは、設定を省略すると推論が有効です。Claude Opus 5、Claude Sonnet 5、Claude Haiku 5.5 は `thinking: {type: "disabled"}` を受理します。Claude Sonnet 5.5 で回答前の推論を省くには、`thinking: {type: "between_tools"}` を送ります。

それ以前の Claude 4 モデル（Claude Opus 4.1、Claude Sonnet 4、Claude Opus 4）は拡張推論だけに対応します。提供状況は[モデルの廃止予定](https://platform.claude.com/docs/en/about-claude/model-deprecations)を参照してください。Claude Fable 5.2、Claude Mythos 5.2、Claude Fable 5.1、Claude Mythos 5.1、Claude Fable 5、Claude Mythos 5 を[データ保持なし](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements)で使うには、Anthropic の明示的な許可が必要です。

## `"thinking.type.enabled"` に対応していないという 400 エラー

リクエストは 400 エラーになり、次のメッセージが返ります。

```text
"thinking.type.enabled" is not supported for this model. Use "thinking.type.adaptive" and "output_config.effort" to control thinking behavior.
```

指定したモデルが拡張推論に対応していないためです。[モデル別の設定表](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#rejected-configurations)を参照してください。

リクエストを `thinking: {type: "adaptive"}` に切り替え、推論の深さは `effort` で調整します。`budget_tokens` からの移行手順は[適応型推論への移行](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#migrating-to-adaptive-thinking)を参照してください。

## `thinking: {type: "disabled"}` を送ると 400 エラーになる

リクエストは 400 エラーになります。Claude Fable 5.2、Claude Mythos 5.2、Claude Fable 5.1、Claude Mythos 5.1、Claude Fable 5、Claude Mythos 5、Claude Opus 5.5 では次のメッセージが返ります。

```text
"thinking.type.disabled" is not supported for this model. Use "thinking.type.adaptive" and "output_config.effort" to control thinking behavior.
```

これらのうち拡張推論を受理する唯一のモデルである Claude Mythos Preview では、次のメッセージが返ります。

```text
"thinking.type.disabled" is not supported for this model. Thinking defaults to adaptive mode when not specified; use "thinking.type.enabled" with "budget_tokens" for extended thinking.
```

これらのモデルでは推論が常に有効なためです。[モデル別の設定表](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#rejected-configurations)を参照してください。

これらのモデルは設定なしで推論するため、`thinking` パラメーターを省略します。応答に推論テキストを出したくない場合は、`display: "omitted"` で表示を省きます。[推論の表示を設定する](https://platform.claude.com/docs/en/build-with-claude/thinking#controlling-thinking-display)を参照してください。

Claude Opus 5 と Claude Haiku 5.5 も、`"disabled"` で 400 エラーになることがあります。`thinking: {type: "disabled"}` を受理するのは [effort](https://platform.claude.com/docs/en/build-with-claude/effort) が `high` 以下の場合で、`xhigh` または `max` との組み合わせは拒否されます。effort を下げるか、`thinking` に `{"type": "adaptive"}` を指定します。

Claude Sonnet 5.5 では、`thinking: {type: "disabled"}` はどの段階でも 400 エラーになります。次のメッセージが返ります。

```text
To turn thinking off on this model, send "thinking": {"type": "between_tools"} instead of {"type": "disabled"}. The model does not think before responding. The short updates it writes between tool calls come back as thinking blocks.
```

Claude Sonnet 5.5 で回答前の推論を省くには、effort を `high` 以下にし、`thinking: {type: "between_tools"}` を送ります。

## `"thinking.type.between_tools"` に対応していないという 400 エラー

リクエストは 400 エラーになり、次のメッセージが返ります。

```text
"thinking.type.between_tools" is not supported for this model.
```

`thinking: {type: "between_tools"}` を受理するのが Claude Sonnet 5.5 だけのためです。[モデル別の設定表](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#rejected-configurations)を参照してください。

`between_tools` を送るのは Claude Sonnet 5.5 に限ります。他のモデルでは `thinking` を省略するか、表で受理される `thinking.type` の値を使います。

## 推論が無効なときに指定できない effort を示す 400 エラー

Claude Sonnet 5.5 で effort が `xhigh` または `max` のときに `thinking: {type: "between_tools"}` を指定すると 400 エラーになり、次のメッセージが返ります。

```text
output_config.effort 'xhigh' is not supported when thinking is disabled on this model. Use effort 'high' or below, or enable thinking.
```

Claude Sonnet 5.5 が `between_tools` を受理するのは [effort](https://platform.claude.com/docs/en/build-with-claude/effort) が `high` 以下の場合です。`between_tools` は回答前の推論を省く設定なので、リクエストが `"disabled"` を送っていなくてもエラーには「推論が無効」と表示されます。メッセージにはリクエストで指定した段階が示されます。

effort を `high` 以下に下げます。`xhigh` または `max` で実行するには、`thinking` フィールドを省略するか `thinking: {"type": "adaptive"}` を送り、適応型推論を使います。エラーの「推論を有効にする」はこの操作を意味します。Claude Sonnet 5.5 は `"enabled"` を 400 エラーで拒否します。

Claude Haiku 5.5 では、effort が `xhigh` または `max` のときに `thinking: {type: "disabled"}` を送ると同じメッセージが返ります。`"disabled"` を受理するのは `high` 以下の場合です。effort を下げるか、`thinking` に `{"type": "adaptive"}` を指定します。

## 推論が無効なときに effort を変更できないという 400 エラー

Claude Sonnet 5.5 で `thinking: {type: "between_tools"}` を指定し、[メッセージ単位の effort](https://platform.claude.com/docs/en/build-with-claude/effort-per-message) で段階を変えると、リクエストは 400 エラーになり、次のメッセージが返ります。

```text
messages.N: output_config.effort 'low' differs from the 'high' in effect before it; effort cannot change when thinking is disabled on this model. Use effort 'high', or enable thinking.
```

`between_tools` は回答前の推論を省く設定なので、エラーには「推論が無効」と表示されます。`between_tools` では会話途中の段階変更ができず、メッセージ単位の `output_config.effort` が適用中の段階と異なる場合は 400 エラーになります。`messages.N` は新しい段階を指定したメッセージの位置です。

そのメッセージ単位の effort を取り除くか、適用中の段階に合わせます。ターンごとに変えるには、`thinking` フィールドを省略するか `thinking: {"type": "adaptive"}` を送り、適応型推論を使います。エラーの「推論を有効にする」はこの操作を意味します。

Claude Haiku 5.5 でも、`thinking: {type: "disabled"}` を指定したリクエストが、適用中の段階と異なるメッセージ単位の effort を設定すると、同じメッセージが返ります。該当するメッセージ単位の effort を取り除きます。ターンごとに変える場合は、`thinking` に `{"type": "adaptive"}` を指定します。

## 適応型推論に対応していないという 400 エラー

リクエストは 400 エラーになり、次のメッセージが返ります。

```text
adaptive thinking is not supported on this model
```

指定したモデルが拡張推論だけに対応するためです。[モデル別の設定表](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#rejected-configurations)を参照してください。

`thinking: {type: "enabled", budget_tokens: N}` を使います。詳しい設定は[拡張推論](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)を参照してください。

## 推論ブロックを変更できないという 400 エラー

ツールの結果を返すリクエストが、次の文言を含む 400 の `invalid_request_error` になります。

```text
`thinking` or `redacted_thinking` blocks in the latest assistant message cannot be modified
```

複数ターンの会話やツール利用では、以前のアシスタントメッセージを `thinking` と `redacted_thinking` ブロックごと API に送り返します。API はブロックの署名を検証します。

リクエスト内の推論ブロックが API の返した内容と一致しない場合に、このエラーが出ることがあります。メッセージには「latest」とありますが、不一致はどのアシスタントターンにも起こり得ます。

推論ブロックを含め、アシスタントターンを受け取ったとおりに送り返します。規則は[推論ブロックを保持する](https://platform.claude.com/docs/en/build-with-claude/thinking#preserving-thinking-blocks)、各 SDK のコード例は[ツール利用と複数ターンの処理における推論](https://platform.claude.com/docs/en/build-with-claude/thinking-tool-workflows#two-turn-tool-use-round-trip)の往復手順を参照してください。

## 推論ブロックの署名が無効だという 400 エラー

Claude Fable 5.2、Claude Mythos 5.2、Claude Fable 5.1、Claude Mythos 5.1、Claude Opus 5.5、Claude Sonnet 5.5、Claude Haiku 5.5 に以前の推論ブロックを送り返すと、次のメッセージが含まれる 400 の `invalid_request_error` になる場合があります。

```text
messages.{i}.content.{j}: Invalid `signature` in `thinking` block. The block is bound to a different conversation. Remove the block, or set `thinking.block_binding.prefix_mismatch_behavior` to "drop_block".
```

リクエストで `thinking-binding-controls-2026-08-01` のベータヘッダーを送っていない場合、エラーに次の文言が加わります。``That setting requires the `thinking-binding-controls-2026-08-01` value in the `anthropic-beta` header.``

エラーメッセージの末尾に、何が変わったかを示す文が付くことがあります。対象は `system` プロンプト、`tools` の一覧、最初に異なったメッセージやブロック、欠落または追加された内容、欠落したか順序の変わった以前の推論ブロックです。この文は人が読んだりログに残したりするためのものです。文言は変わり得るので、コードでの照合には使いません。

メッセージが ``Invalid `signature` in `thinking` block`` で終わる場合は、署名そのものの検証に失敗しています。署名が途中で切れた、変更された、または空のまま送り返された場合で、`prefix_mismatch_behavior` は適用されません。

送り返した推論ブロックが先頭部分の照合を通過するには、それより前の `system` プロンプト、`tools` とメッセージが同じである必要があります。[同じ内容を保つ必要がある箇所と理由](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)を参照してください。このエラーは、リクエスト間で以前の会話の一部が変わったことを示します。次が原因になります。

- ターンの編集、並べ替え、削除
- ターンごとの注意書きの挿入と、その後の削除
- `system` プロンプトや `tools` 配列の再構築
- クライアント側で会話を圧縮した際に、直近のターンと推論をそのまま残した

サーバー側の[トークン数を基準にした圧縮](https://platform.claude.com/docs/en/build-with-claude/compaction-threshold)と[コンテキスト編集](https://platform.claude.com/docs/en/build-with-claude/context-editing)では、このエラーは発生しません。[オンデマンド圧縮](https://platform.claude.com/docs/en/build-with-claude/compaction-on-demand)では、要約の後ろに残したターンの推論が、[推論を残すための条件](https://platform.claude.com/docs/en/build-with-claude/compaction-thinking-blocks#conditions-for-kept-thinking-to-stay-valid)を満たさない場合にエラーになります。`thinking.block_binding.prefix_mismatch_behavior` を指定しないリクエストについては、[先頭部分を照合するモデル](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#enforcement)を参照してください。

同じリクエスト本体で再試行してもエラーは解消しません。保存済みの履歴に変更が残っている場合は、コードを直すだけでも解消しません。会話を続けるには、次のいずれかを行います。

- 再試行とそれ以降のリクエストで、`thinking-binding-controls-2026-08-01` ベータヘッダーを送り、`thinking.block_binding.prefix_mismatch_behavior` を `"drop_block"` にします。無効になった推論が取り除かれ、リクエストが成功します。Claude Sonnet 5.5 と Claude Haiku 5.5 で `block_binding` を使えるのは、`thinking: {"type": "adaptive"}` の場合だけです。他の推論設定では `block_binding` を送れないため、次の方法を使います。
- エラーが示したブロックと、それ以降のすべての `thinking` および `redacted_thinking` ブロックを取り除き、各ターンのほかのブロックは残します。再試行し、取り除いたブロックは後続のリクエストにも含めません。

新しい会話で同じエラーが起きないよう、原因を直します。履歴は追記だけを行い、以前のターンを送受信したとおりに送り返します。`system` や `tools` を編集する代わりに、[会話途中のシステムメッセージ](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)で指示を追加します。履歴を短くする処理には、サーバー側の[コンテキスト編集](https://platform.claude.com/docs/en/build-with-claude/context-editing)や[圧縮](https://platform.claude.com/docs/en/build-with-claude/compaction)を使います。

送り先のモデルが読めない推論ブロックはこのエラーを起こしません。API はブロックを取り除き、ベータヘッダーが指定されていれば `input_transformations` で知らせます。

## 応答の thinking フィールドが空になる

応答には `thinking` ブロックがありますが、`thinking` フィールドは空文字列で、`signature` フィールドだけに値が入っています。

一部のモデルでは `display` の既定値が `"omitted"` で、推論ブロックのテキストを省いて返すためです。[推論の表示を設定する](https://platform.claude.com/docs/en/build-with-claude/thinking#controlling-thinking-display)を参照してください。

要約された推論テキストを受け取るには、推論設定で `display: "summarized"` を指定します。モデルごとの既定値は[推論の表示を設定する](https://platform.claude.com/docs/en/build-with-claude/thinking#controlling-thinking-display)を参照してください。一部のモデルがツール呼び出しの間に書く短い進捗報告だけを受け取るには、ベータ機能の `display: "updates"` を指定します。[ツール呼び出し間の進捗報告](https://platform.claude.com/docs/en/build-with-claude/thinking#progress-updates)を参照してください。

`thinking` フィールドが空でもブロックは完全で、`signature` が推論を保持しています。他のブロックと同様に、ターンと一緒に送り返します。[アシスタントターンを受け取ったとおりに返す](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/change-tools-or-instructions#append-assistant-turns-exactly-as-returned)を参照してください。

## 一部のターンで推論ブロックが現れない

推論を設定していても、一部の応答には `thinking` ブロックが含まれません。

適応型推論では通常の挙動です。Claude は直接回答できるほど単純だと判断したリクエストでは、推論を省きます。

推論する頻度や深さを増やしたい場合は、`effort` を上げるか、プロンプトで指示します。[Claude が推論する頻度を調整する](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#tuning-thinking-behavior)を参照してください。

ツール利用を強制する `tool_choice`（`{"type": "any"}` または名前で指定したツール）でも `thinking` ブロックは返らず、応答はツール呼び出しから始まります。ツールを呼ぶ前に推論させるには、`tool_choice: {"type": "auto"}` を使い、いつツールを使うかをプロンプトに書きます。

## ツール呼び出しや XML タグがテキストに現れる

応答では、`tool_use` ブロックとして出すはずのツール呼び出しをテキストに書いたり、利用者に見えるテキストに `<thinking>` などの内部用 XML タグを含めたりする場合があります。テキストに漏れたツール呼び出しは実行されません。また、エージェントがツールを繰り返し使う処理では、そのテキストが会話履歴に残るため、後続のターンにも影響します。

これは Claude Opus 5 で推論を無効にしたときに起き、検索などツールを多用する処理で特に多く見られます。推論を行わないようシステムプロンプトで指示すると、タグが漏れる頻度が上がります。

既定の推論を有効に戻し、`effort` を下げてトークンの費用を抑えます。連携上、推論を無効のままにする必要がある場合は、[推論を無効にして実行する](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5#running-with-thinking-disabled)にあるプロンプトでの対処法を使います。

## `stop_reason: "max_tokens"` で応答が停止する

応答は `stop_reason: "max_tokens"` で終わり、テキストブロックが途中で切れるか、含まれないことがあります。

推論トークンは `max_tokens` に算入されるため、長く推論すると、テキストでの応答を完了する前に上限に達することがあります。

`max_tokens` を上げて推論とテキストの両方に必要な枠を確保するか、`effort` を下げて Claude の推論量を減らします。[費用を調整する](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#cost-control)と[推論とコンテキストウィンドウ](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-the-context-window)を参照してください。

## 推論設定を変えるとキャッシュヒットが減る

それまでキャッシュにヒットしていたリクエストで、`cache_read_input_tokens` が 0 になります。

推論設定と effort の段階（または既定値）は、キャッシュ済みプロンプトの先頭部分に含まれます。いずれかを変えると、先頭部分が新しくなります。推論モードや `budget_tokens` を変えると、メッセージのキャッシュの区切りが無効になり、effort の値の変更でも無効になる場合があります。モデルが設定をどこに反映するかによって、ツールやシステムプロンプトの区切りも無効になることがあります。

同じ会話を続けるリクエストでは推論設定と effort の段階を維持します。パラメーターに既定値を明示しても省略時と同じ扱いになり、キャッシュは無効になりません。[推論とプロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-prompt-caching)を参照してください。

## effort を指定しても推論が変わらない

`effort` を変えても、推論する頻度や深さが変わりません。

推論を主に effort で調整できるのは適応型推論の場合です。拡張推論だけに対応するモデルでは、推論の深さを `budget_tokens` で指定します。

該当するモデルでは `budget_tokens` を調整するか、モデルで使われている推論モードを確認します。[推論と effort](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-effort)を参照してください。拡張推論だけを使い、effort にも対応する唯一のモデルである Claude Opus 4.5 では、effort を推論予算と組み合わせます。[予算の規則と調整](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#budget-rules-and-tuning)を参照してください。

## 関連資料

[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)

推論の仕組み、設定方法、ツール、キャッシュ、ストリーミングとの関係を説明します。

[エラー](https://platform.claude.com/docs/en/api/errors)

推論設定に関する 400 エラーとサーバーが返す正確な文言を含む、エラーのリファレンスです。

[適応型推論への移行](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#migrating-to-adaptive-thinking)

`budget_tokens` を使うリクエストを、effort を伴う適応型推論に切り替えます。
