"""実記事を根拠に、未適用のオントロジー案と隔離した試料を作る。"""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import runpy

import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PLAN = ROOT / "docs/plans/wiki-project-ontology-2026-11-18.yaml"
PILOT = OUT / "pilot-v2/wiki"
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
import wiki_graph_extract as extract

base = yaml.safe_load((ROOT / "wiki/graph/ontology.yaml").read_text(encoding="utf-8"))
descriptions = {
    "component": "製品内の責務を持つ構成要素。ファイル名や UI の単語だけを理由に作らない。",
    "release": "製品の特定版。自前・外部のソフトウェア・モデルを同じ形で表し、release_of で製品へ結ぶ。公開日時や導入確認は別の事実。",
    "change": "範囲を特定した変更。コード、文書、設定、プロンプトを含む。提案と実施を本文で区別する。",
    "issue": "条件と期待との差を記録した問題。原因の仮説、修正案、GitHub issue の番号そのものとは区別する。",
    "evaluation": "対象、版、方法、結果、限界を特定した評価の実施。試験、比較、レビュー、手動確認を含む。",
    "artifact": "変更の対象となる管理された文書・設定・ファイル・リリース本文。repository と path または URL で識別し、要約する source ページと区別する。",
}
for name, description in descriptions.items():
    base["node_types"][name] = {"explicit_only": True, "description": description}

definitions = [
    ("part_of", ["component", "artifact"], ["product", "component"], "構成要素・管理対象物が製品または上位の構成要素に属する。自己参照と循環を採用しない。推移的なエッジは生成しない。"),
    ("release_of", ["release"], ["product"], "その製品の出荷の単位である。製品名と版を根拠で特定する。"),
    ("delivers", ["release"], ["change"], "その版で、その変更を出荷した。計画、main へのマージ、単なる言及だけでは書かない。"),
    ("changes", ["change"], ["component", "artifact"], "変更が直接手を入れた構成要素または文書・設定などの管理対象物。PR の一部なら本文で範囲を特定する。"),
    ("affects", ["issue"], ["product", "component", "release"], "指定した条件で問題が観測された対象。版が分かる障害は release を目的語にし、現行の全版への影響に一般化しない。"),
    ("fixes", ["change"], ["issue"], "その問題を解消する実施済みの変更。根拠の版・条件に限る。提案、回避策、未実施の案は採用しない。"),
    ("implements", ["change"], ["decision"], "変更がその具体的な設計判断を実装した。ADR 全体の要件充足や検証成功を意味しない。"),
    ("motivated_by", ["decision"], ["issue", "evaluation"], "その問題または評価が判断の理由になった。時系列や同時言及から理由を補わない。"),
    ("selects", ["decision"], ["product", "concept", "release"], "判断が製品・方式またはその特定版を選択した。製品の選択と、版の固定方針と、実装で固定した版を混ぜない。"),
    ("evaluates", ["evaluation"], ["product", "component", "release", "change", "decision", "artifact"], "その対象を、その版と方法で評価した。結果と未確認事項は評価ページにも必ず残す。集合のレビューを最終出荷版の評価として書かない。"),
    ("applies_to", ["concept"], ["product", "component"], "手順・教訓・原則の適用範囲として明記された対象。一般的に関係がありそうという理由だけでは書かない。"),
]
for name, subjects, objects, description in definitions:
    base["predicates"][name] = {"subject_types": subjects, "object_types": objects,
        "requires_evidence": True, "description": description}
for side in ("subject_types", "object_types"):
    base["predicates"]["depends_on"][side].extend(["component", "release"])

PLAN.write_text("# 提案: 2026-11-18。既存の定義を残した完全版。実 wiki には未適用。\n"
    "# 詳細な採用条件・識別規則・未実装の検査は同名の Markdown 設計書を参照。\n"
    + yaml.safe_dump(base, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
(PILOT / "graph").mkdir(parents=True, exist_ok=True)
shutil.copyfile(PLAN, PILOT / "graph/ontology.yaml")
(PILOT / "SCHEMA.md").write_text("# オントロジー設計の隔離試料\n\n製品 wiki ではない。原記事の写しと未採用の対象ページを収める。\n", encoding="utf-8")

S = {
    "pdf": "pdfのヘッダーの判定の修正-rag-0.5.1",
    "wording": "pdfのヘッダーの書き方の修正-rag-0.5.2-0.5.3",
    "models": "ingestのモデルの比較-2026-11-13",
    "agent": "追い越された版のリリース-wiki-0.15.0",
    "yt_design": "youtubeの字幕の取り込みの設計-2026-11-15",
    "yt_impl": "youtubeの字幕の取り込みの実装とリリース-wiki-0.23.0",
    "trial": "rawの段を任せるエージェントの確かめ-2026-11-14",
}
evidence = []
used_sources = set()

def ev(key, source, text, meaning):
    path = ROOT / f"wiki/sources/{S[source]}.md"
    contents = path.read_text(encoding="utf-8")
    assert text in contents, (key, text)
    start = contents.index(text)
    line = contents[:start].count("\n") + 1
    evidence.append({"id": key, "path": path.relative_to(ROOT).as_posix(),
        "source_slug": S[source], "line_start": line,
        "line_end": line + text.count("\n"), "quote": text,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "supports": meaning})
    used_sources.add(source)
    return key

ev("E01", "pdf", "rag 0.5.0 の `read_pdf` は、ファイルの先頭がちょうど `%PDF-` でないと「PDF の形式ではありません」として拒んでいた。", "問題の対象と条件")
ev("E02", "pdf", "`%PDF-` の前にあるバイトが 1024 バイト以下なら受け付けるように直した。上限は PDFium にそろえた", "実施した修正と境界")
ev("E03", "pdf", "to884/info-hive-rag#7 を 2026-11-12 にマージし（b3f45e3）、CHANGELOG に日付を入れた #8（0dea049）のあと、v0.5.1 をリリースした。", "修正の出荷と製品・版")
ev("E04", "pdf", "実データの 2 件を、直した `read_pdf` と `extract_pages`（`ocr_mode` は `off`）に通した。70 ページと 18 ページで、すべてテキストのページだった。", "直接経路の評価。MCP 全経路ではない")
ev("E05", "pdf", "実データの 2 件を、MCP の `register_pdf` から索引化までの経路で取り込むことは確かめていない。", "評価の限界")
ev("E06", "wording", "rag 0.5.2（to884/info-hive-rag#9、親は to884/info-hive-dev#81）で、rag の README、CHANGELOG、`rag_index.py` のコメント、v0.5.1 の GitHub リリースの本文、親の ADR-0013 を同じ書き方にした。文書だけの修正である。", "change はコードの実装だけに限定しない")
ev("E07", "models", "Haiku 5.5、Sonnet 5.5、Opus 5.5 で同じ 4 つの Web ページを `/wiki:ingest` に取り込み、raw の違いを比べた調査である。", "評価対象と方法")
ev("E08", "models", "結論として、Sonnet 5.5 を使い続けることにした", "比較にもとづく選択")
ev("E09", "models", "モデルの差が raw に出るのは Web ページだけである。モデルが受け持つのは、雑音の削除、訳、画像の補足、`translated_by` の記入である。", "適用範囲は Web raw の段")
ev("E10", "agent", "wiki 0.15.0（raw の段をエージェント `wiki:web-raw` に任せる変更）のタグと GitHub リリースの記録である。", "Web raw の変更と出荷")
ev("E11", "agent", "使い捨ての設定でマーケットプレイスから入れると、0.16.0 が入った", "タグの版と導入された版を区別する反例")
ev("E12", "yt_impl", "作者が ADR-0027（[[youtubeの字幕の取り込みの設計-2026-11-15]]）を承認し、実装を求めた（2026-11-16）。この記録は、その実装と、それを出した wiki 0.23.0 のものである。", "実装と判断と出荷")
ev("E13", "yt_impl", "`wiki_youtube.py`：PEP 723 で `yt-dlp==2026.8.19` を固定する。", "構成要素の依存の版")
ev("E14", "yt_impl", "Sol の敵対的レビューは 17 回で、どれも却下だった。", "レビューの実施は成功を意味しない")
ev("E15", "yt_design", "`wiki_youtube.py` を `uv run --script` で動かし、PEP 723 で yt-dlp の版を 1 つに固定して、字幕だけを取る。", "判断が選択した手段")
ev("E16", "pdf", "全量の OCR（`docs/research/rag-full-ocr-v050-2026-11-09.md`）で、先頭に改行が 1 バイトあるだけの 2 文書（`L4/` の下の seL4 の論文）が、この理由で失敗した。", "問題を先頭に 1 バイトの改行がある観測 2 件に限定する")
ev("E17", "models", "Haiku 5.5、Sonnet 5.5、Opus 5.5 で同じ 4 つの Web ページを `/wiki:ingest` に取り込み、raw の違いを比べた調査である。原本は `docs/research/wiki-ingest-model-comparison-2026-11-13.md`、実行の記録とスクリプトは `docs/agent-runs/2026-11-13-wiki-ingest-model-comparison/` にある。結論として、Sonnet 5.5 を使い続けることにした", "比較した調査と、その結論を一緒に示す。判断の当時の運用範囲は ingest 全体")
ev("E18", "trial", "wiki プラグイン 0.15.0 で足すエージェント `wiki:web-raw`（`model: sonnet`）に、`/wiki:ingest` の raw を作る段を任せ、要約ページから後をメインのモデル（Opus 5.5）で行ったときの記録である。", "後の raw と後段の分担を、11-13 の判断と別に表す")
ev("E19", "trial", "メインは `model` の引数を渡さずに `wiki:web-raw` を呼び、エージェントは Sonnet 5.5 で取得から `check --finish` までを行い、wiki のページには書かなかった。要約ページ、`index.md`、`log.md` はメインが書いた。", "実装された raw の分担とモデルの実行の観測")
ev("E20", "yt_impl", "wiki に次の 3 つのスクリプトを足した（to884/info-hive-wiki#74）。\n  - `wiki_youtube.py`：PEP 723 で `yt-dlp==2026.8.19` を固定する。", "wiki の字幕取得の構成要素の追加と固定した依存")
ev("E21", "yt_impl", "`v0.23.0` は注釈付きのタグで、#74 のマージコミット（`1252fda`）を指す。", "#74 の変更が出荷タグに含まれること")
ev("E22", "yt_impl", "取り込みの手順に V1〜V10 を足した。確信度の上限の表（`query-confidence.md`）には、動画のソースの行を足した。", "同じ PR のうち、別の変更として扱う文書の範囲")
ev("E23", "wording", "v0.5.2 は 2026-11-13 01:04（日本時間。GitHub の記録では 2026-11-12T16:04Z）にリリースされた。", "文書修正の出荷版")
ev("E24", "pdf", evidence[0]["quote"] + "\n- " + next(e["quote"] for e in evidence if e["id"] == "E16"), "rag 0.5.0 と先頭 1 バイトの改行の観測を一緒に特定する")
ev("E25", "pdf", next(e["quote"] for e in evidence if e["id"] == "E16") + "\n- " + next(e["quote"] for e in evidence if e["id"] == "E02"), "観測した拒否と、その直後に記された受け付け範囲の修正")
ev("E26", "pdf", "版は 0.5.1（パッチ）。今まで受け付けていた入力の扱いを変えず、受け付ける範囲を広げるだけである。", "受け付け範囲の変更と版を直接結ぶ判断")

by_evidence = {e["id"]: e for e in evidence}
objects = []

class QuotedValuesDumper(yaml.SafeDumper):
    def represent_mapping(self, tag, mapping, flow_style=None):
        result = super().represent_mapping(tag, mapping, flow_style)
        for key, _ in result.value:
            key.style = None
        return result

def rel(predicate, obj, eid, notes):
    e = by_evidence[eid]
    return {"predicate": predicate, "object": obj, "source": e["source_slug"],
        "evidence": e["quote"], "confidence": "high", "status": "current", "notes": notes}

def node(nid, title, source_keys, body, relationships=(), *, existing=None):
    typ = nid.split(":", 1)[0]
    slug = nid.replace(":", "--")
    if existing:
        path = ROOT / existing
        meta, _ = extract.parse_frontmatter(path.read_text(encoding="utf-8"))
        slug = path.stem
    else:
        meta = {"type": "concept" if typ in {"concept", "decision"} else "entity", "title": title,
            "tags": ["グラフ"], "sources": [S[k] for k in source_keys],
            "created": "2026-11-18", "updated": "2026-11-18"}
        if typ == "product":
            meta["kind"] = "product"
    meta["graph"] = {"node_id": nid, "node_type": typ, "relationships": list(relationships)}
    folder = "concepts" if meta["type"] == "concept" else "entities"
    target = PILOT / f"{folder}/{slug}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    # トップレベルの文字列は常に引用する。日付は現行 SCHEMA に合わせて引用しない。
    front = yaml.dump(meta, Dumper=QuotedValuesDumper, allow_unicode=True, sort_keys=False, default_style='"', width=1000)
    for key in ("created", "updated"):
        front = front.replace(f'{key}: "2026-11-18"', f'{key}: 2026-11-18')
    if existing:
        # 実記事の必要箇所だけを追加する。既存の改行・H1・メタデータは維持する。
        original = (ROOT / existing).read_text(encoding="utf-8")
        addition = yaml.dump({"graph": meta["graph"]}, Dumper=QuotedValuesDumper, allow_unicode=True, sort_keys=False, default_style='"', width=1000)
        marker = original.index("\n---", 4)
        target.write_text(original[:marker] + "\n" + addition.rstrip() + original[marker:], encoding="utf-8")
    else:
        target.write_text("---\n" + front + "---\n\n# " + title + "\n\n" + body + "\n", encoding="utf-8")
    objects.append({"node_id": nid, "node_type": typ, "title": title,
        "path": target.relative_to(OUT).as_posix(), "source_slugs": [S[k] for k in source_keys],
        "status": "未採用の試料", "relationships": list(relationships), "existing_page": existing})

runpy.run_path(str(OUT / "pilot_v2_nodes.py"), init_globals={"node": node, "rel": rel})

for key in used_sources:
    p = ROOT / f"wiki/sources/{S[key]}.md"
    target = PILOT / "sources" / p.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, target)
# 既存 concept の sources が指す補助の出典も実体を写す。
extra = ROOT / "wiki/sources/rawの段を任せるエージェントの確かめ-2026-11-14.md"
shutil.copyfile(extra, PILOT / "sources" / extra.name)

registry = {"date": "2026-11-18", "evidence": evidence, "objects": objects,
    "pilot_warning": "本番未適用。原記事の写しは SHA-256 で追跡する。試料は索引・raw・すべての wikilink を複製した完全 wiki ではない。",
    "negative_examples": ["評価がある→成功した", "main が 0.16.0→0.15.0 は公開できない", "型付きエッジがない→問題が存在しない", "同じ記事にある→理由になった"]}
(OUT / "evidence_and_pilot.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"node_types": len(base["node_types"]), "predicates": len(base["predicates"]),
    "evidence_records": len(evidence), "pilot_objects": len(objects), "typed_edges": sum(len(n["relationships"]) for n in objects)}, ensure_ascii=False))
