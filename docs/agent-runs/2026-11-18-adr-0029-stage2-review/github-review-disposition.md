# 公開前に届いた GitHub レビューの3件

対象はプラグイン PR #92、`bbd2c56dbda3689d7e2c2dfd4397579cb15e807c`。2026-11-18に確認。いずれもP2で、推測のまま採らず実際の回帰テストで再現した。

| 指摘 | 再現と根本の修正 |
| --- | --- |
| raw の版・身元不一致を字幕検査が黙って除く | 2種類の不一致×無関係・動画・選択原本の6条件で警告がない。共通解決の mismatches を字幕の診断へ渡し、依存する参照だけを欠陥とする |
| 待っているディレクトリの古い属性でリンクをたどる | 後の兄弟の属性検査時に待ち行列の子を junction/symlink に替えると digest が呼ばれる。降りる直前に no-follow 検査を再実行する |
| セッション保存後の検査に session_id がない | wiki/raw を sibling raw のリンクにすると有効な保存が止まり読み取り専用化されない。最終 source と同じ身元と相対基準で解決する |

修正前: 追加した3メソッド、8失敗。修正後: `python -X utf8 -B -m unittest tests.wiki.test_raw_links tests.wiki.test_wiki_youtube tests.wiki.test_wiki_lint tests.wiki.test_wiki_session.ReadOnlyVerifyTests -q` は134件、skip1で成功。完全な同時置換防止を保証する変更ではない。

Opus 第5回は `task-5.md` の範囲を別途調べる。公開前に、修正後のコードと親の試験の CI を改めて通す。
