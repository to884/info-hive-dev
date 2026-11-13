# 既定の書き出し先に利用者のファイルがあるときの、3 つの配置（2026年11月13日）

7 回目の設計のレビューの重大 1 を、試作（7 版目）の実関数と実際のディスクで確かめた。開発用の PC（Windows 11）で流した。

```text
Python 3.14.6 win32
browse-junction: rc = 0、警告 = []、private.txt が残るか: False
data-junction: rc = 0、警告 = []、private.txt が残るか: False
no-link: rc = 0、警告 = []、private.txt が残るか: False
```

- `browse-junction` はレビューの反例である（`<data_dir>/browse` が利用者のディレクトリへのジャンクション）。
- `data-junction` は、ジャンクションが 1 つ上（`<data_dir>` そのもの）にある。`browse` は実のディレクトリである。
- `no-link` は、リンクがなく、利用者が `<data_dir>/browse/<key>/` に手でファイルを置いた場合である。作者の決定（領分の中に利用者が手で置いたものは守らない）のとおりの振る舞いである。
- 3 つとも、既定の書き出し先は門を通さず、前の世代を読まないので、利用者のファイルを前の世代として退避し、消す。
