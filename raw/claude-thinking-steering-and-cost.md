---
url: "https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost"
title: "Steering thinking"
fetched_at: "2026-11-18T21:45:10+09:00"
source_sha256: "51ee50f844d7f5f8444e96828b66834d698a342eb57c719ad4dbf52087cf8dd6"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# 推論の調整

effort の段階、システムプロンプトでの指示、メッセージごとの調整によって Claude が推論する頻度と深さを変える方法と、推論の費用や料金について説明します。

この機能にデータ保持なし（Zero Data Retention、ZDR）がどう適用されるかは、[API とデータ保持](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)を参照してください。

Claude の推論は適応型です。モデルはリクエストごとに、推論するか、どの程度行うかを判断します。利用者が目的を示し、必要に応じて effort を指定すると、モデルは推論が役立ちそうな部分に処理を割り当てます。

この仕組みは、単純な依頼と複雑な依頼が混在する処理や、ステップごとに適した推論量が異なる長時間のエージェント作業に向いています。

推論を有効にする方法と出力の読み方は、[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)を参照してください。このページでは、Claude が推論するかどうかを決める仕組み、推論を調整する方法、それに伴うキャッシュ、費用、料金の仕組みを扱います。

## Claude が推論の要否を決める仕組み

推論の要否はモデルが判断します。Claude はリクエストごとに入力の複雑さを評価し、より深く推論すれば回答がよくなるかを判断します。単純な事実を尋ねる質問には推論ブロックを付けず直接答えることがあります。複数段階の数学の問題や難しいデバッグでは、より深い推論を行います。

Claude はリクエストごとに判断します。同じ会話でも推論するターンと省くターンがあり、推論を省いたターンには推論ブロックが含まれません。アプリケーションの処理では、各アシスタントターンの先頭に推論ブロックがあると仮定しないでください。

この判断を主に調整するのは [effort](https://platform.claude.com/docs/en/build-with-claude/effort) パラメーターです。Claude が推論する頻度や深さの目安になります。段階ごとの効果は、このページの [effort の段階](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#effort-levels)を参照してください。

Claude の推論の頻度を下げたい場合は、プロンプトで指示する前に effort の段階を下げます。

ツールの利用にも自動で推論を挟みます。Claude はツール呼び出しの間で推論し、得られた結果を評価してから次の行動を決められます。[ツール呼び出しの間に行う推論](https://platform.claude.com/docs/en/build-with-claude/thinking#interleaved-thinking)を参照してください。

推論設定と effort パラメーターの関係は、[推論と effort](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-effort)を参照してください。

## Claude が推論する頻度を調整する

Claude があるターンで推論するかどうかは、プロンプトでも調整できます。effort で全般的な傾向を設定したうえで、会話全体に適用するシステムプロンプトや、ユーザーターンの個別メッセージに自然言語の指示を加えられます。

2 つの方法は次の順で使います。

1. 用途で通常求める品質と応答時間のバランスに合う effort の段階を設定します。
2. その段階でも Claude が推論する条件が用途に合わない場合に限り、プロンプトに指示を加えます。

Claude Sonnet 5.5 と Claude Haiku 5.5 の推論を減らすには、effort の段階を下げます。Claude Sonnet 5.5 は、システムプロンプトで推論を減らすよう求めても、推論が安定して減るわけではありません。Anthropic のテストでは、Claude Haiku 5.5 にプロンプトで直接回答するよう求めても、推論を続けました。[Claude Sonnet 5.5 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#calibrate-effort)と [Claude Haiku 5.5 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5#use-effort-to-control-thinking)を参照してください。Claude Fable 5.2 でも、推論を減らすには effort の段階を下げます。Anthropic のテストでは、`medium` 以上で熟考を省いて直接回答するよう指示しても、モデルは推論を続けました。[Claude Fable 5.2 のプロンプトの書き方](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#calibrate-effort)を参照してください。

推論を使うためのプロンプト全般については、[推論とツール呼び出し間の推論を活用する](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#leverage-thinking-and-interleaved-thinking-capabilities)を参照してください。

### effort の段階

推論の調整には主に effort を使います。Claude が推論する頻度と深さは、段階に応じて変わります。

| effort の段階 | 推論の挙動 |
|---|---|
| `max` | Claude は最も積極的に、最も深く推論します。段階自体は推論の長さを制限しません。 |
| `xhigh` | Claude は `high` に比べて積極的に、より深く推論します。長時間にわたる探索に向きます。 |
| `high`（多くのモデルで既定） | Claude は推論が役立つリクエストの大半で推論し、複雑なタスクでは深く掘り下げます。 |
| `medium`（Claude Opus 5.5 と Claude Haiku 5.5 の既定） | Claude は中程度の推論を行います。単純な質問では推論を省く場合があります。 |
| `low` | Claude は推論を抑えます。速さを最優先する単純なタスクでは推論を省きます。 |

どの段階でも、Claude はリクエストごとに推論するかどうかを判断します。ツール利用のループでは、新しいユーザー入力の後の最初のリクエストで推論の大半を行うのが一般的です。`xhigh` や `max` でも、ツールの結果を処理するだけの後続リクエストでは推論を省くことがあります。会話が長くなるほど、リクエストあたりの推論量も減る傾向があります。どの段階でも、すべてのリクエストに推論ブロックが付く保証はありません。

この表は、段階ごとの推論の挙動を説明しています。用途に合う段階の選び方やモデル別の推奨は、effort ガイドの [effort パラメーターを調整する場面](https://platform.claude.com/docs/en/build-with-claude/effort#when-to-adjust-the-effort-parameter)を参照してください。

effort は `output_config.effort` に指定します。`thinking` オブジェクトの外側に置きます。言語別の詳しい例は [effort の指定方法](https://platform.claude.com/docs/en/build-with-claude/effort#basic-usage)を参照してください。

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 4096,
  "output_config": { "effort": "medium" },
  "messages": [{ "role": "user", "content": "..." }]
}
```

モデルによって指定できる段階は異なります。各モデルの対応段階の正確な情報は、effort ガイドの [effort の対応表](https://platform.claude.com/docs/en/build-with-claude/effort#effort-levels)を参照してください。

### システムプロンプトで指示する

システムプロンプトで指示すると、会話中のすべてのリクエストで、Claude が推論を始める条件が変わります。用途に対して推論が多すぎる場合は、次のような指示をシステムプロンプトに加えます。

```text
Extended thinking adds latency and should only be used when it
will meaningfully improve answer quality, typically for problems
that require multistep reasoning. When in doubt, respond directly.
```

推論を促す場合は、次のような表現を使います。

```text
This task involves multistep reasoning. Think carefully before responding.
```

指示の効果は文言に左右されることがあります。ある表現で期待どおりの挙動にならなければ、より直接的な表現を試します。

### メッセージ単位で指示する

システムプロンプトとは別に、ユーザーターンのメッセージごとに推論を調整できます。ユーザーメッセージに `"Please think hard before responding."` を付けると、そのターンで Claude が推論するよう促し、`"Answer directly without deliberating."` を付けると抑えるよう働きかけます。

会話中の一部のリクエストだけで長い推論が必要な場合は、メッセージ単位の指示が役立ちます。たとえばエージェントを動かすアプリケーションでは、計画を立てる段階で推論を促す文言を、定型的な確認では抑える文言を追加できます。システムプロンプトやターン間のリクエストパラメーターを変更する必要はありません。

Claude Haiku 5.5 と Claude Fable 5.2 は、推論を抑える文言で推論が安定して減るわけではありません。Anthropic のテストでは、Claude Fable 5.2 は `medium` 以上で指示を受けても推論を続けました。プラットフォームが対応していれば、これらのモデルで定型的なターンの推論を減らすには、[メッセージ単位の effort](https://platform.claude.com/docs/en/build-with-claude/effort-per-message) を使います。このベータ機能ではプロンプトキャッシュも維持されます。

### 実際の用途で調整の効果を確かめる

プロンプトでの調整はモデルの挙動を変えるため、ほかのプロンプト変更と同様に、本番に導入する前に測定します。実際の処理を代表するリクエストを、指示ありと指示なしで実行します。重要な事例について、推論を行う頻度（応答に推論ブロックがあるか）、出力トークン数、応答時間、回答の品質を比較します。

Claude の推論の頻度を減らすと、推論が役立つタスクでは品質が下がる場合があります。まず [effort](https://platform.claude.com/docs/en/build-with-claude/effort) を下げるのが一般に適しています。文言に左右される指示と比べ、段階ごとに調整された設定だからです。プロンプトでの調整を本番に導入する前に、実際の用途で影響を測定してください。

## 仕組み

Claude が推論を調整する仕組みは、ターンの検証、プロンプトキャッシュ、費用の上限の 3 点に影響します。

### ターンの検証

アシスタントターンは推論ブロックから始まる必要はありません。旧方式の手動の推論予算を使うモデルでは、推論が有効なリクエストの最後のアシスタントターンが推論ブロックから始まることを要求します。[手動モードでのターンの構造](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#turn-structure-in-manual-mode)を参照してください。

複数ターンのアプリケーションでは、次のような会話履歴を送り返せます。

- Claude が推論せず生成したアシスタントターンも、そのまま有効な履歴として使えます。
- 推論なしで始めた会話や、異なる推論設定を使った会話も、履歴を書き換えずに再開できます。
- 複数の出所からまとめた履歴も、各アシスタントターンの先頭に推論ブロックを挿入せずに検証を通せます。

ターンは推論ブロックなしで始められます。受け取った推論ブロックは変更せずに送り返します。ツール利用中は、ブロックに Claude がツールを呼んだ理由が含まれるため、特に重要です。規則の詳細は[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)を参照してください。

### プロンプトキャッシュ

連続するリクエストで推論設定と effort の段階を維持すると、プロンプトキャッシュを再利用できます。詳しい規則は[推論とプロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-and-prompt-caching)を参照してください。適用される effort はプロンプトに反映されるため、リクエスト間で値を変えると、キャッシュの区切りが無効になることがあります。旧方式の [`budget_tokens`](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#extended-thinking-with-prompt-caching) を[対応モデル](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#supported-models)で変更した場合も同様です。`effort` にモデルの既定値を明示しても、省略した場合と同じ扱いになり、キャッシュは無効になりません。

実際の運用では、会話ごとに推論設定とトップレベルの effort の段階を決めて維持します。一部のターンで推論を増減する場合は、[メッセージ単位の effort](https://platform.claude.com/docs/en/build-with-claude/effort-per-message) を[対応モデル](https://platform.claude.com/docs/en/build-with-claude/effort-per-message#feature-availability)で使います。この機能はベータ版です。[メッセージ単位のプロンプトでの指示](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#per-message-steering)も使えます。どちらでも変更前のキャッシュの区切りは維持されます。推論設定やトップレベルの effort を変更した場合は、それらの区切りが無効になることがあります。

以下に、複数ターンでキャッシュが無効になることを確かめられるスクリプトを示します。

#### effort を変えるとプロンプトキャッシュが無効になる場合がある

**cURL**

この処理には、シェルコマンド 1 回で書ける以上の処理が必要です。Anthropic SDK で実行してください。ターンごとの HTTP リクエストは、[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)の例に従います。

**CLI**

この処理には、シェルコマンド 1 回で書ける以上の処理が必要です。Anthropic SDK で実行してください。ターンごとの CLI コマンドは、[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)の例に従います。

```python
import requests

client = Anthropic()


def fetch_article_content(url):
    text = requests.get(url).text
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


# Fetch the content of the article
book_url = "https://www.gutenberg.org/cache/epub/1342/pg1342.txt"
book_content = fetch_article_content(book_url)
# Use just enough text for caching (first few chapters)
LARGE_TEXT = book_content[:10000]

# No system prompt: caching in messages instead
MESSAGES = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": LARGE_TEXT,
                "cache_control": {"type": "ephemeral"},
            },
            {"type": "text", "text": "Analyze the tone of this passage."},
        ],
    }
]

# First request: establish cache
print("First request - establishing cache")
response1 = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    messages=MESSAGES,
)

print(f"First response usage: {response1.usage}")

MESSAGES.append({"role": "assistant", "content": response1.content})
MESSAGES.append({"role": "user", "content": "Analyze the characters in this passage."})

# Second request: same configuration (cache hit expected)
print("\nSecond request - same configuration (cache hit expected)")
response2 = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    messages=MESSAGES,
)

print(f"Second response usage: {response2.usage}")

MESSAGES.append({"role": "assistant", "content": response2.content})
MESSAGES.append({"role": "user", "content": "Analyze the setting in this passage."})

# Third request: different effort level (cache miss expected)
print("\nThird request - different effort level (cache miss expected)")
response3 = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    output_config={"effort": "low"},
    messages=MESSAGES,
)

print(f"Third response usage: {response3.usage}")
```

```typescript
const client = new Anthropic();

async function fetchArticleContent(url: string): Promise<string> {
  const response = await fetch(url);
  const text = await response.text();
  const lines = text.split("\n").map((line) => line.trim());
  return lines.filter((line) => line).join("\n");
}

const bookUrl = "https://www.gutenberg.org/cache/epub/1342/pg1342.txt";
const bookContent = await fetchArticleContent(bookUrl);
const LARGE_TEXT = bookContent.substring(0, 10000);

// No system prompt: caching in messages instead
const messages: Anthropic.MessageParam[] = [
  {
    role: "user",
    content: [
      {
        type: "text",
        text: LARGE_TEXT,
        cache_control: { type: "ephemeral" }
      },
      {
        type: "text",
        text: "Analyze the tone of this passage."
      }
    ]
  }
];

// First request: establish cache
console.log("First request - establishing cache");
const response1 = await client.messages.create({
  model: "claude-opus-5-5",
  max_tokens: 16000,
  thinking: { type: "adaptive" },
  messages
});

console.log("First response usage: ", response1.usage);

messages.push(
  { role: "assistant", content: response1.content },
  { role: "user", content: "Analyze the characters in this passage." }
);

// Second request: same configuration (cache hit expected)
console.log("\nSecond request - same configuration (cache hit expected)");
const response2 = await client.messages.create({
  model: "claude-opus-5-5",
  max_tokens: 16000,
  thinking: { type: "adaptive" },
  messages
});

console.log("Second response usage: ", response2.usage);

messages.push(
  { role: "assistant", content: response2.content },
  { role: "user", content: "Analyze the setting in this passage." }
);

// Third request: different effort level (cache miss expected)
console.log("\nThird request - different effort level (cache miss expected)");
const response3 = await client.messages.create({
  model: "claude-opus-5-5",
  max_tokens: 16000,
  thinking: { type: "adaptive" },
  output_config: { effort: "low" },
  messages
});

console.log("Third response usage: ", response3.usage);
```

```csharp
AnthropicClient client = new();

string bookUrl = "https://www.gutenberg.org/cache/epub/1342/pg1342.txt";
string bookContent = await FetchArticleContent(bookUrl);
string largeText = bookContent.Substring(0, Math.Min(10000, bookContent.Length));

Console.WriteLine("First request - establishing cache");
var parameters1 = new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigAdaptive(),
    Messages =
    [
        new UserMessageParam
        {
            Content = new List<ContentBlockParam>
            {
                new ContentBlockParam(new TextBlockParam()
                {
                    Text = largeText,
                    CacheControl = new CacheControlEphemeral(),
                }),
                new ContentBlockParam(new TextBlockParam()
                {
                    Text = "Analyze the tone of this passage."
                }),
            }
        }
    ]
};

var response1 = await client.Messages.Create(parameters1);
Console.WriteLine($"First response usage: {response1.Usage}");

Console.WriteLine("\nSecond request - same configuration (cache hit expected)");
var parameters2 = new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigAdaptive(),
    Messages =
    [
        new UserMessageParam
        {
            Content = new List<ContentBlockParam>
            {
                new ContentBlockParam(new TextBlockParam()
                {
                    Text = largeText,
                    CacheControl = new CacheControlEphemeral(),
                }),
                new ContentBlockParam(new TextBlockParam()
                {
                    Text = "Analyze the tone of this passage."
                }),
            }
        },
        new AssistantMessageParam
        {
            Content = response1.Content.Select(block => new ContentBlockParam(block.Json)).ToList()
        },
        new UserMessageParam { Content = "Analyze the characters in this passage." }
    ]
};

var response2 = await client.Messages.Create(parameters2);
Console.WriteLine($"Second response usage: {response2.Usage}");

Console.WriteLine("\nThird request - different effort level (cache miss expected)");
var parameters3 = new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigAdaptive(),
    OutputConfig = new OutputConfig
    {
        Effort = Effort.Low
    },
    Messages =
    [
        new UserMessageParam
        {
            Content = new List<ContentBlockParam>
            {
                new ContentBlockParam(new TextBlockParam()
                {
                    Text = largeText,
                    CacheControl = new CacheControlEphemeral(),
                }),
                new ContentBlockParam(new TextBlockParam()
                {
                    Text = "Analyze the tone of this passage."
                }),
            }
        },
        new AssistantMessageParam
        {
            Content = response1.Content.Select(block => new ContentBlockParam(block.Json)).ToList()
        },
        new UserMessageParam { Content = "Analyze the characters in this passage." },
        new AssistantMessageParam
        {
            Content = response2.Content.Select(block => new ContentBlockParam(block.Json)).ToList()
        },
        new UserMessageParam { Content = "Analyze the setting in this passage." }
    ]
};

var response3 = await client.Messages.Create(parameters3);
Console.WriteLine($"Third response usage: {response3.Usage}");

static async Task<string> FetchArticleContent(string url)
{
    using HttpClient httpClient = new();
    string content = await httpClient.GetStringAsync(url);
    return content;
}
```

```go
client := anthropic.NewClient()

bookURL := "https://www.gutenberg.org/cache/epub/1342/pg1342.txt"
bookContent, err := fetchArticleContent(bookURL)
if err != nil {
	log.Fatal(err)
}

largeText := bookContent
if len(largeText) > 10000 {
	largeText = largeText[:10000]
}

// No system prompt: caching in messages instead
messages := []anthropic.MessageParam{
	anthropic.NewUserMessage(
		anthropic.ContentBlockParamUnion{OfText: &anthropic.TextBlockParam{
			Text:         largeText,
			CacheControl: anthropic.NewCacheControlEphemeralParam(),
		}},
		anthropic.NewTextBlock("Analyze the tone of this passage."),
	),
}

// First request: establish cache
fmt.Println("First request - establishing cache")
response1, err := client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeOpus5_5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{},
	},
	Messages: messages,
})
if err != nil {
	log.Fatal(err)
}
fmt.Printf("First response usage: %s\n", response1.Usage.RawJSON())

messages = append(messages, response1.ToParam())
messages = append(messages, anthropic.NewUserMessage(anthropic.NewTextBlock("Analyze the characters in this passage.")))

// Second request: same configuration (cache hit expected)
fmt.Println("\nSecond request - same configuration (cache hit expected)")
response2, err := client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeOpus5_5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{},
	},
	Messages: messages,
})
if err != nil {
	log.Fatal(err)
}
fmt.Printf("Second response usage: %s\n", response2.Usage.RawJSON())

messages = append(messages, response2.ToParam())
messages = append(messages, anthropic.NewUserMessage(anthropic.NewTextBlock("Analyze the setting in this passage.")))

// Third request: different effort level (cache miss expected)
fmt.Println("\nThird request - different effort level (cache miss expected)")
response3, err := client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeOpus5_5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{},
	},
	OutputConfig: anthropic.OutputConfigParam{
		Effort: anthropic.OutputConfigEffortLow,
	},
	Messages: messages,
})
if err != nil {
	log.Fatal(err)
}
fmt.Printf("Third response usage: %s\n", response3.Usage.RawJSON())
```

```java
import com.anthropic.models.messages.CacheControlEphemeral;
// ...
void main() throws Exception {
    AnthropicClient client = AnthropicOkHttpClient.fromEnv();

    String bookUrl = "https://www.gutenberg.org/cache/epub/1342/pg1342.txt";
    String bookContent = fetchArticleContent(bookUrl);
    String largeText = bookContent.substring(0, Math.min(10000, bookContent.length()));

    // First request: establish cache
    IO.println("First request - establishing cache");
    MessageCreateParams params1 = MessageCreateParams.builder()
        .model(Model.CLAUDE_OPUS_5_5)
        .maxTokens(16000L)
        .thinking(ThinkingConfigAdaptive.builder().build())
        .addUserMessageOfContentBlockParams(List.of(
            ContentBlockParam.ofText(TextBlockParam.builder()
                .text(largeText)
                .cacheControl(CacheControlEphemeral.builder().build())
                .build()),
            ContentBlockParam.ofText(TextBlockParam.builder()
                .text("Analyze the tone of this passage.")
                .build())
        ))
        .build();

    Message response1 = client.messages().create(params1);
    IO.println("First response usage: " + response1.usage());

    // Second request: same configuration (cache hit expected)
    IO.println("\nSecond request - same configuration (cache hit expected)");
    MessageCreateParams params2 = MessageCreateParams.builder()
        .model(Model.CLAUDE_OPUS_5_5)
        .maxTokens(16000L)
        .thinking(ThinkingConfigAdaptive.builder().build())
        .addUserMessageOfContentBlockParams(List.of(
            ContentBlockParam.ofText(TextBlockParam.builder()
                .text(largeText)
                .cacheControl(CacheControlEphemeral.builder().build())
                .build()),
            ContentBlockParam.ofText(TextBlockParam.builder()
                .text("Analyze the tone of this passage.")
                .build())
        ))
        .addAssistantMessageOfContentBlockParams(response1.content().stream()
            .map(block -> block.toParam())
            .collect(Collectors.toList()))
        .addUserMessage("Analyze the characters in this passage.")
        .build();

    Message response2 = client.messages().create(params2);
    IO.println("Second response usage: " + response2.usage());

    // Third request: different effort level (cache miss expected)
    IO.println("\nThird request - different effort level (cache miss expected)");
    MessageCreateParams params3 = MessageCreateParams.builder()
        .model(Model.CLAUDE_OPUS_5_5)
        .maxTokens(16000L)
        .thinking(ThinkingConfigAdaptive.builder().build())
        .outputConfig(OutputConfig.builder()
            .effort(OutputConfig.Effort.LOW)
            .build())
        .addUserMessageOfContentBlockParams(List.of(
            ContentBlockParam.ofText(TextBlockParam.builder()
                .text(largeText)
                .cacheControl(CacheControlEphemeral.builder().build())
                .build()),
            ContentBlockParam.ofText(TextBlockParam.builder()
                .text("Analyze the tone of this passage.")
                .build())
        ))
        .addAssistantMessageOfContentBlockParams(response1.content().stream()
            .map(block -> block.toParam())
            .collect(Collectors.toList()))
        .addUserMessage("Analyze the characters in this passage.")
        .addAssistantMessageOfContentBlockParams(response2.content().stream()
            .map(block -> block.toParam())
            .collect(Collectors.toList()))
        .addUserMessage("Analyze the setting in this passage.")
        .build();

    Message response3 = client.messages().create(params3);
    IO.println("Third response usage: " + response3.usage());
}

String fetchArticleContent(String url) throws Exception {
    HttpClient client = HttpClient.newHttpClient();
    HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create(url))
        .build();
    HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
    return response.body();
}
```

```php
function fetchArticleContent($url)
{
    $content = file_get_contents($url);
    $lines = explode("\n", $content);
    $cleanedLines = array_filter(array_map('trim', $lines));
    return implode("\n", $cleanedLines);
}

$client = new Client();

$bookUrl = 'https://www.gutenberg.org/cache/epub/1342/pg1342.txt';
$bookContent = fetchArticleContent($bookUrl);
$largeText = substr($bookContent, 0, 10000);

echo "First request - establishing cache\n";
$response1 = $client->messages->create(
    maxTokens: 16000,
    messages: [[
        'role' => 'user',
        'content' => [
            [
                'type' => 'text',
                'text' => $largeText,
                'cache_control' => ['type' => 'ephemeral']
            ],
            [
                'type' => 'text',
                'text' => 'Analyze the tone of this passage.'
            ]
        ]
    ]],
    model: Model::CLAUDE_OPUS_5_5,
    thinking: ['type' => 'adaptive'],
);

echo 'First response usage: ' . json_encode($response1->usage) . "\n";

echo "\nSecond request - same configuration (cache hit expected)\n";
$response2 = $client->messages->create(
    maxTokens: 16000,
    messages: [
        [
            'role' => 'user',
            'content' => [
                [
                    'type' => 'text',
                    'text' => $largeText,
                    'cache_control' => ['type' => 'ephemeral']
                ],
                [
                    'type' => 'text',
                    'text' => 'Analyze the tone of this passage.'
                ]
            ]
        ],
        [
            'role' => 'assistant',
            'content' => $response1->content
        ],
        [
            'role' => 'user',
            'content' => 'Analyze the characters in this passage.'
        ]
    ],
    model: Model::CLAUDE_OPUS_5_5,
    thinking: ['type' => 'adaptive'],
);

echo 'Second response usage: ' . json_encode($response2->usage) . "\n";

echo "\nThird request - different effort level (cache miss expected)\n";
$response3 = $client->messages->create(
    maxTokens: 16000,
    messages: [
        [
            'role' => 'user',
            'content' => [
                [
                    'type' => 'text',
                    'text' => $largeText,
                    'cache_control' => ['type' => 'ephemeral']
                ],
                [
                    'type' => 'text',
                    'text' => 'Analyze the tone of this passage.'
                ]
            ]
        ],
        [
            'role' => 'assistant',
            'content' => $response1->content
        ],
        [
            'role' => 'user',
            'content' => 'Analyze the characters in this passage.'
        ],
        [
            'role' => 'assistant',
            'content' => $response2->content
        ],
        [
            'role' => 'user',
            'content' => 'Analyze the setting in this passage.'
        ]
    ],
    model: Model::CLAUDE_OPUS_5_5,
    thinking: ['type' => 'adaptive'],
    outputConfig: ['effort' => 'low'],
);

echo 'Third response usage: ' . json_encode($response3->usage) . "\n";
```

```ruby
require "net/http"
require "uri"

def fetch_article_content(url)
  uri = URI.parse(url)
  response = Net::HTTP.get_response(uri)
  text = response.body

  lines = text.split("\n").map(&:strip)
  lines.reject(&:empty?).join("\n")
end

client = Anthropic::Client.new

book_url = "https://www.gutenberg.org/cache/epub/1342/pg1342.txt"
book_content = fetch_article_content(book_url)
large_text = book_content[0...10000]

puts "First request - establishing cache"
response1 = client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 16000,
  thinking: {
    type: "adaptive"
  },
  messages: [{
    role: "user",
    content: [
      {
        type: "text",
        text: large_text,
        cache_control: { type: "ephemeral" }
      },
      {
        type: "text",
        text: "Analyze the tone of this passage."
      }
    ]
  }]
)

puts "First response usage: #{response1.usage}"

puts "\nSecond request - same configuration (cache hit expected)"
response2 = client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 16000,
  thinking: {
    type: "adaptive"
  },
  messages: [
    {
      role: "user",
      content: [
        {
          type: "text",
          text: large_text,
          cache_control: { type: "ephemeral" }
        },
        {
          type: "text",
          text: "Analyze the tone of this passage."
        }
      ]
    },
    {
      role: "assistant",
      content: response1.content
    },
    {
      role: "user",
      content: "Analyze the characters in this passage."
    }
  ]
)

puts "Second response usage: #{response2.usage}"

puts "\nThird request - different effort level (cache miss expected)"
response3 = client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 16000,
  thinking: {
    type: "adaptive"
  },
  output_config: {
    effort: "low"
  },
  messages: [
    {
      role: "user",
      content: [
        {
          type: "text",
          text: large_text,
          cache_control: { type: "ephemeral" }
        },
        {
          type: "text",
          text: "Analyze the tone of this passage."
        }
      ]
    },
    {
      role: "assistant",
      content: response1.content
    },
    {
      role: "user",
      content: "Analyze the characters in this passage."
    },
    {
      role: "assistant",
      content: response2.content
    },
    {
      role: "user",
      content: "Analyze the setting in this passage."
    }
  ]
)

puts "Third response usage: #{response3.usage}"
```

以下はスクリプトの出力です。数値は実行によって多少異なります。

```text
First request - establishing cache
First response usage: { cache_creation_input_tokens: 3546, cache_read_input_tokens: 0, input_tokens: 15, output_tokens: 1033 }

Second request - same configuration (cache hit expected)
Second response usage: { cache_creation_input_tokens: 0, cache_read_input_tokens: 3546, input_tokens: 1062, output_tokens: 1630 }

Third request - different effort level (cache miss expected)
Third response usage: { cache_creation_input_tokens: 3546, cache_read_input_tokens: 0, input_tokens: 2706, output_tokens: 1468 }
```

キャッシュの区切りが messages 配列にある例では、Claude Opus 5.5 の既定値である `medium` から `low` に effort を変えると、区切りが無効になります。2 回目のリクエストではキャッシュをすべて読み出せましたが、3 回目では `cache_creation_input_tokens=3546`、`cache_read_input_tokens=0` になっています。

### 費用を調整する

推論専用のトークン予算は指定しません。費用は次の 2 つの設定で調整します。

- `max_tokens` は、推論と回答テキストを合計したリクエストの総出力の厳密な上限です。Claude はこの上限を超えて生成しません。ツールを繰り返し呼ぶターンでは、ターン内のリクエストごとに `max_tokens` があるため、ターン全体の消費量をこの値で制限することはできません。
- `effort` は、出力のうち推論にどの程度割り当てるかの目安です。Claude の挙動に影響しますが、トークン数は保証しません。

推論は `max_tokens` に含まれるため、推論と回答の両方に必要な分を確保します。推論なしの回答に合わせて設定した `max_tokens` では、難しいリクエストで Claude が推論すると、足りなくなることがあります。

effort が `high` 以上では Claude が長く推論する場合があり、上限に達しやすくなります。応答の停止理由が [`stop_reason: "max_tokens"`](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#stopped-at-max-tokens) なら、次の 2 つの対応があります。

- `max_tokens` を上げ、推論と回答の両方に使える出力枠を広げます。
- effort の段階を下げて Claude の推論量を減らし、回答テキストに使う出力枠を残します。

どちらが適しているかは、途中で切れた応答にその推論が必要だったかで決まります。そのリクエストの品質が重要なら上限を上げ、推論が長すぎたなら effort を下げます。

## 料金の仕組み

推論を使う場合は、次のトークンが課金対象になります。

- Claude が推論で使ったトークン。出力トークンとして課金されます。
- 過去のアシスタントターンからコンテキストに残る推論ブロック。[既定の保持範囲](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-block-preservation-by-model)に従い、全ターンを保持するモデルではすべてのターン分、それ以外では直近のターン分が残ります。入力トークンとして課金されます。
- 通常のテキスト出力のトークン。

推論が有効なとき、API はこの機能向けのシステムプロンプトを自動的に追加します。

`display` の設定によって見える内容は変わります。課金対象は同じです。

|  | `display: "summarized"` | `display: "omitted"` |
|---|---|---|
| **入力トークン** | 元のリクエストのトークン | 要約時と同じ |
| **出力トークン（課金）** | Claude が内部で生成した推論トークンの全量 | 要約時と同じ |
| **出力トークン（表示）** | 要約された推論のテキスト | 推論トークンは 0（`thinking` フィールドは空） |
| **要約の生成** | 料金はかかりません | 該当しません |

課金対象の出力トークン数は、応答で見えるトークン数と**一致しません**。課金されるのは、応答に見えている推論内容の分だけではなく、推論過程の全量です。

課金対象の出力トークンのうち内部推論に使った数は、応答の `usage.output_tokens_details.thinking_tokens` で確認できます。この値は本文に返った要約の長さではなく、モデルが生成した推論の全量を表し、常に `output_tokens` 以下です。`output_tokens` からこの値を引くと、推論以外の出力の概算が得られます。ストリーミングでは、この内訳は最後の `message_delta` イベントにだけ含まれます。

```json
{
  "usage": {
    "input_tokens": 25,
    "output_tokens": 348,
    "output_tokens_details": {
      "thinking_tokens": 312
    }
  }
}
```

`output_tokens` が、課金に使う全出力の正式な合計です。`output_tokens_details` は使用量を把握するための読み取り専用の内訳です。基本料金、キャッシュへの書き込みと読み出し、出力トークンを含む料金の詳細は[料金表](https://platform.claude.com/docs/en/about-claude/pricing)を参照してください。

## 関連資料

[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)

推論を有効にし、推論の出力を読み、モデルごとの対応状況を確認します。

[ツールと複数ターンの処理における推論](https://platform.claude.com/docs/en/build-with-claude/thinking-tool-workflows)

ツール呼び出しをまたいで推論ブロックを保持し、複数ターンの会話で推論を扱います。

[Effort](https://platform.claude.com/docs/en/build-with-claude/effort)

リクエストごとに、Claude が推論と応答の出力にどれだけトークンを割り当てるかを調整します。
