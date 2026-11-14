## 判定

**却下。確信度：高。** 通常の追記を拒む構造検証、異なる wiki ルート間で排他が成立しない配置、承認したバイト列と書き込むバイト列を結び付けていない適用手順が残っている。10節の移行一覧にも、既存の書き込み指示の漏れがある。

未実装の設計への判定である。パーサーの挙動は既存コードで確認した。以下の停止・並行実行・bind mount の反例は、設計の手順から導いたもので、実ファイルを変更する試験は行っていない。

## 致命的・重大な欠陥

### 1.【重大】構造検証が、通常の索引追記とログのサブ行追記を拒む

4節は、足した行より前の最上位ブロックについて、`map` まで変更前と同じであることを要求する。しかし、箇条書きや段落への追記は、その既存ブロックの終端を伸ばす。

既存の `wiki_pages.new_parser()` で、次を確認した。`map` は0始まり、終端を含まない。

| 操作 | 変更前 | 変更後 |
| --- | --- | --- |
| 既存の箇条書きへ項目を追加 | `bullet_list_open [2,4]` | `[2,5]` |
| 既存のログ段落へサブ行を追加 | `paragraph_open [1,2]` | `[1,3]` |

変更前のブロックは挿入位置より前にあるが、そのままの `map` を持つ対応ブロックは変更後に存在しない。規則をそのまま適用すると、正常な操作が `structure_changed` になる。

テンプレートの置き換えにも別の不整合がある。「（ソースを取り込むと追加される）」を索引の1行に置き換える場合、削除1行・追加1行なので後続見出しの位置は変わらない。実測でも、次の見出しは変更前後とも `[14,15]` だった。一方、178行は「足した行の数だけ」ずらすため、`[15,16]` を要求する。

通常の操作で伸びるブロックの扱いと、削除を伴う操作の行番号対応が定義されていない。既存の親リポジトリの索引・ログも、この箇条書きと段落の形である。

根拠：[設計4節・構造検証](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:175)、[テンプレート置換](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:188)、[既存パーサー](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:391)、[実際の索引](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/wiki/index.md:13)、[実際のログ](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/wiki/log.md:17)。

### 2.【重大】入れ子の wiki は別々のロックで同じファイルを書ける

次の配置は禁止されていない。リンクや mount は不要である。

```text
W1 = /kb/wiki
W2 = /kb/wiki/sub

W1/SCHEMA.md
W2/SCHEMA.md
W2/concepts/x.md
```

既存の初期化判定では、W1とW2はどちらも初期化済みである。

AはW1で `edit --path sub/concepts/x.md`、BはW2で `edit --path concepts/x.md` を用意する。両者の行き先は同じファイルだが、取得するロックは異なる。

```text
A: W1/.wiki-cache/apply/apply.lock
B: W2/.wiki-cache/apply/apply.lock
```

次の順序で、両方が成功しながらAの変更を失う。

1. AとBが、それぞれのロックを取る。
2. 両方が手順5で、行き先が自分の前像と一致すると確認する。
3. Aが置き換え、手順8の読み直しに成功する。
4. Bが置き換え、読み直しに成功する。
5. 両方の日誌が `done` になるが、Aの変更は残らない。

途中停止でも破綻する。Aの `pending` が残ったあと、Bは別の `journal/` しか見ずに同じファイルを書ける。その後のAの回復で「どちらでもない」が起きる。**すべての書き手が `wiki_apply.py` を使っていても起きる**ため、282行と保証外9の「加わらない書き手のときだけ」と食い違う。

根拠：[設計6節・ロックと日誌の探索](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:250)、[「どちらでもない」の説明](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:282)、[初期化判定の実装](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_initialized.py:67)、[ADR-0019の定義](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/adr/0019-wiki-root-is-marked-by-schema.md:20)。

### 3.【重大・仕様の欠落】ハッシュ確認後の作業ファイル変更が、書き込み前に拒まれない

ハッシュの確認はロック前の手順0にあり、新しい中身をメモリに作るのはロック内の手順5である。確認したバイト列を保持し、それだけを後続処理に使うという契約はない。

記述を満たす次の実行が可能である。

1. `D/edit/concepts/x.md` の内容Aについて、ハッシュHを承認する。
2. Aプロセスが `apply --expect-sha256 H` の手順0を通る。
3. Aプロセスがロックを待つ。
4. 別のClaude Codeの処理が、許された作業場所である同じファイルを内容BへEditする。
5. Aプロセスがロックを取り、手順5で作業ファイルを読み、Bを置く。

行き先の前像が変わっていなければ、`changed_since_prepared` では止まらない。手順8でハッシュの不一致を発見する実装でも、**未承認のBを置いたあと**である。

これは外部エディターによる wiki の変更ではない。設計がモデルに許している `D/edit/` の編集と、`apply` の実行が重なるだけで成立する。238行の「承認後に書き換えると不一致で拒む」という主張には、時間上の穴がある。

根拠：[設計5節・承認後の変更拒否](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:238)、[手順0](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:246)、[手順5](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:254)、[モデルによる作業ファイルの編集](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:123)。

### 4.【重大】管理領域の祖先検査は、別名で公開ページ側へ保存する配置を通す

開始前から、次の静的なbind mountがある場合を考える。

```text
W/.wiki-cache/apply/work  ← W/sources の bind mount
R                        ← Wと重ならない通常のrawルート
```

この配置は、Writerの4検査を通る。

- シンボリックリンクでも再解析点でもない。
- `work` の実体は `sources` だが、Wや `.wiki-cache`、`apply` と同じ実体ではない。
- rawの実体を含まない。
- `_existing_chain(work)` はmount元の親へ戻らず、指定パス側の `apply` の実体を祖先として含む。

既存の `_existing_chain()` に実体表を与えたメモリ上の検証でも、「祖先の実体は重複しない」「管理領域の実体を含む」が両方真になった。

その状態で `begin` すると、Dは次の二つの名前を持つ。

```text
W/.wiki-cache/apply/work/<名前>-<乱数>/
W/sources/<名前>-<乱数>/
```

モデルが指示どおり `D/new/concepts/x.md` に書いた承認前の記事が、公開ページ側の `sources/<名前>-<乱数>/new/concepts/x.md` にも現れる。既存のページ走査では、後者は除外対象ではない。

Gitの検査も `.wiki-cache` 側の名前だけに対して行うため、`sources/` 側の名前が無視されることを保証しない。**管理領域に属するという祖先検査は、管理領域以外の名前を持たないことを示していない。**

根拠：[設計1節・Writerの検査](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:91)、[Gitの検査](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:111)、[既存の祖先列挙](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:57)、[ページの対象判定](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:49)。

### 5.【重大】Writerの管理領域制約では、管理領域自体を初めて作れない

既存の初期化済みwikiに `.wiki-cache/apply/` がまだない場合である。

105行は、存在しなければWriterで作るとする。一方、Writerの検査4は、管理領域への書き込みでは、対象の親の祖先列に `.wiki-cache/apply` の実体があることを要求する。

```text
作る対象: W/.wiki-cache/apply
その親:   W/.wiki-cache
```

まだ存在しない `apply` の実体は、親の祖先列に存在しない。したがって作成を拒む。`.wiki-cache` 自体がない場合も同じである。

また、111行が古いwikiに作る `.wiki-cache/.gitignore` は、96行の「道具が自分のために書く場所はapply配下だけ」と両立しない。

初期化時だけの例外や別の分類は書かれていない。全書き込みを同じ検査に通すQを厳守すると、通常の初回利用が始まらない。

根拠：[設計1節・検査4と管理領域](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:94)、[存在しない領域の作成](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:105)、[既存初期化の作成対象](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/init_wiki.py:240)。

### 6.【重大】10節の一覧に、移行も例外扱いもされていない書き込み指示が残る

「一覧が移す範囲」である以上、次は既存ファイルが未変更であることへの指摘ではなく、**指定した移行範囲の不足**である。

| 漏れている箇所 | 実際の指示と食い違い |
| --- | --- |
| `commands/ingest.md:44`、`references/ingest-workflow.md:114,116` | Web取り込みの警告を受け入れる際、理由をログのサブ行に書いてからrawの作業を終了する。10節はコマンドの手順6〜7と参照文書の手順5〜9を挙げており、この先行する書き込みを扱っていない。その時点では、後の手順6が返す `log_entries` もない。 |
| `references/agent-memory-integration.md:35` | エージェントの指示へ配る定型文自体に、wikiページを `str_replace` で更新し、索引とログを更新する指示がある。384行は文書全体を「wikiの外のファイル」として対象外にしているが、そこから生成される指示の書き込み先はwikiである。 |
| `references/retrieval-setup.md:42,75` | `SCHEMA.md` のRetrieval節を書く指示と、既存のモデル名を承認後に直す指示がある。10節にも実装対象表にも、この参照文書がない。 |
| `references/lint-workflow.md:57,58,64–67` | リンクの追加・修正、出典やraw参照の修正、タグの体系の追記、日本語の書き損じの修正がある。索引・ログの手順5〜6でも、「残す」とした分割・統合・改名・削除でもない。 |
| `commands/evolve.md:17` と評価ループ | コマンドは通常ページ・索引・ログの更新を命じる。10節が挙げた `evolution-workflow.md:131–134` の書き手は、実際には `wiki_evolve_loop.py` である。同スクリプトはページを直接書き、索引とログをread-modify-writeするが、実装対象表に含まれていない。文書の操作名を書き換えても、この実行経路は変わらない。 |

したがって、対照表510行の「1回目の重大8は生じない」は成立しない。386行の語句検査も、これらを検出したときの移行先・例外の分類を代わりには決めない。

根拠：[設計10節の一覧と検査](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:368)、[Web警告時のログ指示](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:114)、[配布する定型文](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/references/agent-memory-integration.md:35)、[Retrieval節の修正](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/references/retrieval-setup.md:75)、[lintのページ修正](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/references/lint-workflow.md:57)、[評価ループの索引・ログ書き込み](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:467)。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 追記前のブロックは、追記後も同じ `map` を持つ | 既存の箇条書きや段落が伸びる |
| 後続ブロックの移動量は、追加行数である | テンプレート行の削除と追加を同時に行う |
| 同じファイルを書く参加者は、同じwikiのロックを取る | 初期化済みwikiが入れ子になっている |
| 手順0でハッシュを確認すれば、後で読む作業ファイルも同じである | ロック待ちなどの間に、モデルが同じDを編集する |
| 管理領域の実体が祖先にあれば、管理領域だけに保存される | 管理領域の子が、公開ページ側のディレクトリのbind mountである |
| 全書き込みに管理領域の所属検査を課しても、その領域を作れる | 初回利用で管理領域がまだ存在しない |
| メモリ連携文書の書き込み先は、wikiの外だけである | 生成する定型文に、将来のwiki直接編集を命じる文が含まれる |
| 保存手順の文書を変えれば、その書き手も移行する | ページ・索引・ログをPythonの評価ループが直接書いている |

## 見落としと軽微な問題

- **【軽微・回復順序の欠落】一時ファイルを置く前に停止した場合の順序が曖昧である。** 手順7で一時ファイルを作成・fsyncした直後、配置前に停止すると、行き先は前像のまま、一時名は存在する。回復表の「7と同じに置く」を先に実行すると、同じ名前の `O_EXCL` 作成が `FileExistsError` になる。280行には残存名の削除があるが、再作成より先に行う規定はない。記載順で処理する実装では、自分の停止だけで `stuck` になり、wiki全体が止まる。これは保証外9の発生条件とも食い違う。[設計:268](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:268)、[回復表と削除:277](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:277)。

- **【軽微・保証期間の欠落】日誌回収後には、残した計画を二重適用できる。** ログ追記だけの計画を `--keep` で適用し、30日後に別の適用がその `done` 日誌を回収すると、元のDとハッシュは残る。同じ適用を再実行すると、日誌がないため再び追記する。保存日数の選択の是非ではなく、再実行防止がその期間内に限られることと、期限切れ計画の扱いが明記されていない問題である。[設計:270](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:270)、[日誌回収:293](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:293)。

- **【軽微・パーサーと試験条件の食い違い】`<div>` と `| a |` は、記載した理由では拒めない。** 同梱パーサーは `html=False` なので `<div>` はHTMLブロックを開かない。`| a |` も区切り行がなければ通常の段落になる。既存サブ行の後ろに足した両入力が段落内に入ることを確認した。正常な段落拡張を許す解釈では、181行と412行の拒否期待は導けない。[設計:181](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:181)、[パーサー設定](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:397)。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 既存コードの参照版 | **一致。** サブモジュールHEADは `83dbb30abcce7d4ed56babee134cd6247ad7803d` |
| 既存の索引とログが、通常の箇条書き・段落である | **一致。** 親の実ファイルを読み、同梱パーサーでも確認した |
| 追記後も既存ブロックの `map` が変わらない | **食い違い。** 箇条書きと段落の終端が伸びた |
| テンプレート置換後、後続見出しが追加行数だけ移動する | **食い違い。** 1行置換では位置が変わらなかった |
| 初期化判定が入れ子のwikiを拒む | **拒まない。** ルートと直下の `SCHEMA.md` の種類だけを検査する |
| `_existing_chain()` がbind mount元の親へ戻る | **戻る処理はない。** `realpath()` 後の指定パスと、そのパスの祖先を列挙する |
| 評価ループの通常ページ・索引・ログの書き手 | **確認。** `wiki_evolve_loop.py` が直接書く |
| 10節の書き込み指示一覧の網羅性 | **食い違い。** 重大6の漏れがある |
| 1回目の重大1〜7、軽微1〜2の旧反例 | **旧入力のままなら拒否・後始末の規定が追加されている。** ただし、新しい構造の反例は上記のとおり |
| bind mount、実プロセス停止、並行適用 | **実機では確かめていない。** 配置・実行順序からの反例として扱った |
| `concurrency-check.md` の消失数 | 記録を読んだ。今回の独立再測定はしていない |

## 崩せなかった点

- `journal` をrawへのシンボリックリンクにする、1回目の重大1そのものは、Writerのリンク検査に当たる。
- `W/indexes -> W` による `log.md` の迂回編集は、途中のリンク拒否に当たる。W自身へのbind mountも、祖先と同じ実体を拒む規則に当たる。
- `apply` に別の `--raw-root` を渡す旧経路は、引数自体がなくなっている。
- 独立した `begin` が同内容の計画を作っても、`plan_id` が異なるため、旧版の内容一致による取り違えは起きない。
- `os.link` 成功後、一時名の削除前に停止する旧反例には、回復時の一時名削除が追加されている。
- `.md` を途中の要素に含む旧版の親子パスは、登録時に拒まれる。
- 全体の前像ハッシュで照合する `edit` では、別の節の完成形を「当て済み」の証拠にする旧反例は成立しなかった。
- 同じファイルの `ops` を順に合成する規則から、旧版の複数操作による上書き消失は導けなかった。
- 同梱パーサーを使う規則では、`~~~still-data` を誤って閉じフェンスにする旧反例は成立しなかった。

リポジトリのファイルは変更していない。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
