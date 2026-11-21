"""記事 1 本とルートの index.md、log.md の SHA-256 を照合する。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import unicodedata


MANIFEST_VERSION = 1
SHARED_FILES = ("index.md", "log.md")
WAIT = 1
ERROR = 2
LABELS = {
    "match": "一致",
    "mismatch": "内容が不一致",
    "missing": "ファイルが見つからない",
    "unreadable": "ファイルを確認できない",
}


def validate_article(article: str) -> str:
    path = PurePosixPath(article)
    if (
        path.as_posix() != article
        or path.is_absolute()
        or path.suffix.casefold() != ".md"
        or any(part == ".." or ":" in part or "\\" in part for part in path.parts)
        or article.casefold() in SHARED_FILES
    ):
        raise ValueError("記事には wiki 内の相対パスを / 区切りで指定してください。")
    return article


def inspect_file(root: Path, relative: str) -> dict:
    path = root / relative
    result = {"path": relative, "sha256": None, "status": "match", "conflict_copies": []}
    try:
        path.resolve().relative_to(root)
        prefix = unicodedata.normalize("NFC", f"{path.stem} (").casefold()
        result["conflict_copies"] = sorted(
            sibling.relative_to(root).as_posix()
            for sibling in path.parent.iterdir()
            if unicodedata.normalize("NFC", sibling.name).casefold().startswith(prefix)
            and sibling.suffix.casefold() == path.suffix.casefold()
            and sibling.stem.endswith(")")
        )
        with path.open("rb") as stream:
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(65536), b""):
                digest.update(chunk)
            result["sha256"] = digest.hexdigest()
    except FileNotFoundError:
        result["status"] = "missing"
    except (OSError, RuntimeError, ValueError):
        result["status"] = "unreadable"
    return result


def all_match(rows: list[dict]) -> bool:
    return all(row["status"] == "match" and not row["conflict_copies"] for row in rows)


def report(rows: list[dict], json_output: bool) -> int:
    ready = all_match(rows)
    if json_output:
        print(json.dumps({"decision": "ready" if ready else "wait", "files": rows}))
    else:
        print("引き継ぎ可" if ready else "待機")
        for row in rows:
            print(f"  {row['path']}  {LABELS[row['status']]}")
            for copy in row["conflict_copies"]:
                print(f"    競合コピー候補  {copy}")
    return 0 if ready else WAIT


def capture(root: Path, article: str, manifest_path: Path) -> int:
    rows = [inspect_file(root, name) for name in (article, *SHARED_FILES)]
    if not all_match(rows):
        return report(rows, json_output=False)
    manifest = {
        "version": MANIFEST_VERSION,
        "article": article,
        "sha256": {row["path"]: row["sha256"] for row in rows},
    }
    with manifest_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"照合用ファイルを保存しました  {manifest_path}")
    return 0


def compare_files(root: Path, names: tuple[str, ...], hashes: dict) -> list[dict]:
    rows = []
    for name in names:
        row = inspect_file(root, name)
        row["expected_sha256"] = hashes[name].lower()
        if row["status"] == "match" and row["sha256"] != row["expected_sha256"]:
            row["status"] = "mismatch"
        rows.append(row)
    return rows


def check(root: Path, manifest_path: Path, json_output: bool) -> int:
    with manifest_path.open(encoding="utf-8-sig") as stream:
        manifest = json.load(stream)
    if not isinstance(manifest, dict) or type(manifest.get("version")) is not int or manifest["version"] != MANIFEST_VERSION:
        raise ValueError("照合用 JSON の形式またはバージョンが不正です。")
    article = manifest.get("article")
    hashes = manifest.get("sha256")
    if not isinstance(article, str) or not isinstance(hashes, dict):
        raise ValueError("照合用 JSON に記事のパスと SHA-256 が必要です。")
    names = (validate_article(article), *SHARED_FILES)
    if set(hashes) != set(names) or any(
        not isinstance(value, str) or re.fullmatch(r"[0-9A-Fa-f]{64}", value) is None
        for value in hashes.values()
    ):
        raise ValueError("照合用 JSON に対象 3 ファイルの SHA-256 が必要です。")
    rows = compare_files(root, names, hashes)
    if all_match(rows):
        rows = compare_files(root, names, hashes)
    return report(rows, json_output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("capture", "送り手の 3 ファイルの SHA-256 を保存"),
        ("check", "受け手で照合し、引き継ぎの可否を表示"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--wiki", type=Path, required=True, help="wiki のルート")
        command.add_argument("--manifest", type=Path, required=True, help="照合用 JSON")
    commands.choices["capture"].add_argument("--article", required=True, help="記事の相対パス")
    commands.choices["check"].add_argument("--json", action="store_true", help="結果を JSON で表示")
    args = parser.parse_args()
    try:
        root = args.wiki.resolve(strict=True)
        if not (root / "SCHEMA.md").is_file():
            raise ValueError("SCHEMA.md がある wiki のルートを指定してください。")
        if args.command == "capture":
            return capture(root, validate_article(args.article), args.manifest)
        return check(root, args.manifest, args.json)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"照合を開始できません  {error}", file=sys.stderr)
        return ERROR


if __name__ == "__main__":
    sys.exit(main())
