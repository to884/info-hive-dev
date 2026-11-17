# 依頼: プロンプトのフック（ADR-0032 の段階 1）の設計と実装の敵対的レビュー

Claude Code のプラグイン `wiki` に、UserPromptSubmit のフックを足した。指示を送るたびに、指示に関係しそうな wiki のページの候補を語彙で選び、題と場所だけを `additionalContext` で知らせる。候補を読む段のモデルとエフォートは、段の表（R0〜R3）で決めて知らせる。

## 対象が果たすべき目的

- 利用者の指示を決して止めない（UserPromptSubmit で終了コード 2 を返すと指示が止まる）。何が起きても終了コード 0 で黙る。
- 無関係な指示、短文、利用者が打たないターン（`<agent-message>` などのタグで始まる）では何も足さない。
- 足すのは題、パス、見出し、索引の要約だけで、wiki の中の信頼しない文がエージェントへの指示として働かない。
- プロンプトの経路で、サーバーの起動、依存やモデルの取得、wiki への書き込み、外部への送信をしない。遅れは数百 ms に収める。
- `/wiki:query` の確信度の規則（ADR-0028、道具を呼んだ順で決める）と矛盾しない。
- Windows（Git Bash か PowerShell）、macOS、Linux で同じに動く。

## 読むべきファイル（パスは info-hive-dev の worktree のルートから）

- 決定と計画: `docs/adr/0032-wiki-prompt-hook-suggests-candidate-pages.md`、`docs/plans/wiki-prompt-context-hook-2026-11-17.md`、`docs/research/wiki-prompt-hook-stage0-2026-11-17.md`
- 実装: `info-hive-wiki/hooks/hooks.json`、`info-hive-wiki/skills/info-hive/scripts/wiki_prompt_hook.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_prompt_context.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_tokens.py`、`info-hive-wiki/agents/wiki-reader.md`、`info-hive-wiki/.claude-plugin/plugin.json`
- 文書: `info-hive-wiki/skills/info-hive/references/prompt-context.md`、`info-hive-wiki/skills/info-hive/references/query-confidence.md`（理由 0F と決め方の 0）、`info-hive-wiki/skills/info-hive/SKILL.md`（「プロンプトのフックの候補」）
- 試験と評価: `tests/wiki/test_prompt_hook.py`、`tests/wiki/eval_prompt_context.py`、`tests/wiki/fixtures/prompt_context/prompts.json`
- 共有の関数: `info-hive-wiki/skills/info-hive/scripts/wiki_workspace.py`、`wiki_initialized.py`、`wiki_pages.py`（`walk_pages`、`walk_index_files`）、`wiki_text.py`

## 特に崩してほしい点

1. `; exit 0` の起動行で、なお 0 以外になる道、または時間切れで指示が遅れる道。
2. ゲートが評価のデータに過適合していないか。評価のデータの作り方（作者側が書いた問い）の偏り。
3. 無害化をすり抜けて、wiki の文が指示として読まれる道。
4. セッションの状態のファイルの競合（同じセッションで並んで動く場合）、`session_id` の扱い。
5. `wiki_roots` が、意図しない wiki を読む、または `cwd` の取り違えで別のプロジェクトの wiki を出す道。
6. 確信度の規則 0F の文が、既存の決め方 1〜4 と食い違う、または判定できない場面。
7. 段の表と「読み方」の行が、メインに過剰なサブエージェントの呼び出しをさせる、または `effort` の引数を渡す決まりとして不十分な点。
