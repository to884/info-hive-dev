---
url: "https://platform.claude.com/docs/en/build-with-claude/extended-thinking"
title: "Extended thinking"
fetched_at: "2026-11-18T22:18:09+09:00"
source_sha256: "ae2c8fc93c74b98a4dc9e2ae94b7fcdb5c370d10e8c7724b1039c88ff4d1b225"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# 拡張推論

対応する Claude モデルで、固定の budget_tokens を指定して手動の拡張推論を設定する方法と、適応型推論への移行手順を説明します。

拡張推論は従来の機能です。

拡張推論（`thinking.type: "enabled"` と `budget_tokens`）は非推奨です。Claude 4.7 以降のモデルでは、この設定を含むリクエストは 400 エラーになります。

- 推奨する移行先：[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)
- 移行ガイド：[適応型推論への移行](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#migrating-to-adaptive-thinking)

手動モードの拡張推論では、Claude が推論に使うトークン数を直接調整できます。リクエストごとに `thinking: {type: "enabled", budget_tokens: N}` で予算を指定すると、Claude は最終回答を始める前にその予算を目安に推論します。処理時間の見通しや推論費用の細かな調整が必要な場合に使えます。このページでは、予算の設定と調整、ツール呼び出し間の推論やプロンプトキャッシュとの関係、適応型推論への移行を扱います。

推論ブロックと応答の構造、`display` パラメーター、ストリーミング、ツール利用時の推論、暗号化の仕組みは、[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)を参照してください。

## 対応モデル

拡張推論だけを使えるモデルを含め、各モデルの対応状況は[モデル別の設定表](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#supported-models)を参照してください。

## 拡張推論を使う

Messages API で拡張推論を使う例を示します。

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
        "content": "Are there an infinite number of prime numbers such that n mod 4 == 3?"
      }
    ]
  }'
```

```bash
ant messages create --format yaml <<'YAML'
model: claude-sonnet-4-6
max_tokens: 16000
thinking:
  type: enabled
  budget_tokens: 10000
messages:
  - role: user
    content: Are there an infinite number of prime numbers such that n mod 4 == 3?
YAML
```

```python
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[
        {
            "role": "user",
            "content": "Are there an infinite number of prime numbers such that n mod 4 == 3?",
        }
    ],
)

# The response contains summarized thinking blocks and text blocks
for block in response.content:
    match block.type:
        case "thinking":
            print(f"\nThinking summary: {block.thinking}")
        case "text":
            print(f"\nResponse: {block.text}")
```

```typescript
const client = new Anthropic();

const response = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 16000,
  thinking: {
    type: "enabled",
    budget_tokens: 10000
  },
  messages: [
    {
      role: "user",
      content: "Are there an infinite number of prime numbers such that n mod 4 == 3?"
    }
  ]
});

// The response contains summarized thinking blocks and text blocks
for (const block of response.content) {
  switch (block.type) {
    case "thinking":
      console.log(`\nThinking summary: ${block.thinking}`);
      break;
    case "text":
      console.log(`\nResponse: ${block.text}`);
      break;
  }
}
```

```csharp
AnthropicClient client = new();

var response = await client.Messages.Create(new()
{
    Model = Model.ClaudeSonnet4_6,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigEnabled(budgetTokens: 10000),
    Messages =
    [
        new UserMessageParam
        {
            Content = "Are there an infinite number of prime numbers such that n mod 4 == 3?",
        },
    ],
});

// The response contains summarized thinking blocks and text blocks
foreach (var block in response.Content)
{
    if (block.TryPickThinking(out var thinking))
    {
        Console.WriteLine($"\nThinking summary: {thinking.Thinking}");
    }
    else if (block.TryPickText(out var text))
    {
        Console.WriteLine($"\nResponse: {text.Text}");
    }
}
```

```go
client := anthropic.NewClient()

response, err := client.Messages.New(context.Background(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeSonnet4_6,
	MaxTokens: 16000,
	Thinking:  anthropic.ThinkingConfigParamOfEnabled(10000),
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("Are there an infinite number of prime numbers such that n mod 4 == 3?")),
	},
})
if err != nil {
	log.Fatal(err)
}

// The response contains summarized thinking blocks and text blocks
for _, block := range response.Content {
	switch block := block.AsAny().(type) {
	case anthropic.ThinkingBlock:
		fmt.Printf("\nThinking summary: %s", block.Thinking)
	case anthropic.TextBlock:
		fmt.Printf("\nResponse: %s", block.Text)
	}
}
```

```java
import com.anthropic.client.okhttp.AnthropicOkHttpClient;
import com.anthropic.models.messages.MessageCreateParams;
import com.anthropic.models.messages.Model;

void main() {
    var client = AnthropicOkHttpClient.fromEnv();

    var params = MessageCreateParams.builder()
        .model(Model.CLAUDE_SONNET_4_6)
        .maxTokens(16_000)
        .enabledThinking(10_000)
        .addUserMessage("Are there an infinite number of prime numbers such that n mod 4 == 3?")
        .build();

    var response = client.messages().create(params);

    // The response contains summarized thinking blocks and text blocks
    for (var block : response.content()) {
        block.thinking().ifPresent(thinkingBlock ->
            IO.println("\nThinking summary: " + thinkingBlock.thinking())
        );
        block.text().ifPresent(textBlock ->
            IO.println("\nResponse: " + textBlock.text())
        );
    }
}
```

```php
$client = new Client();

$response = $client->messages->create(
    model: 'claude-sonnet-4-6',
    maxTokens: 16000,
    thinking: ['type' => 'enabled', 'budget_tokens' => 10000],
    messages: [
        [
            'role' => 'user',
            'content' => 'Are there an infinite number of prime numbers such that n mod 4 == 3?',
        ],
    ],
);

// The response contains summarized thinking blocks and text blocks
foreach ($response->content as $block) {
    echo match (true) {
        $block instanceof \Anthropic\Messages\ThinkingBlock => "\nThinking summary: {$block->thinking}",
        $block instanceof \Anthropic\Messages\TextBlock => "\nResponse: {$block->text}",
        default => '',
    };
}
```

```ruby
client = Anthropic::Client.new

response = client.messages.create(
  model: Anthropic::Model::CLAUDE_SONNET_4_6,
  max_tokens: 16_000,
  thinking: {
    type: :enabled,
    budget_tokens: 10_000
  },
  messages: [
    {
      role: :user,
      content: "Are there an infinite number of prime numbers such that n mod 4 == 3?"
    }
  ]
)

# The response contains summarized thinking blocks and text blocks
response.content.each do |block|
  case block
  when Anthropic::Models::ThinkingBlock
    puts "\nThinking summary: #{block.thinking}"
  when Anthropic::Models::TextBlock
    puts "\nResponse: #{block.text}"
  end
end
```

手動の拡張推論を有効にするには、`type` に `enabled` を指定し、`budget_tokens` の値を設定した `thinking` オブジェクトを追加します。

`budget_tokens` は、Claude が内部の推論に使うトークン数の目安です。予算を増やすと複雑な問題を詳しく検討でき、回答の品質が上がる場合があります。

## 予算の規則と調整

`budget_tokens` には次の制約があります。

- **最小 1,024 トークン。** それ未満の値は API が拒否します。
- **`max_tokens` 未満。** 推論トークンはターンの `max_tokens` に含まれるため、最終回答に使う分を残しておきます。例外は[手動モードでツール呼び出し間に推論する場合](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#interleaved-thinking)です。この場合、予算は 1 回のアシスタントターンに含まれるすべての推論ブロックを対象とするため、`budget_tokens` は `max_tokens` を超えられます。
- **キャッシュの事前作成には使えません。** `budget_tokens` を `max_tokens` 未満にする必要があるため、拡張推論と `max_tokens: 0`（[キャッシュの事前作成](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#pre-warming-the-cache)）は併用できません。

予算は目安です。実際に使うトークン数はタスクによって異なり、Claude が予算を使い切る前に推論を終えることもあります。出力全体の上限は `max_tokens` です。

拡張推論だけを使い、[effort](https://platform.claude.com/docs/en/build-with-claude/effort) にも対応する唯一のモデルである Claude Opus 4.5 では、effort が応答全体を調整し、`budget_tokens` が推論の深さを指定します。両方を設定してください。

予算を調整する手順は次のとおりです。

- タスクに合わせて最初の値を決めます。単純なタスクなら下限の 1,024 トークン付近から少しずつ増やし、用途に合う範囲を探します。複雑なタスクなら 16,000 トークン以上から始め、必要な応答時間と品質に合わせて調整します。予算を増やすほど詳しく推論できますが、改善幅はタスクによって次第に小さくなり、応答時間は延びます。重要なタスクでは設定を変えて試し、両者のバランスを見ます。
- 推論予算が 32,000 トークンを超える場合は、ネットワークの問題を避けるために[バッチ処理](https://platform.claude.com/docs/en/build-with-claude/batch-processing)を使います。32,000 トークンを超える推論は処理時間が長くなり、システムのタイムアウトや同時接続数の制限に達することがあります。

実際の費用を把握するには、応答の `usage.output_tokens_details.thinking_tokens` を確認します。この値は、課金対象の出力トークンのうち、内部推論に使った数です。ストリーミングでは、内訳は最後の `message_delta` イベントだけに現れます。

手動で予算を指定する方式から切り替えるときは、[適応型推論への移行](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#migrating-to-adaptive-thinking)を参照してください。

## 手動モードでツール呼び出し間に推論する

ツール呼び出し間の推論では、Claude が 1 回のアシスタントターン内でツールの結果を検討してから、次に何をするか決められます。仕組み、ターンの構造、適応型推論での挙動は、推論の概要の[ツール呼び出し間の推論](https://platform.claude.com/docs/en/build-with-claude/thinking#interleaved-thinking)を参照してください。ここでは、手動で `type: "enabled"` を指定したときにこの機能を有効にする手順を説明します。

Claude Opus 4.5、Claude Sonnet 4.5（非推奨）、それ以前の Claude 4 モデルでは、API リクエストに [ベータヘッダー](https://platform.claude.com/docs/en/api/beta-headers) `interleaved-thinking-2025-05-14` を追加します。

4.6 世代では、手動モードの挙動がモデルによって異なります。

- **Claude Sonnet 4.6** では、手動の `type: "enabled"` とベータヘッダーの組み合わせは引き続き動作しますが、非推奨です。[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking)を使うと、ヘッダーを省略してもツール呼び出し間で推論します。
- **Claude Opus 4.6** でツール呼び出し間に推論できるのは適応型推論だけです。このモデルでツールの結果ごとに推論させるには、`thinking: {type: "adaptive"}` に切り替えます。

Claude Haiku 4.5 はツール呼び出し間の推論に対応していません。Claude API はベータヘッダーを受け付けますが、適用しません。

手動モードでツール呼び出し間に推論する場合、次の点にも注意します。

- この場合は `budget_tokens` が `max_tokens` を超えられます。例外の詳細は[予算の規則](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#budget-rules-and-tuning)を参照してください。
- ツール呼び出し間の推論に対応するのは、[Messages API 経由のツール利用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)だけです。

ベータヘッダーの扱いはプラットフォームによって異なります。Claude API、[Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)、[Claude Models on Google Cloud (Anthropic managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/anthropic-managed) はどのモデルでも `interleaved-thinking-2025-05-14` を受け付け、対応しないモデルでは無視します。`type: "enabled"` を拒否するモデル（4.7 以降）、および手動モードでツール呼び出し間の推論に対応しない Claude Opus 4.6 では、ヘッダーを付けても手動モードの挙動は変わりません。適応型推論では自動でツール呼び出し間に推論します。

パートナーが運用する [Claude Models on Google Cloud (Google managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed) と [Amazon Bedrock (`bedrock-mantle`)](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock) は、どのモデルでもベータヘッダーをエラーなしで受け付けます。ツール呼び出し間の推論に対応しないモデルではヘッダーを無視します。

## 手動モードのターンの構造

1 回のターン内で繰り返すツール利用、ターン途中の設定の衝突、ターン間での推論の切り替えなど、共通する規則は[ツール利用時の推論](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-with-tool-use)を参照してください。

手動モードで推論を有効にしたリクエストでは、最後のアシスタントターンは推論ブロックで始まる必要があります。[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking)にこの要件はありません。ターン間で推論設定を変えるとプロンプトキャッシュが無効になります。詳しくは次の節を参照してください。

## 手動モードのプロンプトキャッシュ

[推論とプロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-prompt-caching)で説明する共通の挙動に加え、手動モードでは、リクエスト間で `budget_tokens` を変更するとキャッシュの区切りが無効になります。推論モードの切り替えと同様に、予算の値がプロンプトに反映されるためです。予算を変更するとメッセージの区切りでは常にキャッシュミスが起きます。ツールやシステムプロンプトの区切りでもミスが起きるかどうかは、モデルが設定をどこに反映するかによります。

キャッシュを使う会話の間は、同じ予算を維持します。Claude Sonnet 4.6 でメッセージをキャッシュする複数ターンの会話を実行し、3 回目のリクエストで予算を 4,000 トークンから 8,000 トークンに変えると、キャッシュが無効になることを確認できます。

```text
First request - establishing cache
First response usage: { cache_creation_input_tokens: 1370, cache_read_input_tokens: 0, input_tokens: 17, output_tokens: 700 }

Second request - same thinking parameters (cache hit expected)
Second response usage: { cache_creation_input_tokens: 0, cache_read_input_tokens: 1370, input_tokens: 303, output_tokens: 874 }

Third request - different thinking budget (cache miss expected)
Third response usage: { cache_creation_input_tokens: 1370, cache_read_input_tokens: 0, input_tokens: 747, output_tokens: 619 }
```

リクエスト間で予算を変えたため、3 回目のリクエストはキャッシュを作り直します（`cache_creation_input_tokens=1370`、`cache_read_input_tokens=0`）。適応型推論で同様の実験を実行するコードは、推論の調整ガイドの[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#prompt-caching)を参照してください。手動モードの `budget_tokens` に相当するキャッシュへの影響を、適応型推論では effort の段階で確認できます。

## 推論モードに共通する仕組み

推論の多くの挙動はモードに共通しており、[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)で説明しています。次の節は手動モードにも当てはまります。

- [推論の表示を設定する](https://platform.claude.com/docs/en/build-with-claude/thinking#controlling-thinking-display)
- [推論をストリーミングする](https://platform.claude.com/docs/en/build-with-claude/thinking#streaming-thinking)
- [ツール利用時の推論](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-with-tool-use)と[推論ブロックの保持](https://platform.claude.com/docs/en/build-with-claude/thinking#preserving-thinking-blocks)
- [推論とプロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-prompt-caching)
- [推論とコンテキストウィンドウ](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-the-context-window)
- [推論の暗号化](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-encryption)
- [料金](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#pricing)（[推論の調整ガイド](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)）

## 適応型推論への移行

Claude Sonnet 4.5（非推奨）、Claude Opus 4.5、Claude Haiku 4.5、それ以前の Claude 4 モデルは、拡張推論だけに対応します。これらのモデルで `type: "adaptive"` を指定すると [400 エラー](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#error-thinking-type-adaptive)になります。適応型推論に対応するモデルへ移るまで `budget_tokens` を使い、移行後は以下の手順で設定を切り替えます。

`type: "enabled"` から切り替えが必要なのは次の場合です。

- Claude Opus 4.6 または Claude Sonnet 4.6 を使い、非推奨の `budget_tokens` を指定している。
- バージョン番号が 4.7 以降のモデルを使い、`type: "enabled"` を指定すると 400 エラーになる。例として Claude Opus 5.5、Claude Sonnet 5、Claude Sonnet 5.5、Claude Fable 5.2、Claude Fable 5.1、Claude Haiku 5.5 がある。

`budget_tokens` を削除し、`thinking: {type: "adaptive"}` を設定します。推論の深さは `output_config: {effort: ...}` で調整します。

```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 16000,
  "thinking": {
    "type": "enabled",
    "budget_tokens": 10000
  }
}
```

次のように書き換えます。

```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 16000,
  "thinking": {
    "type": "adaptive"
  },
  "output_config": {
    "effort": "high"
  }
}
```

Claude Sonnet 4.6 では `effort: "high"` が既定値のため、この例で省略しても挙動は同じです。ここでは適応型推論で深さを指定する箇所を示すために書いています。Claude Opus 5.5 と Claude Haiku 5.5 の既定値は `"medium"` で、effort に対応する他のモデルの既定値は `"high"` です（[effort の段階](https://platform.claude.com/docs/en/build-with-claude/effort#effort-levels)を参照）。

移行後は推論の挙動も変わります。固定予算を指定すると Claude はリクエストごとに推論します。適応型推論では Claude がリクエストごとに推論するかどうかと深さを決めます。[effort](https://platform.claude.com/docs/en/build-with-claude/effort) が低い設定では、簡単な入力で推論を省く場合があります。移行後はベータヘッダー `interleaved-thinking-2025-05-14` を削除できます。適応型推論では自動でツール呼び出し間に推論し、Claude API はこれらのモデルでヘッダーを無視します。推論ブロックを保持する範囲も変わります。Claude Opus 4.5 とバージョン番号が 4.6 以降のモデルは、以前のターンの推論ブロックをコンテキストに保持し、入力として課金します。Claude Sonnet 4.5（非推奨）、Claude Haiku 4.5、それ以前のモデルは取り除きます。[モデル別の推論ブロックの保持](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-block-preservation-by-model)を参照してください。

推論モードを切り替えると、切り替え後の最初のリクエストでキャッシュの区切りが無効になります。詳しくは[手動モードのプロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#extended-thinking-with-prompt-caching)を参照してください。

詳しい手順は[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)、[effort](https://platform.claude.com/docs/en/build-with-claude/effort)、[移行ガイド](https://platform.claude.com/docs/en/about-claude/models/migration-guide)を参照してください。

## 関連資料

[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)

推論ブロック、表示、ストリーミング、ツール利用の仕組みを説明します。

[推論の調整](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)

各リクエストで推論するかどうかと深さを Claude が決める仕組みを説明します。

[ツール利用と複数ターンの処理における推論](https://platform.claude.com/docs/en/build-with-claude/thinking-tool-workflows)

推論ブロックを保持し、ツール呼び出しやターンをまたいで推論を扱う手順を説明します。

## 提供状況

一部のモデルで拡張推論を使えます。そのうち一部では非推奨です。

### API の対応

#### [Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)

- 提供状況：利用可能

| 状態 | モデル |
|---|---|
| 利用可能 | Claude Mythos Preview、[Claude Haiku 4.5](https://platform.claude.com/docs/en/models/haiku-4-5/overview)、[Claude Opus 4.5](https://platform.claude.com/docs/en/models/opus-4-5/overview)、[Claude Sonnet 4.5](https://platform.claude.com/docs/en/models/sonnet-4-5/overview) |
| 非推奨 | [Claude Opus 4.6](https://platform.claude.com/docs/en/models/opus-4-6/overview)、[Claude Sonnet 4.6](https://platform.claude.com/docs/en/models/sonnet-4-6/overview) |

#### [Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview)

- 提供状況：利用不可
- 挙動：Claude 4.5 モデルでは、Managed Agents が固定予算で手動の推論を有効にします。予算は変更できません。新しいモデルでは適応型推論を使います。調整には [effort](https://platform.claude.com/docs/en/build-with-claude/effort) を使ってください。
