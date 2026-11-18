# ADR-0029 段階2の設計と実装の敵対的レビュー

raw のリンク検証を壊す反例を探してください。編集と再委譲はしないでください。小さい使い捨ての配置の試験は実行できます。作者の決定の変更は求めません。

規範は docs/adr/0029-wiki-and-raw-hold-no-links.md、docs/plans/wiki-links-2026-11-16.md の対象、根、raw の解決の順番。今回の範囲と後続段階の分担は docs/plans/adr-0029-stage2-raw-links.md にあります。この分担も、段階2単独の目的と矛盾しないか見てください。

対象の実装は info-hive-wiki/skills/info-hive/scripts/ の wiki_raw.py（新規）、wiki_pages.py の resolve_raw と refused_link、wiki_lint.py、wiki_captions.py、wiki_mcp_server.py と wiki_mcp_common.py。呼ぶ側の文書は commands/lint.md と skills/info-hive/references/lint-workflow.md。親の tests/wiki/test_raw_links.py が新規の回帰試験で、test_wiki_links.py、test_mcp_server.py、.github/workflows/wiki-walk.yml に関連の変更があります。親とサブモジュールは別の Git リポジトリなので、差分はそれぞれで確認してください。

段階2の目的:
- source の raw を resolved / missing / ambiguous / unknown / link / outside で区別する。
- 絶対パス、wiki の綴りと解決した根の両方からの相対パス、session_id の親限定、先頭だけの ..、複数の raw と hash を扱う。
- 候補の所属を決める前に realpath で途中のリンクを消さない。リンク検査の起点はもっとも内側の指定された raw の根、なければ wiki の根、なければ対象そのもの。根と祖先は許す。
- リンクや検査不能を、ハッシュ不一致や候補なしで隠さず、中身を読む前に拒否する。ディレクトリの隠し項目以外の木も調べる。
- raw_sha256 で版、なければ session_id / url / final_url で身元を照らし、版未検証を返す。ディレクトリの hash は NFC + 実際の綴りで順を決め、JSON の行を LF で結ぶ（末尾 LF なし）。
- 守る木の外の rag の絶対パスの原本はリンク検査の例外。allowed_roots は外の原本にも当てる。
- lint、missing_raw、字幕と訂正の根拠の raw を共通化する。CLI --raw-root と MCP raw_root。拒否、曖昧さ、不確実さを利用者に伝え、自動で直さない。raw の拒否で wiki の同名のページのリンク切れを消さない。

後続段階: raw の書き手の raw_sha256 と根の記録の作成・記録の読み込み、upgrade、書き込みの部品と依存の完全性、取り込みの残る読み書き。これらの未実装そのものと、TOCTOU の完全防御は今回の欠陥としない。ただし今回接続した lint と字幕検査の迂回は対象。

手元では関連224件（skip7）、MCPサーバー経由2件が成功。その後に根がファイルの入力の拒否、一覧にあったのに属性を取れないメンバーをunknownにする直しと追加5試験を行い、新規31件（skip1）が成功。実際のハードリンクとジャンクションを使い、ファイルsymlinkと制御文字の名前の試験は作れないWindowsではスキップしています。CIの他OSはまだです。

重大には発生の度合い A（必ず）、B（日常で起きる）、C（まれな名前や時機）、D（作為的な配置）を添え、現ファイルと行番号、再現条件と結果を示してください。実測、モック、コードからの推論を分け、同じ原因はまとめてください。推測を欠陥として確定しないでください。判定と確信度を明記してください。
