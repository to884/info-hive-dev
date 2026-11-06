"""E5 の補足: Windows で Tantivy の commit が PermissionDenied で失敗したときに、文書が失われるかを確かめる。

write_safety.py の (d) と (d2) で、commit の一部が「アクセスが拒否されました (os error 5)」で失敗した。
読み手がいなくても起きる。失敗した後も writer を使い続けると、その後の commit が成功を返しても文書が索引に残らない。
ここでは 1 つの書き手だけで、次の 3 通りを比べる。

- 0.2 秒ごとに 50 件を commit し、失敗しても何もしない
- 同じ頻度で、失敗したら rollback して同じ 50 件を入れ直す（最大 6 回）
- 間を空けずに commit し、同じく rollback して入れ直す
"""
from __future__ import annotations

import shutil
import time

from decision_common import DWORK, save

CASES = [(0.2, 60, False), (0.2, 60, True), (0.0, 20, True)]


def run(folder, interval, seconds, recover):
    import tantivy
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    builder = tantivy.SchemaBuilder()
    builder.add_integer_field("id", stored=True, fast=True)
    builder.add_text_field("terms", stored=False, tokenizer_name="ws", index_option="freq")
    index = tantivy.Index(builder.build(), path=str(folder))
    index.register_tokenizer("ws", tantivy.TextAnalyzerBuilder(tantivy.Tokenizer.whitespace()).build())
    writer = index.writer(heap_size=100_000_000, num_threads=1)
    n, commits, errors, retries_ok, gave_up, messages = 0, 0, 0, 0, 0, set()
    ends = time.time() + seconds
    while time.time() < ends:
        batch = range(n, n + 50)
        n += 50
        for attempt in range(6):
            try:
                for i in batch:
                    writer.add_document(tantivy.Document(id=i, terms="税 所得"))
                writer.commit()
                commits += 1
                retries_ok += bool(attempt)
                break
            except Exception as error:
                errors += 1
                messages.add(f"{type(error).__name__}: {error}"[:160])
                if not recover:
                    break
                try:
                    writer.rollback()
                except Exception:
                    pass
                time.sleep(0.05 * (attempt + 1))
        else:
            gave_up += 1
        time.sleep(interval)
    writer.wait_merging_threads()
    index.reload()
    docs = index.searcher().num_docs
    return {"interval_seconds": interval, "seconds": seconds, "recover": recover, "commits": commits, "errors": errors,
            "error_rate": errors / max(1, commits + errors), "retries_ok": retries_ok, "gave_up": gave_up,
            "docs_in_index": docs, "docs_added": n, "lost": n - docs, "messages": sorted(messages)}


def main():
    results = []
    for interval, seconds, recover in CASES:
        result = run(DWORK / "write-safety/tantivy-retry", interval, seconds, recover)
        results.append(result)
        print({k: v for k, v in result.items() if k != "messages"}, flush=True)
    recovered = [r for r in results if r["recover"]]
    save("tantivy-commit-retry.json", {
        "purpose": "Windows で Tantivy の commit が失敗したときに文書が失われるか。rollback して入れ直せば失われないか",
        "results": results,
        "passed": all(r["lost"] == 0 and r["gave_up"] == 0 for r in recovered),
        "criterion": "rollback して入れ直す 2 通りで、失われた文書 0、諦めた batch 0",
        "note": "原因（ウイルス対策の走査など）は切り分けていない。読み手がいなくても起きる"})


if __name__ == "__main__":
    main()
