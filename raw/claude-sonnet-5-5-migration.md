---
url: "https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide"
title: "Claude Sonnet 5.5 migration guide"
fetched_at: "2026-11-18T23:00:46+09:00"
source_sha256: "c46096952f32cf93f3a17cb12f66fe982cab767d8a608d519f703c919ec9b39b"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# Claude Sonnet 5.5 への移行ガイド

以前の Sonnet モデルや Claude Haiku 4.5 から Claude Sonnet 5.5 に切り替える方法を説明します。エラーになる設定、推論の挙動の変化、移行元モデル別のチェックリストを掲載しています。

Claude Sonnet 5、Claude Sonnet 4.6、Claude Sonnet 4.5、Claude Sonnet 4、Claude 3.7 Sonnet、Claude Haiku 4.5 から Claude Sonnet 5.5 へ移行する場合に必要なコードの変更を示します。最初の 2 節を読み、その後、今使っているモデルの節まで順に進みます。[移行チェックリスト](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#migration-checklist)では、移行元ごとにすべての変更を確認できます。

このガイドは [Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) を使うコードの移行を扱います。[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) を使う場合に必要な変更はモデル名の更新です。

Claude Code にコードの移行を任せる

```text
/claude-api migrate this project to claude-sonnet-5-5
```

Claude Sonnet 5.5 の料金は、プロンプトキャッシュの読み取りを除き Claude Sonnet 5 と同じです。読み取りは 100 万トークンあたり 0.10 米ドル（USD）で、Claude Sonnet 5 の半額です。[料金](https://platform.claude.com/docs/en/about-claude/pricing)を参照してください。コンテキストウィンドウと出力上限は [Claude Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview) のモデルページ、機能とプロンプトの書き方は [Claude Sonnet 5.5 の新機能](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5#feature-support)と [Claude Sonnet 5.5 のプロンプトガイド](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5)にあります。

## Claude Sonnet 5.5 にリクエストを送る

次の例はそのまま Claude Sonnet 5.5 で動作します。effort の段階を指定し、400 エラーになる 5 つの設定を省いています。該当するのは[推論予算](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#sonnet-46-breaking-changes)、[サンプリングパラメーター](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#sonnet-46-breaking-changes)、[アシスタントの応答の事前入力](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#migrating-from-sonnet-45)、[強制ツール選択](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#forced-tool-use)、[`thinking: {"type": "disabled"}`](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#turn-off-up-front-thinking)です。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-5-5",
    "max_tokens": 4096,
    "messages": [{
      "role": "user",
      "content": "Analyze the trade-offs between microservices and monolithic architectures"
    }],
    "output_config": {
      "effort": "medium"
    }
  }'
```

```bash
ant messages create \
  --model claude-sonnet-5-5 \
  --max-tokens 4096 \
  --output-config '{effort: medium}' \
  --message '{role: user, content: "Analyze the trade-offs between microservices and monolithic architectures"}'
```

```python
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": "Analyze the trade-offs between microservices and monolithic architectures",
        }
    ],
    output_config={"effort": "medium"},
)

print(f"Stop reason: {response.stop_reason}")
for block in response.content:
    if block.type == "text":
        print(block.text)
```

```typescript
const client = new Anthropic();

const response = await client.messages.create({
  model: "claude-sonnet-5-5",
  max_tokens: 4096,
  messages: [
    {
      role: "user",
      content: "Analyze the trade-offs between microservices and monolithic architectures"
    }
  ],
  output_config: {
    effort: "medium"
  }
});

console.log(`Stop reason: ${response.stop_reason}`);
const textBlock = response.content.find((block) => block.type === "text");
console.log(textBlock?.text);
```

```csharp
AnthropicClient client = new();

var parameters = new MessageCreateParams
{
    Model = Model.ClaudeSonnet5_5,
    MaxTokens = 4096,
    Messages = [
        new UserMessageParam
        {
            Content = "Analyze the trade-offs between microservices and monolithic architectures"
        }
    ],
    OutputConfig = new OutputConfig
    {
        Effort = Effort.Medium
    }
};

var message = await client.Messages.Create(parameters);
Console.WriteLine($"Stop reason: {message.StopReason?.Raw()}");
foreach (var block in message.Content)
{
    if (block.TryPickText(out var textBlock))
    {
        Console.WriteLine(textBlock.Text);
    }
}
```

```go
client := anthropic.NewClient()

response, err := client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeSonnet5_5,
	MaxTokens: 4096,
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("Analyze the trade-offs between microservices and monolithic architectures")),
	},
	OutputConfig: anthropic.OutputConfigParam{
		Effort: anthropic.OutputConfigEffortMedium,
	},
})
if err != nil {
	log.Fatal(err)
}
fmt.Println("Stop reason:", response.StopReason)
for _, block := range response.Content {
	if textBlock, ok := block.AsAny().(anthropic.TextBlock); ok {
		fmt.Println(textBlock.Text)
	}
}
```

```java
import com.anthropic.models.messages.OutputConfig;

void main() {
    AnthropicClient client = AnthropicOkHttpClient.fromEnv();

    MessageCreateParams params = MessageCreateParams.builder()
        .model(Model.CLAUDE_SONNET_5_5)
        .maxTokens(4096L)
        .addUserMessage("Analyze the trade-offs between microservices and monolithic architectures")
        .outputConfig(OutputConfig.builder()
            .effort(OutputConfig.Effort.MEDIUM)
            .build())
        .build();

    Message response = client.messages().create(params);
    response.stopReason().ifPresent(reason -> IO.println("Stop reason: " + reason));
    response.content().stream()
        .flatMap(block -> block.text().stream())
        .forEach(textBlock -> IO.println(textBlock.text()));
}
```

```php
$client = new Client();

$message = $client->messages->create(
    maxTokens: 4096,
    messages: [
        ['role' => 'user', 'content' => 'Analyze the trade-offs between microservices and monolithic architectures']
    ],
    model: Model::CLAUDE_SONNET_5_5,
    outputConfig: ['effort' => 'medium'],
);

echo "Stop reason: {$message->stopReason}", PHP_EOL;
foreach ($message->content as $block) {
    if ($block instanceof \Anthropic\Messages\TextBlock) {
        echo $block->text, PHP_EOL;
    }
}
```

```ruby
client = Anthropic::Client.new

message = client.messages.create(
  model: Anthropic::Model::CLAUDE_SONNET_5_5,
  max_tokens: 4096,
  messages: [
    { role: "user", content: "Analyze the trade-offs between microservices and monolithic architectures" }
  ],
  output_config: {
    effort: "medium"
  }
)

puts "Stop reason: #{message.stop_reason}"
message.content.each do |block|
  puts block.text if block.is_a?(Anthropic::Models::TextBlock)
end
```

## 推論は既定で有効

Claude Sonnet 5.5 では、`thinking` フィールドを省略すると、`thinking: {"type": "adaptive"}` を指定した場合と同じく[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking)が有効になります。Claude Sonnet 4.6 以前と Claude Haiku 4.5 では、同じリクエストで推論は無効でした。最初の応答前の推論を省くには、[最初の応答前の推論を省く](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#turn-off-up-front-thinking)を参照してください。

| モデル | `thinking` フィールドを省略した場合 | 受理する `thinking.type` の値 | `display` の既定値 |
|---|---|---|---|
| Claude Sonnet 5.5 | 有効 | `"adaptive"`、`"between_tools"` | `"omitted"` |
| Claude Sonnet 5 | 有効 | `"adaptive"`、`"disabled"` | `"omitted"` |
| Claude Sonnet 4.6 | 無効 | `"adaptive"`、`"disabled"`、`"enabled"`（非推奨） | `"summarized"` |
| Claude Sonnet 4.5 と Claude Haiku 4.5 | 無効 | `"disabled"`、`"enabled"` | `"summarized"` |

### 応答の推論を処理する

推論を無効にしていたコードでは、次の 3 項目すべてに対応します。Claude Sonnet 5 を使っていたコードでは、最初の 2 項目に対応済みの場合が多いです。

- **`type` で内容ブロックを判別する。** 応答の冒頭に `thinking` ブロックが現れる場合があるため、`content[0].text` を読み取るコードは動作しなくなります。
- **ツール利用のループでは `thinking` ブロックをそのまま送り返す。** 空のブロックも含めます。[推論ブロックの保持](https://platform.claude.com/docs/en/build-with-claude/thinking#preserving-thinking-blocks)を参照してください。
- **`max_tokens` を見直す。** 推論とテキストの合計に適用され、推論トークンも出力トークンとして課金されます。[費用の調整](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#cost-control)を参照してください。

推論テキストは既定で省略されます。`thinking` ブロックには空の `thinking` フィールドと `signature` が含まれます。読める要約を取得するには `display: "summarized"` を設定します。これは Claude Sonnet 4.6 以前と Claude Haiku 4.5 の既定値です。[推論の表示を設定する](https://platform.claude.com/docs/en/build-with-claude/thinking#controlling-thinking-display)を参照してください。

### 最初の応答前の推論を省く

Claude Sonnet 5.5 で最初の応答前の推論を省くには `thinking: {"type": "between_tools"}` を送ります。推論を最小限にする設定です。ツール呼び出し間の進捗報告は、要約テキストを含む `thinking` ブロックで返ります。ツールを使わなければ、応答はテキストだけです。Claude Sonnet 5 では `thinking: {"type": "disabled"}` で推論を無効化し、それより前のモデルでは既定で無効です。Claude Sonnet 5.5 で `disabled` を送ると 400 の `invalid_request_error` が返ります。

```text
To turn thinking off on this model, send "thinking": {"type": "between_tools"} instead of {"type": "disabled"}. The model does not think before responding. The short updates it writes between tool calls come back as thinking blocks.
```

`between_tools` は Claude Sonnet 5.5 を提供するすべてのプラットフォームで使えます。effort の `low`、`medium`、`high` で受理され、`xhigh` と `max` では 400 エラーになります。これらの段階では、`thinking` フィールドを省略するか `thinking: {"type": "adaptive"}` を送って適応型推論を使います。`between_tools` にほかのフィールドは指定できません。`display`、`budget_tokens`、`block_binding` を一緒に送ると 400 エラーになります。[サーバー側のフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#server-side-fallback)で `between_tools` のリクエストが Claude Sonnet 5 に回ると、そのモデルは `thinking: {"type": "disabled"}` で実行します。

`between_tools` では会話の途中で effort を変更できません。適用中の段階と異なる値をメッセージ単位の `output_config.effort` に指定すると 400 エラーになります。ターンごとに effort を変えるには適応型推論を使います。プロンプトの書き方は[最初の応答前の推論を省いて実行する](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#running-without-up-front-thinking)を参照してください。

変更前（Claude Sonnet 5）。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-5",
    "max_tokens": 16000,
    "thinking": {"type": "disabled"},
    "output_config": {"effort": "xhigh"},
    "messages": [{"role": "user", "content": "..."}]
  }'
```

```bash
ant messages create \
  --model claude-sonnet-5 \
  --max-tokens 16000 \
  --thinking '{type: disabled}' \
  --output-config '{effort: xhigh}' \
  --message '{role: user, content: "..."}'
```

```python
client.messages.create(
    model="claude-sonnet-5",
    max_tokens=16000,
    thinking={"type": "disabled"},
    output_config={"effort": "xhigh"},
    messages=[{"role": "user", "content": "..."}],
)
```

```typescript
await client.messages.create({
  model: "claude-sonnet-5",
  max_tokens: 16000,
  thinking: { type: "disabled" },
  output_config: { effort: "xhigh" },
  messages: [{ role: "user", content: "..." }]
});
```

```csharp
await client.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeSonnet5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigDisabled(),
    OutputConfig = new() { Effort = Effort.Xhigh },
    Messages = [new UserMessageParam { Content = "..." }],
});
```

```go
client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeSonnet5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfDisabled: &anthropic.ThinkingConfigDisabledParam{},
	},
	OutputConfig: anthropic.OutputConfigParam{
		Effort: anthropic.OutputConfigEffortXhigh,
	},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("...")),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_SONNET_5)
    .maxTokens(16000L)
    .thinking(ThinkingConfigDisabled.builder().build())
    .outputConfig(OutputConfig.builder()
        .effort(OutputConfig.Effort.XHIGH)
        .build())
    .addUserMessage("...")
    .build();

client.messages().create(params);
```

```php
$client->messages->create(
    model: Model::CLAUDE_SONNET_5,
    maxTokens: 16000,
    thinking: ThinkingConfigDisabled::with(),
    outputConfig: OutputConfig::with(effort: Effort::XHIGH),
    messages: [['role' => 'user', 'content' => '...']],
);
```

```ruby
client.messages.create(
  model: Anthropic::Model::CLAUDE_SONNET_5,
  max_tokens: 16000,
  thinking: Anthropic::ThinkingConfigDisabled.new,
  output_config: { effort: Anthropic::OutputConfig::Effort::XHIGH },
  messages: [{ role: "user", content: "..." }]
)
```

変更後（Claude Sonnet 5.5）。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-5-5",
    "max_tokens": 16000,
    "thinking": {"type": "between_tools"},
    "output_config": {"effort": "high"},
    "messages": [{"role": "user", "content": "..."}]
  }'
```

```bash
ant messages create \
  --model claude-sonnet-5-5 \
  --max-tokens 16000 \
  --thinking '{type: between_tools}' \
  --output-config '{effort: high}' \
  --message '{role: user, content: "..."}'
```

```python
client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=16000,
    thinking={"type": "between_tools"},
    output_config={"effort": "high"},
    messages=[{"role": "user", "content": "..."}],
)
```

```typescript
await client.messages.create({
  model: "claude-sonnet-5-5",
  max_tokens: 16000,
  thinking: { type: "between_tools" },
  output_config: { effort: "high" },
  messages: [{ role: "user", content: "..." }]
});
```

```csharp
await client.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeSonnet5_5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigBetweenTools(),
    OutputConfig = new() { Effort = Effort.High },
    Messages = [new UserMessageParam { Content = "..." }],
});
```

```go
client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeSonnet5_5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfBetweenTools: &anthropic.ThinkingConfigBetweenToolsParam{},
	},
	OutputConfig: anthropic.OutputConfigParam{
		Effort: anthropic.OutputConfigEffortHigh,
	},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("...")),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_SONNET_5_5)
    .maxTokens(16000L)
    .thinking(ThinkingConfigBetweenTools.builder().build())
    .outputConfig(OutputConfig.builder()
        .effort(OutputConfig.Effort.HIGH)
        .build())
    .addUserMessage("...")
    .build();

client.messages().create(params);
```

```php
$client->messages->create(
    model: Model::CLAUDE_SONNET_5_5,
    maxTokens: 16000,
    thinking: ThinkingConfigBetweenTools::with(),
    outputConfig: OutputConfig::with(effort: Effort::HIGH),
    messages: [['role' => 'user', 'content' => '...']],
);
```

```ruby
client.messages.create(
  model: Anthropic::Model::CLAUDE_SONNET_5_5,
  max_tokens: 16000,
  thinking: Anthropic::ThinkingConfigBetweenTools.new,
  output_config: { effort: Anthropic::OutputConfig::Effort::HIGH },
  messages: [{ role: "user", content: "..." }]
)
```

## 移行元モデル別のチェックリスト

上から順に確認し、今使っているモデル名があるグループで止めます。Claude Haiku 4.5 では「Claude Sonnet 4 以前」を飛ばし、「Claude Haiku 4.5 のみ」まで適用します。

### すべての移行元モデル

- モデル ID を `claude-sonnet-5-5` に変更します。
- [内容ブロックを `type` で判別](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#thinking-in-responses)し、`thinking` ブロックをそのまま送り返します。
- 最初の応答前の推論を引き続き省くには、effort を `high` 以下にして[推論を最小限にする設定](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#turn-off-up-front-thinking)を送ります。
- [強制ツール利用](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#forced-tool-use)を `auto` と厳密なツール利用に置き換えます。
- 会話履歴は[追記だけ](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#thinking-blocks)で管理します。
- コンピューター操作を[ツールセット](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#computer-use-toolset)に移行し、ベータヘッダー `fine-grained-tool-streaming-2025-05-14` を取り除きます。Amazon Bedrock では `computer_20251124` も使えます。
- [アドバイザーツールには対応するモデルを組み合わせ](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#advisor-tool)、助言は暗号化されて返るものとして処理します。
- [ツール呼び出し間のテキスト](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#text-between-tool-calls)は `thinking` ブロックから読み取ります。
- [拒否を処理](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#safety-classifiers-and-fallback)し、フォールバックを設定します。
- [effort の段階を変えて改めて比較](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#recommended-changes)し、費用の基準を測り直します。

### Claude Sonnet 4.6 以前

- [`thinking` フィールドを省略したリクエストでの推論](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#thinking-on-by-default)を考慮し、`max_tokens` を見直します。
- [推論予算](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#sonnet-46-breaking-changes)を effort の段階に置き換えます。
- `temperature`、`top_p`、`top_k` を取り除きます。
- [推論テキストを表示する場合](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#thinking-in-responses)は `display: "summarized"` を指定します。
- [トークンを数え直し](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#other-changes-from-claude-sonnet-4-6)、画像トークンの予算を見直します。

### Claude Sonnet 4.5 以前

- [アシスタントの応答の事前入力](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#migrating-from-sonnet-45)をほかの方法に置き換えます。
- 標準の JSON パーサーでツール呼び出しの入力を解析します。
- `output_config.effort` を明示します。
- コンテキストウィンドウのベータヘッダーを取り除きます。
- `interleaved-thinking-2025-05-14` を取り除き、`fine-grained-tool-streaming-2025-05-14` を `eager_input_streaming` に置き換えます。
- `output_format` を `output_config.format` に移します。

### Claude Sonnet 4 以前

- [ツールのバージョン](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#migrating-from-claude-sonnet-4-or-earlier)を `text_editor_20250728` と `code_execution_20260521` に更新します。
- 停止理由 `refusal` と `model_context_window_exceeded` を処理します。
- ツールの文字列パラメーターの末尾の改行を確認します。
- `token-efficient-tools-2025-02-19` と `output-128k-2025-02-19` を取り除きます。
- プロンプトを見直します。

### Claude Haiku 4.5 のみ

- [`claude-haiku-4-5-20251001`](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#migrating-from-claude-haiku-4-5) またはそのエイリアスを置き換えます。
- トークン単価が上がるため、費用の基準を測り直します。
- Claude Haiku 4.5 では短すぎてキャッシュできなかったプロンプトを見直します。

## Claude Sonnet 5 から Claude Sonnet 5.5 への移行

この節の変更はすべての移行元モデルに当てはまります。モデル ID を、日付の接尾辞が付かない `claude-sonnet-5-5` に置き換えます。他のプラットフォームでは[提供状況](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5#availability)に掲載された ID を使います。

### 強制ツール利用は非対応

このガイドで扱う以前のモデルはすべて、種類が `any` または `tool` の `tool_choice` を受理します。Claude Sonnet 5.5 は[トークン数を数える](https://platform.claude.com/docs/en/build-with-claude/token-counting)エンドポイントを含め、どちらも 400 エラーで拒否します。

```text
tool_choice: type "tool" and "any" are not supported for this model.
```

`tool_choice: {"type": "auto"}` を送り、入力がスキーマに従うようにツールに `strict: true` を設定します。モデルはツールを呼び出さずに回答できるため、呼び出す条件はプロンプトに書きます。[厳密なツール利用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use)は JSON Schema の一部に対応し、すべてのオブジェクトに `additionalProperties: false` が必要です。[JSON Schema の制約](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#json-schema-limitations)を参照してください。

変更前（Claude Sonnet 5）。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-5",
    "max_tokens": 1024,
    "tools": [{
      "name": "get_weather",
      "description": "Get the current weather in a given location",
      "input_schema": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA"
          }
        },
        "required": ["location"],
        "additionalProperties": false
      }
    }],
    "tool_choice": {"type": "tool", "name": "get_weather"},
    "messages": [{"role": "user", "content": "What is the weather in Paris?"}]
  }'
```

```bash
ant messages create <<'YAML'
model: claude-sonnet-5
max_tokens: 1024
tools:
  - name: get_weather
    description: Get the current weather in a given location
    input_schema:
      type: object
      properties:
        location:
          type: string
          description: The city and state, e.g. San Francisco, CA
      required: [location]
      additionalProperties: false
tool_choice:
  type: tool
  name: get_weather
messages:
  - role: user
    content: What's the weather in Paris?
YAML
```

```python
client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "get_weather"},
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
)
```

```typescript
await client.messages.create({
  model: "claude-sonnet-5",
  max_tokens: 1024,
  tools,
  tool_choice: { type: "tool", name: "get_weather" },
  messages: [{ role: "user", content: "What's the weather in Paris?" }]
});
```

```csharp
await client.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeSonnet5,
    MaxTokens = 1024,
    Tools = [.. tools],
    ToolChoice = new ToolChoiceTool { Name = "get_weather" },
    Messages = [new UserMessageParam { Content = "What's the weather in Paris?" }],
});
```

```go
client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:      anthropic.ModelClaudeSonnet5,
	MaxTokens:  1024,
	Tools:      tools,
	ToolChoice: anthropic.ToolChoiceParamOfTool("get_weather"),
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("What's the weather in Paris?")),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_SONNET_5)
    .maxTokens(1024L)
    .tools(tools)
    .toolChoice(ToolChoiceTool.of("get_weather"))
    .addUserMessage("What's the weather in Paris?")
    .build();

client.messages().create(params);
```

```php
$client->messages->create(
    model: Model::CLAUDE_SONNET_5,
    maxTokens: 1024,
    tools: $tools,
    toolChoice: ToolChoiceTool::with(name: 'get_weather'),
    messages: [['role' => 'user', 'content' => "What's the weather in Paris?"]],
);
```

```ruby
client.messages.create(
  model: Anthropic::Model::CLAUDE_SONNET_5,
  max_tokens: 1024,
  tools: tools,
  tool_choice: Anthropic::ToolChoiceTool.new(name: "get_weather"),
  messages: [{ role: "user", content: "What's the weather in Paris?" }]
)
```

変更後（Claude Sonnet 5.5）。

```bash
# strict tool use: every call matches the tool's input_schema
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-5-5",
    "max_tokens": 1024,
    "tools": [{
      "name": "get_weather",
      "description": "Get the current weather in a given location",
      "input_schema": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA"
          }
        },
        "required": ["location"],
        "additionalProperties": false
      },
      "strict": true
    }],
    "tool_choice": {"type": "auto"},
    "messages": [{
      "role": "user",
      "content": "What is the weather in Paris? Use the get_weather tool."
    }]
  }'
```

```bash
ant messages create <<'YAML'
model: claude-sonnet-5-5
max_tokens: 1024
tools:
  - name: get_weather
    description: Get the current weather in a given location
    input_schema:
      type: object
      properties:
        location:
          type: string
          description: The city and state, e.g. San Francisco, CA
      required: [location]
      additionalProperties: false
    # strict tool use: every call matches the tool's input_schema
    strict: true
tool_choice:
  type: auto
messages:
  - role: user
    content: What's the weather in Paris? Use the get_weather tool.
YAML
```

```python
client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=1024,
    # strict tool use: every call matches the tool's input_schema
    tools=[{**tool, "strict": True} for tool in tools],
    tool_choice={"type": "auto"},
    messages=[
        {
            "role": "user",
            "content": "What's the weather in Paris? Use the get_weather tool.",
        }
    ],
)
```

```typescript
await client.messages.create({
  model: "claude-sonnet-5-5",
  max_tokens: 1024,
  // strict tool use: every call matches the tool's input_schema
  tools: tools.map((tool) => ({ ...tool, strict: true })),
  tool_choice: { type: "auto" },
  messages: [
    {
      role: "user",
      content: "What's the weather in Paris? Use the get_weather tool."
    }
  ]
});
```

```csharp
await client.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeSonnet5_5,
    MaxTokens = 1024,
    // strict tool use: every call matches the tool's input_schema
    Tools = [.. tools.Select(tool => tool with { Strict = true })],
    ToolChoice = new ToolChoiceAuto(),
    Messages =
    [
        new UserMessageParam
        {
            Content = "What's the weather in Paris? Use the get_weather tool.",
        },
    ],
});
```

```go
// strict tool use: every call matches the tool's input_schema
var strictTools []anthropic.ToolUnionParam
for _, tool := range tools {
	strictTool := *tool.OfTool
	strictTool.Strict = anthropic.Bool(true)
	strictTools = append(strictTools, anthropic.ToolUnionParam{OfTool: &strictTool})
}
client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:      anthropic.ModelClaudeSonnet5_5,
	MaxTokens:  1024,
	Tools:      strictTools,
	ToolChoice: anthropic.ToolChoiceUnionParam{OfAuto: &anthropic.ToolChoiceAutoParam{}},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(
			anthropic.NewTextBlock("What's the weather in Paris? Use the get_weather tool."),
		),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_SONNET_5_5)
    .maxTokens(1024L)
    // strict tool use: every call matches the tool's input_schema
    .tools(tools.stream()
        .map(tool -> tool.tool()
            .map(customTool -> customTool.toBuilder()
                .strict(true)
                .build())
            .map(ToolUnion::ofTool)
            .orElse(tool))
        .toList())
    .toolChoice(ToolChoiceAuto.builder().build())
    .addUserMessage("What's the weather in Paris? Use the get_weather tool.")
    .build();

client.messages().create(params);
```

```php
$client->messages->create(
    model: Model::CLAUDE_SONNET_5_5,
    maxTokens: 1024,
    // strict tool use: every call matches the tool's input_schema
    tools: array_map(fn (Tool $tool) => $tool->withStrict(true), $tools),
    toolChoice: ToolChoiceAuto::with(),
    messages: [
        [
            'role' => 'user',
            'content' => "What's the weather in Paris? Use the get_weather tool.",
        ],
    ],
);
```

```ruby
client.messages.create(
  model: Anthropic::Model::CLAUDE_SONNET_5_5,
  max_tokens: 1024,
  # strict tool use: every call matches the tool's input_schema
  tools: tools.map { |tool| tool.merge(strict: true) },
  tool_choice: Anthropic::ToolChoiceAuto.new,
  messages: [
    { role: "user", content: "What's the weather in Paris? Use the get_weather tool." }
  ]
)
```

例では一覧にあるすべてのツールを厳密モードにしています。1 リクエストで指定できる厳密なツールは最大 20 個です。MCP、コンピューター操作、ブラウザー操作のツールセット項目は `strict` を受理しません。ツールが多い場合は、必要な項目だけに指定します。

### 推論ブロックはモデルと会話にひも付く

Claude Sonnet 5.5 は Claude Sonnet 5、Claude Opus 4.8、Claude Haiku 4.5、および[以前のモデル](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#earlier-models)の推論ブロックを読み取れます。Claude API と Claude Models on Google Cloud (Google managed) では、Claude Haiku 5.5 の推論ブロックも読み取れます。Claude Opus 5、Claude Opus 5.5、Claude Fable、Claude Mythos の推論ブロックは読み取れません。

API はモデルが読み取れないブロックを取り除きます。リクエストには 200 が返り、取り除いたブロックは課金されません。[モデルを切り替えて元に戻す](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#switching-models)を参照してください。

推論ブロックが[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)を通過するよう、会話履歴は追記だけで管理します。指示やツールの変更については[会話途中のシステムメッセージとツールの変更](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)を参照してください。

[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)に失敗したとき、[400 エラー](https://platform.claude.com/docs/en/api/errors#thinking-block-conversation-mismatch)になるかどうかは条件によります。両方の場合の見分け方と対処は[推論ブロックの先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks)を参照してください。

先頭部分の照合は Claude API と[一部のクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#feature-availability)で実行されます。

Claude Sonnet 5.5 の推論ブロックは、生成元のアカウントまたはそれにリンクしたアカウントで使えます。[推論の保持](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#account-bound-thinking)を参照してください。

### コンピューター操作ツールの対応バージョン

Claude Sonnet 5.5 は `computer_toolset_20260801` ツールセットでコンピューター操作に対応します。Amazon Bedrock では、ベータヘッダー `computer-use-2025-11-24` を付けた `computer_20251124` も受理します。Claude API での `computer_20251124` など、対応外のバージョンを指定すると 400 エラーになります。`computer_20250124` はすべてのプラットフォームで拒否されます。

ツールセットを使っている連携は変更不要です。ツールセットに移行する場合は、`computer_20251124` または `computer_20250124` を `computer_toolset_20260801` に置き換え、そのバージョンのベータヘッダーを取り除きます。リクエストとエージェントの処理ループの変更点は[`computer_20251124` から移行する](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool#migrate-from-computer-20251124)を参照してください。

ベータヘッダー `fine-grained-tool-streaming-2025-05-14` を送っている場合は、ツールセットへの移行時に取り除きます。ツールセット項目と一緒に送ると 400 エラーになります。必要なツールごとに `eager_input_streaming: true` を設定します。

### アドバイザーツールで使えるモデルが変わる

[アドバイザーツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)で Claude Sonnet 5.5 を実行側にした場合、アドバイザーに指定できるのは Claude Opus 5、Claude Opus 5.5、Claude Sonnet 5.5、Claude Fable 5、Claude Fable 5.1、Claude Fable 5.2、Claude Mythos 5、Claude Mythos 5.1、Claude Mythos 5.2 です。Claude Opus 4.8、Claude Opus 4.7、Claude Opus 4.6、Claude Sonnet 5、Claude Sonnet 4.6、Claude Haiku 5.5 をアドバイザーにすると 400 エラーになります。助言は暗号化された `advisor_redacted_result` ブロックで返るため、応答からテキストを読み取れません。[モデルの互換性](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#model-compatibility)を参照してください。

### ツール呼び出し間のテキストは推論ブロックで返る

Claude Sonnet 5.5 では、モデルがツール呼び出し間に書く 1〜2 文より長い報告が、[進捗報告の `thinking` ブロック](https://platform.claude.com/docs/en/build-with-claude/thinking#progress-updates)として返ります。既定の `display` ではテキストは空です。短いコメントは `text` のまま返ります。Claude Sonnet 5 以前では、ツール呼び出し間のテキストはすべて `text` ブロックで返ります。リクエストは成功しますが、これらの報告を表示していた画面では、長い報告が表示されなくなります。

適応型推論では、`display` に `"updates"`（ベータ版、ヘッダー `thinking-display-updates-2026-08-18`）を設定すると進捗報告だけが返り、`"summarized"` を設定すると推論の要約と混在して返ります。空でない各 `thinking` ブロックは、直後の `tool_use` ブロックの前に表示します。[`between_tools`](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#turn-off-up-front-thinking) では `display` を指定せずにテキストを受け取れます。[利用者向けの進捗報告](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#user-facing-progress-updates)を参照してください。

### 安全性分類器とフォールバック

Claude Sonnet 5.5 は Claude Sonnet 5 より多くの分類でリクエストを拒否します。拒否時は `stop_reason: "refusal"` が返り、`stop_details` には次の[分類](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#refusal-response)のいずれかが含まれる場合があります。

- **`"cyber"`**。マルウェアや脆弱性を悪用するコードの開発など、サイバー分野の被害につながり得るリクエストです。
- **`"bio"`**。危険な実験手法など、生物分野の被害につながり得るリクエストです。
- **`"frontier_llm"`**。競合する AI モデルの開発に役立ち得るリクエストです。
- **`"reasoning_extraction"`**。モデルの内部推論を応答テキストに再現するよう求めるリクエストです。
- **`"general_harms"`**。その他の利用ポリシーの分野に該当するリクエストです。無害な作業でもこの分類になることがあります。

ベータ版の[サーバー側のフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#server-side-fallback)（`fallbacks: "default"`）は、Claude API と [Claude Models on Google Cloud (Anthropic managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/anthropic-managed) で利用でき、 `"cyber"` と `"frontier_llm"` の拒否を Claude Sonnet 5 で再試行します。`"bio"`、`"reasoning_extraction"`、`"general_harms"` の拒否は再試行しません。[拒否とフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)と[拒否時の課金](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#how-refusals-are-billed)を参照してください。

Claude Sonnet 4.6、Claude Sonnet 4.5、Claude Haiku 4.5 から移行するコードでは、リアルタイムのサイバー対策が新たに適用されます。正当なセキュリティ業務の場合は [Cyber Verification Program](https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude-opus-and-sonnet) に申請します。

### その他の変更

- **プロンプトキャッシュ**。キャッシュできるプロンプトの最小長は 512 トークンです。Claude Sonnet 5、Claude Sonnet 4.6、Claude Sonnet 4.5 では 1,024 トークンでした。[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#cache-limitations)を参照してください。
- **新機能**。会話途中のシステムメッセージ、会話途中のツール変更、メッセージ単位の effort については [Claude Sonnet 5.5 の新機能](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5#feature-support)を参照してください。[`between_tools`](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#turn-off-up-front-thinking) を使う場合、会話の途中で effort は変更できません。

### 推奨する変更

effort の段階を変えて改めて比較します。Claude Sonnet 5.5 の段階は `low`、`medium`、`high`、`xhigh`、`max` の 5 つです。Claude API の既定値は `high` です。段階ごとの調整が変わったため、同じ段階でも推論量は Claude Sonnet 5 と異なります。エージェント型の処理や応答時間を重視する処理を除き、`high` から始めます。エージェント型のコーディングや複数段階のツール利用では、要件が明確なタスクは `medium` から始め、難しいタスクや長いタスクは `high` に上げます。チャットなど応答時間を重視する処理では `medium` または `low` から始めます。段階は `output_config.effort` で指定します。[Claude Sonnet 5.5 の推奨 effort](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-sonnet-5-5)を参照し、モデル固有のプロンプト指示を [Claude Sonnet 5.5 のプロンプトガイド](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5)と照らして見直します。

## Claude Sonnet 4.6 以前から Claude Sonnet 5.5 への移行

置き換え元を `claude-sonnet-4-6` として、まず前の節をすべて適用し、次に以下を反映します。Claude Sonnet 4.5 以前を使う場合は、該当する後続の節にも進みます。

### 互換性を損なう変更

**設定を省略したリクエストで推論が有効になる。** [推論は既定で有効](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#thinking-on-by-default)と[最初の応答前の推論を省く](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#turn-off-up-front-thinking)を参照してください。

**推論予算を送るとエラーになる。** Claude Sonnet 4.6 は `thinking: {"type": "enabled", "budget_tokens": N}` を非推奨の設定として受理します。Claude Sonnet 4.5 と Claude Haiku 4.5 は、推論を有効にする際にこの設定を使います。Claude Sonnet 5.5 では 400 エラーになります。

```text
"thinking.type.enabled" is not supported for this model. Use "thinking.type.adaptive" and "output_config.effort" to control thinking behavior.
```

予算を取り除き、[effort](https://platform.claude.com/docs/en/build-with-claude/effort) の段階を指定します。予算から段階への固定の対応はないため、2〜3 段階で評価を実行します。

変更前（Claude Sonnet 4.6）。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 16000,
    "thinking": {
      "type": "enabled",
      "budget_tokens": 10000
    },
    "messages": [
      {
        "role": "user",
        "content": "..."
      }
    ]
  }'
```

```bash
ant messages create <<'YAML'
model: claude-sonnet-4-6
max_tokens: 16000
thinking:
  type: enabled
  budget_tokens: 10000
messages:
  - role: user
    content: "..."
YAML
```

```python
client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": "..."}],
)
```

```typescript
await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 16000,
  thinking: { type: "enabled", budget_tokens: 10000 },
  messages: [{ role: "user", content: "..." }]
});
```

```csharp
using Anthropic;
using Anthropic.Models.Messages;

AnthropicClient client = new();

var parameters = new MessageCreateParams
{
    Model = Model.ClaudeSonnet4_6,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigEnabled(budgetTokens: 10000),
    Messages = [new UserMessageParam { Content = "..." }]
};

var response = await client.Messages.Create(parameters);
Console.WriteLine(response);
```

```go
client := anthropic.NewClient()

response, err := client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeSonnet4_6,
	MaxTokens: 16000,
	Thinking:  anthropic.ThinkingConfigParamOfEnabled(10000),
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("...")),
	},
})
if err != nil {
	log.Fatal(err)
}
fmt.Println(response)
```

```java
AnthropicClient client = AnthropicOkHttpClient.fromEnv();

MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_SONNET_4_6)
    .maxTokens(16000L)
    .enabledThinking(10000L)
    .addUserMessage("...")
    .build();

Message response = client.messages().create(params);
IO.println(response);
```

```php
$client = new Client();

$message = $client->messages->create(
    maxTokens: 16000,
    messages: [['role' => 'user', 'content' => '...']],
    model: Model::CLAUDE_SONNET_4_6,
    thinking: ['type' => 'enabled', 'budgetTokens' => 10000],
);
```

```ruby
client = Anthropic::Client.new

message = client.messages.create(
  model: Anthropic::Model::CLAUDE_SONNET_4_6,
  max_tokens: 16000,
  thinking: {
    type: "enabled",
    budget_tokens: 10000
  },
  messages: [
    { role: "user", content: "..." }
  ]
)
```

変更後（Claude Sonnet 5.5）。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-5-5",
    "max_tokens": 16000,
    "thinking": {
      "type": "adaptive"
    },
    "output_config": {
      "effort": "high"
    },
    "messages": [
      {
        "role": "user",
        "content": "..."
      }
    ]
  }'
```

```bash
ant messages create <<'YAML'
model: claude-sonnet-5-5
max_tokens: 16000
thinking:
  type: adaptive
output_config:
  effort: high
messages:
  - role: user
    content: "..."
YAML
```

```python
client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},  # or "max", "xhigh", "medium", "low"
    messages=[{"role": "user", "content": "..."}],
)
```

```typescript
await client.messages.create({
  model: "claude-sonnet-5-5",
  max_tokens: 16000,
  thinking: { type: "adaptive" },
  output_config: { effort: "high" }, // or "max", "xhigh", "medium", "low"
  messages: [{ role: "user", content: "..." }]
});
```

```csharp
using Anthropic;
using Anthropic.Models.Messages;

AnthropicClient client = new();

var parameters = new MessageCreateParams
{
    Model = Model.ClaudeSonnet5_5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigAdaptive(),
    OutputConfig = new OutputConfig { Effort = Effort.High }, // or Max, Xhigh, Medium, Low
    Messages = [new UserMessageParam { Content = "..." }]
};

var response = await client.Messages.Create(parameters);
Console.WriteLine(response);
```

```go
client := anthropic.NewClient()

response, err := client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeSonnet5_5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{},
	},
	OutputConfig: anthropic.OutputConfigParam{
		Effort: anthropic.OutputConfigEffortHigh, // or Max, Xhigh, Medium, Low
	},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("...")),
	},
})
if err != nil {
	log.Fatal(err)
}
fmt.Println(response)
```

```java
AnthropicClient client = AnthropicOkHttpClient.fromEnv();

MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_SONNET_5_5)
    .maxTokens(16000L)
    .thinking(ThinkingConfigAdaptive.builder().build())
    .outputConfig(OutputConfig.builder()
        .effort(OutputConfig.Effort.HIGH) // or MAX, XHIGH, MEDIUM, LOW
        .build())
    .addUserMessage("...")
    .build();

Message response = client.messages().create(params);
IO.println(response);
```

```php
$client = new Client();

$message = $client->messages->create(
    maxTokens: 16000,
    messages: [['role' => 'user', 'content' => '...']],
    model: Model::CLAUDE_SONNET_5_5,
    thinking: ['type' => 'adaptive'],
    outputConfig: ['effort' => 'high'], // or 'max', 'xhigh', 'medium', 'low'
);
```

```ruby
client = Anthropic::Client.new

message = client.messages.create(
  model: Anthropic::Model::CLAUDE_SONNET_5_5,
  max_tokens: 16000,
  thinking: {
    type: "adaptive"
  },
  output_config: {
    effort: "high" # or "max", "xhigh", "medium", "low"
  },
  messages: [
    { role: "user", content: "..." }
  ]
)
```

**サンプリングパラメーターを送るとエラーになる。** `temperature`、`top_p`、`top_k` を取り除きます。

**推論テキストは既定で省略される。** [応答の推論を処理する](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#thinking-in-responses)を参照してください。

### その他の変更

- **トークン数が約 30% 増える**。Claude Sonnet 5.5 は Claude Sonnet 5 のトークナイザーを使います。Claude Sonnet 4.6、Claude Sonnet 4.5、Claude Haiku 4.5 と比べて、同じテキストでも内容によってトークン数が約 30% 増えます。[トークン数を数える](https://platform.claude.com/docs/en/build-with-claude/token-counting)機能で再計測し、`max_tokens` と費用を見直します。
- **effort**。Claude Sonnet 5.5 は `xhigh` に対応し、段階ごとの調整も変わっています。[推奨する変更](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#recommended-changes)を参照してください。
- **画像**。Claude Sonnet 5.5 は高解像度の画像を使い、長辺は最大 2,576 ピクセル、画像 1 枚あたり最大 4,784 ビジュアルトークンです。Claude Sonnet 4.6、Claude Sonnet 4.5、Claude Haiku 4.5 の上限は 1,568 ピクセル、1,568 トークンです。2,000×1,500 ピクセルの画像は Claude Sonnet 5.5 で約 2.5 倍のトークンを使います。[解像度とトークンの消費量](https://platform.claude.com/docs/en/build-with-claude/vision#evaluate-image-size)を参照してください。

### Claude Sonnet 4.5 以前からの移行

Claude Sonnet 4.5、Claude Sonnet 4、Claude 3.7 Sonnet では、先に前の節をすべて適用し、次に以下を反映します。

**応答の事前入力はエラーになる。** Claude Sonnet 5.5 は Claude Sonnet 4.6 や Claude Sonnet 5 と同じく、事前入力したアシスタントターンが最後にあると 400 エラーで拒否します。Claude Sonnet 4.5、Claude Haiku 4.5、それ以前のモデルは受理します。エラーメッセージを以下に示します。

```text
This model does not support assistant message prefill. The conversation must end with a user message.
```

事前入力を使っていた目的に応じて置き換えます。

- **出力形式**。[構造化出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)や、分類用の列挙型フィールドを持つツールを使います。
- **前置き**。システムプロンプトで直接回答するよう指示します。
- **意図しない拒否**。通常はユーザーメッセージの指示を明確にすれば足ります。
- **続きを生成する**。指示をユーザーメッセージに移します。たとえば「前の応答は `[previous_response]` で途切れました。中断した箇所から続けてください」と書きます。
- **文脈を伝える補足**。ユーザーターンに書きます。

**ツール入力のエスケープ。** ツール呼び出しの引数でエスケープの表記が異なる場合があります。`input` は標準の JSON パーサーで解析します。

**コンピューター操作。** Claude Sonnet 5.5 は `computer_20250124` を受理しません。[コンピューター操作ツールの対応バージョン](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#computer-use-toolset)を参照してください。

**effort。** Claude Sonnet 4.5 には effort パラメーターがありません。段階を明示して設定します（[推奨する変更](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#recommended-changes)を参照）。

**コンテキストと出力。** Claude Sonnet 5.5 はコンテキストウィンドウが広く、出力上限も高くなります。[Claude Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview) のモデルページを参照してください。コンテキストウィンドウのベータヘッダーは取り除きます。

**ベータヘッダー。** 適応型推論はツール呼び出し間に自動で推論するため、`interleaved-thinking-2025-05-14` を取り除きます。`fine-grained-tool-streaming-2025-05-14` は、必要なツールごとの `eager_input_streaming: true` に置き換えます。このヘッダーをコンピューター操作またはブラウザー操作のツールセット項目と一緒に送ると 400 エラーになります。[細かな単位でのツール入力のストリーミング](https://platform.claude.com/docs/en/agents-and-tools/tool-use/fine-grained-tool-streaming)を参照してください。

**構造化出力。** `output_format` パラメーターは非推奨です。引き続き使うにはベータヘッダー `structured-outputs-2025-11-13` を追加します。ヘッダーなしでは API が 400 エラーを返します。`output_config.format` に切り替えます。

### Claude Sonnet 4 以前からの移行

Claude Sonnet 4 は Claude API で提供を終了していますが、Claude Models on Google Cloud (Google managed) と Amazon Bedrock で利用できます。Claude 3.7 Sonnet は提供を終了しています。どちらから移行する場合も、先に前の節をすべて適用してから次の変更を反映します。

- **ツールのバージョン**。`text_editor_20250728` をツール名 `str_replace_based_edit_tool` で使い、`undo_edit` コマンドは使いません。`code_execution_20260521` を使います。[テキストエディターツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool)と[コード実行ツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool#upgrade-to-latest-tool-version)を参照してください。
- **停止理由**。`refusal` を処理します。Claude 4.5 以降は、コンテキストウィンドウの上限に達すると `model_context_window_exceeded` で停止します。[停止理由とフォールバック](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)を参照してください。
- **末尾の改行**。Claude 4.5 以降は、ツール呼び出しの文字列パラメーターの末尾の改行を保持します。
- **ベータヘッダー**。`token-efficient-tools-2025-02-19` と `output-128k-2025-02-19` を取り除きます。
- **プロンプト**。[プロンプトのベストプラクティス](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)と照らして見直します。

## Claude Haiku 4.5 から Claude Sonnet 5.5 への移行

まず [Claude Sonnet 4.5 以前からの移行](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#migrating-from-sonnet-45)までのすべての節を適用します。Claude Sonnet 4 の小節は飛ばします。次に以下を反映します。

- **モデル ID**。`claude-haiku-4-5-20251001` またはエイリアス `claude-haiku-4-5` を `claude-sonnet-5-5` に置き換えます。
- **費用**。トークン単価が上がり、同じテキストでもトークン数が増えます。トークンを再計測し、費用の基準を測り直します。[料金](https://platform.claude.com/docs/en/about-claude/pricing)を参照してください。
- **プロンプトキャッシュ**。キャッシュできるプロンプトの最小長が 4,096 トークンから [Claude Sonnet 5.5 の下限](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#other-changes-from-claude-sonnet-5)に下がります。
- **ツール呼び出し間の推論**。適応型推論では、ツール呼び出し間で自動的に推論します。
- **ルーティング**。Claude Sonnet 5.5 は Claude Haiku 4.5 の推論ブロックを読み取ります。Claude Sonnet 5.5 に切り替えた会話では以前の推論が保持されます。Claude Haiku 4.5 に戻る会話では、Claude Sonnet 5.5 のブロックが取り除かれます。
