# wiki 0.31.0 の公開と導入の検証

日付: 2026-11-18（日本時間）。ADR-0029 段階1の実装を main に統合して公開した。最初に予定した0.30.0は、並行作業のPlaywright対応が先に公開したため、そのmainを取り込んで0.31.0に変更した。

## 公開したもの

- プラグイン PR: https://github.com/to884/info-hive-wiki/pull/88
- main のマージコミット: `b360f23934f8a2b9768f33e1a72338c72c116140`
- 注釈付きタグ `v0.31.0` は、そのマージコミットを指す。GitHub リリースは draft でも prerelease でもない。
- GitHub リリース: https://github.com/to884/info-hive-wiki/releases/tag/v0.31.0
- Claude Code / Codex の両 manifest は0.31.0、CHANGELOG の日付は2026-11-18。比較リンクは0.31.0と0.30.0を含めて整えた。
- プラグインのリモートブランチ `feat/links-stage1` を削除した。
- 開発用の回帰テストとレビュー、導入の記録は、親 PR https://github.com/to884/info-hive-dev/pull/173 に置く。親の参照はプラグインのマージコミットへ更新する。

## 公開前の確認

`premerge-ci.json` に、確認したコミットと全21ジョブの成功を記録した。プラグイン4、親の walk6 / browse4 / MCP1 / PDF6で、対象はPython3.12/3.14、walkはLinux/macOS/Windowsである。公開したマージコミットと、検証したプラグインの4b751a2の木は、git diffで一致した。

手元でもプラグイン自身のCI手順を完走した（`integration-local-verification.json`）。構造を直した後は関連262件、索引と本文の文脈を分けた後は関連246件、リンク単体74件が成功した。件数は重複するので合計しない。

main統合後の大きな変更はOpusが敵対的にレビューし、最終の読む口には重大な指摘がなかった。最後の索引の文脈分離はOpusの利用上限により再確認できなかったため、ユーザーが先に指定していたAstraが独立に確認した。判定は採用可、確信度中。対象3ファイルのハッシュ一致と、実ディレクトリのリンクからSnapshot / Core / HTML / lintへの確認も保存した。詳しい範囲と留保は `integration-review-summary.md` にある。

## 公開カタログからの導入

すべて使い捨ての設定とプロジェクトで検証した。通常のユーザー設定は変更していない。導入の検証では生成モデルのターンを起動していない。

- Claude Code: `wiki@info-hive` 0.31.0 を導入し、v0.30.0から変わった全28ファイルがタグとバイト単位・SHA-256で一致した。入ったwiki_pagesで記事のハードリンクを拒否することも確認した（`claude-marketplace.json`）。
- Codex: `wiki@info-hive` 0.31.0、`wiki:info-hive` スキル、7個のMCPツールを認識した。重要な7ファイルがタグと一致し、statsと日本語queryが成功した。読む前後で試験用wikiの全ファイルが一致した（`codex-marketplace.json`）。
- スキル単体: `npx skills add to884/info-hive-wiki --skill info-hive --agent codex --copy --yes --json` で導入し、全164ファイルがタグと一致した（`skills-directory.json`）。

Codexの最初の検証は、確認後に一時Gitファイルのロックで後片付けが失敗した。検証の証拠を先に保存し、後片付けだけを期限付きで再試行するよう、開発用ヘルパーを修正して再実行した。再実行は導入・MCP・一時ディレクトリの削除まで成功し、前回残った一時ディレクトリも削除した。最初のエラーは `codex-cleanup-first-error.log` に残した。

## 範囲と残件

wikiの記事と途中の道が対象で、rawのリンクの検査は段階2である。補助的な検索のbacklinksと判定レイヤーのmentionには、拒否した記事と同名の別ページへの解決の整合性の残件がある。禁止した記事の読み取りの迂回ではない。GraphPagesの属性をリストの再構成で落とさない注意も、レビューのまとめに記した。
