## 判定

**条件付きで採用可**。リンクの検査の順番と、拒否をハッシュの不一致に落とさない作りは、攻撃しても崩れませんでした。ただし、身元の照合が既存の raw を `missing` と誤って報告します。これは実際の wiki で起きた退行で、旧版の 0 件が新版で 2 件になりました。また、字幕の検査が、関係のない source ページの raw の不確かさで YouTube の取り込みを止めます。この 2 件を直すまでは採用できません。確信度は中です。

## 致命的・重大な欠陥

### 1. 重大（度合い B、実測）：身元の欄がない raw を「不一致」とみなし、ある原本を `missing` にする

- **主張**：`url:` か `session_id:` を持ち、`raw_sha256:` がないページで、raw の frontmatter に `url` が無いと、候補を捨てます（`info-hive-wiki/skills/info-hive/scripts/wiki_raw.py:295-301`）。結果は `missing` で、lint の `missing_raw` に出ます。規範（設計書の「身元と版で確かめる」）は「合わない候補を捨てる」です。身元の欄がない raw は「合わない」ではなく「確かめられない」なので、`version_unverified` 付きの resolved か unknown にすべきで、`missing` は I4 に反します。
- **同じ状況が 3 通りに割れる**（実測。`%TEMP%\rv29probe\probe.py` の配置 1）：

  | raw の形 | 結果 |
  | --- | --- |
  | frontmatter のないファイル | `missing` |
  | ディレクトリ（身元を照らさない。295 行の `S_ISREG`） | `resolved` |
  | バイナリ（`_raw_meta` が UnicodeDecodeError） | `unknown` |
  | `url` の綴りが末尾の `/` だけ違う | `missing` |

- **実際の wiki での退行**（実測）：親リポジトリの `wiki/` に、旧版（HEAD を `git archive` で取り出したもの）と新版の `wiki_lint.py --json` をかけました。`missing_raw` は 0 件から 2 件に増えました。2 件とも原本はあります。
  - `sources/playwrightの取り込みとログイン状態の利用-wiki-0.30.0.md`。`raw/playwright….md` があり、frontmatter はありません。
  - `sources/翻訳を省略した取り込みの完了の防止-wiki-0.31.1.md`。`docs/agent-runs/2026-11-17-wiki-ingest-translation/summary.md` があります。

  ページの `url:` はリリースの URL で、出典を示すために書いたものです。同じページから `url` だけを除くと、`resolved`（`version_unverified=True`）になりました（probe2 の 4）。原因が `url` の照合だと実測で確かめています。
- **影響**：lint は、ある原本を「ない」と報告します。利用者が `raw:` を書き換える方向へ誘導されます。

### 2. 重大（度合い C。出力は実測、取り込みが止まるのは文書とコードからの推論）：字幕の検査が、動画でないページの raw の不確かさで YouTube の取り込みを止める

- **主張**：`check_pages` は、すべてのページで raw を解きます（`wiki_captions.py:1123-1132`）。`link`、`unknown`、`ambiguous` のどれかなら、動画でないページにも `unreadable_raw` を出します。
- **実測**（probe の 5）：`W/raw/n.md` と `W/../raw/n.md` に別の内容を置き、動画でない source ページ 1 枚から `raw: "raw/n.md"` を指しました。`check_wiki` は `('sources/n.md', 'unreadable_raw', 'raw/n.md: 別の実体の raw が複数ある')` を返しました。
- **推論**：`wiki_youtube.py:640` は、`findings` があると終了コード 1 を返します。`commands/ingest.md:35`（V8）は「`findings` があれば…通るまでユーザーに承認を求めない」と定めています。曖昧な `raw:` は自動で直さない規則（作者の決定の 8、9）なので、利用者が無関係なページの `raw:` を直すまで、どの動画も取り込めません。ADR の I5 が書き込みを止めるのは、その raw に依存する書き込みだけです。ここでは依存のないページまで止まります。
- **重なり**：同じ不確かさは lint でも `raw_unknown`、`raw_ambiguous`、`links` に出ます。`caption_corrections` にも出るので、二重に数えられます。

### 3. 重大（度合い D。検査が知らせを落とすのは実測、verify が読むのはコードからの推論）：`wiki_youtube verify` は raw の根を持つのに渡さず、途中のジャンクションを黙って通る

- **主張**：`wiki_youtube.py:626` は `check_wiki(wiki, overlay, only_raw=...)` を呼びますが、`args.raw_root` があるのに `raw_roots` も `wiki_root_given` も渡しません。さらに `check_pages` は、`parents_unchecked` を捨てます（`wiki_captions.py:1129-1132`。`resolved` ならそのまま `paths_by_page` に入れます）。
- **実測**（probe2 の 9）：`raw/sub` を外のディレクトリへのジャンクションにし、`raw: "raw/sub/v.md"` を置きました。根を渡さないと、`resolve_raw` は `resolved` を返し、`parents_unchecked` は 1 件、`check_wiki` の指摘は 0 件でした。根を渡すと `unreadable_raw` になりました。つまり verify の経路では、リンクを通った中身を、何も知らせずに読みます（I2）。
- **推論**：`cmd_verify` は、`raw_root / slug.md` を `read_text` で直接読みます（`wiki_youtube.py:617-621`）。共通の境界を通りません。依頼が範囲に含めた「今回接続した字幕検査の迂回」に当たります。

## 崩れる前提

- **前提「`url:` があれば、raw は取得器が書いた Web の raw である」**：手で保存した raw や作業記録など、出典の URL を書いただけのページで崩れます。この repo の wiki では 60 枚中 2 枚でした（欠陥 1）。
- **前提「字幕の検査に出す指摘は、動画の要約に関わる」**：`unreadable_raw` を全ページに広げたことで崩れました（欠陥 2）。
- **前提「呼ぶ側は raw の根を渡す」**：MCP の `raw_root` は省略でき、`wiki_youtube` は渡していません。根がないと、次のように扱いが変わります。
  - 既定の兄弟の `raw/` の中にある rag の PDF は、外の原本とみなされます（`wiki_raw.py:260`）。リンクの検査をせず、`parents_unchecked` にも出ません。probe の 3 で実測しました。ハードリンクの PDF が、根なしでは `resolved`（外の原本）、根ありでは `link` になります。
  - 途中の隠しディレクトリは記事として読まれます。根がないと `relative=(p.name,)` になるためです（257 行）。probe の 4 で実測しました。`raw/.trash/old.md` が根なしでは `resolved`、根ありでは `outside` になります。
- **前提「`--raw-root` を 1 つ渡せば、健全な wiki は知らせなしになる」**：崩れます。根を渡しても、`raw_paths_unchecked` が 47 件、`raw_version_unverified` が 57 件残りました（実測）。`docs/` の raw は 1 つの根の下に入らず、CLI と MCP は根を 1 つしか受けません。`render_text` は「問題は見つからなかった」を出さなくなります（`wiki_lint.py:856`）。これは分担（複数の根の記録は段階 3）のとおりですが、段階 2 だけでは、知らせが常に出て本当のリンクを埋もれさせます。
- **前提「raw の根は wiki の根より内側か、兄弟にある」**（推測、未実測）：raw の根が wiki の根の祖先だと、起点に raw の根が選ばれます（255 行。raw の根を優先）。その結果、wiki の根そのものにリンクの判定が当たりえます。規範の「起点は raw の根、次に wiki の根」どおりの結果ですが、「根と祖先のリンクは許す」と食い違います。

## 見落としと軽微な問題

- **軽微（C、実測）：lint が `outside` をどこにも出さない。** `wiki_lint.py:635-655` の分岐に `outside` がありません。probe2 の 3 では、`raw: "raw/.old/a.md"` が、どの欄にも summary にも出ませんでした。旧版は、ないファイルなら `missing_raw` に出していました。`excluded` は存在を確かめる前に決まるので、ない隠しパスは黙って消えます（I4）。
- **軽微（実測）：`wiki_root` なしの `lint()` が `missing_raw` を数えなくなった。** `collect_pages` から `missing_raw` を除いたので、401 行の else の分岐は常に空です。probe2 の 8 では、ない raw があっても `missing_raw` は 0 でした（`wiki_root` を渡すと 1）。新しい `raw_*` の集計も、未検査なのに `None` でなく `0` を返します（749-752 行）。CLI と MCP は `wiki_root` を渡すので、利用者への影響はありません。呼ぶのは `test_browse.py:79`、`eval/scripts/*` などです。
- **軽微（実測）：`missing_raw()` が `missing` しか返さない。** `wiki_session.py:1708` の書いた直後の検査は、`ambiguous` と `link`（ハードリンク）を素通りさせます（probe2 の 7）。そのあと `make_read_only` が共有の inode に当たりえます。書き手は後続段階の範囲ですが、関数の契約が狭まったことは、呼ぶ側から見えません。
- **軽微（C、実測）：本文が水平線の `---` で始まり、閉じない raw。** `url:` のあるページでは、`_raw_meta` が ValueError を出して `unknown` になります。lint は落ちません（probe2 の 6b）。
- **軽微（推測）：外の原本でも `_identity` を呼ぶ。** 外の原本は候補が 1 つなのに、`_identity` で `win_file_id` を呼びます（302 行）。FileIdInfo を返さないファイルシステム（exFAT や一部の SMB）では NoFileId になり、rag のすべてのページが `unknown` になりえます。未実測です。
- **軽微（D、コードからの推論）：大きな木を毎回たどる。** 根なしで、絶対パスのディレクトリ（`raw: C:/` など）を指す rag でない `raw:` があると、`_inspect` が lint のたびに木全体をたどります。
- **軽微：知らせの綴りが揃っていない。** `links` に入る raw の項目の `path` は OS の絶対パスで、wiki の項目は相対パスです。

## 検証した事実

- **`tests/wiki/test_raw_links.py`**：31 件が通り、skip は 1 件で、報告と一致します。skip は `test_directory_hash_with_unicode_collision_and_newlines`（制御文字の名前）です。この機械ではファイルの symlink を作れたので、symlink の試験は skip されずに走りました。
- **親の差分**：`wiki-walk.yml` は新しい試験を paths と実行の両方に足しています。`test_mcp_server.py` は、MCP の `raw_root` と CLI の `--raw-root` が同じ結果を返し、ハードリンクを `links_raw=1` と数えることを確かめています。`test_wiki_links.py` は `_digest` と `_raw_meta` を RAW として一覧に載せています。いずれも一致しました。
- **旧版と新版の lint**（親の `wiki/`）：`missing_raw` は 0 件から 2 件、`links_raw` は None から 0 に変わりました。`raw_version_unverified` は 57 件、`raw_paths_unchecked` は根なしで 60 件、`--raw-root raw` で 47 件です。
- **YouTube の要約ページ**：`url` は raw の `url` を写す決まりです（`ingest-workflow.md:217`、`wiki_youtube.py:303`）。動画のページは欠陥 1 の対象にならないと推論しました。未実測です。
- **`.. ` の綴り**：Windows の `abspath` は、末尾に空白の付いた `.. ` で親に抜けません（`C:\a\b\c\.. ` は `C:\a\b\c\` になります）。
- **`relative_to` の大文字と小文字**：Python 3.14 の `PureWindowsPath.relative_to` は大文字と小文字を区別しません。`within` との食い違いで落ちることはありません。
- **`..` を含む引数**：CLI の `wiki_lint.py ..` と `--raw-root ../raw` では、すべての raw が `unknown` になり、`unreadable_raw` も出ます。黙りはせず、規範どおりです。

## 崩せなかった点

- 候補のどれかがリンクなら、ハッシュが合っても合わなくても `link` にし、中身を読む前に止まります（280 行。既存の試験と probe の 3 で確かめました）。
- 途中の `..` と NUL は、I/O の前に `unknown` になります。
- `refused_link` が `scope: "raw"` を除くので、raw の拒否が wiki の同名のページのリンク切れを消しません。
- `_raw_meta` の例外は、試した入力ではどれも `OSError`、`UnicodeError`、`ValueError` に収まり、lint 全体は落ちません。
- 根の綴りと解決した根の両方を基準にし、同じ実体を 1 つにまとめます（probe の 6 と既存の試験）。

---
使用した MCP サーバー: なし
使用した Agent Skills: なし

推奨のモデルとエフォート：このレビューは Opus / high。次の作業（欠陥 1〜3 を、身元の照合の三値化と、字幕の検査の指摘の範囲の決め直しとして、構造から直すこと）も Opus / high が適しています。
