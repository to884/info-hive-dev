---
url: "https://platform.claude.com/docs/en/models/opus-5-5/migration-guide"
title: "Claude Opus 5.5 migration guide"
fetched_at: "2026-11-18T22:48:49+09:00"
source_sha256: "2ba21a96527c2124281db97ca7bda848c8923216c4c8681c4fff41d546700b91"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# Claude Opus 5.5 への移行ガイド

以前の Opus モデルや Claude Sonnet 5 から Claude Opus 5.5 へ切り替える方法を説明します。エラーになるリクエスト設定、各応答に現れる推論ブロック、移行元モデルごとのチェックリストを扱います。

このガイドは [Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) を使うコードの移行を扱います。[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) を使う場合に必要な変更はモデル名の更新です。

Claude Code にコードの移行を任せる

```text
/claude-api migrate this project to claude-opus-5-5
```

[Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-5)、[Claude Opus 4.8](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-4-8)、[Claude Opus 4.7](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-47)、[Claude Opus 4.6 以前の Opus モデル](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-46)、[Claude Sonnet 5](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-sonnet-5) から Claude Opus 5.5 へ移行する場合に必要なコード変更を示します。まず[すべてのリクエストに共通する要件](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#request-requirements)と[各応答の推論を処理する](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-in-every-response)を確認します。次に、現在のモデルの節へ進み、冒頭にある適用対象の節も確認します。[移行チェックリスト](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migration-checklist)では、移行元ごとに変更を確認できます。

Claude Opus 5.5 の料金は Claude Opus 5 より下がり、100 万トークンあたり入力 4 米ドル（USD）、出力 20 米ドルです。Claude Opus 5 は入力 5 米ドル、出力 25 米ドルです（[料金](https://platform.claude.com/docs/en/about-claude/pricing)を参照）。機能の対応状況は [Claude Opus 5.5 の新機能](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5#feature-support)、挙動の違いとモデルに合ったプロンプトの書き方は [Claude Opus 5.5 のプロンプトガイド](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)を参照してください。

## Claude Opus 5.5 のすべてのリクエストに共通する要件

移行元のモデルにかかわらず、`claude-opus-5-5` へのリクエストは次の条件を満たす必要があります。設定が拒否される場合、API は 400 エラーを返します。

- **モデル ID**。日付の接尾辞が付かない固定のモデル ID `claude-opus-5-5` を指定します。Amazon Bedrock、Claude Platform on AWS、Claude Models on Google Cloud (Anthropic managed)、Claude Models on Google Cloud (Google managed)、Microsoft Foundry では、プラットフォームごとのモデル ID を指定します。[提供状況](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5#availability)を参照してください。
- **推論**。常に[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking)が有効です。`thinking` フィールドを省略する場合と `thinking: {"type": "adaptive"}` を送る場合の挙動は同じです。`thinking: {"type": "disabled"}` と手動の推論予算（`thinking: {"type": "enabled", "budget_tokens": N}`）は拒否されます。[推論設定の変更前後の例](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-cant-be-disabled)を参照してください。
- **effort**。推論の深さを制御するリクエストパラメーターは [effort](https://platform.claude.com/docs/en/build-with-claude/effort) です。全 5 段階（`low`、`medium`、`high`、`xhigh`、`max`）に対応し、既定値は `medium` です。[Claude Opus 5.5 の推奨 effort](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-opus-5-5)を参照してください。
- **ツール選択**。`tool_choice` には `{"type": "auto"}`（既定値）または `{"type": "none"}` を使います。`{"type": "any"}` や `{"type": "tool", "name": "..."}` でツール呼び出しを強制すると拒否されます。[ツール選択の変更前後の例](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#forced-tool-use)を参照してください。
- **サンプリングパラメーター**。`temperature`、`top_p`、`top_k` を省略します。モデルの挙動はプロンプトで調整します。
- **事前入力**。`messages` の末尾に、応答の冒頭を事前入力したアシスタントターンがあると拒否されます。[構造化出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)やシステムプロンプトの指示を使います。
- **コンピューター操作**。`computer_toolset_20260801` ツールセットを宣言します。Amazon Bedrock では `computer_20251124` も使えます。[コンピューター操作に関する互換性の変更](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#computer-use-toolset)を参照してください。
- **コンテキストウィンドウ**。既定で[コンテキストウィンドウは 100 万トークン](https://platform.claude.com/docs/en/build-with-claude/context-windows)です。旧モデル向けにコンテキストウィンドウのベータヘッダーを送っても効果はありません。

次のリクエストはすべての条件を満たします。effort を指定し、`thinking` フィールドを省略しています。推論を含む応答では `thinking` ブロックが先に現れるため、テキストを出力する例ではブロックの種類を見て取り出しています。

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
```

```php
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
    if ($block instanceof \Anthropic\Messages\TextBlock) {
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
  puts block.text if block.is_a?(Anthropic::Models::TextBlock)
end
```

## 各応答の推論を処理する

Claude Opus 5.5 ではすべてのリクエストで推論が有効なので、どの応答でも冒頭に `thinking` ブロックが現れることがあります。`max_tokens` は推論とテキストの合計に適用されます。すでに推論を有効にしていたコードは、多くの場合 1〜3 に対応済みなので、4 と 5 を確認します。旧モデルで推論を無効にしていたコードは全項目を確認します。

1. **`max_tokens` は推論とテキストの合計に適用される**。Claude Opus 4.8 以前の Opus モデルでは `thinking` フィールドを省略すると推論しません。Claude Opus 5 と Claude Sonnet 5 は `thinking: {"type": "disabled"}` を受理します。Claude Opus 5.5 はすべてのリクエストで[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking)が有効です。`max_tokens` は推論と応答テキストの合計の上限なので、推論を無効にしていた処理では見直します。推論テキストが返らない場合も推論トークンは出力として課金されるので、処理によってはリクエストあたりの出力トークン数が増えます。[費用の調整](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost#cost-control)を参照してください。推論のトークン消費を抑えるには [effort](https://platform.claude.com/docs/en/build-with-claude/effort) を下げます。`xhigh` または `max` を使う場合は、推論と処理に使える枠を確保するため、`max_tokens` を 64,000 トークンから試して調整します。推論を無効にした状態に合わせてプロンプトを調整していた場合は、[推論を無効にする前提で書いたプロンプト](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5#prompts-written-for-thinking-disabled)を参照してください。
2. **応答の冒頭に推論ブロックが現れる**。最初の `text` ブロックより先に、1 つ以上の `thinking` ブロックが現れる場合があります。`content[0].text` のように位置で読み取るコードや、最初の `content_block_start` イベントをテキストとみなすストリーム処理は失敗します。`type` で内容ブロックを選びます。`type` が `"text"` のブロックから `text` を読み取り、ストリームイベントの処理ではブロックの種類で分岐します。
3. **ツール利用を繰り返す場合は推論ブロックをそのまま返す**。ツール結果を返す際は、アシスタントの応答に含まれる `thinking` ブロックを完全な形のまま API に返します。`thinking` フィールドが空のブロックも含めます。内容を種類で絞り込んだり、組み立て直したりせず、アシスタントメッセージを受信したまま送ります。編集、順序の変更、一部の脱落があると、API は 400 エラーで拒否します。[推論ブロックの保持](https://platform.claude.com/docs/en/build-with-claude/thinking#preserving-thinking-blocks)を参照してください。
4. **既定では推論テキストを省略する**。`thinking.display` の既定値は `"omitted"` です。`thinking` ブロックには `signature` が含まれ、`thinking` フィールドは空で返ります。`thinking` フィールドは表示用のテキストとして扱います。読める要約を受け取るには、`thinking.display` に `"summarized"` を指定します。
   ```python
   thinking = {
       "type": "adaptive",
       "display": "summarized",
   }
   ```
   ```typescript
   const thinking = {
     type: "adaptive",
     display: "summarized"
   };
   ```
   ```csharp
   var thinking = new ThinkingConfigAdaptive { Display = Display.Summarized };
   ```
   ```go
   thinking := anthropic.ThinkingConfigParamUnion{
   	OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{
   		Display: anthropic.ThinkingConfigAdaptiveDisplaySummarized,
   	},
   }
   ```
   ```java
   ThinkingConfigAdaptive thinking = ThinkingConfigAdaptive.builder()
       .display(ThinkingConfigAdaptive.Display.SUMMARIZED)
       .build();
   ```
   ```php
   $thinking = ['type' => 'adaptive', 'display' => 'summarized'];
   ```
   ```ruby
   thinking = {
     type: "adaptive",
     display: "summarized"
   }
   ```
   利用者に推論をストリーミングする製品では、既定値のままだと出力が始まるまで間が空いたように見えます。`display: "summarized"` を指定すると、推論中の進捗を再び表示できます。[推論の表示を設定する](https://platform.claude.com/docs/en/build-with-claude/thinking#controlling-thinking-display)を参照してください。
5. **ツール呼び出し間のテキストは推論ブロックで返る**。モデルがツール呼び出しの間に書く短い報告は `thinking` ブロックで返り、既定の表示設定では空です。[ツール呼び出し間のテキストは推論ブロックで返る](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#text-between-tool-calls)を参照してください。

## 移行元モデル別のチェックリスト

上から順に確認し、現在のモデル名が書かれたグループまでの項目を適用します。Claude Opus 5 では最初のグループ、Claude Sonnet 5 では最初と最後のグループを適用します。

### すべての移行元モデル

- モデル ID を `claude-opus-5-5` に変更します。
- `thinking: {"type": "disabled"}` と `thinking: {"type": "enabled", ...}` を削除し、effort の段階を指定します。
- `effort` を明示します。Claude Opus 5.5 の既定値は `medium`、Claude Opus 5 の既定値は `high` です。
- `tool_choice` の `any` と `tool` を、`auto` と厳密なツール利用の組み合わせか、構造化出力に置き換えます。
- 古いコンピューター操作ツールを使う場合は、`computer_toolset_20260801` ツールセットを宣言し、旧版のベータヘッダーを取り除き、エージェントの処理ループをツールセットに対応させます。Amazon Bedrock では `computer_20251124` も使えます。[コンピューター操作に関する互換性の変更](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#computer-use-toolset)を参照してください。
- ルーターやフォールバックで会話が Claude Opus 5.5 から別のモデルに切り替わる場合、移行先では通常 Claude Opus 5.5 の推論ブロックを使わずに処理します。Claude Fable 5.1 と Claude Mythos 5.1 は Claude API でブロックを保持します。Claude Fable 5.2 と Claude Mythos 5.2 は Claude API と Claude Models on Google Cloud (Google managed) で保持します。Claude Opus 5.5 は Claude Opus 5 と[以前の Claude Opus、Claude Sonnet、Claude Haiku モデル](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#earlier-models)の推論を読み取れます。Claude API と Claude Models on Google Cloud (Google managed) では Claude Sonnet 5.5 と Claude Haiku 5.5 の推論も読み取れます。Claude Fable や Claude Mythos の推論は読み取れません。
- 内容ブロックを `type` で読み取ります。ツール利用を繰り返す場合は、`thinking` ブロックをそのまま返します。
- ツール呼び出し間のテキストを表示する画面では、ベータ版の `display: "updates"` または `"summarized"` を指定し、空でない `thinking` ブロックを表示します。
- コードが会話の途中で過去のターン、`system` プロンプト、`tools` を編集する場合は、[推論の保持](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)の手順に従います。
- `stop_reason: "refusal"` を処理し、フォールバックを設定します。
- 選んだ effort での費用と応答時間を改めて測定します。
- 推論を無効にしていたコードでは、推論と応答テキストに共通する `max_tokens` を見直します。`xhigh` または `max` の場合は 64,000 トークンから試します。[各応答の推論を処理する](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-in-every-response)を参照してください。

### Claude Opus 4.8 以前

- `thinking` フィールドを省略していた処理を見直します。Claude Opus 5.5 では推論が有効になり、無効にはできません。総出力（推論と応答テキスト）の上限である `max_tokens` を見直し、推論を抑えたい処理では `effort` を下げます。推論トークンは出力として課金されるので、リクエストあたりの出力トークン数が増える場合があります。
- `thinking` フィールドを読むコードが、それを表示用テキストとして扱っていることを確認します。読める要約を受け取るには `display: "summarized"` にします。
- キャッシュの下限に近いプロンプトを見直します。512 トークン以上のプロンプトはキャッシュを作成できます。
- 組織が [Priority Tier](https://platform.claude.com/docs/en/api/service-tiers#supported-models) を契約している場合は、キャパシティを別途計画します。Claude Opus 5.5 は Priority Tier の対象外です。
- `xhigh` または `max` の場合は、出発点として `max_tokens` を 64,000 以上に引き上げます。
- エージェント処理では[タスク予算](https://platform.claude.com/docs/en/build-with-claude/task-budgets)と、会話途中でのツール変更を検討します。いずれもベータ版です。

### Claude Opus 4.7 以前

- 旧モデル用に調整した設定を見直し、自分の評価データで [effort](https://platform.claude.com/docs/en/build-with-claude/effort) の段階を変えて改めて比較します。
- コンテキストウィンドウのベータヘッダーを削除します。
- 指示を更新するために会話履歴を組み立て直している場合は、会話途中のシステムメッセージに切り替えます。履歴を組み立て直すと 400 エラーになる場合があり、プロンプトキャッシュにもヒットしなくなります。
- 拒否応答で、停止理由を扱う処理が `stop_details` を読むことを確認します。
- Claude Opus 4.7 が受理しない高速モードを使う場合は、Claude API へのリクエストで `speed: "fast"` を指定します。

### Claude Opus 4.6 以前

- リクエストから `temperature`、`top_p`、`top_k` を取り除きます。
- `thinking: {"type": "enabled", "budget_tokens": N}` を `thinking: {"type": "adaptive"}` と [effort パラメーター](https://platform.claude.com/docs/en/build-with-claude/effort)の組み合わせに置き換えるか、`thinking` フィールドを省略します。適応型推論は常に有効です。
- UI に推論内容を表示する場合は、推論の要約を明示的に指定します。
- 更新されたトークナイザーで、処理全体の費用と応答時間を測り直します。
- 更新されたトークナイザーに合わせて、圧縮を始める条件も含め `max_tokens` を調整し直します。
- クライアント側でトークン数を見積もる処理を再検証します。
- アプリケーションが画像を送る場合は、[高解像度画像への対応](https://platform.claude.com/docs/en/build-with-claude/vision#high-resolution-image-support-on-claude-opus-4-7)を踏まえて予算を見直します。元の解像度で送ると、1 枚あたりの画像トークン数が最大で約 3 倍になります。細部が不要なら、解像度を下げてから送ります。
- モデルが返す指示位置や境界ボックスの座標を使う場合は、倍率を換算する処理を削除します。Claude Opus 4.7 以降では、座標は実際の画像ピクセルに 1 対 1 で対応します。
- Claude Opus 4.7 で始まった[挙動の変化](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#behavior-changes)を確認します。
- 製品で正当なセキュリティ業務を扱う場合は、[Cyber Verification Program](https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude-opus-and-sonnet) に申請し、サイバー分野の制限を緩和した利用を申し込みます。

### Claude Opus 4.5 以前

- アシスタントメッセージの事前入力を削除します。Claude Opus 4.6 ですでに拒否されます。
- ツール呼び出しの JSON を標準の JSON パーサーで解析していることを確認します。
- `client.beta.messages.create()`（csharp: `client.Beta.Messages.Create()`、go: `client.Beta.Messages.New()`、java: `client.beta().messages().create()`、php: `$client->beta->messages->create()`、cli: `ant beta:messages create`）から `client.messages.create()`（csharp: `client.Messages.Create()`、go: `client.Messages.New()`、java: `client.messages().create()`、php: `$client->messages->create()`、cli: `ant messages create`）に移行します。適応型推論と effort にベータ名前空間は不要です。
- ベータヘッダー `effort-2025-11-24` を削除します。effort パラメーターにこのヘッダーは不要です。
- ベータヘッダー `fine-grained-tool-streaming-2025-05-14` を削除します。
- ベータヘッダー `interleaved-thinking-2025-05-14` を削除します。適応型推論ではツール呼び出し間の推論が自動で有効になります。
- 該当する場合は、`output_format` を `output_config.format` に移行します。

### Claude 4.1 以前

- ツールの版を更新します（`text_editor_20250728`、`code_execution_20260521`）。
- 停止理由 `refusal` を処理します。
- 停止理由 `model_context_window_exceeded` を処理します。
- ツールの文字列パラメーターの末尾の改行を処理できることを確認します。
- ベータヘッダー `token-efficient-tools-2025-02-19` と `output-128k-2025-02-19` を削除します。
- [プロンプトのベストプラクティス](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)に沿ってプロンプトを見直します。

### Claude Sonnet 5 のみ

- 指示を更新するために会話履歴を組み立て直している場合は、会話途中のシステムメッセージに切り替えます。履歴を組み立て直すと 400 エラーになる場合があり、プロンプトキャッシュにもヒットしなくなります。
- キャッシュの下限に近いプロンプトを見直します。512 トークン以上のプロンプトはキャッシュを作成できます。

## Claude Opus 5 から Claude Opus 5.5 への移行

まず[すべてのリクエストに共通する要件](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#request-requirements)と[各応答の推論を処理する](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-in-every-response)を確認します。この節の変更はすべての移行元モデルに当てはまります。Claude Opus 5.5 が拒否する設定と、それに伴う応答の変化を扱います。この節に対応する項目は[移行チェックリスト](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migration-checklist)の最初のグループにあります。

### モデル名を更新する

```python
model = "claude-opus-5"  # Before
model = "claude-opus-5-5"  # After
```

`claude-opus-5-5` は `claude-opus-5` と同じ形式で、日付の接尾辞が付かない固定のモデル ID です。Amazon Bedrock、Claude Platform on AWS、Claude Models on Google Cloud (Anthropic managed)、Claude Models on Google Cloud (Google managed)、Microsoft Foundry では、プラットフォームごとのモデル ID を指定します。[提供状況](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5#availability)を参照してください。

### 互換性を損なう変更

個々の変更は Claude Opus 5.5 の新機能ページの[互換性を損なう変更](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5#breaking-changes)で説明しています。この節では変更ごとにコードの修正を示します。

#### 推論は常に有効

`thinking: {"type": "disabled"}` と `thinking: {"type": "enabled", "budget_tokens": N}` はいずれも 400 エラーになります（`"thinking.type.disabled" is not supported for this model.` または `"thinking.type.enabled" is not supported for this model.`）。`thinking` フィールドを削除し、[effort](https://platform.claude.com/docs/en/build-with-claude/effort) を選びます。トークン消費を抑えるために推論を無効にしていた処理では、低い段階を使います。応答の冒頭には `thinking` ブロックが現れるため、`type` で内容ブロックを選び、ツール結果には `thinking` ブロックをそのまま添えて返します。[推論は常に有効](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5#thinking-cant-be-disabled)を参照してください。

変更前の例です。Claude Opus 5 はこのリクエストを受理し、Claude Opus 5.5 は 400 エラーを返します。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-5",
    "max_tokens": 16000,
    "thinking": {"type": "disabled"},
    "messages": [{"role": "user", "content": "..."}]
  }'
```

```bash
ant messages create \
  --model claude-opus-5 \
  --max-tokens 16000 \
  --thinking '{type: disabled}' \
  --message '{role: user, content: "..."}'
```

```python
client.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    thinking={"type": "disabled"},
    messages=[{"role": "user", "content": "..."}],
)
```

```typescript
await client.messages.create({
  model: "claude-opus-5",
  max_tokens: 16000,
  thinking: { type: "disabled" },
  messages: [{ role: "user", content: "..." }]
});
```

```csharp
await client.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeOpus5,
    MaxTokens = 16000,
    Thinking = new ThinkingConfigDisabled(),
    Messages = [new UserMessageParam { Content = "..." }],
});
```

```go
client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeOpus5,
	MaxTokens: 16000,
	Thinking: anthropic.ThinkingConfigParamUnion{
		OfDisabled: &anthropic.ThinkingConfigDisabledParam{},
	},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("...")),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_OPUS_5)
    .maxTokens(16000L)
    .thinking(ThinkingConfigDisabled.builder().build())
    .addUserMessage("...")
    .build();

client.messages().create(params);
```

```php
$client->messages->create(
    model: Model::CLAUDE_OPUS_5,
    maxTokens: 16000,
    thinking: ThinkingConfigDisabled::with(),
    messages: [['role' => 'user', 'content' => '...']],
);
```

```ruby
client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5,
  max_tokens: 16000,
  thinking: Anthropic::ThinkingConfigDisabled.new,
  messages: [{ role: "user", content: "..." }]
)
```

変更後の例です。

```bash
# thinking is always on; effort is the control
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-5-5",
    "max_tokens": 16000,
    "output_config": {"effort": "low"},
    "messages": [{"role": "user", "content": "..."}]
  }'
```

```bash
# thinking is always on; effort is the control
ant messages create \
  --model claude-opus-5-5 \
  --max-tokens 16000 \
  --output-config '{effort: low}' \
  --message '{role: user, content: "..."}'
```

```python
client.messages.create(
    model="claude-opus-5-5",
    max_tokens=16000,
    output_config={"effort": "low"},  # thinking is always on; effort is the control
    messages=[{"role": "user", "content": "..."}],
)
```

```typescript
await client.messages.create({
  model: "claude-opus-5-5",
  max_tokens: 16000,
  output_config: { effort: "low" }, // thinking is always on; effort is the control
  messages: [{ role: "user", content: "..." }]
});
```

```csharp
await client.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 16000,
    OutputConfig = new() { Effort = Effort.Low }, // thinking is always on; effort is the control
    Messages = [new UserMessageParam { Content = "..." }],
});
```

```go
client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeOpus5_5,
	MaxTokens: 16000,
	OutputConfig: anthropic.OutputConfigParam{
		Effort: anthropic.OutputConfigEffortLow, // thinking is always on; effort is the control
	},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("...")),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_OPUS_5_5)
    .maxTokens(16000L)
    // thinking is always on; effort is the control
    .outputConfig(OutputConfig.builder()
        .effort(OutputConfig.Effort.LOW)
        .build())
    .addUserMessage("...")
    .build();

client.messages().create(params);
```

```php
$client->messages->create(
    model: Model::CLAUDE_OPUS_5_5,
    maxTokens: 16000,
    // thinking is always on; effort is the control
    outputConfig: OutputConfig::with(effort: Effort::LOW),
    messages: [['role' => 'user', 'content' => '...']],
);
```

```ruby
client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 16000,
  # thinking is always on; effort is the control
  output_config: { effort: Anthropic::OutputConfig::Effort::LOW },
  messages: [{ role: "user", content: "..." }]
)
```

#### 強制ツール利用は非対応

`tool_choice` の `any` と `tool` は、トークン数を数えるエンドポイントを含め、400 エラーになります（`tool_choice: type "tool" and "any" are not supported for this model.`）。`auto` と[厳密なツール利用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use)または[構造化出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)を使い、ツールを使う条件をプロンプトに書きます。厳密なツール利用が受理するのは JSON Schema の一部なので、`strict: true` を追加する前に各ツールの `input_schema` を確認します。スキーマ内のすべてのオブジェクトに `additionalProperties: false` を指定する必要があります。[JSON Schema の制約](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#json-schema-limitations)と、[強制ツール利用は非対応](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5#forced-tool-use-is-not-supported)を参照してください。

変更前の例です。Claude Opus 5 はこのリクエストを受理し、Claude Opus 5.5 は 400 エラーを返します。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-5",
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
model: claude-opus-5
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
    content: What is the weather in Paris?
YAML
```

```python
client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "get_weather"},
    messages=[{"role": "user", "content": "What is the weather in Paris?"}],
)
```

```typescript
await client.messages.create({
  model: "claude-opus-5",
  max_tokens: 1024,
  tools,
  tool_choice: { type: "tool", name: "get_weather" },
  messages: [{ role: "user", content: "What is the weather in Paris?" }]
});
```

```csharp
await client.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeOpus5,
    MaxTokens = 1024,
    Tools = [.. tools],
    ToolChoice = new ToolChoiceTool { Name = "get_weather" },
    Messages = [new UserMessageParam { Content = "What is the weather in Paris?" }],
});
```

```go
client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:      anthropic.ModelClaudeOpus5,
	MaxTokens:  1024,
	Tools:      tools,
	ToolChoice: anthropic.ToolChoiceParamOfTool("get_weather"),
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("What is the weather in Paris?")),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_OPUS_5)
    .maxTokens(1024L)
    .tools(tools)
    .toolChoice(ToolChoiceTool.of("get_weather"))
    .addUserMessage("What is the weather in Paris?")
    .build();

client.messages().create(params);
```

```php
$client->messages->create(
    model: Model::CLAUDE_OPUS_5,
    maxTokens: 1024,
    tools: $tools,
    toolChoice: ToolChoiceTool::with(name: 'get_weather'),
    messages: [['role' => 'user', 'content' => 'What is the weather in Paris?']],
);
```

```ruby
client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5,
  max_tokens: 1024,
  tools: tools,
  tool_choice: Anthropic::ToolChoiceTool.new(name: "get_weather"),
  messages: [{ role: "user", content: "What is the weather in Paris?" }]
)
```

変更後の例です。

```bash
# strict tool use: every call matches the tool's input_schema
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-5-5",
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
model: claude-opus-5-5
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
    content: What is the weather in Paris? Use the get_weather tool.
YAML
```

```python
client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    # strict tool use: every call matches the tool's input_schema
    tools=[{**tool, "strict": True} for tool in tools],
    tool_choice={"type": "auto"},
    messages=[
        {
            "role": "user",
            "content": "What is the weather in Paris? Use the get_weather tool.",
        }
    ],
)
```

```typescript
await client.messages.create({
  model: "claude-opus-5-5",
  max_tokens: 1024,
  // strict tool use: every call matches the tool's input_schema
  tools: tools.map((tool) => ({ ...tool, strict: true })),
  tool_choice: { type: "auto" },
  messages: [
    {
      role: "user",
      content: "What is the weather in Paris? Use the get_weather tool."
    }
  ]
});
```

```csharp
await client.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 1024,
    // strict tool use: every call matches the tool's input_schema
    Tools = [.. tools.Select(tool => tool with { Strict = true })],
    ToolChoice = new ToolChoiceAuto(),
    Messages =
    [
        new UserMessageParam { Content = "What is the weather in Paris? Use the get_weather tool." },
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
	Model:      anthropic.ModelClaudeOpus5_5,
	MaxTokens:  1024,
	Tools:      strictTools,
	ToolChoice: anthropic.ToolChoiceUnionParam{OfAuto: &anthropic.ToolChoiceAutoParam{}},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(
			anthropic.NewTextBlock("What is the weather in Paris? Use the get_weather tool."),
		),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_OPUS_5_5)
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
    .addUserMessage("What is the weather in Paris? Use the get_weather tool.")
    .build();

client.messages().create(params);
```

```php
$client->messages->create(
    model: Model::CLAUDE_OPUS_5_5,
    maxTokens: 1024,
    // strict tool use: every call matches the tool's input_schema
    tools: array_map(fn (Tool $tool) => $tool->withStrict(true), $tools),
    toolChoice: ToolChoiceAuto::with(),
    messages: [
        [
            'role' => 'user',
            'content' => 'What is the weather in Paris? Use the get_weather tool.',
        ],
    ],
);
```

```ruby
client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 1024,
  # strict tool use: every call matches the tool's input_schema
  tools: tools.map { |tool| tool.merge(strict: true) },
  tool_choice: Anthropic::ToolChoiceAuto.new,
  messages: [
    { role: "user", content: "What is the weather in Paris? Use the get_weather tool." }
  ]
)
```

#### 推論ブロックはモデルと会話にひも付く

推論ブロックが[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)を通るよう、会話の履歴は追記だけを行い、途中で `system` プロンプト、`tools`、過去のメッセージを編集しません。Claude Code、claude.ai、Claude Managed Agents、Claude Agent SDK はこの方式を採用しています。会話を追記だけで管理する連携はコードの変更が不要です。

[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)に失敗したとき、[400 エラー](https://platform.claude.com/docs/en/api/errors#thinking-block-conversation-mismatch)になるかどうかは条件によります。両方の場合の見分け方と対処は[推論ブロックの先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks)を参照してください。

対象のプラットフォームは[推論の保持の提供状況](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#feature-availability)を参照してください。

各推論ブロックには生成元のモデルも記録されます。ルーターやフォールバックによって、Claude Opus 5.5 の推論ブロックを読めないモデルへ会話が移ると、API が移行先に渡す前にブロックを取り除き、リクエストは成功します。どのモデルがどのブロックを読めるかは Claude Opus 5.5 の新機能ページの[推論ブロックはモデルと会話にひも付く](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5#thinking-blocks-are-tied-to-the-model-that-produced-them)を参照してください。[推論の保持](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)にも説明があります。

#### コンピューター操作ツールの対応バージョン

Claude Opus 5.5 は `computer_toolset_20260801` ツールセットでコンピューター操作をサポートします。Amazon Bedrock では `computer-use-2025-11-24` ベータヘッダー付きの `computer_20251124` も受理します。Claude API での `computer_20251124` など、対応していないツールのバージョンは 400 エラーになります。`computer_20250124` はすべてのプラットフォームで拒否されます。Claude API のエラーメッセージは `'claude-opus-5-5' does not support tool types: computer_20251124.` で始まり、その後に受理するツールの種類が続きます。

ツールセットをすでに使っている連携は変更不要です。`computer_20251124` から移行するには、ベータヘッダーを取り除き、`name` や画面の寸法を付けずに `computer_toolset_20260801` を送ります。エージェントの処理ループでは、同じターンに含まれる各 `tool_use` ブロックを処理し、すべての結果に `toolset_name` をそのまま返します。実行する操作の読み取り元を、従来の `input.action` から各ブロックの `name` に変更します。処理ループの変更は[`computer_20251124` から移行する](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool#migrate-from-computer-20251124)を参照してください。

変更前の例です。Claude Opus 5 はこのリクエストを受理し、Claude API の Claude Opus 5.5 は 400 エラーを返します。

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "anthropic-beta: computer-use-2025-11-24" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-5",
    "max_tokens": 4096,
    "tools": [{
      "type": "computer_20251124",
      "name": "computer",
      "display_width_px": 1024,
      "display_height_px": 768
    }],
    "messages": [{"role": "user", "content": "Open the display settings."}]
  }'
```

```bash
ant beta:messages create --beta computer-use-2025-11-24 <<'YAML'
model: claude-opus-5
max_tokens: 4096
tools:
  - type: computer_20251124
    name: computer
    display_width_px: 1024
    display_height_px: 768
messages:
  - role: user
    content: Open the display settings.
YAML
```

```python
client.beta.messages.create(
    model="claude-opus-5",
    max_tokens=4096,
    betas=["computer-use-2025-11-24"],
    tools=[
        {
            "type": "computer_20251124",
            "name": "computer",
            "display_width_px": 1024,
            "display_height_px": 768,
        }
    ],
    messages=[{"role": "user", "content": "Open the display settings."}],
)
```

```typescript
await client.beta.messages.create({
  model: "claude-opus-5",
  max_tokens: 4096,
  betas: ["computer-use-2025-11-24"],
  tools: [
    {
      type: "computer_20251124",
      name: "computer",
      display_width_px: 1024,
      display_height_px: 768
    }
  ],
  messages: [{ role: "user", content: "Open the display settings." }]
});
```

```csharp
await client.Beta.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeOpus5,
    MaxTokens = 4096,
    Betas = [AnthropicBeta.ComputerUse2025_11_24],
    Tools =
    [
        new BetaToolComputerUse20251124
        {
            DisplayWidthPx = 1024,
            DisplayHeightPx = 768,
        },
    ],
    Messages = [new BetaUserMessageParam { Content = "Open the display settings." }],
});
```

```go
client.Beta.Messages.New(context.TODO(), anthropic.BetaMessageNewParams{
	Model:     anthropic.ModelClaudeOpus5,
	MaxTokens: 4096,
	Betas:     []anthropic.AnthropicBeta{anthropic.AnthropicBetaComputerUse2025_11_24},
	Tools: []anthropic.BetaToolUnionParam{
		{OfComputerUseTool20251124: &anthropic.BetaToolComputerUse20251124Param{
			DisplayWidthPx:  1024,
			DisplayHeightPx: 768,
		}},
	},
	Messages: []anthropic.BetaMessageParam{
		anthropic.NewBetaUserMessage(anthropic.NewBetaTextBlock("Open the display settings.")),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_OPUS_5)
    .maxTokens(4096L)
    .addBeta(AnthropicBeta.COMPUTER_USE_2025_11_24)
    .addTool(BetaToolComputerUse20251124.builder()
        .displayWidthPx(1024L)
        .displayHeightPx(768L)
        .build())
    .addUserMessage("Open the display settings.")
    .build();

client.beta().messages().create(params);
```

```php
$client->beta->messages->create(
    model: Model::CLAUDE_OPUS_5,
    maxTokens: 4096,
    betas: [AnthropicBeta::COMPUTER_USE_2025_11_24],
    tools: [
        BetaToolComputerUse20251124::with(
            displayWidthPx: 1024,
            displayHeightPx: 768,
        ),
    ],
    messages: [['role' => 'user', 'content' => 'Open the display settings.']],
);
```

```ruby
client.beta.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5,
  max_tokens: 4096,
  betas: [Anthropic::AnthropicBeta::COMPUTER_USE_2025_11_24],
  tools: [
    Anthropic::Beta::BetaToolComputerUse20251124.new(
      name: :computer,
      display_width_px: 1024,
      display_height_px: 768
    )
  ],
  messages: [{ role: "user", content: "Open the display settings." }]
)
```

変更後の例です。

```bash
# no beta header; the toolset entry takes no name or display size
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2026-10-21" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-5-5",
    "max_tokens": 4096,
    "tools": [{"type": "computer_toolset_20260801"}],
    "messages": [{"role": "user", "content": "Open the display settings."}]
  }'
```

```bash
# no beta header; the toolset entry takes no name or display size
ant messages create \
  --model claude-opus-5-5 \
  --max-tokens 4096 \
  --tool '{type: computer_toolset_20260801}' \
  --message '{role: user, content: "Open the display settings."}'
```

```python
client.messages.create(
    model="claude-opus-5-5",
    max_tokens=4096,
    # no beta header; the toolset entry takes no name or display size
    tools=[{"type": "computer_toolset_20260801"}],
    messages=[{"role": "user", "content": "Open the display settings."}],
)
```

```typescript
await client.messages.create({
  model: "claude-opus-5-5",
  max_tokens: 4096,
  // no beta header; the toolset entry takes no name or display size
  tools: [{ type: "computer_toolset_20260801" }],
  messages: [{ role: "user", content: "Open the display settings." }]
});
```

```csharp
await client.Messages.Create(new MessageCreateParams
{
    Model = Model.ClaudeOpus5_5,
    MaxTokens = 4096,
    // no beta header; the toolset entry takes no name or display size
    Tools = [new ComputerToolset20260801()],
    Messages = [new UserMessageParam { Content = "Open the display settings." }],
});
```

```go
client.Messages.New(context.TODO(), anthropic.MessageNewParams{
	Model:     anthropic.ModelClaudeOpus5_5,
	MaxTokens: 4096,
	// no beta header; the toolset entry takes no name or display size
	Tools: []anthropic.ToolUnionParam{
		{OfComputerToolset20260801: &anthropic.ComputerToolset20260801Param{}},
	},
	Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock("Open the display settings.")),
	},
})
```

```java
MessageCreateParams params = MessageCreateParams.builder()
    .model(Model.CLAUDE_OPUS_5_5)
    .maxTokens(4096L)
    // no beta header; the toolset entry takes no name or display size
    .addTool(ComputerToolset20260801.builder().build())
    .addUserMessage("Open the display settings.")
    .build();

client.messages().create(params);
```

```php
$client->messages->create(
    model: Model::CLAUDE_OPUS_5_5,
    maxTokens: 4096,
    // no beta header; the toolset entry takes no name or display size
    tools: [ComputerToolset20260801::with()],
    messages: [['role' => 'user', 'content' => 'Open the display settings.']],
);
```

```ruby
client.messages.create(
  model: Anthropic::Model::CLAUDE_OPUS_5_5,
  max_tokens: 4096,
  # no beta header; the toolset entry takes no name or display size
  tools: [Anthropic::ComputerToolset20260801.new],
  messages: [{ role: "user", content: "Open the display settings." }]
)
```

### ツール呼び出し間のテキストは推論ブロックで返る

Claude Opus 5 では、モデルがツール呼び出しの間に書いたテキストは `text` ブロックで返ります。Claude Opus 5.5 では Claude Fable 5.1 と同じく、[進捗報告の `thinking` ブロック](https://platform.claude.com/docs/en/build-with-claude/thinking#progress-updates)として、各ツール呼び出しの前に最大 1 つ返ります。`thinking.display` が既定の `"omitted"` の場合、ブロックの `thinking` フィールドは空です。リクエストは成功しますが、このテキストを進捗として配信する画面ではツール呼び出しの間に報告が出ません。報告を表示するには `thinking` ブロックから読み取り、テキストが返る `display` を指定します。ベータ版の `"updates"`（ヘッダー `thinking-display-updates-2026-08-18`）は推論本文を非表示にして進捗報告を返し、`"summarized"` は両方を混在させて返します。空でない `thinking` ブロックは対応する `tool_use` ブロックの前に表示します。アシスタントターンのほかの部分と一緒に、ブロックをそのまま返します。[利用者向けの進捗報告](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5#user-facing-progress-updates)を参照してください。

### 安全性分類器とフォールバック

Claude Opus 5.5 は `stop_reason: "refusal"` とともに `stop_details` の分類を返すことがあります。分類器の対象は Claude Opus 5 より広く、`stop_details.category` に `"cyber"`、`"reasoning_extraction"` に加えて `"bio"` などが現れます。[拒否理由の分類表](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#refusal-response)を参照してください。拒否を処理し、[サーバー側のフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#server-side-fallback)または独自の再試行を設定します。サーバー側のフォールバックでは、`"reasoning_extraction"` で拒否した場合、拒否応答を返します。[拒否とフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)と[安全対策による拒否](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5#safeguard-refusals)を参照してください。

### 推奨する変更

1. **effort の段階を変えて改めて比較する**。Claude Opus 5.5 の推論の深さを指定するリクエストパラメーターは effort です。Claude Opus 5.5 の既定値は `medium` で、Claude Opus 5 の `high` より 1 段低いため、`effort` を省略したリクエストの挙動が変わります。品質を保てる場合は段階を下げ、難しい処理では段階を上げます。[effort](https://platform.claude.com/docs/en/build-with-claude/effort)を参照してください。
2. **モデル固有のプロンプト指示を再評価する**。Claude Opus 5 に合わせた指示が不要になる場合があります。[Claude Opus 5.5 のプロンプトガイド](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)を参照してください。推論を無効にしていた場合は[推論を無効にする前提で書いたプロンプト](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5#prompts-written-for-thinking-disabled)も参照してください。
3. 本番トラフィックを切り替える前に**開発環境でテストする**。

## Claude Opus 4.8 から Claude Opus 5.5 への移行

まず、置き換えるモデル ID を `claude-opus-4-8` として、[すべてのリクエストに共通する要件](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#request-requirements)、[各応答の推論を処理する](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-in-every-response)、[Claude Opus 5 から Claude Opus 5.5 への移行](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-5)の順に確認します。Claude Opus 4.8 は Claude Opus 5 と同じく次の性質があるため、Claude Opus 5 の節はすべて当てはまります。

- `thinking: {"type": "disabled"}`、強制ツール選択、`computer_20251124` を受理する。
- ツール呼び出し間のテキストを `text` ブロックで返す。
- effort の既定値は `high`。

次に[変更点](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#what-changed-from-claude-opus-4-8)で Claude Opus 4.8 と Claude Opus 5 の間で適用された変更を確認します。[移行チェックリスト](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migration-checklist)では最初の 2 グループが該当します。

### 変更点

1. **推論の設定を省略しても推論が有効になる**。Claude Opus 4.8 では明示的に指定した場合に推論が有効になります。Claude Opus 5.5 では `thinking` フィールドを省略しても推論が有効です。このようなコードには[各応答の推論を処理する](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-in-every-response)の全項目が当てはまります。従来から `thinking` フィールドを送っていないコードには、[推論設定の変更前後の例](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-cant-be-disabled)の削除対象はありません。
2. **プロンプトキャッシュの下限が下がる**。Claude Opus 5.5 のキャッシュを作成できる最小プロンプト長は 512 トークンです。Claude Opus 4.8 では 1,024 トークンでした。以前は短すぎたプロンプトもコードを変えずにキャッシュを作成できます。モデルごとの下限は[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#cache-limitations)を参照してください。
3. **Priority Tier は非対応**。Claude Opus 4.8 は [Priority Tier](https://platform.claude.com/docs/en/api/service-tiers#supported-models) に引き続き対応しています。Claude Opus 5.5 は非対応です。組織が Priority Tier を契約している場合は、キャパシティを別途計画します。

### 推奨する変更

次の変更は任意です。利用時の挙動を改善できる場合があります。

1. **タスク予算を検討する（ベータ版）**。エージェント処理では、[タスク予算](https://platform.claude.com/docs/en/build-with-claude/task-budgets)により、処理ループ全体で使えるトークン数をモデルに伝えられます。ベータヘッダー `task-budgets-2026-03-13` が必要です。
2. **会話途中でのツール変更を検討する（ベータ版）**。`role: "system"` メッセージでターン間にツールを追加または削除し、以前のターンの[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)のヒットを保てます。`tools` 配列を変更するとヒットしなくなります。この機能は 2 種類のベータヘッダーで有効にできます。使っているプラットフォームで両方が使える場合は、`inline-tools-2026-09-15` を送ります。
   - `inline-tools-2026-09-15` は Claude API、Claude Platform on AWS、Claude Models on Google Cloud (Anthropic managed)、Microsoft Foundry で使えます。
   - `mid-conversation-tool-changes-2026-07-01` は、Claude Models on Google Cloud (Google managed)、Amazon Bedrock と、`inline-tools-2026-09-15` に対応する 4 つのプラットフォームで使えます。[`tool_addition` ブロック内でツールを定義する](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#define-tools-in-a-message-beta)機能には対応しません。

## Claude Opus 4.7 から Claude Opus 5.5 への移行

まず、置き換えるモデル ID を `claude-opus-4-7` として、[すべてのリクエストに共通する要件](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#request-requirements)、[各応答の推論を処理する](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-in-every-response)、[Claude Opus 5 から Claude Opus 5.5 への移行](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-5)、[Claude Opus 4.8 から Claude Opus 5.5 への移行](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-4-8)の順に確認します。いずれも当てはまります。Claude Opus 4.7 は Claude Opus 4.8 と同じく `thinking: {"type": "disabled"}`、強制ツール選択、`computer_20251124` を受理します。effort の既定値は `high` で、明示的に指定した場合に推論が有効になります。

次の項目を確認します。Claude Opus 4.6 以前を使うコードは、Claude Opus 4.7 で互換性に影響した変更を扱う [Claude Opus 4.6 以前から Claude Opus 5.5 への移行](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-46)に進みます。[移行チェックリスト](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migration-checklist)では最初の 3 グループを参照してください。

### 変更点

ここで扱う項目に加え、互換性に影響する変更は前の節に記載されています。モデル ID を切り替えたあとに、次の項目を確認します。

1. **effort の段階ごとのトークン配分が変わる**。各段階の配分は Claude Opus 5.5 と Claude Opus 4.7 で異なります。Claude Opus 5.5 の既定値は `medium` で、Claude Opus 4.7 は `high` です。自分の評価データで effort の段階を変えて改めて比較し、Claude Opus 4.7 向けに調整した設定も見直します。[effort](https://platform.claude.com/docs/en/build-with-claude/effort)を参照してください。
2. **既定のコンテキストウィンドウは 100 万トークン**。Claude Opus 5.5 では既定で 100 万トークンの[コンテキストウィンドウ](https://platform.claude.com/docs/en/build-with-claude/context-windows)を使えます。旧モデルとの互換性のためにクライアントがコンテキストウィンドウのベータヘッダーを送っている場合は削除します。
3. **会話途中のシステムメッセージ**。[対応プラットフォーム](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#feature-availability)の Claude Opus 5.5 は、[配置の規則](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#limitations)を満たせば、`messages` 配列でユーザーターンの直後に `role: "system"` メッセージを受け付けます。最初から適用する指示は最上位の `system` フィールドに書きます。Claude Opus 4.7 は `messages` 内の `role: "system"` を 400 エラーで拒否します。指示の更新のために全履歴を組み立て直しているコードでは、システムメッセージに切り替えます。履歴を組み立て直すと 400 エラーが起きることがあり、[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)にもヒットしなくなります。
4. **拒否時の停止の詳細**。モデルがリクエストを拒否すると、Claude Opus 5.5 は停止理由 `refusal` とともに、拒否の分類を示す `stop_details` オブジェクトを返します。この挙動は常に有効です。Claude Opus 4.7 も同じオブジェクトを返すため、停止理由を扱うコードですでに読み取っていれば変更は不要です。まだ処理していない場合は[停止理由とフォールバック](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)を参照してください。Claude Opus 5.5 では拒否の分類が増えます。[安全性分類器とフォールバック](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#safety-classifiers-and-fallback)を参照してください。
5. **高速モード**。Claude Opus 5.5 の[高速モード](https://platform.claude.com/docs/en/build-with-claude/fast-mode)は、Claude API と[一部のクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)で使えます。Claude Opus 4.7 では `speed: "fast"` がエラーになります。Claude API で利用するにはリクエストに `speed: "fast"` を設定します。
6. **コンピューター操作ツールセットとブラウザー操作ツール**。Claude Opus 5.5 は `computer_toolset_20260801` ツールセットで[コンピューター操作](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)に対応し、Web ページ内のタスクに使う[ブラウザー操作ツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)にも対応します。Claude Opus 4.7 はどちらにも対応しません。`computer_20251124` をツールセットに移行するには、[コンピューター操作に関する互換性の変更](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#computer-use-toolset)を参照してください。

## Claude Opus 4.6 以前から Claude Opus 5.5 への移行

先に、前にある節を順に確認します。[すべてのリクエストに共通する要件](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#request-requirements)、[各応答の推論を処理する](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-in-every-response)、[Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-5)、[Claude Opus 4.8](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-4-8)、[Claude Opus 4.7](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-47) の各節です。Claude Opus 4.6 以前も `thinking: {"type": "disabled"}` と強制ツール選択を受理し、明示的に指定した場合に推論が有効になるため、前の節の変更も適用されます。Claude Opus 4.6 は `computer_20251124` を受理し、effort の既定値は `high` です。

次に、Claude Opus 4.7 で適用された以下の変更を反映します。置き換えるモデル ID は `claude-opus-4-6` です。[Claude Opus 4.5 以前](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-45)および [Claude 4.1 以前](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-4-1-or-earlier)を使う場合に必要な追加の変更は、それぞれの節にあります。[移行チェックリスト](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migration-checklist)は対象のモデル名があるグループまで確認します。

### 互換性を損なう変更

1. **拡張推論の廃止**。`thinking: {"type": "enabled", "budget_tokens": N}` は Claude Opus 4.7 以降では非対応で、400 エラーになります。[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking)（`thinking: {"type": "adaptive"}`）に切り替え、[effort パラメーター](https://platform.claude.com/docs/en/build-with-claude/effort)で推論の深さを調整します。Claude Opus 5.5 では適応型推論が常に有効なので、`thinking: {"type": "adaptive"}` を指定した場合と `thinking` フィールドを省略した場合の挙動は同じです。
   変更前（Claude Opus 4.6）。
   ```bash
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2026-10-21" \
     -H "content-type: application/json" \
     -d '{
       "model": "claude-opus-4-6",
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
   model: claude-opus-4-6
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
       model="claude-opus-4-6",
       max_tokens=16000,
       thinking={"type": "enabled", "budget_tokens": 10000},
       messages=[{"role": "user", "content": "..."}],
   )
   ```
   ```typescript
   await client.messages.create({
     model: "claude-opus-4-6",
     max_tokens: 16000,
     thinking: { type: "enabled", budget_tokens: 10000 },
     messages: [{ role: "user", content: "..." }]
   });
   ```
   ```csharp
   AnthropicClient client = new();

   var parameters = new MessageCreateParams
   {
       Model = Model.ClaudeOpus4_6,
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
   	Model:     anthropic.ModelClaudeOpus4_6,
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
       .model(Model.CLAUDE_OPUS_4_6)
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
       model: Model::CLAUDE_OPUS_4_6,
       thinking: ['type' => 'enabled', 'budgetTokens' => 10000],
   );
   ```
   ```ruby
   client = Anthropic::Client.new

   message = client.messages.create(
     model: Anthropic::Model::CLAUDE_OPUS_4_6,
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
   変更後（Claude Opus 5.5）。モデル ID、`thinking`、`output_config` の行が変わります。
   ```bash
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2026-10-21" \
     -H "content-type: application/json" \
     -d '{
       "model": "claude-opus-5-5",
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
   model: claude-opus-5-5
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
       model="claude-opus-5-5",
       max_tokens=16000,
       thinking={"type": "adaptive"},
       output_config={"effort": "high"},  # or "max", "xhigh", "medium", "low"
       messages=[{"role": "user", "content": "..."}],
   )
   ```
   ```typescript
   await client.messages.create({
     model: "claude-opus-5-5",
     max_tokens: 16000,
     thinking: { type: "adaptive" },
     output_config: { effort: "high" }, // or "max", "xhigh", "medium", "low"
     messages: [{ role: "user", content: "..." }]
   });
   ```
   ```csharp
   AnthropicClient client = new();

   var parameters = new MessageCreateParams
   {
       Model = Model.ClaudeOpus5_5,
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
   	Model:     anthropic.ModelClaudeOpus5_5,
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
       .model(Model.CLAUDE_OPUS_5_5)
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
       model: Model::CLAUDE_OPUS_5_5,
       thinking: ['type' => 'adaptive'],
       outputConfig: ['effort' => 'high'], // or 'max', 'xhigh', 'medium', 'low'
   );
   ```
   ```ruby
   client = Anthropic::Client.new

   message = client.messages.create(
     model: Anthropic::Model::CLAUDE_OPUS_5_5,
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
   適応型推論では、プロンプトと [effort パラメーター](https://platform.claude.com/docs/en/build-with-claude/effort)で推論を調整します。推論量の調整には手動予算から effort に切り替えます。`budget_tokens` の値を換算する代わりに、自分の評価データで effort の段階を変えて比較します。各段階の用途は [effort の段階の表](https://platform.claude.com/docs/en/build-with-claude/effort#effort-levels)、このモデルの目安は [Claude Opus 5.5 の推奨 effort](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-opus-5-5)にあります。
2. **サンプリングパラメーターの廃止**。`temperature`、`top_p`、`top_k` を省略します。Claude Opus 5.5 の挙動はプロンプトで調整します。旧モデルでも、`temperature = 0` で出力が毎回同じになる保証はありませんでした。
3. **既定では推論テキストを省略する**。Claude Opus 4.7 以降でも推論ブロックは応答ストリームに現れますが、明示的に表示を指定するまで `thinking` フィールドは空です。推論の要約テキストを既定で返した Claude Opus 4.6 から変更されています。要約を受け取るには[各応答の推論を処理する](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-in-every-response)の項目 4 を参照してください。
4. **トークンの数え方の変更**。Claude Opus 4.7 から新しいトークナイザーを採用しており、Claude Opus 5.5 を含む後続の Opus モデルもこれを使います。さまざまなタスクの性能向上に寄与します。テキストを処理する場合、Claude Opus 4.7 より前のモデルに比べてトークン数が約 1〜1.35 倍（内容により最大約 35% 増）になることがあります。
   [`/v1/messages/count_tokens`](https://platform.claude.com/docs/en/build-with-claude/token-counting) が返すトークン数は Claude Opus 5.5 と Claude Opus 4.6 で異なります。トークンの効率は処理の内容によって変わります。
   圧縮を始める条件も含めて `max_tokens` に余裕を持たせます。クライアント側でトークン数を見積もる処理や、トークン数と文字数の比率を固定している処理を再検証します。[トークン数を数える](https://platform.claude.com/docs/en/build-with-claude/token-counting)エンドポイントで確認してください。プロンプトの調整、[`task_budget`](https://platform.claude.com/docs/en/build-with-claude/task-budgets)、[`effort`](https://platform.claude.com/docs/en/build-with-claude/effort)で費用を調整できますが、モデルの能力との兼ね合いがあります。
5. **事前入力の廃止（Claude Opus 4.6 で適用済み）**。アシスタントメッセージを事前入力すると、Claude Opus 4.6 以降の Opus モデル（Claude Opus 5.5 を含む）では 400 エラーになります。Claude Opus 4.5 以前から移行する場合は変更が必要です。[構造化出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)やシステムプロンプトの指示を使います。

### 挙動の変化

Claude Opus 4.7 では Claude Opus 4.6 から挙動が変わりました。API の互換性を損なう変更とは別に、コードや実行環境に関わる点が 3 つあります。

1. **エージェント処理での進捗報告**。Claude Opus 4.7 は長いエージェント処理の間、より規則的に利用者へ詳しい進捗を伝えます。「ツールを 3 回呼び出すごとに進捗を要約する」など、途中経過を強制する仕組みを追加している場合は、外して試します。Claude Opus 5.5 では報告は `thinking` ブロックで返り、既定の `thinking.display` では空です。報告を受け取るには[ツール呼び出し間のテキストは推論ブロックで返る](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#text-between-tool-calls)、報告の長さや内容を調整するには[利用者向けの進捗報告](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5#user-facing-progress-updates)を参照してください。
2. **リアルタイムのサイバーセキュリティ対策**。Claude Opus 4.7 で導入され、禁止されている内容や高いリスクを伴う内容のリクエストは拒否される場合があります。ペネトレーションテスト、脆弱性研究、レッドチーム活動などの正当なセキュリティ業務には、[Cyber Verification Program](https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude-opus-and-sonnet) の申請手続きで制限の緩和を依頼できます。申請経路は Claude へのアクセス方法によって異なります。
3. **高解像度画像への対応**。Claude Opus 4.7 は、高解像度画像に対応した最初の Claude モデルです。画像の長辺の上限は以前のモデルの 1,568 ピクセルから 2,576 ピクセルになりました。画像を多く扱う処理を改善でき、特にコンピューター操作、スクリーンショットの理解、文書の分析で役立ちます。
   高解像度対応は自動で適用されます。次の 2 点を考慮します。
   - 元の解像度で送る画像のトークン数は、以前のモデルの最大約 3 倍になります。1 枚あたりの上限は約 1,600 トークンから 4,784 トークンになります。画像を多く使う処理では `max_tokens` と費用の見積もりを見直します。細部が不要な場合は解像度を下げて送ります。
   - Claude Opus 4.7 が返す指示位置や境界ボックスの座標は実際の画像ピクセルと 1 対 1 に対応するため、倍率の換算は不要です。
   詳細は [Claude Opus 4.7 の高解像度画像対応](https://platform.claude.com/docs/en/build-with-claude/vision#high-resolution-image-support-on-claude-opus-4-7)を参照してください。

プロンプトに関する違いは [Claude Opus 5.5 のプロンプトガイド](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)と[プロンプトのベストプラクティス](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)を参照してください。

### Claude Opus 4.5 以前からの移行

Claude Opus 4.5、Claude Opus 4.1、またはそれ以前のモデルから直接 Claude Opus 5.5 へ移行する場合は、次の手順を使います。

1. このページの冒頭からこの節まで順に確認し、[Claude Opus 4.6 からの移行で互換性を損なう変更](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#opus-46-breaking-changes)も確認します。
2. この節の変更を適用します。これらは Claude Opus 4.5 から Claude Opus 4.7 までに適用された変更です。
3. Claude Opus 4.1 以前を使用している場合は、[Claude 4.1 以前からの移行](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-4-1-or-earlier)へ進みます。

#### 互換性を損なう変更

1. **事前入力の廃止**は、[Claude Opus 4.6 からの移行で互換性を損なう変更](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#opus-46-breaking-changes)に記載されています。
2. **ツールパラメーターの引用符処理**。Claude Opus 4.6 以降のツール呼び出し引数では、JSON 文字列のエスケープ表記が以前とわずかに異なる場合があります。例として Unicode エスケープやスラッシュのエスケープがあります。ツール呼び出しの `input` を生の文字列として解析している場合は、処理を確認します。`json.loads()` や `JSON.parse()` などの標準 JSON パーサーは、この違いを自動で処理できます。

#### 推奨する変更

最初の変更は Claude Opus 5.5 で必須です。ほかの変更は推奨です。

1. **適応型推論に移行する（必須）**。`thinking: {"type": "enabled", "budget_tokens": N}` は Claude Opus 4.7 以降で 400 エラーになります。変更前後の例は[Claude Opus 4.6 からの移行で互換性を損なう変更](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#opus-46-breaking-changes)の項目 1 にあります。この移行では、`client.beta.messages.create()`（csharp: `client.Beta.Messages.Create()`、go: `client.Beta.Messages.New()`、java: `client.beta().messages().create()`、php: `$client->beta->messages->create()`、cli: `ant beta:messages create`）から `client.messages.create()`（csharp: `client.Messages.Create()`、go: `client.Messages.New()`、java: `client.messages().create()`、php: `$client->messages->create()`、cli: `ant messages create`）に切り替えます。適応型推論と effort には SDK のベータ名前空間やベータヘッダーが不要です。
2. **effort のベータヘッダーを削除する**。effort パラメーターにベータヘッダーは不要なので、リクエストから `effort-2025-11-24` を削除します。
3. **細かな単位でのツールストリーミングのベータヘッダーを削除する**。この機能にベータヘッダーは不要なので、リクエストから `fine-grained-tool-streaming-2025-05-14` を削除します。
4. **ツール呼び出し間の推論のベータヘッダーを削除する**。適応型推論に対応するモデルでは、適応型推論を使うとツール呼び出し間でも自動で推論します。リクエストから `interleaved-thinking-2025-05-14` を削除します。
5. **`output_config.format` に移行する**。構造化出力を使う場合は `output_format={...}` を `output_config={"format": {...}}` に変更します。`output_format` は非推奨で、今後削除されます。引き続き使うにはベータヘッダー `structured-outputs-2025-11-13` が必要です。ヘッダーを省略すると API は 400 エラーを返します。Python SDK（v1.0 以降）でスキーマの辞書を `output_format={...}` として渡すと `TypeError` になるため、`output_config` を使います。Pydantic モデルを `output_format=Model` として `parse()` や `stream()` に渡す場合は、SDK が `output_config` に変換するため、変更やベータヘッダーは不要です。

### Claude 4.1 以前からの移行

Claude Opus 4.1 以前のモデルから直接 Claude Opus 5.5 へ移行する場合は、次の手順を使います。

1. このページの冒頭から[Claude Opus 4.5 以前からの移行](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-45)まで順に確認します。
2. この節の追加の変更を適用します。

#### 互換性を損なう追加の変更

1. **サンプリングパラメーターを削除する**。[サンプリングパラメーターの廃止](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#opus-46-breaking-changes)に記載されています。
2. **ツールのバージョンを更新する**
   Claude 3.x モデルからの移行では、互換性を損なう変更です。
   現在のツールバージョンに更新し、`undo_edit` コマンドを使うコードを削除します。
   ```python
   # Before
   tools = [{"type": "text_editor_20250124", "name": "str_replace_editor"}]

   # After
   tools = [{"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"}]
   ```
   ```typescript
   // Before
   const legacyTools = [{ type: "text_editor_20250124", name: "str_replace_editor" }];

   // After
   const tools = [{ type: "text_editor_20250728", name: "str_replace_based_edit_tool" }];
   ```
   ```csharp
   var parameters = new MessageCreateParams
   {
       // Before: {"type": "text_editor_20250124", "name": "str_replace_editor"}
       // After:
       Tools = [new ToolTextEditor20250728()],
       // ...
   };
   ```
   ```go
   params := anthropic.MessageNewParams{
   	// Before: {"type": "text_editor_20250124", "name": "str_replace_editor"}
   	// After:
   	Tools: []anthropic.ToolUnionParam{
   		{OfTextEditor20250728: &anthropic.ToolTextEditor20250728Param{}},
   	},
   	// ...
   }
   ```
   ```java
   MessageCreateParams params = MessageCreateParams.builder()
       // Before: {"type": "text_editor_20250124", "name": "str_replace_editor"}
       // After:
       .addTool(ToolTextEditor20250728.builder().build())
       // ...
       .build();
   ```
   ```php
   $message = $client->messages->create(
       // Before: ['type' => 'text_editor_20250124', 'name' => 'str_replace_editor']
       // After:
       tools: [new ToolTextEditor20250728()],
       // ...
   );
   ```
   ```ruby
   # Before
   legacy_tools = [{ type: "text_editor_20250124", name: "str_replace_editor" }]

   # After
   tools = [{ type: "text_editor_20250728", name: "str_replace_based_edit_tool" }]
   ```
   - **テキストエディター**。`text_editor_20250728` と `str_replace_based_edit_tool` を使います。詳細は[テキストエディターツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool)を参照してください。
   - **コード実行**。`code_execution_20260521` に更新します。移行手順は[コード実行ツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool#upgrade-to-latest-tool-version)を参照してください。
   - **コンピューター操作**。Claude Opus 5.5 は `computer_20250124` を受理しないため、`computer_toolset_20260801` ツールセットに切り替えます。Amazon Bedrock では `computer_20251124` も使えます。[コンピューター操作に関する互換性の変更](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#computer-use-toolset)を参照してください。
3. **停止理由 `refusal` を処理する**
   アプリケーションを更新し、[停止理由 `refusal` を処理する](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/handle-streaming-refusals)ようにします。
   ```python
   response = client.messages.create(...)

   if response.stop_reason == "refusal":
       # Handle refusal appropriately
       pass
   ```
   ```typescript
   const response = await client.messages.create(/* ... */);

   if (response.stop_reason === "refusal") {
     // Handle refusal appropriately
   }
   ```
   ```csharp
   var response = await client.Messages.Create(...);

   if (response.StopReason?.Value() == StopReason.Refusal)
   {
       // Handle refusal appropriately
   }
   ```
   ```go
   response, _ := client.Messages.New(ctx, params) // your existing request

   if response.StopReason == anthropic.StopReasonRefusal {
   	// Handle refusal appropriately
   }
   ```
   ```java
   Message response = client.messages().create(...);

   StopReason reason = response.stopReason().orElse(StopReason.END_TURN);
   if (reason.equals(StopReason.REFUSAL)) {
       // Handle refusal appropriately
   }
   ```
   ```php
   $response = $client->messages->create(...);

   if ($response->stopReason === 'refusal') {
       // Handle refusal appropriately
   }
   ```
   ```ruby
   response = client.messages.create(...)

   if response.stop_reason == :refusal
     # Handle refusal appropriately
   end
   ```
4. **停止理由 `model_context_window_exceeded` を処理する**
   Claude 4.5 以降では、生成が指定した `max_tokens` に達する前にコンテキストウィンドウの上限で停止すると、停止理由 `model_context_window_exceeded` を返します。アプリケーションを更新し、この停止理由を処理します。
   ```python
   response = client.messages.create(...)

   if response.stop_reason == "model_context_window_exceeded":
       # Handle context window limit appropriately
       pass
   ```
   ```typescript
   const response = await client.messages.create(/* ... */);

   if (response.stop_reason === "model_context_window_exceeded") {
     // Handle context window limit appropriately
   }
   ```
   ```csharp
   var response = await client.Messages.Create(...);

   if (response.StopReason?.Raw() == "model_context_window_exceeded")
   {
       // Handle context window limit appropriately
   }
   ```
   ```go
   response, _ := client.Messages.New(ctx, params) // your existing request

   if response.StopReason == "model_context_window_exceeded" {
   	// Handle context window limit appropriately
   }
   ```
   ```java
   Message response = client.messages().create(...);

   StopReason reason = response.stopReason().orElse(StopReason.END_TURN);
   if (reason.equals(StopReason.of("model_context_window_exceeded"))) {
       // Handle context window limit appropriately
   }
   ```
   ```php
   $response = $client->messages->create(...);

   if ($response->stopReason === 'model_context_window_exceeded') {
       // Handle context window limit appropriately
   }
   ```
   ```ruby
   response = client.messages.create(...)

   if response.stop_reason == :model_context_window_exceeded
     # Handle context window limit appropriately
   end
   ```
5. **ツールパラメーターの末尾の改行を確認する**
   Claude 4.5 以降は、以前は取り除いていたツール呼び出しの文字列パラメーターの末尾の改行を保持します。ツールのパラメーターが文字列の完全一致を前提とする場合は、末尾の改行を処理できることを確認します。
6. **挙動の変化に合わせてプロンプトを更新する**
   Claude 4 以降は、より簡潔で直接的な書き方で応答し、明示的な指示を必要とします。調整にあたっては[プロンプトのベストプラクティス](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)を参照してください。

#### 推奨する追加の変更

- **ベータヘッダー**。`token-efficient-tools-2025-02-19` と `output-128k-2025-02-19` を削除します。Claude 4 以降の全モデルはトークンを効率よく使うツール利用を標準で備えており、これらのヘッダーに効果はありません。

## Claude Sonnet 5 から Claude Opus 5.5 への移行

置き換えるモデル ID を `claude-sonnet-5` として、[すべてのリクエストに共通する要件](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#request-requirements)、[各応答の推論を処理する](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#thinking-in-every-response)、[Claude Opus 5 から Claude Opus 5.5 への移行](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migrating-from-claude-opus-5)の順に確認します。Claude Sonnet 5 は Claude Opus 5 と次の性質を共有するため、Claude Opus 5 の節の変更はすべて当てはまります。

- 既定で推論が有効で、`thinking: {"type": "disabled"}` を受理する。すべての effort の段階でこの指定を受理する。Claude Opus 5 には段階の制約がある。
- 強制ツール選択と `computer_20251124` ツールを受理する。
- ツール呼び出し間のテキストを `text` ブロックで返す。
- effort の既定値は `high`。

手動の拡張推論、サンプリングパラメーター、アシスタントメッセージの事前入力は Claude Sonnet 5 と Claude Opus 5.5 の両方で 400 エラーになります。これらの設定の扱いは共通です。Claude Opus 4.8、4.7、4.6 の節にある必須の変更は、この移行には適用されません。

### 変更点

1. **会話途中のシステムメッセージ**。[対応プラットフォーム](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#feature-availability)の Claude Opus 5.5 は、[配置の規則](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages#limitations)を満たせば、`messages` 配列でユーザーターンの直後に `role: "system"` メッセージを受け付けます。Claude Sonnet 5 はこの機能に対応していません。指示の更新のためにメッセージ履歴を再構築している場合は、システムメッセージに切り替えます。履歴を再構築すると 400 エラーが起きる場合があり、[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)にもヒットしなくなります。
2. **プロンプトキャッシュの下限が下がる**。Claude Opus 5.5 でキャッシュを作れる最小プロンプト長は 512 トークンです。Claude Sonnet 5 では 1,024 トークンでした。短すぎてキャッシュできなかったプロンプトもコードを変えずにキャッシュを作成できます。モデルごとの下限は[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#cache-limitations)を参照してください。
