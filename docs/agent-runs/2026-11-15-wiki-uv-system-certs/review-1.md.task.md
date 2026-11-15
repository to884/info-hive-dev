# 依頼: 古い uv の UV_SYSTEM_CERTS の扱いを直した修正の敵対的レビュー

## 対象の目的

info-hive-wiki の MCP サーバーの入口と中継は、`uv sync --script` が TLS 証明書の検証で失敗すると、OS の証明書ストアを使って 1 回だけやり直す（`skills/info-hive/scripts/wiki_mcp_common.py` の `_uv_sync`）。利用者が証明書の設定を決めていれば、やり直さない。

直す前の不具合: 利用者が `UV_SYSTEM_CERTS` か `UV_NATIVE_TLS` を設定していれば、値と uv の版に関わらず「利用者が決めた」とみなしていた。古い uv は `UV_SYSTEM_CERTS` を黙って無視するので、古い uv で `UV_SYSTEM_CERTS=true` を設定した利用者は、やり直し（古い uv では `UV_NATIVE_TLS=true`）を受けられず、設定しないときより悪かった。

直し方: 利用者が決めたとみなすのを、この uv が読む設定だけにした（`_user_tls_setting`）。

- `UV_NATIVE_TLS` は新旧どちらの uv も読むので、値に関わらず決定とみなす。
- `UV_SYSTEM_CERTS` が偽の値なら、uv の既定と同じなので、uv が読むかに関わらず決定とみなす。
- `UV_SYSTEM_CERTS` が真の値なら、`uv sync --help` でこの uv が読むかを確かめ、読むなら決定、読まないなら「届いていない設定」として `UV_NATIVE_TLS=true` でやり直す。

あわせて、失敗したときの案内（`tls_error_message`）、README のトラブルシューティング、CHANGELOG（0.19.4）、`plugin.json` の版を直した。

## 対象

- プラグイン: サブモジュール `info-hive-wiki` のコミット 2ce076d（`git -C info-hive-wiki show 2ce076d`）。主に `skills/info-hive/scripts/wiki_mcp_common.py`
- 試験: `tests/wiki/test_uv_tls.py`（親のコミット b018ea4）。`uv run --python 3.12 --with cryptography python -X utf8 -m unittest tests/wiki/test_uv_tls.py -v` で流せる

## 確かめてほしいこと

- 「この uv が読む設定」の判定に、反例がないか。uv の版、値の書き方（大文字、空白、`0`、`no`、空文字など）、両方の変数があるとき、`uv sync --help` が失敗するとき、新しい uv が `UV_NATIVE_TLS` を読むという前提。
- uv が真偽の値をどう読むか（clap の BoolishValueParser と同じとした）が、uv の実際と合うか。合わない値で、誤ってやり直すか、やり直さないか。
- やり直しで直ったときに `os.environ` に入れる値が、以後の uv の呼び出しと子のプロセスで正しく働くか。
- 案内の文と README の記述が、実装と合うか。
- 試験が、直す前の実装で失敗し、直したあとの実装で通るものになっているか。
