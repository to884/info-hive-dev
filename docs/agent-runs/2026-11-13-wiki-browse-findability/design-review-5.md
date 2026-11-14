## 判定

**却下。確信度：高。** 参照実装の第2段に、通常の入力で組み立てが停止する反例と、`data-groups` の契約を満たせない反例があります。致命的な欠陥は確認していません。

## 致命的・重大な欠陥

1. **重大：NFCで同じになる索引ファイルが併存すると、参照実装が停止する。**

   次の入力です。ファイル名はPythonの文字列リテラルで示します。`a.md`、`b.md` は通常のページです。

   ```python
   {
       "index.md": "- [[indexes/caf\u00e9]]\n",
       "indexes/cafe\u0301.md": "# First\n- [[a]]\n",
       "indexes/caf\u00e9.md": "# Second\n- [[b]]\n",
   }
   ```

   現行の `Core._nav()` は、ディスク上の綴りから別々のIDを作り、両方の索引グループを保持します。しかし参照実装の `stage_one()` は、NFCに正規化済みの `f.rel` を辞書のキーにします。後のファイルが先のグループを上書きするため、`index.md` の項目が指すIDが `id_to_rel` から失われます。

   メモリ上で実行した結果、`build()` は **`KeyError: '_ga51794a61a'`** で停止しました。読み取り失敗も競合も不要です。`index.md` からの参照がなければ、停止せず片方の索引グループが消えます。

   根拠：[辞書への格納とIDの逆引き](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:58)、[現行のディスク上のパスによるID生成](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:769)。この入力形式は、既存の [NFC衝突索引の試験](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/tests/wiki/test_browse.py:455)でも扱っています。

2. **重大：種類に空白があると、参照実装のグループIDを `data-groups` に格納できない。**

   索引のないWikiに、次のページを1つ置きます。

   ```markdown
   ---
   type: "research note"
   title: "A"
   ---

   # A

   本文。
   ```

   参照実装が返す種類グループのIDは **`_rest_research note`** です。設計4.1に従って所属を空白区切りで書くと、次になります。

   ```html
   data-groups="_rest _rest_research note"
   ```

   読み取れる所属は `_rest`、`_rest_research`、`note` となり、後二者は木にありません。したがって、2.1末尾の「`data-groups` のIDはどれも木にある」を破ります。このグループで絞る場合も、木の件数は1件なのに一覧は0件になります。

   未知の種類をそのまま扱うことはN7・4.1の契約内です。また、`_rest` 系のID生成自体が、2.2の「今と同じIDを使う」という規則と食い違います。

   根拠：[参照実装の種類からのID生成](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:124)、[所属の空白区切り](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:222)、[IDの契約](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:127)。

## 崩れる前提

- **正規化後の相対パスで、索引ファイルを一意に識別できる。** NFCとNFDだけが違う名前を併存できる環境で崩れます。第1段が区別したファイルを、第2段への受け渡しで再びまとめています。
- **種類の値をIDに直接埋めても、所属の区切りと衝突しない。** 空白を含む未知の種類で崩れます。
- **表の表示が一致すれば、木の項目の名前も一致している。** 次の軽微な問題のとおり、表を描く関数が実データの `label` を使わないため成立しません。

## 見落としと軽微な問題

**軽微：グループへの項目の `label` がN6どおりに変更されず、表だけが変更後の名前を表示する。**

`index.md` に次を置き、`indexes/x.md` の題名を `Custom` にします。`a` を併記することで、N6による包みの削除を避けます。

```markdown
- [[a]]
- [[indexes/x|User alias]]
```

参照実装の結果は、グループ項目の **`label: "User alias"`** を保持します。一方、表を作る `render()` は、項目の `label` を無視してIDから題名を引くため、**`→Custom`** と表示します。両方を実行して確認しました。

N6はリンクの名前を行き先のグループ名にすると定めています。第9節で実際の項目を参照実装と比較すると、文章上の規則と異なる期待値になります。

根拠：[変換処理](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:75)、[`label` を使わない表の描画](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:160)、[N6](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:96)。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 設計書の15例の表は参照実装の出力と一致する | **一致**。同じ入力をメモリ上のSnapshotで実行し、15例すべて比較 |
| 前回のコード内wikilink、Setext、番号付きリスト、`.md`、短いスラッグ、日本語キーの反例 | **今回の例では解消**。第1段は現行Coreを使用 |
| 第2段が現行Coreの作る索引グループを保持する | **食い違い**。NFC衝突でグループ消失・例外を確認 |
| 第2段のIDが空白区切りの所属と両立する | **食い違い**。`research note` で確認 |
| グループ項目の名前がN6に従う | **食い違い**。内部の `label` と表の表示が異なる |
| 遅延読み込みの各ブラウザでのCSP・`file://`動作、1,000行の表示時間 | **確かめられず**。実ブラウザ試験・計測は未実行 |

実行はメモリ上に限定しました。ファイルは変更していません。

## 崩せなかった点

- 通常の15例では、中継・相互参照・自己参照から、木にないグループへの項目は作れませんでした。
- N3の1回だけの圧縮と、N6による0件の「索引」の包みの除去は、掲載例で成立しました。
- 要約を入力の文字から作る方針に、構造の直しのP7を破る機械情報の追加は見つかりませんでした。
- 世代変更によるグループIDの意味の変化は、明記された限界として扱い、重大には数えていません。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
