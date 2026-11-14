# browse の Fluent 2 の試作

`/wiki:browse` の画面を Fluent 2 にした試作である。配布対象ではない。設計は `docs/plans/wiki-browse-fluent2-2026-11-14.md` にある。

- `proto_fluent.py`: 合成の Wiki から、索引と記事のページを描く。スコープの表示の案ごとに `out/project-green/`、`out/project-neutral/`、`out/user/` を作る。
- `assets/`: 試作の独自の CSS（`style.css`）、配色を描く前に決める `theme.js`、ナビと絞り込みと検索の `app.js`。
- `shoot.mjs`: Chromium で撮り、`[style]`、CSP の違反、外への要求、はみ出し、コントラスト比、配色の切り替えの保存を確かめる。

Fluent 2 の CSS は、プラグインに同梱した写し（`info-hive-wiki/skills/info-hive/scripts/browse_assets/fluent2.css`）を使う。サブモジュールを `feature/browse-fluent2` にしておくか、`--assets` で場所を渡す。

```bash
python -X utf8 proto_fluent.py
node shoot.mjs <playwright の index.mjs の絶対パス> <out の絶対パス> <撮った画面の保存先>
```
