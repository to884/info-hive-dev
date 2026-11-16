## 判定

**採用可。確信度：高。** 前回の「本文の `update` まで消える」反例は再現せず、新たな重大欠陥も崩せませんでした。ただし、追加テストには除外処理の欠落を検出できない穴があります。

## 致命的・重大な欠陥

なし。

## 崩れる前提

- **同じ表示なら管理用の値と認識される、とは限りません。** 判定は表示文字列ではなく `tok.content.strip()` の一致です。見出しを `## **主張と行き先**`、列名を `**行き先**`、セルを `**create**` や `cre&#97;te` にすると除外されません。実行で確認しました。訂正の隠蔽にはなりませんが、管理用の語が再び目印に混入します。根拠：[wiki_captions.py:617](C:/Works/info-hive-dev/.claude/worktrees/yt-fix/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:617)、[同:638](C:/Works/info-hive-dev/.claude/worktrees/yt-fix/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:638)。

## 見落としと軽微な問題

**軽微：追加テストは、管理用の値を一切除外しない実装でも通ります。**

メモリ上で `_prose` を次の挙動に差し替え、既存の `test_unknown_words` 全体が成功することを確認しました。

```python
if it.workflow_value:
    return it.display  # 除外を無効化
```

原因は次の二つです。

- `create` と `update` は検査対象の別の本文にも存在するため、行き先セルから漏れても検出結果が変わりません。
- 非検出を確認する `source` は、raw の frontmatter の `source_sha256` に最初から含まれます。`source_only` の除外を無効にすると `only` が増えますが、それを検査していません。

根拠：[test_wiki_youtube.py:1082](C:/Works/info-hive-dev/.claude/worktrees/yt-fix/tests/wiki/test_wiki_youtube.py:1082)、[同:1089](C:/Works/info-hive-dev/.claude/worktrees/yt-fix/tests/wiki/test_wiki_youtube.py:1089)、[同:355](C:/Works/info-hive-dev/.claude/worktrees/yt-fix/tests/wiki/test_wiki_youtube.py:355)、raw 全文との部分一致を使う [wiki_captions.py:1072](C:/Works/info-hive-dev/.claude/worktrees/yt-fix/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1072)。

## 検証した事実

- **一致：** 二つのパッチの計14ハンクは現行ファイルと一致しました。
- **一致：** 三つの値について、本文・主張列・理由列・節外・次の h1／h2・引用やコード内の見出し・列の並べ替えなど、39ケースの境界試験が成功しました。
- **一致：** 通信と時計を差し替え、`inspect` と `write same` で「json3取得 → 採時 → raw生成」の順序、時差付き・秒精度の `fetched_at` を確認しました。
- **試験結果：** 書き込み不要の既存21テストと、ファイル入出力をメモリに置き換えた照合系14テストが成功しました。
- **未検証：** 実ネットワークでの取得と、実ファイルへの書き込みを伴う全体試験。

## 崩せなかった点

- 通常本文や主張列にある `create`、`update`、`source_only` を、今回の除外で隠す経路。
- 次の h1／h2 以降へ除外状態を持ち越す経路。
- 新しい除外によって、印・定義の照合や confidence の計算を迂回する経路。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
