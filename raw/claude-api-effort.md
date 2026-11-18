---
url: "https://platform.claude.com/docs/en/build-with-claude/effort"
title: "Effort"
fetched_at: "2026-11-18T21:08:51+09:00"
source_sha256: "f381842cdc74aca09d7db32505ffe58b95ef454faf18127db08eb3674bff5aa1"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# Effort

effort パラメーターは、Claude が応答に使うトークン量を調整し、回答の詳しさとトークン効率のバランスを取るための設定です。

**API の対応状況**。指定方法は製品によって異なります。

- **Messages API** では、リクエストの `output_config.effort` に設定します。省略するとモデルの既定値が適用されます。
- **Managed Agents** では、エージェントのモデルオブジェクトか、セッションのモデル設定を上書きする箇所で `effort` を指定します。省略すると Managed Agents がモデルの既定値を補います。

effort パラメーターを使うと、Claude がリクエストへの応答に費やすトークン量を調整できます。同じモデルで、回答の詳しさとトークン効率のバランスを変えられます。

effort と推論の関係や設定の選び方は、[推論と effort（Thinking and effort）](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-effort)を参照してください。適応型推論を利用できる場合は、effort で推論の深さを調整することを推奨します。

## effort の指定方法

リクエストに `output_config.effort` を指定します。以下の例では、`medium` で 1 回リクエストを実行します。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-5-5",
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
  --model claude-opus-5-5 \
  --max-tokens 4096 \
  --output-config '{effort: medium}' \
  --message '{role: user, content: "Analyze the trade-offs between microservices and monolithic architectures"}'
```

```python
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": "Analyze the trade-offs between microservices and monolithic architectures",
        }
    ],
    output_config={"effort": "medium"},
)

for block in response.content:
    if block.type == "text":
        print(block.text)
```

```typescript
const client = new Anthropic();

const response = await client.messages.create({
  model: "claude-opus-5-5",
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

const textBlock = response.content.find((block) => block.type === "text");
console.log(textBlock?.text);
```

```csharp
AnthropicClient client = new();

var parameters = new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
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
	Model:     anthropic.ModelClaudeOpus5_5,
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
        .model(Model.CLAUDE_OPUS_5_5)
        .maxTokens(4096L)
        .addUserMessage("Analyze the trade-offs between microservices and monolithic architectures")
        .outputConfig(OutputConfig.builder()
            .effort(OutputConfig.Effort.MEDIUM)
            .build())
        .build();

    Message response = client.messages().create(params);
    response.content().stream()
        .flatMap(block -> block.text().stream())
        .forEach(textBlock -> IO.println(textBlock.text()));
}
```

```php
use Anthropic\Client;
use Anthropic\Messages\Model;
use Anthropic\Messages\TextBlock;

$client = new Client();

$message = $client->messages->create(
    maxTokens: 4096,
    messages: [
        ['role' => 'user', 'content' => 'Analyze the trade-offs between microservices and monolithic architectures']
    ],
    model: Model::CLAUDE_OPUS_5_5,
    outputConfig: ['effort' => 'medium'],
);

foreach ($message->content as $block) {
    if ($block instanceof TextBlock) {
        echo $block->text, PHP_EOL;
    }
}
```

```ruby
client = Anthropic::Client.new

message = client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 4096,
  messages: [
    { role: "user", content: "Analyze the trade-offs between microservices and monolithic architectures" }
  ],
  output_config: {
    effort: "medium"
  }
)

message.content.each do |block|
  case block
  when Anthropic::Models::TextBlock
    puts block.text
  end
end
```

## effort の仕組み

ほとんどの Claude モデルでは既定値が high で、質の高い結果に必要なだけトークンを使います。Claude Opus 5.5 と Claude Haiku 5.5 の既定値は medium です。最高の能力を引き出すには `max` に引き上げます。引き下げると能力はいくらか落ちますが、トークン消費を抑え、速度と費用を優先できます。

`effort` にモデルの既定値（Claude Opus 5.5 と Claude Haiku 5.5 では `"medium"`、ほかのモデルでは `"high"`）を明示した場合の挙動は、`effort` パラメーターを省略した場合と同じです。

effort パラメーターは、応答に含まれる**すべてのトークン**に作用します。

- テキストでの回答と説明
- ツール呼び出しと関数の引数
- 推論（有効な場合）

effort はすべての出力トークンに作用するため、推論の有効・無効にかかわらず使えます。低い段階にすると、ツール呼び出しの回数が減り、内容も簡潔になります。

### effort の段階

| 段階 | 説明 | 主な用途 |
|---|---|---|
| `max` | トークン消費を抑えず、能力を最大限に引き出します。対応モデルは Claude Fable 5.2、Claude Mythos 5.2、Claude Fable 5.1、Claude Mythos 5.1、Claude Fable 5、Claude Mythos 5、Claude Mythos Preview、Claude Opus 5.5、Claude Opus 5、Claude Opus 4.8、Claude Opus 4.7、Claude Opus 4.6、Claude Sonnet 5.5、Claude Sonnet 5、Claude Sonnet 4.6、Claude Haiku 5.5 です。 | 最大限深い推論と詳細な分析が必要なタスク |
| `xhigh` | 長時間にわたる作業に向けて能力を高めます。対応モデルは Claude Fable 5.2、Claude Mythos 5.2、Claude Fable 5.1、Claude Mythos 5.1、Claude Fable 5、Claude Mythos 5、Claude Opus 5.5、Claude Opus 5、Claude Opus 4.8、Claude Opus 4.7、Claude Sonnet 5.5、Claude Sonnet 5、Claude Haiku 5.5 です。 | 30 分を超え、数百万トークンの予算を持つエージェント作業やコーディング |
| `high` | 質の高い結果を得るために必要なだけトークンを使います。Claude Opus 5.5 と Claude Haiku 5.5 を除く対応モデルの既定値です。 | 複雑な推論、難しいコーディング、エージェント作業 |
| `medium` | 能力を保ちつつ、トークンをある程度節約します。Claude Opus 5.5 と Claude Haiku 5.5 の既定値です。 | 速度、費用、性能のバランスが求められるエージェント作業 |
| `low` | トークン効率が最も高い段階です。能力はいくらか落ちますが、トークンを大幅に節約できます。 | サブエージェントなど、速度と費用を優先する比較的単純な作業 |

`max` に対応していても、`xhigh` を使えないモデルがあります。

effort はモデルの挙動を調整する設定で、トークンの厳密な予算ではありません。低い段階でも難しい問題では Claude は推論を行いますが、同じ問題に費やす推論は高い段階より少なくなります。

この表と後述のモデル別の推奨が異なる場合は、モデル別の推奨を優先してください。

## モデル別の推奨設定

**[Claude Fable 5.2](https://platform.claude.com/docs/en/models/fable-5-2/overview) と [Claude Mythos 5.2](https://platform.claude.com/docs/en/models/mythos-5-2/overview)**。高度な推論や長時間のエージェント作業向けです。

Claude Fable 5.2 は 5 段階すべてに対応します。API の既定値は `high` です。適応型推論は常時有効で、推論の深さ、応答時間、費用は主に effort で調整します。

まず `high` を使います。能力の伸びの大半は `high` までに得られ、それより上の効果はタスクによって差があります。長時間かかる難しいコーディングやエージェント作業では、評価で改善を確認できた場合に `xhigh` に引き上げます。品質を維持できる場合は `medium` や `low` に下げます。`max` はモデルの能力の上限を測る場合や、時間とトークン消費を問わないまれなタスクに使います。`max` はトークンの費用を考慮せず能力を優先します。`xhigh` より遅く費用もかかり、改善は小幅にとどまることがよくあります。

Claude Fable 5.1 の設定を引き継ぐ前に、自分の評価で複数の段階を試してください。`high` 以上では `max_tokens` を大きく設定します。これは推論と回答テキストを合わせた総出力の厳密な上限です。effort を変えても回答の長さはほとんど変わらないため、長さや語調はプロンプトで指定してください。

Claude Mythos 5.2 にも同じ推奨が当てはまります。

[対応プラットフォーム](https://platform.claude.com/docs/en/build-with-claude/effort-per-message#feature-availability)では、Claude Fable 5.2 と Claude Mythos 5.2 はメッセージごとの `output_config` により[会話の途中で effort を変更](https://platform.claude.com/docs/en/build-with-claude/effort-per-message)できます。この方法ではプロンプトキャッシュが維持されます。

関連資料として [Claude Fable 5.2 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#calibrate-effort)を参照してください。

**[Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview)**。長時間のエージェント型コーディングや知的作業向けです。

Claude Opus 5.5 は 5 段階すべてに対応し、既定値は `medium` です。Claude Opus 5 以前の Opus モデルでは既定値が `high` なので、`effort` を省略すると Claude Opus 5.5 は従来より 1 段階低い設定で動きます。

適応型推論は常時有効で、無効化できません。推論量とリクエストの費用は主に effort で調整します。`thinking: {"type": "disabled"}` を指定したリクエストは、どの段階でも 400 エラーになります。

以前のモデルの設定を引き継ぐ前に、自分の評価で複数の段階を試してください。`xhigh` または `max` では `max_tokens` を大きく設定します。これは推論と回答テキストを合わせた総出力の厳密な上限です。

Claude Opus 5.5 でもメッセージごとの `output_config` により[会話の途中で effort を変更](https://platform.claude.com/docs/en/build-with-claude/effort-per-message)でき、プロンプトキャッシュを維持できます。

関連資料として [Claude Opus 5.5 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)を参照してください。

**[Claude Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview)**。速度と知的能力のバランスに優れています。

Claude Sonnet 5.5 は 5 段階すべてに対応し、Claude API の既定値は `high` です。段階ごとの調整が異なるため、同じ設定でも Claude Sonnet 5 と推論量は異なります。Claude Sonnet 5 の設定を引き継ぐ前に、自分の評価で複数の段階を試してください。

エージェント作業や応答時間を重視する処理を除き、まず `high` を使います。エージェント型コーディングや複数段階のツール利用では、要件が明確な場合は `medium` から始め、より難しい、または長いタスクでは `high` に上げます。チャットなど応答時間を重視する仕事は `medium` か `low` から始め、`xhigh` や `max` は評価で品質の向上を確認できた場合に使います。

推論と回答の両方に十分な `max_tokens` を設定します。推論の内容が返らない場合も、そのトークンは `max_tokens` に含まれます。エージェント型コーディングでは、モデルの上限である 128,000 に `max_tokens` を設定し、応答をストリーミングします。[メッセージのストリーミング（Streaming messages）](https://platform.claude.com/docs/en/build-with-claude/streaming)を参照してください。

最初の応答前の推論を省くには、`"disabled"` の代わりに `thinking: {"type": "between_tools"}` を送ります。この設定は `low`、`medium`、`high` で使えます。`xhigh` と `max` では 400 エラーになるため、その段階では既定の適応型推論を使います。[応答前の推論を省く方法（Running without up-front thinking）](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#running-without-up-front-thinking)を参照してください。

[対応プラットフォーム](https://platform.claude.com/docs/en/build-with-claude/effort-per-message#feature-availability)では、Claude Sonnet 5.5 もメッセージごとの `output_config` で[会話の途中で effort を変更](https://platform.claude.com/docs/en/build-with-claude/effort-per-message)でき、プロンプトキャッシュを維持できます。`between_tools` の場合は途中で変更できず、異なる段階の `output_config.effort` をメッセージに設定すると 400 エラーになります。ターンごとに変えるには適応型推論を使います。

関連資料として [Claude Sonnet 5.5 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#calibrate-effort)を参照してください。

**[Claude Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview)**。分類、抽出、振り分けなど、大量に処理し応答時間も重視する用途に向きます。

Claude Haiku 5.5 は 5 段階すべてに対応し、既定値は `medium` です。モデルの推論量、それに伴う品質、応答時間、費用は主に effort で調整します。**エージェント型コーディングを含め、多くの作業は `medium` から始めます。** チャット、短いツール操作、単純で件数の多いリクエストには、最も低費用で速い `low` を使います。長いエージェント向けプロンプトで `low` を使うと、検索を飛ばしたり、途中で止めたり、確認を省いたりする可能性が上がります。知的作業、長時間のエージェント作業、厳密に指示に従わせる用途には `high` を使います。`xhigh` と `max` は評価で品質の向上が得られた場合に使い、Claude Sonnet 5.5 と性能、費用、速度を比較します。推論は既定で有効で、推論トークンも `max_tokens` に含めて余裕を持たせます。

推論量を減らすには effort を下げます。`high` 以下では `thinking: {"type": "disabled"}` も送れます。`xhigh` と `max` では 400 エラーになるため、適応型推論を使います。その場合は `thinking` を省略するか、`thinking: {"type": "adaptive"}` を送ります。

[対応プラットフォーム](https://platform.claude.com/docs/en/build-with-claude/effort-per-message#feature-availability)では、Claude Haiku 5.5 でもメッセージごとの `output_config` で[会話の途中で effort を変更](https://platform.claude.com/docs/en/build-with-claude/effort-per-message)でき、プロンプトキャッシュを維持できます。`thinking: {"type": "disabled"}` のときは途中で変更できず、メッセージ単位の `output_config.effort` に異なる段階を指定すると 400 エラーになります。ターンごとに変えるには適応型推論を使います。

関連資料として [Claude Haiku 5.5 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5#use-effort-to-control-thinking)を参照してください。

**[Claude Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview) と [Claude Mythos 5.1](https://platform.claude.com/docs/en/models/mythos-5-1/overview)**

Claude Fable 5.1 は 5 段階すべてに対応します。**まず既定の `high` を使います。** 高い能力が必要なエージェント作業やコーディングでは `xhigh` か `max` へ上げ、定型作業や速さが求められる処理では、品質を維持できることを評価で確かめてから `medium` か `low` へ下げます。`high` 以上では `max_tokens` を大きく設定します。これは推論と回答テキストを合わせた総出力の厳密な上限です。

Claude Fable 5.1 でもメッセージごとの `output_config` で[会話の途中で effort を変更](https://platform.claude.com/docs/en/build-with-claude/effort-per-message)でき、プロンプトキャッシュを維持できます。

関連資料として [Claude Fable 5.1 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#consider-all-effort-levels)を参照してください。

**[Claude Fable 5](https://platform.claude.com/docs/en/models/fable-5/overview) と [Claude Mythos 5](https://platform.claude.com/docs/en/models/mythos-5/overview)**

Claude Fable 5 では、知的能力、応答時間、費用のバランスを主に effort で調整します。**ほとんどのタスクは既定の `high` から始めます。** 高い能力が求められる処理には `xhigh` を使い、定型処理には `medium` や `low` に下げます。Claude Fable 5 は低い段階でも性能が高く、多くの場合、以前のモデルを `xhigh` で使ったときの性能を上回ります。`high` と `xhigh` では `max_tokens` を大きく設定します。これは推論と回答テキストを合わせた総出力の厳密な上限です。[費用の調整（Cost control）](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#cost-control)を参照してください。

タスクを完了できても必要以上に時間がかかる場合や、対話のテンポを速めたい場合は、effort を下げます。

関連資料として [Claude Fable 5 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)を参照してください。

**[Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview)**

Claude Opus 5 は 5 段階すべてに対応します。**まず既定の `high` から始め**、自分の評価結果に基づいて調整します。難しいコーディングやエージェント作業には `xhigh` を、トークン消費を問わず能力を引き出す価値のあるタスクには `max` を使います。品質が維持できると評価で確認した処理では、主に `low` と `medium` でトークンの費用と応答時間を抑えます。以前のモデルで使っていた設定はそのまま引き継がず、自分の評価で複数の段階を改めて試してください。

effort は推論量の調整に使います。Claude Opus 5 では effort を変えても表示される回答が安定して短くなるわけではないため、[長さはプロンプトで指定](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5#response-length-and-verbosity)してください。

API の既定値は `high` です。別の段階を使うには `effort` を明示し、その値で既定値を上書きします。

Claude Opus 5 の `xhigh` と `max` では推論を無効化できません。これらの段階で `thinking: {"type": "disabled"}` を指定すると 400 エラーが返ります。[effort と推論（Effort with thinking）](https://platform.claude.com/docs/en/build-with-claude/effort#effort-with-thinking)を参照してください。

Claude Opus 5 を `xhigh` または `max` で使うときは、サブエージェントやツール呼び出しを伴う推論と処理に余裕ができるよう、`max_tokens` を大きくします。約 64,000 トークンから始め、必要に応じて調整するのが妥当です。

[対応プラットフォーム](https://platform.claude.com/docs/en/build-with-claude/effort-per-message#feature-availability)では、Claude Opus 5 もメッセージごとの `output_config` で[会話の途中で effort を変更](https://platform.claude.com/docs/en/build-with-claude/effort-per-message)でき、プロンプトキャッシュを維持できます。

関連資料として [Claude Opus 5 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)を参照してください。

**[Claude Opus 4.8](https://platform.claude.com/docs/en/models/opus-4-8/overview)**

Claude Opus 4.7 の指針は Claude Opus 4.8 にも当てはまります。**コーディングとエージェント作業は `xhigh` から始めます。** それ以外で知的能力を重視する処理の多くには `high` を使い、自分の評価で品質を維持できた場合に `medium` や `low` へ下げます。

API の既定値は `high` です。別の段階を使うには `effort` を明示し、その値で既定値を上書きします。

Claude Opus 4.8 を `xhigh` または `max` で使うときは、サブエージェントやツール呼び出しを伴う推論と処理に余裕ができるよう、`max_tokens` を大きくします。約 64,000 トークンから始め、必要に応じて調整するのが妥当です。

関連資料として [Claude Opus 4.8 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8)を参照してください。

**[Claude Opus 4.7](https://platform.claude.com/docs/en/models/opus-4-7/overview)**

**コーディングとエージェント作業は `xhigh` から始めます。** 知的能力が重要な処理の多くでは `high` 以上を使います。費用を重視する処理には `medium` に下げ、`xhigh` からの改善を評価で測定できた場合に `max` に上げます。

API の既定値は `high` です。`xhigh` を使うには `effort` に明示し、その値で既定値を上書きします。

- **低い段階（`low`）**。効率がよく、短く範囲の明確なタスク向けです。タスクが複数の部分に分かれる場合は、明示的なチェックリストを併用します。
- **中程度の段階（medium）**。費用を減らしつつ良い結果を得たい標準的な作業向けです。
- **高い段階（high）**。能力とトークン消費のバランスも求められる高度な用途向けです。多くの場合、品質とトークン効率のバランスが最もよい段階です。
- **さらに高い段階（xhigh）**。コーディングやエージェント作業、ツールの反復呼び出し、詳細な Web 検索、ナレッジベース検索などの探索的なタスクで推奨する出発点です。`high` よりもトークン消費が大幅に増えます。
- **最高の段階（`max`）**。最難関の問題に使います。ほとんどの処理で、品質の向上は比較的小さい一方で費用は大幅に増えます。構造化出力や深い推論をあまり必要としないタスクの一部では、推論が過剰になることもあります。

Claude Opus 4.7 は Claude Opus 4.6 より effort の段階に厳密に従い、特に `low` と `medium` で差が出ます。低い段階では求められた範囲に作業を絞ります。Claude Opus 4.7 が複雑な問題を浅くしか推論しない場合は、プロンプトで補おうとする前に effort を上げます。応答時間のために低い設定を維持する必要があれば、「このタスクには複数段階の推論が必要です。回答する前に慎重に考えてください」のように具体的な指示を加えます。

Claude Opus 4.7 を `xhigh` または `max` で使うときは、サブエージェントやツール呼び出しを伴う推論と処理に余裕ができるよう、`max_tokens` を大きくします。約 64,000 トークンから始め、必要に応じて調整するのが妥当です。

関連資料として、[プロンプト作成のベストプラクティス](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)を参照してください。

**[Claude Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview)**

Claude Sonnet 5 の既定値は、Claude API と Claude Code の両方で `high` です。

- **高い段階（high、既定）**。速度や費用より品質を重視する複雑な推論、コーディング、エージェント作業に適しています。
- **さらに高い段階（xhigh）**。最も難しいコーディングやエージェント作業向けです。
- **中程度の段階（medium）**。既定より費用を抑えられます。Claude Sonnet 4.6 の high に相当します。
- **低い段階（low）**。件数の多い処理や応答時間を重視する処理に適しています。速度を優先するチャットやコーディング以外の用途に使います。
- **最高の段階（max）**。トークン消費を抑えず、最高の能力が求められるタスクに使います。

関連資料として [Claude Sonnet 5 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5#calibrating-effort-and-thinking-depth)を参照してください。

**[Claude Sonnet 4.6](https://platform.claude.com/docs/en/models/sonnet-4-6/overview)**

Claude Sonnet 4.6 の既定値は `high` です。想定以上に応答に時間がかかることを避けるには、effort を指定します。

- **中程度の段階（medium、推奨）**。ほとんどの用途で速度、費用、性能のバランスが最もよい段階です。エージェント型コーディング、ツールを多用する作業、コード生成に適しています。
- **低い段階（low）**。件数の多い処理や応答時間を重視する処理に適しています。速度を優先するチャットやコーディング以外の用途に使います。
- **高い段階（high）**。品質を優先する複雑な推論やタスクに使います。
- **最高の段階（max）**。トークン消費を抑えず、最高の能力が求められるタスクに使います。

関連資料として、[プロンプト作成のベストプラクティス](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)を参照してください。

## ツールを使う場合の effort

ツール利用時には、effort がツール呼び出しとその前後の説明に作用します。低い段階には次の傾向があります。

- 複数の操作をまとめ、少ない呼び出しで処理する
- ツール呼び出しの回数が減る
- 前置きを省いてすぐに操作を始める
- 完了を短いメッセージで伝える

高い段階では、次のような挙動が見られる場合があります。

- ツールを多く呼び出す
- 操作を始める前に計画を説明する
- 変更点を詳しくまとめる
- コードのコメントを詳しく書く

## effort と推論

`thinking` は、Claude が回答前に[推論ブロック](https://platform.claude.com/docs/en/build-with-claude/thinking)で推論するかどうかを制御します。`effort` は、応答全体への労力の配分を調整します。適応型推論では、推論を行う頻度や深さもこの配分に含まれます。`adaptive` は `effort` の値には使えません。推論モードとして `adaptive` を指定します。

effort を高くすると、Claude が推論に入る頻度が増え、より長く推論します。ツールを繰り返し使う処理では、ツールの結果を処理するだけの後続リクエストなら、どの段階でも推論を省くことがあります。低い段階では、単純な問題の推論をすべて省くこともあります。設定を組み合わせる方法は[推論と effort（Thinking and effort）](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-effort)を参照してください。

effort に対応し、拡張推論だけを使うモデルは Claude Opus 4.5 です。effort と [`budget_tokens`](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) を組み合わせて使います。タスクに合わせて effort の段階を選び、必要な推論の深さから推論トークンの予算を設定します。

モデル別の推論機能は[モデル別の設定表](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#supported-models)を参照してください。推論の有効・無効にかかわらず effort を使えます。詳しくは [effort の仕組み（How effort works）](https://platform.claude.com/docs/en/build-with-claude/effort#how-effort-works)を参照してください。

## 会話の途中で effort を変更する

後続のターンから effort を変える方法は 2 つあります。メッセージごとに変更する方法ではプロンプトキャッシュを維持できます。次のリクエストでトップレベルの値を変える方法は、プロンプトキャッシュの一部または全部を無効にする場合があります。

### メッセージごとの effort

[メッセージごとの effort](https://platform.claude.com/docs/en/build-with-claude/effort-per-message) では、`messages` の `system` メッセージで新しい段階を指定します。

### 次のリクエストでトップレベルの effort を指定する

トップレベルの `output_config.effort` はリクエスト全体に適用されます。会話の後半を別の段階で処理するには、次のリクエストに新しい値を指定します。トップレベルの値がプロンプトの組み立てに影響するため、変えると過去のターンからキャッシュされた先頭部分が無効になる場合があります。長いセッションを通して[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)を利用し、モデルがメッセージごとの変更に対応していない場合は、最初に段階を選び、それを使い続けてください。

## ベストプラクティス

1. **effort を明示する。** API の既定値は `high` で、Claude Opus 5.5 と Claude Haiku 5.5 では `medium` です。どの段階から試すかはモデルと処理内容によって異なります。
2. **速度を重視する処理や単純な処理は low を使う。** 応答時間が重要な場合や単純なタスクでは、低い段階にすると時間と費用を大幅に減らせることがあります。
3. **自分の用途で評価する。** effort の効果はタスクごとに違います。本番に導入する前に、実際の用途で性能を確認します。
4. **タスクに合わせて段階を変える。** 処理の複雑さに応じて effort を調整します。単純な質問は低い段階で足りる場合があり、エージェント型コーディングや複雑な推論は高い段階が有利です。同じ会話の中で変える場合は次の項目を参照してください。
5. **キャッシュを使う会話ではトップレベルの値を固定する。** リクエスト間でトップレベルの effort を変えると、[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)の一部または全部が無効になることがあります。キャッシュヒットを前提とする会話では値を固定し、異なる用途の間で変えます。対応モデルでは、キャッシュを維持できる[メッセージごとの effort](https://platform.claude.com/docs/en/build-with-claude/effort-per-message)を使います。[推論とプロンプトキャッシュ（Thinking and prompt caching）](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-prompt-caching)を参照してください。

## 関連資料

[タスクの予算](https://platform.claude.com/docs/en/build-with-claude/task-budgets)

エージェントの処理全体についてトークン予算の目安を Claude に伝え、長い作業でモデルがトークン消費を調整できるようにします。

[推論の調整](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)

Claude が推論の有無と量を判断する適応型推論の仕組みと、effort やプロンプトで推論を調整する方法を説明します。

[推論](https://platform.claude.com/docs/en/build-with-claude/thinking)

推論の仕組み、Claude が既定で推論する条件、effort との関係を説明します。

## 提供状況

effort は一部のモデルで利用でき、データ保持なし（Zero Data Retention）と HIPAA 対応の対象です。

### 対応する API

#### [Messages API の利用](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)

- 常に利用できます。
- リクエストに `output_config.effort` を指定します。省略するとモデルの既定値が適用されます。

| 提供状況 | クラウドプラットフォーム | 対応モデル |
|---|---|---|
| 利用可能 | 対応するすべてのプラットフォーム | [Claude Fable 5.2](https://platform.claude.com/docs/en/models/fable-5-2/overview)、[Claude Mythos 5.2](https://platform.claude.com/docs/en/models/mythos-5-2/overview)、[Claude Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview)、[Claude Mythos 5.1](https://platform.claude.com/docs/en/models/mythos-5-1/overview)、[Claude Fable 5](https://platform.claude.com/docs/en/models/fable-5/overview)、[Claude Mythos 5](https://platform.claude.com/docs/en/models/mythos-5/overview)、Claude Mythos Preview、[Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview)、[Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview)、[Claude Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview)、[Claude Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview)、[Claude Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview)、[Claude Opus 4.8](https://platform.claude.com/docs/en/models/opus-4-8/overview)、[Claude Opus 4.7](https://platform.claude.com/docs/en/models/opus-4-7/overview)、[Claude Opus 4.6](https://platform.claude.com/docs/en/models/opus-4-6/overview)、[Claude Sonnet 4.6](https://platform.claude.com/docs/en/models/sonnet-4-6/overview)、[Claude Opus 4.5](https://platform.claude.com/docs/en/models/opus-4-5/overview) |

#### [Managed Agents の概要](https://platform.claude.com/docs/en/managed-agents/overview)

- 常に利用できます。
- エージェントのモデルオブジェクトか、セッションのモデル設定を上書きする箇所に `effort` を指定します。省略すると Managed Agents がモデルの既定値を補います。

| 提供状況 | クラウドプラットフォーム | 対応モデル |
|---|---|---|
| 利用可能 | Claude API、[Claude Platform on AWS の概要](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws) | [Claude Fable 5.2](https://platform.claude.com/docs/en/models/fable-5-2/overview)、[Claude Mythos 5.2](https://platform.claude.com/docs/en/models/mythos-5-2/overview)、[Claude Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview)、[Claude Mythos 5.1](https://platform.claude.com/docs/en/models/mythos-5-1/overview)、[Claude Fable 5](https://platform.claude.com/docs/en/models/fable-5/overview)、[Claude Mythos 5](https://platform.claude.com/docs/en/models/mythos-5/overview)、Claude Mythos Preview、[Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview)、[Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview)、[Claude Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview)、[Claude Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview)、[Claude Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview)、[Claude Opus 4.8](https://platform.claude.com/docs/en/models/opus-4-8/overview)、[Claude Opus 4.7](https://platform.claude.com/docs/en/models/opus-4-7/overview)、[Claude Opus 4.6](https://platform.claude.com/docs/en/models/opus-4-6/overview)、[Claude Sonnet 4.6](https://platform.claude.com/docs/en/models/sonnet-4-6/overview)、[Claude Opus 4.5](https://platform.claude.com/docs/en/models/opus-4-5/overview) |

### データの取り扱い

[データの取り扱いの概要](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#feature-eligibility)

| 項目 | データ保持なし | HIPAA |
|---|---|---|
| 状態 | 対象（[保持要件が個別に定められたモデル（Covered Models）](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements)を除く） | 対象 |

対象となるエンドポイント

- `effort` を指定した `/v1/messages`
