3件とも、既存コードのパス解決と16版の処理順序を根拠に指摘できると判断しました。ロック内での通常の追記・再適用からは、新しい変更消失の反例を導けていません。残る指摘は raw 保護の3件と、16版への変更後も残った規則・試験の食い違いです。
## 判定

**却下。確信度：高。** 書き込み経路に別名がないことから、raw と重ならないことは導けない。また、参加する書き手だけでも、ロック待ち中に増えた raw 参照を見落として原本を書き換えられる。

## 致命的・重大な欠陥

### 1.【重大】raw 側にある bind mount は、書き込み経路の検査にも根の重なりの検査にも掛からない

Linux で、開始前から次の静的な配置があるとする。実体の識別子と必要な権限は取得できるものとする。

```text
W = /kb/wiki
R = /archive/raw-old
K = /data/info-hive/apply/work

W/SCHEMA.md
W/concepts/originals/x.md    Markdown の原本
R                           W/concepts/originals の bind mount
```

`W` と `K` の下には mount point がない。mount point は、外にある **R 自身**である。

1. `begin --wiki W --raw-root R` で計画を作る。
2. `edit --path concepts/originals/x.md` を登録し、承認する。
3. `apply` が、そのファイルを置き換える。
4. **同じディレクトリを別名で読む `R/x.md` も書き換わる。**

指定された検査は、次の理由で通る。

- mount point の列挙は `W` と `K` の下を対象にするため、R は拒否対象にならない。
- 書き込み経路 `W/concepts/originals/x.md` 自体には、リンクも mount point もない。
- `_existing_chain(R)` は、R、`/archive`、`/` の実体を返す。mount 元の `W/concepts` や W へ戻らない。
- `identity(R)` は `identity(W/concepts/originals)` と同じだが、W 自身とは違う。したがって、R と W の一方の根が他方の祖先列にあるかを調べても、重なりを検出できない。

既存の `_existing_chain()` と `overlaps()` に、この配置の実体表を与えた検証でも、R と W、`.wiki-cache`、K、`data_dir()` の重なりはすべて `False` になった。R は今回の計画から既知なので、保証外14の「記録にもページにもない raw」には該当しない。

根拠：[mount の列挙範囲・638行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:638)、[根の重なり・650行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:650)、[既存の祖先列・57行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:57)。

同じ推論を使う保証外14の「raw のファイルを書き換えることはない」も成立しない。そこで認めている **未知の raw ルートの下に W がある配置**では、W 内に残る Markdown 原本を通常の `edit` で置換できる。別名は一つも要らない。これは未知のルートを検出しない限界そのものではなく、その限界に付け加えた不変性の保証への反例である。

根拠：[保証外14・864行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:864)。対照表936〜937行の「bind mount は生じない」「どの raw のファイルにもならない」は成立しない。

### 2.【重大】ロック待ち中に増えた「wiki の中の raw」を見落とす

初期状態として、`W/original.md` が存在し、それを指す `raw:` はまだないものとする。リンクや mount は使わない。

1. B が `edit original.md` を用意して承認を得る。`apply` の手順0を終え、ロック取得前で中断する。B の「wiki の中の raw」の集合は空である。
2. A が、別のソースページの `raw:` を `W/original.md` に直す計画を、同じ wiki のロックで適用する。A は成功してロックを外す。`original.md` 自体は変えていない。
3. B がロックを取る。
4. B の1cは `raw-roots.json` を読み直すが、ページから作った「wiki の中の raw」は更新しない。
5. B の `before_sha256` は一致したままなので、**原本になった `original.md` を置き換えて成功する。**

書き込みは同じロックで順番に行っている。非参加者、`unlock --force`、途中の別名変更は不要である。

CA が保護する対象は、ファイルの物理的な配置だけでは決まらない。参加する書き手がページの `raw:` を変更するだけでも増える。しかし、手順0の集合を使い続け、ロック内ではページを読み直さないことが明記され、試験でも要求されている。

根拠：[手順0・532行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:532)、[1cの更新対象・537行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:537)、[ロック内で読み直さない試験・801行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:801)。

したがって、対照表1019行の「wiki の中の raw の原本を守る」は、並行する参加者について成立しない。

### 3.【重大・仕様の衝突】管理領域内を指す `raw:` は収集するが、管理の書き込みでは保護しない

次の状態を考える。

```text
L/raw-roots.json             既存の有効な記録。R0 が入っている

W/sources/record-source.md
  type: source
  raw: "/kb/wiki/.wiki-cache/apply/raw-roots.json"
```

この `raw:` を拒む規則はない。7節646行に従えば、参照先は W 内なので、外部 raw ルートにはせず、「wiki の中の raw」に入る。

ここで、W と `data_dir()` の外にある新しい R1 を指定した計画を適用する。

1. 手順0が、`L/raw-roots.json` を「wiki の中の raw」として収集する。
2. 根の重なりの検査は通る。
3. 手順1cが R1 を記録に足し、**原本として収集した `L/raw-roots.json` を置き換える。**

`Writer` の検査cは、ページの書き込みには内部 raw との照合を要求する一方、管理の欄では「`.wiki-cache` の下に raw はない」として、その検査を置いていない。この前提を、入力の拒否条件で成立させていない。

同様に、既存の `P/<差分の名前>/plan.diff` を `raw:` が指していれば、表どおりの管理用検査では `pending --discard` による原本の削除も止まらない。

根拠：[内部 raw の収集・646行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:646)、[Writerの検査c・360行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:360)、[記録の置換・537行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:537)。

7節の禁止を管理の書き込みにも適用する読み方と、Writer の表どおりに実装する読み方が衝突している。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 書き込み経路に別名がなければ、raw と交わらない | raw 側のパスが wiki 内部の別名になっている |
| 根の祖先列の比較で、物理的な包含関係を判定できる | bind mount が、根の途中にある祖先を隠している |
| 手順0で作った内部 raw の集合は、適用まで有効である | 待機中に、参加者がページの `raw:` を変更する |
| `.wiki-cache` の下に raw はない | 存在する管理ファイルをページの `raw:` が指す |
| 未知の raw ルートとの重なりを見逃しても、原本のバイト列は変わらない | その raw の木の中に W と編集可能な原本がある |

## 見落としと軽微な問題

- **【軽微・仕様の衝突】W 自身の mount を許すかが一致しない。** Writer のeは、Wから始まるすべてのディレクトリが mount point でないことを要求する。一方、638行は W 自身を列挙から除き、665行は「外から wiki を mount するのはよい」とする。W 自身がボリュームの mount point である通常の配置について、許可と拒否の両方が書かれている。根拠：[検査e・362行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:362)、[許可の説明・665行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:665)。

- **【軽微】16版と両立しない試験が残る。** 815行は W 配下の bind mount を `raw_overlap` で拒むことを要求するが、638・816行では開始時に `mount_in_wiki` で止まる。また、833行は `.wiki-cache` と行き先を別のファイルシステムに置いて復旧する試験を要求するが、記載された tmpfs・別ドライブの配置は、現在のリンク／mount 拒否に掛かり、7bまで進めない。根拠：[raw の試験・815行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:815)、[別ファイルシステムの試験・833行](/C:/Works/info-hive-dev/.claude/worktrees/wiki-apply-design/docs/plans/wiki-apply-2026-11-14.md:833)。

## 検証した事実

| 確かめた事項 | 結果 |
| --- | --- |
| サブモジュールの版 | **一致。** `83dbb30abcce7d4ed56babee134cd6247ad7803d` |
| 新実装の有無 | **未実装。** `wiki_apply.py`、`wiki_fsguard.py` は存在しない |
| `_existing_chain()` が mount 元の祖先を復元するか | **復元しない。** 解いたパスと、その字面上の祖先を列挙する |
| 重大1の根の重なり | **模擬した実体表で確認。** 指定された既存関数では、すべて非重複になる |
| `raw:` のファイル・ディレクトリ参照 | **既存コードと一致。** `missing_raw()` は両方を認め、管理領域を除外する規則もない |
| 親の索引への通常追記 | **解析結果は一致。** 項目一つ分の5トークンが増え、既存のインライン本文が残った |
| 親のログへの通常のサブ行追記 | **解析結果は一致。** ブロックの並びを維持した |
| 既存の主要な書き込み経路と移行表 | 上記以外に、確実な移行漏れは確認できなかった |
| 実際の mount、電源断、新実装の停止・並行実行 | **確かめられず。** 本報告の反例は設計手順と既存コードから導いた |

リポジトリのファイルは変更していない。

## 崩せなかった点

- 14回目の重大1・3の**元の配置**である、W配下への bind mount は、16版の開始時検査で止まる。
- BVにより `D/base` も保持する規則では、待機中の `rebase` によって承認済み差分の前像を失う旧反例は成立しない。
- 全体ハッシュによる `edit`、同じファイルの `ops` の逐次合成、完了印のロック内再確認から、通常の適用に新しい変更消失・二重適用の反例は導けなかった。
- 明記された保証外13を除き、ロック取得・日誌の前進・自分の計画の適用という順序から、新しい二重書き込みの反例は導けなかった。
- POSIXで各同期が成功する条件では、BOの公開順序から、完了印だけが行き先より先に永続化される旧反例は導けなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: research
