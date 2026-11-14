# プラグインのサブエージェントのモデルを確かめた記録（2026-11-14）

URL の取り込みの raw の段を Sonnet のエージェントに任せる設計（[wiki-web-raw-agent-2026-11-14.md](../plans/wiki-web-raw-agent-2026-11-14.md)）の前提のうち、公式の文書で確かめられなかったものを、試しのプラグインで確かめた。

## 方法

スクラッチパッドに、次の 3 つのファイルだけの試しのプラグイン `probe` を作った。

- `.claude-plugin/plugin.json`: 名前 `probe`。
- `agents/echo-model.md`: `model: sonnet`、`tools: Read`。システムの指示に書かれた自分のモデル名を答えるだけのエージェント。
- `commands/ask.md`: 「Agent ツールで `probe:echo-model` を呼ぶ。`model` の引数は渡さない」と書いたコマンド。

`claude plugin validate` は通った（警告あり）。空のフォルダーで、次を実行した（Claude Code 2.1.316、Windows 11）。

```text
claude -p "/probe:ask" --plugin-dir <probe> --model haiku --allowedTools "Agent" --output-format json
```

## 結果

| 確かめたこと | 結果 |
| --- | --- |
| `claude -p` で、プラグインのコマンド（`/probe:ask`）が動くか | 動いた |
| `subagent_type` に `<プラグイン名>:<name>`（`probe:echo-model`）を渡して呼べるか | 呼べた |
| メインが Haiku でも、エージェントが `model: sonnet` で動くか | 動いた。出力の `modelUsage` に `claude-haiku-5-5` と `claude-sonnet-5-5` が並び、エージェントの記録（`~/.claude/projects/<作業フォルダー>/<セッション>/subagents/agent-*.jsonl`）の応答のモデルは `claude-sonnet-5-5` だった |
| エージェントは、自分のモデル名を知っているか | 知っていた。「Sonnet 5.5、モデル ID: claude-sonnet-5-5」と答えた（メインは「Haiku 5.5（claude-haiku-5-5）」） |
| エージェントに渡る指示 | エージェントの本文のほかに、ユーザーのグローバルの `CLAUDE.md` とプロジェクトの指示が、メインと同じく渡っていた。報告は `SubagentHandback` で呼び出し元に届いた（デスクトップアプリの中から動かした `claude -p`） |

費用は 0.027 USD だった。

## 設計への影響

- 表示名（`translated_by`）は、エージェントがシステムの指示から自分のモデル名を読んで書ける。
- 実地の確かめでは、出力の `modelUsage` とエージェントの記録の応答のモデルで、エージェントが Sonnet で動いたことを確かめられる。
- エージェントにもユーザーの指示（応答の最後に使った道具を書く、wiki に記録する、など）が渡るので、報告の JSON のあとに文が続いたり、エージェントが wiki に書こうとしたりしうる。報告の読み方と、エージェントの本文の書き方で扱う。

## 追試: `omitClaudeMd`（2026-11-14）

試しのエージェントの frontmatter に `omitClaudeMd: true` を足して、同じコマンドを動かした（費用は 1 回目と同じくらい）。

| 確かめたこと | 1 回目（なし） | 追試（`omitClaudeMd: true`） |
| --- | --- | --- |
| エージェントの記録に、ユーザーの `CLAUDE.md` の中身（「Contents of C:」で始まる指示）があるか | 2 か所ある | ない |
| エージェントの本文の `${CLAUDE_PLUGIN_ROOT}` が置き換わるか | 置き換わる | 置き換わる（プラグインのパスを答えた） |
| エージェントのモデル | `claude-sonnet-5-5` | `claude-sonnet-5-5` |

`omitClaudeMd: true` を付ければ、ユーザーとプロジェクトの指示はエージェントに渡らない。エージェントに要る条件は、呼び出す側が依頼に書いて渡す。
