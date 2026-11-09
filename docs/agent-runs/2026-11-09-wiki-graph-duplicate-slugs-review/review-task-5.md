4 回目の指摘を受けて直した。差分は同じく 64acc43 からの全体（未コミット）。応答は日本語で、同じ形式で書く。

1. 重大（contradicts の循環参照で ID が変わる）: 項目の中身全体ではなく、VARIANT_FIELDS（confidence、status、valid_from、valid_to、notes、raw_ref）だけを ID に入れる（relationship_variant_key）。contradicts、supersedes、未知の拡張の欄は入れない。番号は、ID に入る欄（述語、目的語、出典、証拠、VARIANT_FIELDS）がすべて同じ項目の中で、ページで出てきた順に数える。
2. 軽微（入れ子の辞書のキーで TypeError）: _stable_json で、sort_keys が使えないときは並べ替えずに直列化する。拡張の欄はそもそも ID に入れない。
3. 軽微（「必ず 1 本」に例外がない）: CHANGELOG と手順書に、predicate と object があり、目的語が曖昧でない項目に限ることを書いた。
4. 試験を足した: contradicts で互いを指しても ID が変わらない、入れ子の拡張の欄で止まらない、述語の違う項目の並べ替えで ID が変わらない（試験は全体で 25 件）。

直した点が正しいか、直したことで新しく崩れたものがないかを確かめてほしい。特に、VARIANT_FIELDS だけが違う項目と、contradicts だけが違う項目の扱い（後者は番号で分かれるので、並べ替えると ID が入れ替わる）が (a) の性質と ID の安定性の両方に照らして妥当か。
