"""ベンチマークの試料の中身と正解。

試料はすべてこのファイルの文から作る。架空の社内文書で、実在の組織や人物とは関係がない。
正解（truth）は、抽出の結果に出てくるべき文字列を、出てくるべき順に並べたものである。
"""

from __future__ import annotations

TITLE = "在宅勤務の手引き（架空の株式会社ミナモ）"
HEADER = "社外秘・試料"

SECTIONS = [
    {
        "heading": "1. 目的と対象",
        "paragraphs": [
            "この手引きは、株式会社ミナモの従業員が在宅で働くときの決まりと手順をまとめたものである。",
            "対象は、正社員と契約社員のうち、入社から３か月を過ぎた者とする。派遣社員は派遣元の規程に従う。",
            "在宅勤務は週に最大3日までとし、部署の業務に支障がない範囲で認める。",
        ],
        "bullets": [
            "申請は前週の金曜日までに出す",
            "緊急の在宅勤務は当日の9時30分までに上長へ連絡する",
            "顧客の個人情報を扱う業務は在宅では行わない",
        ],
    },
    {
        "heading": "2. 勤務時間と連絡",
        "paragraphs": [
            "勤務時間は原則として9時から18時までとし、休憩は12時から13時までの1時間とする。",
            "始業と終業の連絡は Microsoft Teams の「勤怠」チャンネルに書き込む。",
            "連絡がつかない時間が30分を超える場合は、事前に予定表へ「離席」と入れておく。",
        ],
        "numbered": [
            "始業時に勤怠チャンネルへ「開始」と書く",
            "業務の予定を予定表に入れる",
            "終業時にその日の作業を3行で報告する",
        ],
    },
    {
        "heading": "3. 費用の補助",
        "paragraphs": [
            "在宅勤務に伴う費用は、次の表の金額を上限として補助する。",
            "領収書は翌月の5日までに経理部へ提出する。電子データでの提出も受け付ける。",
        ],
        "table": [
            ["項目", "月額の上限", "対象", "備考"],
            ["通信費", "3,000円", "全員", "定額で支給"],
            ["電気代", "1,500円", "週2日以上", "実費は問わない"],
            ["机と椅子", "20,000円", "初回のみ", "購入から3か月以内"],
            ["モニター", "15,000円", "希望者", "27インチまで"],
        ],
    },
    {
        "heading": "4. 情報の安全",
        "paragraphs": [
            "業務の資料は会社が貸与したパソコンだけで扱い、私物の端末に保存しない。",
            "公共の Wi-Fi を使う場合は、必ず VPN に接続してから作業を始める。",
            "紛失や盗難に気づいたときは、ただちに情報システム部（内線 4021）へ届け出る。",
            "詳しい規程は社内ポータルの https://portal.example.jp/security に掲載している。",
        ],
    },
]

# 長い文書（PDF で 3 ページ以上になるもの）にするための追加の節。
EXTRA_SECTION = {
    "heading": "5. よくある質問",
    "paragraphs": [
        "問1：在宅勤務の日に出社してもよいか。答え：よい。ただし予定表を更新する。",
        "問2：家族の看護のために在宅勤務を使えるか。答え：使える。看護休暇との併用も認める。",
        "問3：海外から在宅勤務をしてもよいか。答え：認めない。税と労務の扱いが異なるためである。",
        "問4：通信費の補助は日割りになるか。答え：ならない。月の途中で始めても全額を支給する。",
        "問5：モニターの補助は2台目にも使えるか。答え：使えない。1人1台までとする。",
    ],
}

SLIDES = [
    {"title": "在宅勤務の手引き", "subtitle": "2026年度版・人事部"},
    {"title": "対象と申請", "bullets": ["入社から３か月を過ぎた正社員と契約社員",
                                   "申請は前週の金曜日まで", "週に最大3日まで"],
     "notes": "派遣社員は派遣元の規程に従うことを口頭で補足する。"},
    {"title": "費用の補助", "table": SECTIONS[2]["table"]},
    {"title": "連絡の流れ", "left": "始業時に勤怠チャンネルへ「開始」と書く",
     "right": "終業時にその日の作業を3行で報告する"},
    {"title": "問い合わせ先", "bullets": ["人事部：内線 3010", "情報システム部：内線 4021"]},
]

SHEET_EXPENSES = [
    ["氏名", "部署", "通信費", "電気代", "机と椅子", "合計"],
    ["青木 遥", "営業部", 3000, 1500, 20000, None],
    ["石田 湊", "開発部", 3000, 1500, 0, None],
    ["上野 朱里", "人事部", 3000, 0, 18500, None],
    ["遠藤 蓮", "開発部", 3000, 1500, 0, None],
]
# 合計の列は Excel の式（=SUM）で書き、Excel で保存して値を持たせる。
SHEET_EXPENSES_TOTALS = [24500, 4500, 21500, 4500]

SHEET_DAYS = [
    ["日付", "曜日", "在宅勤務の人数"],
    ["2026-04-06", "月", 12],
    ["2026-04-07", "火", 15],
    ["2026-04-08", "水", 9],
]

HTML_NOISE = ["ホームに戻る", "ログイン", "Cookie の設定", "© 2026 ミナモ"]

CSV_ROWS = [["社員番号", "氏名", "部署", "在宅日数"],
            ["A001", "青木 遥", "営業部", "3"],
            ["A002", "石田 湊", "開発部", "2"],
            ["A003", "上野 朱里", "人事部", "1"],
            ["A004", "遠藤 蓮", "開発部", "3"]]

JSON_DATA = {
    "policy": "在宅勤務の手引き",
    "version": "2026.1",
    "limits": {"days_per_week": 3, "apply_deadline": "前週の金曜日"},
    "allowances": [
        {"item": "通信費", "monthly_max": 3000},
        {"item": "電気代", "monthly_max": 1500},
    ],
    "contacts": [{"dept": "情報システム部", "ext": "4021"}],
}

XML_TEXT = """<?xml version="1.0" encoding="UTF-8"?>
<policy name="在宅勤務の手引き" version="2026.1">
  <rule id="r1">在宅勤務は週に最大3日までとする。</rule>
  <rule id="r2">申請は前週の金曜日までに出す。</rule>
  <allowance item="通信費" max="3000"/>
  <allowance item="電気代" max="1500"/>
  <contact dept="情報システム部" ext="4021"/>
</policy>
"""

EPUB_CHAPTERS = [
    {"title": "第1章 はじまり", "paragraphs": [
        "春の朝、湊は初めて在宅で働く日を迎えた。窓の外では桜が散り始めていた。",
        "机の上には貸与されたパソコンと、届いたばかりのモニターが並んでいる。"]},
    {"title": "第2章 午後の会議", "paragraphs": [
        "午後二時、Teams の会議に十二人が集まった。画面越しでも、遥の声はよく通った。",
        "会議の最後に、湊はその日の作業を三行で報告した。"]},
]


def doc_truth(long: bool = False) -> list[str]:
    """文書（DOCX と、それを書き出した PDF）の正解。表のセルは行ごとに並べる。"""
    items = [TITLE]
    sections = SECTIONS + ([EXTRA_SECTION] if long else [])
    for section in sections:
        items.append(section["heading"])
        items += section["paragraphs"]
        items += section.get("bullets", [])
        items += section.get("numbered", [])
        for row in section.get("table", []):
            items += row
    return items


def doc_rows() -> list[list[str]]:
    return SECTIONS[2]["table"]


def slide_truth(with_notes: bool) -> list[str]:
    items = []
    for slide in SLIDES:
        items.append(slide["title"])
        if "subtitle" in slide:
            items.append(slide["subtitle"])
        items += slide.get("bullets", [])
        for row in slide.get("table", []):
            items += row
        if "left" in slide:
            items += [slide["left"], slide["right"]]
        if with_notes and "notes" in slide:
            items.append(slide["notes"])
    return items


def sheet_truth() -> list[str]:
    items = []
    for i, row in enumerate(SHEET_EXPENSES):
        cells = [str(c) for c in row if c is not None]
        if i:
            cells.append(str(SHEET_EXPENSES_TOTALS[i - 1]))
        items += cells
    for row in SHEET_DAYS:
        items += [str(c) for c in row]
    return items


def sheet_rows() -> list[list[str]]:
    rows = [[str(c) for c in SHEET_EXPENSES[0]]]
    for i, row in enumerate(SHEET_EXPENSES[1:]):
        rows.append([str(c) for c in row[:-1]] + [str(SHEET_EXPENSES_TOTALS[i])])
    return rows + [[str(c) for c in row] for row in SHEET_DAYS]
