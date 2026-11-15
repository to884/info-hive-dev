# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = ["yt-dlp==2026.8.19"]
# ///
"""uv で固定した yt-dlp を Python の API として使い、字幕の一覧と json3 の取得を試す（調査用）。

使い方: uv run --script ytprobe.py <出力のディレクトリ> <動画の URL> <トラック> [<トラック> ...]
同じトラックを 2 回取り、バイト列の SHA-256 を比べる。
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

import yt_dlp

out = Path(sys.argv[1])
url = sys.argv[2]
tracks = sys.argv[3:]
logs = []


class Log:
    def debug(self, m):
        pass

    def info(self, m):
        pass

    def warning(self, m):
        logs.append("WARNING " + m)

    def error(self, m):
        logs.append("ERROR " + m)


opts = {"skip_download": True, "noplaylist": True, "quiet": True, "logger": Log()}
with yt_dlp.YoutubeDL(opts) as ydl:
    info = ydl.extract_info(url, download=False)
    res = {
        "python": sys.version.split()[0],
        "yt_dlp": yt_dlp.version.__version__,
        "id": info.get("id"),
        "language": info.get("language"),
        "live_status": info.get("live_status"),
        "availability": info.get("availability"),
        "subtitles": sorted(info.get("subtitles") or {}),
        "orig": [k for k in (info.get("automatic_captions") or {}) if k.endswith("-orig")],
        "chapters": len(info.get("chapters") or []),
        "description_len": len(info.get("description") or ""),
        "hashes": {},
    }
    for t in tracks:
        pool = (info.get("subtitles") or {}).get(t) or (info.get("automatic_captions") or {}).get(t) or []
        fm = [f for f in pool if f.get("ext") == "json3"]
        if not fm:
            res["hashes"][t] = "no json3"
            continue
        hs = []
        for i in range(2):
            # yt-dlp の通信の口（クッキーとヘッダーをそろえる）で取る
            data = ydl.urlopen(fm[0]["url"]).read()
            (out / f"{info['id']}.{t}.{i}.json3").write_bytes(data)
            hs.append(hashlib.sha256(data).hexdigest()[:16] + f"/{len(data)}")
        res["hashes"][t] = hs
res["logs"] = [m[:160] for m in logs]
(out / f"probe-{res['id']}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps(res, ensure_ascii=True))
