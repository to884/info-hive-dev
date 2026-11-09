`x.md` と `x.MD` が同じページ識別子になることも確認しました。PoC では片方が上書きされます。また、静的出力先をサーバーの状態ディレクトリと同じ場所にできるため、世代の入れ替えが稼働中のロックのパスを動かす設計上の反例があります。これらは、新実装での実行確認と区別して報告します。
## 判定

**却下。確信度：高。** グラフ抽出に求める契約に、既存データと両立しない規則と、同時には満たせない条件がある。加えて、ページ識別子の衝突と、書き込み先の重複によって閲覧専用・サーバーの排他が崩れる入力が残っている。

以下は、現行関数で確認した結果と、未実装の設計から導いた反例を区別して記す。

## 致命的・重大な欠陥

**1.【重大】関係の目的語を `resolve_link()` で解決する契約が、既存のノード ID を受け付けない。**

既存スキーマでは、次のように目的語をノード ID で書く。

```yaml
graph:
  relationships:
    - predicate: uses
      object: concept:y
```

`concepts/y.md` のノードが `concept:y` であっても、現行 `wiki_pages.resolve_link("concept:y", ...)` の結果は `None` だった。同じ入力で `"concepts/y"` は `"y"` に解決された。現行のグラフ関数は、`object: concept:y` のエッジを生成する。

設計の契約 3 をそのまま適用すると、既存の正常な型付き関係が未解決として除かれる。ノード ID とページ参照を区別する規則、その変換に使う対応表が契約にない。

根拠：[設計 §3、契約3](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:54)、[既存スキーマの例](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md:31)、[`resolve_link()`](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:230)、[現在の型付きエッジ生成](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:336)。**結果：既存スキーマとの食い違いを、メモリ上の実行で確認。**

**2.【重大】`sources:` について、契約3と契約5を同時に満たせない。**

反例は次の3ページである。

```text
concepts/a.md            type: concept、sources: ["paper"]
sources/left/paper.md    type: source
sources/right/paper.md   type: source
```

現行 lint の実行結果は次のとおりだった。

```text
unresolved_sources: []
duplicate_slugs: paper の2ページ
```

この入力に対して、設計は同時に次を要求する。

- 契約3：同じスラッグが複数ある曖昧な参照なので、エッジを作らない。
- 契約5：`unresolved_sources` が空なので、`sources:` のどの値からもエッジを作る。

lint は曖昧性を `unresolved_sources` に含めていない。したがって、この条件式を抽出修正の合格条件にすると、実装は必ずどちらかに違反する。

根拠：[設計の契約3〜5](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:54)、[lint の重複検出](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:430)、[`sources:` の検査](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:547)。**結果：契約の矛盾を、現行 lint の実行結果で確認。**

**3.【重大】`.md` と `.MD` だけが違うページが、同じ識別子に潰れる。**

Linux では次の2ファイルを同時に置ける。

```text
concepts/x.md    本文「SECOND」
concepts/x.MD    本文「FIRST」
```

`wiki_pages` は両方をページとして認める。一方、設計の識別子生成では、両方が `concepts/x` になる。

これは NFC/NFD の衝突ではない。lint は `duplicate_slugs` と `case_only_duplicates` を報告するが、`normalization_collision` は付けない。設計の「大文字小文字だけが違う出力に接尾辞を足す」処理より前に、識別子が同一になっている。

PoC の `Core` に、この2件を返す収集関数を与えると、ページ数は1件になり、本文は `SECOND` だけが残った。新設計には、この衝突を止める・除外する規則がない。

根拠：[設計の衝突処理](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:38)、[識別子と出力名](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:44)、[ページの判定](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:38)、[PoC の辞書への格納](C:/Works/info-hive-dev/poc/browse/gen.py:170)。**結果：識別子の一致と、PoC での片方の消失を再現。新実装での動作は未確認。**

**4.【重大】Wiki 外の入力を読む一方、書き込み保護は Wiki のルートしか守らない。**

設計から導いた反例：

1. Wiki を `C:/Work/wiki`、既存の browse 出力を `C:/Cache/site` とする。出力には正規の目印がある。
2. `site/original.md` を置き、`wiki/concepts/a.md` をそのファイルへのシンボリックリンクにする。
3. `build <WIKI_ROOT> --out C:/Cache/site` を実行する。

設計 §2 に従えば、`a.md` は外部の実体から読む。書き込み先、作業場所、その親はすべて Wiki のルートと重ならないため、§7 の検査も通る。

ところが、新世代には `original.md` がない。旧出力の退避・削除により原本が消え、Wiki 内の `a.md` がリンク切れになる。閲覧前後のファイル読み取り結果もハッシュも維持できない。

保護対象に、読み込んだ入力の実体が含まれていない。「出力先が Wiki の外」という条件だけでは、§2 で許可した入力との非重複を保証しない。

根拠：[外部の入力を読む規則](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:36)、[出力先の検査](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:102)、[世代の入れ替え](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:105)、[書き込み直前の検査](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:112)。**結果：設計上の検査範囲の欠落。実ファイルの削除は未実行。**

**5.【重大】静的出力をサーバーの状態ディレクトリに重ねると、稼働中の排他を壊せる。**

Linux を仮定する。`K = wiki_key(W)`、`D = <data_dir>/browse/K.server` とする。

1. `build W --out D` を実行する。`D` は空なので許可され、browse の目印が付く。
2. `serve W` を実行する。状態ディレクトリは同じ `D`。サーバーAが `D/server.lock` を保持する。
3. 再度 `build W --out D` を実行する。`D` は目印付きの出力なので許可される。
4. 世代の入れ替えで、`D` が `old-*` に移り、新しいディレクトリが `D` になる。
5. `serve W` をもう一度実行する。

POSIX のファイルロックは、移動前に開いたファイルに残る。新しい `D/server.lock` は別のファイルなので、後続の `serve` が取得でき、サーバーBが起動する。Aの記録も現行の状態パスから失われる。

これはジャンクションの差し替え競合を必要としない。設計が認める `--out` と `serve` の組み合わせだけで成立する。静的出力とサーバー状態の場所が重なることを拒否する規則がない。

根拠：[任意の出力先と所有確認](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:100)、[ディレクトリの入れ替え](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:108)、[サーバーの状態と排他](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:127)、[採用するロック機構](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_common.py:138)。**結果：設計上の競合。Linux の実プロセスによる再現は未実行。**

## 崩れる前提

- **「`resolve_link()` が返せば、行き先のページが一意に分かる」**  
  返り値はページ識別子ではなくスラッグである。実行確認では、`sources/left/paper` と `sources/right/paper` がともに `"paper"` を返した。パス付き参照の識別情報を別に保持しなければ、目的語を再び取り違える。

- **「`unresolved_sources` が空なら、曖昧なソース参照もない」**  
  欠陥2の入力で崩れる。曖昧性は別の検出項目に出る。

- **「識別子の衝突は NFC/NFD と出力名の大文字小文字だけで尽くせる」**  
  `.md` と `.MD` を除去した時点で同一になる入力がある。

- **「Wiki のルートと重ならなければ、入力を変更しない」**  
  外部実体を持つページ、索引、オントロジーが書き込み先にあると崩れる。

- **「ロックファイルをサーバー自身が消さなければ、同じパスの排他は維持される」**  
  別の browse 操作が親ディレクトリを入れ替えると崩れる。

## 見落としと軽微な問題

- **【軽微】外部通信の合格条件の範囲が一致していない。**  
  [ADR-0016 の決定](C:/Works/info-hive-dev/docs/adr/0016-wiki-browse-stage1-accepts-two-delivery-methods.md:25)は、閲覧操作について外部通信0件を要求する。一方、[設計の試験](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:167)は「表示の時点」に限定し、外部リンクのクリックは通信を横取りして試す。実際の製品ではクリック時の外部移動を許すため、試験が証明する範囲はADRの文面より狭い。クリックを条件の外に置くという例外は、ADR-0016 にない。

- **【軽微・推測】`seq` 自体が途中で壊れた場合の復旧が未定義。**  
  通常の上書きで更新する実装を仮定すると、truncate 後の停止で空ファイルになり得る。[設計 §7](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:104)はロック内での読み書きしか定めず、壊れた `seq` の扱いを定めない。[中断試験](C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:157)も「各手順の後」であり、この途中状態を明示していない。原子的に更新する実装になるかは、まだ確かめられない。

## 検証した事実

| 主張・対象 | 結果 |
| --- | --- |
| 対象は wiki 0.9.0、`64acc43` | 一致。HEAD と `plugin.json` を確認 |
| 同梱 markdown-it-py は3.0.0 | 一致。実際に同梱モジュールを読み込んで確認 |
| lint とグラフは `canonical_meta()` を使う | 一致。双方のパース処理を確認 |
| グラフ抽出の依存は PyYAML 6.0.3 | 一致。PEP 723 の宣言を確認 |
| `concept:y` をページ用 resolver で解決できる | 食い違い。結果は `None` |
| `unresolved_sources` が空なら曖昧な参照がない | 食い違い。重複した `paper` の反例で空になった |
| `.md` と `.MD` を識別子で区別できる | 食い違い。PoC では片方が消えた |
| PoC サーバーが要求時に Markdown を描く | 食い違い。`serve.py` は生成済みファイルを読む |
| 新設計の安全性・復旧・ブラウザ試験が通る | 確かめられず。製品の実装はまだない |

実行確認は `python -B` とメモリ上のページデータ・抽出した関数で行った。リポジトリのファイルは作成・変更・削除していない。

## 崩せなかった点

- ADR-0016 により、第1段階を2方式で確認すること自体は承認済みになった。過去レビューの「3方式が必要」という指摘は、この版には当てはまらない。
- 127.0.0.1限定、厳密な Host 照合、起動ごとのトークンという契約を破る DNS rebinding の反例は示せなかった。
- デコード後の禁止要素検査と、中核の既知の出力名だけを返す規則から、任意ファイル取得の経路は示せなかった。
- `os.kill` を使う停止処理は撤回されており、以前の PID 再利用の反例は適用できない。
- 読み取り前の印を保存し、組み立てを直列化する規則は、過去に指摘された更新検出と古い結果の逆転を設計上は閉じている。
- 生成記録を出力外に置くこと、公開前に漏れを検査して失敗させること、複数の退避世代から `published_seq` で復旧することは、現在の設計に明記されている。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
