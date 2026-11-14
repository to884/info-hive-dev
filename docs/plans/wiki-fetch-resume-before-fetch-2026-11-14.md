# 途中の取り込みは、取得の前に再開する（wiki_fetch.py）

- 状態: 5 版（2026-11-14）。1 版は設計レビュー、2〜4 版は実装レビューで却下（下の「改訂の履歴」）。5 版はレビューにかけていない
- 対象: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`、`wiki_rawcheck.py`、`commands/ingest.md`、`references/ingest-workflow.md`、`CHANGELOG.md` の `[Unreleased]`
- 試験: `tests/wiki/test_wiki_web_check.py`
- 前提の設計: [wiki-web-ingest-check-2026-11-13.md](wiki-web-ingest-check-2026-11-13.md)（作業用の写しと、写しがそろった印を raw のあとに置く順）

## 問題

`--html-file` と `--page-url` で取得したページ（`source_sha256_of: "dom"`）の取り込みを途中でやめ、あとで URL だけで `wiki_fetch.py` を呼ぶと、作業用の写し（`<WIKI_ROOT>/.wiki-cache/ingest/<スラッグ>/`）がそろっていても、再開できない。

- `build` は先にページを取得し、取得した HTML の SHA-256 を raw の `source_sha256`（保存した DOM の SHA-256）と比べる。両者は別のバイト列なので、ほぼ必ず違い、写しを見る前に終了コード 3（`existing_differs`）で止まる。
- ネットにつながらなければ、取得の失敗（終了コード 2）で止まる。
- URL で取得したページでも、取得のたびにバイト列が変わるページ（時刻やトークンを埋め込むページ）は同じに止まる。

0.14.0 の `main` で再現する（`FetchCase.build(html_page(...), html_file=<保存した HTML>, page_url=PAGE_URL)` のあと、`html_file` なしで `wiki_fetch.build(args())` を呼ぶと、終了コード 3 と `error: existing_differs`）。

## 原因

「途中の取り込みを続けられるか」を、「取り直した原文が raw と同じか」の答えに載せている。前者は、作業用の写しと raw の状態だけで決まる問いで、ページをもう一度取る必要はない。後者は、原文を取り直せて、同じバイト列が返るときにしか成り立たない。DOM から取ったページや、取得のたびに変わるページでは、後者がいつも偽になるので、前者に答えられない。

再開を写しだけで決めると、写しが続きの手順に渡す内容が足りるか、写しのファイルどうしが同じ取得のものかが問題になる（1 版と 2 版のレビューで分かった）。

- 再開の出力は、最後に終えた段の出力を返していなかった。取得のあと（`fetched`）では、本文が空か短いという警告（W3 で見る）を返さないので、取得した直後に止まった取り込みを続けると、本文を取れたかを確かめる段を飛ばす。削除を固定したあと（`frozen`）では、`freeze` の報告（消した行と、消した文字の割合の警告。W5 で読む）を返さないので、`freeze` の直後に止まると、本文を消しすぎていないかを確かめる段を飛ばす。今の取得後の再開の枝も同じである。
- 写しのファイル（`fetched.md`、`fetch.json`、`cleaned.md`）と raw が 1 つの取得の組であることを、書く順（`fetch.json` を最後に置く、`cleaned.md` を最後に置く）だけに頼っていた。raw と `fetched.md` は frontmatter で照らすが、`fetch.json` と `cleaned.md` は照らしていない。取得元とハッシュ（`url`、`final_url`、`source_sha256`）で照らしても、同じ URL の同じ原文を別の設定（`--keep-noise` など）で取った記録は見分けられない。取得の前に再開すると、出力の値をすべて写しから取るので、ファイルの一部だけが別の取得のもの（一部だけを戻したバックアップなど）なら、誤った値を返したり、照らしていない組で続けたりする。

## 前提（守る範囲）

保証するのは整合である。写しのファイルの組（`fetched.md`、`fetch.json`、あれば `cleaned.md`）と raw が、1 つの取得と、その取得のあとの `freeze` が残しうる組のときだけ続ける。

- どこで止まっても（書く順）、この組でなければ続けない。
- 写しのファイルの一部を、丸ごと別の取得のものに置き換えたとき（一部だけを戻したバックアップなど）も、この組でなければ続けない。

どの取得がその組を残したか（取得の出自）は保証しない。ファイルからは決められないからである。別の設定で取っても `fetched.md` が同じバイト列になれば、写しの組は、どちらの取得が残したものとしても正しい（どちらの `fetch.json` も、その本文を作った取得の正しい記録である）。別の取得の `cleaned.md` でも、今の `fetched.md` のあとの `freeze` が通す内容なら、同じく正しい組である。

作業用の写しは、`wiki_fetch.py` と `wiki_rawcheck.py freeze` だけが書く。ファイルの中を手で書き換えたものは、前提の外である（形の違う `fetch.json` で例外にならないようにはする）。

## 記録に何が残っているか

- 0.14.0 の `fetch.json` は `build` の出力（`result`）そのもので、`url`、`final_url`、`source_sha256`、`needs_translation`、`images`、`removed_by_rule`、`title`、`source_lang`、`ja_ratio` などがある。`source_sha256_of` と、`--html-file` を使ったか（ファイルのパス）は残っていない。
- `fetched.md` と raw の frontmatter には、`url`、`source_sha256`、`source_sha256_of`（`dom` か `html`）、`final_url`（`--page-url` が `url` と違うとき）が残る。
- 再開の判定は、どちらの取得だったかに依らない（下の設計）。ただし続きの手順（W3）は、本文が短いときにブラウザで取り直すかを、どちらの取得だったかで決める。DOM の取得を続けて、本文が短いという警告を読み直すと、ブラウザでの取り直しに戻ってしまう。そこで出力（と `fetch.json`）に `source_sha256_of` を足し、続けるときにも返す。

## 設計

### 再開の判定を取得の前に置く

`build` の、保存先とスラッグの検査のすぐあと、取得（と `--html-file` の読み込み）の前に、次のすべてを満たすかを見る。

1. `--wiki` がある（`build` は `getattr(args, "wiki", None)` で読む）。
2. `--force` がない。
3. `--html-file` がない。
4. raw（`<RAW_ROOT>/<スラッグ>.md`）がある。
5. 作業用の写しがそろい（`work_dir_complete`）、raw の frontmatter が写しの `fetched.md` と同じ（`work_dir_matches_raw`。`translated_by` を除く）。
6. `fetch.json` が取得器の書いた形である。続けるときに使うキーがその型である（`url`、`final_url`、`source_sha256`、`fetched_sha256`、`source_sha256_of` が文字列、`needs_translation` が真偽値、`images` が `path` を文字列で持つ辞書のリスト、`removed_by_rule` が `rule` と `text` を文字列で持つ辞書のリスト、`warnings` が文字列のリスト）。
7. `fetch.json` が `fetched.md` と内容で結ばれている。取得器は、`fetched.md` に書くバイト列の SHA-256 を `fetched_sha256` として出力と `fetch.json` に記録する。`fetch.json` の `fetched_sha256` が、`fetched.md` のバイト列（`read_bytes`。改行を変えない）の SHA-256 と同じでなければ続けない。`fetched.md` を書くのは `build` の 1 か所だけで、あとで書き換えるものはない。
8. `fetch.json` の `url`、`final_url`、`source_sha256` が、`fetched.md` の frontmatter の `url`、`final_url`（キーがなければ `url`。あれば文字列でなければならない）、`source_sha256` と同じ（5 と合わせて、raw とも同じになる）。
9. `cleaned.md` があれば、`freeze` の通す内容である。frontmatter が `fetched.md` と同じで、本文が `fetched.md` から消すことだけで作れる（`freeze` の判定のうち、画像のファイルの検査を除いたもの。`deletion_errors` に切り出し、`freeze` と共に使う）。画像のファイルは raw の側にあり、`freeze` のあとの段で変わりうるので見ない。これは、`frozen` で返す報告（`deletion_report`）の前提でもある。
10. `fetch.json` の `url` が、今回の URL（位置引数）と文字列として同じ。

9 は、ファイルの組が `freeze` の残しうるものかを、`freeze` と同じ条件で確かめる。ハッシュで `cleaned.md` を結ぶ（`removed.json` に記録する）方法は採らない。2 回目の `freeze` が `removed.json` と `cleaned.md` の名前の変更のあいだで止まった写しは、正しい組なのに、ハッシュでは続けられなくなるからである。9 の条件なら続けられる。

満たせば、ページを取得せずに、終了コード 0 で次を返す。前の取得の出力に、取得しなかったことと、どこまで進んだかと、最後に終えた段の出力を足したものである。

- `path`、`url`（今回の値）、`final_url`、`source_sha256`（`fetch.json` の値。8 で frontmatter と同じことを確かめてある）
- `unchanged: true`（何も書いていない）
- `fetch_skipped: true`（ページを取得しなかった。この形の出力にだけ付ける）
- `work_dir: true`、`work_stage`
- 前の取得の出力のうち、取得した内容から作ったものすべて（`RESUME_KEYS`）: `source_sha256_of`、`title`、`source_lang`、`encoding`、`content_root`、`ja_ratio`、`needs_translation`、`chars`、`images`、`dropped_images`、`removed_by_rule`、`warnings`
- `frozen` なら、`freeze` の報告（`freeze`: `removed_lines`、`shortened_lines`、`warnings`）。`fetched.md` と固定した内容（`cleaned.md`。`freeze` が通したときの raw）から、`freeze` と同じ関数（`deletion_report`）で作り直す。`removed.json` は読まない（結ぶファイルを増やさない）。`images` は削除のあとに残った画像だけにする。`freeze` の警告は、取得の警告（`warnings`）と混ぜない。

今の「原文が同じ」の枝も、同じ判定（5〜9）と同じ値を返す。

### 0.14.0 が書いた写し

0.14.0 の `fetch.json` には `fetched_sha256` と `source_sha256_of` がない。この写しでは、どちらの枝でも続けない（6 を満たさない）。

4 版までは、取得して原文が同じなら 0.14.0 と同じに続けていた。しかし、7 を照らせない記録は、同じ原文を別の設定（`--keep-noise` など）で取った記録を丸ごと戻したものと見分けられず、「前提」の整合の保証と両立しない（4 版の実装レビューの重大 1）。どの取得かも分からないので、今回の入力の方法で `source_sha256_of` を返すと、写しの frontmatter と逆の値になる（同じく重大 2）。保証を条件なしに成り立たせるため、互換を捨てる。0.14.0 で始めて途中で止めた取り込みは、`"work_dir": false` になるので、`--force` で取り直す（それまでの削除や訳は消える）。0.14.0 は 2026-11-14 に `main` に入ったばかりで、途中の取り込みはほとんどないと見込む。

満たさなければ、今の動き（取得して比べる）を変えない。写しがない、そろわない、raw と別の取得の写し、別の URL、`--force`、`--html-file` のときである。

### `--html-file` を判定から外す理由

`--html-file` は、呼び出し側がこの内容で取ると明示した入力である。W3 では、URL での取得で本文が空だったとき（写しはそろう）、保存した DOM を渡して W2 をやり直す。これを再開に吸い込むと、空の本文の写しで続けてしまう。渡した内容を読んで比べる今の動き（同じなら再開、違えば終了コード 3）を残す。

### 再開の値を 1 か所で組み立てる

`wiki_rawcheck.py` に、次の 2 つを足し、取得の前の再開と、今の「原文が同じ」の枝の両方から使う。

- `resumable_fetch(wiki, slug, raw_path) -> dict | None`: 上の 5〜9 を満たせば `fetch.json` の中身を返し、満たさなければ `None`。
- `resume_fields(wiki, slug, saved) -> dict`: `work_stage` と、最後に終えた段の出力。今の `build` の枝にある組み立て（`frozen` なら `cleaned.md` から残った画像を選び直す）を移す。
- `deletion_errors(src_fm, src_body, out_fm, out_body, out_tree) -> list`: `freeze` の判定のうち、画像のファイルの検査を除いたもの（frontmatter、参照の定義、消すことだけか、題名）。`freeze` と `resumable_fetch`（9）の両方が使う。`freeze` の誤りの順と文は変えない。
- `deletion_report(fetch, src_body, out_body, out_tree, offset) -> dict`: `freeze` の報告（消した行、一部を消した行、消した文字の割合の警告、残った画像）。`freeze` と `resume_fields` の両方が使う。

今の「原文が同じ」の枝も、`fetch.json` の形が違うときに例外で落ちず、`work_dir: false` を返すようになる。

### 文字の出力

`fetch_skipped` のときは、「内容は前回と同じ」とは書かない（比べていない）。作業用の写しから続けること、ページが更新されたかは見ていないこと、取り直すなら `--force`（途中の作業を捨て、写しと raw の両方を作り直す）を書く。続けるとき（取得後の枝も）は、段と、最後に終えた段の出力（`fetched` なら規則で消したものと注意、`frozen` なら消した行、一部を消した行、警告、補足を書く画像）を並べる。

### 手順書

- `commands/ingest.md` の W2: `"fetch_skipped": true` の意味を 1 文で足す。`"work_stage": "fetched"` なら、W4 ではなく W3（出力の `warnings` と `removed_by_rule` を見る段）から続ける。出力のそれらは前の取得のものである。`"work_stage": "frozen"` なら、出力の `freeze` を読んで W5 の確かめをしてから W6 に進む。
- `commands/ingest.md` の W3: ブラウザで保存した HTML で取り直すときに `--force` を付ける。今は付けていないので、URL での取得のあとの取り直しは、原文のハッシュが違って終了コード 3 になる（既存の詰まり）。再開が W3 を通るようになるので、ここで直す。0.15.0 の準備のブランチ（`references/web-raw.md`）も同じに直している。出力の `source_sha256_of` がもう `dom` なら、ブラウザでの取り直しを繰り返さずに、取り直すかをユーザーに聞く（`--force` の取り直しは、途中の作業を消す）。
- `references/ingest-workflow.md`: `source_sha256` を比べる段落、`--html-file` の段落と例のコマンド（`--force` を付ける）、途中で止まったあとの段落を、上に合わせる。

## 変わること（意図した変更）

- 途中の取り込み（写しがそろい、raw と一致する）があれば、ページが更新されていても終了コード 3 にならず、前の取得の写しから続ける。写しは `check --finish` で消えるまで残るので、取り込みを終えるまでは、URL だけの呼び直しでページの更新を知らせない。取り込んでいるのは写しを取った時点の内容であり、frontmatter の `fetched_at` がその時点を示す。更新を取り込むなら、取り込みを終えたあとで取り直すか、`--force` で取り直す。
- ネットにつながらなくても、途中の取り込みは続けられる。

## 変えないこと

- 写しがないとき（取り込みを終えた、写しを失った）は、今までどおり取得して比べる。DOM から取った raw を URL で取り直すと、バイト列が違うので終了コード 3 になる。比べる原文の種類（`source_sha256_of`）が違うのに「ページが更新された」と言う点は、この変更の範囲の外に残す（限界）。
- `--force`、`--html-file`、別の URL、raw と別の取得の写しのときの動き。
- 写しを書く順と、`fetch.json` の形（`fetched_sha256` を足すほかは）。PR to884/info-hive-wiki#54 が `build` の最後と `write_outputs` を直しているので、そこには触れない（`fetched_sha256` は、出力に `title` などを入れる所で足す）。
- バージョン（`plugin.json`）。CHANGELOG の `[Unreleased]` にだけ書く。

## 試験

`tests/wiki/test_wiki_web_check.py` に足す。

- 再現: DOM で取ったあと、URL だけで呼ぶと、終了コード 0、`fetch_skipped`、`work_stage: fetched`、取得を呼ばない（`stub.requested == []`）、`source_sha256` は DOM の値。直す前のコードでは終了コード 3 で落ちる。
- ネットにつながらない（取得が `FetchError` を投げる）ときも再開する。
- 削除を固定したあと（`frozen`）は、残った画像だけを返す。
- 対照（取得して比べる）: `--force`、`--html-file` に別の内容（終了コード 3）、別の URL、raw の frontmatter を書き換えた、写しを消した（DOM の raw は終了コード 3）。
- 文字の出力が「前回と同じ」と書かず、`--force` を案内する。
- 1 版のレビューの反例: 本文が短いという警告を、続けるときも返す（取得の前の再開と、`--html-file` に同じ内容を渡した枝の両方。文字の出力も）。`fetch.json` の `url`、`source_sha256`、`final_url` だけを別の値にすると、続けずに取得に進む。`fetch.json` が辞書でない、キーがない、続けるときに使うキーの型が違う（`images: null` に `cleaned.md` があるときなど）と、例外にならずに取得に進む。
- 2 版のレビューの反例: 同じページを、ふつうに取ったあと `--keep-noise --force` で取り、raw と `fetched.md` を前の取得のものに戻して `fetch.json` だけを残すと、続けずに取得に進む。`freeze` の直後に止まった取り込みを続けると、`freeze` と同じ報告（消した行、警告）を返す。frontmatter の `final_url` が文字列でなければ続けない。`fetched_sha256` のない記録（0.14.0）は、取得の前には続けず、取得して原文が同じなら続ける。返す値の検査は、実装の定数に頼らずにキーを書き並べる。
- 3 版のレビューの反例: 08:00 に取って `freeze` し、09:00 に別の原文で取り直してから、前の `cleaned.md` だけを戻すと、どちらの枝でも続けない。同じ秒の同じ原文を、規則を止めて取って `freeze` し、規則を使って取り直してから `cleaned.md` を戻したもの（frontmatter が同じで、本文で見分ける）も続けない。対照: 今の取得のあとの `freeze` が通す内容の `cleaned.md` なら、別の取得のものでも続ける（整合の定義）。2 回目の `freeze` が `cleaned.md` を置く前に止まった写しは、1 回目の `cleaned.md` で続ける。DOM の取得を続けると `source_sha256_of: "dom"` を返す。
- 4 版のレビューの反例: 0.14.0 の形の記録（`fetched_sha256` と `source_sha256_of` を除いたもの）は、取得のあとと削除を固定したあとのどちらでも、URL だけでも `--html-file` でも続けない。同じ原文を `--keep-noise` で取った 0.14.0 の記録を、ふつうに取り直した写しに丸ごと戻しても続けない。文字の出力は 0.14.0 の写しを続けないことと `--force` を示す。2 版の反例のうち 0.14.0 の記録を続けるとしたものは、この試験に置き換えた。

## 限界

- 写しがないとき（取り込みを終えた、写しを失った）に、DOM から取った raw を URL で取り直すと、比べる原文の種類（`source_sha256_of`）が違うのに「ページが更新された」として終了コード 3 になる。今の動きのまま残す。
- 同じ秒の取り直しなどで frontmatter が同じ別の版の raw に、本文だけを戻したものは、写しと raw の照合（frontmatter）では見分けられない（`work_dir_matches_raw` の注記のとおり、今からある限界）。続きの `freeze` と `check` が写しと照らすので、多くは止まる。
- 取得して原文を比べる枝（`--html-file`）は、`--page-url`（`final_url`）が写しと違っても、原文が同じなら写しで続ける（0.14.0 からの動き）。出力の `url` と `final_url` は今回の値で、写しの段と値は前の取得のものになる。この変更の範囲の外に残す。
- 0.14.0 で始めて途中で止めた取り込みは、続けられない（上の「0.14.0 が書いた写し」）。`--force` で取り直す。
- 取得の出自は保証しない（上の「前提」）。別の設定でも `fetched.md` が同じバイト列になる 2 つの取得は、写しの組からは見分けられず、どちらの `fetch.json` で続けても正しい組である。
- `check` は、今までどおり `cleaned.md` を照らさずに基準にする（`main` と同じ）。`wiki_fetch.py` で続けるときは 9 で確かめるが、`check` を直接呼んだときは確かめない。

## 改訂の履歴

- 1 版（2026-11-14）: Sol の設計レビュー（`docs/agent-runs/2026-11-14-wiki-fetch-resume/design-review-1.md`）で却下（確信度 高）。重大 2 件: 再開の出力が警告を返さず、本文を取れなかった取り込みを W3 を飛ばして続ける。`fetch.json` を `fetched.md` と照らさないので、`fetch.json` だけが別の取得のものなら誤った URL とハッシュを返す。軽微: 続けるときに使うキーの型を確かめていない（`images: null` で落ちる）、W3 の取り直しに `--force` がない。
- 2 版（2026-11-14）: 再開の出力を「前の取得の出力に、どこまで進んだかを足したもの」にし（警告を含む）、`fetched` なら W3 から続けることにした。`fetch.json` の取得元とハッシュを `fetched.md` の frontmatter と照らし、続けるときに使うキーの型を確かめることにした。W3 に `--force` を足した。実装のレビュー（`impl-review-1.md`）で却下（確信度 高）。重大 2 件: 同じ URL の同じ原文を別の設定で取った `fetch.json` は、取得元とハッシュで見分けられない。`freeze` の直後に止まると、`freeze` の報告を読む段を飛ばす（`frozen` の枝に今からある問題）。軽微: 取得後の枝の文字の出力が警告を並べない、frontmatter の `final_url` の型を見ない、試験が実装の定数に頼る。
- 3 版（2026-11-14）: 守る範囲（前提）を書いた。`fetch.json` と `fetched.md` を、`fetched.md` のバイト列のハッシュ（`fetched_sha256`）で結ぶことにした。0.14.0 の写しは取得の前には続けず、取得して原文が同じときだけ続ける。再開の出力を「最後に終えた段の出力」にし、`frozen` では `freeze` の報告を `freeze` と同じ関数で作り直して返し、W5 の確かめから続けることにした。文字の出力を、取得後の枝でもそろえた。実装のレビュー（`impl-review-2.md`）で却下（確信度 高）。重大 2 件: 別の取得の `cleaned.md` だけを戻した写しを照らさずに `frozen` で続ける。別の設定でも `fetched.md` が同じバイト列になる取得では、`fetch.json` を差し替えると前の取得の警告が消える。軽微: 試験がこの 2 つの混在を見ない、`ingest-workflow.md` の例のコマンドに `--force` がない。
- 4 版（2026-11-14）: 保証を、取得の出自ではなく整合（1 つの取得と、そのあとの `freeze` が残しうる組）と定めた。3 版の前提の「丸ごと別の取得のものに置き換えたとき、続けない」は出自の保証で、ファイルからは決められなかった。重大 2 はこの定義で欠陥でなくなる（写しの組は、もう一方の取得が残した組と同じである）。`cleaned.md` は、`freeze` と同じ条件（`deletion_errors`）で、今の `fetched.md` のあとの `freeze` が通す内容かを確かめる（9）。DOM の取得を続けたときに W3 がブラウザでの取り直しを繰り返さないよう、`source_sha256_of` を出力に足した。例のコマンドに `--force` を足した。並行していた PR（to884/info-hive-wiki#54）が `main` に入ったので、両方のブランチに `main` をマージした。実装のレビュー（`impl-review-3.md`）で却下（確信度 高）。重大 2 件はどちらも 0.14.0 の写しを続ける互換の経路のもの: `fetched_sha256` のない記録は `fetched.md` と結べないので、別の設定で取った 0.14.0 の記録を丸ごと戻すと、取得して原文が同じだからと続けてしまう。0.14.0 の記録には `source_sha256_of` がないので、今回の入力の方法で上書きし、写しと逆の値を返す。軽微: 試験の 0.14.0 の記録が実際の形でない、W2 が「途中の取り込みがあれば取得しない」と言い切っている（`--html-file` のときは取得して比べる）。
- 5 版（2026-11-14）: 0.14.0 の写しを続ける互換を捨てた（どちらの枝でも続けない）。`fetched_sha256` と `source_sha256_of` を、取得の記録の必須のキーにした（6）。保証が条件なしに成り立ち、重大 2 件は構造ごとなくなる。W2 の文を「URL だけで呼んだときに」に直し、`"work_dir": false` に 0.14.0 の写しを含めた。CHANGELOG に互換でない変更として書いた。この版はレビューにかけていない。
