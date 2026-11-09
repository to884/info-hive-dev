"""36 件の結果から、機械で出せる指標と、人が対応づけるための表を作る。

意味の対応づけ（どの候補が同じ知見か、どの新規ページが同じページか）は推測しない。
ここで出すのは、文字列として確かめられることだけである。

使い方:
    python tabulate.py --snapshot-root <dir>

出力（リポジトリ）:
    runs/<run_id>.json              1 件ごとの結果。引用を行番号とハッシュに置き換える
    metrics/mechanical.json, metrics/mechanical.md
    mapping/<資料>-candidates.csv   候補の一覧（実行を伏せた ID つき。人が cluster_id などを埋める）。引用を伏せる
    mapping/<資料>-pages.csv        新しく作るページの一覧（人が page_cluster を埋める）
    mapping/blind-key.csv           伏せた ID と実行の対応（対応づけが終わるまで見ない）
出力（リポジトリの外、PRIVATE）:
    mapping/<資料>-candidates.csv   引用を伏せない版
    mapping/<資料>-raw-lines.md     照合に使う原文の行番号つきの写し
"""
from __future__ import annotations

import argparse
import csv
import os
import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent
# 生の記録はリポジトリの外にある（run_poc.py と同じ場所）。
PRIVATE = Path(os.environ.get("POC_PRIVATE_DIR") or Path.home() / "info-hive-dev-private" / RUN_DIR.name)
# 公開リポジトリに原文の引用を載せない資料。O は Medium の会員限定記事、R と V は非公開の SemaSynth の記録である。
REDACT_SOURCES = {"O", "R", "V"}
SOURCES = ("O", "R", "V")
METHODS = ("current", "hybrid")
MODELS = ("opus", "sol")

# 条件を表す語。根拠の行にこれがあり、conditions が空なら「脱落の疑い」として人に回す。
COND_JA = re.compile(r"では|場合|とき|時に|前提|限り|のみ|だけ|以外|異なる|同一|条件|範囲|保証|ない限り|未実|未確認|推測")
COND_EN = re.compile(r"\b(if|when|unless|only|under|assum\w*|provided|except|until|whether)\b", re.I)


# ---------------------------------------------------------------------------
# 引用の照合（page-conventions.md の「引用の書き方」の照合規則に合わせる）
# ---------------------------------------------------------------------------

def _is_word(ch: str) -> bool:
    return ch.isascii() and ch.isalnum()


def norm(text: str) -> str:
    """大文字と小文字を吸収し、空白を 1 つにし、英数字どうしの間以外の空白を消す。全角と半角は区別する。"""
    t = re.sub(r"\s+", " ", text.lower()).strip()
    out = []
    for i, ch in enumerate(t):
        if ch == " ":
            prev = t[i - 1] if i > 0 else ""
            nxt = t[i + 1] if i + 1 < len(t) else ""
            if not (_is_word(prev) and _is_word(nxt)):
                continue
        out.append(ch)
    return "".join(out)


PUNCT = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "—": "-", "–": "-", "`": ""})


def check_quote(quote: str, raw_lines: list[str], ls: int | None, le: int | None) -> dict:
    """引用が原本にあるかと、示した行にあるかを確かめる。"""
    q = norm(quote or "")
    whole = norm("\n".join(raw_lines))
    res = {"found": False, "found_loose": False, "in_cited_lines": False}
    if not q:
        return res
    res["found"] = q in whole
    res["found_loose"] = res["found"] or q.translate(PUNCT) in whole.translate(PUNCT)
    if isinstance(ls, int) and isinstance(le, int) and 1 <= ls <= le <= len(raw_lines) + 1:
        lo, hi = max(1, ls - 1), min(len(raw_lines), le + 1)  # 1 行のずれは許す
        seg = norm("\n".join(raw_lines[lo - 1:hi]))
        res["in_cited_lines"] = q in seg or q.translate(PUNCT) in seg.translate(PUNCT)
    return res


# ---------------------------------------------------------------------------

def load_runs() -> list[dict]:
    runs = []
    for p in sorted((PRIVATE / "runs").glob("*.json")):
        runs.append(json.loads(p.read_text(encoding="utf-8")))
    return runs


def candidates(run: dict) -> list[dict]:
    return list(((run.get("plan") or {}).get("candidates")) or [])


def dest_kind(c: dict) -> str:
    a = c.get("action")
    if a == "source_only":
        return "source_only"
    t, k = c.get("page_type"), c.get("page_kind")
    if t == "concept" and k == "claim":
        return f"claim_{a}"
    if t == "concept" and (c.get("section") or "").startswith("###"):
        return f"section_{a}"
    return f"{t}_{a}"


def created_pages(run: dict) -> list[dict]:
    pages = ((run.get("plan") or {}).get("pages")) or []
    return [p for p in pages if p.get("action") == "create" and p.get("type") != "source"]


def updated_existing(run: dict) -> set[str]:
    pages = ((run.get("plan") or {}).get("pages")) or []
    return {p.get("slug") for p in pages if p.get("action") == "update" and p.get("type") != "source"}


def usage_summary(run: dict) -> dict:
    u = run.get("usage") or {}
    if run.get("vendor") == "claude":
        uu = u.get("usage") or {}
        return {"cost_usd": u.get("total_cost_usd"),
                "input_tokens": sum(uu.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                                             "cache_read_input_tokens")),
                "output_tokens": uu.get("output_tokens")}
    return {"cost_usd": None, "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens")}


def jaccard(a: set, b: set) -> float | None:
    if not a and not b:
        return None
    return len(a & b) / len(a | b)


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), 3) if xs else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-root", required=True, type=Path)
    args = ap.parse_args()
    manifest = json.loads((RUN_DIR / "snapshots" / "manifest.json").read_text(encoding="utf-8"))
    raws = {}
    for s in SOURCES:
        src = manifest["sources"][s]
        raw = args.snapshot_root / src["snapshot"] / src["raw_rel"]
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == src["raw_sha256"], f"原本のハッシュが違う: {raw}"
        raws[s] = raw.read_text(encoding="utf-8").splitlines()

    runs = load_runs()
    per_run = []
    for r in runs:
        cs = candidates(r)
        raw_lines = raws[r["source"]]
        dk = Counter(dest_kind(c) for c in cs)
        q_total = q_found = q_loose = q_loc = 0
        not_found, cond_flags = [], []
        n_cond_empty = 0
        for c in cs:
            ev = c.get("evidence") or []
            if not (c.get("conditions") or []):
                n_cond_empty += 1
            ev_text = []
            for e in ev:
                q_total += 1
                chk = check_quote(e.get("quote", ""), raw_lines, e.get("line_start"), e.get("line_end"))
                q_found += chk["found"]
                q_loose += chk["found_loose"]
                q_loc += chk["in_cited_lines"]
                if not chk["found_loose"]:
                    not_found.append({"cand": c.get("id"), "quote": e.get("quote")})
                ls, le = e.get("line_start"), e.get("line_end")
                if isinstance(ls, int) and isinstance(le, int):
                    ev_text.extend(raw_lines[max(0, ls - 1):min(len(raw_lines), le)])
            joined = "\n".join(ev_text)
            if not (c.get("conditions") or []) and (COND_JA.search(joined) or COND_EN.search(joined)):
                cond_flags.append(c.get("id"))
        cp = created_pages(r)
        u = usage_summary(r)
        per_run.append({
            "run_id": r["run_id"], "source": r["source"], "method": r["method"], "model_key": r["model_key"],
            "rep": r["rep"], "ok": r.get("ok"), "error": (r.get("error") or "")[:200],
            "n_candidates": len(cs),
            "n_source_only": dk.get("source_only", 0),
            "source_only_ratio": round(dk.get("source_only", 0) / len(cs), 3) if cs else None,
            "dest_kinds": dict(dk),
            "n_pages_created": len(cp),
            "n_concept_created": sum(1 for p in cp if p.get("type") == "concept"),
            "n_claim_created": sum(1 for p in cp if p.get("type") == "concept" and p.get("kind") == "claim"),
            "n_entity_created": sum(1 for p in cp if p.get("type") == "entity"),
            "created_slugs": sorted(p.get("slug") or "" for p in cp),
            "updated_existing": sorted(x for x in updated_existing(r) if x),
            "n_quotes": q_total, "n_quotes_found": q_found, "n_quotes_found_loose": q_loose,
            "n_quotes_in_cited_lines": q_loc, "quotes_not_found": not_found,
            "n_conditions_empty": n_cond_empty, "cond_dropout_suspects": cond_flags,
            "n_outside_snapshot": len(r.get("outside_snapshot") or []),
            "outside_snapshot": r.get("outside_snapshot") or [],
            "n_files_read": len(r.get("files_read") or []), "n_tool_calls": r.get("n_tool_calls"),
            "elapsed_s": r.get("elapsed_s"), **u,
        })

    # 文字列として一致するものだけの一致率（意味の一致ではない）
    agree = []
    for s in SOURCES:
        for m in METHODS:
            group = [x for x in per_run if x["source"] == s and x["method"] == m and x["ok"]]
            for a, b in combinations(group, 2):
                kind = ("同じモデルの別の回" if a["model_key"] == b["model_key"] else "別のモデル")
                agree.append({
                    "source": s, "method": m, "pair": f"{a['run_id']}~{b['run_id']}", "kind": kind,
                    "updated_existing_jaccard": jaccard(set(a["updated_existing"]), set(b["updated_existing"])),
                    "created_slug_jaccard": jaccard(set(a["created_slugs"]), set(b["created_slugs"])),
                })

    groups = []
    for s in SOURCES:
        for m in METHODS:
            for mk in MODELS + ("all",):
                g = [x for x in per_run if x["source"] == s and x["method"] == m and x["ok"]
                     and (mk == "all" or x["model_key"] == mk)]
                if not g:
                    continue
                ag = [a for a in agree if a["source"] == s and a["method"] == m]
                groups.append({
                    "source": s, "method": m, "model": mk, "n_runs": len(g),
                    "candidates": [x["n_candidates"] for x in g],
                    "source_only_ratio_mean": mean(x["source_only_ratio"] for x in g),
                    "concept_created": [x["n_concept_created"] for x in g],
                    "claim_created": [x["n_claim_created"] for x in g],
                    "entity_created": [x["n_entity_created"] for x in g],
                    "quotes_not_found": sum(x["n_quotes"] - x["n_quotes_found_loose"] for x in g),
                    "quotes_total": sum(x["n_quotes"] for x in g),
                    "quotes_off_location": sum(x["n_quotes_found_loose"] - x["n_quotes_in_cited_lines"] for x in g),
                    "conditions_empty": sum(x["n_conditions_empty"] for x in g),
                    "cond_dropout_suspects": sum(len(x["cond_dropout_suspects"]) for x in g),
                    "outside_snapshot_runs": sum(1 for x in g if x["n_outside_snapshot"]),
                    "updated_existing_jaccard_mean": (mean(a["updated_existing_jaccard"] for a in ag)
                                                      if mk == "all" else None),
                    "created_slug_jaccard_mean": mean(a["created_slug_jaccard"] for a in ag) if mk == "all" else None,
                    "cost_usd_sum": round(sum(x["cost_usd"] or 0 for x in g), 2),
                    "input_tokens_sum": sum(x["input_tokens"] or 0 for x in g),
                    "output_tokens_sum": sum(x["output_tokens"] or 0 for x in g),
                    "elapsed_s_mean": mean(x["elapsed_s"] for x in g),
                })

    out = RUN_DIR / "metrics"
    out.mkdir(exist_ok=True)
    (out / "mechanical.json").write_text(json.dumps({"per_run": per_run, "groups": groups, "pairs": agree},
                                                    ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    write_markdown(out / "mechanical.md", per_run, groups)
    write_mapping(runs, raws, manifest)
    write_public_runs(runs)
    print(f"runs={len(runs)} ok={sum(1 for x in per_run if x['ok'])}")


def write_markdown(path: Path, per_run: list[dict], groups: list[dict]) -> None:
    L = ["# 機械で出した指標", "",
         "`scripts/tabulate.py` が `runs/` から作った。意味の対応づけは含まない。一致率は、既存のページのスラッグ、"
         "または新規のページのスラッグが**文字列として**一致したものだけを数えた参考値である。", "",
         "## 資料 × 方式 × モデル", "",
         "| 資料 | 方式 | モデル | 件数 | 候補の数 | source_only の割合 | concept の新規 | うち claim | entity の新規 "
         "| 引用が原本にない / 引用の数 | 引用の行がずれた | 条件が空 | 条件の脱落の疑い | 外のパス | 既存の更新先の Jaccard "
         "| 新規スラッグの Jaccard | 費用 USD | 入力トークン | 出力トークン | 平均の秒 |",
         "| --- | --- | --- | ---: | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: "
         "| ---: | ---: | ---: | ---: |"]
    for g in groups:
        L.append("| {source} | {method} | {model} | {n_runs} | {c} | {sor} | {cc} | {cl} | {en} | {qn} / {qt} | {qo} "
                 "| {ce} | {cd} | {os} | {uj} | {cj} | {cost} | {it:,} | {ot:,} | {el} |".format(
                     source=g["source"], method=g["method"], model=g["model"], n_runs=g["n_runs"],
                     c=",".join(map(str, g["candidates"])), sor=g["source_only_ratio_mean"],
                     cc=",".join(map(str, g["concept_created"])), cl=",".join(map(str, g["claim_created"])),
                     en=",".join(map(str, g["entity_created"])), qn=g["quotes_not_found"], qt=g["quotes_total"],
                     qo=g["quotes_off_location"], ce=g["conditions_empty"], cd=g["cond_dropout_suspects"],
                     os=g["outside_snapshot_runs"],
                     uj="" if g["updated_existing_jaccard_mean"] is None else g["updated_existing_jaccard_mean"],
                     cj="" if g["created_slug_jaccard_mean"] is None else g["created_slug_jaccard_mean"],
                     cost=g["cost_usd_sum"] or "", it=g["input_tokens_sum"], ot=g["output_tokens_sum"],
                     el=g["elapsed_s_mean"]))
    L += ["", "数の列（候補の数、concept の新規など）は、回ごとの値をカンマで並べた。", "",
          "## 実行ごと", "",
          "| run_id | ok | 候補 | 行き先の内訳 | 新規ページ | 更新する既存ページ | 引用（原本にある / 数） | 外のパス |",
          "| --- | --- | ---: | --- | --- | --- | --- | ---: |"]
    for x in per_run:
        L.append(f"| {x['run_id']} | {x['ok']} | {x['n_candidates']} | "
                 + ", ".join(f"{k} {v}" for k, v in sorted(x["dest_kinds"].items()))
                 + f" | {'、'.join(x['created_slugs'])} | {'、'.join(x['updated_existing'])} | "
                 f"{x['n_quotes_found_loose']} / {x['n_quotes']} | {x['n_outside_snapshot']} |")
    nf = [(x["run_id"], q) for x in per_run for q in x["quotes_not_found"]]
    L += ["", "## 原本に見つからなかった引用", "",
          "記号（引用符、ダッシュ）の違いを吸収したうえで、原本に見つからなかったもの。捏造かどうかは人が確かめる。", ""]
    L += [f"- {rid} {q['cand']}: 「{q['quote']}」" for rid, q in nf] or ["- なし"]
    osd = [(x["run_id"], h) for x in per_run for h in x["outside_snapshot"]]
    L += ["", "## スナップショットの外を指したツールの呼び出し", ""]
    L += [f"- {rid}: `{h}`" for rid, h in osd] or ["- なし"]
    path.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def write_mapping(runs: list[dict], raws: dict, manifest: dict) -> None:
    out = RUN_DIR / "mapping"
    out.mkdir(exist_ok=True)
    # 実行を伏せる。順番は run_id の SHA-256 で決め、資料ごとに 01〜12 を振る。
    key_rows = []
    blind = {}
    for s in SOURCES:
        rs = sorted([r for r in runs if r["source"] == s],
                    key=lambda r: hashlib.sha256(("poc-2026-11-09:" + r["run_id"]).encode()).hexdigest())
        for i, r in enumerate(rs, 1):
            blind[r["run_id"]] = f"{s}-{i:02d}"
            key_rows.append({"blind_id": f"{s}-{i:02d}", "run_id": r["run_id"], "method": r["method"],
                             "model": r["model"], "rep": r["rep"]})
    with (out / "blind-key.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(key_rows[0]))
        w.writeheader()
        w.writerows(key_rows)

    for s in SOURCES:
        raw_lines = raws[s]
        rows, page_rows = [], {}
        for r in runs:
            if r["source"] != s:
                continue
            for c in candidates(r):
                ev = c.get("evidence") or []
                checks = [check_quote(e.get("quote", ""), raw_lines, e.get("line_start"), e.get("line_end"))
                          for e in ev]
                first = min((e.get("line_start") for e in ev if isinstance(e.get("line_start"), int)), default=9999)
                rows.append({
                    "blind_id": blind[r["run_id"]], "cand_id": c.get("id"), "first_line": first,
                    "lines": "; ".join(f"L{e.get('line_start')}-{e.get('line_end')}" for e in ev),
                    "subject": c.get("subject"), "claim": c.get("claim"),
                    "conditions": " / ".join(c.get("conditions") or []), "epistemic": c.get("epistemic"),
                    "quotes": " / ".join(e.get("quote") or "" for e in ev),
                    "quote_check": " / ".join("原本にある" if k["found_loose"] else "原本にない" for k in checks),
                    "action": c.get("action"), "page_type": c.get("page_type"), "page_kind": c.get("page_kind"),
                    "page_slug": c.get("page_slug"), "section": c.get("section"),
                    "cluster_id": "", "faithful": "", "conditions_kept": "", "memo": "",
                })
            for p in created_pages(r):
                k = (blind[r["run_id"]], p.get("slug"))
                page_rows[k] = {"blind_id": k[0], "slug": p.get("slug"), "title": p.get("title"),
                                "type": p.get("type"), "kind": p.get("kind"),
                                "candidate_ids": ",".join(p.get("candidate_ids") or []), "page_cluster": ""}
        rows.sort(key=lambda x: (x["first_line"], x["blind_id"], str(x["cand_id"])))
        prs = sorted(page_rows.values(), key=lambda x: (x["type"] or "", x["slug"] or "", x["blind_id"]))
        page_fields = ["blind_id", "slug", "title", "type", "kind", "candidate_ids", "page_cluster"]
        # 人が埋める版（リポジトリの外、引用を伏せない）
        priv = PRIVATE / "mapping"
        priv.mkdir(parents=True, exist_ok=True)
        if rows:
            write_csv_guarded(priv / f"{s}-candidates.csv", rows, "cluster_id")
        write_csv_guarded(priv / f"{s}-pages.csv", prs, "page_cluster", page_fields)
        # 記録の版（リポジトリ）。候補の本文は原文をほぼ写すので載せず、行き先と行番号だけを残す
        if rows:
            keep = ["blind_id", "cand_id", "first_line", "lines", "epistemic", "quote_check",
                    "action", "page_type", "page_kind", "page_slug"]
            pub = [{k: x[k] for k in keep} for x in rows]
            write_csv(out / f"{s}-candidates.csv", pub, keep)
        write_csv(out / f"{s}-pages.csv", prs, page_fields)
        src = manifest["sources"][s]
        md = [f"# {src['title']}（{s}）の原文", "",
              f"原本 `{src['raw_rel']}`（sha256 `{src['raw_sha256']}`）の写し。候補の照合に使う行番号を付けた。",
              "公開リポジトリには入れない。", ""]
        for i, line in enumerate(raw_lines, 1):
            md.append(f"`L{i}` {line}" if line.strip() else f"`L{i}`")
            md.append("")
        (priv / f"{s}-raw-lines.md").write_text("\n".join(md), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


HUMAN_COLUMNS = ("cluster_id", "faithful", "conditions_kept", "memo", "page_cluster")


def write_csv_guarded(path: Path, rows: list[dict], fill_col: str, fields: list[str] | None = None) -> None:
    """人が埋め始めた表は上書きしない。そのときは .new.csv に書く。

    人が書く列（HUMAN_COLUMNS）のどれか 1 つでも埋まっていれば、埋め始めたとみなす。
    fill_col は表の主な列で、表にその列がなければ書き損じとして止める。
    """
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            existing = list(reader)
            cols = [c for c in HUMAN_COLUMNS if c in (reader.fieldnames or [])]
        if fill_col not in cols:
            raise SystemExit(f"{path} に {fill_col} の列がない。手で直した表かもしれないので上書きしない")
        if any((row.get(c) or "").strip() for row in existing for c in cols):
            path = path.with_suffix(".new.csv")
    write_csv(path, rows, fields)


def redact_run(run: dict) -> dict:
    """公開用の記録。

    モデルは知見（claim）を原文に近い言い回しで書くので、引用だけを伏せても原文が漏れる。
    候補の本文（subject、claim、conditions、reason、引用）を落とし、行き先、区分、条件の数、
    根拠の行と引用のハッシュだけを残す。最終メッセージの全文も落とす。全文はリポジトリの外にある。
    """
    r = json.loads(json.dumps(run, ensure_ascii=False))
    if r["source"] not in REDACT_SOURCES:
        return r
    final = r.get("final_text") or ""
    r["final_text_sha256"] = hashlib.sha256(final.encode("utf-8")).hexdigest()
    r["final_text"] = "（伏せた。全文はリポジトリの外の runs/ にある）"
    plan = r.get("plan") or {}
    slim = []
    for c in plan.get("candidates") or []:
        slim.append({
            "id": c.get("id"), "epistemic": c.get("epistemic"), "n_conditions": len(c.get("conditions") or []),
            "evidence": [{"line_start": e.get("line_start"), "line_end": e.get("line_end"),
                          "quote_sha256": hashlib.sha256((e.get("quote") or "").encode("utf-8")).hexdigest(),
                          "quote_chars": len(e.get("quote") or "")} for e in c.get("evidence") or []],
            "action": c.get("action"), "page_slug": c.get("page_slug"), "page_type": c.get("page_type"),
            "page_kind": c.get("page_kind"), "has_section": bool(c.get("section")),
        })
    plan["candidates"] = slim
    plan.pop("pages_read", None)
    return r


def write_public_runs(runs: list[dict]) -> None:
    out = RUN_DIR / "runs"
    out.mkdir(exist_ok=True)
    for r in runs:
        (out / f"{r['run_id']}.json").write_text(json.dumps(redact_run(r), ensure_ascii=False, indent=2) + "\n",
                                                 encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
