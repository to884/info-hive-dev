## 判定

**条件付きで採用可。確信度：高。** 致命的・重大な欠陥は確認できなかった。ただし、旧版 rag に対する無条件の案内と、1024 バイト境界の表現に食い違いが残る。

## 致命的・重大な欠陥

なし。

## 崩れる前提

- **「rag の MCP ツールが使えるなら、新しい受理条件が適用される」**：wiki だけを更新し、rag 0.5.0 を使い続けると崩れる。接続できることと、前置きのある PDF を処理できることは別である。
- **「1024 バイト目」と「オフセット 1024」が同じ位置を指す**：通常の 1 始まりの数え方では崩れる。実装が受け付ける最終位置は、1025 バイト目である。

## 見落としと軽微な問題

1. **軽微：実際の取り込み手順には、rag のバージョン条件がない。**

   `skills/info-hive/references/ingest-workflow.md:18` は、前置きのある PDF を無条件に受け付けると案内する。

   反例は、**wiki 0.11.1＋rag 0.5.0** で、改行 1 バイトの後ろに有効な PDF 本体が続くファイルを取り込む場合。登録後、ワーカーの `read_pdf` が「PDF の形式ではありません」で失敗する。`CHANGELOG.md:13` には旧版との差があるが、取り込み手順自身にはなく、`SKILL.md:163` にも CHANGELOG を読む指示はない。

   旧実装の根拠は、[rag 0.5.0 の `scripts/rag_index.py:63`](https://github.com/to884/info-hive-rag/blob/0ca80c7cd4e485ff1d5f602c735d455318c50eeb/scripts/rag_index.py#L63)。旧版が安全に拒否するため、重大とは判定しない。

2. **軽微：境界を文字どおり読むと、受理範囲が 1 バイト狭い。**

   対象は `ingest-workflow.md:18` と `CHANGELOG.md:13` の「先頭から 1024 バイト目まで」。

   反例は、`b" " * 1024 + PDF本体`。`%PDF-` は **1025 バイト目、0 始まりのオフセット 1024** に始まるが、実装の `has_pdf_header` は `True` を返す。抽出した実関数を実行し、オフセット 1023・1024 は通り、1025 は通らないことを確認した。

   根拠は [rag の `scripts/rag_index.py:36–42`](https://github.com/to884/info-hive-rag/blob/3a2cbe31038e42ba9c997736788784af67a249af/scripts/rag_index.py#L36)。rag 側の説明文にも同じ曖昧さがある。

3. **軽微：CHANGELOG のリリースリンクが規約と一致しない。既存不整合の継承である。**

   `CONTRIBUTING.md:139,159` は、新版の参照リンク追加と `[Unreleased]` の比較元更新を要求する。しかし `[0.11.1]: …` はなく、`CHANGELOG.md:378` の比較元は `v0.7.0` のまま。変更履歴を読むと、新版の見出しからリリースへ移動できず、Unreleased は公開済みの変更まで含む。

   ただし `origin/main` でも比較元は `v0.7.0` で、0.11.0 の参照リンクもない。今回新たに生じた比較元の退行ではない。

## 検証した事実

- **差分：一致。** HEAD `014593f` の変更は、提示された 3 ファイルの差分と一致した。
- **拒否の段階：確認。** 拡張子・通常ファイル・パスの条件は登録時の `Config.pdf_path` で検査する。ヘッダーは登録時には読まず、ワーカーの `Engine.ingest_pdf → read_pdf` で検査し、失敗をジョブの `failed` にする。[`rag_config.py:181`](https://github.com/to884/info-hive-rag/blob/3a2cbe31038e42ba9c997736788784af67a249af/scripts/rag_config.py#L181)、[`rag_jobs.py:55`](https://github.com/to884/info-hive-rag/blob/3a2cbe31038e42ba9c997736788784af67a249af/scripts/rag_jobs.py#L55)、[`rag_worker.py:150`](https://github.com/to884/info-hive-rag/blob/3a2cbe31038e42ba9c997736788784af67a249af/scripts/rag_worker.py#L150)。
- **既存のパス条件：一致。** 解決後の通常ファイルと `.pdf` を検査し、拡張子は大文字小文字を区別しない。UNC 入力と、派生データ・モデルキャッシュ・uv キャッシュ内の PDF を拒否する。
- **古い条件の残存：見つからず。** 隠しファイルと通常は無視されるファイルも含めて検索した。残る `%PDF-` は今回の 2 文と `eval/scripts/test_fetch.py:127` のテスト用データで、旧条件を要求する期待値ではなかった。
- **バージョン：一致。** `plugin.json:3` と CHANGELOG の見出しはともに 0.11.1。親 `AGENTS.md` の同時更新規則と、`CONTRIBUTING.md:153` の文書変更を PATCH とする規則に合う。
- **依頼時点との違い：確認。** 調査時点で [rag PR #7](https://github.com/to884/info-hive-rag/pull/7) はマージ済みだった。照合には PR の head `3a2cbe3` を使用した。
- 実行検証はヘッダー判定関数まで。PDFium による抽出を含む結合試験は実行していない。ファイルは変更していない。

## 崩せなかった点

- rag 0.5.1 が、先頭の改行や空白だけを理由に PDF を拒否しなくなったという変更。
- 拡張子・通常ファイル・UNC・派生データについての既存の制約。
- `queued` を完了扱いせず、`completed` 後に要約を作る手順。
- 0.11.0 から 0.11.1 への PATCH 更新。

使用した MCP サーバー：GitHub  
使用した Agent Skills：なし
