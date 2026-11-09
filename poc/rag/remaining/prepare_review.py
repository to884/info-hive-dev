"""独立点検した質問と正解ページの修正候補を、人手確認用 CSV にする。"""
import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
OLD = (Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04").resolve()
OUT = POC_DATA / "full-20261104/review"
OUT.mkdir(parents=True, exist_ok=True)
queries = json.loads((ROOT / "poc/rag/pdf-queries.json").read_text(encoding="utf-8"))
lookup = {q["id"]: q for q in queries}
manifest = json.loads((OLD / "sample-manifest.json").read_text(encoding="utf-8"))
revised = {
    "p019": "F# Interactiveは、どのようなものを対話的に評価するためのツールか？",
    "p023": "F# Interactiveの実行ファイル名として挙げられている2つは何？",
    "p025": '文字列 "Couldn\'t put Humpty together again" を showWordCount に渡すと、単語数はいくつと表示される？',
    "p026": "F#では、初期化後のローカル値を変更可能にするには何を明示する？",
    "p033": "F#のタプル例で、site1に推論された型と値は何？",
    "p042": "F#とSuaveのサンプルWebサーバーは、初期状態でどこからアクセスできる？",
    "p044": "F#の関数型プログラミングの基本要素として挙げられているものは何？",
    "p047": "F#で文字列の一文字をインデックス指定で変更しようとすると、どのエラーになる？",
    "p050": "問題解決のアイデアを、どのような状態まで具体化する考え方が紹介されている？",
    "p051": "競争優位性がある状態とは、どのような状態か？",
    "p054": "ポジショニングマップの軸には、顧客が商品・サービスの認知や選択で思い浮かべる、または重視する何を選ぶ？",
    "p056": "ビジネスモデルとは、顧客に価値を継続的に提供するためのどのような仕組みか？",
    "p058": "AIDMAは、商品・サービスの購買プロセスのどの段階からどの段階までを可視化する？",
}
alternatives = {"p008":["p009","p012"],"p011":["p012"],"p015":["p016"],"p019":["p023"],
                "p028":["p023"],"p032":["p017"],"p035":["p034"],"p036":["p037"],
                "p041":["p042"],"p055":["p050"],"p056":["p057"]}
rows = []
for q in queries:
    expected = sorted(set(q["expected"] + [label for identity in alternatives.get(q["id"],[]) for label in lookup[identity]["expected"]]))
    rows.append({"id":q["id"],"review_state":"pending","proposed_question":revised.get(q["id"],q["query"]),
                 "proposed_relevant_pages":json.dumps(expected,ensure_ascii=False),
                 "source_file":manifest["files"][q["sample"]]["relative_path"],"pdf_page":q["page"],
                 "evidence":q["evidence"],"original_question":q["query"],
                 "ai_note":" / ".join(note for flag,note in [(q["id"] in revised,"文面修正候補"),(q["id"] in alternatives,"別ページにも根拠候補")] if flag),
                 "human_note":""})
with (OUT / "qa-review.csv").open("w",encoding="utf-8-sig",newline="") as stream:
    writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(OUT / "README.md").write_text("""# 評価質問の人手レビュー

`qa-review.csv` の 60 問を確認してください。
AI の独立点検では根拠から回答できない問は見つかりませんでしたが、13 問の文面修正と 11 問の別ページの根拠候補があります。
重複を除くと 22 問が点検対象で、残る 38 問も正解の妥当性を確認してください。

- `proposed_question` は修正後の質問です。必要に応じて直してください。
- `proposed_relevant_pages` は正解ページの候補の一覧です。唯一の正解ページではなく、根拠を持つページの集合として扱います。別の正解があれば追加してください。
- `source_file` と `pdf_page` は原本の相対パスと PDF のページ番号です。紙面に印刷されたページ番号とは異なる場合があります。
- `evidence` は抽出した根拠です。原本との一致と、質問に十分な根拠かを確認してください。
- `review_state` は `accepted`、`corrected`、`rejected` のいずれかにしてください。`pending` は未確認のまま扱います。
- 原本は変更しないでください。修正案を全件そのまま採用する場合は、チャットでその旨を回答しても構いません。

この CSV は元資料の抜粋を含むため Git の対象外に置いています。
""",encoding="utf-8")
print(json.dumps({"path":str(OUT / "qa-review.csv"),"questions":len(rows),"revised_questions":len(revised),"multiple_relevance_candidates":len(alternatives)},ensure_ascii=False))
