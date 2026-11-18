---
url: "https://platform.claude.com/docs/en/models/fable-5-2/migration-guide"
title: "Claude Fable 5.2 and Claude Mythos 5.2 migration guide"
fetched_at: "2026-11-18T22:32:30+09:00"
source_sha256: "f6602973881b2aac48e3ebd8b165a79f49a9e68ef49493b4c7056fb4557d5431"
source_sha256_of: "dom"
fetch_method: "html_file"
source_lang: "en"
translated_by: "GPT-6"
fetched_by: "wiki_fetch.py 0.1"
---

# Claude Fable 5.2 と Claude Mythos 5.2 への移行ガイド

Claude Fable 5.1、Claude Mythos 5.1、Claude Opus 5.5、またはそれ以前の Claude Fable、Claude Mythos、Claude Opus から、Claude Fable 5.2 や Claude Mythos 5.2 へ移行するためのガイドです。移行先のモデル ID、互換性を損なう変更、移行チェックリストを掲載しています。

このガイドは [Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) を使うコードの移行を扱います。[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) を使う場合、基本の変更はモデル名の更新です。

Claude Code にコードの移行を任せる

```text
/claude-api migrate this project to claude-fable-5-2
```

Claude Managed Agents のエージェントにアドバイザーを設定している場合は、エージェント本体とともにアドバイザーの `model` も `claude-fable-5-2` か `claude-mythos-5-2` に変更します。[Claude Fable 5.2 の実行側には Claude Fable 5.2 か Claude Mythos 5.2 のアドバイザーが必要](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-advisor-pairs)を参照してください。エージェントの `model` オブジェクトに `speed: "fast"` があれば削除します。

以下の節では、Claude Fable 5.1、Claude Mythos 5.1、Claude Opus 5.5、またはそれ以前の Claude Fable、Claude Mythos、Claude Opus から Claude Fable 5.2 や Claude Mythos 5.2 に切り替える手順を示します。変更点は [Claude Fable 5.2 の新機能](https://platform.claude.com/docs/en/models/fable-5-2/whats-new-fable-5-2)、挙動の違いとモデルに合ったプロンプトの書き方は [Claude Fable 5.2 のプロンプトガイド](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)を参照してください。

Claude Fable 5.2 は、Claude API、[Amazon Bedrock（`bedrock-runtime`）](https://platform.claude.com/docs/en/build-with-claude/claude-on-amazon-bedrock-legacy)、[Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)、[Claude Models on Google Cloud (Anthropic managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/anthropic-managed)、[Claude Models on Google Cloud (Google managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)、[Microsoft Foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry) で利用できます。[Claude Mythos 5.2](https://platform.claude.com/docs/en/models/mythos-5-2/overview) は同じ機能を備え、[Cyber Verification Program](https://support.claude.com/en/articles/14604842) など Anthropic の認証プログラムで確認された組織に提供されます。

`claude-fable-5-2` と `claude-mythos-5-2` に共通する基本設定は次のとおりです。

- **推論**。Claude Fable 5.1 と同じく、[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking)が常に有効です。いつどの程度推論するかをモデルが判断し、[effort](https://platform.claude.com/docs/en/build-with-claude/effort) パラメーターで深さを調整できます。`thinking: {type: "disabled"}` と手動の拡張推論（`thinking: {type: "enabled", budget_tokens: N}`）はいずれも 400 エラーになります。
- **effort**。Claude Fable 5.1 と同じく、[effort](https://platform.claude.com/docs/en/build-with-claude/effort) の全 5 段階に対応し、既定値は `high` です。[Claude Fable 5.2 の推奨 effort](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-fable-5-2)を参照してください。
- **事前入力**。Claude Fable 5.1 と同じく、アシスタントメッセージの先頭を事前入力すると 400 エラーになります。指示はシステムプロンプトに書きます。
- **サンプリングパラメーター**。Claude Fable 5.1 と同じく、`temperature`、`top_p`、`top_k` を省略します。400 エラーになる値は[サンプリングパラメーター](https://platform.claude.com/docs/en/build-with-claude/thinking#sampling-parameters)を参照してください。
- **ツールの選択**。既定の `{type: "auto"}` と `{type: "none"}` に対応します。Claude Fable 5.1 と同じく、`{type: "any"}` や `{type: "tool", name: "..."}` でツール呼び出しを強制すると 400 エラーになります。
- **構造化出力**。Claude Fable 5.1 と同じく、[顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)（CMEK）を使う組織では、どちらのモデルも[構造化出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)に対応しません。厳密なツール利用と JSON 出力の両方が対象です。その環境で `strict: true` や `output_config.format` を指定している場合は削除し、コードで出力を検証します。
- **モデル切り替え時の推論の保持**。Claude API と Claude Models on Google Cloud (Google managed) では、Claude Fable 5.2 と Claude Mythos 5.2 が互いの推論ブロックを読み取れます。Claude Opus 5.5、Claude Sonnet 5.5、Claude Haiku 5.5 などのほかのモデルが生成したブロックも読み取れます。この 2 モデルが生成したブロックを読み取れるのは、互いのモデルだけです。詳しくは [Claude API でモデルを切り替えても推論が保持される組み合わせ](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#which-model-switches-keep-reasoning)を参照してください。
- **アカウントにひも付く推論**。Claude Fable 5.2 と Claude Mythos 5.2 の推論ブロックは、生成元またはそれにリンクしたアカウントで使えます。別のアカウントから送ると、API はモデルに渡す前にブロックを取り除き、リクエストは成功します。Claude API と Claude Models on Google Cloud (Google managed) でベータヘッダー `thinking-binding-controls-2026-08-01` を送ると、応答の `input_transformations` に、取り除いたブロックごとに `reason: "organization_binding_mismatch"` が記録されます。[アカウントとクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#account-bound-thinking)を参照してください。
- **コンテキストウィンドウと出力**。既定の[コンテキストウィンドウは 100 万トークン](https://platform.claude.com/docs/en/build-with-claude/context-windows)で、1 リクエストあたり最大 128,000 トークンを出力できます。
- **料金**。100 万トークンあたり入力 8 米ドル（USD）、出力 40 米ドルです。Claude Fable 5.1 と Claude Mythos 5.1 では、それぞれ 10 米ドル、50 米ドルでした。プロンプトキャッシュの読み取りは 100 万トークンあたり 0.20 米ドルで、以前の両モデルでは 0.25 米ドルでした。[料金](https://platform.claude.com/docs/en/about-claude/pricing)を参照してください。
- **データ保持**。Claude Fable 5.1 と Claude Mythos 5.1 と同様に、両モデルは対象モデル（Covered Models）に指定され、データの 30 日間保持が必要です。Anthropic が明示的に承認した場合に限り、データ保持なし（ZDR）の契約で利用できます。Claude API では、30 日間保持を設定していない組織またはワークスペースからのリクエストは 400 の `invalid_request_error` になります。ZDR 契約の組織は Anthropic の担当チームに問い合わせるか、ワークスペースごとに保持を設定してください。各プラットフォームの詳細は[モデル別のデータ保持要件](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements)を参照してください。
- **Priority Tier**。どちらのモデルも [Priority Tier](https://platform.claude.com/docs/en/api/service-tiers#supported-models) では使えません。
- **高速モード**。どちらのモデルも Messages API のリクエストで[高速モード](https://platform.claude.com/docs/en/build-with-claude/fast-mode)を使えます。モデルごとの対応プラットフォームは[高速モードの提供状況](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)を参照してください。

2 つのモデルには次の違いがあります。

- **提供条件**。Claude API で Claude Fable 5.2 を使う際に承認は不要です。Claude Mythos 5.2 は [Cyber Verification Program](https://support.claude.com/en/articles/14604842) など Anthropic の認証プログラムで確認された組織に提供されます。アクセスを希望する場合は、用途に合うプログラムに申請するか、Anthropic の担当チームへお問い合わせください。
- **レート制限**。Claude Fable 5.2 には独自のレート制限があり、Claude Fable 5.1 と Claude Fable 5 が共有する制限とは別に適用されます。Claude Mythos 5.2 は Claude Mythos 5.1 と Claude Mythos 5 と同じ制限を共有します。[レート制限](https://platform.claude.com/docs/en/api/rate-limits#rate-limits)を参照してください。

## Claude Fable 5.1 から Claude Fable 5.2 への移行

大半はモデルを差し替えるだけで移行できます。API の仕様、常に有効な適応型推論、強制ツール選択の制約、拒否の処理、`stop_details` の分類、データ保持要件は Claude Fable 5.1 と共通です。料金は Claude Fable 5.2 が 100 万トークンあたり入力 8 米ドル（USD）、出力 40 米ドルで、Claude Fable 5.1 の入力 10 米ドル、出力 50 米ドルより下がります。コードに影響する変更は 4 つあります。過去のターンの編集を検出する[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)に失敗すると 400 エラーになります（[別の会話にひも付いた推論ブロック](https://platform.claude.com/docs/en/api/errors#thinking-block-conversation-mismatch)を参照）。Claude Fable 5.1 は Claude Fable 5.2 の推論ブロックを読み取れません。従来のコンピューター操作ツール `computer_20251124` は、Amazon Bedrock を除くすべてのプラットフォームで 400 エラーになります。アドバイザーツールを使う場合、Claude Fable 5.2 が実行側なら、アドバイザーには Claude Fable 5.2 または Claude Mythos 5.2 だけを指定できます。

### モデル名を更新する

```python
model = "claude-fable-5-1"  # Before
model = "claude-fable-5-2"  # After
```

Amazon Bedrock を除くすべてのプラットフォームで、モデル ID は `claude-fable-5-2` です。Amazon Bedrock では `global.anthropic.claude-fable-5-2` または `us.anthropic.claude-fable-5-2` を使い、`bedrock-runtime` エンドポイントでのみ利用できます。

### 互換性を損なう変更

1. **先頭部分の照合に失敗すると 400 エラーになる**。Claude Fable 5.2 では各リクエストで[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)を行います。会話の途中で `system`、`tools`、または過去のメッセージを変更したあとに推論ブロックを送り返すと照合に失敗し、400 エラーになります。
   Claude Code、claude.ai、[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview)、[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) が会話履歴を管理している場合、変更は不要です。コードで `messages` 配列を組み立てている場合は、リクエスト間の処理を[システムプロンプト、ツール、履歴をコードで変更する場合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#what-to-check)と照らし合わせてください。リクエスト間でこうした変更を行うと、変更箇所より後ろにある既存の推論は無効になります。後続のリクエストで送り返すと次の 400 エラーになります。
   ```text
   messages.5.content.0: Invalid `signature` in `thinking` block. The block is bound to a different conversation. Remove the block, or set `thinking.block_binding.prefix_mismatch_behavior` to "drop_block". That setting requires the `thinking-binding-controls-2026-08-01` value in the `anthropic-beta` header.
   ```
   同じリクエスト本体を再送してもエラーは解消しません。本番のトラフィックを切り替える前に、現在の Claude Fable 5.1 または Claude Opus 5.5 に対して[先頭部分の照合に失敗する処理を検出するテスト](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/fix-bound-to-a-different-conversation#how-to-tell-whether-your-integration-is-impacted)を実行します。[MCP コネクター](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)を使っていて[サーバーのツール一覧を固定していない](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector#pin-mcp-tool-list)場合は、`claude-fable-5-2` に対してもテストします。Claude Fable 5.2 の推論ブロックでは、リクエスト間にツール一覧が変わると編集として扱われます。Claude Fable 5.1 や Claude Opus 5.5 のブロックでは編集として扱われません。各パターンの対処は[先頭部分の照合を保ったままツールや指示を変更する](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/change-tools-or-instructions)を参照してください。
   本番環境で不一致が必ずコードの不具合を意味するなら、`prefix_mismatch_behavior` は既定の `"error"` のままにします。原因を修正する間、影響を受けたブロックを取り除いて処理を続けるには `"drop_block"` にします。[ブロックを取り除くと出力トークンが増える場合がある](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/fix-bound-to-a-different-conversation#drop-block-cost)ため、一時的な対応として使います。
   Claude Fable 5.1 や Claude Opus 5.5 の会話は Claude Fable 5.2 で続けられます。会話内の `system`、`tools`、過去のメッセージを変更していた場合は、400 エラーが発生する可能性があります。[別の会話にひも付いた推論ブロック](https://platform.claude.com/docs/en/api/errors#thinking-block-conversation-mismatch)を参照してください。
2. **Claude Fable 5.1 は Claude Fable 5.2 の推論ブロックを読み取れない**。Claude API と Claude Models on Google Cloud (Google managed) では、Claude Fable 5.2 が Claude Fable 5.1 のブロックを読み取るため、`claude-fable-5-1` から `claude-fable-5-2` に会話を移しても以前の推論が保持されます。Claude Fable 5.1 に戻す場合、そのモデルは Claude Fable 5.2 のブロックを読み取れません。
   ルーターによる切り替え、クライアント側での再試行、[分類器による拒否時のフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)によって、Claude Fable 5.2 から Claude Fable 5.1 などのモデルに会話が移ると、API は移行先で読み取れないブロックを取り除きます。リクエストは成功し、取り除いた入力トークンは課金されません。移行先はその推論なしで処理するため、切り替え後の最初のターンで費用と応答時間が増える場合があります。
   ベータヘッダー `thinking-binding-controls-2026-08-01` を送ると、取り除いたブロックごとに `input_transformations` に `reason: "model_binding_mismatch"` が記録されます。[モデルを切り替えて元に戻す](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#switching-models)を参照してください。
3. **コンピューター操作を `computer_20251124` からツールセットに移す**。Amazon Bedrock を除くすべてのプラットフォームで、`tools` に種類が `computer_20251124` の項目を入れると 400 エラーになります。`computer_toolset_20260801` ツールセットを宣言し、ベータヘッダーを削除して、`name` や画面の寸法を付けずに送ります。次にエージェントのループをツールセットに対応させます（[`computer_20251124` から移行する](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool#migrate-from-computer-20251124)を参照）。Amazon Bedrock では Claude Fable 5.2 と Claude Mythos 5.2 が従来のツールを受理します。InvokeModel API ではリクエスト本体の `anthropic_beta` 配列に `computer-use-2025-11-24` を入れます。
4. **Claude Fable 5.2 の実行側には Claude Fable 5.2 か Claude Mythos 5.2 のアドバイザーが必要**。ベータ版の[アドバイザーツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)では、アドバイザーの能力が実行側と同等以上である必要があります。Claude Fable 5.2 または Claude Mythos 5.2 を実行側に使う場合、受理するアドバイザーは Claude Fable 5.2 または Claude Mythos 5.2 に限られます。Claude Fable 5.1 や Claude Mythos 5.1 などを指定すると、400 の `invalid_request_error` になります。[モデルの互換性](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#model-compatibility)を参照してください。
   実行側のモデル ID を変更するときは、アドバイザーツール定義の `model` を `claude-fable-5-2` か `claude-mythos-5-2` に設定します。アドバイザーの `model` の変更は `tools` の編集に当たるので、新しい会話から変更を適用します。変更後に以前の推論ブロックを送り返すと[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)に失敗します。`prefix_mismatch_behavior` を `"drop_block"` にしていなければ 400 エラーになります。
   現在の実行側を維持してアドバイザーだけを変更する場合は、アドバイザーの `model` に `claude-fable-5-2` を指定します。すべての実行側モデルが受理します。
   Claude Fable 5.2 のアドバイザーは助言を暗号化して返します。コードで助言のテキストを読む場合は[結果の種類](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#result-variants)を参照してください。
   [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) のエージェントにアドバイザーがある場合も、同じモデル要件が適用されます。エージェントのモデルを変更するときは、そのアドバイザーの `model` も `claude-fable-5-2` か `claude-mythos-5-2` に設定します。[セッションにアドバイザーを設定する](https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration#give-the-session-an-advisor)を参照してください。

### 挙動の変化

1. **effort が `medium` 以上の場合、プロンプトで推論を減らすよう求めても推論する**。Claude Fable 5.1 は通常「熟考せず直接答えてください」といった指示に従います。Anthropic の試験では、この指示を与えても Claude Fable 5.2 は `medium` 以上で推論しました。該当する指示を削除して effort を下げます。[effort を調整する](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#calibrate-effort)を参照してください。
2. **effort が高いと、モデルは自分の作業を見直すサブエージェントを起動できる**。Anthropic はエージェント型のコーディング製品で、`xhigh` や `max` などの設定時に Claude Fable 5.2 がサブエージェントで自分の作業を見直すことを確認しました。同じタスクで Claude Fable 5.1 はこの処理を行いませんでした。サブエージェントがセッション費用の大きな部分を占める場合があります。[サブエージェントの利用を見込む](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#set-expectations-for-subagents)を参照してください。
3. **`max_tokens` が小さいとテキストを返す前に上限に達することがある**。推論トークンも `max_tokens` に含まれるため、`max_tokens` が小さいリクエストは `thinking` ブロックのあと、テキストを生成する前に `stop_reason: "max_tokens"` で停止することがあります。Claude Fable 5.1 の推論を抑えられたプロンプトでも、Claude Fable 5.2 は effort が `medium` 以上なら推論することがあります。従来この指示で小さな `max_tokens` に収めていたリクエストは、テキストを返す前にトークンを使い切る可能性があります。推論に使う分を見込んで `max_tokens` を増やすか、[effort](https://platform.claude.com/docs/en/build-with-claude/effort) を下げます。

プロンプトを引き継ぐ際に確認するほかの挙動は、[挙動の違い](https://platform.claude.com/docs/en/models/fable-5-2/whats-new-fable-5-2#behavior-differences)を参照してください。

### 移行チェックリスト

- モデル名を `claude-fable-5-1` から `claude-fable-5-2` に変更します。
- 本番のトラフィックを移す前に[レート制限](https://platform.claude.com/docs/en/api/rate-limits#rate-limits)を確認します。Claude Fable 5.2 の制限は、Claude Fable 5.1 と Claude Fable 5 が共有するものとは別に適用されます。
- Amazon Bedrock 以外で `computer_20251124` を使うと、Claude Fable 5.2 はそのツールに対して 400 エラーを返します。`computer_toolset_20260801` を宣言し、エージェントのループをツールセットに対応させます。
- Claude Fable 5.2 を実行側にしてアドバイザーツールを使う場合は、アドバイザーの `model` を `claude-fable-5-2` または `claude-mythos-5-2` に設定します。
- コードで `messages` 配列を組み立てる場合は、ベータヘッダー `thinking-binding-controls-2026-08-01` と `prefix_mismatch_behavior: "drop_block"` を付けてセッションを実行します。`input_transformations` を記録し、`prefix_binding_mismatch` の原因をすべて修正します。
- 本番で使う `prefix_mismatch_behavior` を選びます。既定値は `"error"` です。[ブロックを取り除くと出力トークンが増える場合がある](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/fix-bound-to-a-different-conversation#drop-block-cost)ため、`"drop_block"` は原因を修正する間の一時的な設定とします。400 エラーや `input_transformations` の記録を監視します。
- 空のものも含めて `thinking` ブロックを毎ターンそのまま送り返します。ルーターやフォールバックで Claude Fable 5.2 から Claude Fable 5.1 に会話を移せる場合、Claude Fable 5.1 は Claude Fable 5.2 のブロックなしで動作します。
- 保存した会話を別のアカウントで再現する場合は、生成元のアカウントか、それにリンクしたアカウントで再現します。ほかのアカウントで生成された Claude Fable 5.2 の推論ブロックは API が取り除きます。[アカウントとクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#account-bound-thinking)を参照してください。
- 自分の評価データで [effort の段階を変えた比較](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-fable-5-2)を再実行し、費用と応答時間の基準を測り直します。
- 移行するシステムプロンプト、スキル、その他の指示は、[旧モデル向けのプロンプトと実行環境を見直す](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#review-instructions-written-for-earlier-models)と照らして確認します。

## Claude Mythos 5.1 から Claude Mythos 5.2 への移行

[Claude Mythos 5.2](https://platform.claude.com/docs/en/models/mythos-5-2/overview) は Claude Fable 5.2 に対応するモデルで、[Cyber Verification Program](https://support.claude.com/en/articles/14604842) など Anthropic の認証プログラムで確認された組織向けです。モデル ID を切り替える前に、組織が Claude Mythos 5.2 を利用できることを確認してください。

Claude Mythos 5.2 では[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)に失敗したリクエストは 400 エラーになります。Amazon Bedrock では Claude Mythos 5.1 からの移行で互換性に影響します。リクエスト間で `system`、`tools`、過去のメッセージを変更するコードでは、[過去のターンを編集すると推論ブロックが無効になる](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-edited-history)を参照し、`claude-mythos-5-2` に対してテストを実行します。

Claude API と Claude Models on Google Cloud (Google managed) では、Claude Mythos 5.2 が Claude Mythos 5.1 の推論ブロックを読み取るため、会話を `claude-mythos-5-1` から `claude-mythos-5-2` に移しても以前の推論が保持されます。Claude Mythos 5.1 に戻す場合、同モデルは Claude Mythos 5.2 のブロックを読み取れません。API がブロックを取り除き、リクエストは成功します。[モデルを切り替えて元に戻す](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#switching-models)を参照してください。

ベータ版の[アドバイザーツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)で Claude Mythos 5.2 を実行側にすると、アドバイザーに使えるのは Claude Mythos 5.2 または Claude Fable 5.2 だけです。Claude Mythos 5.1 や Claude Fable 5.1 を指定すると 400 エラーになります。[Claude Fable 5.2 を実行側に使う場合のアドバイザー要件](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-advisor-pairs)を参照してください。

Claude Mythos 5.2 は `computer_toolset_20260801` ツールセットでコンピューター操作に対応します。`tools` で `computer_20251124` を指定すると、従来のツールが動作する Amazon Bedrock を除くすべてのプラットフォームで 400 エラーになります。[`computer_20251124` からツールセットに移す](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-computer-use)を参照してください。

Claude Mythos 5.2 の料金は、100 万トークンあたり入力 8 米ドル（USD）、出力 40 米ドルです。Claude Mythos 5.1 では入力 10 米ドル、出力 50 米ドルでした。プロンプトキャッシュの読み取りは 100 万トークンあたり 0.25 米ドルから 0.20 米ドルになりました。

### モデル名を更新する

```python
model = "claude-mythos-5-1"  # Before
model = "claude-mythos-5-2"  # After
```

### 移行チェックリスト

- モデル名を `claude-mythos-5-1` から `claude-mythos-5-2` に変更します。
- Amazon Bedrock 以外で `computer_20251124` を使うと、Claude Mythos 5.2 はそのツールに対して 400 エラーを返します。`computer_toolset_20260801` を宣言し、エージェントのループをツールセットに対応させます。
- Claude Mythos 5.2 を実行側にしてアドバイザーツールを使う場合は、アドバイザーの `model` を `claude-mythos-5-2` または `claude-fable-5-2` に設定します。
- 空のものも含めて `thinking` ブロックを毎ターンそのまま送り返します。
- 保存した会話を別のアカウントで再現する場合は、生成元のアカウントか、それにリンクしたアカウントで再現します。ほかのアカウントで生成された Claude Mythos 5.2 の推論ブロックは API が取り除きます。[アカウントとクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#account-bound-thinking)を参照してください。
- コードで `messages` 配列を組み立てる場合は、[過去のターンを編集すると推論ブロックが無効になる](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-edited-history)のテストを `claude-mythos-5-2` で実行し、`prefix_binding_mismatch` の原因をすべて修正します。会話履歴は追記だけを行います（[変更と見なされる操作](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#what-counts-as-an-edit)を参照）。追記だけの履歴ではプロンプトキャッシュも再利用できます。
- `stop_reason: "refusal"` を処理し、応答の内容より先に `stop_details.category` を読みます。[拒否とフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)を参照してください。
- effort の段階を変えた比較を再実行し、費用と応答時間の基準を測り直します。
- 移行するシステムプロンプト、スキル、その他の指示は、[旧モデル向けのプロンプトと実行環境を見直す](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#review-instructions-written-for-earlier-models)と照らして確認します。

## Claude Opus 5.5 から Claude Fable 5.2 への移行

Claude Fable 5.2 は [Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview) と同じ Messages API とツール利用の方式を使います。両モデルで適応型推論が常に有効で、ツール選択を強制すると 400 エラーになるため、これらに対応済みのリクエストは引き継げます。Claude Fable 5.2 にトラフィックやフォールバック先を切り替える場合は、次の違いを確認します。

### モデル名を更新する

```python
model = "claude-opus-5-5"  # Before
model = "claude-fable-5-2"  # After
```

### 変更点

1. **データ保持が必要**。Claude Fable 5.2 ではデータを 30 日間保持します。データ保持なし（ZDR）の契約で使うには Anthropic の明示的な承認が必要です。組織またはワークスペースで ZDR により Claude Opus 5.5 を使っている場合は、切り替え前にワークスペースで 30 日間の保持を設定するか、Anthropic の担当チームへ問い合わせてください。この条件を満たさない場合、Claude API の Claude Fable 5.2 宛てのリクエストはすべて 400 の `invalid_request_error` になります。[モデル別のデータ保持要件](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements)を参照してください。
2. **先頭部分の照合に失敗すると 400 エラーになる**。Claude Fable 5.2 では各リクエストで[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)を行います。会話の途中で `system`、`tools`、過去のメッセージを変更したあとに推論ブロックを送り返すと照合に失敗し、400 エラーになります。切り替え前にコードをテストする方法は[照合に失敗するリクエストを探す](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-preserved-thinking)を参照してください。
3. **Claude Opus 5.5 は Claude Fable 5.2 の推論ブロックを読み取れない**。Claude Fable 5.2 から Claude Opus 5.5 に会話を移すと、テキストとツール呼び出しは保持されます。API はモデルに渡す前に Claude Fable 5.2 の推論ブロックを取り除くので、切り替え後のターンはその推論なしで実行されます。リクエストは成功し、取り除いたブロックは課金されません。切り替え後の最初のターンでは費用と応答時間の増加を見込んでください。逆方向では、Claude API と Claude Models on Google Cloud (Google managed) において Claude Fable 5.2 が Claude Opus 5.5 の推論ブロックを読み取れるため、`claude-opus-5-5` から `claude-fable-5-2` に会話を移しても以前の推論を保持します。
4. **安全性分類器とフォールバック**。Claude Fable 5.2 の安全性分類器は、Claude Fable 5.1 と同じ `stop_details` の分類を扱います。Claude Opus 5.5 で見た分類に加えて、[拒否理由の分類表](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#refusal-response)のすべての分類を処理します。拒否されたリクエストを別のモデルで再試行する場合は、Anthropic が分類ごとに推奨するモデルを使う `fallbacks: "default"` を設定するか、独自の再試行処理を実装します。このパラメーターは Claude API と Claude Models on Google Cloud (Anthropic managed) のベータ版で、`server-side-fallback-2026-07-01` ベータヘッダーが必要です。Claude Fable 5.2 のフォールバック先として指定できるのは Claude Opus 4.8（`claude-opus-4-8`）と Claude Opus 5（`claude-opus-5`）です。`"reasoning_extraction"` で拒否されたリクエストはサーバー側で再試行せず、拒否の応答を返します。フォールバック先のモデルには Claude Fable 5.2 の推論ブロックを渡しません。[拒否とフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)を参照してください。
5. **料金**。Claude Fable 5.2 は 100 万トークンあたり入力 8 米ドル（USD）、出力 40 米ドルです。Claude Opus 5.5 は入力 4 米ドル、出力 20 米ドルです。プロンプトキャッシュの読み取りは両モデルとも 100 万トークンあたり 0.20 米ドルです。[料金](https://platform.claude.com/docs/en/about-claude/pricing)を参照してください。
6. **高速モード**。Claude Fable 5.2 は Claude Opus 5.5 と同じく、Claude API の Messages API リクエストで[高速モード](https://platform.claude.com/docs/en/build-with-claude/fast-mode)（`speed: "fast"`）に対応します。高速モードの料金は Claude Fable 5.2 が 100 万トークンあたり入力 16 米ドル（USD）、出力 80 米ドルです。Claude Opus 5.5 の高速モードは入力 8 米ドル、出力 40 米ドルです。[高速モードの料金](https://platform.claude.com/docs/en/about-claude/pricing#fast-mode-pricing)を参照してください。
   [Claude Models on Google Cloud (Anthropic managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/anthropic-managed) でも、同じ `speed: "fast"` 設定で Claude Fable 5.2 の高速モードを使えます。
   [Claude Models on Google Cloud (Google managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed) でも、同じ `speed: "fast"` 設定で Claude Fable 5.2 の高速モードを使えます。この環境の料金は Google Cloud が決めます。[クラウドプラットフォームの料金](https://platform.claude.com/docs/en/about-claude/pricing#cloud-platform-pricing)を参照してください。
   [Claude in Microsoft Foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry) でも、Anthropic がホストするデプロイで Claude Fable 5.2 の高速モードを使えます。高速モードに固有のモデル ID があるので、`claude-fable-5-2-fast` のデプロイ先にリクエストを送り、`speed` は省略します。
   Claude Mythos 5.2 も Claude API の Messages API リクエストで高速モードを使えます。料金は Claude Fable 5.2 の高速モードと同じです。[高速モードの提供状況](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)で Claude Mythos 5.2 が対応するすべてのプラットフォームを確認できます。
   Claude Managed Agents では `speed: "fast"` を取り除きます。[高速モードの提供状況](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)に移行先モデルが掲載されていないプラットフォームやホスティング方式でも同様に取り除きます。
7. **CMEK を使う組織での構造化出力**。[顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では、Claude Opus 5.5 が[構造化出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)に対応し、Claude Fable 5.2 は非対応です。移行するリクエストから `strict: true` と `output_config.format` を取り除き、コードで出力を検証します。
8. **effort の既定値は `high`**。Claude Opus 5.5 の既定値は `medium` なので、`effort` を省略したリクエストは Claude Fable 5.2 で 1 段階高く実行されます。リクエストは成功し、違いは費用、応答時間、結果に表れます。`effort` を明示し、自分の評価データで [effort の段階を変えた比較](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-fable-5-2)を再実行します。
9. **Claude Fable 5.2 の実行側には Claude Fable 5.2 か Claude Mythos 5.2 のアドバイザーが必要**。ベータ版の[アドバイザーツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)では、Claude Opus 5.5 を実行側にすると Claude Opus 5.5 と Claude Fable 5.1 など複数のアドバイザーを使えます。Claude Fable 5.2 を実行側にすると、Claude Fable 5.2 または Claude Mythos 5.2 だけを受理し、ほかのアドバイザーを指定すると 400 エラーになります。実行側のモデルを変更する際は、アドバイザーの `model` を `claude-fable-5-2` か `claude-mythos-5-2` に設定します。[Claude Fable 5.2 を実行側に使う場合のアドバイザー要件](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-advisor-pairs)を参照してください。

### 移行チェックリスト

- 組織に ZDR 契約がある場合は、最初にワークスペースの 30 日間保持を有効にするか、利用条件を Anthropic の担当チームに確認します。
- モデル ID を `claude-opus-5-5` から `claude-fable-5-2` に変更します。
- 本番のトラフィックを移す前に[レート制限](https://platform.claude.com/docs/en/api/rate-limits#rate-limits)を確認します。Claude Fable 5.2 の制限は Claude Opus 5.5 とは別に適用され、各階層でトークン上限が低くなります。
- コードで `messages` 配列を組み立てる場合は、[先頭部分の照合に失敗すると 400 エラーになる](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-preserved-thinking)に記載されたテストを実行します。
- すべての `stop_details.category` を処理します。`fallbacks` の一覧を明示する場合は、Claude Fable 5.2 が許可する移行先だけを指定します。
- ルーターやフォールバックが Claude Fable 5.2 から Claude Opus 5.5 に会話を移す場合、切り替え後のターンは Claude Fable 5.2 の推論ブロックなしで実行されます。
- 保存した会話を別のアカウントで再現する場合は、生成元のアカウントか、それにリンクしたアカウントで再現します。ほかのアカウントで生成された Claude Fable 5.2 の推論ブロックは API が取り除きます。[アカウントとクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#account-bound-thinking)を参照してください。
- Messages API リクエストで高速モードを使う場合は、[高速モードの提供状況](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)に移行先モデルが掲載されているプラットフォームやホスティング方式でのみ `speed: "fast"` を維持し、[高速モードの料金](https://platform.claude.com/docs/en/about-claude/pricing#fast-mode-pricing)をもとに費用の基準を見直します。その他のプラットフォームやホスティング方式と Claude Managed Agents では `speed: "fast"` を削除します。ベータヘッダー `fast-mode-2026-02-01` は不要です。Claude API では引き続きヘッダーを付けても動作します。Claude in Microsoft Foundry は例外で、`speed: "fast"` を省き、`claude-fable-5-2-fast` のデプロイ先に送ります。
- Claude Fable 5.2 を実行側にしてアドバイザーツールを使う場合は、アドバイザーの `model` を `claude-fable-5-2` または `claude-mythos-5-2` に設定します。
- [顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では、`strict: true` と `output_config.format` を取り除き、コードで出力を検証します。
- `effort` を明示します。Claude Fable 5.2 の既定値は `high`、Claude Opus 5.5 の既定値は `medium` のため、省略すると 1 段階高く実行されます。自分の評価データで [effort の段階を変えた比較](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-fable-5-2)を再実行し、費用と応答時間の基準を測り直します。
- 移行するシステムプロンプト、スキル、その他の指示は、[旧モデル向けのプロンプトと実行環境を見直す](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#review-instructions-written-for-earlier-models)と照らして確認します。

## Claude Fable 5 から Claude Fable 5.2 への移行

API の仕様、コンテキストウィンドウと出力の上限、トークナイザー、常に有効な適応型推論、拒否の処理は Claude Fable 5 と共通です。次の変更の一部は Claude Mythos 5 から Claude Mythos 5.2 に移行する場合にも適用されます。[Claude Mythos 5 から Claude Mythos 5.2 への移行](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#migrating-from-claude-mythos-5-to-claude-mythos-5-2)を参照してください。

### モデル名を更新する

```python
model = "claude-fable-5"  # Before
model = "claude-fable-5-2"  # After
```

### 互換性を損なう変更

1. **ツール選択を強制すると 400 エラーになる**。Claude Fable 5 は `tool_choice` の `auto`、`none`、`any`、`tool` を受理します。`claude-fable-5-2` では `{type: "any"}` と `{type: "tool", name: "..."}` は 400 の `invalid_request_error` になり、[トークン数を数えるエンドポイント](https://platform.claude.com/docs/en/build-with-claude/token-counting)でも同じです。エラーメッセージは[強制ツール利用に対応していない](https://platform.claude.com/docs/en/api/errors#forced-tool-use-not-supported)を参照してください。
   強制設定を使わずにツールを呼ばせるには、`tool_choice` を `auto` のままにして指示でツール名を指定します。ツールに `strict: true` を設定すると、呼び出しがスキーマに従います。[厳密なツール利用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use)を参照してください。スキーマに沿った JSON を得るためだけにツールを強制していた場合は、[JSON 出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#usage)を使います。[顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では、Claude Fable 5.2 と Claude Mythos 5.2 はどちらも[構造化出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)に非対応で、厳密なツール利用と JSON 出力の両方が対象です。その場合は `auto` と指示を使い、`strict` を省略してコードでツール入力を検証します。
   アプリケーションが現在のターンで特定のツール呼び出しを必要とする場合は、直近の `user` ターンの後に[会話途中のシステムメッセージ](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)を追加します。そこでツール名を示し、そのターンでは呼び出しが必須で、応答の冒頭で呼び出すよう指示します。以前のターンが保持されるため、対応するキャッシュヒットと推論ブロックは有効です。対応プラットフォームは[会話途中のシステムメッセージとツールの変更](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)を参照してください。ツールを呼び出してはいけないターンでは、`tool_choice: {"type": "none"}` を使えます。[ツール利用の強制](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools#forcing-tool-use)を参照してください。
2. **過去のターンを編集すると推論ブロックが無効になる**。Claude Fable 5.2 の `thinking` ブロックは、それより前の `system` プロンプト、`tools`、メッセージに対してのみ有効です。いずれかが変更されると、ブロックを送り返すリクエストは[先頭部分の照合](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#prefix-check)に失敗して 400 エラーになります。同じリクエスト本体を再送しても解消しません。
   Claude Code、claude.ai、[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview)、[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) が会話履歴を管理している場合は、変更が不要です。コードで `messages` 配列を組み立てる場合は、履歴を追記だけにします。セッション中は `system` と `tools` を固定します。指示やツールは[会話途中のシステムメッセージ](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)で変更し、コンテキストはサーバー側の[圧縮](https://platform.claude.com/docs/en/build-with-claude/compaction)または[コンテキスト編集](https://platform.claude.com/docs/en/build-with-claude/context-editing)で短くします。対応プラットフォームは[会話途中のシステムメッセージとツールの変更](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)、変更ごとの送り方は[先頭部分の照合を保ったままツールや指示を変更する](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/change-tools-or-instructions)を参照してください。
   本番のトラフィックを切り替える前に、[先頭部分の照合に失敗する処理を検出するテスト](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/fix-bound-to-a-different-conversation#how-to-tell-whether-your-integration-is-impacted)を `claude-fable-5-2` で実行します。本番環境で不一致が必ずコードの不具合を意味するなら、`prefix_mismatch_behavior` は既定の `"error"` のままにします。原因を修正する間、影響を受けたブロックを取り除いて処理を続けるには、ベータヘッダー `thinking-binding-controls-2026-08-01` とともに `"drop_block"` を指定します。[ブロックを取り除くと出力トークンが増える場合がある](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/fix-bound-to-a-different-conversation#drop-block-cost)ため、一時的な対応として使います。
3. **Claude Fable 5 は Claude Fable 5.2 の推論ブロックを読み取れない**。Claude API と Claude Models on Google Cloud (Google managed) では Claude Fable 5.2 が Claude Fable 5 のブロックを読み取れるため、`claude-fable-5` から `claude-fable-5-2` に会話を移しても以前の推論が保持されます。Claude Fable 5 に戻す場合、そのモデルは Claude Fable 5.2 のブロックを読み取れません。
   ルーターによる切り替え、クライアント側での再試行、[分類器による拒否時のフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)によって、Claude Fable 5.2 から Claude Fable 5 など別のモデルに会話が移ると、API は移行先で読み取れないブロックを取り除きます。リクエストは成功し、取り除いた入力トークンは課金されません。ベータヘッダー `thinking-binding-controls-2026-08-01` を送ると、取り除いたブロックごとに `input_transformations` に `reason: "model_binding_mismatch"` が記録されます。[モデルを切り替えて元に戻す](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#switching-models)を参照してください。
4. **コンピューター操作を `computer_20251124` からツールセットに移す**。Claude Fable 5.2 では、`tools` に種類が `computer_20251124` の項目を入れると、Amazon Bedrock を除くすべてのプラットフォームで 400 エラーになります。Claude Fable 5 はベータヘッダー付きで受理します。`computer_toolset_20260801` ツールセットを宣言します（[`computer_20251124` からツールセットに移す](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-computer-use)を参照）。
5. **Claude Fable 5.2 の実行側には Claude Fable 5.2 か Claude Mythos 5.2 のアドバイザーが必要**。ベータ版の[アドバイザーツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)では、Claude Fable 5.2 が実行側の場合、Claude Fable 5.2 または Claude Mythos 5.2 だけをアドバイザーとして受理します。Claude Fable 5 を実行側にすると使える Claude Fable 5 や Claude Opus 5.5 などを指定すると、400 エラーになります。実行側のモデルを切り替える場合は、アドバイザーの `model` を `claude-fable-5-2` か `claude-mythos-5-2` に設定します。[Claude Fable 5.2 を実行側に使う場合のアドバイザー要件](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-advisor-pairs)を参照してください。

### その他の変更

- **料金**。100 万トークンあたり入力 8 米ドル（USD）、出力 40 米ドルです。Claude Fable 5 は入力 10 米ドル、出力 50 米ドルです。プロンプトキャッシュの読み取りは 100 万トークンあたり 1 米ドルから 0.20 米ドルになりました。[料金](https://platform.claude.com/docs/en/about-claude/pricing)を参照してください。
- **Priority Tier**。Claude Fable 5.2 は [Priority Tier](https://platform.claude.com/docs/en/api/service-tiers#supported-models) に対応していません。Claude Fable 5 は対応しています。組織が Priority Tier を契約している場合は、別途キャパシティを計画します。
- **メッセージ単位の effort（ベータ版）**。会話の途中でプロンプトキャッシュのヒットを保ちながら effort を変更するには、リクエスト間で `output_config.effort` を変える操作を、[メッセージ単位の effort](https://platform.claude.com/docs/en/build-with-claude/effort-per-message) を指定する `role: "system"` メッセージの送信に置き換えます。対応プラットフォームはメッセージ単位の effort のページを参照してください。

### 移行チェックリスト

- モデル名を `claude-fable-5` から `claude-fable-5-2` に変更します。
- 本番のトラフィックを移す前に[レート制限](https://platform.claude.com/docs/en/api/rate-limits#rate-limits)を確認します。Claude Fable 5.2 の制限は、Claude Fable 5.1 と Claude Fable 5 が共有するものとは別に適用されます。
- 強制の `tool_choice`（`{type: "any"}` または `{type: "tool", ...}`）は、`{type: "auto"}` と明示的な指示、`strict: true` を使うツールの組み合わせか、JSON 出力に置き換えます。指示は `user` ターンに書きます。アプリケーションが呼び出しを必須とする場合は、[会話途中のシステムメッセージ](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)に掲載されたプラットフォームで会話途中の `role: "system"` メッセージに書きます。[顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では、Claude Fable 5.2 で厳密なツール利用と JSON 出力を使えません。この場合は `{type: "auto"}` と指示を使い、コードでツール入力を検証します。
- コードで `messages` 配列を組み立てる場合は、ベータヘッダー `thinking-binding-controls-2026-08-01` と `prefix_mismatch_behavior: "drop_block"` を付けて `claude-fable-5-2` でセッションを実行します。`input_transformations` を記録し、`prefix_binding_mismatch` の原因をすべて修正します。
- 履歴を追記だけにします。セッションの開始時に `system` と `tools` を固定し、途中の変更には `role: "system"` メッセージを使い、コンテキストはサーバー側で短くします。対応プラットフォームは[会話途中のシステムメッセージとツールの変更](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)を参照してください。
- 本番で使う `prefix_mismatch_behavior` を選びます。既定値は `"error"` です。[ブロックを取り除くと出力トークンが増える場合がある](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/fix-bound-to-a-different-conversation#drop-block-cost)ため、`"drop_block"` は原因を修正する間の一時的な設定とします。400 エラーや `input_transformations` の記録を監視します。
- 空のものも含めて `thinking` ブロックを毎ターンそのまま送り返します。ルーターやフォールバックで Claude Fable 5.2 から Claude Fable 5 に会話を移せる場合、Claude Fable 5 は Claude Fable 5.2 のブロックなしで動作します。
- 保存した会話を別のアカウントで再現する場合は、生成元のアカウントか、それにリンクしたアカウントで再現します。ほかのアカウントで生成された Claude Fable 5.2 の推論ブロックは API が取り除きます。[アカウントとクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#account-bound-thinking)を参照してください。
- Amazon Bedrock 以外で `computer_20251124` を使うと、Claude Fable 5.2 はそのツールに対して 400 エラーを返します。`computer_toolset_20260801` を宣言し、エージェントのループをツールセットに対応させます。
- Claude Fable 5.2 を実行側にしてアドバイザーツールを使う場合は、アドバイザーの `model` を `claude-fable-5-2` または `claude-mythos-5-2` に設定します。
- リクエスト間で effort を変更する場合は、対応プラットフォームで、ベータ版のメッセージ単位の effort を使う `role: "system"` メッセージに変更を移します。
- 組織が Priority Tier を契約している場合は、別途キャパシティを計画します。
- `stop_reason: "refusal"` を処理し、`stop_details.category` を読みます。Claude API と Claude Models on Google Cloud (Anthropic managed) でベータ版の `fallbacks: "default"` も検討します。
- 自分の評価データで [effort の段階を変えた比較](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-fable-5-2)を再実行し、費用と応答時間の基準を測り直します。
- 移行するシステムプロンプト、スキル、その他の指示は、[旧モデル向けのプロンプトと実行環境を見直す](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#review-instructions-written-for-earlier-models)と照らして確認します。

## Claude Mythos 5 から Claude Mythos 5.2 への移行

[Claude Mythos 5.2](https://platform.claude.com/docs/en/models/mythos-5-2/overview) は Claude Fable 5.2 に対応するモデルで、[Cyber Verification Program](https://support.claude.com/en/articles/14604842) など Anthropic の認証プログラムで確認された組織向けです。モデル ID を切り替える前に、組織が Claude Mythos 5.2 を利用できることを確認してください。

[Claude Fable 5 から Claude Fable 5.2 への移行](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#migrating-from-claude-fable-5-to-claude-fable-5-2)にある次の 4 つの変更がそのまま適用されます。

- [ツール選択を強制すると 400 エラーになる](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-forced-tool-choice)。
- [過去のターンを編集すると推論ブロックが無効になる](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-edited-history)。
- [コンピューター操作を `computer_20251124` からツールセットに移す](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-computer-use)。
- Claude Fable 5.2 または Claude Mythos 5.2 を実行側にする場合は、[そのどちらかをアドバイザーに指定する必要がある](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-advisor-pairs)。

Claude API と Claude Models on Google Cloud (Google managed) では、Claude Mythos 5.2 が Claude Mythos 5 の推論ブロックを読み取るため、会話を `claude-mythos-5` から `claude-mythos-5-2` に移しても以前の推論が保持されます。Claude Mythos 5 に戻す場合、同モデルは Claude Mythos 5.2 のブロックを読み取れません。API がブロックを取り除き、リクエストは成功します。[モデルを切り替えて元に戻す](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#switching-models)を参照してください。

Claude Mythos 5.2 の料金は、100 万トークンあたり入力 8 米ドル（USD）、出力 40 米ドルです。Claude Mythos 5 は入力 10 米ドル、出力 50 米ドルです。プロンプトキャッシュの読み取りは 100 万トークンあたり 1 米ドルから 0.20 米ドルになりました。

### モデル名を更新する

```python
model = "claude-mythos-5"  # Before
model = "claude-mythos-5-2"  # After
```

### 移行チェックリスト

- モデル名を `claude-mythos-5` から `claude-mythos-5-2` に変更します。
- 強制の `tool_choice`（`any` または `tool`）は、`auto` と明示的な指示、`strict: true` を使うツールの組み合わせか、JSON 出力に置き換えます。[顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では、Claude Mythos 5.2 で厳密なツール利用と JSON 出力を使えません。この場合は `auto` と指示を使い、コードでツール入力を検証します。
- Amazon Bedrock 以外で `computer_20251124` を使うと、Claude Mythos 5.2 はそのツールに対して 400 エラーを返します。`computer_toolset_20260801` を宣言し、エージェントのループをツールセットに対応させます。
- Claude Mythos 5.2 を実行側にしてアドバイザーツールを使う場合は、アドバイザーの `model` を `claude-mythos-5-2` または `claude-fable-5-2` に設定します。
- 空のものも含めて `thinking` ブロックを毎ターンそのまま送り返します。
- 保存した会話を別のアカウントで再現する場合は、生成元のアカウントか、それにリンクしたアカウントで再現します。ほかのアカウントで生成された Claude Mythos 5.2 の推論ブロックは API が取り除きます。[アカウントとクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#account-bound-thinking)を参照してください。
- コードで `messages` 配列を組み立てる場合は、[過去のターンを編集すると推論ブロックが無効になる](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-edited-history)のテストを `claude-mythos-5-2` で実行し、`prefix_binding_mismatch` の原因をすべて修正します。会話履歴は追記だけを行います（[変更と見なされる操作](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking/prefix-checks#what-counts-as-an-edit)を参照）。追記だけの履歴ではプロンプトキャッシュも再利用できます。
- `stop_reason: "refusal"` を処理し、応答の内容より先に `stop_details.category` を読みます。[拒否とフォールバック](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)を参照してください。
- effort の段階を変えた比較を再実行し、費用と応答時間の基準を測り直します。
- 移行するシステムプロンプト、スキル、その他の指示は、[旧モデル向けのプロンプトと実行環境を見直す](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#review-instructions-written-for-earlier-models)と照らして確認します。

## Claude Opus 5 から Claude Fable 5.2 への移行

Claude Fable 5.2 は、[Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) と[ツール利用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)で [Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview) と同じ方式を使います。100 万トークンのコンテキストウィンドウ、最大 128,000 出力トークン、プロンプトキャッシュの下限 512 トークン、[会話途中のシステムメッセージ](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)は引き継げます。事前入力とサンプリングパラメーターの制約も共通です。トラフィックやフォールバック先を Claude Fable 5.2 に切り替えるときは、次の違いを確認します。

### モデル名を更新する

```python
model = "claude-opus-5"  # Before
model = "claude-fable-5-2"  # After
```

### 変更点

1. **推論は常に有効**。Claude Opus 5 は [effort](https://platform.claude.com/docs/en/build-with-claude/effort) が `high` 以下の場合に `thinking: {type: "disabled"}` を受理します。Claude Fable 5.2 では[適応型推論](https://platform.claude.com/docs/en/build-with-claude/thinking)が常に有効で、`thinking: {type: "disabled"}` は effort にかかわらず 400 エラーになります。このフィールドを削除し、effort を下げてトークン消費量を調整します。推論を無効にしていた処理では、推論と応答テキストを含む `max_tokens` を見直します。`content[0].text` のように位置で内容を読むコードでは、`thinking` ブロックが先に来るため、`type` でブロックを選びます。
2. **ツール選択を強制すると 400 エラーになる**。Claude Opus 5 は `tool_choice` の `any` と `tool` を受理します。Claude Fable 5.2 は両方を拒否します。指定の変更方法は[ツール選択を強制すると 400 エラーになる](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-forced-tool-choice)を参照してください。
3. **過去のターンを編集すると推論ブロックが無効になる**。リクエスト間に過去のメッセージを編集したり、`system` や `tools` を組み立て直したり、クライアント側で圧縮したりすると、変更箇所より後ろの推論ブロックが無効になります。そのブロックを Claude Fable 5.2 に送り返すと 400 エラーになります。`prefix_mismatch_behavior` を `"drop_block"` にしている場合は API がブロックを取り除きます。コードの修正とテスト方法は[過去のターンを編集すると推論ブロックが無効になる](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-edited-history)を参照してください。
4. **Claude Opus 5 は Claude Fable 5.2 の推論ブロックを読み取れない**。Claude API と Claude Models on Google Cloud (Google managed) では Claude Fable 5.2 が Claude Opus 5 のブロックを読み取るため、会話を `claude-opus-5` から `claude-fable-5-2` に移しても以前の推論が保持されます。
   Claude Fable 5.2 から Claude Opus 5 に会話を移す場合、Claude Opus 5 は切り替え後のターンを Claude Fable 5.2 の推論なしで実行します。API がモデルに渡す前にブロックを取り除き、リクエストは成功します。取り除いたブロックは課金されません。[モデルを切り替えて元に戻す](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#switching-models)を参照してください。
5. **ツール呼び出し間のテキストは推論ブロックで返る**。Claude Opus 5 では、呼び出し間にモデルが書いたテキストが `text` ブロックで返ります。Claude Fable 5.2 は進捗報告を `thinking` ブロックで返し、各ツール呼び出しの前に最大 1 つが現れます。この報告を画面に出す場合は、`thinking.display` にベータ版の `"updates"` を指定すると推論本文を非表示にして報告のテキストを受け取れます。`"summarized"` では両方を受け取れます。そのうえで、`tool_use` ブロック間の空でない `thinking` ブロックを表示します。[ツール呼び出し間の進捗報告](https://platform.claude.com/docs/en/build-with-claude/thinking#progress-updates)を参照してください。
6. **コンピューター操作を `computer_20251124` からツールセットに移す**。Claude Opus 5 は従来の `computer_20251124` ツールをベータヘッダー付きで受理します。Claude Fable 5.2 では Amazon Bedrock を除くすべてのプラットフォームで 400 エラーになります。[`computer_20251124` からツールセットに移す](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-computer-use)を参照してください。
7. **安全性分類器とフォールバック**。Claude Fable 5.2 の安全性分類器は Claude Opus 5 より広い範囲の `stop_details` の分類を扱います。`"bio"` などの `stop_details.category` が追加されることを見込み、[拒否理由の分類表](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback#refusal-response)のすべての分類を処理します。拒否されたリクエストを別のモデルで再試行する場合は、`fallbacks: "default"` を指定するか、独自の再試行処理を実装します。このパラメーターは Claude API と Claude Models on Google Cloud (Anthropic managed) のベータ版で、`server-side-fallback-2026-07-01` ベータヘッダーが必要です。許可されているフォールバック先は[拒否、フォールバック、課金](https://platform.claude.com/docs/en/models/fable-5-2/whats-new-fable-5-2#refusals-fallback-and-billing)を参照してください。
8. **料金**。Claude Fable 5.2 は 100 万トークンあたり入力 8 米ドル（USD）、出力 40 米ドルです。Claude Opus 5 は入力 5 米ドル、出力 25 米ドルです。プロンプトキャッシュの読み取りは 100 万トークンあたり 0.50 米ドルから 0.20 米ドルになりました。[料金](https://platform.claude.com/docs/en/about-claude/pricing)を参照してください。
9. **データ保持が必要**。Claude Fable 5.2 ではデータを 30 日間保持します。データ保持なし（ZDR）の契約で使うには Anthropic の明示的な承認が必要です。Claude Opus 5 は ZDR で利用できます。Claude API では、30 日間保持を設定していない組織またはワークスペースからのリクエストは 400 の `invalid_request_error` になります。[モデル別のデータ保持要件](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements)を参照してください。
10. **高速モード**。Claude Opus 5 は研究プレビューの[高速モード](https://platform.claude.com/docs/en/build-with-claude/fast-mode)（`speed: "fast"`）を `fast-mode-2026-02-01` ベータヘッダー付きで使えます。Claude Fable 5.2 では、Claude API の Messages API リクエストでヘッダーを省略して使えます。ヘッダー付きのリクエストも引き続き動作します。高速モードは Claude Fable 5.2 が 100 万トークンあたり入力 16 米ドル（USD）、出力 80 米ドルで、Claude Opus 5 は入力 10 米ドル、出力 50 米ドルです。[高速モードの料金](https://platform.claude.com/docs/en/about-claude/pricing#fast-mode-pricing)を参照してください。
    [Claude Models on Google Cloud (Anthropic managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/anthropic-managed) でも、同じ `speed: "fast"` 設定で Claude Fable 5.2 の高速モードを使えます。
    [Claude Models on Google Cloud (Google managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed) でも、同じ `speed: "fast"` 設定で Claude Fable 5.2 の高速モードを使えます。この環境の料金は Google Cloud が決めます。[クラウドプラットフォームの料金](https://platform.claude.com/docs/en/about-claude/pricing#cloud-platform-pricing)を参照してください。
    [Claude in Microsoft Foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry) でも、Anthropic がホストするデプロイで Claude Fable 5.2 の高速モードを使えます。高速モードに固有のモデル ID があるので、`claude-fable-5-2-fast` のデプロイ先にリクエストを送り、`speed` は省略します。
    Claude Mythos 5.2 も Claude API の Messages API リクエストでヘッダーを省略して高速モードを使えます。料金は Claude Fable 5.2 の高速モードと同じです。[高速モードの提供状況](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)で Claude Mythos 5.2 が対応するすべてのプラットフォームを確認できます。
    Claude Managed Agents では `speed: "fast"` を取り除きます。[高速モードの提供状況](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)に移行先モデルが掲載されていない場合も取り除きます。
11. **CMEK を使う組織での構造化出力**。[顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では、Claude Opus 5 が[構造化出力](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)に対応し、Claude Fable 5.2 は非対応です。移行するリクエストから `strict: true` と `output_config.format` を取り除き、コードで出力を検証します。
12. **Claude Fable 5.2 の実行側には Claude Fable 5.2 か Claude Mythos 5.2 のアドバイザーが必要**。ベータ版の[アドバイザーツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)では、Claude Opus 5 を実行側にすると Claude Opus 5 と Claude Fable 5.1 など複数のアドバイザーを使えます。Claude Fable 5.2 を実行側にすると、Claude Fable 5.2 または Claude Mythos 5.2 だけを受理し、ほかのアドバイザーを指定すると 400 エラーになります。実行側のモデルを変更する際は、アドバイザーの `model` を `claude-fable-5-2` か `claude-mythos-5-2` に設定します。[Claude Fable 5.2 を実行側に使う場合のアドバイザー要件](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-advisor-pairs)を参照してください。

### 移行チェックリスト

- 組織に ZDR 契約がある場合は、最初にワークスペースの 30 日間保持を有効にするか、利用条件を Anthropic の担当チームに確認します。
- モデル ID を `claude-opus-5` から `claude-fable-5-2` に変更します。
- 本番のトラフィックを移す前に[レート制限](https://platform.claude.com/docs/en/api/rate-limits#rate-limits)を確認します。Claude Fable 5.2 の制限は Claude Opus 5 とは別に適用され、各階層でトークン上限が低くなります。
- `thinking: {type: "disabled"}` の設定を取り除きます。effort を下げてトークン消費量を調整し、`max_tokens` を見直し、`type` で内容ブロックを選びます。
- 空のものも含めて `thinking` ブロックを毎ターンそのまま送り返します。ツール利用を繰り返す場合は、ツールの結果とともに送り返します。[推論ブロックの保持](https://platform.claude.com/docs/en/build-with-claude/thinking#preserving-thinking-blocks)を参照してください。
- 強制の `tool_choice`（`any` または `tool`）は、`auto` と明示的な指示、`strict: true` を使うツールの組み合わせか、JSON 出力に置き換えます。[顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では、Claude Fable 5.2 で厳密なツール利用と JSON 出力を使えません。この場合は `auto` と指示を使い、コードでツール入力を検証します。
- コードで `messages` 配列を組み立てる場合は、[過去のターンを編集すると推論ブロックが無効になる](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#fable-5-2-edited-history)のテストを `claude-fable-5-2` で実行し、`prefix_binding_mismatch` の原因をすべて修正します。履歴は追記だけを行います。
- Amazon Bedrock 以外で `computer_20251124` を使うと、Claude Fable 5.2 はそのツールに対して 400 エラーを返します。`computer_toolset_20260801` を宣言し、エージェントのループをツールセットに対応させます。
- Claude Fable 5.2 を実行側にしてアドバイザーツールを使う場合は、アドバイザーの `model` を `claude-fable-5-2` または `claude-mythos-5-2` に設定します。
- ルーターやフォールバックが Claude Fable 5.2 から Claude Opus 5 に会話を移す場合、切り替え後のターンは Claude Fable 5.2 の推論ブロックなしで実行されます。
- 保存した会話を別のアカウントで再現する場合は、生成元のアカウントか、それにリンクしたアカウントで再現します。ほかのアカウントで生成された Claude Fable 5.2 の推論ブロックは API が取り除きます。[アカウントとクラウドプラットフォーム](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking#account-bound-thinking)を参照してください。
- ツール呼び出し間のテキストを画面に表示する場合は、`thinking.display` にベータ版の `"updates"` または `"summarized"` を指定し、空でない `thinking` ブロックを表示します。
- すべての `stop_details.category` を処理します。`fallbacks` の一覧を明示する場合は、Claude Fable 5.2 が許可する移行先だけを指定します。
- Claude API の Messages API リクエストで高速モードを使う場合は、[高速モードの提供状況](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)に移行先モデルが掲載されている場合に限り `speed: "fast"` を維持します。維持する場合は[高速モードの料金](https://platform.claude.com/docs/en/about-claude/pricing#fast-mode-pricing)をもとに費用の基準を見直します。Claude Managed Agents では `speed: "fast"` を削除します。ベータヘッダー `fast-mode-2026-02-01` は省略でき、付けていてもリクエストは引き続き動作します。
- [顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では、`strict: true` と `output_config.format` を取り除き、コードで出力を検証します。
- 自分の評価データで [effort の段階を変えた比較](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-fable-5-2)を再実行し、費用と応答時間の基準を測り直します。
- 移行するシステムプロンプト、スキル、その他の指示は、[旧モデル向けのプロンプトと実行環境を見直す](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2#review-instructions-written-for-earlier-models)と照らして確認します。

## Claude Opus 4.8 以前から Claude Fable 5.2 への移行

まず、置き換えるモデル ID を `claude-opus-4-8` にして、[Claude Opus 5 から Claude Fable 5.2 への移行](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#migrating-from-claude-opus-5-to-claude-fable-5-2)の手順を実行します。Claude Opus 4.8 は Claude Opus 5 と同じく、次の性質を持つため、その節の手順が Claude Opus 4.8 を使うコードにも当てはまります。

- `thinking: {type: "disabled"}`、強制ツール選択、`computer_20251124` ツール、高速モードを受理する。高速モードは [Claude Opus 4.8 で非推奨](https://platform.claude.com/docs/en/build-with-claude/fast-mode)。
- ツール呼び出し間のテキストを `text` ブロックで返す。
- データ保持なし（ZDR）の契約で使える。
- 100 万トークンあたり入力 5 米ドル（USD）、出力 25 米ドルで、プロンプトキャッシュの読み取りは 0.50 米ドル。

ここでは Claude Opus 5 の節に含まれない違いを説明します。

### 変更点

1. **推論の設定を省略しても推論が有効になる**。Claude Opus 4.8 は明示的に指定しない限り推論が無効です。Claude Fable 5.2 では、`thinking` フィールドを省略しても適応型推論が動作します。応答では `text` より先に `thinking` ブロックが現れることがあるため、`content[0].text` のように位置を固定せず `type` で内容ブロックを選びます。ツール利用を繰り返すときは、空のものも含めた `thinking` ブロックをツールの結果と一緒にそのまま送り返します。推論トークンは出力として課金され、`max_tokens` は推論と応答テキストを合わせた上限です。`max_tokens` を見直し、推論を減らしたい場合は `effort` を下げます。Claude API と Claude Models on Google Cloud (Google managed) では、Claude Fable 5.2 が以前の Claude Opus 4.8 のターンの推論ブロックを読み取れるため、`claude-fable-5-2` に会話を移してもその推論を保持します。
2. **プロンプトキャッシュの下限が下がる**。Claude Fable 5.2 のキャッシュを作成できる最小プロンプト長は 512 トークンです。Claude Opus 4.8 では 1,024 トークンでした。以前は短すぎたプロンプトもコードを変えずにキャッシュを作成できます。[プロンプトキャッシュ](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#cache-limitations)を参照してください。
3. **Priority Tier は非対応**。Claude Opus 4.8 は [Priority Tier](https://platform.claude.com/docs/en/api/service-tiers#supported-models) に対応し、Claude Fable 5.2 は非対応です。組織が Priority Tier を契約している場合は、別途キャパシティを計画します。
4. **アドバイザーツールの助言は暗号化して返る**。ベータ版の[アドバイザーツール](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)で Claude Opus 4.8 を実行側にすると、Claude Opus 4.8 など助言を平文で返すアドバイザーと組み合わせられます。Claude Fable 5.2 が実行側の場合に受理する Claude Fable 5.2 と Claude Mythos 5.2 は、助言を暗号化した `advisor_redacted_result` ブロックで返すため、クライアントはテキストを読めません。コードが助言のテキストを読む場合は、その依存を取り除きます。[結果の種類](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#result-variants)を参照してください。

Claude Opus 4.7 以前を使うコードでは、Claude Opus 5.5 の移行ガイドのチェックリストも一部適用します。[Claude Opus 4.7 以前](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#migration-checklist-from-claude-opus-47)のグループから始め、使っているモデルを明記したグループまで順番に適用します。これらのグループは、サンプリングパラメーターやベータヘッダーの廃止など、Claude Opus 4.8 より前に行われたリクエストの変更を扱います。高速モードの項目は、[高速モードの提供状況](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)に移行先モデルが掲載されている場合に適用します。[顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では、Claude Fable 5.2 で構造化出力を使えないため、`output_config.format` の項目は適用しません。リクエストから `output_format` を取り除き、コードで JSON を検証します。

### 移行チェックリスト

- 置き換えるモデル ID を `claude-opus-4-8` として、[Claude Opus 5 のチェックリスト](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide#migration-checklist-fable-5-2-from-opus-5)を実行します。
- `thinking` フィールドを省略していた処理を見直します。Claude Fable 5.2 では推論が有効になるため、`max_tokens` を見直し、推論を減らしたい処理では `effort` を下げ、`type` で内容ブロックを選びます。
- `thinking` フィールドを読むコードでは、表示用のテキストとしてだけ扱っていることを確認します。読める要約を受け取るには `thinking.display` を `"summarized"` に設定します。
- キャッシュの下限に近いプロンプトを見直します。512 トークン以上のプロンプトはキャッシュを作成できます。
- 組織が Priority Tier を契約している場合は、別途キャパシティを計画します。
- アドバイザーツールを使い、コードで助言のテキストを読んでいる場合は、その依存を取り除きます。助言は暗号化された `advisor_redacted_result` ブロックで届きます。
- 自分の評価データで effort の段階を変えた比較を改めて実行します。Claude Opus 4.8 向けに調整した設定も見直します。
- Claude Opus 4.7 以前の場合は、対象モデル向けの Claude Opus 5.5 移行ガイドのチェックリストも適用します。[高速モードの提供状況](https://platform.claude.com/docs/en/build-with-claude/fast-mode#feature-availability)に移行先モデルがなければ、高速モードの項目を省きます。[顧客管理の暗号鍵](https://platform.claude.com/docs/en/manage-claude/cmek)を使う組織では `output_config.format` の項目も省き、リクエストから `output_format` を取り除きます。
