"""画像だけの測定の反例を確認する。"""

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from measure_visual_ink import from_pack, measure


class MeasureVisualInkTest(unittest.TestCase):
    def test_touching_fragment_cannot_take_part_in_selection(self):
        gray = np.full((8, 8), 255, dtype=np.uint8)
        gray[2:4, 0] = 0
        gray[4:6, 2:5] = 0
        window, target = (10, 10, 18, 18), (9, 9, 13, 19)
        plain = measure(gray, window, target, 0, 255, ())
        self.assertIsNone(plain["selected_measurement"])
        self.assertTrue(plain["components"][0]["touches_window_edge"])
        selected = measure(gray, window, target, 0, 255, (2,))
        self.assertEqual(selected["selected_measurement"]["axis_overlap"], 1)
        self.assertEqual(selected["selected_measurement"]["axis_length"], 3)
        self.assertIsNone(measure(gray, window, target, 0, 255, (1, 2))["selected_measurement"])

    def test_explicit_selection_keeps_both_parts_and_excludes_neighbor(self):
        gray = np.full((10, 12), 255, dtype=np.uint8)
        gray[1:4, 2:5] = 0
        gray[5:8, 2:5] = 0
        gray[2:5, 8:11] = 0
        window, target = (0, 0, 12, 10), (0, 0, 7, 4)
        whole = measure(gray, window, target, 1, 255, (1, 3))
        self.assertEqual(whole["selected_measurement"]["bounds"], [2, 1, 5, 8])
        self.assertEqual(whole["selected_measurement"]["axis_overlap"], 3)
        self.assertEqual(whole["selected_measurement"]["axis_length"], 7)
        self.assertTrue(whole["selected_measurement"]["cross_axis_center_inside"])
        self.assertEqual(measure(gray, window, target, 1, 255, (1,))["selected_measurement"]["axis_length"], 3)
        with self.assertRaises(ValueError):
            measure(gray, window, target, 1, 255, (1, 1))

    def test_archive_window_uses_surrounding_background_and_display_coordinates(self):
        with tempfile.TemporaryDirectory() as scratch:
            folder = Path(scratch)
            name = "a" * 12
            png = f"{name}-150-plain.png"
            data = [{"id": name, "allocation_axis": "x", "views": [
                {"dpi": 150, "display_scale": 3, "target_rectangle": [0, 0, 60, 120],
                 "images": [{"kind": "plain", "image": png}]}
            ]}]
            (folder / "index.json").write_text(json.dumps(data), encoding="utf-8")
            original = np.full((40, 40), 255, dtype=np.uint8)
            original[10:30, 10:30] = 0
            shown = original.repeat(3, axis=0).repeat(3, axis=1)
            Image.fromarray(shown).save(folder / png)
            result = from_pack(folder, name, (27, 27, 93, 93), (1,))
            self.assertEqual(result["background"], 255)
            self.assertEqual(result["selected_measurement"]["bounds"], [10, 10, 30, 30])
            self.assertEqual(result["selected_measurement"]["axis_overlap"], 10)
            self.assertEqual(result["selected_measurement"]["axis_length"], 20)
            self.assertEqual(set(result["input_sha256"]), {"index.json", png})
            with self.assertRaises(ValueError):
                from_pack(folder, name, (28, 27, 93, 93), (1,))
            shown[30, 30] = 255
            Image.fromarray(shown).save(folder / png)
            with self.assertRaises(ValueError):
                from_pack(folder, name, (27, 27, 93, 93), (1,))


if __name__ == "__main__":
    unittest.main()
