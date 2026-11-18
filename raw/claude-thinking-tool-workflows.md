---
url: "https://platform.claude.com/docs/en/build-with-claude/thinking-tool-workflows"
title: "Thinking in tool and multi-turn workflows"
fetched_at: "2026-11-18T21:57:35+09:00"
source_sha256: "e39ce2a8889c37975c16296d1afec0a267863d88ff81db8d27b93644a81781ad"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# ツール利用と複数ターンの処理における推論

2 回のリクエストでツールを呼び出し、推論ブロックを保持して結果を返すまでの流れを確認します。ツール呼び出しの間に推論を行うと、処理の流れがどう変わるかも説明します。

この機能にデータ保持なし（Zero Data Retention、ZDR）がどう適用されるかは、[API とデータ保持](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)を参照してください。

このページでは、推論を有効にしてツールの呼び出しと結果の返送を 2 回のリクエストで行う例を取り上げます。Claude は推論を行い、ツールの呼び出しを求め、結果を受け取って回答を完成させます。各手順で、推論ブロックを正しく扱うコードを示します。詳しい規則は Thinking の[ツール利用時の推論](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-with-tool-use)と[推論ブロックを保持する](https://platform.claude.com/docs/en/build-with-claude/thinking#preserving-thinking-blocks)を参照してください。

## この手順で守る規則

各項目から、規則の詳しい説明を参照できます。

- [手動モードではツール選択を `auto` か `none` にする](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-with-tool-use)。手動の拡張推論（`thinking: {type: "enabled"}`）でツール利用を強制する `tool_choice` を指定すると、エラーになります。
- [適応型推論で選んだモデルがツール利用の強制に対応するかを確認する](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-with-tool-use)。適応型推論では、動作がモデルによって異なります。
  - **Claude Opus 5.5、Claude Sonnet 5.5、Claude Fable 5.2、Claude Mythos 5.2、Claude Fable 5.1、Claude Mythos 5.1**。ツール利用を強制すると 400 エラーが返ります。
  - **その他のモデル**。ツール利用の強制が受理されると、推論は省かれ、応答はツール呼び出しから始まります。
- [1 つのアシスタントターンでは同じ推論設定を使う](https://platform.claude.com/docs/en/build-with-claude/thinking#thinking-with-tool-use)。ツールを呼び出して結果を返すループは 1 つのアシスタントターンなので、設定を変えるのはターンの区切りです。
- [推論ブロックを完全な形で変更せずに送り返す](https://platform.claude.com/docs/en/build-with-claude/thinking#preserving-thinking-blocks)。ツールの結果を返すときは、アシスタントメッセージに含まれていた推論ブロックも一緒に送ります。
- [アシスタントメッセージを受信したとおりに送り返す](https://platform.claude.com/docs/en/build-with-claude/thinking#preserving-thinking-blocks)。推論ブロックを落とすと、エラーが出ない場合でも、そのブロックに含まれる推論が失われます。

例では適応型推論を使います。Claude Opus 4.5、Claude Sonnet 4.5、Claude Haiku 4.5 およびそれ以前の Claude 4 モデルでは、`thinking: {type: "enabled", budget_tokens: N}` に置き換えます。アシスタントターンの送り返し方は同じです。

## 2 回のリクエストでツール利用を一往復させる

この例では `get_weather` ツールを定義し、Claude に推論とツール呼び出しの要求を行わせます。結果を返す際は、推論ブロックを含むアシスタントターンの内容を受信したとおりに送り返します。

### ツールを指定して最初のリクエストを送る

適応型推論を有効にし、ツールを定義してリクエストを送ります。`thinking` パラメーター以外は、通常の[ツール利用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)と同じです。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -d '{
    "model": "claude-opus-5-5",
    "max_tokens": 16000,
    "thinking": {"type": "adaptive"},
    "tools": [{
      "name": "get_weather",
      "description": "Get current weather for a location",
      "input_schema": {
        "type": "object",
        "properties": {
          "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
      }
    }],
    "messages": [{"role": "user", "content": "What is the weather in Paris?"}]
  }'
```

```bash
ant messages create <<'YAML'
model: claude-opus-5-5
max_tokens: 16000
thinking:
  type: adaptive
tools:
  - name: get_weather
    description: Get current weather for a location
    input_schema:
      type: object
      properties:
        location:
          type: string
          description: City name
      required:
        - location
messages:
  - role: user
    content: "What's the weather in Paris?"
YAML
```

```python
client = anthropic.Anthropic()

weather_tool = {
    "name": "get_weather",
    "description": "Get current weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "City name"}},
        "required": ["location"],
    },
}

# First request: Claude responds with thinking and tool request
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    tools=[weather_tool],
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
)
print(response)
```

```typescript
const client = new Anthropic();

const weatherTool: Anthropic.Tool = {
  name: "get_weather",
  description: "Get current weather for a location",
  input_schema: {
    type: "object",
    properties: {
      location: { type: "string", description: "City name" }
    },
    required: ["location"]
  }
};

// First request: Claude responds with thinking and tool request
const response = await client.messages.create({
  model: "claude-opus-5-5",
  max_tokens: 16000,
  thinking: {
    type: "adaptive"
  },
  tools: [weatherTool],
  messages: [{ role: "user", content: "What's the weather in Paris?" }]
});
console.log(response);
```

```csharp
AnthropicClient client = new();

var weatherTool = new ToolUnion(new Tool()
{
    Name = "get_weather",
    Description = "Get current weather for a location",
    InputSchema = new InputSchema()
    {
        Properties = new Dictionary<string, JsonElement>
        {
            ["location"] = JsonSerializer.SerializeToElement(new { type = "string", description = "City name" }),
        },
        Required = ["location"],
    },
});

var parameters = new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigAdaptive(),
    Tools = [weatherTool],
    Messages = [new UserMessageParam { Content = "What's the weather in Paris?" }]
};

var message = await client.Messages.Create(parameters);
Console.WriteLine(message);
```

```go
client := anthropic.NewClient()

weatherTool := anthropic.ToolUnionParam{
	OfTool: &anthropic.ToolParam{
		Name:        "get_weather",
		Description: anthropic.String("Get current weather for a location"),
		InputSchema: anthropic.ToolInputSchemaParam{
			Properties: map[string]any{
				"location": map[string]any{
					"type":        "string",
					"description": "City name",
				},
			},
			Required: []string{"location"},
		},
	},
}

response, err := client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeOpus5_5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{},
	},
	Tools: []anthropic.ToolUnionParam{weatherTool},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("What's the weather in Paris?")),
	},
})
if err != nil {
	log.Fatal(err)
}
fmt.Println(response)
```

```java
import com.anthropic.models.messages.ThinkingConfigAdaptive;
// ...
    AnthropicClient client = AnthropicOkHttpClient.fromEnv();

    MessageCreateParams params = MessageCreateParams.builder()
        .model(Model.CLAUDE_OPUS_5_5)
        .maxTokens(16000L)
        .thinking(ThinkingConfigAdaptive.builder().build())
        .addTool(Tool.builder()
            .name("get_weather")
            .description("Get current weather for a location")
            .inputSchema(Tool.InputSchema.builder()
                .properties(JsonValue.from(Map.of(
                    "location", Map.of("type", "string", "description", "City name")
                )))
                .required(List.of("location"))
                .build())
            .build())
        .addUserMessage("What's the weather in Paris?")
        .build();

    Message response = client.messages().create(params);
    IO.println(response);
```

```php
$client = new Client();

$weatherTool = [
    'name' => 'get_weather',
    'description' => 'Get current weather for a location',
    'input_schema' => [
        'type' => 'object',
        'properties' => [
            'location' => ['type' => 'string', 'description' => 'City name']
        ],
        'required' => ['location']
    ]
];

$message = $client->messages->create(
    maxTokens: 16000,
    messages: [
        ['role' => 'user', 'content' => "What's the weather in Paris?"]
    ],
    model: Model::CLAUDE_OPUS_5_5,
    thinking: ['type' => 'adaptive'],
    tools: [$weatherTool],
);
echo $message;
```

```ruby
client = Anthropic::Client.new

weather_tool = {
  name: "get_weather",
  description: "Get current weather for a location",
  input_schema: {
    type: "object",
    properties: {
      location: { type: "string", description: "City name" }
    },
    required: ["location"]
  }
}

message = client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 16000,
  thinking: {
    type: "adaptive"
  },
  tools: [weather_tool],
  messages: [
    { role: "user", content: "What's the weather in Paris?" }
  ]
)
puts message
```

### 送り返す content 配列を確保する

推論を行った場合は、応答の内容に `thinking` ブロックと `tool_use` ブロックが含まれます。単純なリクエストでは、適応型推論で推論ブロックが省かれる場合があります。ツール呼び出し前に Claude が書く説明は、`text` ブロックとして返ります。[進捗報告](https://platform.claude.com/docs/en/build-with-claude/thinking#progress-updates)を出すモデルでは、別の `thinking` ブロックとして返る場合があります。次の手順で配列をそのまま送り返すので、変更せず保持します。

出力例のように推論テキストを表示するには、リクエストに `display: "summarized"` を加えます。Claude Opus 5.5 など、表示の既定値が省略のモデルでは、指定しなければ `thinking` フィールドが空の文字列で返り、`signature` だけに値が入ります。いずれの場合も、応答の内容を収めた配列は変更せず送り返します。[推論の表示を設定する](https://platform.claude.com/docs/en/build-with-claude/thinking#controlling-thinking-display)を参照してください。

```json
{
  "content": [
    {
      "type": "thinking",
      "thinking": "The user wants to know the current weather in Paris. I have access to a function `get_weather`...",
      "signature": "BDaL4VrbR2Oj0hO4XpJxT28J5T...."
    },
    {
      "type": "tool_use",
      "id": "toolu_01CswdEQBMshySk6Y9DFKrfq",
      "name": "get_weather",
      "input": {
        "location": "Paris"
      }
    }
  ]
}
```

### ツールの結果と元のアシスタントターンを返す

クライアント側でツールを実行し、会話に 2 つのメッセージを追加して 2 回目のリクエストを送ります。1 つ目は、受け取った内容をそのまま送り返すアシスタントメッセージです。推論ブロックを変更せず `tool_use` ブロックと一緒に含めます。2 つ目は、`tool_result` を含むユーザーメッセージです。

各コード例は単独で実行できます。最初のリクエストを実行し、その応答を受け取ってすぐに後続のリクエストを送ります。

**cURL**

この処理にはシェルコマンド 1 回で書ける以上の処理が必要です。[Anthropic SDK](https://platform.claude.com/docs/en/cli-sdks-libraries/overview) で実行してください。

**CLI**

この処理にはシェルコマンド 1 回で書ける以上の処理が必要です。[Anthropic SDK](https://platform.claude.com/docs/en/cli-sdks-libraries/overview) で実行してください。

```python
client = anthropic.Anthropic()
weather_tool = {
    "name": "get_weather",
    "description": "Get current weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "City name"}},
        "required": ["location"],
    },
}
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    tools=[weather_tool],
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
)
# Extract the tool use block to get its ID for the tool result
tool_use_block = next(block for block in response.content if block.type == "tool_use")

# This is where your actual weather API call would go
# Pretend this is what the weather API returns
weather_data = {"temperature": 88}

# Second request: include the assistant turn and the tool result
continuation = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    tools=[weather_tool],
    messages=[
        {"role": "user", "content": "What's the weather in Paris?"},
        # Echo the assistant content exactly as received. When a thinking
        # block is present, it must accompany the tool_use block.
        {"role": "assistant", "content": response.content},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": f"Current temperature: {weather_data['temperature']}°F",
                }
            ],
        },
    ],
)
print(continuation)
```

```typescript
const client = new Anthropic();

const weatherTool: Anthropic.Tool = {
  name: "get_weather",
  description: "Get current weather for a location",
  input_schema: {
    type: "object",
    properties: {
      location: { type: "string", description: "City name" }
    },
    required: ["location"]
  }
};

const response = await client.messages.create({
  model: "claude-opus-5-5",
  max_tokens: 16000,
  thinking: {
    type: "adaptive"
  },
  tools: [weatherTool],
  messages: [{ role: "user", content: "What's the weather in Paris?" }]
});

// Extract the tool use block to get its ID for the tool result
const toolUseBlock = response.content.find((block) => block.type === "tool_use");

// This is where your actual weather API call would go
// Pretend this is what the weather API returns
const weatherData = { temperature: 88 };

if (toolUseBlock) {
  // Second request: include the assistant turn and the tool result
  const continuation = await client.messages.create({
    model: "claude-opus-5-5",
    max_tokens: 16000,
    thinking: {
      type: "adaptive"
    },
    tools: [weatherTool],
    messages: [
      { role: "user", content: "What's the weather in Paris?" },
      // Echo the assistant content exactly as received. When a thinking
      // block is present, it must accompany the tool_use block.
      { role: "assistant", content: response.content },
      {
        role: "user",
        content: [
          {
            type: "tool_result" as const,
            tool_use_id: toolUseBlock.id,
            content: `Current temperature: ${weatherData.temperature}°F`
          }
        ]
      }
    ]
  });
  console.log(continuation);
}
```

```csharp
AnthropicClient client = new();

var weatherTool = new ToolUnion(new Tool()
{
    Name = "get_weather",
    Description = "Get current weather for a location",
    InputSchema = new InputSchema()
    {
        Properties = new Dictionary<string, JsonElement>
        {
            ["location"] = JsonSerializer.SerializeToElement(new { type = "string", description = "City name" }),
        },
        Required = ["location"],
    },
});

var parameters = new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigAdaptive(),
    Tools = [weatherTool],
    Messages = [new UserMessageParam { Content = "What's the weather in Paris?" }]
};

var response = await client.Messages.Create(parameters);

// Extract the tool_use block to get its ID for the tool result
ToolUseBlock? toolUseBlock = null;
foreach (var block in response.Content)
{
    if (block.TryPickToolUse(out var toolUse))
    {
        toolUseBlock = toolUse;
        break;
    }
}

var weatherData = new { temperature = 88 };

// Build continuation with tool result
var continuationParams = new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigAdaptive(),
    Tools = [weatherTool],
    Messages = [
        new UserMessageParam { Content = "What's the weather in Paris?" },
        // response.Content includes the thinking blocks; passing them back is required
        new AssistantMessageParam { Content = response.Content.Select(block => new ContentBlockParam(block.Json)).ToList() },
        new UserMessageParam
        {
            Content = new List<ContentBlockParam>
            {
                new ContentBlockParam(new ToolResultBlockParam()
                {
                    ToolUseID = toolUseBlock?.ID ?? "",
                    Content = $"Current temperature: {weatherData.temperature}°F"
                })
            }
        }
    ]
};

var continuation = await client.Messages.Create(continuationParams);
Console.WriteLine(continuation);
```

```go
client := anthropic.NewClient()

weatherTool := anthropic.ToolUnionParam{
	OfTool: &anthropic.ToolParam{
		Name:        "get_weather",
		Description: anthropic.String("Get current weather for a location"),
		InputSchema: anthropic.ToolInputSchemaParam{
			Properties: map[string]any{
				"location": map[string]any{
					"type":        "string",
					"description": "City name",
				},
			},
			Required: []string{"location"},
		},
	},
}

response, err := client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeOpus5_5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{},
	},
	Tools: []anthropic.ToolUnionParam{weatherTool},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("What's the weather in Paris?")),
	},
})
if err != nil {
	log.Fatal(err)
}

var toolUseBlock anthropic.ToolUseBlock
for _, block := range response.Content {
	if v, ok := block.AsAny().(anthropic.ToolUseBlock); ok {
		toolUseBlock = v
		break
	}
}

weatherData := map[string]int{"temperature": 88}

continuation, err := client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeOpus5_5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{},
	},
	Tools: []anthropic.ToolUnionParam{weatherTool},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("What's the weather in Paris?")),
		response.ToParam(),
		anthropic.NewUserMessage(
			anthropic.NewToolResultBlock(toolUseBlock.ID, fmt.Sprintf("Current temperature: %d°F", weatherData["temperature"]), false),
		),
	},
})
if err != nil {
	log.Fatal(err)
}

fmt.Println(continuation)
```

```java
import com.anthropic.models.messages.ThinkingConfigAdaptive;
// ...

void main() {
    AnthropicClient client = AnthropicOkHttpClient.fromEnv();

    Tool weatherTool = Tool.builder()
        .name("get_weather")
        .description("Get current weather for a location")
        .inputSchema(Tool.InputSchema.builder()
            .properties(JsonValue.from(Map.of(
                "location", Map.of("type", "string", "description", "City name")
            )))
            .required(List.of("location"))
            .build())
        .build();

    MessageCreateParams initialParams = MessageCreateParams.builder()
        .model(Model.CLAUDE_OPUS_5_5)
        .maxTokens(16000L)
        .thinking(ThinkingConfigAdaptive.builder().build())
        .addTool(weatherTool)
        .addUserMessage("What's the weather in Paris?")
        .build();

    Message response = client.messages().create(initialParams);

    ToolUseBlock toolUseBlock = null;
    for (var block : response.content()) {
        if (block.toolUse().isPresent()) {
            toolUseBlock = block.toolUse().get();
            break;
        }
    }

    int temperature = 88;

    // Second request: echo the assistant turn as received, then the tool result
    MessageCreateParams continuationParams = MessageCreateParams.builder()
        .model(Model.CLAUDE_OPUS_5_5)
        .maxTokens(16000L)
        .thinking(ThinkingConfigAdaptive.builder().build())
        .addTool(weatherTool)
        .addUserMessage("What's the weather in Paris?")
        .addMessage(response)
        .addUserMessageOfContentBlockParams(List.of(
            ContentBlockParam.ofToolResult(
                ToolResultBlockParam.builder()
                    .toolUseId(toolUseBlock.id())
                    .content("Current temperature: " + temperature + "°F")
                    .build()
            )
        ))
        .build();

    Message continuation = client.messages().create(continuationParams);
    IO.println(continuation);
}
```

```php
$client = new Client();

$weatherTool = [
    'name' => 'get_weather',
    'description' => 'Get current weather for a location',
    'input_schema' => [
        'type' => 'object',
        'properties' => [
            'location' => [
                'type' => 'string',
                'description' => 'City name'
            ]
        ],
        'required' => ['location']
    ]
];

$response = $client->messages->create(
    maxTokens: 16000,
    messages: [
        ['role' => 'user', 'content' => "What's the weather in Paris?"]
    ],
    model: 'claude-opus-5-5',
    thinking: ['type' => 'adaptive'],
    tools: [$weatherTool],
);

$toolUseBlock = null;
foreach ($response->content as $block) {
    if ($block->type === 'tool_use') {
        $toolUseBlock = $block;
        break;
    }
}

$weatherData = ['temperature' => 88];

$continuation = $client->messages->create(
    maxTokens: 16000,
    messages: [
        ['role' => 'user', 'content' => "What's the weather in Paris?"],
        ['role' => 'assistant', 'content' => $response->content],
        ['role' => 'user', 'content' => [
            [
                'type' => 'tool_result',
                'tool_use_id' => $toolUseBlock->id,
                'content' => "Current temperature: {$weatherData['temperature']}°F"
            ]
        ]]
    ],
    model: 'claude-opus-5-5',
    thinking: ['type' => 'adaptive'],
    tools: [$weatherTool],
);

echo $continuation;
```

```ruby
client = Anthropic::Client.new

weather_tool = {
  name: "get_weather",
  description: "Get current weather for a location",
  input_schema: {
    type: "object",
    properties: {
      location: { type: "string", description: "City name" }
    },
    required: ["location"]
  }
}

response = client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 16000,
  thinking: {
    type: "adaptive"
  },
  tools: [weather_tool],
  messages: [
    { role: "user", content: "What's the weather in Paris?" }
  ]
)

tool_use_block = response.content.find { |block| block.type == :tool_use }

raise "No tool_use block found" unless tool_use_block

weather_data = { temperature: 88 }

continuation = client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 16000,
  thinking: {
    type: "adaptive"
  },
  tools: [weather_tool],
  messages: [
    { role: "user", content: "What's the weather in Paris?" },
    { role: "assistant", content: response.content },
    { role: "user", content: [
      {
        type: "tool_result",
        tool_use_id: tool_use_block.id,
        content: "Current temperature: #{weather_data[:temperature]}°F"
      }
    ] }
  ]
)

puts continuation
```

### 最終応答を読む

Claude がテキストでターンを完了します。適応型推論では[ツール呼び出しの間に行う推論](https://platform.claude.com/docs/en/build-with-claude/thinking#interleaved-thinking)が自動で有効なため、後続の応答では最終テキストの前に新しい推論ブロックが現れることもあります。

```json
{
  "content": [
    {
      "type": "text",
      "text": "Currently in Paris, the temperature is 88°F (31°C)"
    }
  ]
}
```

## ツール呼び出しの間に推論すると処理はどう変わるか

呼び出し間の推論では、Claude はツールの結果を得て、次に行動する前にその結果を検討できます。仕組みとモデル別の対応状況は、Thinking の[ツール呼び出しの間に行う推論](https://platform.claude.com/docs/en/build-with-claude/thinking#interleaved-thinking)を参照してください。ツールを連続して呼び出せる点は共通で、この機能によって推論ブロックが現れる位置が変わります。以下では、ツールを 2 つ使う処理を比較します。

### 呼び出し間の推論を行わずにツールを使う

呼び出し間の推論を行わない方式では、Claude はアシスタントターンの最初に 1 回推論します。ツール結果を受け取った後の応答には、新しい推論ブロックを加えず処理を続けます。

```text
User: "What's the total revenue if we sold 150 units at $50 each,
       and how does this compare to our average monthly revenue?"

Response 1: [thinking] "I need to calculate 150 * $50, then check the database..."
            [tool_use: calculator] { "expression": "150 * 50" }
  ↓ tool result: "7500"

Response 2: [tool_use: database_query] { "query": "SELECT AVG(revenue)..." }
            ↑ no thinking block
  ↓ tool result: "5200"

Response 3: [text] "The total revenue is $7,500, which is 44% above your
            average monthly revenue of $5,200."
            ↑ no thinking block
```

### 呼び出しの間にも推論しながらツールを使う

呼び出し間の推論が有効な場合は、ツール結果を受け取るたびに Claude が推論し、途中の結果を検討してから処理を続けられます。

```text
User: "What's the total revenue if we sold 150 units at $50 each,
       and how does this compare to our average monthly revenue?"

Response 1: [thinking] "I need to calculate 150 * $50 first..."
            [tool_use: calculator] { "expression": "150 * 50" }
  ↓ tool result: "7500"

Response 2: [thinking] "Got $7,500. Now I should query the database to compare..."
            [tool_use: database_query] { "query": "SELECT AVG(revenue)..." }
            ↑ thinking after receiving calculator result
  ↓ tool result: "5200"

Response 3: [thinking] "$7,500 vs $5,200 average - that's a 44% increase..."
            [text] "The total revenue is $7,500, which is 44% above your
            average monthly revenue of $5,200."
            ↑ thinking before final answer
```

## 関連資料

[推論の概要](https://platform.claude.com/docs/en/build-with-claude/thinking)

推論を有効にする方法、推論出力の読み方、ツール利用、キャッシュ、ストリーミングの詳しい規則を説明します。

[推論の調整](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)

effort の段階とプロンプトによる指示で、Claude が推論する頻度と深さを調整します。

[拡張推論](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)

手動の推論予算について、`budget_tokens` の仕組みと適応型推論への移行を説明します。
