# OCR用CUDAランタイム調査

## 互換性

ORT公式資料によると、1.27以降のPyPI標準 `onnxruntime-gpu` はCUDA 13.0とcuDNN 9系で構築され、CUDA 12系の別ビルドはCUDA 12.8/cuDNN 9系です。公式互換表は1.30.xまでの記載のため、1.31.1標準wheelへの適用はこの規則からの判断です。CUDA 13.xの最小driverは580以上。報告されたdriver 617.42 / CUDA max 13.4はCUDA 13.0の要件を満たす見込みです。

Torch 2.8 `+cu128` のDLLはCUDA 12.8です。ORT 1.31.1標準PyPI wheelへ `preload_dlls(directory=Torch/lib)` で混ぜるとCUDA majorが合いません。ORT 1.31.1の `preload_dlls` はディレクトリ指定に対応しますが、互換性のあるランタイムDLLを使う必要があります。

## 固定ソースで確認した実行経路

固定archiveのNDLOCR-Lite `deim.py` と `parseq.py` は、`device="cuda"` で `CUDAExecutionProvider` を優先し、`CPUExecutionProvider` にfallbackします。`device` の既定値はCPUです。製品 `rag_pdf.py` の既存ページOCR経路も現在は `--device cpu` を指定します。

`session.get_providers()` は登録されたEP一覧で、実際のノード割当を示しません。ORT 1.31.1では、`SessionOptions` に `session.record_ep_graph_assignment_info=1` を追加して作成したsessionから `get_provider_graph_assignment_info()` を取得できます。推論後の `enable_profiling=True` / `end_profiling()` によるprofileも、実行ノードの確認に使えます。

## 親エージェントからの実施状況

親の報告では、`.rag-ocr-gpu-venv` に `onnxruntime-gpu==1.31.1` の `cuda,cudnn` extrasを導入済みです。確認されたランタイムはCUDA 13.4.92、cuDNN 9.27.0.42、cuBLAS 13.8等です。最初の小規模GPU pilotは `networkx` 未導入で失敗し、親が新venvに不足依存を追加中です。本調査ではインストールやGPU実行をしていません。

## 一次資料

- [ONNX Runtime CUDA EP互換性とDLL preload](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)
- [ONNX Runtime install要件](https://onnxruntime.ai/docs/install/)
- [PyPI: onnxruntime-gpu 1.31.1 wheel](https://pypi.org/project/onnxruntime-gpu/1.31.1/)
- [ONNX Runtime v1.31.1: preload_dlls実装](https://github.com/microsoft/onnxruntime/blob/v1.31.1/onnxruntime/__init__.py)
- [ONNX Runtime v1.31.1: provider割当API](https://github.com/microsoft/onnxruntime/blob/v1.31.1/onnxruntime/python/onnxruntime_inference_collection.py)
- [NVIDIA CUDA driver互換性](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html)
