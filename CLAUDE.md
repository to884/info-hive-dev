# Claude Code Instructions

@AGENTS.md

## Claude が参照するファイルについて

ユーザーに参照するファイルを提示する際に、worktree で変更しているファイルにもかかわらず、リポジトリのルートからのパスで示している。
ユーザーが Claude のリンクをクリックしても、それらは存在しないか、変更が加えられていないものになり意味をなさない。
したがって、Claude が提示するファイルは worktree をルートとして扱う。worktree がなければリポジトリをルートとして扱う。

## タスクで使用するモデルおよびエフォートについて

- 指示でタスクを実行する際、タスクの内容を Claude が理解して、タスクの終了時にタスクを行うのに最適なモデル（"Haiku"、"Sonnet"、"Opus"、"Fable"）およびエフォート（"low"、"medium"、"high"、"xhigh"、"max"）を報告すること
- 次に行うタスクを Claude が知っている場合、タスクを行うのに最適なモデル（"Haiku"、"Sonnet"、"Opus"、"Fable"）およびエフォート（"low"、"medium"、"high"、"xhigh"、"max"）を案内すること
