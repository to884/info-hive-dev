# /// script
# requires-python = ">=3.10"
# dependencies = ["markdown-it-py==3.0.0"]
# ///
"""ADR-0010 の未決 3 の材料。gen.py の export_name() を、Codex のレビューが挙げた反例で確かめる。配布対象ではない。

使い方: uv run --script names_check.py
"""
import json
import sys
import ntpath
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402

LIMIT = 200


def names(ids):
    out = {pid: gen.export_name(pid, LIMIT) for pid in ids}
    try:
        gen.check_unique(out)
        return out, None
    except gen.NameCollision as exc:
        return out, json.loads(str(exc))


cases = {}
# 1. 接尾辞の形の名前を足しても、既存のページの名前が変わらない
base = ["concepts/foo."]
step1, _ = names(base)
step2, err2 = names(base + [gen.export_name("concepts/foo.", LIMIT)[:-5]])
step3, err3 = names(base + [step2[base[0]][:-5], step2[base[0]][:-5] + "~974383d7"])
cases["suffix_like_names"] = {
    "alone": step1, "with_suffix_like_page": step2, "error2": err2, "with_more": step3, "error3": err3,
    "stable": step1[base[0]] == step2[base[0]] == step3[base[0]],
}
# 2. ディレクトリ foo.html とページ foo
out, err = names(["concepts/foo", "concepts/foo.html/bar"])
cases["dir_named_like_output"] = {"names": out, "error": err}
# 3. 予約名
out, _ = names(["concepts/CON.x", "concepts/nul", "concepts/LPT1 .y"])
cases["reserved"] = {"names": out, "reserved_after": {k: ntpath.isreserved(v.split("/")[-1]) if hasattr(ntpath, "isreserved") else False
                                                       for k, v in out.items()}}
# 4. 同じディレクトリのページは同じ出力のディレクトリに入る
out, _ = names(["dir. /a", "dir. /b"])
cases["same_dir"] = {"names": out, "same": len({v.rsplit("/", 1)[0] for v in out.values()}) == 1}
# 5. 大文字と小文字だけが違う出力は、生成を止めずに接尾辞で分ける（Core._names()）。それでも重なれば止める
cases["case_only"] = names(["concepts/Foo", "concepts/foo"])[1]

print(json.dumps(cases, ensure_ascii=False, indent=2))
ok = (cases["suffix_like_names"]["stable"] and not cases["suffix_like_names"]["error3"]
      and not cases["dir_named_like_output"]["error"] and not any(cases["reserved"]["reserved_after"].values())
      and cases["same_dir"]["same"])
print("OK" if ok else "NG")
sys.exit(0 if ok else 1)
