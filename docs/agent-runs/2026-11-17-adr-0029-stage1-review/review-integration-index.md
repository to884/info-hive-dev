## 判定

**条件付きで採用可**（確信度: 高）

閲覧の側（`Core.resolve`、索引の行、描いた HTML）は、意図どおりに動きます。スラッグで照合する規則と、ページを明示したパスの照合も後退していません。

ただし、`refused_link` は lint と出典の判定も共用しています。そのため lint では、もともと誤りだった参照が、索引がリンクになった途端に指摘されなくなります。本文の `[[indexes/topic]]` と `sources: ["[[indexes/topic]]"]` です。この後退は軽微です。

## 致命的・重大な欠陥

なし

## 崩れる前提

- **前提: パスで照合して `refused` になる参照は、リンクでなければ解決できたはずである**
  - 崩れる条件: lint の解決の規則が、そもそも索引を行き先として認めない場合です。
  - lint の `by_path` はページだけで作ります（`resolve_available` から `resolve_link`）。`classify_source_ref` も、ページの索引（`link_candidates`）だけを引きます。そのため `indexes/topic.md` が普通のファイルでも、本文の `[[indexes/topic]]` はリンク切れになり、`sources: ["[[indexes/topic]]"]` は `missing` になります。
  - 今回の変更で、パスで照合する条件が `is_article_path` に広がり、`indexes/*.md` を含むようになりました。索引がハードリンクになると、2 つの指摘が消えて `links` の 1 件だけが残ります。
  - その結果、「リンクでなくても誤りの参照」が、リンクのときだけ黙ります。消える指摘は、リンクを直したあとで初めて現れます。

## 見落としと軽微な問題

1. **軽微: lint のリンク切れと出典の指摘が、索引の拒否で消える**（再現済み）
   - 手順（プローブは `index_ref_probe.py`、Windows、Python 3.12）:
     1. `concepts/a.md` に、本文の `[[indexes/topic]]` と `sources: ["[[indexes/topic]]"]` を置く。
     2. `indexes/topic.md` が普通のファイルのまま、lint を流す。
     3. `indexes/topic.md` をハードリンクにして、もう一度 lint を流す。
   - 普通のファイルのとき:
     - `broken_links` に `{'from': 'a', 'to': 'indexes/topic'}` が出る。
     - `unresolved_sources` に `{'source': '[[indexes/topic]]', 'reason': 'missing'}` が出る。
   - ハードリンクのとき:
     - `links` に `[{'path': 'indexes/topic.md', 'kind': 'hardlink'}]` が出る。
     - `broken_links` と `unresolved_sources` は空になる。
   - 根拠: `wiki_pages.py:1101-1102` の `kind == "path"` のときの `is_article_path` です。lint（`wiki_lint.py` の `resolve_available` とリンク切れの判定）と `classify_source_ref` が、この関数を共用しています。
   - グラフの `link_target` は、もともと索引を行き先にしないので、結果は変わりません（辺を作らないまま）。
2. **軽微（推測）: 最上位の記事は、パスの形で照合されない**
   - `link_lookup` は、`/` を含む行き先だけを `path` にします。そのため、最上位の `index.md`、`log.md`、`SCHEMA.md` は、`is_article_path` に含まれても、この分岐では照合されません。
   - `[[index]]` はスラッグの形になり、`is_page_path` が偽なので `None` を返します。従来と同じで後退ではありませんが、`is_article_path` に替えたことで最上位の記事も含まれるように読める点は、実際の挙動と食い違います。

## 検証した事実

- **差分:** 差分は `wiki_pages.py:1101-1102` の条件の 1 か所です（`fb4d6c4`）。パスの形は `is_article_path`、スラッグの形は従来どおり `is_page_path` を使います。一致。
- **ページの照合:** `is_article_path` は、`.` で始まる要素を除いたうえで、最上位の記事、`indexes/` の下、`is_page_path` を真にします。`is_page_path` を含むので、ページをパスで照合する既存の規則は変わりません。一致。
- **スラッグの照合:** スラッグの形の分岐は変わらず、裸の `[[topic]]` は索引の記事に結び付きません。一致。
- **新しい試験:** `test_refused_index_article_matches_an_explicit_path_only` は、手元で OK でした。
- **lint の挙動:** 本文と `sources:` の `[[indexes/topic]]` を、lint は索引が普通のファイルでも誤りとして挙げます。上のプローブで確認しました。

## 崩せなかった点

- スラッグの照合は、ページに限ったままです（`[[topic]]` は `indexes/topic.md` を指さない）。
- ページを明示したパスの照合と、拒否した道の下を要素の境界で照合する部分は、どちらも変わっていません。
- 閲覧の索引で、明示した `[[indexes/topic|Topic]]` の拒否が、「リンクなので読まない」として表示されます。依頼元の試験と、コードの経路（`_nav_item` から `resolve`）で一致しました。

---
使用した MCP サーバー: なし
使用した Agent Skills: なし
次の作業（lint 側の判定の範囲をそろえるかの判断）に向くモデルとエフォート: Opus、medium
