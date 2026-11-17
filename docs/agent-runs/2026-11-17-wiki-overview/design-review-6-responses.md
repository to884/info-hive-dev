# 第6回のレビューへの対応（設計第6版）

2026年11月17日、作者の依頼に従って、[Astra の指摘](design-review-6-astra-native.md) 2 件を設計書と ADR-0031 に反映した。
対象は `docs/plans/wiki-overview-2026-11-17.md` と `docs/adr/0031-wiki-page-overview-lives-in-a-sidecar.md` である。

| 指摘 | 対応 |
| --- | --- |
| 重大・C：原子的な置き換えから電源断後の存続を保証できない | 保証を、OS とファイルシステムが稼働し続ける間のプロセス停止に限定した。置き換え前の状態には初回の未作成も含める。電源断後の欠落、巻き戻り、破損は保証の範囲に含めず、元ページから再生成する。`written` 通知後も同じ制限があることを明記した |
| 軽微：元ページを読めなくなった場合の `write` の状態と応答が未定義 | 置き換え前に現在のページを読み、`page_changed` を確定する。消失は `page_gone` と終了コード 3、そのほかの読み取り失敗と非 UTF-8 は `page_unreadable` と終了コード 1。サイドカーを置き換えず、作業フォルダーを保持する。回復後は同じ `work_id` で再試行できる。応答ではページを再読せず、保存前の比較結果を使う |

設計書の背景、スクリプトの手順、コマンドの案内、保証の範囲、試験の計画、レビューの対応表を更新した。
ADR の決定、理由、影響にも同じ契約を書いた。

## 確認

- `git diff --check` は通った。
- `write` の手順が 1〜9 の順になっていること、現在のページの読み取りが置き換え前にあること、応答に再読が不要なことを確認した。
- 初回の未作成、既存概要の保持、読み取りの回復後の再試行、読み取り後のページ変更を、試験の計画に加えた。
- 電源断後も旧版か新版が壊れずに残るという断定が、設計書と ADR に残っていないことを確認した。
- 一次資料は [Python の `os.replace`](https://docs.python.org/3.12/library/os.html#os.replace) と [Linux の `fsync(2)`](https://man7.org/linux/man-pages/man2/fsync.2.html) を参照した。

新機能は未実装なので、新しいスクリプトの実行試験は行っていない。

## 完了後のレビューの状態

`AGENTS.md` に従い、`ask-claude` で Opus 5.5（high）に第7回の敵対的レビューを依頼した。
2026年11月17日22:04（日本時間）、Claude の5時間の利用上限で、対象を読む前に失敗した。
エラーに表示された解除予定は、同日23:30（日本時間）である。
**修正後の Opus レビューは未実施であり、採用可の判定を得たものではない。**

その後、作者が Opus の代わりに Astra でレビューすることを明示した。
第7回は GPT-6 Astra（high）で実施し、**採用可（確信度：高）、新しい致命的・重大・軽微の指摘なし**という判定を得た。
対象2文書のハッシュは、修正後の値から変わっていない。

- [第7回の Astra の依頼書](design-review-7-astra-task.md)
- [第7回の Astra の結果](design-review-7-astra-native.md)

- [第7回の依頼書](design-review-7-opus-task.md)
- [第7回の実行状態](design-review-7-opus.md.status.json)
- [第7回の実行ログ](design-review-7-opus.md.log)

対象の SHA-256：

- 設計書：`158411d580ebee759e4e0bb52b7a35521f9c587391e431f86b2515023cc77618`
- ADR：`1e02016b6e2bfd436c0f3814edfccc71939bddf277b5e84005170972c5f6899f`

使用した MCP サーバー: なし
使用した Agent Skills: japanese-tech-writing、ask-claude、claude-model-routing
