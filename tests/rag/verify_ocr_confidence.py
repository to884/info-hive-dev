"""OCR の確信度の受け取り（rag_ocr_confidence）を、本物の NDLOCR-Lite で確かめる（ADR-0025 の試験 8 の一部）。

CI では NDLOCR-Lite を読み込めないので、手元の rag の OCR の環境（uv の rag-ocr-*）の Python で動かす。

    <rag-ocr の環境の python.exe> -X utf8 tests/rag/verify_ocr_confidence.py

1. 本物の process_cascade に、長さを決めたスタブの読み手を渡す（モデルは要らない）。読み直しの境目（25、45 文字）と、
   長い行を左右に分けて読む場合（98 文字以上）を通し、行の記録が不変条件（文字の確率の数が本文の文字の数、
   終わりの記号の確率の数が読みの数以下）を満たすことを確かめる。
2. 本物の 3 つの認識器で、合成の行の画像を読み、包んだ読み（ConfidentRecognizer）と元の read の文字列が同じこと、
   確率が 0〜1 であることを確かめる。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag" / "scripts"))

import ocr  # noqa: E402  NDLOCR-Lite
from rag_ocr_confidence import ConfidentRecognizer, ProbStr, line_records  # noqa: E402


class LengthReader:
    """画像の幅（ピクセル）を、読んだ文字の数として返すスタブ。確率は 0.9 と、終わりの記号 0.8 にする。"""

    def __init__(self, limit: int, name: str):
        self.limit, self.name, self.calls = limit, name, 0

    def read(self, img):
        self.calls += 1
        length = min(img.shape[1], self.limit)
        eos = [0.8] if length < self.limit else []
        return ProbStr(self.name[0] * length, [0.9] * length, eos, 1)


def check_cascade() -> None:
    readers = (LengthReader(30, "a"), LengthReader(50, "b"), LengthReader(100, "c"))
    # 予測した文字の数（pred_char_cnt）と、画像の幅（= スタブが読む文字の数）の組
    cases = [(3, 10), (3, 24), (3, 25), (2, 44), (2, 45), (1, 97), (1, 98), (1, 150)]
    lines = [ocr.RecogLine(np.zeros((10, width, 3), dtype=np.uint8), index, count) for index, (count, width) in enumerate(cases)]
    results = ocr.process_cascade(lines, *readers, is_cascade=True)
    records = line_records([{"text": text, "boundingBox": [[0, 0], [0, 1], [1, 0], [1, 1]], "confidence": 0.5}
                            for text in results])
    for (count, width), text, record in zip(cases, results, records):
        assert isinstance(text, ProbStr), (count, width)
        assert record["confidence"] is not None, (count, width, record)
        assert len(record["chars"]) == len(record["text"]), (count, width)
        assert len(record["eos"]) <= text.reads, (count, width)
        print(f"予測 {count}、幅 {width}: 読み {text.reads} 回、{len(text)} 文字、終わりの記号 {len(text.eos)}、確信度 {record['confidence']}")
    # 98 文字以上の横長の行は、左右に分けて 2 回読み、つなぐ
    split = results[-1]
    assert split.reads == 2 and len(split) == 150, (split.reads, len(split))
    print("process_cascade: 不変条件を満たした")


def check_models() -> None:
    from types import SimpleNamespace
    from PIL import Image, ImageDraw, ImageFont

    package = Path(ocr.__file__).resolve().parent
    args = SimpleNamespace(device="cpu", rec_classes=str(package / "config/NDLmoji.yaml"),
                           rec_weights=str(package / "model/parseq-ndl-24x768-100-tiny-153epoch-tegaki3-r8data-202604.onnx"))
    weights = [str(package / "model/parseq-ndl-24x256-30-tiny-189epoch-tegaki3-r8data-202604.onnx"),
               str(package / "model/parseq-ndl-24x384-50-tiny-300epoch-tegaki3-r8data-202604.onnx"), None]
    font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 28)
    samples = ["情報通信白書の概要", "令和七年版の防衛白書を読む", "確信度を数える試験の行です"]
    for weight in weights:
        model = ocr.get_recognizer(args, weight) if weight else ocr.get_recognizer(args)
        wrapped = ConfidentRecognizer(model)
        for sample in samples:
            image = Image.new("RGB", (40 * len(sample), 48), "white")
            ImageDraw.Draw(image).text((8, 8), sample, fill="black", font=font)
            pixels = np.array(image)
            original, ours = model.read(pixels), wrapped.read(pixels)
            assert str(ours) == original, (original, str(ours))
            assert all(0.0 <= p <= 1.0 for p in ours.chars + ours.eos)
            assert len(ours.chars) == len(ours)
            print(f"{Path(model.model_path).name[:24]}: {original!r} 最小 {min(ours.chars + ours.eos):.4f}")
    print("本物の認識器: 包んだ読みと元の read の文字列が同じ")


if __name__ == "__main__":
    check_cascade()
    check_models()
