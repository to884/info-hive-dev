"""利用枠の確証と、送付を止めるだけの疑いを区別する。"""

import json
import re

LIMIT = re.compile(
    r"(?:usage limit|rate[ -]limit|too many requests|(?:http|status(?: code)?)\s*[:=]?\s*429)",
    re.IGNORECASE,
)


def suspected(folder, role, receipt):
    if receipt["availability"] not in ("failed-technical", "invalid-technical"):
        return receipt
    log = folder / "response.jsonl"
    texts = []
    for line in log.read_bytes().splitlines():
        try:
            event = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if not isinstance(event, dict):
            continue
        info = event.get("rate_limit_info")
        if event.get("api_error_status") == 429 or (event.get("type") == "rate_limit_event"
                                                    and isinstance(info, dict) and info.get("status") == "rejected"):
            return {**receipt, "availability": "quota-unproven"}
        if role == "gpt" and event.get("type") in ("turn.failed", "error"):
            error = event.get("error", event)
            if isinstance(error, dict):
                texts.append(error.get("message", ""))
    if any(isinstance(message, str) and LIMIT.search(message) for message in texts):
        return {**receipt, "availability": "quota-unproven"}
    return receipt
