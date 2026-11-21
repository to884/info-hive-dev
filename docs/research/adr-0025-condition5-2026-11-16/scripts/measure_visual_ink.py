"""匿名の固定150 DPI画像で、指定した範囲のインクと箱の重なりを測る試作。"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image
from scipy.ndimage import find_objects, label


# region_truth と同じコントラストと、窓の短辺だけ広げた範囲の背景中央値を使う。
CONTRAST = 64
SCALE = 3


def checked_rectangle(rectangle, size):
    """半開区間の整数の箱を確認する。"""
    left, top, right, bottom = rectangle
    width, height = size
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError("指定した範囲が画像の外にあるか空です")
    return left, top, right, bottom


def span(ink, target, axis):
    """割当軸の重なりと、直交軸の中心の位置を返す。"""
    orthogonal = 1 - axis
    first = max(ink[axis], target[axis])
    last = min(ink[axis + 2], target[axis + 2])
    twice_center = ink[orthogonal] + ink[orthogonal + 2]
    return {
        "bounds": list(ink),
        "axis_overlap": max(0, last - first),
        "axis_length": ink[axis + 2] - ink[axis],
        "cross_axis_center_inside": 2 * target[orthogonal] <= twice_center <= 2 * target[orthogonal + 2],
    }


def expanded_window(window, size):
    left, top, right, bottom = window
    width, height = size
    pad = min(right - left, bottom - top)
    return max(0, left - pad), max(0, top - pad), min(width, right + pad), min(height, bottom + pad)


def measure(gray, window, target, axis, background, selected):
    """成分を列挙し、明示的に選ばれた成分だけを測る。"""
    mask = np.abs(gray.astype(np.int16) - background) > CONTRAST
    numbers, _ = label(mask, structure=np.ones((3, 3), dtype=bool))
    left, top, right, bottom = window
    components = []
    for number, (rows, columns) in enumerate(find_objects(numbers), start=1):
        ink = left + columns.start, top + rows.start, left + columns.stop, top + rows.stop
        pixels = int(np.count_nonzero(numbers[rows, columns] == number))
        touches = ink[0] == left or ink[1] == top or ink[2] == right or ink[3] == bottom
        components.append({"id": number, **span(ink, target, axis), "pixels": pixels, "touches_window_edge": touches})
    if len(set(selected)) != len(selected) or any(i < 1 or i > len(components) for i in selected):
        raise ValueError("成分番号が重複しているか指定範囲に存在しません")
    chosen = [components[i - 1] for i in selected]
    measurement = None
    if chosen and not any(c["touches_window_edge"] for c in chosen):
        boxes = [c["bounds"] for c in chosen]
        bounds = tuple(f(values) for f, values in zip((min, min, max, max), zip(*boxes), strict=True))
        measurement = span(bounds, target, axis)
    return {
        "window": list(window),
        "target_rectangle": list(target),
        "allocation_axis": "xy"[axis],
        "background": background,
        "components": components,
        "selected_components": list(selected),
        "selected_measurement": measurement,
    }


def fixed_coordinates(rectangle):
    if len(rectangle) != 4 or any(type(value) is not int or value % SCALE for value in rectangle):
        raise ValueError("表示画像の座標は3の倍数で指定してください")
    return tuple(value // SCALE for value in rectangle)


def from_pack(folder, image_id, display_window, selected=()):
    """同じフォルダーの一覧と対応する枠なしPNGを使う。"""
    if not re.fullmatch(r"[0-9a-f]{12}", image_id):
        raise ValueError("匿名IDの形式が違います")
    folder = folder.resolve()
    index_path = folder / "index.json"
    if index_path.resolve().parent != folder:
        raise ValueError("一覧は指定した束の中に置いてください")
    index_bytes = index_path.read_bytes()
    index = json.loads(index_bytes.decode("utf-8"))
    rows = [row for row in index if row["id"] == image_id]
    if len(rows) != 1 or rows[0]["allocation_axis"] not in ("x", "y"):
        raise ValueError("一覧のIDか割当軸が違います")
    row = rows[0]
    views = [view for view in row["views"] if view["dpi"] == 150]
    if len(views) != 1 or views[0]["display_scale"] != SCALE:
        raise ValueError("固定150 DPIの表示倍率が違います")
    view = views[0]
    plain = [part["image"] for part in view["images"] if part["kind"] == "plain"]
    name = f"{image_id}-150-plain.png"
    path = folder / name
    if plain != [name] or path.resolve().parent != folder:
        raise ValueError("枠なし画像は指定した束の中に置いてください")
    raw = path.read_bytes()
    with Image.open(io.BytesIO(raw)) as image:
        if image.format != "PNG" or image.width % SCALE or image.height % SCALE:
            raise ValueError("固定150 DPIの画像形式か寸法が違います")
        size = image.width // SCALE, image.height // SCALE
        target = checked_rectangle(fixed_coordinates(view["target_rectangle"]), size)
        window = checked_rectangle(fixed_coordinates(display_window), size)
        context = expanded_window(window, size)
        gray = np.asarray(image.crop(tuple(value * SCALE for value in context)).convert("L"))
    base = gray[::SCALE, ::SCALE]
    if not np.array_equal(gray, base.repeat(SCALE, axis=0).repeat(SCALE, axis=1)):
        raise ValueError("固定150 DPIの最近傍拡大ではありません")
    left, top, right, bottom = window
    x, y = context[:2]
    pixels = base[top - y:bottom - y, left - x:right - x]
    result = measure(pixels, window, target, "xy".index(row["allocation_axis"]), float(np.median(base)), selected)
    return {
        "image_id": image_id,
        "input_sha256": {"index.json": hashlib.sha256(index_bytes).hexdigest(), name: hashlib.sha256(raw).hexdigest()},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "coordinates": "150dpi-crop-relative-half-open",
        "display_window": list(display_window),
        "background_window": list(context),
        **result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", required=True, type=Path)
    parser.add_argument("--id", required=True)
    parser.add_argument("--window", required=True, nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
                        help="3倍拡大した枠なし画像上の座標。右端と下端は範囲に含めない")
    parser.add_argument("--components", nargs="+", type=int, default=(),
                        help="同じ文字に属する成分の番号。指定しない場合は成分の一覧だけを返す")
    args = parser.parse_args()
    try:
        result = from_pack(args.folder, args.id, args.window, args.components)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
