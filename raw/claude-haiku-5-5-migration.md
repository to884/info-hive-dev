---
url: "https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide"
title: "Claude Haiku 5.5 migration guide"
fetched_at: "2026-11-18T23:11:16+09:00"
source_sha256: "ee0b40e8c4f404fe2632cc15b92b9ed45d602c8997cc014dbf67ef1b10cf24b4"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# Claude Haiku 5.5 への移行ガイド

以前の Haiku モデルから Claude Haiku 5.5 へ切り替える方法を説明します。新しいモデル ID、エラーになる設定、推論の挙動の変化、移行元モデル別のチェックリストを掲載しています。

このガイドは [Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) を使うコードの移行を扱います。[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) を使う場合に必要な変更はモデル名の更新です。

Claude Code にコードの移行を任せる

```text
/claude-api migrate this project to claude-haiku-5-5
```

このガイドは Claude Haiku 4.5 を呼び出すコードから Claude Haiku 5.5 への移行を扱います。Claude Haiku 3.5 または Claude Haiku 3 を呼び出すコードには、[Claude Haiku 3.5 以前から Claude Haiku 5.5 への移行](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#migrating-from-haiku-35)の変更も適用します。Sonnet や Opus に切り替える場合は[モデル移行ガイド一覧](https://platform.claude.com/docs/en/about-claude/models/migration-guide)、Claude Haiku 4.5 の提供期間は[モデルの廃止予定](https://platform.claude.com/docs/en/about-claude/model-deprecations)を参照してください。

## 移行元モデル別のチェックリスト

上から順に確認し、現在のモデル名があるグループで止めます。Claude Haiku 4.5 では最初のグループだけを適用します。各項目はコードへの変更 1 件に対応します。

### すべての移行元モデル

1. モデル ID を利用先のプラットフォームの Claude Haiku 5.5 の ID に置き換えます。[Claude Haiku 5.5 のモデル ID を使う](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#use-the-claude-haiku-5-5-model-id)を参照してください。
2. 同じテキストや大きい画像に必要なトークン数が増えるため、プロンプトのトークン数を数え直し、`max_tokens` の上限と費用の見積もりを見直します。[トークンを数え直す](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#recount-tokens)を参照してください。
3. リクエストで `thinking: {"type": "enabled", "budget_tokens": N}` を送っている場合は、`thinking` を `{"type": "adaptive"}` に変更します。[推論を設定する](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#configure-thinking)を参照してください。
4. 最初の内容ブロックを回答として読み取るコードでは、`type` でブロックを選びます。[推論を設定する](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#configure-thinking)を参照してください。
5. リクエストから `temperature`、`top_p`、`top_k` を取り除きます。[サンプリングパラメーターを取り除く](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#remove-sampling-parameters)を参照してください。
6. モデルに続きを生成させるため `messages` の末尾をアシスタントターンにしている場合は、ユーザーターンに変えます。[アシスタントの応答の事前入力を置き換える](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#replace-assistant-prefill)を参照してください。
7. コンピューター操作を使う場合は、`computer_20250124` を `computer_toolset_20260801` ツールセットに置き換えます。Amazon Bedrock では `computer_20251124` も使えます。[コンピューター操作をツールセットに移行する](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#computer-use-toolset)を参照してください。
8. 保存した会話を別アカウントで再現する処理では、会話を生成元アカウントで再現します。[生成元アカウントで推論ブロックを再送する](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#replay-thinking-blocks-through-the-producing-account)を参照してください。
9. リクエスト間に会話の `system`、`tools`、過去の `messages` を変更し、推論ブロックを送り返すコードでは、履歴を追記だけで管理します。[過去のターンを保持する](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#keep-earlier-turns-unchanged)を参照してください。
10. `stop_reason: "refusal"` を処理します。Claude Haiku 5.5 の安全性分類器はリクエストを拒否することがあります。サーバー側のフォールバックはありません。[安全対策による拒否](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5#safeguard-refusals)を参照してください。

組織が Claude Haiku 4.5 の [Priority Tier](https://platform.claude.com/docs/en/api/service-tiers#supported-models) を契約している場合は、キャパシティを別途計画します。Claude Haiku 5.5 は Priority Tier に対応しません。

### Claude Haiku 3.5 以前

1. Claude Haiku 3.5 または Claude Haiku 3 のモデル ID を、利用先のプラットフォームの Claude Haiku 5.5 の ID に置き換えます。[Claude Haiku 3.5 以前から Claude Haiku 5.5 への移行](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#migrating-from-haiku-35)を参照してください。
2. `code_execution_20250522` ツールを使う場合は、`code_execution_20250825` 以降に変更します。
3. テキストエディターツールを使う場合は、`text_editor_20250728` に変更します。
4. 停止理由 `refusal` と `model_context_window_exceeded` を処理します。
5. ツール呼び出しの文字列パラメーターを完全一致で比較するコードでは、末尾の改行も考慮します。
6. プロンプトを見直します。

## Claude Haiku 5.5 のモデル ID を使う

Claude Haiku 4.5 のモデル ID を、利用先のプラットフォームの Claude Haiku 5.5 の ID に置き換えます。

| プラットフォーム | Claude Haiku 4.5 | Claude Haiku 5.5 |
|---|---|---|
| Claude API | `claude-haiku-4-5-20251001` または `claude-haiku-4-5` | `claude-haiku-5-5` |
| Amazon Bedrock | `anthropic.claude-haiku-4-5` | `anthropic.claude-haiku-5-5` |
| Claude Platform on AWS | `claude-haiku-4-5` | `claude-haiku-5-5` |
| Claude Models on Google Cloud (Anthropic managed) | `claude-haiku-4-5-20251001` | `claude-haiku-5-5` |
| Claude Models on Google Cloud (Google managed) | `claude-haiku-4-5@20251001` | `claude-haiku-5-5` |
| Microsoft Foundry | `claude-haiku-4-5` | `claude-haiku-5-5` |

`claude-haiku-5-5` は固定のモデル ID です。日付の接尾辞や別のエイリアスはありません。

## トークンを数え直す

Claude Haiku 5.5 は Claude 4.7 以降と同じトークナイザーを使います。このトークナイザーを使うほかのモデルと同様、同じ入力テキストを Claude Haiku 4.5 と Claude Haiku 5.5 で比較すると、後者のトークン数が約 30% 増えます。増加幅は内容によって異なります。リクエスト、応答、ストリーミングのイベントの構造は共通です。トークン単位での測定や予算には次の変更があります。

- 同じテキストでも `usage` の各項目と[トークン数の計測](https://platform.claude.com/docs/en/build-with-claude/token-counting)の値が増えます。
- 同じトークン数に収まるテキストが短くなります。
- Claude Haiku 4.5 に合わせた `max_tokens` の上限では、同等の出力が途中で切れる場合があります。
- Claude Haiku 4.5 のトークン数に基づく費用の見積もりは、Claude Haiku 5.5 のトークン数と料金で計算し直します。長いプロンプトに適用される高い料金も考慮します。[料金](https://platform.claude.com/docs/en/about-claude/pricing)と[長いコンテキストの料金](https://platform.claude.com/docs/en/about-claude/pricing#long-context-pricing)を参照してください。

大きな画像もトークン消費が増える場合があります。Claude Haiku 5.5 は高解像度の画像区分を使い、長辺が 2,576 ピクセルまたは 4,784 ビジュアルトークンを超える画像は縮小します。Claude Haiku 4.5 以前は標準の画像区分を使い、長辺が 1,568 ピクセルまたは 1,568 ビジュアルトークンを超える画像を縮小します。2,000×1,500 ピクセルの画像は、Claude Haiku 5.5 で Claude Haiku 4.5 の約 2.5 倍のビジュアルトークンを消費します。[解像度とトークンの消費量](https://platform.claude.com/docs/en/build-with-claude/vision#evaluate-image-size)を参照してください。

Claude Haiku 4.5 で測ったトークン数は見直します。`model` に `claude-haiku-5-5` を指定し、プロンプトを測り直します。

## 推論を設定する

Claude Haiku 5.5 の推論設定は Claude Haiku 4.5 と異なります。`thinking` の値に `{"type": "enabled", "budget_tokens": N}` を指定すると 400 エラーになるため、別の `thinking` の値を指定する必要があります。

変更前の例では、Claude Haiku 4.5 のリクエストで `thinking` を `enabled` に設定し、トークン予算を指定していました。

```json
{
  "model": "claude-haiku-4-5",
  "max_tokens": 16000,
  "thinking": { "type": "enabled", "budget_tokens": 8000 },
  "messages": [{ "role": "user", "content": "..." }]
}
```

変更後は、同じリクエストで Claude Haiku 5.5 の適応型推論を使います。`thinking` の値を変更し、`output_config.effort` で推論量を調整します。

```json
{
  "model": "claude-haiku-5-5",
  "max_tokens": 16000,
  "thinking": { "type": "adaptive" },
  "output_config": { "effort": "medium" },
  "messages": [{ "role": "user", "content": "..." }]
}
```

既定で適応型推論が有効なため、リクエストで `thinking` を設定しなくても、応答の冒頭に 1 つ以上の `thinking` ブロックが現れる場合があります。`thinking` を省略するか `{"type": "adaptive"}` を指定し、[effort](https://platform.claude.com/docs/en/build-with-claude/effort) で調整します。トークンを節約するため Claude Haiku 4.5 で推論を無効にしていた場合や、小さい予算で実行していた場合は、effort を下げます。低い段階では推論量が減り、単純なリクエストでは推論を省く場合があります。プロンプトの書き方は [effort で推論を調整する](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5#use-effort-to-control-thinking)を参照してください。内容ブロックは `type` で選び、ツール結果を返すときは `thinking` ブロックをそのまま送り返します。

推論トークンは `max_tokens` に含まれます。`max_tokens` が小さいと、`thinking` ブロックを返したあと、テキストを生成する前に `stop_reason: "max_tokens"` で停止する場合があります。Claude Haiku 4.5 用に `max_tokens` を小さく設定していた場合は、推論に使う分を見込んで上限を引き上げるか、[effort](https://platform.claude.com/docs/en/build-with-claude/effort) を下げます。

過去のアシスタントターンの推論ブロックはコンテキストに残り、入力トークンとして数えられます。Claude Haiku 4.5 では直近のターンのブロックだけが残ります。そのため、複数ターンの会話の入力トークンは、トークナイザーの変更による増加分を上回る場合があります。古いブロックを取り除くには[推論ブロックの削除](https://platform.claude.com/docs/en/build-with-claude/context-editing#thinking-block-clearing)を使います。[モデル別の推論ブロックの保持](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-block-preservation-by-model)を参照してください。

Claude Haiku 5.5 は既定で `thinking` ブロックの `thinking` フィールドを空にし、`signature` だけを返します。Claude Haiku 4.5 は推論の要約を返します。要約を受け取るには、`thinking: {"type": "adaptive", "display": "summarized"}` を指定します。

Claude Haiku 5.5 は強制の `tool_choice`（`any` または名前で指定したツール）を受理します。この場合、応答はツール呼び出しから始まり、`thinking` ブロックは返りません。ツールを呼ぶ前に推論させるには `tool_choice: {"type": "auto"}` を指定し、ツールを使う条件をプロンプトに書きます。

Claude Haiku 4.5 から Claude Haiku 5.5 に会話を切り替えると、推論は保持されます。ほかの切り替えは、移行元と移行先の組み合わせによります。

| 切り替え | 推論を保持できるか |
|---|---|
| Claude Haiku 4.5 以前、Claude Sonnet 5 以前、Claude Opus 4.8 以前から Claude Haiku 5.5 へ | はい |
| それ以外のモデルから Claude Haiku 5.5 へ | いいえ。API が移行元モデルの推論ブロックをエラーなしで取り除く。 |
| Claude Haiku 5.5 から Claude Opus 5.5、Claude Sonnet 5.5、Claude Fable 5.2、Claude Mythos 5.2 へ | はい。Claude API と Claude Models on Google Cloud (Google managed) に限る。 |
| Claude Haiku 5.5 からそれ以外のモデルへ | いいえ |

[モデルを切り替えて元に戻す](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#switching-models)を参照してください。Claude Haiku 5.5 を含まない切り替えについては、[Claude API でモデルを切り替えても推論が保持される組み合わせ](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#which-model-switches-keep-reasoning)を参照してください。

## サンプリングパラメーターを取り除く

Claude Haiku 5.5 では `temperature`、`top_p`、`top_k` を省略し、プロンプトでモデルの挙動を調整します。

## アシスタントの応答の事前入力を置き換える

事前入力とは、モデルに続きを生成させるため、`messages` の末尾にアシスタントターンを置くことです。Claude Haiku 4.5 は推論が無効な場合に受理します。Claude Haiku 5.5 は推論を無効にしても 400 エラーで拒否します。`messages` の末尾をユーザーターンにし、事前入力を使っていた目的に応じて次の方法を使います。

- **出力形式**。[構造化出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)や、分類用の列挙型フィールドを持つツールを使います。
- **前置き**。システムプロンプトで直接回答するように指示します。
- **続きを生成する**。指示をユーザーメッセージに移します。たとえば「前の応答は `[previous_response]` で途切れました。中断した箇所から続けてください」と書きます。
- **文脈を伝える補足**。ユーザーターンに書きます。

## コンピューター操作をツールセットに移行する

Claude Haiku 4.5 はベータヘッダー `computer-use-2025-01-24` を付けて `computer_20250124` ツールによる[コンピューター操作](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)を使えます。Claude Haiku 5.5 は `computer_toolset_20260801` ツールセットでコンピューター操作に対応します。Claude Haiku 5.5 宛てのリクエストで `computer_20250124` を宣言すると 400 エラーになります。

ツールセットに移行するには、ベータヘッダー `computer-use-2025-01-24` を取り除き、`tools` の項目を `{"type": "computer_toolset_20260801"}` に置き換えます。次に、[`computer_20251124` から移行する](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool#migrate-from-computer-20251124)にあるリクエストとエージェントの処理ループの変更を適用します。処理の分岐は従来の `input.action` から各メンバーの `tool_use` ブロックの `name` と `toolset_name` に切り替えます。ターン内の該当ブロックをすべて処理し、各結果に `toolset_name` をそのまま返します。ズームはツールセットで既定で有効です。環境が対応していない場合は `"configs": {"zoom": {"enabled": false}}` を追加します。ベータヘッダー `fine-grained-tool-streaming-2025-05-14` を送っている場合は取り除きます。ツールセット項目と一緒に送ると 400 エラーになります。

Amazon Bedrock では、Claude Haiku 5.5 はベータヘッダー `computer-use-2025-11-24` を付けた `computer_20251124` ツールも受理します。

Claude Haiku 5.5 は Web ページ内の操作に使う[ブラウザー操作ツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)（`browser_toolset_20260801`）に対応します。Claude Haiku 4.5 は非対応です。

## 生成元アカウントで推論ブロックを再送する

Claude Haiku 5.5 の推論ブロックは、生成元のアカウントか、それにリンクしたアカウントで使えます。別のアカウントから送ると、API がモデルに渡す前にブロックを取り除き、その推論を使わずにリクエストは成功します。たとえば 1 つの会話ストアで複数の顧客を扱うサービスなど、会話を保存し、別のアカウントで再現するコードが影響を受けます。会話は生成元のアカウントで再現します。[アカウントとクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#account-bound-thinking)を参照してください。

## 過去のターンを保持する

会話履歴は追記だけで管理します。Claude Haiku 5.5 の推論ブロックは、それより前に送った `system` プロンプト、`tools`、それ以前のすべてのメッセージに変更がない場合に有効です。

[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)に失敗したとき、[400 エラー](https://platform.claude.com/docs/en/api/errors#thinking-block-conversation-mismatch)になるかどうかは条件によります。両方の場合の見分け方と対処は[推論ブロックの先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks)を参照してください。

エラーにつながる変更と対処方法は[システムプロンプト、ツール、履歴をコードで変更する場合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#what-to-check)を参照してください。

## Claude Haiku 3.5 以前から Claude Haiku 5.5 への移行

Claude Haiku 3.5 は Claude API、Amazon Bedrock、Claude Models on Google Cloud (Google managed) で提供を終了しました。Claude Haiku 3 は Claude API と Claude Models on Google Cloud (Google managed) で提供を終了しました。[モデルの廃止予定](https://platform.claude.com/docs/en/about-claude/model-deprecations)を参照してください。

どちらから移行する場合も、先に前の節をすべて適用し、その後に次の変更を反映します。

- **モデル ID**。`claude-3-5-haiku-20241022`、そのエイリアス `claude-3-5-haiku-latest`、または `claude-3-haiku-20240307` を `claude-haiku-5-5` に置き換えます。Claude Models on Google Cloud (Google managed) では `claude-3-5-haiku@20241022` を `claude-haiku-5-5` に置き換えます。Amazon Bedrock では [Claude Haiku 5.5 のモデル ID を使う](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide#use-the-claude-haiku-5-5-model-id)にある ID を使います。
- **コード実行**。Claude Haiku 5.5 は `code_execution_20250825` 以降を受理します。Python 専用の `code_execution_20250522` を使っている場合は、対応するバージョンに切り替えます。[最新のツールバージョンに更新する](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool#upgrade-to-latest-tool-version)を参照してください。
- **テキストエディター**。テキストエディターツールを使っている場合は、`undo_edit` コマンドを持たない `text_editor_20250728`（ツール名は `str_replace_based_edit_tool`）に切り替えます。[テキストエディターツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool)を参照してください。
- **停止理由**。`refusal` と `model_context_window_exceeded` を処理します。[停止理由とフォールバック](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)を参照してください。
- **末尾の改行**。Claude 4.5 以降では、ツール呼び出しの文字列パラメーターの末尾にある改行を保持します。文字列を完全一致で比較するコードでは、改行を考慮します。
- **プロンプト**。Claude 4 以降は、より簡潔で直接的な書き方で応答し、明示的な指示を必要とします。[Claude Haiku 5.5 のプロンプトガイド](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5)と[プロンプトのベストプラクティス](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)に照らして見直します。
