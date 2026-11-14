# プラグインのコマンドの本文の `${CLAUDE_SESSION_ID}` と、依頼の記録の書かれる時点（2026年11月14日）

[セッションの取り込みの設計](../plans/wiki-session-ingest-2026-11-14.md)の「実装で触る範囲」が求める、実装の前段の確かめである。S1 は、`commands/ingest.md` の本文の `${CLAUDE_SESSION_ID}` で実行中のセッションの ID を得て、記録の中の取り込みの依頼の `uuid` を `--before` にする。これが成り立つには、次の 2 つが要る。

- (a) プラグインのコマンドの本文で、`${CLAUDE_SESSION_ID}` がセッションの ID に置き換わる。
- (b) 取り込みの依頼（スラッシュコマンドを打った記録）が、コマンドの本文が動き始めた時点で、記録のファイルに書かれている。

## 結論

どちらも成り立った。設計の S1 は変えずに進める。

| 確かめ | `claude -p` | 対話のセッション |
| --- | --- | --- |
| (a) 置き換わる | 成り立つ | 成り立つ |
| (b) 依頼の記録が先に書かれている | 成り立つ（`origin` なし） | 成り立つ（`origin.kind` が `human`） |

## 方法

一時的なプラグイン `probe`（`--plugin-dir` で読み込む）に、コマンド `/probe:check` を置いた。本文は、最初のツールの呼び出しとして次のコマンドを実行させる。

```text
python "<probe.py>" '${CLAUDE_SESSION_ID}' "<result.jsonl>"
```

引数を単一引用符で囲み、シェルが環境変数として展開しないようにした。置き換わらなければ、`probe.py` は `${CLAUDE_SESSION_ID}` の文字列をそのまま受け取る。`probe.py` は、受け取った ID で `~/.claude/projects/*/<ID>.jsonl` を探し、その時点のファイルにある記録を読み、`<command-name>` を含み `/probe:check` を含む `user` の記録があるかを見る。会話の文は出さず、記録の種類、`uuid`、`origin.kind`、`isMeta` だけを書き出す。

- `claude -p`: 標準入力から `/probe:check` を渡し、`--model claude-haiku-5-5 --allowedTools "Bash(python:*)"` で動かした。
- 対話のセッション: ターミナルで `claude '/probe:check' --plugin-dir <probe> --model claude-haiku-5-5 --allowedTools 'Bash(python:*)'` を起動した（プロンプトを先に置かないと、`--allowedTools` の可変長の引数に飲まれ、コマンドが動かなかった）。

## 結果

- どちらでも、`probe.py` が受け取った引数は UUID で、そのファイルが 1 つだけ見つかった。環境変数 `CLAUDE_SESSION_ID` は、ツールのプロセスには設定されていなかった。
- どちらでも、本文が動いた時点の記録に、依頼の記録があった。その直後に、展開したコマンドの本文が `isMeta` の `user` の記録として続き、その後に `attachment` の記録が並んでいた。
- 対話のセッションでは、依頼の記録の `origin.kind` は `human` だった。設計の区分 H に入り、`inspect` の `human_tail` に現れる。`claude -p` では `origin` がなく、人の発言が 0 件なので終了コード 2 で止まる（設計どおり）。
- 手元の記録（全プロジェクト）では、`<command-name>` を含む `user` の記録 389 件の直後の記録は、どれも親（`parentUuid`）がその記録だった。`origin.kind` が `human` のもの 216 件の直後は、どれも `isMeta` の `user` の記録だった。

## 確かめていないこと

- 確かめたのは、Claude Code 2.1.316（CLI）で、スラッシュコマンドを打った場合だけである。デスクトップアプリのセッション、Skill ツールを通したコマンドの起動、2.1.321 以降は確かめていない。
- そのため、S1 は、`${CLAUDE_SESSION_ID}` が置き換わらずに残ったときや、UUID の形でないときは、ユーザーに ID か記録のパスを聞く。`${CLAUDE_SESSION_ID}` は `commands/ingest.md` の本文に書く。Read で読む参照の文書（`references/` の下）では置き換わらない。

## 実装のための記録（会話の文は含まない）

同じ日に、手元の全プロジェクトの記録の構造を数えた。設計書の「検証環境の値」は 1 つのプロジェクトの値なので、種類が増えている。

- `uuid` のない記録の種類は 23 あった。`agent-name`、`ai-title`、`api-request`、`api-request-blob`、`api-request-shape`、`artifact-autoreact-ledger`、`artifact-comment-monitor`、`atis-latch`、`bridge-session`、`cost-state`、`custom-title`、`file-history-delta`、`file-history-snapshot`、`frame-link`、`last-prompt`、`mode`、`permission-mode`、`pr-link`、`queue-operation`、`relocated`、`session-owner`、`tools-used`、`worktree-state`。
- `attachment` の種類は 43 あった。`origin` を持つのは `queued_command` だけだった。
- `origin.kind` の値は `human`、`task-notification`、`peer` の 3 つだった。`queued_command` の `attachment.origin.kind` も同じ 3 つで、`origin` のない `queued_command` が 474 件あった。
- `system` の `subtype` に、設計書の表にない `model_refusal_fallback` と `turn_duration` があった。アシスタントのブロックに `fallback` が 1 件あった。どれも、設計の表のとおり閉じる側（境界、または除く）に入る。
