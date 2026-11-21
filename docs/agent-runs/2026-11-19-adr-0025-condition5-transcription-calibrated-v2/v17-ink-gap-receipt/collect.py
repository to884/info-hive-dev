"""保存された最終回答と、内容の取得を伴わないJSON構文エラーを分ける。"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "v17-ink-gap-pilot"
sys.path.insert(0, str(ORIGINAL))
spec = importlib.util.spec_from_file_location("original_gap_trial", ORIGINAL / "run.py")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)
original = trial.session_and_response
handled = []


def validated(events, family, model, last_message):
    if family != "claude":
        return original(events, family, model, last_message)
    rejected = set()
    for event in events:
        content = event.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if (part.get("type") == "tool_result" and part.get("is_error") is True
                    and isinstance(part.get("content"), str)
                    and part["content"].startswith("<tool_use_error>InputValidationError: StructuredOutput ")):
                rejected.add(part["tool_use_id"])
    filtered = []
    for event in events:
        message = event.get("message", {})
        content = message.get("content")
        if not isinstance(content, list):
            filtered.append(event)
            continue
        keep = []
        for part in content:
            if (part.get("type") == "tool_use" and part.get("id") in rejected
                    and part.get("name") == "StructuredOutput" and set(part["input"]) == {"__unparsedToolInput"}):
                handled.append(part["id"])
            else:
                keep.append(part)
        filtered.append({**event, "message": {**message, "content": keep}})
    return original(filtered, family, model, last_message)


def main():
    plan = trial.load(trial.LOCK)
    if any(trial.sha(Path(f)) != h for f, h in plan["inputs"].items()):
        raise ValueError("初回の配布と受領の方法の来歴が変わった")
    if trial.load(trial.OUT / "started.json")["lock_sha256"] != trial.sha(trial.LOCK):
        raise ValueError("実際に配った束と開発試験の固定が異なる")
    trial.session_and_response, trial.HERE = validated, HERE
    trial.collect(plan)
    print("JSON構文エラーと確認した内部応答", len(handled), flush=True)


if __name__ == "__main__":
    main()
