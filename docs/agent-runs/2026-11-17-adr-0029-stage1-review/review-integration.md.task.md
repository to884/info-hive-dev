ADR-0029 段階1を最新 main に統合した後の敵対的レビューです。変更禁止、読み取り専用です。
Astra 第6回は review-6-native.md で採用可でした。今回は最新 main (plugin 10afe5d) への統合と CI 接続を主な対象とします。
plugin は 9d51a2c で、git -C info-hive-wiki diff origin/main HEAD を読んでください。
競合解消は CHANGELOG で Unreleased の段階1項目と最新リリースを両方残し、wiki_browse_core.WikiSite.__init__ で self._build_assets() とリンク診断追加を両方残しました。自動マージされた wiki_pages/wiki_lint/wiki_browse_fs と Codex/SVG/Mermaid 追加の交点も確認してください。
親の tests/wiki/test_wiki_links.py が Linux/macOS/Windows × Python3.12/3.14 の .github/workflows/wiki-walk.yml に接続されています。POSIX 実ファイル名や .. とリンクの反例が実行されることを確認してください。
重大・軽微を再現条件と根拠付きで記載してください。スコープ外の raw 段階2、TOCTOU 完全防御は要求しません。必要ならローカルの安全なテストを実行できます。新しいレビューの再委譲は不要です。
