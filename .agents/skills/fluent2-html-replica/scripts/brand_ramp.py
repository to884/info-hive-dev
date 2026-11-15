"""1 つのキーの色から、ブランドの 16 段（--fui-brand-10〜160）を作る。

Fluent UI のテーマデザイナー（microsoft/fluentui の packages/react-components/theme-designer、commit f9720c35）の
getBrandTokensFromPalette と同じ計算を、依存なしの Python に写したもの。元のコードは MIT License
（Copyright (c) Microsoft Corporation）。元のコードは、さらに次の出どころから写したと記している。
- 色空間の変換: CSS Color Module Level 4 のサンプルコード（W3C Software and Document License、Copyright © 2021 W3C）
- 色域への収め方と、行列とベクトルの積: Lea Verou の css.land の lch.js と multiply-matrices.js（MIT License）
- 2 次ベジェ曲線: three.js（MIT License、Copyright © 2010-2021 three.js authors）
それぞれの著作権表示と許諾の文は、同じフォルダーの上の THIRD-PARTY-NOTICES.txt にある。

使い方:
  python brand_ramp.py "#5b5fc7"
  python brand_ramp.py "#5b5fc7" --vibrancy 10 --hue-torsion -5
  python brand_ramp.py "#5b5fc7" --format json
  python brand_ramp.py "#5b5fc7" --selector ".my-section"

--vibrancy と --hue-torsion は、テーマデザイナーの画面の目盛り（-50〜50 の整数、既定 0）と同じ単位である。
画面と同じく、vibrancy は 100 で割って暗い側と明るい側の両方の制御点に、hue torsion は 100 で割ってねじれに使う。
出力の CSS は、fluent2.css の後に読む CSS に貼る。コントラストの確認の結果は標準エラーに出す。
"""
import argparse
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

# スキルのフォルダーに __pycache__ を作らない
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("_hue_map", Path(__file__).with_name("_hue_map.py"))
_hue_map = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_hue_map)
HUE_TO_SNAPPING_POINTS = _hue_map.HUE_TO_SNAPPING_POINTS


# ---------------------------------------------------------------------------
# 行列とベクトル（csswg.ts の multiplyMatrices。足す順序も同じにする）
# ---------------------------------------------------------------------------
def _mul(m, v):
    out = []
    for row in m:
        acc = 0
        for c, x in zip(row, v):
            acc = acc + c * x
        out.append(acc)
    return out


# ---------------------------------------------------------------------------
# 色の変換（csswg.ts）
# ---------------------------------------------------------------------------
def lin_sRGB(rgb):
    out = []
    for val in rgb:
        sign = -1 if val < 0 else 1
        a = abs(val)
        out.append(val / 12.92 if a < 0.04045 else sign * math.pow((a + 0.055) / 1.055, 2.4))
    return out


def gam_sRGB(rgb):
    out = []
    for val in rgb:
        sign = -1 if val < 0 else 1
        a = abs(val)
        out.append(sign * (1.055 * math.pow(a, 1 / 2.4) - 0.055) if a > 0.0031308 else 12.92 * val)
    return out


_M_LIN_TO_XYZ = [
    [0.41239079926595934, 0.357584339383878, 0.1804807884018343],
    [0.21263900587151027, 0.715168678767756, 0.07219231536073371],
    [0.01933081871559182, 0.11919477979462598, 0.9505321522496607],
]
_M_XYZ_TO_LIN = [
    [3.2409699419045226, -1.537383177570094, -0.4986107602930034],
    [-0.9692436362808796, 1.8759675015077202, 0.04155505740717559],
    [0.05563007969699366, -0.20397695888897652, 1.0569715142428786],
]
_M_D65_TO_D50 = [
    [1.0479298208405488, 0.022946793341019088, -0.05019222954313557],
    [0.029627815688159344, 0.990434484573249, -0.01707382502938514],
    [-0.009243058152591178, 0.015055144896577895, 0.7518742899580008],
]
_M_D50_TO_D65 = [
    [0.9554734527042182, -0.023098536874261423, 0.0632593086610217],
    [-0.028369706963208136, 1.0099954580058226, 0.021041398966943008],
    [0.012314001688319899, -0.020507696433477912, 1.3303659366080753],
]
_EPS = 216 / 24389
_KAPPA = 24389 / 27
_WHITE = [0.96422, 1.0, 0.82521]


def XYZ_to_Lab(xyz):
    s = [v / _WHITE[i] for i, v in enumerate(xyz)]
    f = [math.cbrt(v) if v > _EPS else (_KAPPA * v + 16) / 116 for v in s]
    return [116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])]


def Lab_to_XYZ(lab):
    f1 = (lab[0] + 16) / 116
    f0 = lab[1] / 500 + f1
    f2 = f1 - lab[2] / 200
    xyz = [
        math.pow(f0, 3) if math.pow(f0, 3) > _EPS else (116 * f0 - 16) / _KAPPA,
        math.pow((lab[0] + 16) / 116, 3) if lab[0] > _KAPPA * _EPS else lab[0] / _KAPPA,
        math.pow(f2, 3) if math.pow(f2, 3) > _EPS else (116 * f2 - 16) / _KAPPA,
    ]
    return [v * _WHITE[i] for i, v in enumerate(xyz)]


def Lab_to_LCH(lab):
    hue = (math.atan2(lab[2], lab[1]) * 180) / math.pi
    return [lab[0], math.sqrt(math.pow(lab[1], 2) + math.pow(lab[2], 2)), hue if hue >= 0 else hue + 360]


def LCH_to_Lab(lch):
    return [lch[0], lch[1] * math.cos((lch[2] * math.pi) / 180), lch[1] * math.sin((lch[2] * math.pi) / 180)]


def sRGB_to_LCH(rgb):
    return Lab_to_LCH(XYZ_to_Lab(_mul(_M_D65_TO_D50, _mul(_M_LIN_TO_XYZ, lin_sRGB(rgb)))))


def LCH_to_sRGB(lch):
    return gam_sRGB(_mul(_M_XYZ_TO_LIN, _mul(_M_D50_TO_D65, Lab_to_XYZ(LCH_to_Lab(lch)))))


def LAB_to_sRGB(lab):
    return gam_sRGB(_mul(_M_XYZ_TO_LIN, _mul(_M_D50_TO_D65, Lab_to_XYZ(lab))))


def _inside_sRGB(l, c, h):
    e = 0.000005
    return all(0 - e <= b <= 1 + e for b in LCH_to_sRGB([l, c, h]))


def snap_into_gamut(lab):
    eps = 0.0001
    l, c, h = Lab_to_LCH(lab)
    if _inside_sRGB(l, c, h):
        return lab
    hi, lo = c, 0
    c /= 2
    while hi - lo > eps:
        if _inside_sRGB(l, c, h):
            lo = c
        else:
            hi = c
        c = (hi + lo) / 2
    return LCH_to_Lab([l, c, h])


# ---------------------------------------------------------------------------
# 16 進数（palettes.ts）と色相（hueMap.ts）
# ---------------------------------------------------------------------------
def hex_to_sRGB(hex_color):
    m = re.match(r"#?(..)(..)(..)", hex_color)
    return [int(m.group(i), 16) / 255 for i in (1, 2, 3)] if m else [0, 0, 0]


def sRGB_to_hex(rgb):
    def channel(x):
        return 0 if x < 0 else math.floor(255 if x >= 1.0 else x * 256)
    return "#" + "".join(f"{channel(x):02x}" for x in rgb)


def hex_to_hue(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    cmax, cmin = max(r, g, b), min(r, g, b)
    delta = cmax - cmin
    if delta == 0:
        hue = 0
    elif cmax == r:
        hue = math.fmod((g - b) / delta, 6)  # JS の % は被除数の符号を保つ
    elif cmax == g:
        hue = (b - r) / delta + 2
    else:
        hue = (r - g) / delta + 4
    hue = math.floor(hue * 60 + 0.5)  # JS の Math.round（0.5 は +∞ の側へ）
    if hue < 0:
        hue += 360
    return hue


# ---------------------------------------------------------------------------
# 曲線（geometry.ts と palettes.ts）
# ---------------------------------------------------------------------------
def _quadratic_bezier(t, p0, p1, p2):
    k = 1 - t
    return k * k * p0 + 2 * (1 - t) * t * p1 + t * t * p2


def _points_on_curve(points, divisions):
    v0, v1, v2 = points
    return [[_quadratic_bezier(d / divisions, v0[i], v1[i], v2[i]) for i in range(3)] for d in range(divisions + 1)]


def _points_on_curve_path(curves, divisions):
    out, last = [], None
    for points in curves:
        for p in _points_on_curve(points, divisions):
            if last is not None and last == p:
                continue
            out.append(p)
            last = p
    return out


def _point_on_helix(point, torsion, torsion_t0):
    t = point[0]
    l, c, h = Lab_to_LCH(point)
    return LCH_to_Lab([l, c, h + torsion * (t - torsion_t0)])


def _linear_through_point(start, end, in_between, n):
    ratio = (in_between - start) / (end - start)
    idx = math.floor((n - 1) * ratio)
    result = [None] * n
    result[0] = start
    result[idx] = in_between
    result[n - 1] = end
    step_before = (in_between - start) / idx if idx else math.inf
    step_after = (end - in_between) / (n - 1 - idx)
    for i in range(1, idx):
        result[i] = start + i * step_before
    for i in range(idx + 1, n - 1):
        result[i] = in_between + (i - idx) * step_after
    return result


def _log_space(lo, hi, n):
    a = 0 if lo <= 0 else math.log(lo)
    b = math.log(hi)
    delta = (b - a) / n
    out = [math.pow(math.e, a)]
    for i in range(1, n):
        out.append(math.pow(math.e, a + delta * i))
    out.append(math.pow(math.e, b))
    return out


def brand_ramp(key_color, vibrancy=0, hue_torsion=0):
    """テーマデザイナーの画面と同じ入力（目盛り -50〜50）から 16 段を作る。{10: '#rrggbb', …, 160: …} を返す。"""
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", key_color):
        raise ValueError("キーの色は #RRGGBB の形で書く")
    for name, v in (("vibrancy", vibrancy), ("hue_torsion", hue_torsion)):
        # 画面（Sidebar/Form.tsx）は目盛りを parseInt して整数で渡す。小数を許すと、末尾のけたの差で 16 進数が 1 違うことがある
        if isinstance(v, bool) or not isinstance(v, int) or not -50 <= v <= 50:
            raise ValueError(f"{name} は -50〜50 の整数にする")
    dark_cp = light_cp = vibrancy / 100
    torsion = hue_torsion / 100

    # getBrandTokensFromPalette → hexColorsFromPalette(keyColor, palette, 16, 1)
    key_lch = sRGB_to_LCH(hex_to_sRGB(key_color))
    key = LCH_to_Lab(key_lch)
    l, a, b = key
    curves = [
        [[0, 0, 0], [l * (1 - dark_cp), a, b], key],
        [key, [l + (100 - l) * light_cp, a, b], [100, 0, 0]],
    ]
    divisions = math.ceil((24 * (1 + abs(torsion or 1))) / 2)  # 元の `curve.torsion || 1`
    points = [_point_on_helix(p, torsion, l) for p in _points_on_curve_path(curves, divisions)]

    hue = hex_to_hue(key_color)
    snap = [v * 100 for v in HUE_TO_SNAPPING_POINTS[hue]]
    lo, hi = snap[0], snap[2]
    linearity = 1
    log_l = _log_space(-math.inf, math.log10(100), 16)
    lin_l = _linear_through_point(lo, hi, HUE_TO_SNAPPING_POINTS[hue][1] * 100, 16)
    shades, c = [], 0
    for i in range(16):
        lightness = min(hi, max(lo, log_l[i] * (1 - linearity) + lin_l[i] * linearity))
        while lightness > points[c + 1][0]:
            c += 1
        l1, a1, b1 = points[c]
        l2, a2, b2 = points[c + 1]
        u = (lightness - l1) / (l2 - l1)
        shades.append(snap_into_gamut([l1 + (l2 - l1) * u, a1 + (a2 - a1) * u, b1 + (b2 - b1) * u]))
    return {(i + 1) * 10: sRGB_to_hex(LAB_to_sRGB(s)) for i, s in enumerate(shades)}


# ---------------------------------------------------------------------------
# コントラストの確認（テーマデザイナーの AccessiblePairs と、白い文字を載せる組）
# ---------------------------------------------------------------------------
def _luminance(hex_color):
    def ch(v):
        return v / 12.92 if v <= 0.04045 else math.pow((v + 0.055) / 1.055, 2.4)
    r, g, b = (ch(x) for x in hex_to_sRGB(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(c1, c2):
    a, b = sorted((_luminance(c1), _luminance(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


# ダークの文字のブランド色の段。fluent は createDarkTheme（packages/tokens/src/alias/darkColor.ts。fluent2.css の既定）、
# designer はテーマデザイナーが書き出すダークのテーマ（theme-designer/src/utils/getOverridableTokenBrandColors.ts:70-76 の
# createDarkThemeWithUpdatedMapping。colorBrandForeground1 を 110、colorBrandForeground2 を 120 にする）
DARK_MAPPING = {
    "fluent": {"colorBrandForeground1": 100, "colorBrandForeground2": 110},
    "designer": {"colorBrandForeground1": 110, "colorBrandForeground2": 120},
}


def checks_for(dark_mapping):
    """確かめる組（トークンがどの段を参照するかは lightColor.ts と darkColor.ts。fluent2.css と同じ）。"""
    d = DARK_MAPPING[dark_mapping]
    return [
        ("light", "colorBrandForeground1 / colorNeutralBackground1", 80, "#ffffff"),
        ("light", "colorBrandForeground2 / colorBrandBackground2", 70, 160),
        ("light", "colorNeutralForegroundOnBrand / colorBrandBackground", "#ffffff", 80),
        ("dark", "colorBrandForeground1 / colorNeutralBackground1", d["colorBrandForeground1"], "#292929"),
        ("dark", "colorBrandForeground2 / colorBrandBackground2", d["colorBrandForeground2"], 20),
        ("dark", "colorNeutralForegroundOnBrand / colorBrandBackground", "#ffffff", 70),
    ]


def check_contrast(ramp, dark_mapping="designer"):
    rows = []
    for theme, label, fg, bg in checks_for(dark_mapping):
        f = ramp[fg] if isinstance(fg, int) else fg
        b = ramp[bg] if isinstance(bg, int) else bg
        ratio = contrast(f, b)
        rows.append({"theme": theme, "pair": label, "ratio": round(ratio, 2), "ok": ratio >= 4.5})
    return rows


def ramp_css(key_color, vibrancy=0, hue_torsion=0, selector=":root", dark_mapping="designer"):
    """16 段と、ダークの文字のブランド色の切り替えを、1 つの規則として返す。

    セレクターの文字列には何も足さない。ダークの段の選び直しは、fluent2.css のダークの規則が読む切り替えの変数
    --fui-dark-mapping-designer で渡す。値が空なら、ダークの規則が colorBrandForeground1 と colorBrandForeground2 を
    テーマデザイナーと同じ 110 と 120 の段にする。切り替えだけが受け継がれ、色はダークの規則を宣言する要素ごとに、
    その要素のブランドの段から決まる。そのため、この規則が当たる要素の中の入れ子の data-theme="dark" と
    data-theme="auto" にも届き、内側で 16 段だけを差し替えた区画でも、その区画のブランドの段が使われる。
    """
    ramp = brand_ramp(key_color, vibrancy, hue_torsion)
    lines = [f"/* ブランドの 16 段（キーの色 {key_color}、vibrancy {vibrancy}、hue torsion {hue_torsion}、ダークの段 {dark_mapping}）。"
             "brand_ramp.py が Fluent UI のテーマデザイナーと同じ計算で作った。fluent2.css の後に読む */",
             f"{selector} {{"]
    lines += [f"  --fui-brand-{k}: {v};" for k, v in ramp.items()]
    if dark_mapping == "designer":
        # 空の値（スペースのトグルのオン）。fluent2.css のダークの規則が 110 と 120 の段を選ぶ
        lines.append("  --fui-dark-mapping-designer: ;")
    else:
        # 外側の区画がオンにしていても、ここから内側は createDarkTheme の段（100 と 110）に戻す
        lines.append("  --fui-dark-mapping-designer: initial;")
    lines.append("}")
    return ramp, "\n".join(lines)


def _selector(text):
    s = text.strip()
    if not s or any(ch in s for ch in "{};") or "/*" in s or "*/" in s:
        raise argparse.ArgumentTypeError("セレクターが空か、{ } ; やコメントを含んでいる")
    return s


def main(argv=None):
    ap = argparse.ArgumentParser(description="キーの色から Fluent 2 のブランドの 16 段を作る")
    ap.add_argument("key_color", help="キーの色（#RRGGBB）")
    ap.add_argument("--vibrancy", type=int, default=0,
                    help="テーマデザイナーの Vibrancy（-50〜50 の整数、既定 0。画面と同じく整数だけを受け付ける）")
    ap.add_argument("--hue-torsion", type=int, default=0,
                    help="テーマデザイナーの Hue torsion（-50〜50 の整数、既定 0）")
    ap.add_argument("--format", choices=("css", "json"), default="css")
    ap.add_argument("--selector", type=_selector, default=":root",
                    help="16 段を宣言するセレクター（既定 :root）。区画だけを替えるときは、data-theme を付けた要素を指す")
    ap.add_argument("--dark-mapping", choices=("designer", "fluent"), default="designer",
                    help="ダークの文字のブランド色の段。designer（既定）はテーマデザイナーの書き出しと同じ 110 と 120、"
                         "fluent は Fluent の createDarkTheme のままの 100 と 110")
    args = ap.parse_args(argv)
    for name in ("vibrancy", "hue_torsion"):
        if not -50 <= getattr(args, name) <= 50:
            ap.error(f"--{name.replace('_', '-')} は -50〜50 にする")
    ramp, css = ramp_css(args.key_color, args.vibrancy, args.hue_torsion, args.selector, args.dark_mapping)
    checks = check_contrast(ramp, args.dark_mapping)
    if args.format == "json":
        out = json.dumps({"brand": {str(k): v for k, v in ramp.items()}, "darkMapping": args.dark_mapping,
                          "darkSteps": DARK_MAPPING[args.dark_mapping], "contrast": checks}, ensure_ascii=False, indent=2)
    else:
        out = css
    sys.stdout.buffer.write((out + "\n").encode("utf-8"))
    report = ["コントラスト（4.5:1 以上が目安）:"]
    report += [f"  {'OK ' if r['ok'] else 'NG '} {r['theme']:5s} {r['pair']}: {r['ratio']}:1" for r in checks]
    sys.stderr.buffer.write(("\n".join(report) + "\n").encode("utf-8"))
    return 0 if all(r["ok"] for r in checks) else 2


if __name__ == "__main__":
    sys.exit(main())
