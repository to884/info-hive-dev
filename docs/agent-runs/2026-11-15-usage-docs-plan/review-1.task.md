# レビューの対象が果たすべき目的

info-hive の Claude Code プラグイン（wiki、今後 rag など）の使い方を、まったく知らない人に説明する利用者向け文書を作る。その計画（`docs/plans/usage-docs-2026-11-15.md`）と、置き場所と形式の決定（`docs/adr/0022-usage-docs-are-html-in-plugin-docs.md`）を壊してほしい。

読者は Claude Code を使ったことはあるが、Python、uv、GitHub の認証には詳しくない。基準の環境は Windows 11 と Claude のデスクトップアプリ（Code タブ）で、Cowork での違いはハウツー 1 本に分ける。文書の種類は Diátaxis で分け、チュートリアルを最優先にし、読む順番は一本道にする。チュートリアルでは手順ごとに、毎回同じに現れる「成功の目印」を示す。事実は、コマンドの定義、スクリプト、実際の実行から取り、確かめていないことは未確認と書く。

作者がすでに決めたこと（計画の「決まったこと」の表）は、決定そのものを覆すのではなく、その決定のもとで計画が成り立つかを見てほしい。ただし、決定どうしが矛盾する、または決定が既存の仕組み（`/wiki:help`、ADR-0021、AGENTS.md の決まり）を壊すなら、それは指摘してよい。

## 特に崩してほしい点

1. 計画の事実の主張。プラグインの実装と食い違うもの。対象は `info-hive-wiki/`（サブモジュール。v0.16.0 の 8c400d7 が checkout されている）の `commands/*.md`、`skills/info-hive/`、`docs/`、`.mcp.json`。例: `/wiki:init` の質問、作られるファイル、`"status": "ready"`、`python` を直接呼ぶコマンド、`/wiki:help` と `docs/commands.md` の関係、モデルの大きさ。
2. チュートリアル（C1、W1、W2）の成功の目印が、本当に毎回同じに現れるか。モデルの判断に左右されるものが残っていないか。
3. 段階 2（新しい Windows 11 の環境での確認）の進め方で、確かめたいことが確かめられない手順。
4. ADR-0022 と ADR-0021（to884/info-hive-dev#105 で提案中。ブランチ `origin/docs/wiki-browse-fluent2` の `docs/adr/0021-wiki-browse-uses-fluent2-replica.md`）との矛盾。`fluent2.css` を 2 か所に持つことの扱い。
5. 既存の文書を消すことと、README、`SKILL.md`、`references/`、`UPSTREAM.md`、`wiki_help.py` の書き換えの規則、`tests/wiki/test_help_command.py` との関係で、壊れるもの。
6. 公開先を試作のあとに回すことで、それまでの段階で手戻りが生じる所。
