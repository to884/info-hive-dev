"""固定した箱の画像だけを MinerU へ渡し、主や正解を替えず別読みを得る。"""

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from PIL import Image, ImageOps

BENCH = Path(__file__).resolve().parent.parent
CORPUS = BENCH / "corpus"
OUT = CORPUS / "probe-v6-mineru"
RESULTS = BENCH / "results"
ROOT = BENCH.parents[2]
PACKAGES = Path("C:/Works/info-hive-dev-data/mineru-benchmark-env/Lib/site-packages")
MODEL_BASE = Path("C:/Works/info-hive-dev-data/mineru-benchmark/home/models")
MODEL = MODEL_BASE / "MinerU2.5-Pro-2605-1.2B-GGUF"
ENGINE = {"n_ctx_seq": 8192, "n_gpu_layers": 99, "n_parallel": 4, "n_threads": 4, "max_concurrency": 4, "verbosity": 3}
ENVIRONMENT = {"MINERU_HOME": str(OUT / "home"), "MINERU_MODEL_SOURCE": "local",
               "MINERU_TELEMETRY_DISABLED": "1", "MINERU_MODEL_ONNX_DEVICE": "gpu",
               "MINERU_LLAMA_CPP_BACKEND": "vulkan", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
NETWORK_ATTEMPTS = []


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, value, immutable=True):
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")
    if path.exists() and immutable:
        if path.read_bytes() != data:
            raise ValueError("既存の取得結果を上書きしない: " + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def guard_network(event, args):
    if event in ("socket.connect", "socket.getaddrinfo", "urllib.Request"):
        NETWORK_ATTEMPTS.append(event)
        save(OUT / "network-blocked.json", {"events": NETWORK_ATTEMPTS}, immutable=False)
        raise RuntimeError("この取得では Python の通信を許可しない")


def setup():
    os.environ.update(ENVIRONMENT)
    config = {"model": {"base_dir": str(MODEL_BASE), "source": "local", "onnx_device": "gpu",
                         "vlm": {"engine": "llama-cpp", "server_url": "", "max_concurrency": 4}}}
    save(OUT / "home/config.yaml", config)


def sampling():
    from mineru_vl_utils.mineru_client import _build_default_sampling_params
    params = _build_default_sampling_params("llama-cpp-engine")
    params["[default]"] = replace(params["[default]"], max_new_tokens=1024)
    return params


def profile():
    if Path(sys.executable).resolve() != (PACKAGES.parent.parent / "Scripts/python.exe").resolve():
        raise ValueError("指定した MinerU の環境で実行する必要がある")
    paths = [Path(__file__).resolve(), OUT / "home/config.yaml"]
    for name in ("mineru", "mineru_vl_utils", "mineru_llama_cpp", "docvortex", "PIL"):
        paths.extend(p for p in (PACKAGES / name).rglob("*") if p.is_file() and p.suffix.lower() in (".py", ".pyd", ".dll", ".so"))
    for name in ("mineru", "mineru-vl-utils", "mineru-llama-cpp", "docvortex", "pillow"):
        distribution = importlib.metadata.distribution(name)
        paths.extend(Path(distribution.locate_file(p)).resolve() for p in distribution.files or [] if Path(p).name in ("METADATA", "RECORD"))
    paths.extend(MODEL / name for name in ("MinerU2.5-Pro-2605-1.2B-Q8_0.gguf", "mmproj-MinerU2.5-Pro-2605-1.2B-Q8_0.gguf"))
    hardware = "unavailable"
    if command := shutil.which("nvidia-smi"):
        hardware = subprocess.check_output([command, "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"], encoding="utf-8").strip()
    return {"schema": "mineru-v6-row-profile-v1", "python": sys.version, "platform": platform.platform(),
            "hardware": hardware, "environment": ENVIRONMENT, "engine": ENGINE, "backend": "llama-cpp-engine",
            "model_path": str(MODEL), "padding": 4, "rotation": "none", "chunk_size": 32,
            "allow_truncated_content": False, "sampling": {k: asdict(v) for k, v in sampling().items()},
            "versions": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
            "external_files": {p.as_posix(): sha(p) for p in sorted(set(paths))}}


def crop(page, box):
    if len(box) != 4 or any(type(v) is not int for v in box):
        raise ValueError("主の箱が整数の 4 値でない")
    x, y, width, height = box
    if min(x, y) < 0 or min(width, height) < 1 or x + width > page.width or y + height > page.height:
        raise ValueError("主の箱が画像からはみ出している")
    return ImageOps.expand(page.crop((x, y, x + width, y + height)), border=4, fill="white")


def pixels_sha(image):
    return hashlib.sha256(str((image.height, image.width, 3)).encode("ascii") + image.tobytes()).hexdigest()


def request_record(key, index, line, image, profile_sha):
    return {"key": key, "line_index": index, "box": line["box"], "shape": [image.height, image.width, 3],
            "crop_sha256": pixels_sha(image), "profile_sha256": profile_sha}


def response_record(output):
    if isinstance(output, str):
        return {"response_kind": "text", "text": str(output)}
    if output is None:
        return {"response_kind": "no_text", "text": ""}
    if isinstance(output, Exception):
        return {"response_kind": "error", "text": None, "error_kind": type(output).__name__,
                "truncated": type(output).__name__ == "RequestError" and str(output) == "The output was truncated due to length limit.",
                "error_message_sha256": hashlib.sha256(str(output).encode("utf-8")).hexdigest()}
    raise TypeError("認識の返り値の型が契約と違う")


def valid_response(row):
    kind, text = row.get("response_kind"), row.get("text")
    return (kind == "text" and isinstance(text, str) or kind == "no_text" and text == ""
            or kind == "error" and text is None and isinstance(row.get("error_kind"), str))


def pilot_selection(manifest):
    keys = sorted(k for k, v in manifest.items() if v["side"] == "tuning" and k.startswith(("kanpo", "wp-")))
    if len(keys) != 15:
        raise ValueError("運転確認の 15 ページの範囲が違う")
    selected, all_boxes = set(), []
    for key in sorted(manifest):
        lines = load(CORPUS / "ocr3" / (key + ".json"))["lines"]
        if key in keys:
            if len(lines) < 6:
                raise ValueError("運転確認の先頭 6 行がない")
            selected.update((key, i) for i in range(6))
        for i, row in enumerate(lines):
            _, _, w, h = row["box"]
            all_boxes.append((key, i, w * h, max((w + 8) / (h + 8), (h + 8) / (w + 8))))
    for column in (2, 3):
        largest = min(all_boxes, key=lambda r: (-r[column], r[0], r[1]))
        selected.add((largest[0], largest[1]))
    return sorted(selected)


def freeze():
    before = profile()
    save(OUT / "profile.json", before)
    manifest_path = CORPUS / "probe-v4/manifest.json"
    method = BENCH.parent / "adr-0025-condition5-mineru-v6-2026-11-18.md"
    save_sources = [BENCH / "scripts" / name for name in ("collect_mineru_v6.py", "mineru_features_v6.py", "train_flags_v6.py", "test_mineru_v6.py", "diagnose_mineru_v6.py")]
    save_sources.append(method)
    prior = load(RESULTS / "v5-candidates.json")["inputs"]
    for name, digest in prior.items():
        if sha(ROOT / name) != digest:
            raise ValueError("前回の固定した入力が変わった")
    snapshot = OUT / "design-before-inference.md"
    if snapshot.exists() and snapshot.read_bytes() != method.read_bytes():
        raise ValueError("推論前の設計の写しを上書きしない")
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_bytes(method.read_bytes())
    save(RESULTS / "v6-acquisition-plan.json", {"profile_sha256": sha(OUT / "profile.json"),
        "sources": {p.relative_to(ROOT).as_posix(): sha(p) for p in save_sources}, "prior_inputs": prior,
        "manifest_sha256": sha(manifest_path), "snapshot_sha256": sha(snapshot),
        "pilot_rows": [{"key": k, "line_index": i} for k, i in pilot_selection(load(manifest_path))],
        "new_candidates": 38, "cumulative_candidates": 534, "classification_training_started": False})
    print("最初の推論前に取得・特徴・学習器を固定")


def checked_plan():
    plan = load(RESULTS / "v6-acquisition-plan.json")
    for name, digest in {**plan["prior_inputs"], **plan["sources"]}.items():
        if sha(ROOT / name) != digest:
            raise ValueError("最初の推論前から入力か設計が変わった")
    if sha(CORPUS / "probe-v4/manifest.json") != plan["manifest_sha256"] or sha(OUT / "profile.json") != plan["profile_sha256"]:
        raise ValueError("最初の推論前の取得条件が変わった")
    if sha(OUT / "design-before-inference.md") != plan["snapshot_sha256"]:
        raise ValueError("推論前の設計の写しが変わった")
    return plan


def row_path(key, index):
    return OUT / "rows" / key / f"{index:04d}.json"


def receipt_path(key, index):
    return OUT / "receipts" / key / f"{index:04d}.json"


def save_observation(value):
    path = row_path(value["key"], value["line_index"])
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")
    save(receipt_path(value["key"], value["line_index"]), {"row_sha256": hashlib.sha256(raw).hexdigest(),
         "profile_sha256": value["profile_sha256"], "crop_sha256": value["crop_sha256"]})
    save(path, value)


def update_counts(counts, key, side, rows):
    stratum = "public" if key.startswith(("kanpo", "wp-", "defense", "disaster")) else "synthetic"
    value = counts.setdefault(f"{side}-{stratum}", {"rows": 0, "empty": 0, "no_text": 0, "errors": 0, "truncated": 0})
    for row in rows:
        value["rows"] += 1
        value["empty"] += row["text"] == ""
        value["no_text"] += row["response_kind"] == "no_text"
        value["errors"] += row["response_kind"] == "error"
        value["truncated"] += bool(row.get("truncated"))


def checked_row(path, expected):
    value = load(path)
    if any(value.get(k) != v for k, v in expected.items()) or not valid_response(value):
        raise ValueError("保存した行の画像や取得条件が違う")
    receipt = load(receipt_path(expected["key"], expected["line_index"]))
    if receipt != {"row_sha256": sha(path), "profile_sha256": expected["profile_sha256"], "crop_sha256": expected["crop_sha256"]}:
        raise ValueError("最初の観測値の記録が違う")
    return value


def make_reader(before, profile_sha):
    from mineru.config import get_config
    from mineru.model.vlm.handles import RuntimeHandle
    from mineru_llama_cpp import Engine
    from mineru_vl_utils import MinerUClient
    if get_config().model.source != "local" or Path(get_config().model.base_dir).resolve() != MODEL_BASE.resolve():
        raise ValueError("ローカルの取得条件が有効でない")
    # 共有キャッシュの実体を書き換えず、このプロセスだけが所有する読み手を構築する。
    native = Engine(MODEL / "MinerU2.5-Pro-2605-1.2B-Q8_0.gguf", MODEL / "mmproj-MinerU2.5-Pro-2605-1.2B-Q8_0.gguf",
                    **{k: v for k, v in ENGINE.items() if k != "max_concurrency"})
    try:
        client = MinerUClient(backend="llama-cpp-engine", llama_cpp_engine=native, sampling_params=sampling(),
                              max_concurrency=4, use_tqdm=False)
    except BaseException:
        native.close()
        raise
    predictor = RuntimeHandle(client, backend="llama-cpp-engine", close_engine=native.close)
    try:
        client.client.allow_truncated_content = False
        if predictor.backend != "llama-cpp-engine" or client.client.allow_truncated_content:
            raise ValueError("明示したローカルの実行条件が違う")
        actual_sampling = {k: asdict(v) for k, v in client.sampling_params.items()}
        if actual_sampling != before["sampling"] or {k: asdict(v) for k, v in client.helper.sampling_params.items()} != actual_sampling:
            raise ValueError("実際の生成の条件が取得前と違う")
        save(OUT / "runtime.json", {"profile_sha256": profile_sha, "backend": predictor.backend,
                                    "sampling": actual_sampling, "allow_truncated_content": False,
                                    "client_concurrency": client.client.max_concurrency,
                                    "minimum_image_edge": client.helper.min_image_edge,
                                    "maximum_image_edge_ratio": client.helper.max_image_edge_ratio,
                                    "engine_parameters_requested": ENGINE})
    except BaseException:
        predictor.shutdown()
        raise
    return predictor


def read(pilot=False):
    plan = checked_plan()
    if not pilot and not (OUT / "pilot-summary.json").is_file():
        raise ValueError("本取得の前に運転確認を完了する必要がある")
    before = profile()
    save(OUT / "profile.json", before)
    profile_sha = sha(OUT / "profile.json")
    manifest = load(CORPUS / "probe-v4/manifest.json")
    selected = {(r["key"], r["line_index"]) for r in plan["pilot_rows"]}
    keys = sorted(set(k for k, i in selected) if pilot else manifest)
    predictor = make_reader(before, profile_sha)
    client = predictor.predictor
    total, newly_read, seconds = 0, 0, 0.0
    counts_by_group = {}
    started = time.monotonic()
    try:
        for key in keys:
            source = CORPUS / "ocr3" / (key + ".json")
            png = CORPUS / "probe-v4/png" / (key + ".png")
            if sha(source) != manifest[key]["ocr3_sha256"] or sha(png) != manifest[key]["png_sha256"]:
                raise ValueError("固定した主か画像が変わった")
            primary = load(source)["lines"]
            indices = [i for i in range(len(primary)) if not pilot or (key, i) in selected]
            with Image.open(png) as original:
                page = original.convert("RGB")
            jobs, rows = [], {}
            for i in indices:
                image = crop(page, primary[i]["box"])
                expected = request_record(key, i, primary[i], image, profile_sha)
                path = row_path(key, i)
                if path.exists():
                    rows[i] = checked_row(path, expected)
                else:
                    if receipt_path(key, i).exists():
                        raise ValueError("最初の観測の本文が失われているため再認識しない")
                    jobs.append((i, image, expected))
                if len(jobs) < 32 and i != indices[-1]:
                    continue
                if jobs:
                    tick = time.monotonic()
                    # ここに渡すものは PIL の画素だけであり、箱や ID、主の本文は渡さない。
                    if client.client.allow_truncated_content or {k: asdict(v) for k, v in client.helper.sampling_params.items()} != before["sampling"]:
                        raise ValueError("実際の生成条件が途中で変わった")
                    outputs = predictor.batch_recognize_text([j[1] for j in jobs])
                    elapsed = time.monotonic() - tick
                    if len(outputs) != len(jobs):
                        raise ValueError("別読みの出力数が画像数と違う")
                    for (index, _, expected_row), output in zip(jobs, outputs):
                        value = {**expected_row, **response_record(output), "batch_seconds": elapsed, "batch_size": len(jobs)}
                        save_observation(value)
                        rows[index] = value
                    newly_read += len(jobs)
                    seconds += elapsed
                    jobs = []
                    save(OUT / "status.json", {"key": key, "finished_in_page": len(rows), "page_total": len(indices),
                                                 "newly_read": newly_read, "inference_seconds": seconds, "pilot": pilot}, immutable=False)
            page.close()
            if not pilot:
                save(OUT / "reads" / (key + ".json"), {"profile_sha256": profile_sha, "primary_sha256": sha(source),
                     "image_sha256": sha(png), "lines": [rows[i] for i in range(len(primary))]})
            total += len(rows)
            update_counts(counts_by_group, key, manifest[key]["side"], rows.values())
            print(key, len(rows), "行、累計", total, flush=True)
    finally:
        predictor.shutdown()
    if NETWORK_ATTEMPTS or profile() != before or checked_plan() != plan:
        raise ValueError("通信の試みか取得条件の変化があった")
    save(OUT / ("pilot-summary.json" if pilot else "read-summary.json"), {
        "pages": len(keys), "rows": total, "newly_read": newly_read, "inference_seconds": seconds,
        "wall_seconds": time.monotonic() - started, "profile_sha256": profile_sha,
        "counts_by_group": counts_by_group, "network_attempts": NETWORK_ATTEMPTS})


def validate():
    plan = checked_plan()
    before = profile()
    if load(OUT / "profile.json") != before:
        raise ValueError("取得条件が変わった")
    manifest = load(CORPUS / "probe-v4/manifest.json")
    profile_sha = sha(OUT / "profile.json")
    coverage, inputs, counts, counts_by_group = {}, {}, {}, {}
    for key, record in sorted(manifest.items()):
        source = CORPUS / "ocr3" / (key + ".json")
        png = CORPUS / "probe-v4/png" / (key + ".png")
        target = OUT / "reads" / (key + ".json")
        primary, readings = load(source)["lines"], load(target)
        if readings["profile_sha256"] != profile_sha or readings["primary_sha256"] != record["ocr3_sha256"] or readings["image_sha256"] != record["png_sha256"]:
            raise ValueError("別読みと固定した主・画像の対応が違う")
        if len(readings["lines"]) != len(primary):
            raise ValueError("別読みの行数が違う")
        with Image.open(png) as original:
            page = original.convert("RGB")
        for i, line in enumerate(primary):
            image = crop(page, line["box"])
            expected = request_record(key, i, line, image, profile_sha)
            row = readings["lines"][i]
            if any(row.get(k) != v for k, v in expected.items()) or not valid_response(row):
                raise ValueError("別読みの行と画素が違う")
            if checked_row(row_path(key, i), expected) != row:
                raise ValueError("学習へ渡す読みが最初の観測と違う")
        page.close()
        for path, digest in ((source, record["ocr3_sha256"]), (png, record["png_sha256"])):
            if sha(path) != digest:
                raise ValueError("主か画像が変わった")
        for path in (source, png, target):
            inputs[path.relative_to(BENCH).as_posix()] = sha(path)
        coverage[key] = {"rows": len(primary), "read_sha256": sha(target), "primary_sha256": sha(source), "image_sha256": sha(png)}
        count = counts.setdefault(record["side"], {"pages": 0, "rows": 0, "empty": 0, "no_text": 0, "errors": 0})
        count["pages"] += 1
        count["rows"] += len(primary)
        count["empty"] += sum(r["text"] == "" for r in readings["lines"])
        count["no_text"] += sum(r["response_kind"] == "no_text" for r in readings["lines"])
        count["errors"] += sum(r["response_kind"] == "error" for r in readings["lines"])
        update_counts(counts_by_group, key, record["side"], readings["lines"])
    if len(coverage) != 300 or sum(c["rows"] for c in counts.values()) != 15658:
        raise ValueError("全ページ・全行がそろっていない")
    for path in (OUT / "profile.json", OUT / "runtime.json", OUT / "design-before-inference.md", RESULTS / "v6-acquisition-plan.json", Path(__file__).resolve()):
        inputs[path.relative_to(BENCH).as_posix()] = sha(path)
    if before != profile() or NETWORK_ATTEMPTS or checked_plan() != plan:
        raise ValueError("検証中に取得条件か通信の状態が変わった")
    save(RESULTS / "v6-mineru-coverage.json", {"schema": "mineru-v6-row-coverage-v1", "source_root": "corpus/probe-v6-mineru",
        "coverage": coverage, "counts": counts, "profile_sha256": profile_sha, "inputs": inputs,
        "external_files": before["external_files"], "counts_by_group": counts_by_group, "runtime_enabled": False})
    print("MinerU 全行の結び付きを検証", counts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "pilot", "read", "validate"))
    args = parser.parse_args()
    setup()
    sys.addaudithook(guard_network)
    {"freeze": freeze, "pilot": lambda: read(True), "read": read, "validate": validate}[args.mode]()
