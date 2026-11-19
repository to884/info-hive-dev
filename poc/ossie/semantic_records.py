"""一方向 PoC の意味レコードと、隔離した版の遷移。"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from hashlib import sha256
import json


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# キーが列名、値が対応する Ossie の型。各表の id は wiki の範囲を含む。
TABLES = {
    "definitions": ("WikiDefinition", {"name": "String", "description": "String", "rules_json": "String"}),
    "entities": ("WikiEntity", {"name": "String", "entity_type": "String", "page": "String",
                                "page_sha256": "String", "aliases_json": "String"}),
    "articles": ("WikiArticle", {"title": "String", "page": "String", "page_sha256": "String"}),
    "claims": ("WikiClaim", {
        "predicate": "String", "subject_entity_id": "WikiEntity", "subject_article_id": "WikiArticle",
        "object_entity_id": "WikiEntity", "object_article_id": "WikiArticle",
        "polarity": "String", "qualifier": "String",
    }),
    "revisions": ("WikiClaimRevision", {
        "claim_id": "WikiClaim", "definition_id": "WikiDefinition", "previous_id": "WikiClaimRevision",
        "state": "String", "intervals_json": "String", "recorded_at": "String", "details_json": "String",
    }),
    "heads": ("WikiClaimHead", {"claim_id": "WikiClaim", "revision_id": "WikiClaimRevision"}),
    "evidence": ("WikiEvidence", {
        "article_id": "WikiArticle", "quote": "String", "raw_ref": "String", "raw_sha256": "String",
        "verification": "String", "original_source": "String", "method": "String",
    }),
    "supports": ("WikiEvidenceLink", {
        "revision_id": "WikiClaimRevision", "evidence_id": "WikiEvidence", "kind": "String",
    }),
    "references": ("WikiRevisionReference", {
        "kind": "String", "from_id": "WikiClaimRevision", "to_id": "WikiClaimRevision",
        "derived_from_id": "WikiRevisionReference", "evidence_id": "WikiEvidence", "reason": "String",
    }),
    "record_references": ("WikiRecordReference", {
        "kind": "String", "from_id": "WikiClaimRevision", "to_entity_id": "WikiEntity",
        "to_article_id": "WikiArticle", "original_value": "String",
    }),
    "holds": ("WikiHold", {
        "definition_id": "WikiDefinition", "original_revision_id": "WikiClaimRevision",
        "original_reference_id": "WikiRevisionReference", "product_id": "WikiEntity",
        "kind": "String", "reference_kind": "String", "candidates_json": "String",
    }),
    "decisions": ("WikiHoldDecision", {
        "hold_id": "WikiHold", "definition_id": "WikiDefinition", "state": "String", "reason": "String",
        "resolution_revision_id": "WikiClaimRevision", "evidence_id": "WikiEvidence",
        "actor": "String", "recorded_at": "String",
    }),
    "legacy_refs": ("WikiLegacyReference", {
        "snapshot": "String", "legacy_kind": "String", "legacy_id": "String", "entity_id": "WikiEntity",
        "article_id": "WikiArticle", "revision_id": "WikiClaimRevision", "disposition": "String",
    }),
}

STATES = {"candidate", "accepted", "disputed", "withdrawn", "superseded"}


def checked_intervals(intervals: list) -> list:
    """空のリストは時点不明。None の終了日は明示的な開放端。"""
    normalized = []
    for start, end in intervals:
        if start != date.fromisoformat(start).isoformat():
            raise ValueError("日付は YYYY-MM-DD で指定してください")
        if end is not None and (end != date.fromisoformat(end).isoformat() or start >= end):
            raise ValueError("有効期間の終了は開始より後の日付を指定してください")
        normalized.append([start, end])
    return sorted(normalized, key=lambda pair: (pair[0], pair[1] or "9999-12-31"))


class Trial:
    def __init__(self, wiki_id: str):
        if not wiki_id.strip():
            raise ValueError("wiki_id が空です")
        self.wiki_id = wiki_id
        self.rows = {table: {} for table in TABLES}
        self.definition_id = None
        self.parent_release = None
        self._last_release = None

    def key(self, table: str, key) -> str:
        return sha256(canonical([self.wiki_id, table, key]).encode("utf-8")).hexdigest()

    def put(self, table: str, key, **values) -> str:
        pk = self.key(table, key)
        fields = TABLES[table][1]
        if values.keys() - fields.keys():
            raise ValueError(f"{table} の未知の列: {values.keys() - fields.keys()}")
        row = {"id": pk, "wiki_id": self.wiki_id, **{name: values.get(name) for name in fields}}
        previous = self.rows[table].setdefault(pk, row)
        if previous != row:
            raise ValueError(f"{table} の固定レコードが衝突しました: {pk}")
        return pk

    def definition(self, name, description, rules):
        self.definition_id = self.put(
            "definitions", [name, description, rules], name=name, description=description,
            rules_json=canonical(rules),
        )
        return self.definition_id

    def entity(self, key, name, entity_type, *, page=None, page_sha256=None, aliases=()):
        return self.put("entities", key, name=name, entity_type=entity_type, page=page,
                        page_sha256=page_sha256, aliases_json=canonical(sorted(set(aliases))))

    def article(self, key, title, page, page_sha256):
        return self.put("articles", key, title=title, page=page, page_sha256=page_sha256)

    def add_evidence(self, article_id, quote, *, raw_ref=None, raw_sha256=None, original_source=None,
                     method, verification):
        return self.put("evidence", [article_id, original_source, quote, raw_ref, raw_sha256],
                        article_id=article_id, quote=quote, raw_ref=raw_ref, raw_sha256=raw_sha256,
                        verification=verification, original_source=original_source, method=method)

    def endpoint(self, entity_or_article: str) -> str:
        if entity_or_article in self.rows["entities"]:
            return "entity_id"
        if entity_or_article in self.rows["articles"]:
            return "article_id"
        raise ValueError("実体または記事の参照先がありません")

    def claim(self, predicate, subject, obj, *, polarity="positive", qualifier=None):
        if polarity not in {"positive", "negative", "unknown"}:
            raise ValueError("主張の極性が不明です")
        return self.put("claims", [predicate, subject, obj, polarity, qualifier], predicate=predicate,
                        **{f"subject_{self.endpoint(subject)}": subject, f"object_{self.endpoint(obj)}": obj},
                        polarity=polarity, qualifier=qualifier)

    def current(self, claim_id) -> str | None:
        row = self.rows["heads"].get(self.key("heads", claim_id))
        return row["revision_id"] if row else None

    def revise(self, claim_id, *, state, evidence=(), intervals=(), details=None, recorded_at=None,
               inherit_references=False):
        previous = self.current(claim_id)
        if claim_id not in self.rows["claims"] or state not in STATES or self.definition_id is None:
            raise ValueError("主張・定義・状態を確認してください")
        normalized = checked_intervals(intervals)
        support = sorted(set(evidence))
        if any(eid not in self.rows["evidence"] or kind not in {"supports", "opposes", "context"}
               for eid, kind in support):
            raise ValueError("根拠の参照先がありません")
        if state == "accepted" and not any(kind == "supports" for _, kind in support):
            raise ValueError("主張の確定には支持する根拠が必要です")
        values = dict(claim_id=claim_id, definition_id=self.definition_id, state=state,
                      intervals_json=canonical(normalized), details_json=canonical(details or {}))
        if previous:
            old = self.rows["revisions"][previous]
            if all(old[key] == value for key, value in values.items()) and self.support(previous) == support:
                return previous
            equivalent = (all(old[key] == value for key, value in values.items())
                          and set(self.support(previous)) <= set(support))
            if inherit_references and not equivalent:
                raise ValueError("根拠の追加以外の改訂では反証先を再評価してください")
        new = self.put("revisions", [values, previous, support, recorded_at], previous_id=previous,
                       recorded_at=recorded_at, **values)
        head = self.key("heads", claim_id)
        self.rows["heads"][head] = {"id": head, "wiki_id": self.wiki_id,
                                     "claim_id": claim_id, "revision_id": new}
        for eid, kind in support:
            self.put("supports", [new, eid, kind], revision_id=new, evidence_id=eid, kind=kind)
        if previous:
            self.reference("supersedes", new, previous, reason="同じ主張の新版")
            self.retarget_references(previous, [new], {}, equivalent=equivalent)
        return new

    def support(self, revision_id):
        return sorted((row["evidence_id"], row["kind"]) for row in self.rows["supports"].values()
                      if row["revision_id"] == revision_id)

    def reference(self, kind, from_id, to_id, *, original=None, evidence_id=None, reason):
        if kind not in {"supersedes", "contradicts"} or from_id == to_id:
            raise ValueError("履歴の参照の種類または対象が不正です")
        if evidence_id is not None and evidence_id not in self.rows["evidence"]:
            raise ValueError("履歴の判断根拠がありません")
        for revision_id in (from_id, to_id):
            if revision_id not in self.rows["revisions"]:
                raise ValueError("履歴の参照先の版がありません")
        return self.put("references", [kind, from_id, to_id, original, evidence_id, reason], kind=kind,
                        from_id=from_id, to_id=to_id, derived_from_id=original,
                        evidence_id=evidence_id, reason=reason)

    def contradictions(self, revision_id):
        current = {head["revision_id"] for head in self.rows["heads"].values()}
        return [
            row for row in self.rows["references"].values()
            if row["kind"] == "contradicts"
            and ((row["from_id"] == revision_id and row["to_id"] in current)
                 or (row["to_id"] == revision_id and row["from_id"] in current))
        ]

    def transfer_reference(self, ref, previous, new, evidence, reason):
        return self.reference(
            ref["kind"], new if ref["from_id"] == previous else ref["from_id"],
            new if ref["to_id"] == previous else ref["to_id"], original=ref["id"],
            evidence_id=evidence, reason=reason,
        )

    def retarget_references(self, previous, successors, decisions, *, equivalent=False):
        claim = self.rows["claims"][self.rows["revisions"][previous]["claim_id"]]
        for ref in self.contradictions(previous):
            if equivalent:
                self.transfer_reference(ref, previous, successors[0], ref["evidence_id"], "同じ命題への根拠追加")
            elif ref["id"] in decisions:
                chosen, evidence, reason = decisions[ref["id"]]
                self.transfer_reference(ref, previous, chosen, evidence, reason)
            else:
                self.open_hold("reference_pending", previous, "反証先を再評価する",
                               product_id=claim["object_entity_id"], source_reference=ref["id"],
                               candidates=successors)

    def transition_reference_evidence(self, ref, chosen):
        linked = {eid for revision in (ref["from_id"], ref["to_id"], chosen)
                  for eid, _ in self.support(revision)}
        return linked | ({ref["evidence_id"]} - {None})

    def resolve_reference(self, hold_id, target, evidence_id, reason):
        hold = self.rows["holds"][hold_id]
        if hold["kind"] != "reference_pending" or evidence_id not in self.rows["evidence"] or not reason.strip():
            raise ValueError("反証の保留と判断根拠を指定してください")
        ref = self.rows["references"].get(hold["original_reference_id"])
        if target is not None:
            # 解消先は、保留時の候補のうち現行の版に限る。
            if not ref or target not in json.loads(hold["candidates_json"]):
                raise ValueError("保留されていた反証の候補版を指定してください")
            other = ref["to_id"] if ref["from_id"] == hold["original_revision_id"] else ref["from_id"]
            if any(self.current(self.rows["revisions"][rev]["claim_id"]) != rev for rev in (target, other)):
                raise ValueError("反証の両端に現行の主張の版を指定してください")
        decision = self.put("decisions", [hold_id, "resolved"], hold_id=hold_id,
                            definition_id=self.definition_id, state="resolved", reason=reason,
                            resolution_revision_id=target, evidence_id=evidence_id)
        if target is not None:
            self.transfer_reference(ref, hold["original_revision_id"], target, evidence_id, reason)
        return decision

    def record_reference(self, kind, source, target, value):
        endpoint = self.endpoint(target)
        return self.put("record_references", [kind, source, target], kind=kind, from_id=source,
                        original_value=value, **{f"to_{endpoint}": target})

    def split(self, original, successors, decisions):
        """反証ごとの判断を入力にし、指定された後継だけを結ぶ。"""
        old_claim = self.rows["revisions"][original]["claim_id"]
        if self.current(old_claim) != original:
            raise ValueError("分割元は現行版を指定してください")
        successors = set(successors)
        claim = self.rows["claims"][old_claim]
        roles = ("subject_entity_id", "subject_article_id", "object_entity_id", "object_article_id")
        if len(successors) < 2 or any(
            self.rows["revisions"][rev]["claim_id"] == old_claim
            or self.current(self.rows["revisions"][rev]["claim_id"]) != rev
            or self.rows["revisions"][rev]["definition_id"] != self.definition_id
            or any(self.rows["claims"][self.rows["revisions"][rev]["claim_id"]][role] != claim[role]
                   for role in roles)
            for rev in successors
        ):
            raise ValueError("分割先には同じ実体を対象とする現行の主張を2件以上指定してください")
        refs = {ref["id"]: ref for ref in self.contradictions(original)}
        if set(decisions) - refs.keys() or any(
            chosen not in successors or not reason.strip()
            or evidence not in self.transition_reference_evidence(refs[ref_id], chosen)
            for ref_id, (chosen, evidence, reason) in decisions.items()
        ):
            raise ValueError("反証の移行先・判断根拠が分割案と一致しません")
        for revision in sorted(successors):
            self.reference("supersedes", revision, original, reason="意味を分割")
        self.retarget_references(original, sorted(successors), decisions)
        del self.rows["heads"][self.key("heads", old_claim)]

    def open_hold(self, kind, original, reason, *, product_id=None, source_reference=None,
                  candidates=(), reference_key=None, actor=None, recorded_at=None):
        origin = self.rows["revisions"][original]["definition_id"] if original else self.definition_id
        hold = self.put("holds", [kind, original, source_reference, origin, product_id, reference_key],
                        definition_id=origin,
                        original_revision_id=original, original_reference_id=source_reference,
                        product_id=product_id, kind=kind, reference_kind=reference_key,
                        candidates_json=canonical(sorted(candidates)))
        self.put("decisions", [hold, "open"], hold_id=hold, definition_id=self.definition_id,
                 state="open", reason=reason, actor=actor, recorded_at=recorded_at)
        return hold

    def resolve_hold(self, hold_id, target, evidence_id, reason, *, actor=None, recorded_at=None):
        hold = self.rows["holds"][hold_id]
        revision = self.rows["revisions"][target]
        claim = self.rows["claims"][revision["claim_id"]]
        original = hold["original_revision_id"]
        old_claim = self.rows["revisions"][original]["claim_id"] if original else None
        if (
            revision["definition_id"] != self.definition_id or revision["state"] != "accepted"
            or self.current(revision["claim_id"]) != target
            or (evidence_id, "supports") not in self.support(target) or not reason.strip()
            or (hold["product_id"] and hold["product_id"] != claim["object_entity_id"])
            or (old_claim and self.rows["claims"][old_claim]["subject_entity_id"] != claim["subject_entity_id"])
            or hold["kind"] != "migration_pending"
        ):
            raise ValueError("保留先には現行定義の確定済みの版と根拠を指定してください")
        decision = self.put("decisions", [hold_id, "resolved"], hold_id=hold_id,
                            definition_id=self.definition_id, state="resolved", reason=reason,
                            resolution_revision_id=target, evidence_id=evidence_id,
                            actor=actor, recorded_at=recorded_at)
        if original and target != original:
            self.reference("supersedes", target, original, evidence_id=evidence_id, reason=reason)
            if old_claim != revision["claim_id"] and self.current(old_claim) == original:
                self.retarget_references(original, [target], {})
                del self.rows["heads"][self.key("heads", old_claim)]
        return decision

    def freeze(self):
        """同じ内容では ID が変わらない。出力した版は後続の遷移で変更しない。"""
        rows = {name: [records[id].copy() for id in sorted(records)] for name, records in self.rows.items()}
        state = self.key("release_state", [self.definition_id, rows])
        if self._last_release and self._last_release[0] == state:
            return self._last_release[1].copy(), rows
        release = self.key("release", [self.definition_id, self.parent_release, rows])
        manifest = {"wiki_id": self.wiki_id, "release_id": release, "definition_id": self.definition_id,
                    "parent_release_id": self.parent_release}
        self.parent_release = release
        self._last_release = (state, manifest.copy())
        return manifest, rows
