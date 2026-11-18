---
type: "source"
title: "古い uv の UV_SYSTEM_CERTS の直しと wiki 0.19.4 のリリース"
tags: ["リリース", "mcp", "uv", "証明書"]
authors: ["to884"]
raw: "docs/agent-runs/2026-11-15-wiki-uv-system-certs"
ingested: 2026-11-15
created: 2026-11-15
updated: 2026-11-15
---

# 古い uv の UV_SYSTEM_CERTS の直しと wiki 0.19.4 のリリース

利用者向け文書の計画（`docs/plans/usage-docs-2026-11-15.md` の 2-1）で見つけた、MCP サーバーの入口と中継の不具合を直し、wiki 0.19.4 として出した記録である。原本は `docs/agent-runs/2026-11-15-wiki-uv-system-certs/` にある。

## 不具合

入口と中継は、`uv sync --script` が TLS 証明書の検証で失敗すると、OS の証明書ストアを使って 1 回だけやり直す（`wiki_mcp_common.py` の `_uv_sync`）。利用者が証明書の設定を決めていれば、やり直さない。

0.19.3 までは、`UV_SYSTEM_CERTS` か `UV_NATIVE_TLS` が設定されているだけで「利用者が決めた」とみなしていた。古い uv は `UV_SYSTEM_CERTS` を黙って無視するので、古い uv で `UV_SYSTEM_CERTS=true` を設定した利用者は、証明書の検証に失敗したうえ、`UV_NATIVE_TLS=true` でのやり直しも受けられなかった。設定しないときより悪かった。

## 直し方

利用者が決めたとみなすのを、uv が実際に使う設定だけにした。

- `UV_NATIVE_TLS` があるか、両方あるとき: どの uv でも利用者の設定を使うので、決定とみなす。
- `UV_SYSTEM_CERTS` だけで、真でない値: 新しい uv では決定、古い uv では無視されるが uv の既定と同じなので、決定とみなす。
- `UV_SYSTEM_CERTS` だけで、真の値: `uv sync --help` で uv の版を確かめ、新しい uv のときだけ決定とみなす。古い uv なら `UV_NATIVE_TLS=true` で、確かめられなければ両方の名前を真にしてやり直す。
- 真偽の値は、uv と同じに、大文字と小文字を区別せず、前後の空白を除かずに読む。

## レビュー

GPT-6.1 Sol の敵対的レビューを 2 回受けた。1 回目の重大は、`uv sync --help` が失敗したときに「新しい uv」とみなすので、直すはずの失敗が残ることだった。原因は、uv の版の判定が「読む」と「確かめられない」を同じ値で返していたことで、判定を 3 つの状態（読む、読まない、分からない）にして直した。前からあった「利用者の設定がなく、版が分からないとき」の取り違えも、同じ直しで消えた。2 回目は採用可で、案内の文の軽微な指摘 2 件を直した。uv 0.11 と 0.12 は、両方の変数があるとき、どちらかが真なら OS の証明書ストアを使う。のちの版は `UV_SYSTEM_CERTS` を優先する。

## リリース

1. 子の PR（to884/info-hive-wiki#67）の CI 4 つが通ってから、マージした（`9deda8f`）。
2. 注釈付きのタグ `v0.19.4` を `9deda8f` に付け、GitHub リリース `v0.19.4` を作った。本文は CHANGELOG の 0.19.4 の節である。
3. `claude plugin marketplace update info-hive` と `claude plugin update wiki@info-hive` で、0.19.4 が入ることを確かめた。入ったファイルに、新しい関数 `uv_reads_system_certs` がある。
4. 親の PR（to884/info-hive-dev#128）で、サブモジュールの参照を `9deda8f` に進め、試験 9 件を足した。

古い uv で `UV_SYSTEM_CERTS=true` を設定し、実際のプロキシの内側で確かめることはしていない。利用者向け文書の段階 2 の確認 9（社内のプロキシ）で、その環境があれば確かめる。

## 関係するページ

- [[リリースの確かめ方]]
