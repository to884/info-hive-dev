# Fluent 2 Web のトークン一覧

値は `@fluentui/tokens` 1.0.0-alpha.24（microsoft/fluentui commit `f9720c35ba89`、2026-11-12）のソースから機械的に抽出した。このファイルは `tools/build_tokens.py` が生成する。手で直さない。

CSS では `var(--<トークン名>)` で参照する（例: `var(--colorNeutralBackground1)`）。定義は `assets/fluent2.css` の先頭にある。

## 色以外のトークン

| トークン | 値 |
|---|---|
| `borderRadiusNone` | `0` |
| `borderRadiusSmall` | `2px` |
| `borderRadiusMedium` | `4px` |
| `borderRadiusLarge` | `6px` |
| `borderRadiusXLarge` | `8px` |
| `borderRadius2XLarge` | `12px` |
| `borderRadius3XLarge` | `16px` |
| `borderRadius4XLarge` | `24px` |
| `borderRadius5XLarge` | `32px` |
| `borderRadius6XLarge` | `40px` |
| `borderRadiusCircular` | `10000px` |
| `fontSizeBase100` | `10px` |
| `fontSizeBase200` | `12px` |
| `fontSizeBase300` | `14px` |
| `fontSizeBase400` | `16px` |
| `fontSizeBase500` | `20px` |
| `fontSizeBase600` | `24px` |
| `fontSizeHero700` | `28px` |
| `fontSizeHero800` | `32px` |
| `fontSizeHero900` | `40px` |
| `fontSizeHero1000` | `68px` |
| `lineHeightBase100` | `14px` |
| `lineHeightBase200` | `16px` |
| `lineHeightBase300` | `20px` |
| `lineHeightBase400` | `22px` |
| `lineHeightBase500` | `28px` |
| `lineHeightBase600` | `32px` |
| `lineHeightHero700` | `36px` |
| `lineHeightHero800` | `40px` |
| `lineHeightHero900` | `52px` |
| `lineHeightHero1000` | `92px` |
| `fontFamilyBase` | `'Segoe UI', 'Segoe UI Web (West European)', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', sans-serif` |
| `fontFamilyMonospace` | `Consolas, 'Courier New', Courier, monospace` |
| `fontFamilyNumeric` | `Bahnschrift, 'Segoe UI', 'Segoe UI Web (West European)', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', sans-serif` |
| `fontWeightRegular` | `400` |
| `fontWeightMedium` | `500` |
| `fontWeightSemibold` | `600` |
| `fontWeightBold` | `700` |
| `strokeWidthThin` | `1px` |
| `strokeWidthThick` | `2px` |
| `strokeWidthThicker` | `3px` |
| `strokeWidthThickest` | `4px` |
| `spacingHorizontalNone` | `0` |
| `spacingHorizontalXXS` | `2px` |
| `spacingHorizontalXS` | `4px` |
| `spacingHorizontalSNudge` | `6px` |
| `spacingHorizontalS` | `8px` |
| `spacingHorizontalMNudge` | `10px` |
| `spacingHorizontalM` | `12px` |
| `spacingHorizontalL` | `16px` |
| `spacingHorizontalXL` | `20px` |
| `spacingHorizontalXXL` | `24px` |
| `spacingHorizontalXXXL` | `32px` |
| `spacingVerticalNone` | `0` |
| `spacingVerticalXXS` | `2px` |
| `spacingVerticalXS` | `4px` |
| `spacingVerticalSNudge` | `6px` |
| `spacingVerticalS` | `8px` |
| `spacingVerticalMNudge` | `10px` |
| `spacingVerticalM` | `12px` |
| `spacingVerticalL` | `16px` |
| `spacingVerticalXL` | `20px` |
| `spacingVerticalXXL` | `24px` |
| `spacingVerticalXXXL` | `32px` |
| `durationUltraFast` | `50ms` |
| `durationFaster` | `100ms` |
| `durationFast` | `150ms` |
| `durationNormal` | `200ms` |
| `durationGentle` | `250ms` |
| `durationSlow` | `300ms` |
| `durationSlower` | `400ms` |
| `durationUltraSlow` | `500ms` |
| `curveAccelerateMax` | `cubic-bezier(0.9,0.1,1,0.2)` |
| `curveAccelerateMid` | `cubic-bezier(1,0,1,1)` |
| `curveAccelerateMin` | `cubic-bezier(0.8,0,0.78,1)` |
| `curveDecelerateMax` | `cubic-bezier(0.1,0.9,0.2,1)` |
| `curveDecelerateMid` | `cubic-bezier(0,0,0,1)` |
| `curveDecelerateMin` | `cubic-bezier(0.33,0,0.1,1)` |
| `curveEasyEaseMax` | `cubic-bezier(0.8,0,0.2,1)` |
| `curveEasyEase` | `cubic-bezier(0.33,0,0.67,1)` |
| `curveLinear` | `cubic-bezier(0,0,1,1)` |

## 書体のスタイル（typographyStyles）

| スタイル | fontSize | lineHeight | fontWeight | fontFamily |
|---|---|---|---|---|
| `body1` | `fontSizeBase300`（14px） | `lineHeightBase300`（20px） | `fontWeightRegular`（400） | `fontFamilyBase` |
| `body1Strong` | `fontSizeBase300`（14px） | `lineHeightBase300`（20px） | `fontWeightSemibold`（600） | `fontFamilyBase` |
| `body1Stronger` | `fontSizeBase300`（14px） | `lineHeightBase300`（20px） | `fontWeightBold`（700） | `fontFamilyBase` |
| `body2` | `fontSizeBase400`（16px） | `lineHeightBase400`（22px） | `fontWeightRegular`（400） | `fontFamilyBase` |
| `caption1` | `fontSizeBase200`（12px） | `lineHeightBase200`（16px） | `fontWeightRegular`（400） | `fontFamilyBase` |
| `caption1Strong` | `fontSizeBase200`（12px） | `lineHeightBase200`（16px） | `fontWeightSemibold`（600） | `fontFamilyBase` |
| `caption1Stronger` | `fontSizeBase200`（12px） | `lineHeightBase200`（16px） | `fontWeightBold`（700） | `fontFamilyBase` |
| `caption2` | `fontSizeBase100`（10px） | `lineHeightBase100`（14px） | `fontWeightRegular`（400） | `fontFamilyBase` |
| `caption2Strong` | `fontSizeBase100`（10px） | `lineHeightBase100`（14px） | `fontWeightSemibold`（600） | `fontFamilyBase` |
| `subtitle1` | `fontSizeBase500`（20px） | `lineHeightBase500`（28px） | `fontWeightSemibold`（600） | `fontFamilyBase` |
| `subtitle2` | `fontSizeBase400`（16px） | `lineHeightBase400`（22px） | `fontWeightSemibold`（600） | `fontFamilyBase` |
| `subtitle2Stronger` | `fontSizeBase400`（16px） | `lineHeightBase400`（22px） | `fontWeightBold`（700） | `fontFamilyBase` |
| `title1` | `fontSizeHero800`（32px） | `lineHeightHero800`（40px） | `fontWeightSemibold`（600） | `fontFamilyBase` |
| `title2` | `fontSizeHero700`（28px） | `lineHeightHero700`（36px） | `fontWeightSemibold`（600） | `fontFamilyBase` |
| `title3` | `fontSizeBase600`（24px） | `lineHeightBase600`（32px） | `fontWeightSemibold`（600） | `fontFamilyBase` |
| `largeTitle` | `fontSizeHero900`（40px） | `lineHeightHero900`（52px） | `fontWeightSemibold`（600） | `fontFamilyBase` |
| `display` | `fontSizeHero1000`（68px） | `lineHeightHero1000`（92px） | `fontWeightSemibold`（600） | `fontFamilyBase` |

## ブランド色の段階（brandWeb）

| 段階 | 値 | CSS の補助の変数 |
|---|---|---|
| 10 | `#061724` | `--fui-brand-10` |
| 20 | `#082338` | `--fui-brand-20` |
| 30 | `#0a2e4a` | `--fui-brand-30` |
| 40 | `#0c3b5e` | `--fui-brand-40` |
| 50 | `#0e4775` | `--fui-brand-50` |
| 60 | `#0f548c` | `--fui-brand-60` |
| 70 | `#115ea3` | `--fui-brand-70` |
| 80 | `#0f6cbd` | `--fui-brand-80` |
| 90 | `#2886de` | `--fui-brand-90` |
| 100 | `#479ef5` | `--fui-brand-100` |
| 110 | `#62abf5` | `--fui-brand-110` |
| 120 | `#77b7f7` | `--fui-brand-120` |
| 130 | `#96c6fa` | `--fui-brand-130` |
| 140 | `#b4d6fa` | `--fui-brand-140` |
| 150 | `#cfe4fa` | `--fui-brand-150` |
| 160 | `#ebf3fc` | `--fui-brand-160` |

## 色と影のトークン

「light」「dark」の括弧内は、参照しているブランド色の段階。「HC」は createHighContrastTheme の値と、意図されたシステムカラー。

| トークン | light | dark | HC |
|---|---|---|---|
| `colorNeutralForeground1` | `#242424` | `#ffffff` | `#ffffff`（CanvasText） |
| `colorNeutralForeground1Hover` | `#242424` | `#ffffff` | `#000000`（HighlightText） |
| `colorNeutralForeground1Pressed` | `#242424` | `#ffffff` | `#000000`（HighlightText） |
| `colorNeutralForeground1Selected` | `#242424` | `#ffffff` | `#000000`（HighlightText） |
| `colorNeutralForeground2` | `#424242` | `#d6d6d6` | `#ffffff`（CanvasText） |
| `colorNeutralForeground2Hover` | `#242424` | `#ffffff` | `#000000`（HighlightText） |
| `colorNeutralForeground2Pressed` | `#242424` | `#ffffff` | `#000000`（HighlightText） |
| `colorNeutralForeground2Selected` | `#242424` | `#ffffff` | `#000000`（HighlightText） |
| `colorNeutralForeground2BrandHover` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#000000`（HighlightText） |
| `colorNeutralForeground2BrandPressed` | `#115ea3`（brand 70） | `#2886de`（brand 90） | `#000000`（HighlightText） |
| `colorNeutralForeground2BrandSelected` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#000000`（HighlightText） |
| `colorNeutralForeground3` | `#616161` | `#adadad` | `#ffffff`（CanvasText） |
| `colorNeutralForeground3Hover` | `#424242` | `#d6d6d6` | `#000000`（HighlightText） |
| `colorNeutralForeground3Pressed` | `#424242` | `#d6d6d6` | `#000000`（HighlightText） |
| `colorNeutralForeground3Selected` | `#424242` | `#d6d6d6` | `#000000`（HighlightText） |
| `colorNeutralForeground3BrandHover` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#000000`（HighlightText） |
| `colorNeutralForeground3BrandPressed` | `#115ea3`（brand 70） | `#2886de`（brand 90） | `#000000`（HighlightText） |
| `colorNeutralForeground3BrandSelected` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#000000`（HighlightText） |
| `colorNeutralForeground4` | `#707070` | `#999999` | `#ffffff`（CanvasText） |
| `colorNeutralForeground5` | `#616161` | `#adadad` | `#ffffff`（CanvasText） |
| `colorNeutralForeground5Hover` | `#242424` | `#ffffff` | `#000000`（HighlightText） |
| `colorNeutralForeground5Pressed` | `#242424` | `#ffffff` | `#000000`（HighlightText） |
| `colorNeutralForeground5Selected` | `#242424` | `#ffffff` | `#000000`（HighlightText） |
| `colorNeutralForegroundDisabled` | `#bdbdbd` | `#5c5c5c` | `#3ff23f`（GrayText） |
| `colorNeutralForegroundInvertedDisabled` | `rgba(255, 255, 255, 0.4)` | `rgba(255, 255, 255, 0.4)` | `#3ff23f`（GrayText） |
| `colorBrandForegroundLink` | `#115ea3`（brand 70） | `#479ef5`（brand 100） | `#ffff00`（LinkText） |
| `colorBrandForegroundLinkHover` | `#0f548c`（brand 60） | `#62abf5`（brand 110） | `#ffff00`（LinkText） |
| `colorBrandForegroundLinkPressed` | `#0c3b5e`（brand 40） | `#2886de`（brand 90） | `#ffff00`（LinkText） |
| `colorBrandForegroundLinkSelected` | `#115ea3`（brand 70） | `#479ef5`（brand 100） | `#ffff00`（LinkText） |
| `colorNeutralForeground2Link` | `#424242` | `#d6d6d6` | `#ffff00`（LinkText） |
| `colorNeutralForeground2LinkHover` | `#242424` | `#ffffff` | `#ffff00`（LinkText） |
| `colorNeutralForeground2LinkPressed` | `#242424` | `#ffffff` | `#ffff00`（LinkText） |
| `colorNeutralForeground2LinkSelected` | `#242424` | `#ffffff` | `#ffff00`（LinkText） |
| `colorCompoundBrandForeground1` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#1aebff`（Highlight） |
| `colorCompoundBrandForeground1Hover` | `#115ea3`（brand 70） | `#62abf5`（brand 110） | `#1aebff`（Highlight） |
| `colorCompoundBrandForeground1Pressed` | `#0f548c`（brand 60） | `#2886de`（brand 90） | `#1aebff`（Highlight） |
| `colorBrandForeground1` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#ffffff`（CanvasText） |
| `colorBrandForeground2` | `#115ea3`（brand 70） | `#62abf5`（brand 110） | `#ffffff`（CanvasText） |
| `colorBrandForeground2Hover` | `#0f548c`（brand 60） | `#96c6fa`（brand 130） | `#ffffff`（CanvasText） |
| `colorBrandForeground2Pressed` | `#0a2e4a`（brand 30） | `#ebf3fc`（brand 160） | `#ffffff`（CanvasText） |
| `colorNeutralForeground1Static` | `#242424` | `#242424` | `#000000`（Canvas） |
| `colorNeutralForegroundStaticInverted` | `#ffffff` | `#ffffff` | `#ffffff`（CanvasText） |
| `colorNeutralForegroundInverted` | `#ffffff` | `#242424` | `#000000`（HighlightText） |
| `colorNeutralForegroundInvertedHover` | `#ffffff` | `#242424` | `#000000`（HighlightText） |
| `colorNeutralForegroundInvertedPressed` | `#ffffff` | `#242424` | `#000000`（HighlightText） |
| `colorNeutralForegroundInvertedSelected` | `#ffffff` | `#242424` | `#000000`（HighlightText） |
| `colorNeutralForegroundInverted2` | `#ffffff` | `#242424` | `#ffffff`（CanvasText） |
| `colorNeutralForegroundOnBrand` | `#ffffff` | `#ffffff` | `#000000`（ButtonText） |
| `colorNeutralForegroundInvertedLink` | `#ffffff` | `#ffffff` | `#ffff00`（LinkText） |
| `colorNeutralForegroundInvertedLinkHover` | `#ffffff` | `#ffffff` | `#ffff00`（LinkText） |
| `colorNeutralForegroundInvertedLinkPressed` | `#ffffff` | `#ffffff` | `#ffff00`（LinkText） |
| `colorNeutralForegroundInvertedLinkSelected` | `#ffffff` | `#ffffff` | `#ffff00`（LinkText） |
| `colorBrandForegroundInverted` | `#479ef5`（brand 100） | `#0f6cbd`（brand 80） | `#ffffff`（CanvasText） |
| `colorBrandForegroundInvertedHover` | `#62abf5`（brand 110） | `#115ea3`（brand 70） | `#000000`（HighlightText） |
| `colorBrandForegroundInvertedPressed` | `#479ef5`（brand 100） | `#0f548c`（brand 60） | `#000000`（HighlightText） |
| `colorBrandForegroundOnLight` | `#0f6cbd`（brand 80） | `#0f6cbd`（brand 80） | `#000000`（ButtonText） |
| `colorBrandForegroundOnLightHover` | `#115ea3`（brand 70） | `#115ea3`（brand 70） | `#000000`（HighlightText） |
| `colorBrandForegroundOnLightPressed` | `#0e4775`（brand 50） | `#0e4775`（brand 50） | `#000000`（HighlightText） |
| `colorBrandForegroundOnLightSelected` | `#0f548c`（brand 60） | `#0f548c`（brand 60） | `#000000`（HighlightText） |
| `colorNeutralBackground1` | `#ffffff` | `#292929` | `#000000`（Canvas） |
| `colorNeutralBackground1Hover` | `#f5f5f5` | `#3d3d3d` | `#1aebff`（Highlight） |
| `colorNeutralBackground1Pressed` | `#e0e0e0` | `#1f1f1f` | `#1aebff`（Highlight） |
| `colorNeutralBackground1Selected` | `#ebebeb` | `#383838` | `#1aebff`（Highlight） |
| `colorNeutralBackground2` | `#fafafa` | `#1f1f1f` | `#000000`（Canvas） |
| `colorNeutralBackground2Hover` | `#f0f0f0` | `#333333` | `#1aebff`（Highlight） |
| `colorNeutralBackground2Pressed` | `#dbdbdb` | `#141414` | `#1aebff`（Highlight） |
| `colorNeutralBackground2Selected` | `#e6e6e6` | `#2e2e2e` | `#1aebff`（Highlight） |
| `colorNeutralBackground3` | `#f5f5f5` | `#141414` | `#000000`（Canvas） |
| `colorNeutralBackground3Hover` | `#ebebeb` | `#292929` | `#1aebff`（Highlight） |
| `colorNeutralBackground3Pressed` | `#d6d6d6` | `#0a0a0a` | `#1aebff`（Highlight） |
| `colorNeutralBackground3Selected` | `#e0e0e0` | `#242424` | `#1aebff`（Highlight） |
| `colorNeutralBackground4` | `#f0f0f0` | `#0a0a0a` | `#000000`（Canvas） |
| `colorNeutralBackground4Hover` | `#fafafa` | `#1f1f1f` | `#1aebff`（Highlight） |
| `colorNeutralBackground4Pressed` | `#f5f5f5` | `#000000` | `#1aebff`（Highlight） |
| `colorNeutralBackground4Selected` | `#ffffff` | `#1a1a1a` | `#1aebff`（Highlight） |
| `colorNeutralBackground5` | `#ebebeb` | `#000000` | `#000000`（Canvas） |
| `colorNeutralBackground5Hover` | `#f5f5f5` | `#141414` | `#1aebff`（Highlight） |
| `colorNeutralBackground5Pressed` | `#f0f0f0` | `#050505` | `#1aebff`（Highlight） |
| `colorNeutralBackground5Selected` | `#fafafa` | `#0f0f0f` | `#1aebff`（Highlight） |
| `colorNeutralBackground6` | `#e6e6e6` | `#333333` | `#000000`（Canvas） |
| `colorNeutralBackground7` | `#00000000` | `#00000000` | `#000000`（Canvas） |
| `colorNeutralBackground7Hover` | `#ebebeb` | `#1a1a1a` | `#1aebff`（Highlight） |
| `colorNeutralBackground7Pressed` | `#d6d6d6` | `#0a0a0a` | `#1aebff`（Highlight） |
| `colorNeutralBackground7Selected` | `#00000000` | `#00000000` | `#1aebff`（Highlight） |
| `colorNeutralBackground8` | `#fcfcfc` | `#292929` | `#000000`（Canvas） |
| `colorNeutralBackgroundInverted` | `#292929` | `#ffffff` | `#000000`（Canvas） |
| `colorNeutralBackgroundInvertedHover` | `#3d3d3d` | `#f5f5f5` | `#1aebff`（Highlight） |
| `colorNeutralBackgroundInvertedPressed` | `#1f1f1f` | `#e0e0e0` | `#1aebff`（Highlight） |
| `colorNeutralBackgroundInvertedSelected` | `#383838` | `#ebebeb` | `#1aebff`（Highlight） |
| `colorNeutralBackgroundStatic` | `#333333` | `#3d3d3d` | `#000000`（Canvas） |
| `colorNeutralBackgroundAlpha` | `rgba(255, 255, 255, 0.5)` | `rgba(26, 26, 26, 0.5)` | `#000000`（Canvas） |
| `colorNeutralBackgroundAlpha2` | `rgba(255, 255, 255, 0.8)` | `rgba(31, 31, 31, 0.7)` | `#000000`（Canvas） |
| `colorSubtleBackground` | `transparent` | `transparent` | `transparent` |
| `colorSubtleBackgroundHover` | `#f5f5f5` | `#383838` | `#1aebff`（Highlight） |
| `colorSubtleBackgroundPressed` | `#e0e0e0` | `#2e2e2e` | `#1aebff`（Highlight） |
| `colorSubtleBackgroundSelected` | `#ebebeb` | `#333333` | `#1aebff`（Highlight） |
| `colorSubtleBackgroundLightAlphaHover` | `rgba(255, 255, 255, 0.7)` | `rgba(36, 36, 36, 0.8)` | `#1aebff`（Highlight） |
| `colorSubtleBackgroundLightAlphaPressed` | `rgba(255, 255, 255, 0.5)` | `rgba(36, 36, 36, 0.5)` | `#1aebff`（Highlight） |
| `colorSubtleBackgroundLightAlphaSelected` | `transparent` | `transparent` | `#1aebff`（Highlight） |
| `colorSubtleBackgroundInverted` | `transparent` | `transparent` | `transparent` |
| `colorSubtleBackgroundInvertedHover` | `rgba(0, 0, 0, 0.1)` | `rgba(0, 0, 0, 0.1)` | `#1aebff`（Highlight） |
| `colorSubtleBackgroundInvertedPressed` | `rgba(0, 0, 0, 0.3)` | `rgba(0, 0, 0, 0.3)` | `#1aebff`（Highlight） |
| `colorSubtleBackgroundInvertedSelected` | `rgba(0, 0, 0, 0.2)` | `rgba(0, 0, 0, 0.2)` | `#1aebff`（Highlight） |
| `colorTransparentBackground` | `transparent` | `transparent` | `transparent` |
| `colorTransparentBackgroundHover` | `transparent` | `transparent` | `#1aebff`（Highlight） |
| `colorTransparentBackgroundPressed` | `transparent` | `transparent` | `#1aebff`（Highlight） |
| `colorTransparentBackgroundSelected` | `transparent` | `transparent` | `#1aebff`（Highlight） |
| `colorNeutralBackgroundDisabled` | `#f0f0f0` | `#141414` | `#000000`（Canvas） |
| `colorNeutralBackgroundDisabled2` | `#ffffff` | `#292929` | `#3ff23f`（GrayText） |
| `colorNeutralBackgroundInvertedDisabled` | `rgba(255, 255, 255, 0.1)` | `rgba(255, 255, 255, 0.1)` | `#000000`（Canvas） |
| `colorNeutralStencil1` | `#e6e6e6` | `#575757` | `#ffffff`（CanvasText） |
| `colorNeutralStencil2` | `#fafafa` | `#333333` | `#ffffff`（CanvasText） |
| `colorNeutralStencil1Alpha` | `rgba(0, 0, 0, 0.1)` | `rgba(255, 255, 255, 0.1)` | `#ffffff`（CanvasText） |
| `colorNeutralStencil2Alpha` | `rgba(0, 0, 0, 0.05)` | `rgba(255, 255, 255, 0.05)` | `#ffffff`（CanvasText） |
| `colorBackgroundOverlay` | `rgba(0, 0, 0, 0.4)` | `rgba(0, 0, 0, 0.5)` | `rgba(0, 0, 0, 0.5)` |
| `colorScrollbarOverlay` | `rgba(0, 0, 0, 0.5)` | `rgba(255, 255, 255, 0.6)` | `#ffffff`（ButtonFace） |
| `colorBrandBackground` | `#0f6cbd`（brand 80） | `#115ea3`（brand 70） | `#ffffff`（ButtonFace） |
| `colorBrandBackgroundHover` | `#115ea3`（brand 70） | `#0f6cbd`（brand 80） | `#1aebff`（Highlight） |
| `colorBrandBackgroundPressed` | `#0c3b5e`（brand 40） | `#0c3b5e`（brand 40） | `#1aebff`（Highlight） |
| `colorBrandBackgroundSelected` | `#0f548c`（brand 60） | `#0f548c`（brand 60） | `#1aebff`（Highlight） |
| `colorCompoundBrandBackground` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#1aebff`（Highlight） |
| `colorCompoundBrandBackgroundHover` | `#115ea3`（brand 70） | `#62abf5`（brand 110） | `#1aebff`（Highlight） |
| `colorCompoundBrandBackgroundPressed` | `#0f548c`（brand 60） | `#2886de`（brand 90） | `#1aebff`（Highlight） |
| `colorBrandBackgroundStatic` | `#0f6cbd`（brand 80） | `#0f6cbd`（brand 80） | `#000000`（Canvas） |
| `colorBrandBackground2` | `#ebf3fc`（brand 160） | `#082338`（brand 20） | `#000000`（Canvas） |
| `colorBrandBackground2Hover` | `#cfe4fa`（brand 150） | `#0c3b5e`（brand 40） | `#000000`（Canvas） |
| `colorBrandBackground2Pressed` | `#96c6fa`（brand 130） | `#061724`（brand 10） | `#000000`（Canvas） |
| `colorBrandBackground3Static` | `#0f548c`（brand 60） | `#0f548c`（brand 60） | `#000000`（Canvas） |
| `colorBrandBackground4Static` | `#0c3b5e`（brand 40） | `#0c3b5e`（brand 40） | `#000000`（Canvas） |
| `colorBrandBackgroundInverted` | `#ffffff` | `#ffffff` | `#ffffff`（ButtonFace） |
| `colorBrandBackgroundInvertedHover` | `#ebf3fc`（brand 160） | `#ebf3fc`（brand 160） | `#1aebff`（Highlight） |
| `colorBrandBackgroundInvertedPressed` | `#b4d6fa`（brand 140） | `#b4d6fa`（brand 140） | `#1aebff`（Highlight） |
| `colorBrandBackgroundInvertedSelected` | `#cfe4fa`（brand 150） | `#cfe4fa`（brand 150） | `#1aebff`（Highlight） |
| `colorNeutralCardBackground` | `#fafafa` | `#333333` | `#000000`（Canvas） |
| `colorNeutralCardBackgroundHover` | `#ffffff` | `#3d3d3d` | `#1aebff`（Highlight） |
| `colorNeutralCardBackgroundPressed` | `#f5f5f5` | `#2e2e2e` | `#1aebff`（Highlight） |
| `colorNeutralCardBackgroundSelected` | `#ebebeb` | `#383838` | `#1aebff`（Highlight） |
| `colorNeutralCardBackgroundDisabled` | `#f0f0f0` | `#141414` | `#000000`（Canvas） |
| `colorNeutralStrokeAccessible` | `#616161` | `#adadad` | `#ffffff`（CanvasText） |
| `colorNeutralStrokeAccessibleHover` | `#575757` | `#bdbdbd` | `#1aebff`（Highlight） |
| `colorNeutralStrokeAccessiblePressed` | `#4d4d4d` | `#b3b3b3` | `#1aebff`（Highlight） |
| `colorNeutralStrokeAccessibleSelected` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#1aebff`（Highlight） |
| `colorNeutralStroke1` | `#d1d1d1` | `#666666` | `#ffffff`（CanvasText） |
| `colorNeutralStroke1Hover` | `#c7c7c7` | `#757575` | `#1aebff`（Highlight） |
| `colorNeutralStroke1Pressed` | `#b3b3b3` | `#6b6b6b` | `#1aebff`（Highlight） |
| `colorNeutralStroke1Selected` | `#bdbdbd` | `#707070` | `#1aebff`（Highlight） |
| `colorNeutralStroke2` | `#e0e0e0` | `#525252` | `#ffffff`（CanvasText） |
| `colorNeutralStroke3` | `#f0f0f0` | `#3d3d3d` | `#ffffff`（CanvasText） |
| `colorNeutralStroke4` | `#ebebeb` | `#3d3d3d` | `#ffffff`（CanvasText） |
| `colorNeutralStroke4Hover` | `#e0e0e0` | `#2e2e2e` | `#1aebff`（Highlight） |
| `colorNeutralStroke4Pressed` | `#d6d6d6` | `#242424` | `#1aebff`（Highlight） |
| `colorNeutralStroke4Selected` | `#ebebeb` | `#3d3d3d` | `#1aebff`（Highlight） |
| `colorNeutralStrokeSubtle` | `#e0e0e0` | `#0a0a0a` | `#ffffff`（CanvasText） |
| `colorNeutralStrokeOnBrand` | `#ffffff` | `#292929` | `#000000`（Canvas） |
| `colorNeutralStrokeOnBrand2` | `#ffffff` | `#ffffff` | `#ffffff`（CanvasText） |
| `colorNeutralStrokeOnBrand2Hover` | `#ffffff` | `#ffffff` | `#ffffff`（CanvasText） |
| `colorNeutralStrokeOnBrand2Pressed` | `#ffffff` | `#ffffff` | `#ffffff`（CanvasText） |
| `colorNeutralStrokeOnBrand2Selected` | `#ffffff` | `#ffffff` | `#ffffff`（CanvasText） |
| `colorBrandStroke1` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#ffffff`（CanvasText） |
| `colorBrandStroke2` | `#b4d6fa`（brand 140） | `#0e4775`（brand 50） | `#ffffff`（CanvasText） |
| `colorBrandStroke2Hover` | `#77b7f7`（brand 120） | `#0e4775`（brand 50） | `#1aebff`（Highlight） |
| `colorBrandStroke2Pressed` | `#0f6cbd`（brand 80） | `#0a2e4a`（brand 30） | `#1aebff`（Highlight） |
| `colorBrandStroke2Contrast` | `#b4d6fa`（brand 140） | `#0e4775`（brand 50） | `#000000`（Canvas） |
| `colorCompoundBrandStroke` | `#0f6cbd`（brand 80） | `#479ef5`（brand 100） | `#1aebff`（Highlight） |
| `colorCompoundBrandStrokeHover` | `#115ea3`（brand 70） | `#62abf5`（brand 110） | `#1aebff`（Highlight） |
| `colorCompoundBrandStrokePressed` | `#0f548c`（brand 60） | `#2886de`（brand 90） | `#1aebff`（Highlight） |
| `colorNeutralStrokeDisabled` | `#e0e0e0` | `#424242` | `#3ff23f`（GrayText） |
| `colorNeutralStrokeDisabled2` | `#ebebeb` | `#3d3d3d` | `#3ff23f`（GrayText） |
| `colorNeutralStrokeInvertedDisabled` | `rgba(255, 255, 255, 0.4)` | `rgba(255, 255, 255, 0.4)` | `#3ff23f`（GrayText） |
| `colorTransparentStroke` | `transparent` | `transparent` | `#ffffff`（CanvasText） |
| `colorTransparentStrokeInteractive` | `transparent` | `transparent` | `#1aebff`（Highlight） |
| `colorTransparentStrokeDisabled` | `transparent` | `transparent` | `#3ff23f`（GrayText） |
| `colorNeutralStrokeAlpha` | `rgba(0, 0, 0, 0.05)` | `rgba(255, 255, 255, 0.1)` | `#ffffff`（CanvasText） |
| `colorNeutralStrokeAlpha2` | `rgba(255, 255, 255, 0.2)` | `rgba(255, 255, 255, 0.2)` | `#000000`（Canvas） |
| `colorStrokeFocus1` | `#ffffff` | `#000000` | `#000000`（Canvas） |
| `colorStrokeFocus2` | `#000000` | `#ffffff` | `#1aebff`（Highlight） |
| `colorNeutralShadowAmbient` | `rgba(0,0,0,0.12)` | `rgba(0,0,0,0.24)` | `rgba(0,0,0,0.24)` |
| `colorNeutralShadowKey` | `rgba(0,0,0,0.14)` | `rgba(0,0,0,0.28)` | `rgba(0,0,0,0.28)` |
| `colorNeutralShadowAmbientLighter` | `rgba(0,0,0,0.06)` | `rgba(0,0,0,0.12)` | `rgba(0,0,0,0.12)` |
| `colorNeutralShadowKeyLighter` | `rgba(0,0,0,0.07)` | `rgba(0,0,0,0.14)` | `rgba(0,0,0,0.14)` |
| `colorNeutralShadowAmbientDarker` | `rgba(0,0,0,0.20)` | `rgba(0,0,0,0.40)` | `rgba(0,0,0,0.40)` |
| `colorNeutralShadowKeyDarker` | `rgba(0,0,0,0.24)` | `rgba(0,0,0,0.48)` | `rgba(0,0,0,0.48)` |
| `colorBrandShadowAmbient` | `rgba(0,0,0,0.30)` | `rgba(0,0,0,0.30)` | `rgba(0,0,0,0.30)` |
| `colorBrandShadowKey` | `rgba(0,0,0,0.25)` | `rgba(0,0,0,0.25)` | `rgba(0,0,0,0.25)` |
| `colorPaletteRedBackground1` | `#fdf6f6` | `#3f1011` | `#000000`（Canvas） |
| `colorPaletteRedBackground2` | `#f1bbbc` | `#751d1f` | `#000000`（Canvas） |
| `colorPaletteRedBackground3` | `#d13438` | `#d13438` | `#ffffff`（CanvasText） |
| `colorPaletteRedForeground1` | `#bc2f32` | `#e37d80` | `#ffffff`（CanvasText） |
| `colorPaletteRedForeground2` | `#751d1f` | `#f1bbbc` | `#ffffff`（CanvasText） |
| `colorPaletteRedForeground3` | `#d13438` | `#e37d80` | `#ffffff`（CanvasText） |
| `colorPaletteRedBorderActive` | `#d13438` | `#e37d80` | `#1aebff`（Highlight） |
| `colorPaletteRedBorder1` | `#f1bbbc` | `#d13438` | `#ffffff`（CanvasText） |
| `colorPaletteRedBorder2` | `#d13438` | `#e37d80` | `#ffffff`（CanvasText） |
| `colorPaletteGreenBackground1` | `#f1faf1` | `#052505` | `#000000`（Canvas） |
| `colorPaletteGreenBackground2` | `#9fd89f` | `#094509` | `#000000`（Canvas） |
| `colorPaletteGreenBackground3` | `#107c10` | `#107c10` | `#ffffff`（CanvasText） |
| `colorPaletteGreenForeground1` | `#0e700e` | `#54b054` | `#ffffff`（CanvasText） |
| `colorPaletteGreenForeground2` | `#094509` | `#9fd89f` | `#ffffff`（CanvasText） |
| `colorPaletteGreenForeground3` | `#107c10` | `#9fd89f` | `#ffffff`（CanvasText） |
| `colorPaletteGreenBorderActive` | `#107c10` | `#54b054` | `#1aebff`（Highlight） |
| `colorPaletteGreenBorder1` | `#9fd89f` | `#107c10` | `#ffffff`（CanvasText） |
| `colorPaletteGreenBorder2` | `#107c10` | `#9fd89f` | `#ffffff`（CanvasText） |
| `colorPaletteDarkOrangeBackground1` | `#fdf6f3` | `#411200` | `#000000`（Canvas） |
| `colorPaletteDarkOrangeBackground2` | `#f4bfab` | `#7a2101` | `#000000`（Canvas） |
| `colorPaletteDarkOrangeBackground3` | `#da3b01` | `#da3b01` | `#ffffff`（CanvasText） |
| `colorPaletteDarkOrangeForeground1` | `#c43501` | `#e9835e` | `#ffffff`（CanvasText） |
| `colorPaletteDarkOrangeForeground2` | `#7a2101` | `#f4bfab` | `#ffffff`（CanvasText） |
| `colorPaletteDarkOrangeForeground3` | `#da3b01` | `#e9835e` | `#ffffff`（CanvasText） |
| `colorPaletteDarkOrangeBorderActive` | `#da3b01` | `#e9835e` | `#1aebff`（Highlight） |
| `colorPaletteDarkOrangeBorder1` | `#f4bfab` | `#da3b01` | `#ffffff`（CanvasText） |
| `colorPaletteDarkOrangeBorder2` | `#da3b01` | `#e9835e` | `#ffffff`（CanvasText） |
| `colorPaletteYellowBackground1` | `#fffef5` | `#4c4400` | `#000000`（Canvas） |
| `colorPaletteYellowBackground2` | `#fef7b2` | `#817400` | `#000000`（Canvas） |
| `colorPaletteYellowBackground3` | `#fde300` | `#fde300` | `#ffffff`（CanvasText） |
| `colorPaletteYellowForeground1` | `#817400` | `#feee66` | `#ffffff`（CanvasText） |
| `colorPaletteYellowForeground2` | `#817400` | `#fef7b2` | `#ffffff`（CanvasText） |
| `colorPaletteYellowForeground3` | `#fde300` | `#fdea3d` | `#ffffff`（CanvasText） |
| `colorPaletteYellowBorderActive` | `#fde300` | `#feee66` | `#1aebff`（Highlight） |
| `colorPaletteYellowBorder1` | `#fef7b2` | `#fde300` | `#ffffff`（CanvasText） |
| `colorPaletteYellowBorder2` | `#fde300` | `#fdea3d` | `#ffffff`（CanvasText） |
| `colorPaletteBerryBackground1` | `#fdf5fc` | `#3a1136` | `#000000`（Canvas） |
| `colorPaletteBerryBackground2` | `#edbbe7` | `#6d2064` | `#000000`（Canvas） |
| `colorPaletteBerryBackground3` | `#c239b3` | `#c239b3` | `#ffffff`（CanvasText） |
| `colorPaletteBerryForeground1` | `#af33a1` | `#da7ed0` | `#ffffff`（CanvasText） |
| `colorPaletteBerryForeground2` | `#6d2064` | `#edbbe7` | `#ffffff`（CanvasText） |
| `colorPaletteBerryForeground3` | `#c239b3` | `#d161c4` | `#ffffff`（CanvasText） |
| `colorPaletteBerryBorderActive` | `#c239b3` | `#da7ed0` | `#1aebff`（Highlight） |
| `colorPaletteBerryBorder1` | `#edbbe7` | `#c239b3` | `#ffffff`（CanvasText） |
| `colorPaletteBerryBorder2` | `#c239b3` | `#d161c4` | `#ffffff`（CanvasText） |
| `colorPaletteLightGreenBackground1` | `#f2fbf2` | `#063004` | `#000000`（Canvas） |
| `colorPaletteLightGreenBackground2` | `#a7e3a5` | `#0b5a08` | `#000000`（Canvas） |
| `colorPaletteLightGreenBackground3` | `#13a10e` | `#13a10e` | `#ffffff`（CanvasText） |
| `colorPaletteLightGreenForeground1` | `#11910d` | `#5ec75a` | `#ffffff`（CanvasText） |
| `colorPaletteLightGreenForeground2` | `#0b5a08` | `#a7e3a5` | `#ffffff`（CanvasText） |
| `colorPaletteLightGreenForeground3` | `#13a10e` | `#3db838` | `#ffffff`（CanvasText） |
| `colorPaletteLightGreenBorderActive` | `#13a10e` | `#5ec75a` | `#1aebff`（Highlight） |
| `colorPaletteLightGreenBorder1` | `#a7e3a5` | `#13a10e` | `#ffffff`（CanvasText） |
| `colorPaletteLightGreenBorder2` | `#13a10e` | `#3db838` | `#ffffff`（CanvasText） |
| `colorPaletteMarigoldBackground1` | `#fefbf4` | `#463100` | `#000000`（Canvas） |
| `colorPaletteMarigoldBackground2` | `#f9e2ae` | `#835b00` | `#000000`（Canvas） |
| `colorPaletteMarigoldBackground3` | `#eaa300` | `#eaa300` | `#ffffff`（CanvasText） |
| `colorPaletteMarigoldForeground1` | `#d39300` | `#f2c661` | `#ffffff`（CanvasText） |
| `colorPaletteMarigoldForeground2` | `#835b00` | `#f9e2ae` | `#ffffff`（CanvasText） |
| `colorPaletteMarigoldForeground3` | `#eaa300` | `#efb839` | `#ffffff`（CanvasText） |
| `colorPaletteMarigoldBorderActive` | `#eaa300` | `#f2c661` | `#1aebff`（Highlight） |
| `colorPaletteMarigoldBorder1` | `#f9e2ae` | `#eaa300` | `#ffffff`（CanvasText） |
| `colorPaletteMarigoldBorder2` | `#eaa300` | `#efb839` | `#ffffff`（CanvasText） |
| `colorPaletteRedForegroundInverted` | `#dc5e62` | `#d13438` | `#ffffff`（CanvasText） |
| `colorPaletteGreenForegroundInverted` | `#359b35` | `#107c10` | `#ffffff`（CanvasText） |
| `colorPaletteYellowForegroundInverted` | `#fef7b2` | `#817400` | `#ffffff`（CanvasText） |
| `colorPaletteDarkRedBackground2` | `#d69ca5` | `#590815` | `#000000`（Canvas） |
| `colorPaletteDarkRedForeground2` | `#420610` | `#d69ca5` | `#ffffff`（CanvasText） |
| `colorPaletteDarkRedBorderActive` | `#750b1c` | `#ac4f5e` | `#1aebff`（Highlight） |
| `colorPaletteCranberryBackground2` | `#eeacb2` | `#6e0811` | `#000000`（Canvas） |
| `colorPaletteCranberryForeground2` | `#6e0811` | `#eeacb2` | `#ffffff`（CanvasText） |
| `colorPaletteCranberryBorderActive` | `#c50f1f` | `#dc626d` | `#1aebff`（Highlight） |
| `colorPalettePumpkinBackground2` | `#efc4ad` | `#712d09` | `#000000`（Canvas） |
| `colorPalettePumpkinForeground2` | `#712d09` | `#efc4ad` | `#ffffff`（CanvasText） |
| `colorPalettePumpkinBorderActive` | `#ca5010` | `#df8e64` | `#1aebff`（Highlight） |
| `colorPalettePeachBackground2` | `#ffddb3` | `#8f4e00` | `#000000`（Canvas） |
| `colorPalettePeachForeground2` | `#8f4e00` | `#ffddb3` | `#ffffff`（CanvasText） |
| `colorPalettePeachBorderActive` | `#ff8c00` | `#ffba66` | `#1aebff`（Highlight） |
| `colorPaletteGoldBackground2` | `#ecdfa5` | `#6c5700` | `#000000`（Canvas） |
| `colorPaletteGoldForeground2` | `#6c5700` | `#ecdfa5` | `#ffffff`（CanvasText） |
| `colorPaletteGoldBorderActive` | `#c19c00` | `#dac157` | `#1aebff`（Highlight） |
| `colorPaletteBrassBackground2` | `#e0cea2` | `#553e06` | `#000000`（Canvas） |
| `colorPaletteBrassForeground2` | `#553e06` | `#e0cea2` | `#ffffff`（CanvasText） |
| `colorPaletteBrassBorderActive` | `#986f0b` | `#c1a256` | `#1aebff`（Highlight） |
| `colorPaletteBrownBackground2` | `#ddc3b0` | `#50301a` | `#000000`（Canvas） |
| `colorPaletteBrownForeground2` | `#50301a` | `#ddc3b0` | `#ffffff`（CanvasText） |
| `colorPaletteBrownBorderActive` | `#8e562e` | `#bb8f6f` | `#1aebff`（Highlight） |
| `colorPaletteForestBackground2` | `#bdd99b` | `#294903` | `#000000`（Canvas） |
| `colorPaletteForestForeground2` | `#294903` | `#bdd99b` | `#ffffff`（CanvasText） |
| `colorPaletteForestBorderActive` | `#498205` | `#85b44c` | `#1aebff`（Highlight） |
| `colorPaletteSeafoamBackground2` | `#a8f0cd` | `#00723b` | `#000000`（Canvas） |
| `colorPaletteSeafoamForeground2` | `#00723b` | `#a8f0cd` | `#ffffff`（CanvasText） |
| `colorPaletteSeafoamBorderActive` | `#00cc6a` | `#5ae0a0` | `#1aebff`（Highlight） |
| `colorPaletteDarkGreenBackground2` | `#9ad29a` | `#063b06` | `#000000`（Canvas） |
| `colorPaletteDarkGreenForeground2` | `#063b06` | `#9ad29a` | `#ffffff`（CanvasText） |
| `colorPaletteDarkGreenBorderActive` | `#0b6a0b` | `#4da64d` | `#1aebff`（Highlight） |
| `colorPaletteLightTealBackground2` | `#a6e9ed` | `#00666d` | `#000000`（Canvas） |
| `colorPaletteLightTealForeground2` | `#00666d` | `#a6e9ed` | `#ffffff`（CanvasText） |
| `colorPaletteLightTealBorderActive` | `#00b7c3` | `#58d3db` | `#1aebff`（Highlight） |
| `colorPaletteTealBackground2` | `#9bd9db` | `#02494c` | `#000000`（Canvas） |
| `colorPaletteTealForeground2` | `#02494c` | `#9bd9db` | `#ffffff`（CanvasText） |
| `colorPaletteTealBorderActive` | `#038387` | `#4cb4b7` | `#1aebff`（Highlight） |
| `colorPaletteSteelBackground2` | `#94c8d4` | `#00333f` | `#000000`（Canvas） |
| `colorPaletteSteelForeground2` | `#00333f` | `#94c8d4` | `#ffffff`（CanvasText） |
| `colorPaletteSteelBorderActive` | `#005b70` | `#4496a9` | `#1aebff`（Highlight） |
| `colorPaletteBlueBackground2` | `#a9d3f2` | `#004377` | `#000000`（Canvas） |
| `colorPaletteBlueForeground2` | `#004377` | `#a9d3f2` | `#ffffff`（CanvasText） |
| `colorPaletteBlueBorderActive` | `#0078d4` | `#5caae5` | `#1aebff`（Highlight） |
| `colorPaletteRoyalBlueBackground2` | `#9abfdc` | `#002c4e` | `#000000`（Canvas） |
| `colorPaletteRoyalBlueForeground2` | `#002c4e` | `#9abfdc` | `#ffffff`（CanvasText） |
| `colorPaletteRoyalBlueBorderActive` | `#004e8c` | `#4a89ba` | `#1aebff`（Highlight） |
| `colorPaletteCornflowerBackground2` | `#c8d1fa` | `#2c3c85` | `#000000`（Canvas） |
| `colorPaletteCornflowerForeground2` | `#2c3c85` | `#c8d1fa` | `#ffffff`（CanvasText） |
| `colorPaletteCornflowerBorderActive` | `#4f6bed` | `#93a4f4` | `#1aebff`（Highlight） |
| `colorPaletteNavyBackground2` | `#a3b2e8` | `#001665` | `#000000`（Canvas） |
| `colorPaletteNavyForeground2` | `#001665` | `#a3b2e8` | `#ffffff`（CanvasText） |
| `colorPaletteNavyBorderActive` | `#0027b4` | `#546fd2` | `#1aebff`（Highlight） |
| `colorPaletteLavenderBackground2` | `#d2ccf8` | `#3f3682` | `#000000`（Canvas） |
| `colorPaletteLavenderForeground2` | `#3f3682` | `#d2ccf8` | `#ffffff`（CanvasText） |
| `colorPaletteLavenderBorderActive` | `#7160e8` | `#a79cf1` | `#1aebff`（Highlight） |
| `colorPalettePurpleBackground2` | `#c6b1de` | `#341a51` | `#000000`（Canvas） |
| `colorPalettePurpleForeground2` | `#341a51` | `#c6b1de` | `#ffffff`（CanvasText） |
| `colorPalettePurpleBorderActive` | `#5c2e91` | `#9470bd` | `#1aebff`（Highlight） |
| `colorPaletteGrapeBackground2` | `#d9a7e0` | `#4c0d55` | `#000000`（Canvas） |
| `colorPaletteGrapeForeground2` | `#4c0d55` | `#d9a7e0` | `#ffffff`（CanvasText） |
| `colorPaletteGrapeBorderActive` | `#881798` | `#b55fc1` | `#1aebff`（Highlight） |
| `colorPaletteLilacBackground2` | `#e6bfed` | `#63276d` | `#000000`（Canvas） |
| `colorPaletteLilacForeground2` | `#63276d` | `#e6bfed` | `#ffffff`（CanvasText） |
| `colorPaletteLilacBorderActive` | `#b146c2` | `#cf87da` | `#1aebff`（Highlight） |
| `colorPalettePinkBackground2` | `#f7c0e3` | `#80215d` | `#000000`（Canvas） |
| `colorPalettePinkForeground2` | `#80215d` | `#f7c0e3` | `#ffffff`（CanvasText） |
| `colorPalettePinkBorderActive` | `#e43ba6` | `#ef85c8` | `#1aebff`（Highlight） |
| `colorPaletteMagentaBackground2` | `#eca5d1` | `#6b0043` | `#000000`（Canvas） |
| `colorPaletteMagentaForeground2` | `#6b0043` | `#eca5d1` | `#ffffff`（CanvasText） |
| `colorPaletteMagentaBorderActive` | `#bf0077` | `#d957a8` | `#1aebff`（Highlight） |
| `colorPalettePlumBackground2` | `#d696c0` | `#5a003b` | `#000000`（Canvas） |
| `colorPalettePlumForeground2` | `#43002b` | `#d696c0` | `#ffffff`（CanvasText） |
| `colorPalettePlumBorderActive` | `#77004d` | `#ad4589` | `#1aebff`（Highlight） |
| `colorPaletteBeigeBackground2` | `#d7d4d4` | `#444241` | `#000000`（Canvas） |
| `colorPaletteBeigeForeground2` | `#444241` | `#d7d4d4` | `#ffffff`（CanvasText） |
| `colorPaletteBeigeBorderActive` | `#7a7574` | `#afabaa` | `#1aebff`（Highlight） |
| `colorPaletteMinkBackground2` | `#cecccb` | `#343231` | `#000000`（Canvas） |
| `colorPaletteMinkForeground2` | `#343231` | `#cecccb` | `#ffffff`（CanvasText） |
| `colorPaletteMinkBorderActive` | `#5d5a58` | `#9e9b99` | `#1aebff`（Highlight） |
| `colorPalettePlatinumBackground2` | `#cdd6d8` | `#3b4447` | `#000000`（Canvas） |
| `colorPalettePlatinumForeground2` | `#3b4447` | `#cdd6d8` | `#ffffff`（CanvasText） |
| `colorPalettePlatinumBorderActive` | `#69797e` | `#a0adb2` | `#1aebff`（Highlight） |
| `colorPaletteAnchorBackground2` | `#bcc3c7` | `#202427` | `#000000`（Canvas） |
| `colorPaletteAnchorForeground2` | `#202427` | `#bcc3c7` | `#ffffff`（CanvasText） |
| `colorPaletteAnchorBorderActive` | `#394146` | `#808a90` | `#1aebff`（Highlight） |
| `colorStatusSuccessBackground1` | `#f1faf1` | `#052505` | `#000000`（Canvas） |
| `colorStatusSuccessBackground2` | `#9fd89f` | `#094509` | `#000000`（Canvas） |
| `colorStatusSuccessBackground3` | `#107c10` | `#107c10` | `#ffffff`（CanvasText） |
| `colorStatusSuccessForeground1` | `#0e700e` | `#54b054` | `#ffffff`（CanvasText） |
| `colorStatusSuccessForeground2` | `#094509` | `#9fd89f` | `#ffffff`（CanvasText） |
| `colorStatusSuccessForeground3` | `#107c10` | `#9fd89f` | `#ffffff`（CanvasText） |
| `colorStatusSuccessForegroundInverted` | `#54b054` | `#0e700e` | `#ffffff`（CanvasText） |
| `colorStatusSuccessBorderActive` | `#107c10` | `#54b054` | `#1aebff`（Highlight） |
| `colorStatusSuccessBorder1` | `#9fd89f` | `#107c10` | `#ffffff`（CanvasText） |
| `colorStatusSuccessBorder2` | `#107c10` | `#9fd89f` | `#ffffff`（CanvasText） |
| `colorStatusWarningBackground1` | `#fff9f5` | `#4a1e04` | `#000000`（Canvas） |
| `colorStatusWarningBackground2` | `#fdcfb4` | `#8a3707` | `#000000`（Canvas） |
| `colorStatusWarningBackground3` | `#f7630c` | `#f7630c` | `#ffffff`（CanvasText） |
| `colorStatusWarningForeground1` | `#bc4b09` | `#faa06b` | `#ffffff`（CanvasText） |
| `colorStatusWarningForeground2` | `#8a3707` | `#fdcfb4` | `#ffffff`（CanvasText） |
| `colorStatusWarningForeground3` | `#bc4b09` | `#f98845` | `#ffffff`（CanvasText） |
| `colorStatusWarningForegroundInverted` | `#faa06b` | `#bc4b09` | `#ffffff`（CanvasText） |
| `colorStatusWarningBorderActive` | `#f7630c` | `#faa06b` | `#1aebff`（Highlight） |
| `colorStatusWarningBorder1` | `#fdcfb4` | `#f7630c` | `#ffffff`（CanvasText） |
| `colorStatusWarningBorder2` | `#bc4b09` | `#f98845` | `#ffffff`（CanvasText） |
| `colorStatusDangerBackground1` | `#fdf3f4` | `#3b0509` | `#000000`（Canvas） |
| `colorStatusDangerBackground2` | `#eeacb2` | `#6e0811` | `#000000`（Canvas） |
| `colorStatusDangerBackground3` | `#c50f1f` | `#c50f1f` | `#ffffff`（CanvasText） |
| `colorStatusDangerForeground1` | `#b10e1c` | `#dc626d` | `#ffffff`（CanvasText） |
| `colorStatusDangerForeground2` | `#6e0811` | `#eeacb2` | `#ffffff`（CanvasText） |
| `colorStatusDangerForeground3` | `#c50f1f` | `#eeacb2` | `#ffffff`（CanvasText） |
| `colorStatusDangerForegroundInverted` | `#dc626d` | `#b10e1c` | `#ffffff`（CanvasText） |
| `colorStatusDangerBorderActive` | `#c50f1f` | `#dc626d` | `#1aebff`（Highlight） |
| `colorStatusDangerBorder1` | `#eeacb2` | `#c50f1f` | `#ffffff`（CanvasText） |
| `colorStatusDangerBorder2` | `#c50f1f` | `#dc626d` | `#ffffff`（CanvasText） |
| `colorStatusDangerBackground3Hover` | `#b10e1c` | `#b10e1c` | `#1aebff`（Highlight） |
| `colorStatusDangerBackground3Pressed` | `#960b18` | `#960b18` | `#1aebff`（Highlight） |
| `shadow2` | `0 0 2px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.14)` | `0 0 2px rgba(0,0,0,0.24), 0 1px 2px rgba(0,0,0,0.28)` | `0 0 2px rgba(0,0,0,0.24), 0 1px 2px rgba(0,0,0,0.28)` |
| `shadow4` | `0 0 2px rgba(0,0,0,0.12), 0 2px 4px rgba(0,0,0,0.14)` | `0 0 2px rgba(0,0,0,0.24), 0 2px 4px rgba(0,0,0,0.28)` | `0 0 2px rgba(0,0,0,0.24), 0 2px 4px rgba(0,0,0,0.28)` |
| `shadow8` | `0 0 2px rgba(0,0,0,0.12), 0 4px 8px rgba(0,0,0,0.14)` | `0 0 2px rgba(0,0,0,0.24), 0 4px 8px rgba(0,0,0,0.28)` | `0 0 2px rgba(0,0,0,0.24), 0 4px 8px rgba(0,0,0,0.28)` |
| `shadow16` | `0 0 2px rgba(0,0,0,0.12), 0 8px 16px rgba(0,0,0,0.14)` | `0 0 2px rgba(0,0,0,0.24), 0 8px 16px rgba(0,0,0,0.28)` | `0 0 2px rgba(0,0,0,0.24), 0 8px 16px rgba(0,0,0,0.28)` |
| `shadow28` | `0 0 8px rgba(0,0,0,0.12), 0 14px 28px rgba(0,0,0,0.14)` | `0 0 8px rgba(0,0,0,0.24), 0 14px 28px rgba(0,0,0,0.28)` | `0 0 8px rgba(0,0,0,0.24), 0 14px 28px rgba(0,0,0,0.28)` |
| `shadow64` | `0 0 8px rgba(0,0,0,0.12), 0 32px 64px rgba(0,0,0,0.14)` | `0 0 8px rgba(0,0,0,0.24), 0 32px 64px rgba(0,0,0,0.28)` | `0 0 8px rgba(0,0,0,0.24), 0 32px 64px rgba(0,0,0,0.28)` |
| `shadow2Brand` | `0 0 2px rgba(0,0,0,0.30), 0 1px 2px rgba(0,0,0,0.25)` | `0 0 2px rgba(0,0,0,0.30), 0 1px 2px rgba(0,0,0,0.25)` | `0 0 2px rgba(0,0,0,0.30), 0 1px 2px rgba(0,0,0,0.25)` |
| `shadow4Brand` | `0 0 2px rgba(0,0,0,0.30), 0 2px 4px rgba(0,0,0,0.25)` | `0 0 2px rgba(0,0,0,0.30), 0 2px 4px rgba(0,0,0,0.25)` | `0 0 2px rgba(0,0,0,0.30), 0 2px 4px rgba(0,0,0,0.25)` |
| `shadow8Brand` | `0 0 2px rgba(0,0,0,0.30), 0 4px 8px rgba(0,0,0,0.25)` | `0 0 2px rgba(0,0,0,0.30), 0 4px 8px rgba(0,0,0,0.25)` | `0 0 2px rgba(0,0,0,0.30), 0 4px 8px rgba(0,0,0,0.25)` |
| `shadow16Brand` | `0 0 2px rgba(0,0,0,0.30), 0 8px 16px rgba(0,0,0,0.25)` | `0 0 2px rgba(0,0,0,0.30), 0 8px 16px rgba(0,0,0,0.25)` | `0 0 2px rgba(0,0,0,0.30), 0 8px 16px rgba(0,0,0,0.25)` |
| `shadow28Brand` | `0 0 8px rgba(0,0,0,0.30), 0 14px 28px rgba(0,0,0,0.25)` | `0 0 8px rgba(0,0,0,0.30), 0 14px 28px rgba(0,0,0,0.25)` | `0 0 8px rgba(0,0,0,0.30), 0 14px 28px rgba(0,0,0,0.25)` |
| `shadow64Brand` | `0 0 8px rgba(0,0,0,0.30), 0 32px 64px rgba(0,0,0,0.25)` | `0 0 8px rgba(0,0,0,0.30), 0 32px 64px rgba(0,0,0,0.25)` | `0 0 8px rgba(0,0,0,0.30), 0 32px 64px rgba(0,0,0,0.25)` |

## shared の色（グローバル）

| 名前 | shade50 | shade40 | shade30 | shade20 | shade10 | primary | tint10 | tint20 | tint30 | tint40 | tint50 | tint60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `darkRed` | `#130204` | `#230308` | `#420610` | `#590815` | `#690a19` | `#750b1c` | `#861b2c` | `#962f3f` | `#ac4f5e` | `#d69ca5` | `#e9c7cd` | `#f9f0f2` |
| `burgundy` | `#1a0607` | `#310b0d` | `#5c1519` | `#7d1d21` | `#942228` | `#a4262c` | `#af393e` | `#ba4d52` | `#c86c70` | `#e4afb2` | `#f0d3d4` | `#fbf4f4` |
| `cranberry` | `#200205` | `#3b0509` | `#6e0811` | `#960b18` | `#b10e1c` | `#c50f1f` | `#cc2635` | `#d33f4c` | `#dc626d` | `#eeacb2` | `#f6d1d5` | `#fdf3f4` |
| `red` | `#210809` | `#3f1011` | `#751d1f` | `#9f282b` | `#bc2f32` | `#d13438` | `#d7494c` | `#dc5e62` | `#e37d80` | `#f1bbbc` | `#f8dadb` | `#fdf6f6` |
| `darkOrange` | `#230900` | `#411200` | `#7a2101` | `#a62d01` | `#c43501` | `#da3b01` | `#de501c` | `#e36537` | `#e9835e` | `#f4bfab` | `#f9dcd1` | `#fdf6f3` |
| `bronze` | `#1b0a01` | `#321303` | `#5e2405` | `#7f3107` | `#963a08` | `#a74109` | `#b2521e` | `#bc6535` | `#ca8057` | `#e5bba4` | `#f1d9cc` | `#fbf5f2` |
| `pumpkin` | `#200d03` | `#3d1805` | `#712d09` | `#9a3d0c` | `#b6480e` | `#ca5010` | `#d06228` | `#d77440` | `#df8e64` | `#efc4ad` | `#f7dfd2` | `#fdf7f4` |
| `orange` | `#271002` | `#4a1e04` | `#8a3707` | `#bc4b09` | `#de590b` | `#f7630c` | `#f87528` | `#f98845` | `#faa06b` | `#fdcfb4` | `#fee5d7` | `#fff9f5` |
| `peach` | `#291600` | `#4d2a00` | `#8f4e00` | `#c26a00` | `#e67e00` | `#ff8c00` | `#ff9a1f` | `#ffa83d` | `#ffba66` | `#ffddb3` | `#ffedd6` | `#fffaf5` |
| `marigold` | `#251a00` | `#463100` | `#835b00` | `#b27c00` | `#d39300` | `#eaa300` | `#edad1c` | `#efb839` | `#f2c661` | `#f9e2ae` | `#fcefd3` | `#fefbf4` |
| `yellow` | `#282400` | `#4c4400` | `#817400` | `#c0ad00` | `#e4cc00` | `#fde300` | `#fde61e` | `#fdea3d` | `#feee66` | `#fef7b2` | `#fffad6` | `#fffef5` |
| `gold` | `#1f1900` | `#3a2f00` | `#6c5700` | `#937700` | `#ae8c00` | `#c19c00` | `#c8a718` | `#d0b232` | `#dac157` | `#ecdfa5` | `#f5eece` | `#fdfbf2` |
| `brass` | `#181202` | `#2e2103` | `#553e06` | `#745408` | `#89640a` | `#986f0b` | `#a47d1e` | `#b18c34` | `#c1a256` | `#e0cea2` | `#efe4cb` | `#fbf8f2` |
| `brown` | `#170e07` | `#2b1a0e` | `#50301a` | `#6c4123` | `#804d29` | `#8e562e` | `#9c663f` | `#a97652` | `#bb8f6f` | `#ddc3b0` | `#edded3` | `#faf7f4` |
| `darkBrown` | `#0c0704` | `#170c08` | `#2b1710` | `#3a1f15` | `#452519` | `#4d291c` | `#623a2b` | `#784d3e` | `#946b5c` | `#caada3` | `#e3d2cb` | `#f8f3f2` |
| `lime` | `#121b06` | `#23330b` | `#405f14` | `#57811b` | `#689920` | `#73aa24` | `#81b437` | `#90be4c` | `#a4cc6c` | `#cfe5af` | `#e5f1d3` | `#f8fcf4` |
| `forest` | `#0c1501` | `#162702` | `#294903` | `#376304` | `#427505` | `#498205` | `#599116` | `#6ba02b` | `#85b44c` | `#bdd99b` | `#dbebc7` | `#f6faf0` |
| `seafoam` | `#002111` | `#003d20` | `#00723b` | `#009b51` | `#00b85f` | `#00cc6a` | `#19d279` | `#34d889` | `#5ae0a0` | `#a8f0cd` | `#cff7e4` | `#f3fdf8` |
| `lightGreen` | `#031a02` | `#063004` | `#0b5a08` | `#0e7a0b` | `#11910d` | `#13a10e` | `#27ac22` | `#3db838` | `#5ec75a` | `#a7e3a5` | `#cef0cd` | `#f2fbf2` |
| `green` | `#031403` | `#052505` | `#094509` | `#0c5e0c` | `#0e700e` | `#107c10` | `#218c21` | `#359b35` | `#54b054` | `#9fd89f` | `#c9eac9` | `#f1faf1` |
| `darkGreen` | `#021102` | `#032003` | `#063b06` | `#085108` | `#0a5f0a` | `#0b6a0b` | `#1a7c1a` | `#2d8e2d` | `#4da64d` | `#9ad29a` | `#c6e7c6` | `#f0f9f0` |
| `lightTeal` | `#001d1f` | `#00373a` | `#00666d` | `#008b94` | `#00a5af` | `#00b7c3` | `#18bfca` | `#32c8d1` | `#58d3db` | `#a6e9ed` | `#cef3f5` | `#f2fcfd` |
| `teal` | `#001516` | `#012728` | `#02494c` | `#026467` | `#037679` | `#038387` | `#159195` | `#2aa0a4` | `#4cb4b7` | `#9bd9db` | `#c7ebec` | `#f0fafa` |
| `darkTeal` | `#001010` | `#001f1f` | `#003939` | `#004e4e` | `#005c5c` | `#006666` | `#0e7878` | `#218b8b` | `#41a3a3` | `#92d1d1` | `#c2e7e7` | `#eff9f9` |
| `cyan` | `#00181e` | `#002e38` | `#005669` | `#00748f` | `#008aa9` | `#0099bc` | `#18a4c4` | `#31afcc` | `#56bfd7` | `#a4deeb` | `#cdedf4` | `#f2fafc` |
| `steel` | `#000f12` | `#001b22` | `#00333f` | `#004555` | `#005265` | `#005b70` | `#0f6c81` | `#237d92` | `#4496a9` | `#94c8d4` | `#c3e1e8` | `#eff7f9` |
| `lightBlue` | `#091823` | `#112d42` | `#20547c` | `#2c72a8` | `#3487c7` | `#3a96dd` | `#4fa1e1` | `#65ade5` | `#83bdeb` | `#bfddf5` | `#dcedfa` | `#f6fafe` |
| `blue` | `#001322` | `#002440` | `#004377` | `#005ba1` | `#006cbf` | `#0078d4` | `#1a86d9` | `#3595de` | `#5caae5` | `#a9d3f2` | `#d0e7f8` | `#f3f9fd` |
| `royalBlue` | `#000c16` | `#00172a` | `#002c4e` | `#003b6a` | `#00467e` | `#004e8c` | `#125e9a` | `#286fa8` | `#4a89ba` | `#9abfdc` | `#c7dced` | `#f0f6fa` |
| `darkBlue` | `#000910` | `#00111f` | `#002039` | `#002b4e` | `#00335c` | `#003966` | `#0e4a78` | `#215c8b` | `#4178a3` | `#92b5d1` | `#c2d6e7` | `#eff4f9` |
| `cornflower` | `#0d1126` | `#182047` | `#2c3c85` | `#3c51b4` | `#4760d5` | `#4f6bed` | `#637cef` | `#778df1` | `#93a4f4` | `#c8d1fa` | `#e1e6fc` | `#f7f9fe` |
| `navy` | `#00061d` | `#000c36` | `#001665` | `#001e89` | `#0023a2` | `#0027b4` | `#173bbd` | `#3050c6` | `#546fd2` | `#a3b2e8` | `#ccd5f3` | `#f2f4fc` |
| `lavender` | `#120f25` | `#221d46` | `#3f3682` | `#5649b0` | `#6656d1` | `#7160e8` | `#8172eb` | `#9184ee` | `#a79cf1` | `#d2ccf8` | `#e7e4fb` | `#f9f8fe` |
| `purple` | `#0f0717` | `#1c0e2b` | `#341a51` | `#46236e` | `#532982` | `#5c2e91` | `#6b3f9e` | `#7c52ab` | `#9470bd` | `#c6b1de` | `#e0d3ed` | `#f7f4fb` |
| `darkPurple` | `#0a0411` | `#130820` | `#240f3c` | `#311552` | `#3a1861` | `#401b6c` | `#512b7e` | `#633e8f` | `#7e5ca7` | `#b9a3d3` | `#d8cce7` | `#f5f2f9` |
| `orchid` | `#16101d` | `#281e37` | `#4c3867` | `#674c8c` | `#795aa6` | `#8764b8` | `#9373c0` | `#a083c9` | `#b29ad4` | `#d7caea` | `#e9e2f4` | `#f9f8fc` |
| `grape` | `#160418` | `#29072e` | `#4c0d55` | `#671174` | `#7a1589` | `#881798` | `#952aa4` | `#a33fb1` | `#b55fc1` | `#d9a7e0` | `#eaceef` | `#faf2fb` |
| `berry` | `#1f091d` | `#3a1136` | `#6d2064` | `#932b88` | `#af33a1` | `#c239b3` | `#c94cbc` | `#d161c4` | `#da7ed0` | `#edbbe7` | `#f5daf2` | `#fdf5fc` |
| `lilac` | `#1c0b1f` | `#35153a` | `#63276d` | `#863593` | `#9f3faf` | `#b146c2` | `#ba58c9` | `#c36bd1` | `#cf87da` | `#e6bfed` | `#f2dcf5` | `#fcf6fd` |
| `pink` | `#24091b` | `#441232` | `#80215d` | `#ad2d7e` | `#cd3595` | `#e43ba6` | `#e750b0` | `#ea66ba` | `#ef85c8` | `#f7c0e3` | `#fbddf0` | `#fef6fb` |
| `hotPink` | `#240016` | `#44002a` | `#7f004e` | `#ad006a` | `#cc007e` | `#e3008c` | `#e61c99` | `#ea38a6` | `#ee5fb7` | `#f7adda` | `#fbd2eb` | `#fef4fa` |
| `magenta` | `#1f0013` | `#390024` | `#6b0043` | `#91005a` | `#ac006b` | `#bf0077` | `#c71885` | `#ce3293` | `#d957a8` | `#eca5d1` | `#f5cee6` | `#fcf2f9` |
| `plum` | `#13000c` | `#240017` | `#43002b` | `#5a003b` | `#6b0045` | `#77004d` | `#87105d` | `#98246f` | `#ad4589` | `#d696c0` | `#e9c4dc` | `#faf0f6` |
| `beige` | `#141313` | `#252323` | `#444241` | `#5d5958` | `#6e6968` | `#7a7574` | `#8a8584` | `#9a9594` | `#afabaa` | `#d7d4d4` | `#eae8e8` | `#faf9f9` |
| `mink` | `#0f0e0e` | `#1c1b1a` | `#343231` | `#474443` | `#54514f` | `#5d5a58` | `#706d6b` | `#84817e` | `#9e9b99` | `#cecccb` | `#e5e4e3` | `#f8f8f8` |
| `silver` | `#151818` | `#282d2e` | `#4a5356` | `#657174` | `#78868a` | `#859599` | `#92a1a5` | `#a0aeb1` | `#b3bfc2` | `#d8dfe0` | `#eaeeef` | `#fafbfb` |
| `platinum` | `#111314` | `#1f2426` | `#3b4447` | `#505c60` | `#5f6d71` | `#69797e` | `#79898d` | `#89989d` | `#a0adb2` | `#cdd6d8` | `#e4e9ea` | `#f8f9fa` |
| `anchor` | `#090a0b` | `#111315` | `#202427` | `#2b3135` | `#333a3f` | `#394146` | `#4d565c` | `#626c72` | `#808a90` | `#bcc3c7` | `#dbdfe1` | `#f6f7f8` |
| `charcoal` | `#090909` | `#111111` | `#202020` | `#2b2b2b` | `#333333` | `#393939` | `#515151` | `#686868` | `#888888` | `#c4c4c4` | `#dfdfdf` | `#f7f7f7` |

## グレーの段階（グローバル）

| 段階 | 値 |
|---|---|
| grey[2] | `#050505` |
| grey[4] | `#0a0a0a` |
| grey[6] | `#0f0f0f` |
| grey[8] | `#141414` |
| grey[10] | `#1a1a1a` |
| grey[12] | `#1f1f1f` |
| grey[14] | `#242424` |
| grey[16] | `#292929` |
| grey[18] | `#2e2e2e` |
| grey[20] | `#333333` |
| grey[22] | `#383838` |
| grey[24] | `#3d3d3d` |
| grey[26] | `#424242` |
| grey[28] | `#474747` |
| grey[30] | `#4d4d4d` |
| grey[32] | `#525252` |
| grey[34] | `#575757` |
| grey[36] | `#5c5c5c` |
| grey[38] | `#616161` |
| grey[40] | `#666666` |
| grey[42] | `#6b6b6b` |
| grey[44] | `#707070` |
| grey[46] | `#757575` |
| grey[48] | `#7a7a7a` |
| grey[50] | `#808080` |
| grey[52] | `#858585` |
| grey[54] | `#8a8a8a` |
| grey[56] | `#8f8f8f` |
| grey[58] | `#949494` |
| grey[60] | `#999999` |
| grey[62] | `#9e9e9e` |
| grey[64] | `#a3a3a3` |
| grey[66] | `#a8a8a8` |
| grey[68] | `#adadad` |
| grey[70] | `#b3b3b3` |
| grey[72] | `#b8b8b8` |
| grey[74] | `#bdbdbd` |
| grey[76] | `#c2c2c2` |
| grey[78] | `#c7c7c7` |
| grey[80] | `#cccccc` |
| grey[82] | `#d1d1d1` |
| grey[84] | `#d6d6d6` |
| grey[86] | `#dbdbdb` |
| grey[88] | `#e0e0e0` |
| grey[90] | `#e6e6e6` |
| grey[92] | `#ebebeb` |
| grey[94] | `#f0f0f0` |
| grey[96] | `#f5f5f5` |
| grey[98] | `#fafafa` |
| grey[99] | `#fcfcfc` |
