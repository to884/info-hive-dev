"""7 回目のレビューの重大 1 の確かめ（実際のディスク）。既定の書き出し先に利用者のファイルがあるとき、3 つの配置で書き出す。

- browse-junction: <data_dir>/browse が、利用者のディレクトリへのジャンクション（レビューの反例）
- data-junction: <data_dir> そのものが、利用者のディレクトリへのジャンクション。その下の browse は実のディレクトリ
- no-link: リンクはない。<data_dir>/browse/<key> に、利用者が手でファイルを置いた
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, r"C:\Works\info-hive-dev\docs\agent-runs\2026-11-11-wiki-browse-structure")
import write_model as m  # noqa: E402


def junction(link, target):
    subprocess.run(["cmd", "/c", "mklink", "/J", link, target], check=True, capture_output=True)


def case(name):
    with tempfile.TemporaryDirectory() as box:
        wiki = os.path.join(box, "wiki")
        os.makedirs(wiki)
        with open(os.path.join(wiki, "a.md"), "w", encoding="utf-8") as f:
            f.write("# a\n")
        data = os.path.join(box, "data")
        user = os.path.join(box, "user")
        if name == "browse-junction":
            private = os.path.join(user, "KEY", "private.txt")
            os.makedirs(data)
            os.makedirs(os.path.dirname(private))
            junction(os.path.join(data, "browse"), user)
        elif name == "data-junction":
            private = os.path.join(user, "browse", "KEY", "private.txt")
            os.makedirs(os.path.dirname(private))
            junction(data, user)
        else:
            private = os.path.join(data, "browse", "KEY", "private.txt")
            os.makedirs(os.path.dirname(private))
        with open(private, "w", encoding="utf-8") as f:
            f.write("keep me\n")
        out = os.path.join(data, "browse", "KEY")
        m.WARNINGS.clear()
        try:
            rc = m.build(wiki, out, {"index.html": b"<p>N</p>"}, default=True, owner="A")
        except Exception as e:   # noqa: BLE001
            rc = f"{type(e).__name__}: {e}"
        print(f"{name}: rc = {rc}、警告 = {m.WARNINGS}、private.txt が残るか: {os.path.exists(private)}")
        for link in (os.path.join(data, "browse"), data):
            if os.path.lexists(link) and (os.path.islink(link) or os.path.isjunction(link)):
                os.unlink(link)


print("Python", sys.version.split()[0], sys.platform)
for name in ("browse-junction", "data-junction", "no-link"):
    case(name)
