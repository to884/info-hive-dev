"""回答位置に合わせず、既存の全ページ抽出から自然な分割の評価索引を作る。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
from rag_config import Config, write_json
from rag_pdf import chunks_for

WORK = ROOT / ".rag-poc-data/natural-20261104"
CACHE = ROOT / ".rag-poc-data/model-cache"
OUT = ROOT / "docs/research/rag-validation-remaining-2026-11-04"


def prepare():
    old = (Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04").resolve()
    manifest = json.loads((old / "sample-manifest.json").read_text(encoding="utf-8"))
    pages = defaultdict(list)
    for line in (old / "pages.jsonl").open(encoding="utf-8"):
        row = json.loads(line)
        pages[row["sample"]].append({"page": row["page"], "text": row["text"]})
    config = Config({"embedding_model":"cl-nagoya/ruri-v3-30m"})
    rows, documents = [], []
    for sample, values in sorted(pages.items()):
        name = manifest["files"][sample]["relative_path"]
        doc_id = f"sample-{sample}"
        title = Path(name).stem
        chunks = chunks_for(sorted(values, key=lambda p:p["page"]), title, config)
        documents.append({"doc_id":doc_id,"title":title,"relative_path":name,"pages":len(values),"chunks":len(chunks)})
        rows.extend({**chunk,"doc_id":doc_id,"title":title,"label":f"{doc_id}:p{chunk['page']}"} for chunk in chunks)
    fixed = ROOT / "info-hive-wiki/eval/retrieval/ja/corpus/wiki"
    import re
    import unicodedata
    for path in sorted(fixed.rglob("*.md")):
        if path.name == "SCHEMA.md":
            continue
        title = unicodedata.normalize("NFC", path.stem)
        text = re.sub(r"\A---.*?\n---\s*", "", path.read_text(encoding="utf-8-sig"), flags=re.S)
        chunks = chunks_for([{"page":1,"text":text}], title, config)
        doc_id = "wiki:" + title
        documents.append({"doc_id":doc_id,"title":title,"relative_path":path.relative_to(fixed).as_posix(),"pages":1,"chunks":len(chunks)})
        rows.extend({**chunk,"doc_id":doc_id,"title":title,"label":title} for chunk in chunks)
    queries = [q for q in json.loads((ROOT / "info-hive-wiki/eval/retrieval/ja/queries.json").read_text(encoding="utf-8")) if q["expected"]]
    queries += json.loads((Path(__file__).with_name("reviewed-queries.json")).read_text(encoding="utf-8"))
    labels = {row["label"] for row in rows}
    assert all(set(q["expected"]) <= labels for q in queries)
    # 存在しない識別子の定義を聞く。一般的な分野外質問の棄却性能とは区別する。
    for number in range(12):
        token = "IH-ABSENT-" + hashlib.sha256(f"20261104:{number}".encode()).hexdigest()[:20]
        assert all(token not in row["text"] for row in rows)
        queries.append({"id":f"negative-{number:02}","query":f"資料中の識別子「{token}」に定義されている{'検索設定値' if number%2 else '手順と制約'}を教えてください。", "expected":[],"negative_kind":"absent_identifier"})
    WORK.mkdir(parents=True, exist_ok=True)
    write_json(WORK / "corpus.json", {"rows":rows,"documents":documents,"queries":queries,"source_root":manifest["root"],"native_text_only":True})
    write_json(OUT / "natural-corpus.json", {"pdf_documents":len(pages),"pdf_pages":sum(map(len,pages.values())),"documents":len(documents),"chunks":len(rows),"positive_queries":len(queries)-12,"negative_queries":12,"forced_answer_chunks":0,"ocr_included":False,"sha256":hashlib.sha256((WORK/'corpus.json').read_bytes()).hexdigest()})


def embed(device):
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    if device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA が利用できません。")
        torch.cuda.set_per_process_memory_fraction(.3)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    data = json.loads((WORK / "corpus.json").read_text(encoding="utf-8"))
    cfg = Config({"embedding_model":"cl-nagoya/ruri-v3-30m"})
    model = SentenceTransformer(cfg.model, revision=cfg.revision, cache_folder=str(CACHE), device=device, model_kwargs={"attn_implementation":"sdpa"})
    model.max_seq_length = 2048
    texts = ["検索文書: " + row["embedding_text"] for row in data["rows"]]
    lengths = [len(v) for v in model.tokenizer(texts, truncation=False, padding=False)["input_ids"]]
    assert max(lengths) <= 2048
    order = np.argsort(lengths)
    target = WORK / "vectors.npy"
    result = np.lib.format.open_memmap(target, mode="w+", dtype=np.float32, shape=(len(texts),cfg.dimension))
    started = time.perf_counter()
    for start in range(0,len(order),128):
        selected = order[start:start+128]
        result[selected] = model.encode([texts[i] for i in selected], normalize_embeddings=True, batch_size=8, show_progress_bar=False)
        result.flush()
        print(json.dumps({"completed":start+len(selected),"total":len(texts),"seconds":time.perf_counter()-started}),flush=True)
    write_json(WORK / "embedding-meta.json", {"device":device,"model":cfg.model,"revision":cfg.revision,"seconds":time.perf_counter()-started,"max_tokens":max(lengths),"dimension":cfg.dimension})


def index():
    import numpy as np
    from rag_index import Engine
    data = json.loads((WORK / "corpus.json").read_text(encoding="utf-8"))
    wiki = WORK / "wiki"
    (wiki / "sources").mkdir(parents=True, exist_ok=True)
    (wiki / "SCHEMA.md").write_text("# 自然分割の評価\n",encoding="utf-8")
    values = {"reference_roots":{"books":data["source_root"]},"data_dir":str(WORK/'data'),"model_cache_dir":str(CACHE),"embedding_model":"cl-nagoya/ruri-v3-30m","cpu_threads":4,"reranker":"off"}
    write_json(WORK / "config.json", values)
    cfg = Config(values)
    engine = Engine(cfg)
    folder = cfg.workspace(str(wiki))
    engine._check_policy(folder)
    table = engine._table(folder, create=True)
    if table.count_rows():
        raise RuntimeError("評価索引は作成済みです。既存データを上書きしません。")
    vectors = np.load(WORK / "vectors.npy", mmap_mode="r")
    for start in range(0,len(data["rows"]),512):
        batch = []
        for number,row in enumerate(data["rows"][start:start+512], start):
            generation = hashlib.sha256((row["doc_id"]+cfg.fingerprint).encode()).hexdigest()
            batch.append({"chunk_id":f"{generation}:{number}","doc_id":row["doc_id"],"generation":generation,"page":row["page"],"section":row["section"],"title":row["title"],"text":row["text"],"terms":engine.tokenize(row["embedding_text"]),"vector":vectors[number].tolist()})
        table.add(batch)
    table.create_fts_index("terms",base_tokenizer="whitespace",stem=False,remove_stop_words=False,ascii_folding=False)
    with engine._catalog(folder) as conn:
        for doc in data["documents"]:
            generation = hashlib.sha256((doc["doc_id"]+cfg.fingerprint).encode()).hexdigest()
            conn.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?)",(doc["doc_id"],generation,doc["title"],"books",doc["relative_path"],doc["pages"],doc["chunks"],cfg.fingerprint,time.time()))
            conn.execute("INSERT INTO citations VALUES (?,?)",(doc["doc_id"],"sources/"+doc["doc_id"].replace(":","-")+".md"))
    write_json(WORK / "index-complete.json", {"rows":table.count_rows(),"note":"製品 Engine の検索形式へ評価用の抽出済み本文を投入。PDF 取り込み E2E とは別。"})


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("stage",choices=["prepare","embed","index"])
    parser.add_argument("--device",choices=["cpu","cuda"],default="cuda")
    args=parser.parse_args()
    if args.stage == "prepare": prepare()
    elif args.stage == "embed": embed(args.device)
    else: index()
