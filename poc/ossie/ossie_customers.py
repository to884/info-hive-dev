"""Ossie の型付き実行結果を使う、顧客と根拠のローカル照会。"""

from datetime import date
import json

from export_wiki_graph import VERSION, ident
from ossie_adapter import metric_results


VIEW_FIELDS = {
    "entity": ("WikiEntity", "name entity_type wiki_id"),
    "definition": ("WikiDefinition", "rules_json wiki_id"),
    "claim": ("WikiClaim", "predicate subject_entity_id object_entity_id polarity qualifier wiki_id"),
    "head": ("WikiClaimHead", "claim_id revision_id"),
    "revision": ("WikiClaimRevision", "claim_id definition_id state intervals_json"),
    "reference": ("WikiRevisionReference", "kind from_id to_id"),
    "hold": ("WikiHold", "product_id kind candidates_json wiki_id"),
    "decision": ("WikiHoldDecision", "hold_id state"),
    "support": ("WikiEvidenceLink", "revision_id evidence_id kind"),
}

DATASET = "customer_evidence"


def metrics_document():
    columns = ("customer_id", "claim_id", "evidence_id")
    return {
        "version": VERSION,
        "name": "Info Hive Wiki Customer Metrics",
        "description": "対象時点の顧客主張に根拠を結合した行から計数する。",
        "datasets": [{
            "name": DATASET, "source": DATASET,
            "fields": [{"name": name, "datatype": "String",
                        "expression": {"sql": f"source.{ident(name)}"}} for name in columns],
        }],
        "metrics": [
            {"name": name, "expression": {"sql": f"COUNT(DISTINCT {DATASET}.{column})"}}
            for name, column in zip(("customers", "claims", "evidence"), columns)
        ],
    }


# 期間は [開始, 終了)。現在の定義との互換、反証と未解決を判定し、根拠はその後で結合する。
CLASSIFY = """
CREATE OR REPLACE TEMP TABLE customer_scope AS
WITH query AS (SELECT ?::VARCHAR AS wiki_id, ?::VARCHAR AS product, ?::VARCHAR AS def, ?::DATE AS day),
current_rows AS (
    SELECT c.id AS claim_id, r.id AS revision_id, c.subject_entity_id AS customer_id,
           c.predicate, c.polarity, c.qualifier, r.state, a.rules_json AS prior, d.rules_json AS current,
           CASE WHEN json_array_length(r.intervals_json) = 0 THEN 'unknown'
                WHEN EXISTS (
                    SELECT 1 FROM json_each(r.intervals_json) p
                    WHERE json_extract_string(p.value, '$[0]')::DATE <= q.day
                      AND (json_extract_string(p.value, '$[1]') IS NULL
                           OR q.day < json_extract_string(p.value, '$[1]')::DATE)
                ) THEN 'inside' ELSE 'outside' END AS timing
    FROM claim c JOIN head h ON h.claim_id = c.id
    JOIN revision r ON r.id = h.revision_id AND r.claim_id = c.id
    JOIN definition a ON a.id = r.definition_id
    CROSS JOIN query q JOIN definition d ON d.id = q.def AND d.wiki_id = q.wiki_id
    WHERE c.wiki_id = q.wiki_id AND c.object_entity_id = q.product
      AND r.state IN ('accepted', 'candidate', 'disputed')
),
compatible AS (
    SELECT *,
        CASE json_type(prior, '$.predicates')
          WHEN 'ARRAY' THEN EXISTS (
              SELECT 1 FROM json_each(prior, '$.predicates') p
              WHERE json_extract_string(p.value, '$') = 'customer_of')
          WHEN 'OBJECT' THEN json_exists(prior, '$.predicates.customer_of')
          ELSE false END AS prior_declares,
        CASE json_type(current, '$.predicates')
          WHEN 'ARRAY' THEN EXISTS (
              SELECT 1 FROM json_each(current, '$.predicates') p
              WHERE json_extract_string(p.value, '$') = 'customer_of')
          WHEN 'OBJECT' THEN json_exists(current, '$.predicates.customer_of')
          ELSE false END AS current_declares
    FROM current_rows
),
heads AS (
    SELECT *, prior_declares AND current_declares AS applicable
    FROM compatible
),
pending AS (
    SELECT h.kind, json_extract_string(p.value, '$') AS revision_id
    FROM hold h CROSS JOIN query q LEFT JOIN LATERAL json_each(h.candidates_json) p ON true
    WHERE h.wiki_id = q.wiki_id AND (h.product_id IS NULL OR h.product_id = q.product)
      AND NOT EXISTS (SELECT 1 FROM decision d WHERE d.hold_id = h.id AND d.state = 'resolved')
),
opponents AS (
    SELECT a.revision_id,
           bool_or(b.state <> 'candidate' AND b.timing = 'inside') AS disputed,
           bool_or(b.state = 'candidate' OR b.timing = 'unknown') AS unresolved
    FROM heads a JOIN heads b ON b.polarity = 'negative' AND b.timing <> 'outside'
    WHERE a.predicate = 'customer_of' AND a.polarity = 'positive' AND (
        (b.predicate = a.predicate AND b.applicable
         AND b.customer_id IS NOT DISTINCT FROM a.customer_id
         AND b.qualifier IS NOT DISTINCT FROM a.qualifier)
        OR EXISTS (
            SELECT 1 FROM reference r WHERE r.kind = 'contradicts'
              AND ((r.from_id = a.revision_id AND r.to_id = b.revision_id)
                OR (r.from_id = b.revision_id AND r.to_id = a.revision_id))
        )
    )
    GROUP BY a.revision_id
),
reasons AS (
    SELECT a.claim_id, a.revision_id, a.customer_id,
           CASE WHEN NOT coalesce(a.applicable, false) THEN ['migration_pending']
                WHEN a.state = 'candidate' THEN ['claim_candidate']
                WHEN a.state = 'disputed' THEN ['disputed']
                WHEN coalesce(o.disputed, false) OR coalesce(o.unresolved, false) OR p.revision_id IS NOT NULL THEN
                    list_concat(
                        CASE WHEN coalesce(o.disputed, false) THEN ['disputed'] ELSE [] END,
                        CASE WHEN coalesce(o.unresolved, false) OR p.revision_id IS NOT NULL
                             THEN ['reference_pending'] ELSE [] END)
                WHEN a.timing = 'unknown' THEN ['unknown_valid_time']
                ELSE [] END AS limitations
    FROM heads a LEFT JOIN opponents o USING (revision_id)
    LEFT JOIN (SELECT DISTINCT revision_id FROM pending WHERE kind = 'reference_pending') p USING (revision_id)
    WHERE a.predicate = 'customer_of' AND a.polarity = 'positive' AND a.timing <> 'outside'
)
SELECT claim_id, revision_id, customer_id, limitations FROM reasons
UNION ALL
SELECT NULL, NULL, NULL, [kind] FROM pending
"""


def set_views(adapter):
    for view, (concept, fields) in VIEW_FIELDS.items():
        adapter.concept_view(view, concept, fields.split())
    db = adapter.db
    # この照会プロファイルの定義には、述語名と任意の null だけを許す。
    # SemaSynth の任意の定義は型付きリンクの照合にだけ使う。
    for (rules_json,) in db.execute("SELECT rules_json FROM definition").fetchall():
        rules = json.loads(rules_json)
        predicates = rules.get("predicates") if isinstance(rules, dict) else None
        valid = (isinstance(predicates, list) and all(isinstance(v, str) for v in predicates)
                 or isinstance(predicates, dict) and all(v is None for v in predicates.values()))
        if not valid or rules.keys() != {"predicates"}:
            raise ValueError("顧客照会で評価できる定義は述語名の列挙に限ります")

    for sql, description in (
        ("""SELECT h.id FROM head h LEFT JOIN revision r ON r.id = h.revision_id
              WHERE h.claim_id IS NULL OR r.claim_id IS DISTINCT FROM h.claim_id""", "現行版の主張 ID"),
        ("SELECT id FROM revision WHERE intervals_json IS NULL", "有効期間の表現"),
        ("""SELECT id FROM claim WHERE predicate = 'customer_of'
              AND (subject_entity_id IS NULL OR object_entity_id IS NULL)""", "顧客主張の実体"),
        ("SELECT id FROM support WHERE evidence_id IS NULL OR revision_id IS NULL", "根拠リンクの両端"),
    ):
        if db.execute(sql).fetchone():
            raise ValueError(f"顧客照会に必要な値が一致しません: {description}")


def evaluate_customer(adapter, metrics_path, wiki_id, definition_id, product_id, day):
    if date.fromisoformat(day).isoformat() != day:
        raise ValueError("照会日は YYYY-MM-DD で指定してください")
    release = adapter.release
    if not release or (release["wiki_id"], release["definition_id"]) != (wiki_id, definition_id):
        raise ValueError("wiki または定義の版が読み込んだバンドルと一致しません")
    db = adapter.db
    if not db.execute("""
        SELECT 1 FROM entity e JOIN definition d ON e.wiki_id = d.wiki_id
        WHERE e.id = ? AND e.entity_type = 'product' AND e.wiki_id = ? AND d.id = ?
    """, (product_id, wiki_id, definition_id)).fetchone():
        raise ValueError("指定した wiki・定義・製品の組み合わせを解決できません")
    db.execute(CLASSIFY, (wiki_id, product_id, definition_id, day))
    db.execute(f"""
        CREATE OR REPLACE TEMP TABLE {DATASET} AS
        SELECT c.customer_id, c.claim_id, s.evidence_id
        FROM customer_scope c LEFT JOIN support s ON s.revision_id = c.revision_id AND s.kind = 'supports'
        WHERE len(c.limitations) = 0
    """)
    metrics = metric_results(db, metrics_path, DATASET)
    ids = db.execute(f"SELECT DISTINCT customer_id FROM {DATASET} ORDER BY customer_id").fetchall()
    limitations = db.execute("""
        SELECT DISTINCT item FROM customer_scope, UNNEST(limitations) t(item) ORDER BY item
    """).fetchall()
    joined = db.execute(f"SELECT count(*) FROM {DATASET}").fetchone()[0]
    return {**metrics, "customer_ids": [row[0] for row in ids],
            "limitations": [row[0] for row in limitations]}, joined
