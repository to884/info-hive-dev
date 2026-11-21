"""保存票で枠内・境界上のコンマ候補を保留する追加ルールを比較する。"""

from collections import Counter
from hashlib import sha256
from pathlib import Path
import json


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
V100 = HERE.parent / "v100-separator-role-second-look"
V99 = HERE.parent / "v99-filter-components-before-agreement"
MODELS = ("gpt", "claude")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify(path, digest):
    if sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"保存資料のハッシュが一致しない: {path}")


def fixed_inputs():
    integrity = load(V100 / "integrity.json")
    lock_path = V100 / "lock.json"
    base_path = V100 / "comparison.json"
    verify(lock_path, integrity["lock_sha256"])
    verify(base_path, integrity["comparison_sha256"])
    lock = load(lock_path)
    for path, digest in lock["files"].items():
        verify(REPO_ROOT / path, digest)
    for path, digest in integrity["formal_hashes"].items():
        verify(REPO_ROOT / path, digest)
    delivery = next(REPO_ROOT / path for path in integrity["formal_hashes"] if path.endswith("packages.json"))
    attachments = 0
    for pack_id, pack in load(delivery)["packs"].items():
        request = pack["request"]
        for name, digest in zip(request["images"], request["image_sha256"], strict=True):
            verify(delivery.parent / "cards" / pack_id / name, digest)
            attachments += 1
    if attachments != integrity["formal_audit_attachments_verified"]:
        raise ValueError("正式監査の添付点数が一致しない")
    comparison = load(base_path)
    if len(comparison["cases"]) != 16 or (comparison["saved_votes"], comparison["new_role_votes"]) != (64, 32):
        raise ValueError("再集計する枠数・保存票数が一致しない")
    return comparison, load(V99 / "replay-result.json"), attachments


def blocked_components(kept, roles):
    commas = [{str(ident) for _, mark, ident in kept[model] if mark == ","} for model in MODELS]
    both_noise = {ident for ident, role in roles.items() if role == "X"}
    return {
        "either_transcription": sorted(both_noise & (commas[0] | commas[1])),
        "both_transcriptions": sorted(both_noise & commas[0] & commas[1]),
    }


def replay(comparison, replay_v99):
    rows = {}
    for row, case in comparison["cases"].items():
        votes = replay_v99["cases"][row + "/new"]["votes"]
        kept = {m: votes[m]["kept"] for m in MODELS}
        ids = {str(ident) for candidates in kept.values() for _, _, ident in candidates}
        roles = {}
        for ident in ids:
            gpt, claude = (case["parsed"][m][ident] for m in MODELS)
            roles[ident] = gpt if gpt == claude else "U"
        if roles != case["agreed_roles"]:
            raise ValueError(f"保存した役割二票と集計の不一致: {row}")
        blocked = blocked_components(kept, roles)
        before = case["verdict"]["pair"]
        # XをUに変える経路では、元の確定を保留にすることだけが可能。
        after = {rule: ["unresolved"] if ids else before for rule, ids in blocked.items()}
        # 正解カテゴリと採点は行判定が終わってから報告用に取り出す。
        rows[row] = {
            "group": case["group"], "v99": case["saved"]["pair"], "v100": before,
            **after, "blocked": blocked,
            "v100_final": case["final"]["pair"],
        }
    return rows


def counts(rows):
    groups = ("inside", "edge", "outside", "no-comma")
    fields = ("same", "omitted", "extra", "unresolved")
    versions = ("v99", "v100", "either_transcription", "both_transcriptions")
    scopes = {"all": list(rows.values())}
    for group in groups:
        scopes[group] = [entry for entry in rows.values() if entry["group"] == group]
    scopes["v99-extra"] = [entry for entry in rows.values() if "extra" in entry["v99"]]
    result = {}
    for scope, entries in scopes.items():
        result[scope] = {}
        for version in versions:
            per_outcome = Counter(outcome for entry in entries for outcome in entry[version])
            result[scope][version] = {name: per_outcome[name] for name in fields}
    return result


def main():
    base, original, attachments = fixed_inputs()
    rows = replay(base, original)
    result = {
        "frames": 16, "saved_transcription_votes": 64, "saved_role_votes": 32,
        "new_image_reads": 0, "formal_attachments_verified": attachments,
        "counts": counts(rows), "rows": rows,
    }
    output = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path = HERE / "comparison.json"
    if path.exists() and path.read_text(encoding="utf-8") != output:
        raise ValueError("再計算が保存済みの集計と一致しない")
    if not path.exists():
        path.write_text(output, encoding="utf-8", newline="\n")
    print(json.dumps(result["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()

