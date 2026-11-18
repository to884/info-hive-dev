---
url: "https://platform.claude.com/docs/en/build-with-claude/effort-per-message"
title: "Per-message effort"
fetched_at: "2026-11-18T21:21:28+09:00"
source_sha256: "ada9c615f994cd7e7658f6a883cc4addf25da76facf6448f6a5edd67bd86f7d6"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# メッセージ単位の effort

システムメッセージを使うと、プロンプトキャッシュを維持したまま、会話の途中で effort の段階を変更できます。

メッセージ単位の変更では、リクエストのトップレベルの値を保ったまま、会話の後続のターンに新しい effort を設定できます。キャッシュ済みの先頭部分は変更後も一致します。

## effort の段階を変える

会話の途中で段階を変える手順は次のとおりです。

1. `messages` に `role: "system"` のメッセージを追加します。`content` は空にし、`output_config.effort` に新しい [effort](https://platform.claude.com/docs/en/build-with-claude/effort) の段階を指定します。
2. [ベータヘッダー](https://platform.claude.com/docs/en/api/beta-headers)として `mid-conversation-output-config-2026-07-01` を送信します。
3. トップレベルの値を維持します。

次の例ではトップレベルの値を `high` に保ち、定型的な追加の依頼には `low` を使います。

```bash
# Effort-only system message: the new level takes effect from the next user turn.
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "anthropic-beta: mid-conversation-output-config-2026-07-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-5-5",
    "max_tokens": 4096,
    "output_config": {"effort": "high"},
    "messages": [
      {"role": "user", "content": "Plan a migration from SQLite to PostgreSQL in three short steps."},
      {"role": "assistant", "content": "1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts."},
      {"role": "system", "content": [], "output_config": {"effort": "low"}},
      {"role": "user", "content": "Summarize the plan in one sentence."}
    ]
  }'
```

```bash
ant beta:messages create \
  --beta mid-conversation-output-config-2026-07-01 <<'YAML'
model: claude-opus-5-5
max_tokens: 4096
output_config:
  effort: high
messages:
  - role: user
    content: Plan a migration from SQLite to PostgreSQL in three short steps.
  - role: assistant
    content: "1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts."
  # Effort-only system message: the new level takes effect from the next user turn.
  - role: system
    content: []
    output_config:
      effort: low
  - role: user
    content: Summarize the plan in one sentence.
YAML
```

```python
client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-opus-5-5",
    max_tokens=4096,
    output_config={"effort": "high"},
    messages=[
        {
            "role": "user",
            "content": "Plan a migration from SQLite to PostgreSQL in three short steps.",
        },
        {
            "role": "assistant",
            "content": "1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts.",
        },
        # Effort-only system message: the new level takes effect from the next user turn.
        {"role": "system", "content": [], "output_config": {"effort": "low"}},
        {"role": "user", "content": "Summarize the plan in one sentence."},
    ],
    betas=["mid-conversation-output-config-2026-07-01"],
)

for block in response.content:
    if block.type == "text":
        print(block.text)
```

```typescript
const client = new Anthropic();

const response = await client.beta.messages.create({
  model: "claude-opus-5-5",
  max_tokens: 4096,
  output_config: { effort: "high" },
  messages: [
    {
      role: "user",
      content: "Plan a migration from SQLite to PostgreSQL in three short steps."
    },
    {
      role: "assistant",
      content:
        "1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts."
    },
    // Effort-only system message: the new level takes effect from the next user turn.
    { role: "system", content: [], output_config: { effort: "low" } },
    { role: "user", content: "Summarize the plan in one sentence." }
  ],
  betas: ["mid-conversation-output-config-2026-07-01"]
});

for (const block of response.content) {
  if (block.type === "text") {
    console.log(block.text);
  }
}
```

```csharp
using Anthropic.Models.Beta;
using Anthropic.Models.Beta.Messages;
// ...

AnthropicClient client = new();

var response = await client.Beta.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 4096,
    OutputConfig = new() { Effort = Effort.High },
    Messages =
    [
        new BetaUserMessageParam { Content = "Plan a migration from SQLite to PostgreSQL in three short steps." },
        new BetaAssistantMessageParam { Content = "1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts." },
        // Effort-only system message: the new level takes effect from the next user turn.
        new BetaSystemMessageParam
        {
            Content = new([]),
            OutputConfig = new() { Effort = BetaSystemMessageOutputConfigEffort.Low },
        },
        new BetaUserMessageParam { Content = "Summarize the plan in one sentence." },
    ],
    Betas = [AnthropicBeta.MidConversationOutputConfig2026_07_01],
});

foreach (var block in response.Content)
{
    if (block.TryPickText(out var textBlock))
    {
        Console.WriteLine(textBlock.Text);
    }
}
```

```go
client := anthropic.NewClient()

response, err := client.Beta.Messages.New(context.Background(), anthropic.BetaMessageNewParams{
	Model:     anthropic.ModelClaudeOpus5_5,
	MaxTokens: 4096,
	OutputConfig: anthropic.BetaOutputConfigParam{
		Effort: anthropic.BetaOutputConfigEffortHigh,
	},
	Messages: []anthropic.BetaMessageParam{
		anthropic.NewBetaUserMessage(anthropic.NewBetaTextBlock("Plan a migration from SQLite to PostgreSQL in three short steps.")),
		{OfAssistant: &anthropic.BetaAssistantMessageParam{
			Content: []anthropic.BetaContentBlockParamUnion{anthropic.NewBetaTextBlock("1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts.")},
		}},
		// Effort-only system message: the new level takes effect from the next user turn.
		anthropic.NewBetaSystemMessage(anthropic.BetaSystemMessageOutputConfigParam{
			Effort: anthropic.BetaSystemMessageOutputConfigEffortLow,
		}),
		anthropic.NewBetaUserMessage(anthropic.NewBetaTextBlock("Summarize the plan in one sentence.")),
	},
	Betas: []anthropic.AnthropicBeta{anthropic.AnthropicBetaMidConversationOutputConfig2026_07_01},
})
if err != nil {
	log.Fatal(err)
}

for _, block := range response.Content {
	if textBlock, ok := block.AsAny().(anthropic.BetaTextBlock); ok {
		fmt.Println(textBlock.Text)
	}
}
```

```java
import com.anthropic.models.beta.AnthropicBeta;
import com.anthropic.models.beta.messages.BetaMessage;
import com.anthropic.models.beta.messages.BetaOutputConfig;
import com.anthropic.models.beta.messages.BetaSystemMessageOutputConfig;
import com.anthropic.models.beta.messages.BetaSystemMessageParam;
import com.anthropic.models.beta.messages.MessageCreateParams;
// ...

void main() {
    AnthropicClient client = AnthropicOkHttpClient.fromEnv();

    MessageCreateParams params = MessageCreateParams.builder()
        .model(Model.CLAUDE_OPUS_5_5)
        .maxTokens(4096L)
        .addBeta(AnthropicBeta.MID_CONVERSATION_OUTPUT_CONFIG_2026_07_01)
        .outputConfig(BetaOutputConfig.builder()
            .effort(BetaOutputConfig.Effort.HIGH)
            .build())
        .addUserMessage("Plan a migration from SQLite to PostgreSQL in three short steps.")
        .addAssistantMessage("1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts.")
        // Effort-only system message: the new level takes effect from the next user turn.
        .addMessage(BetaSystemMessageParam.builder()
            .contentOfBlocks(List.of())
            .outputConfig(BetaSystemMessageOutputConfig.builder()
                .effort(BetaSystemMessageOutputConfig.Effort.LOW)
                .build())
            .build())
        .addUserMessage("Summarize the plan in one sentence.")
        .build();

    BetaMessage response = client.beta().messages().create(params);
    response.content().stream()
        .flatMap(block -> block.text().stream())
        .forEach(textBlock -> IO.println(textBlock.text()));
}
```

```php
use Anthropic\Beta\AnthropicBeta;
use Anthropic\Beta\Messages\BetaMessageParam;
use Anthropic\Beta\Messages\BetaOutputConfig;
use Anthropic\Beta\Messages\BetaSystemMessageOutputConfig;
use Anthropic\Beta\Messages\BetaTextBlock;
// ...

$client = new Client();

$response = $client->beta->messages->create(
    model: Model::CLAUDE_OPUS_5_5,
    maxTokens: 4096,
    outputConfig: BetaOutputConfig::with(effort: 'high'),
    messages: [
        BetaMessageParam::with(role: 'user', content: 'Plan a migration from SQLite to PostgreSQL in three short steps.'),
        BetaMessageParam::with(role: 'assistant', content: '1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts.'),
        // Effort-only system message: the new level takes effect from the next user turn.
        BetaMessageParam::with(
            role: 'system',
            content: [],
            outputConfig: BetaSystemMessageOutputConfig::with(effort: 'low'),
        ),
        BetaMessageParam::with(role: 'user', content: 'Summarize the plan in one sentence.'),
    ],
    betas: [AnthropicBeta::MID_CONVERSATION_OUTPUT_CONFIG_2026_07_01],
);

foreach ($response->content as $block) {
    if ($block instanceof BetaTextBlock) {
        echo $block->text, PHP_EOL;
    }
}
```

```ruby
client = Anthropic::Client.new

response = client.beta.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 4096,
  output_config: { effort: :high },
  messages: [
    { role: "user", content: "Plan a migration from SQLite to PostgreSQL in three short steps." },
    { role: "assistant", content: "1. Export the SQLite data. 2. Create the PostgreSQL schema. 3. Import the data and verify row counts." },
    # Effort-only system message: the new level takes effect from the next user turn.
    { role: "system", content: [], output_config: { effort: :low } },
    { role: "user", content: "Summarize the plan in one sentence." }
  ],
  betas: [Anthropic::AnthropicBeta::MID_CONVERSATION_OUTPUT_CONFIG_2026_07_01]
)

response.content.each do |block|
  case block
  when Anthropic::Beta::BetaTextBlock
    puts block.text
  end
end
```

新しい段階の適用が始まる時点は、メッセージを置く位置で決まります。

- 新しい入力を含む `user` ターンの直後に置くと、そのターンに対する Claude の回答に新しい段階が適用されます。
- それ以外の位置に置くと、新しい入力を含む次の `user` ターンから適用されます。前の例では、`assistant` ターンと次の `user` ターンの間に置いています。

`tool_result` ブロックだけを含む `user` ターンは、新しい入力に数えません。

新しい段階は、後続のメッセージで設定を変えるまで有効です。

すでに送信した内容の末尾にメッセージを追加し、後続のリクエストでも同じ位置に置きます。送信済みのターンより前への挿入や、後からの移動・削除は避けてください。[推論の保持（preserved thinking）](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)に対応するモデルでは、いずれの操作も、そのメッセージより後の `assistant` ターンの推論ブロックを無効にします。その後の挙動は、[Set `prefix_mismatch_behavior`（不一致時の挙動の設定）](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#mismatch-behavior)を参照してください。

内容のある `system` メッセージと隣り合う場合は、両方のメッセージが[会話途中のシステムメッセージの配置規則](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#limitations)に従う必要があります。

Amazon Bedrock の InvokeModel API では、リクエスト本体の `anthropic_beta` 配列でベータの値を送信します。対応モデルは、[Bedrock の会話途中のシステムメッセージ（Mid-conversation system messages on Bedrock）](https://platform.claude.com/docs/en/build-with-claude/claude-on-amazon-bedrock-legacy#mid-conversation-system-messages-on-bedrock)を参照してください。

## エラーの条件

- ベータヘッダーを省略してメッセージ単位の `output_config` を指定すると、400 エラー `messages.N.output_config: Extra inputs are not permitted` が返ります。`N` は、`messages` 内の `system` メッセージのインデックスです。
- ベータヘッダーを付けても、Claude Fable 5 など、この機能に対応していないモデルでは 400 エラー `output_config.effort requires a model that supports per-turn effort; this model does not` が返ります。Amazon Bedrock では、それらのモデルと Claude Opus 5 が `Extra inputs are not permitted` を返します。
- Claude Sonnet 5.5 で `thinking: {"type": "between_tools"}`、Claude Haiku 5.5 で `thinking: {"type": "disabled"}` を使う場合、会話途中で段階を変更できません。メッセージ単位の `output_config.effort` に別の段階を設定すると 400 エラーになります。ターンごとに段階を変えるには、適応型推論を使います。

## メッセージ単位とトップレベルの設定の違い

リクエスト間で[トップレベルの値を変える](https://platform.claude.com/docs/en/build-with-claude/effort#top-level-effort-on-the-next-request)方法より、メッセージ単位での変更を推奨します。メッセージ単位の変更では、それより前の内容が保たれ、キャッシュ済みの先頭部分が引き続き一致します。トップレベルの変更ではキャッシュが一部または全部無効になる場合があります。Claude Fable 5.1 では、トップレベルの値を変えてもモデルの挙動への反映が弱くなることがあります。以前の回答が変更前の段階で書かれており、モデルはその回答と一貫した挙動を取りやすいためです。

## 提供状況

メッセージ単位の effort は、一部のモデルでベータ版として提供されています。

### 対応する API

#### [Messages API の利用](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)

- 利用できます。

| 提供状況 | クラウドプラットフォーム | 対応モデル |
|---|---|---|
| ベータ | Claude API、[Amazon Bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)、[Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)、[Claude Models on Google Cloud （Anthropic が運用）](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/anthropic-managed)、[Claude Models on Google Cloud （Google が運用）](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)、[Microsoft Foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry) | [Claude Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview)、[Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview) |
| ベータ（注 1） | [Amazon Bedrock (bedrock-runtime)](https://platform.claude.com/docs/en/build-with-claude/claude-on-amazon-bedrock-legacy) | [Claude Fable 5.2](https://platform.claude.com/docs/en/models/fable-5-2/overview)、[Claude Mythos 5.2](https://platform.claude.com/docs/en/models/mythos-5-2/overview)、[Claude Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview)、[Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview) |
| ベータ | Claude API、[Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)、[Claude Models on Google Cloud （Anthropic が運用）](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/anthropic-managed)、[Claude Models on Google Cloud （Google が運用）](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)、[Microsoft Foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry) | [Claude Fable 5.2](https://platform.claude.com/docs/en/models/fable-5-2/overview)、[Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview)、[Claude Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview)、[Claude Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview) |
| ベータ | Claude API、[Amazon Bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)、[Claude Models on Google Cloud （Google が運用）](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)、[Microsoft Foundry （Anthropic がホスト）](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry) | [Claude Mythos 5.1](https://platform.claude.com/docs/en/models/mythos-5-1/overview) |
| ベータ | Claude API、[Claude Models on Google Cloud （Anthropic が運用）](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/anthropic-managed)、[Claude Models on Google Cloud （Google が運用）](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)、[Microsoft Foundry （Anthropic がホスト）](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry) | [Claude Mythos 5.2](https://platform.claude.com/docs/en/models/mythos-5-2/overview) |

1. リクエスト本体の `anthropic_beta` 配列でベータの値を送信します。

#### [Managed Agents の概要](https://platform.claude.com/docs/en/managed-agents/overview)

- この機能は提供対象外です。
- セッションの effort は、エージェントのモデル設定を上書きして指定します。

### 必須のベータヘッダー

[ベータヘッダーの概要](https://platform.claude.com/docs/en/api/beta-headers)

ベータヘッダーを指定すると、標準 API に組み込まれる前の試験的な機能や新しいモデル機能を利用できます。

- `mid-conversation-output-config-2026-07-01`
