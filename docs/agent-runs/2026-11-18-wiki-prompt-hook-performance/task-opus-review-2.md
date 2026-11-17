# 性能修正の指摘を直したコードの再レビュー

前回セッション `3e5998ab-ddc9-4989-ba17-2af1d0e915cf` の却下の指摘に対応した。前回のレポートを根拠に、修正した箇所と、新たな欠陥を敵対的にレビューしてほしい。読み取り専用、日本語。追加の有料モデル、全件ベンチマーク、他作業のプロセス操作は禁止。

## 対応

1. **致命: rawcheck/fetchのimport失敗、重大: 外部版の型と規則の混在**
   - `wiki_pages.markdown_module(name)` を追加した。同梱版の初期化・検証をロック内で済ませてからサブモジュールを取得し、そのファイルの所在も同梱ディレクトリ内と検査する。初期化後に外部のサブモジュールが混ざった場合も拒否する。
   - `wiki_rawcheck` の2箇所の `importlib.import_module` と、`wiki_browse_core` のTokenの取得を、この共通の口へ変更した。全scriptsとragを、通常のimportだけでなく動的importも含めて検索した。
   - `test_page_set.VendoredParserTests.test_rawcheck_and_fetch_load_vendored_modules_before_using_them` はfreshなPythonで、外部版なし・外部版を先にsys.modulesへ入れた場合の両方を試す。rawcheck/fetch/browseのimportとTokenの同一性、表の規則の所在、同梱パーサーの型、表の解析、初期化後に外部サブモジュールを差し込んだ場合の拒否まで確認する。
   - 実際の外部markdown-it-py 4.3.0を先にimportしたuv環境でも、rawcheckが同梱3.0.0のTokenへ切り替わることを確認した（単なるinspect.getfileではなくクラスのidentity）。
2. **子の優先度の二重適用**
   - 子は `_foreground_priority()` を呼ばず、親が成功したときだけcreationflagsでAboveNormalになる。試験用コピーは、子でこの関数が呼ばれたら失敗させる。さらに親のSetPriorityClassを拒否した場合に、親子ともNormalになることを実起動で確認した。
3. **既存venvと表現**
   - 入口が `VIRTUAL_ENV` またはcwdの `.venv` を使うことと、入口のランチャーのコストが残ることを明記した。除くのはスクリプト専用venvであり、system Pythonのみとは主張しない。
   - 実起動の試験を、cwdの既存venv、有効なVIRTUAL_ENV、BashとPowerShellで追加。実際にvenvのsys.executableが選ばれ、候補が届くことを確認した。
4. **測定のハッシュ・条件・幅**
   - ベンチマークのシェルcwdも合成プロジェクトにそろえた。逐次にもhook/context/pagesのhashを記録。
   - コード変更後に全て測り直した。フック4本同時。8負荷20回、16負荷20回を2バッチ、cwdのvenv+8負荷20回、active venv+8負荷20回、明示リンクなしの題の一致+8負荷20回。**計120/120で候補2件が届き、全てexit0・stderr空・5秒以内、最大3.2588秒**。
   - 16負荷の2バッチはp95 1.3563秒と1.6256秒。逐次検索はp95 780.2ms・10/10。前の1.17秒も残しており、一定の速度向上率や任意の負荷の保証は主張しない。
   - 最終データは `review2-*`（`review2-names-8.json` を除く）。名前一致の最初の測定はページ1の元の題を取り違えて置換できず、候補1件となった無効なfixtureで0/20になった。製品のゲートは変えず、元の題をファイルから読むよう測定器を直し、別ファイル `review2-names-corrected-8.json` に再測定した。誤った記録も残して報告書で区別した。
   - S1/S2、150ページ、同時フック4本、通常優先度の合成負荷だけの測定。I/Oや同じAboveNormalとの競合、任意の負荷への上限は引き続き保証しない。RUST_LOGを除いた条件もそのまま明示している。

## 試験の結果

- フック・実起動・測定・ページ集合・fetch・web_check・web_raw・YouTube: **393件成功（1skip）**。
- PyYAML6.0.3付きPython3.12でuninitializedとbrowse: **171件成功（6skip）**。前回の未切り分けの9件も含む全ての非skipが通る。
- 最後の同梱版の追加チェック: **6件全成功**。
- `docs/research/wiki-prompt-hook-performance-2026-11-18/validation.json` に現在のコードと各最終測定のhash・合否・試験の結果を保存し、実際に現在のソースとの一致をassertした。

生データは `docs/research/wiki-prompt-hook-performance-2026-11-18/`。説明は同名の `.md`。

既知の実装の重大欠陥が閉じたか、修正でさらに壊したものがないかを判定する。前回から変えていない設計とモデル表の全調査を繰り返す必要はない。優先してrawcheckのfreshなimportと外部版の混在、優先度失敗時の親子、最終データのhashと数値、報告書の主張を照合してほしい。必要な試験は狭く実行する。重大と軽微、実装の欠陥と既知の測定範囲の限界、確認と推測を区別する。
