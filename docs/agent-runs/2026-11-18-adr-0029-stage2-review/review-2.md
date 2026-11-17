## 判定

**採用可**（軽微のみ）。第1回の重大 1〜3 は、どれも再現の手順で閉じたことを確かめました。今回の修正が入れた新しい欠陥に、重大なものは見つかりませんでした。残るのは軽微な 5 件と推測の 1 件で、`..` を含む根で保存が失敗する件、訂正の根拠のソースの拒否が「見つからない」と書かれる件などです。確信度は中です。

## 致命的・重大な欠陥

なし。

第1回の重大 3 件の閉鎖を、同じ反例を今のコードに流し直して判定しました。

| 第1回の重大 | 再現の結果（実測） | 判定 |
| --- | --- | --- |
| 1. 身元の欄がない原本を `missing` にする | frontmatter のないファイル、frontmatter に `url` がないもの、バイナリ、水平線で始まる原本、ディレクトリが、どれも `resolved` と `version_unverified=True` になった。実際の wiki の 2 ページは、`url` があってもなくても `resolved` になった。親の `wiki/` に `--raw-root raw` で lint をかけると、`missing_raw` は 0、`caption_corrections` は 0 | 閉鎖 |
| 2. 無関係なページの曖昧さが字幕の findings に入る | 動画でないページの曖昧な raw で、`check_wiki` の findings は `[]` になり、知らせは `raw_warnings` に移った。`commands/ingest.md:35` の V8 にも「無関係な原本の知らせだけで止めない」と書かれた | 閉鎖 |
| 3. `wiki_youtube verify` が raw の根を渡さない | `wiki_youtube.py:619-623` が、最初の raw を `resolve_raw(..., raw_roots=[raw_root])` で検査してから読む。`check_wiki` にも `raw_roots` と `wiki_root_given` を渡している（630-631 行）。`parents_unchecked` も `raw_warnings` に残る（`wiki_captions.py:1149-1151`） | 閉鎖 |

## 崩れる前提

- **前提「`--raw-root` には `..` を含まない絶対パスが来る」**：保存と verify が、新たにこの前提に頼るようになりました。
  - 実測：`W\..\raw` を根にすると、`resolve_raw` は `unknown`（「.. を含むパスの所属は決められない」）を返しました。一方、`wiki_session.check_destination` はこの根を受け入れました。
  - 推論：セッションの `cmd_write` は、raw を作ったあとの 1707-1711 行で `Fail` します。raw は読み取り専用にならないまま残り、やり直しても `identical` のあと同じ検査で止まります。YouTube でも、`write` は通るのに V8 の verify で止まります。
  - 度合いは C です。`workspace.json` の `dirs.*` は `..` を拒みます（`wiki_workspace.check_relative`）。そのため、この形になるのは、利用者やエージェントがパスを直接書いたときだけです。
- **前提「身元の欄がない候補は、明示的に合う候補と同じ重みでよい」**（判断の分かれ目で、欠陥とはしません）：`session_id` が合う原本と、frontmatter のない無関係なファイルが並ぶと、`ambiguous` になります。修正前は、合う方に決まっていました。安全側に倒した結果で、I4 には反しません。
- **前提「根を渡さなければ、その限界を必ず知らせる」**：rag のページでは崩れたままです。既定の兄弟の `raw/` の中にあるハードリンクの PDF は、根なしでは `resolved`（外の原本）になり、`parents_unchecked` は 0 件でした（実測）。外の原本の分岐（`wiki_raw.py:263-274`）は、知らせを付けずに `continue` します。外の原本の例外は作者が承認した規範ですが、「守る木の外か」を根なしで決めたことは、どこにも出ません。

## 見落としと軽微な問題

- **軽微（推論）：訂正の根拠に使うソースの raw がリンクだと、定義の指摘は「raw が見つからない」になる。** 実測では、根拠のソースのハードリンクは `raw_warnings` に `link` として出るだけで、findings には出ませんでした。`other_raw_texts` は `paths_by_page` から `resolved` だけを集めます（`wiki_captions.py:1186-1196`）。そのため、その根拠を使う定義には、`check_definition` が「根拠のソース `slug` の raw が見つからない（同じ raw は使えない）」を返します（950-952 行）。取り込みは止まりますが、止める指摘の文面が拒否を「ない」と言い換えています（I4）。対応の記録の「使う時点で検査する」は、検査ではなく除外になっています。
- **軽微（実測）：ページの `url:` が配列だと、合う原本も `missing` になる。** `meta["url"] not in (rm.get("url"), ...)` は、配列を文字と比べます（`wiki_raw.py:303`）。`url: ["https://e/a"]` で、raw の `url` が同じ値でも `missing` でした。取り込みの手順は配列を書かないので、度合いは C です。
- **軽微（実測）：明示的に違う身元やハッシュの候補を、ファイルがあるのに `missing_raw` として出し、区別する欄がない。** `url` の末尾の `/` だけが違う raw は `missing` になり、lint の項目には `raw` と `absolute` しかありません。不一致は規範どおりですが、利用者には「ファイルがない」と「別の版がある」を区別できません。
- **軽微（文書）：`raw_outside` の説明がない。** `commands/lint.md` の 2a に `raw_outside` がありません（`lint-workflow.md` には 1 か所あります）。
- **軽微（実測）：`wiki_root` を渡さない lint で、件数と一覧が食い違う。** `LintPages` の文脈で raw を解いた結果、raw のリンクは `findings["links"]` に入ります。一方、`summary.links` は `wiki_root is None` のときに `None` のままです（`wiki_lint.py:764`）。一覧に項目があるのに、件数は「未検査」になります。CLI と MCP には影響がありません。
- **推測（未実測）：FileIdInfo を返さないファイルシステムで、保存が必ず失敗する。** 外の原本は `_identity` を外しましたが、外でない候補は候補が 1 つでも `_identity` を呼びます（306 行）。raw の根が exFAT や FAT にあると、セッションの保存直後の検査は NoFileId から `unknown` になり、毎回 `Fail` するはずです。

## 検証した事実

- **試験**：`tests/wiki/test_raw_links.py`、`test_wiki_youtube.py`、`test_wiki_session.py` を合わせて流し、190 件が成功、skip 1 件でした（Python 3.14.6、Windows）。依頼元の「105 件、skip 1」は、この一部と見て一致とします。
- **実際の wiki**：`missing_raw` が 0 件に戻ったことと一致しました。`raw_version_unverified` は 59 件、`raw_paths_unchecked` は 47 件で、依頼元の報告と同じです。
- **`outside`**：lint は `raw_outside` に出し、summary にも件数が載ります（第1回の軽微は閉鎖）。
- **`wiki_root` のない `lint()`**：ない raw を `missing_raw=1` と数え、手作りの配列では `raw_*` の件数が `null` になります（第1回の軽微は閉鎖）。
- **`_raw_meta`**：本文が水平線で始まる原本は `{}` を返し、lint は `unknown` を出しません（閉鎖）。
- **`..` を含む CLI の引数**：`wiki_lint.py ..` では raw が `unknown` になりますが、`caption_corrections` は 0 になりました。動画でないページの不確かさは、止める指摘から外れています。
- **セッションの保存直後の検査**：`resolved` 以外で止まり、`raw_sha256` を渡すので、別の版を誤って解くことはありません（`wiki_session.py:1707-1711` を読んで一致）。

## 崩せなかった点

- 身元の判定の三値化。合わないと明示されたものだけを捨て、欄がないものとバイナリは未確認のまま残します。
- verify が最初に読む raw のリンクは、`parse_raw` より前に拒みます。
- 動画でないページの曖昧さとリンクは `raw_warnings` に残り、取り込みは止まりません。それでも、利用者への知らせは失われません。
- 外の原本の識別子を求めないことで、外の原本の結果は変わりませんでした（コードと既存の試験で確かめました）。
- 第1回で確かめた、リンクを先に判定する順番、途中の `..` の拒否、`refused_link` の scope の除外は、今回の修正でも崩れていません。

---
使用した MCP サーバー: なし
使用した Agent Skills: なし

推奨のモデルとエフォート：このレビューは Opus / high。残る軽微の直し（根拠のソースの拒否の文面、配列の `url`、`..` の根を保存の前に拒むこと）は Sonnet / medium で足ります。
