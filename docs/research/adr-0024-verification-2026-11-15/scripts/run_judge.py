"""Sol（GPT-6.1 Sol）に、ページの画像を添えて判定させる。判定は judge/sol-result.md に書く。

使い方: python -I run_judge.py
ask-codex の ask と同じ設定（読み取り専用、承認なし、effort high）で codex exec を呼び、
judge/<ページ>/page.png を -i で、prepare_judge.SELECTED の順に添える。
1 回目の判定では画像を開かなかったため（記録に page.png を読んだ跡がない）、画像を必ず渡すためにこの形にした。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_judge import JUDGE_DIR, SELECTED  # noqa: E402  --set 2 で 2 回目の組を判定する

BENCH = Path(__file__).resolve().parent.parent
REPO = BENCH.parents[2]
JUDGE = BENCH / JUDGE_DIR


def main() -> None:
    exe = shutil.which("codex")
    if not exe:
        raise SystemExit("codex が見つからない")
    keys = [f"{stem}-p{page}" for stem, page in SELECTED]
    order = "\n".join(f"{i + 1}. {key}" for i, key in enumerate(keys))
    prompt = (JUDGE / "task.md").read_text(encoding="utf-8") + (
        "\n\n## 添えた画像\n\nこの依頼には、各ページの画像（`judge/<ページ>/page.png` と同じもの）を、次の順で添えてある。"
        "判定の前に、必ず画像を見て、ページに書かれていることと読む順を確かめる。画像を見られなかったときは、"
        "そのことを総評の最初に書く。\n\n" + order + "\n")
    images = [arg for key in keys for arg in ("-i", str(JUDGE / key / "page.png"))]
    cmd = [exe, "exec", "-c", 'model_reasoning_effort="high"', "-c", 'approval_policy="never"', "-m", "gpt-6.1-sol",
           "-s", "read-only", "-C", str(REPO), "-o", str(JUDGE / "sol-result.md"), *images, "-"]
    log = (JUDGE / "sol-result.md.log").open("wb")
    done = subprocess.run(cmd, input=prompt.encode("utf-8"), stdout=log, stderr=subprocess.STDOUT, timeout=3600)
    print("exit", done.returncode)


if __name__ == "__main__":
    main()
