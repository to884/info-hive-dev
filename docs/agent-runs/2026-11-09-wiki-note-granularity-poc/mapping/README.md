# 人が対応づけるための表

36 件の計画に出た候補を、資料ごとに 1 つの表にした。どの候補が同じ知見か、どの新規ページが同じページかは、人が決める（レポートの第 8 節）。表の列は `scripts/tabulate.py` が作り、人が埋める列は空のままにしてある。推測では埋めていない。

## どの表を埋めるか

人が埋めるのは、リポジトリの外の次の表である。引用を伏せていない。

```text
%USERPROFILE%\info-hive-dev-private\2026-11-09-wiki-note-granularity-poc\mapping\
  O-candidates.csv  R-candidates.csv  V-candidates.csv   候補の一覧
  O-pages.csv       R-pages.csv       V-pages.csv        新しく作るページの一覧
  O-raw-lines.md    R-raw-lines.md    V-raw-lines.md     照合に使う原文（行番号つき）
```

このフォルダーの `*-candidates.csv` と `*-pages.csv` は、記録のための写しである。公開リポジトリに原文を載せないため、候補の本文（`subject`、`claim`、`conditions`、引用）を落とし、行き先と根拠の行だけを残した。モデルは知見を原文に近い言い回しで書くので、引用だけを伏せても原文が漏れるからである。O は Medium の会員限定記事、R と V はリモートのない SemaSynth のプロジェクトの記録である。

## 実行を伏せてある

`blind_id`（`R-01`〜`R-12` など）は、実行を伏せた ID である。どのモデルの、どの方式の、何回目かは [blind-key.csv](blind-key.csv) にある。対応づけが終わるまで開かない。並びは run_id の SHA-256 で決めた。

## 埋める列

| 表 | 列 | 書くこと |
| --- | --- | --- |
| candidates | `cluster_id` | 同じ知見の候補に同じ ID を付ける（`R01`、`R02` …）。題名の似かたではなく、対象、条件、肯定か否定か、断定の強さが同じかで決める。条件だけが違う候補は別の ID にする。知見と呼べない候補（ソースにないこと、ソースの単なる見出し）は `-` |
| candidates | `faithful` | ソースの範囲で言えることなら `o`、ソースにないことを述べていれば `x`（捏造） |
| candidates | `conditions_kept` | ソースが付けている条件を保っていれば `o`、落としていれば `x`。条件のない知見は空のままでよい |
| candidates | `memo` | 判断に迷った理由など |
| pages | `page_cluster` | 同じページとみなす新規ページに同じ ID を付ける（`P01` …）。用語ページと主張ページは別の ID にする |
| （新規）`<資料>-gold.csv` | `cluster_id` | 任意。その資料から抜き出すべき知見の ID を 1 行に 1 つ。作らなければ、2 件以上の実行が出した知見を正解とみなす |

照合の手がかりは、`first_line`（根拠の最初の行）、`lines`、`quotes`、`quote_check` である。表は `first_line` の順に並んでいるので、同じ行を根拠にした候補が隣り合う。`quote_check` が「原本にない」の候補は、捏造の疑いとして先に見る。

## 埋めたあと

```bash
python docs/agent-runs/2026-11-09-wiki-note-granularity-poc/scripts/metrics_from_mapping.py
```

`metrics/agreement.md` に、資料と方式ごとの必須条件（捏造、条件の脱落）、知見の recall と precision、配置先の一致率（別モデルどうし、同じモデルの別の回）、同居の F1 と、合格の目安との比較が出る。
