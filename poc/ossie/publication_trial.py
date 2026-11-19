"""共通の書く段を使う合成 wiki の ingest と公開の試験用入口。"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
from tempfile import TemporaryDirectory
import time

PLUGIN = Path(__file__).resolve().parents[2] / "info-hive-wiki" / "skills" / "info-hive"
sys.path.insert(0, str(PLUGIN / "scripts"))

import wiki_apply
import wiki_graph_extract as extract
import wiki_graph_lint as graph_lint
from semantic_export import write_release
from semantic_records import Trial


SEED = {"source": "seed", "maker": "verified-maker", "part": "BASE",
        "quote": "KabutoMarker この出典の旧版は製品が基盤に依存すると述べる。"}
TEMPLATE = PLUGIN / "assets" / "ontology.yaml.template"
TRIAL_FILES = "ontology/trial-files.json"


def read_json(path):
    return json.loads(path.read_bytes())


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def product_slug(maker, part):
    # 試験入力で確認済みのメーカー・品番だけを、一意なキーにする。
    return "product-" + sha256(wiki_apply.encoded([maker, part])).hexdigest()[:20]


def insert(state, intent):
    slug = intent["source"]
    if not re.fullmatch(r"[a-z][a-z0-9-]*", slug) or not all(intent[k] for k in ("maker", "part", "quote")):
        raise ValueError("出典と確認済みの識別子、引用を指定してください")
    product = product_slug(intent["maker"], intent["part"])
    entries = state["citations"]
    new = {key: intent[key] for key in ("maker", "part", "quote")}
    before = entries.setdefault(slug, new)
    if before != new:
        raise wiki_apply.Conflict("同じ出典 ID を別の内容では作れません")
    return product


def frontmatter(meta, body):
    # JSON を inline YAML として書き、日本語と引用をそのまま保つ。
    values = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in meta.items())
    return f"---\n{values}\n---\n\n{body}\n"


def restore_semantics(base):
    trial = Trial("isolated-publication-fixture")
    if base is not None:
        directory = base.root / "ontology" / "ossie"
        old = read_json(directory / "release.json")
        for line in (directory / "records.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            table = row.pop("table")
            trial.rows[table][row["id"]] = row
        trial.parent_release = old["release_id"]
    return trial


def materialize(work, base, state):
    common = {"tags": ["fixture"], "created": "2026-11-19", "updated": "2026-11-19"}
    save(work / "SCHEMA.md", "# 公開試験の wiki\n")
    save(work / "assets" / "badge.svg", (
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24">'
        f'<text x="0" y="14">{len(state["citations"])}</text></svg>'
    ))
    save(work / "concepts" / "platform.md", frontmatter(
        {**common, "type": "concept", "title": "基盤"}, "検証で使う基盤。"))
    # スラッグが同じ場合に、一方を勝手に選べないことを確かめる。
    for directory, title in (("concepts", "概念の共通名"), ("entities", "実体の共通名")):
        save(work / directory / "shared.md", frontmatter(
            {**common, "type": "concept", "title": title, "graph": {"node_id": f"concept:{directory}-shared"}},
            f"{title}。"))

    by_product = {}
    sources = []
    for slug, evidence in sorted(state["citations"].items()):
        product = product_slug(evidence["maker"], evidence["part"])
        by_product.setdefault(product, []).append((slug, evidence))
        save(work / "sources" / f"{slug}.md", frontmatter(
            {**common, "type": "source", "title": f"出典 {slug}"},
            f'{evidence["quote"]}\n\n![公開版を示す図](../assets/badge.svg)\n\n[[entities/{product}]]'))
        sources.append(f"- [[sources/{slug}]]")
    for product, evidences in by_product.items():
        rels = [{"predicate": "depends_on", "object": "concept:platform", "source": slug,
                 "evidence": evidence["quote"], "confidence": "high", "status": "current"}
                for slug, evidence in evidences]
        save(work / "entities" / f"{product}.md", frontmatter(
            {**common, "type": "entity", "kind": "product", "title": evidences[0][1]["part"],
             "sources": [slug for slug, _ in evidences],
             "graph": {"node_id": f"product:{product}", "relationships": rels}},
            "この製品は [[concepts/platform]] に依存する。"))
    save(work / "index.md", "# 索引\n\n## ソース\n" + "\n".join(sources) +
         "\n\n## エンティティ\n" + "\n".join(f"- [[entities/{p}]]" for p in sorted(by_product)) +
         "\n\n## 概念\n- [[concepts/platform]]\n- [[concepts/shared]]\n- [[entities/shared]]\n")
    save(work / "log.md", "# ログ\n\n" + "".join(
        f"- 2026-11-19 ingest [[sources/{slug}]]\n" for slug in sorted(state["citations"])))
    save(work / "graph" / "ontology.yaml", TEMPLATE.read_text(encoding="utf-8"))
    ontology = extract.read_ontology(work / "graph" / "ontology.yaml")
    pages = extract.collect_pages(work)
    nodes, ids, aliases = extract.build_nodes(pages, ontology)
    edges = extract.build_edges(pages, ids)
    extract.write_outputs(work / "graph", ["jsonl", "sqlite"], nodes, aliases, edges)
    findings = graph_lint.lint(pages, ontology)
    for name in ("unknown_predicates", "broken_object_refs", "missing_evidence", "broken_source_refs"):
        if findings[name]:
            raise ValueError(f"公開試行中の graph lint に違反があります: {name}")

    trail = restore_semantics(base)
    trail.definition(state["definition"]["label"], "合成 wiki の製品依存関係", {"predicates": ["depends_on"]})
    platform = trail.entity("platform", "基盤", "concept")
    for product, records in by_product.items():
        obj = trail.entity(product, records[0][1]["part"], "product")
        claim = trail.claim("depends_on", obj, platform)
        supports = []
        for slug, evidence in records:
            rel = f"sources/{slug}.md"
            article_sha = wiki_apply.digest((work / rel).read_bytes())
            article = trail.article([slug, article_sha], slug, rel, article_sha)
            evidence_id = trail.add_evidence(article, evidence["quote"], method="approved_fixture",
                                              original_source=slug, verification="matched_article")
            supports.append((evidence_id, "supports"))
        trail.revise(claim, state="accepted", evidence=supports)
    save(work / "ontology" / "registry.json", wiki_apply.encoded(state).decode("utf-8"))
    save(work / "ontology" / "definition.json", wiki_apply.encoded(state["definition"]).decode("utf-8"))
    write_release(work / "ontology" / "ossie", trail.freeze())
    save(work / TRIAL_FILES, wiki_apply.encoded(wiki_apply.source_files(work)).decode("utf-8"))


def initial(wiki, scratch):
    wiki.mkdir()
    save(wiki / "SCHEMA.md", "# 公開試験の wiki\n")
    state = {"definition": {"label": "初版"}, "citations": {}}
    insert(state, SEED)
    return publish_state(wiki, scratch, None, state, plan_id="0"*32)


def state_of(base):
    return read_json(base.root / "ontology" / "registry.json")


def verify_ingest_base(base):
    actual = wiki_apply.source_files(base.root)
    actual.pop(TRIAL_FILES, None)
    recorded = base.root / TRIAL_FILES
    if not recorded.is_file() or actual != read_json(recorded):
        raise wiki_apply.Conflict("試験用 ingest で再現できない変更があります。公開内容を再検査してください")


def prepare(wiki, scratch, base, state, plan_id):
    live_base = wiki_apply.capture_live_base(wiki) if base is None else None
    materialize(scratch, base, state)
    return wiki_apply.build_plan(wiki, scratch, base=base, plan_id=plan_id, live_base=live_base)


def publish_state(wiki, scratch, base, state, plan_id, checkpoint=lambda _: None):
    plan = prepare(wiki, scratch, base, state, plan_id)
    return wiki_apply.apply_plan(wiki, scratch, plan, wiki_apply.digest(wiki_apply.encoded(plan)),
                                 checkpoint=checkpoint)


def ingest(wiki, approved, stamp, *, after_prepare=lambda *_: None, checkpoint=lambda _: None):
    # 承認対象は入力と定義版。現在の版が変わっても、この入力を変更しない。
    approved = json.loads(wiki_apply.encoded(approved))
    approval = wiki_apply.digest(wiki_apply.encoded(approved))
    for attempt in range(1, 5):
        wiki_apply.recover(wiki)
        base = wiki_apply.resolve_publication(wiki)
        if base is None:
            raise wiki_apply.Conflict("公開の基準版がありません")
        verify_ingest_base(base)
        state = state_of(base)
        registered = state.setdefault("approved_ingests", {})
        previous = registered.get(stamp)
        if previous is not None:
            if previous["approval"] != approval:
                raise wiki_apply.Conflict("完了した ID に別の承認入力は使えません")
            return {**wiki_apply.read_receipt(wiki, stamp), "attempts": attempt, "product": previous["product"]}
        if base.definition_id != approved["definition_id"]:
            raise wiki_apply.Conflict("承認後に定義が変わりました。入力を再検査してください")
        product = insert(state, approved["intent"])
        registered[stamp] = {"approval": approval, "product": product}
        with TemporaryDirectory(prefix="wiki-approved-") as folder:
            source = Path(folder)
            plan = prepare(wiki, source, base, state, stamp)
            after_prepare(attempt, base.release_id)
            try:
                applied = wiki_apply.apply_plan(wiki, source, plan, wiki_apply.digest(wiki_apply.encoded(plan)),
                                               checkpoint=checkpoint)
            except wiki_apply.Conflict:
                if wiki_apply.resolve_publication(wiki).release_id == base.release_id:
                    raise
            else:
                return {**applied, "attempts": attempt, "product": product}
    raise wiki_apply.Conflict("並行更新が続いたため公開を保留しました")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki", type=Path)
    parser.add_argument("approved", type=Path)
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("--ready", type=Path)
    parser.add_argument("--go", type=Path)
    parser.add_argument("--crash", choices=("before_pointer", "after_pointer"))
    args = parser.parse_args()

    def ready(attempt, release_id):
        if attempt == 1 and args.ready:
            args.ready.write_text(release_id, encoding="utf-8")
            if args.go:
                deadline = time.monotonic() + 40
                while not args.go.exists():
                    if time.monotonic() >= deadline:
                        raise TimeoutError("試験の開始合図がありません")
                    time.sleep(0.03)

    def checkpoint(label):
        if label == args.crash:
            os._exit(71)

    try:
        report = ingest(args.wiki, read_json(args.approved), args.plan_id, after_prepare=ready, checkpoint=checkpoint)
    except wiki_apply.Conflict as error:
        print(str(error), file=sys.stderr)
        return 4
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
