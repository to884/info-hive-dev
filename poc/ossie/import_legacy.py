"""既存グラフを読み取り専用で照合して意味レコードに投影する。"""

from __future__ import annotations

from hashlib import sha256
from contextlib import closing
import json
from pathlib import Path, PurePosixPath
import re
import sys

import export_wiki_graph as legacy
from semantic_records import Trial


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def raw_quote(wiki: Path, ref: str | None, quote: str) -> tuple[str | None, str]:
    if not ref:
        return None, "no_raw_ref"
    match = re.fullmatch(r"(raw/.+)#L([1-9][0-9]*)", ref)
    if not match:
        return None, "unsupported_raw_ref"
    path = PurePosixPath(match[1])
    if path.is_absolute() or ".." in path.parts or "\\" in match[1] or ":" in match[1]:
        return None, "unsupported_raw_ref"
    for base in (wiki, wiki.parent):
        raw_root = base / "raw"
        here = (base / path).resolve()
        if not here.is_relative_to(raw_root) or not here.is_file():
            continue
        data = here.read_bytes()
        try:
            lines = data.decode("utf-8-sig").splitlines()
        except UnicodeDecodeError:
            return digest(data), "invalid_raw_encoding"
        line = int(match[2])
        return digest(data), "matched" if line <= len(lines) and quote in lines[line - 1] else "anchor_mismatch"
    return None, "raw_not_found"


def read_export(source):
    with closing(legacy.readonly(source)) as db:
        return {
            table: legacy.read_rows(db, name, legacy.EXPORT_COLUMNS[table], legacy.KEYS[table])
            for table, name in legacy.NAMES.items()
        }


def import_wiki(wiki, wiki_id, legacy_dir, scratch_db):
    scripts = Path(__file__).resolve().parents[2] / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        import wiki_graph_extract as extract
    finally:
        sys.path.remove(str(scripts))

    exported = read_export(legacy_dir / legacy.DATA)
    source = {table: [{key: row[key] for key in legacy.SOURCE_COLUMNS[table]} for row in rows]
              for table, rows in exported.items()}
    ontology_file = wiki / "graph" / "ontology.yaml"
    old_ontology = ontology_file.read_bytes()
    pinned_ontology = legacy_dir / "ontology.source.yaml"
    pinned_ontology.write_bytes(old_ontology)
    ontology = extract.read_ontology(pinned_ontology)
    pages = extract.collect_pages(wiki)
    nodes, page_ids, aliases = extract.build_nodes(pages, ontology)
    edges = extract.build_edges(pages, page_ids)
    scratch_db.touch(exist_ok=False)
    extract.build_sqlite(scratch_db, nodes, aliases, edges)
    if legacy.snapshot(scratch_db) != source or ontology_file.read_bytes() != old_ontology:
        raise ValueError("入力 Markdown・定義と既存 SQLite の再抽出結果が一致しません")

    pages_by_id = {}
    for page in pages:
        pages_by_id.setdefault(page_ids[extract.page_key(page)], page)
    trial = Trial(wiki_id)
    snapshot = trial.key("legacy_snapshot", [source, digest(old_ontology)])
    trial.definition("legacy", "既存オントロジーの取り込み", ontology)
    article_ids, entity_ids, revisions, evidence_ids = {}, {}, {}, {}
    graph_aliases = {}
    for row in source["aliases"]:
        graph_aliases.setdefault(row["node_id"], []).append(row["alias"])
    for node in source["nodes"]:
        old_id = node["id"]
        page = pages_by_id[old_id]
        disk = Path(page["path"]).resolve(strict=True)
        if not disk.is_relative_to(wiki):
            raise ValueError("ページのファイルが wiki の外を指しています")
        page_data = disk.read_bytes()
        page_text = page_data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        if extract.read_frontmatter(page_text) != (
            page["meta"], page["body"], page["fm_problems"],
        ):
            raise ValueError("処理中に入力記事が変更されました")
        page_hash = digest(page_data)
        meta = page["meta"]
        classification = (
            "explicit_graph_node_type" if isinstance(meta.get("graph"), dict) and meta["graph"].get("node_type")
            else "maps_from" if extract.derive_node_type(meta, ontology)
            else "default_concept"
        )
        if node["page_type"] in {"source", "synthesis"}:
            article_ids[old_id] = trial.article(old_id, node["title"], node["path"], page_hash)
        else:
            candidates = meta.get("aliases") or []
            candidates = candidates if isinstance(candidates, list) else [candidates]
            entity_ids[old_id] = trial.entity(
                old_id, node["title"], node["node_type"], page=node["path"], page_sha256=page_hash,
                aliases=[*graph_aliases.get(old_id, []), *(str(value) for value in candidates)],
            )
        trial.put("legacy_refs", [snapshot, "node", old_id], snapshot=snapshot, legacy_kind="node",
                  legacy_id=old_id, entity_id=entity_ids.get(old_id), article_id=article_ids.get(old_id),
                  disposition=classification)

    endpoints = {**article_ids, **entity_ids}
    for edge in exported["edges"]:
        old_id = edge["id"]
        subject, obj = endpoints.get(edge["subject"]), endpoints.get(edge["object"])
        explicit = edge["extraction_method"] == "explicit_graph_frontmatter"
        if explicit and edge["evidence"]:
            raw_ref = edge["raw_ref"]
            raw_hash, verification = raw_quote(wiki, raw_ref, edge["evidence"])
            evidence_ids[old_id] = trial.add_evidence(
                article_ids.get(edge["source_node_id"]), edge["evidence"], raw_ref=raw_ref,
                raw_sha256=raw_hash, original_source=edge["source"],
                verification=verification, method=edge["extraction_method"],
            )
        if explicit and subject and obj and edge["predicate"] in ontology["predicates"]:
            claim = trial.claim(edge["predicate"], subject, obj, polarity="unknown", qualifier=old_id)
            supports = [(evidence_ids[old_id], "supports")] if old_id in evidence_ids else []
            # 旧状態と期間の表記は完全に保持し、移行後の確定判断とは区別する。
            revisions[old_id] = trial.revise(claim, state="candidate", evidence=supports,
                                             details={key: edge[key] for key in legacy.SOURCE_COLUMNS["edges"]})
        trial.put("legacy_refs", [snapshot, "edge", old_id], snapshot=snapshot, legacy_kind="edge",
                  legacy_id=old_id, revision_id=revisions.get(old_id),
                  disposition="claim_candidate" if old_id in revisions else "unresolved" if explicit else "structural")

    for edge in exported["edges"]:
        source_id = revisions.get(edge["id"])
        if source_id:
            for kind in ("supersedes", "contradicts"):
                target_id = revisions.get(edge[f"{kind}_edge_id"])
                if target_id and target_id != source_id:
                    trial.reference(kind, source_id, target_id, reason="既存関係からの参照")
                elif edge[f"{kind}_node_id"] in endpoints:
                    trial.record_reference(kind, source_id, endpoints[edge[f"{kind}_node_id"]], edge[kind])
                elif edge[f"{kind}_resolution"]:
                    claim = trial.rows["claims"][trial.rows["revisions"][source_id]["claim_id"]]
                    trial.open_hold("reference_pending", source_id,
                                    f"既存の {kind} を主張の版へ対応づけられない",
                                    product_id=claim["object_entity_id"],
                                    reference_key=kind)
    return trial, source, snapshot, evidence_ids


def verify_import(source, snapshot, evidence_ids, path):
    with closing(legacy.readonly(path)) as db:
        mapping = {(kind, old_id): (entity or article, revision) for kind, old_id, entity, article, revision in db.execute(
            "SELECT legacy_kind, legacy_id, entity_id, article_id, revision_id FROM sem_legacy_refs WHERE snapshot = ?",
            (snapshot,),
        )}
        expected = {(kind, row["id"]) for kind, table in (("node", "nodes"), ("edge", "edges"))
                    for row in source[table]}
        if mapping.keys() != expected:
            raise ValueError("意味モデルの旧 ID 対応が入力と一致しません")
        original_edges = {row["id"]: row for row in source["edges"]}
        predicates = json.loads(db.execute("SELECT rules_json FROM sem_definitions").fetchone()[0])["predicates"]
        expected_edges, expected_records, expected_holds = set(), set(), set()
        for edge in legacy.project_edges(source):
            oid = edge["id"]
            revision = mapping["edge", oid][1]
            candidate = (edge["extraction_method"] == "explicit_graph_frontmatter"
                         and ("node", edge["subject"]) in mapping and ("node", edge["object"]) in mapping
                         and edge["predicate"] in predicates)
            if bool(revision) != candidate:
                raise ValueError("旧関係の主張候補への対応が入力と一致しません")
            if not revision:
                continue
            old = original_edges[oid]
            migrated = db.execute("""
                SELECT c.predicate, coalesce(c.subject_entity_id, c.subject_article_id),
                       coalesce(c.object_entity_id, c.object_article_id), r.details_json
                FROM sem_revisions r JOIN sem_claims c ON c.id = r.claim_id WHERE r.id = ?
            """, (revision,)).fetchone()
            if not migrated or migrated[:3] != (edge["predicate"], mapping["node", old["subject"]][0],
                                                mapping["node", old["object"]][0]) or json.loads(migrated[3]) != old:
                raise ValueError("意味モデルの主張が旧関係と一致しません")
            for kind in ("contradicts", "supersedes"):
                edge_target = mapping.get(("edge", edge[f"{kind}_edge_id"]), (None, None))[1]
                node_target = mapping.get(("node", edge[f"{kind}_node_id"]), (None, None))[0]
                if edge_target and edge_target != revision:
                    expected_edges.add((kind, revision, edge_target))
                elif node_target:
                    expected_records.add((kind, revision, node_target, edge[kind]))
                elif edge[f"{kind}_resolution"]:
                    expected_holds.add((kind, revision))
        for actual, expected_links in (
            ("SELECT kind, from_id, to_id FROM sem_references", expected_edges),
            ("SELECT kind, from_id, coalesce(to_entity_id, to_article_id), original_value FROM sem_record_references",
             expected_records),
            ("SELECT reference_kind, original_revision_id FROM sem_holds", expected_holds),
        ):
            if set(db.execute(actual)) != expected_links:
                raise ValueError("旧関係の履歴参照または保留が入力と一致しません")
        citations = []
        for edge in source["edges"]:
            evidence_id = evidence_ids.get(edge["id"])
            if not evidence_id:
                continue
            row = db.execute("""
                SELECT e.quote, e.original_source, e.raw_ref, e.verification, a.page_sha256, map.revision_id,
                       c.predicate, coalesce(s.legacy_id, sa.legacy_id), coalesce(o.legacy_id, oa.legacy_id),
                       link.evidence_id
                FROM sem_evidence e
                JOIN sem_legacy_refs map ON map.legacy_kind = 'edge' AND map.legacy_id = ?
                LEFT JOIN sem_articles a ON a.id = e.article_id
                LEFT JOIN sem_revisions r ON r.id = map.revision_id
                LEFT JOIN sem_claims c ON c.id = r.claim_id
                LEFT JOIN sem_legacy_refs s ON s.entity_id = c.subject_entity_id
                LEFT JOIN sem_legacy_refs sa ON sa.article_id = c.subject_article_id
                LEFT JOIN sem_legacy_refs o ON o.entity_id = c.object_entity_id
                LEFT JOIN sem_legacy_refs oa ON oa.article_id = c.object_article_id
                LEFT JOIN sem_supports link ON link.revision_id = r.id AND link.evidence_id = e.id
                WHERE e.id = ?
            """, (edge["id"], evidence_id)).fetchone()
            raw_ref = legacy.metadata(edge["metadata_json"]).get("raw_ref")
            if not row or row[:3] != (edge["evidence"], edge["source"], raw_ref):
                raise ValueError("意味モデルの根拠の値が入力と一致しません")
            if row[5] and row[6:] != (edge["predicate"], edge["subject"], edge["object"], evidence_id):
                raise ValueError("意味モデルの主張と根拠の対応が入力と一致しません")
            citations.append({"legacy_id": edge["id"], "predicate": edge["predicate"],
                              "linked": row[5] is not None, "raw_verification": row[3],
                              "source_page_version": row[4] is not None})
    return {"legacy_id_matches": len(expected), "evidence": citations,
            "legacy_history": {"revision_links": len(expected_edges), "record_links": len(expected_records),
                               "unresolved": len(expected_holds)}}
