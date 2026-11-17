# Codex の会話履歴の取り込みの検証

日付: 2026-11-17。設計は [ADR-0032](../../adr/0032-codex-session-history.md)。前の Codex プラグイン対応と同じ、未公開の 0.28.0 の変更に含めた。Claude CLI とモデルのターンは呼んでいない。

## 実機で確認したこと

Windows と Codex CLI 0.166.0 で、合成した会話を一時的な `CODEX_HOME` に置いて検証した。[結果の JSON](smoke.json) は件数、ハッシュ、検査の真偽値だけを含み、会話本文は含まない。

```powershell
python -X utf8 -B tests/wiki/check_codex_session.py --out docs/research/wiki-codex-session-2026-11-17/smoke.json
```

- legacy と paginated の両方で、実際の `wiki_session.py` を直接起動し、`locate`、`inspect`、`decide init`、`show --meta`、`write`、`verify` を通した。
- 両方式で、人の発言 1 件と Codex の応答 1 件を抽出した。最新のターン全体を除外し、`cutoff_kind: "turn"` で範囲が固定されていることを確かめた。
- raw は `source_kind: "codex-session"`、`source_sha256_of: "codex-thread-range-v1"` となり、承認済みハッシュとの一致、読み取り専用、取り込み前後の元の履歴のバイト列の一致を確認した。
- paginated の試験の準備としてだけ、合成したホームに対して `migrate-rollouts --apply --thread` を明示的に実行した。製品の処理には移行を含めていない。
- 確認後、合成したホームと読み取り専用の raw を含む一時ディレクトリを削除した。通常の Codex の設定と会話の内容は変更していない。

別途、実行中のチャットでも `locate` → 範囲を固定した二回の読み取り → メモリ内での raw の生成が通ることを確認した。この検証では件数だけを出し、会話本文、未加工の API 応答、生成した raw はファイルに保存していない。

## 自動試験

Codex の追加試験は `tests/wiki/test_codex_session.py` の 36 件で、すべて成功した。合成した API 応答を使い、本文の許可リスト、伏せ字、返答先、時差、メタデータの制限、境界以後の追記と範囲内の改変、現在の ID の選択、ページング、形式別の取得、RPC のエラーからの漏れ防止、共通の raw の保存と scan / verify を確かめた。

Claude Code の既存の fixture は、変更前と同じ `base_sha256` と raw の SHA-256 に一致した。従来の決定ファイルの形式と、Claude Code の出力は変えていない。

関連する 8 ファイルの通し試験は 228 件で失敗なし、Windows で動かさない POSIX の 1 件だけスキップした。その後、入力上限を取得前に検査する試験と、表示の時差で出典のハッシュが変わらない試験を追加し、Codex の 36 件を再実行して通した。文字コードの静的検査は 60 ファイルで通った。追加試験は既存の Wiki MCP の CI にも組み込んだ。

## レビューで修正したこと

- 実行中の範囲を「最新のユーザー発言」で決めると、追加入力が間に入ったときに取り込み依頼や作業が混ざる。依頼を含むターン全体を除外する境界に変えた。
- legacy の `thread/items/list` は実機で未対応のエラーを返した。legacy は `thread/turns/list` の完全なターン、paginated は `thread/items/list` に分けた。
- ユーザー本文の先頭の見た目から、指示の差し込みかを推す処理を除いた。正規化された `userMessage` と構造上の型で判定する。
- 直接スクリプトとして起動した入口と、アダプターが参照する共有モジュールを同一にした。`Fail` が二つのクラスになり、例外が捕まらない問題を防いだ。

Codex の別エージェントによる読み取り専用レビューでは、修正後は採用可と判断された。利用者の指示に従い `ask-claude` は使っていない。

## 検証していない範囲

macOS / Linux の実行、他の Codex CLI の版、公開済みのマーケットプレイスからの導入は未確認である。履歴 API には過去の応答のモデル名を確実に取得できない場合があるため、現在の設定から推測せず「不明」と記録する。Codex 自身が古い履歴の検索用の索引を補うことはある。
