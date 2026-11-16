# 4 回目のレビュー（プロンプトの監査の指摘による直し）

`commands/query.md` を、Claude Sonnet 5.5 を対象にして監査した（claude-api スキルの prompt-audit）。その指摘 1〜5 で直した。差分は `git -C info-hive-wiki show HEAD`（b493f83）にある。

直したことは次のとおりである。

1. 18 行の `warning` の説明を、コードに合わせた。`warning` は埋め込みの途中だけでなく、モデルを用意している途中と使えないときにも出る。このとき意味の検索は使っていない。
2. `query-workflow.md` の手順 4 の被リンクの探し方を、grep から `--backlinks` に変えた。コマンドの 20 行と `SKILL.md` の 115 行にそろえた。
3. 27 行の `decision-models.md` のパスに `${CLAUDE_PLUGIN_ROOT}` を付けた。
4. 手順 4 の先頭に、答えを自分の知識ではなく wiki から取り、答えを知っていると思う質問でも wiki を確かめてから答えることを足した。wiki に関係する内容がないと伝える前に検索することも足した。Claude Sonnet 5.5 は、知識を問う質問で、つながっている検索を使わずに自分の知識で答えることがある、という移行の手引きによる。
5. 「0 件でも、同じ検索を CLI でやり直さない」を、「同じ検索語で」に限り、理由を添えた。検索語を変えて探し直すのはよいと書いた。

CHANGELOG の 0.20.0 に Fixed を足した。

## 特に崩してほしい点

- 直しが、手順 5b（確からしさ）や手順 7（wiki に内容がないとき）、手順 8（保存）と新しく食い違っていないか。
- 4 の「答えを知っていると思う質問でも wiki を確かめる」が、インデックスを先に読み、すべてのページを読まないという設計（`SKILL.md` の「インデックスを先に読むナビゲーション」）と衝突しないか。読むページを増やしすぎないか。
- 5 の「検索語を変えて探し直すのはよい」が、検索を際限なく繰り返す道を開かないか。
- 1 の `warning` の 3 つの場合が、`wiki_mcp_server.py` の実際の文言と合っているか。
- 2 の `--backlinks` のコマンドの形が、`wiki_search.py` の引数と合っているか。
- 1〜5 のどれかが、コマンド、スキル、利用者向けの文書（`docs/commands.md`、`docs/workflows.md`）の間に新しい食い違いを作っていないか。

重大度は、利用者が普通に使う場面で起きる度合いで分けてほしい。

## 対象のファイル

- `info-hive-wiki/commands/query.md`
- `info-hive-wiki/skills/info-hive/references/query-workflow.md`
- `info-hive-wiki/CHANGELOG.md`
