"""実際のフックを合成wikiで起動し、時間と候補が届いた回数を記録する。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import bench_prompt_hook as bench


def run(pages, runs):
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        bench.synthetic_wiki(project / "wiki", pages)
        env = dict(os.environ, CLAUDE_PLUGIN_DATA=str(Path(tmp) / "data"), INFO_HIVE_PROMPT_CONTEXT="1")
        env.pop("RUST_LOG", None)  # 実行ホストのデバッグの設定は測定条件から外す。
        hook = (bench.SCRIPTS / "wiki_prompt_hook.py").resolve()
        command = bench.shell_line(hook)
        argv = [bench.bash_path(), "-c", command]
        result = {"pages": pages, "runs": runs, "shell": "git_bash", "deadline_seconds": 2.5,
                  "command": command, "source_sha256": hashlib.sha256(hook.read_bytes()).hexdigest(),
                  "context_sha256": hashlib.sha256((bench.SCRIPTS / 'wiki_prompt_context.py').read_bytes()).hexdigest(),
                  "pages_sha256": hashlib.sha256((bench.SCRIPTS / 'wiki_pages.py').read_bytes()).hexdigest(),
                  "excluded_env": ["RUST_LOG"], "cases": {}}
        for label, prompt in [("skip", "はい"), ("search", "[[page-0000]] [[page-0001]] の手順を確認して")]:
            values, codes, errors, delivered = [], [], [], 0
            for i in range(runs + 1):
                payload = json.dumps({"prompt": prompt, "cwd": str(project), "session_id": f"{label}-{i}",
                                      "hook_event_name": "UserPromptSubmit"}).encode("utf-8")
                started = time.perf_counter()
                proc = subprocess.run(argv, input=payload, capture_output=True, env=env, cwd=project, timeout=20)
                elapsed, code, stdout, stderr = time.perf_counter() - started, proc.returncode, proc.stdout, proc.stderr
                if i:
                    values.append(elapsed)
                    codes.append(code)
                    delivered += code == 0 and not stderr and bench.valid_candidate_output(stdout)
                    if stderr:
                        errors.append(stderr.decode("utf-8", "replace")[:100])
            result["cases"][label] = {**bench.summary(values), "delivered": delivered,
                                      "exit_codes": sorted(set(codes)), "stderr": errors}
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=int, default=150)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.pages, args.runs)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False))
