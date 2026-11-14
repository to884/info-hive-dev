## 判定

**却下。確信度：中。** Windows の 8.3 短縮名が生成される配置で、初回は成功するのに、自分が生成した世代を次回更新できなくなる反例がある。短縮名の生成規則は Windows API で確認したが、書き出し全体の再現はメモリ上の入出力の代役による。

## 致命的・重大な欠陥

### 1. 重大／A：出力ディレクトリの短縮名が衝突し、一覧と実際の木が食い違う

前提は、書き出し先が 8.3 短縮名を生成する NTFS 上にあり、書き出し先と作業用ディレクトリがまだないことである。初期化済みの Wiki に、次の二つのページを置く。

```text
wiki/
  SCHEMA.md
  index.md
  data/a.md
  data~a~1/b.md
```

入力の `data` と `data~a~1` は、どちらも有効な 8.3 名なので、同じディレクトリ内に共存できる。ところが、生成器は次の出力名を返す。

| ページ | 出力名 |
| --- | --- |
| `data/a` | `data~a451b6e6/a.html` |
| `data~a~1/b` | `data~a~1/b.html` |

`data` は生成器の予約名なので接尾辞が付く。Windows の `RtlGenerate8dot3Name()` は、この `data~a451b6e6` に対して **`DATA~A~1`** を返した。

書き込みは名前順なので、長い名前のディレクトリを先に作る。その短縮名が `DATA~A~1` に割り当てられると、後続の `kind("data~a~1")` は既存ディレクトリと答える。結果として、二つのページが同じ実ディレクトリに入る。

```text
実際の木:
  data~a451b6e6/a.html
  data~a451b6e6/b.html

一覧に記録した名前:
  data~a451b6e6/a.html
  data~a~1/b.html
```

メモリ上の代役で、製品の走査・描画・`wiki_browse.build()`・`fs.build()` を通した結果は次のとおりだった。失敗や競合は入れていない。

```text
初回: 正常終了、pages=2、warnings=[]
世代の検証: 一覧にない、または種類が違う: data~a451b6e6/b.html
二回目: Stop（browse が作っていないものがある）
```

実ディスクでの再現手順は、上記の Wiki に対して、同じ書き出しを二回行うことである。

```powershell
$env:INFO_HIVE_DATA_DIR = 'C:\box\state'
python -B info-hive-wiki/skills/info-hive/scripts/wiki_browse.py build C:\box\wiki --out C:\box\site
```

これは、初回の木が描くべきファイルの表と一致するという設計 9.1 の約束を破る。利用者が一覧を書き換える必要もない。

根拠：

- [予約名に接尾辞を付ける処理](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:243)
- [`casefold()` でディレクトリの綴りを統一する処理](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:303)
- [既存ディレクトリならそのまま使う書き込み](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:1114)
- [実際の列挙名を一覧と照合する門](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:831)
- [設計 9.1「新しい世代」](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/docs/plans/wiki-browse-structure-2026-11-11.md:466)

**検証の限界：** 新規ディレクトリへの短縮名割り当てを含む、実ディスク上の書き出しは未実施である。

## 崩れる前提

- **`casefold()` で異なる出力ディレクトリは、ディスク上でも異なる。** 作成によって生まれる 8.3 短縮名で崩れる。
- **出力途中で既存ディレクトリが見つかれば、予定した共有ディレクトリである。** 別の出力ディレクトリの短縮名だった場合に崩れる。
- **前回の短縮名問題は、作成後の再判定と巻き戻しで覆える。** 今回はその再判定より後、世代の中身を作る段階で別名が生まれる。拒否処理にも巻き戻しにも入らない。

## 見落としと軽微な問題

**軽微：構文木検査は、関数を変数に入れるだけで層外の入出力を見逃す。**

次のコードに対して、`io_violations()` は実際に `[]` を返した。

```python
import os
read = os.read

def leak(fd):
    return read(fd, 1)
```

`import io as i` と `i.FileIO(p, "w")` の組み合わせも `[]` だった。製品コードでこの漏れを利用した入出力は確認していない。

根拠：[呼び出し時の綴りを検査する箇所](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/tests/wiki/test_browse_fs.py:116)、[インポートの検査](C:/Works/info-hive-dev/.claude/worktrees/affectionate-vaughan-42c8af/tests/wiki/test_browse_fs.py:153)。

また、書く側の探索は固定の `FILES_N`、読む側の探索は固定の `WIKI` を使っている。上記のように、**名前変換によって初めて生じる別名の衝突**は、既存の全量探索には含まれていない。

## 検証した事実

- **食い違い：** 上記のメモリ実行では、初回成功後の世代が門を通らず、二回目の書き出しが拒否された。
- **一致：** Windows API は `data` と `data~a~1` を有効な 8.3 名と判定し、`data~a451b6e6` の短縮名として `DATA~A~1` を返した。
- **一致：** `LayerContractTest` の二件と `ClassifyTest.test_absent_and_unknown` は成功した。
- **一致：** `sweep-7/` の七つの記録は、いずれも `exit 0` で終わっている。ただし、今回は全探索を再実行していない。
- **検証範囲：** Windows／Python 3.14.6。リポジトリの変更なし。実ディスクへの書き出し、実サーバー通信、Linux での検証は未実施。

## 崩せなかった点

以下はメモリ上で確認した。

- 前回の `NEWDAT~1` による拒否では、作成したディレクトリが巻き戻され、名前が残らなかった。
- 確定後に `Stop`、`Unknown`、`Absent`、`ValueError` を発生させても、書き出しは 0 を返し、警告が残った。
- `remove_record()` の領分確認で `Unknown` が発生しても、例外は外へ出ず、警告になった。
- 小さな入力では、読めないページを含む中核と、そのページを取り除いた中核の意味的な結果が一致した。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
