"""作者が配布する AVX2 int8 ONNX を CPUExecutionProvider で比較する。"""
import os
import urllib.request
from pathlib import Path

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer


class Int8Reranker:
    def __init__(self, work: Path, model_id: str, revision: str):
        target = work / "onnx" / (model_id.split("/")[-1] + "-qint8-avx2.onnx")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            url = f"https://huggingface.co/{model_id}/resolve/{revision}/onnx/model_qint8_avx2.onnx"
            with urllib.request.urlopen(url, timeout=60) as response, target.with_suffix(".part").open("wb") as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
            target.with_suffix(".part").replace(target)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, cache_dir=str(work / "models"))
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(target), sess_options=options, providers=["CPUExecutionProvider"])
        self.inputs = {item.name for item in self.session.get_inputs()}

    def predict(self, pairs, show_progress_bar=False, batch_size=8):
        scores = []
        for start in range(0, len(pairs), batch_size):
            batch = pairs[start:start + batch_size]
            values = self.tokenizer([pair[0] for pair in batch], [pair[1] for pair in batch],
                                    padding=True, truncation=True, max_length=512, return_tensors="np")
            output = self.session.run(None, {key: value for key, value in values.items() if key in self.inputs})[0]
            scores.extend(output.reshape(-1).tolist())
        return np.asarray(scores)
