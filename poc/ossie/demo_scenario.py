"""合成 wiki で、集計と版をまたぐ移行を再現する。"""

from contextlib import closing
from pathlib import Path

import export_wiki_graph as legacy
from import_legacy import digest
from semantic_export import customer_counts, write_release
from semantic_records import Trial


ASK_DATE = "2025-06-01"


def equal(actual, expected, label):
    if actual != expected:
        raise ValueError(f"{label} が期待値と異なります: {actual!r}")


def article(trial: Trial, wiki: Path, key: str, quote: str) -> str:
    relative = f"sources/{key}.md"
    path = wiki / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntype: source\ntitle: {key}\n---\n\n{quote}\n", encoding="utf-8")
    data = path.read_bytes()
    article_id = trial.article(key, key, relative, digest(data))
    if quote not in data.decode("utf-8"):
        raise ValueError("合成記事の根拠を確認できません")
    return trial.add_evidence(article_id, quote, original_source=key, method="fixture",
                              verification="matched_article")


def add_claim(trial, predicate, org, product, evidence, *, intervals=(("2025-01-01", "2025-07-01"),),
              status="accepted", polarity="positive", qualifier=None):
    claim = trial.claim(predicate, org, product, polarity=polarity, qualifier=qualifier)
    return trial.revise(claim, state=status, intervals=intervals,
                        evidence=[(item, "supports") for item in evidence],
                        recorded_at="2025-06-01T00:00:00Z")


def database(output, label):
    return output / label / legacy.DATA


def counts(output, label, manifest, product, day=ASK_DATE):
    return customer_counts(database(output, label), manifest["definition_id"], manifest["wiki_id"], product, day)


def open_migrations(path):
    with closing(legacy.readonly(path)) as db:
        return db.execute("""
            SELECT count(*) FROM sem_holds h WHERE h.kind = 'migration_pending'
              AND NOT EXISTS (SELECT 1 FROM sem_decisions d WHERE d.hold_id = h.id AND d.state = 'resolved')
        """).fetchone()[0]


def run_demo(output, checkout=None):
    wiki = output / "synthetic-wiki"
    wiki.mkdir()
    (wiki / "SCHEMA.md").write_text("# 版の移行を試す合成 wiki\n", encoding="utf-8")
    trial = Trial("synthetic-project")
    rules = {"predicates": ["customer_of", "dealer_of", "uses", "does_not_use", "plan_offer"]}
    v1_id = trial.definition("v1", "顧客と利用契約の初期定義", rules)
    org = trial.entity("organization-a", "A社", "organization")
    a = trial.entity("product-a", "製品A", "product")
    b = trial.entity("product-b", "製品B", "product")
    c = trial.entity("product-c", "製品C", "product")
    service = trial.entity("service-plan", "保守プラン", "product")

    first = article(trial, wiki, "customer-1", "A社は2025年上半期に製品Aの顧客だった。")
    second = article(trial, wiki, "customer-2", "期間別台帳でもA社は製品Aの顧客と確認できた。")
    dealer = article(trial, wiki, "dealer", "A社は製品Bを代理販売した。")
    undated = article(trial, wiki, "undated", "A社は製品Cの顧客だった。時期の記録はない。")
    disputed = article(trial, wiki, "disputed", "別契約の顧客資格は確認が割れている。")
    usage = article(trial, wiki, "usage", "利用記録には製品Bの試用と契約が記載されている。")
    earlier = article(trial, wiki, "usage-start", "利用の開始は2020年ではなく2019年と確認できた。")
    opposition = article(trial, wiki, "opposition", "A社は試用していたが、製品Bを契約していなかった。")
    unclear = article(trial, wiki, "unclear", "A社の利用記録には疑問がある。何に対する疑義かは不明。")
    offer = article(trial, wiki, "offer", "保守プランの旧資料には提供形態が書かれていない。")

    initial_customer = add_claim(trial, "customer_of", org, a, [first])
    customer_claim = trial.claim("customer_of", org, a)
    equal(trial.current(customer_claim), initial_customer, "同じ命題の再取り込み")
    customer_rev = add_claim(trial, "customer_of", org, a, [first, second])
    add_claim(trial, "dealer_of", org, b, [dealer])
    add_claim(trial, "customer_of", org, c, [undated], intervals=())
    add_claim(trial, "customer_of", org, c, [disputed], status="disputed", qualifier="another-contract")
    trial.open_hold("not_analyzed", None, "製品Cの関連記事を未確認", product_id=c)

    use_claim = trial.claim("uses", org, b)
    old_start = trial.revise(use_claim, state="accepted", intervals=[("2020-01-01", None)],
                             evidence=[(usage, "supports")])
    changed = trial.revise(use_claim, state="accepted", intervals=[("2019-01-01", None)],
                           evidence=[(usage, "supports"), (earlier, "supports")])
    neg = add_claim(trial, "does_not_use", org, b, [opposition], polarity="negative", qualifier="contract")
    vague = add_claim(trial, "does_not_use", org, b, [unclear], polarity="negative", qualifier="unknown")
    ref_old = trial.reference("contradicts", neg, changed, evidence_id=opposition, reason="旧分類で利用に対する反証")
    trial.reference("contradicts", vague, changed, evidence_id=unclear, reason="対象を特定できない旧参照")
    updated = trial.revise(use_claim, state="accepted", intervals=[("2019-01-01", None)],
                           evidence=[(usage, "supports"), (earlier, "supports"), (first, "context")],
                           inherit_references=True)
    carried = next(row["id"] for row in trial.contradictions(updated) if row["derived_from_id"] == ref_old)

    old_plan = add_claim(trial, "plan_offer", org, service, [offer], status="candidate", intervals=())
    hold = trial.open_hold("migration_pending", old_plan, "旧資料だけでは保守契約か判断できない",
                           product_id=service, actor="fixture reviewer", recorded_at="2025-06-01T00:00:00Z")

    reports = {"v1": write_release(output / "v1", trial.freeze(), checkout)}
    trial.definition("v1-renamed", "顧客と利用契約の初期定義", rules)
    reports["v1-renamed"] = write_release(output / "v1-renamed", trial.freeze(), checkout)

    v2_id = trial.definition("v2", "利用を試用と契約へ分割",
                             {"predicates": ["customer_of", "dealer_of", "trial", "contract"]})
    trial_head = add_claim(trial, "trial", org, b, [usage])
    contract_head = add_claim(trial, "contract", org, b, [usage], status="disputed")
    trial.split(updated, [trial_head, contract_head], {
        carried: (contract_head, opposition, "引用は試用の有無ではなく契約の有無を述べている"),
    })
    ref_hold = next(row["id"] for row in trial.rows["holds"].values() if row["kind"] == "reference_pending")
    reports["v2"] = write_release(output / "v2", trial.freeze(), checkout)

    v3_id = trial.definition("v3", "保守契約を追加",
                             {"predicates": ["customer_of", "dealer_of", "trial", "contract", "maintenance_contract"]})
    new_evidence = article(trial, wiki, "maintenance", "新しい原本で保守プランの契約番号 MT-01 を確認した。")
    maintenance = add_claim(trial, "maintenance_contract", org, service, [new_evidence], qualifier="MT-01")
    trial.resolve_hold(hold, maintenance, new_evidence, "新しい原本に契約番号が記載された",
                       actor="fixture reviewer", recorded_at="2025-06-03T00:00:00Z")
    clarified = article(trial, wiki, "clarified", "疑義の対象は資料の集計手順で、試用や契約の有無ではない。")
    trial.resolve_reference(ref_hold, None, clarified, "試用・契約とは無関係と判断")
    reports["v3"] = write_release(output / "v3", trial.freeze(), checkout)

    other = Trial("synthetic-user")
    other.definition("v1", "別 wiki の顧客定義", rules)
    other_org = other.entity("organization-a", "A社", "organization")
    other_a = other.entity("product-a", "製品A", "product")
    reports["other"] = write_release(output / "other", other.freeze(), checkout)
    equal(org == other_org or a == other_a, False, "wiki ごとの ID 分離")

    observed = {
        "product_a": counts(output, "v1", reports["v1"], a),
        "product_a_after_period": counts(output, "v1", reports["v1"], a, "2025-07-01"),
        "product_b": counts(output, "v1", reports["v1"], b),
        "product_c": counts(output, "v1", reports["v1"], c),
        "product_a_after_rename": counts(output, "v1-renamed", reports["v1-renamed"], a),
        "product_a_v3": counts(output, "v3", reports["v3"], a),
        "product_b_v2": counts(output, "v2", reports["v2"], b),
        "product_b_v3": counts(output, "v3", reports["v3"], b),
        "other_product_a": counts(output, "other", reports["other"], other_a),
    }
    positive = {"customers": 1, "claims": 1, "evidence": 2, "customer_ids": [org], "limitations": []}
    empty = {"customers": 0, "claims": 0, "evidence": 0, "customer_ids": [], "limitations": []}
    for key, expected in {
        "product_a": positive, "product_a_after_rename": positive, "product_a_v3": positive,
        "product_a_after_period": empty, "product_b": empty, "other_product_a": empty,
        "product_b_v2": {**empty, "limitations": ["reference_pending"]}, "product_b_v3": empty,
        "product_c": {**empty, "limitations": ["disputed", "not_analyzed", "unknown_valid_time"]},
    }.items():
        equal(observed[key], expected, key)

    with closing(legacy.readonly(database(output, "v2"))) as db:
        history = db.execute("""
            SELECT id, claim_id, intervals_json FROM sem_revisions WHERE id IN (?, ?, ?)
        """, (old_start, changed, updated)).fetchall()
        equal({row[1] for row in history}, {use_claim}, "開始日訂正と根拠追加の主張 ID")
        equal(len(history), 3, "開始日訂正と根拠追加の版数")
        refs = db.execute("""
            SELECT from_id, to_id, derived_from_id FROM sem_references WHERE kind = 'contradicts'
        """).fetchall()
        active = db.execute("""
            SELECT r.from_id, r.to_id, r.derived_from_id FROM sem_references r
            JOIN sem_heads s ON s.revision_id = r.from_id JOIN sem_heads o ON o.revision_id = r.to_id
            WHERE r.kind = 'contradicts'
        """).fetchall()
        equal(active, [(neg, contract_head, carried)], "分割後の反証先")
        equal((neg, changed, None) in refs and (neg, updated, ref_old) in refs, True, "旧・改訂版の参照")
        pending = db.execute("""
            SELECT count(*) FROM sem_holds WHERE kind = 'reference_pending' AND original_revision_id = ?
        """, (updated,)).fetchone()[0]
        equal(pending, 1, "分割後に保留した参照")

    remaining = {label: open_migrations(database(output, label)) for label in ("v1", "v2", "v3")}
    equal(remaining, {"v1": 1, "v2": 1, "v3": 0}, "保留の版をまたぐ解消")
    with closing(legacy.readonly(database(output, "v3"))) as db:
        decisions = db.execute("""
            SELECT state, definition_id, reason, resolution_revision_id, evidence_id
            FROM sem_decisions WHERE hold_id = ? ORDER BY state
        """, (hold,)).fetchall()
        equal(decisions, [
            ("open", v1_id, "旧資料だけでは保守契約か判断できない", None, None),
            ("resolved", v3_id, "新しい原本に契約番号が記載された", maintenance, new_evidence),
        ], "保留と解消の判断履歴")
        count = db.execute("""
            SELECT count(*) FROM sem_claims c JOIN sem_heads h ON h.claim_id = c.id
            JOIN sem_revisions r ON r.id = h.revision_id
            WHERE c.predicate = 'maintenance_contract' AND c.object_entity_id = ? AND r.state = 'accepted'
        """, (service,)).fetchone()[0]
        equal(count, 1, "最新版の確定した保守契約")
        equal(db.execute("SELECT count(*) FROM sem_definitions WHERE id IN (?, ?, ?)",
                         (v1_id, v2_id, v3_id)).fetchone()[0], 3, "旧定義の保持")
        equal(db.execute("""
            SELECT state, definition_id, evidence_id FROM sem_decisions
            WHERE hold_id = ? AND state = 'resolved'
        """, (ref_hold,)).fetchone(), ("resolved", v3_id, clarified), "反証の保留を解消した根拠")

    return {
        "releases": reports, "counts": observed,
        "customer_claim_revision_id": customer_rev,
        "references": {"before": changed, "after_evidence_added": updated, "trial": trial_head,
                       "contract": contract_head, "active_target": contract_head, "undecided": pending},
        "migration_remaining": remaining,
        "resolved": {"hold_id": hold, "target_revision_id": maintenance, "confirmed": count,
                     "initial_reason": decisions[0][2], "resolution_reason": decisions[1][2]},
    }
