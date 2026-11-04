"""自作の日本語 PDF。原資料の複製を使わない制御試験用。"""
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

folder = Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04/fixtures"
folder.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
pdf = canvas.Canvas(str(folder / "protocol.pdf"), pagesize=(595, 842))
gold = []
for page in range(1, 9):
    text = f"日本語資料の検索検証。第{page}章では、原本を変更せずに参照します。"
    pdf.setFont("HeiseiMin-W3", 18)
    pdf.drawString(45, 780, f"RAG の検証資料：第 {page} 章")
    pdf.setFont("HeiseiMin-W3", 12)
    for line, sentence in enumerate([text, "PDF の本文はローカルで抽出します。", "ジョブの進捗は、ページごとに保存します。", "検索結果には資料名とページ番号を付けます。"]):
        pdf.drawString(45, 720 - 28 * line, sentence)
    gold.append({"page": page, "kind": "text", "text": text})
    pdf.showPage()
font = ImageFont.truetype(r"C:\Windows\Fonts\meiryo.ttc", 44)
for vertical in (False, True):
    image = Image.new("RGB", (1000, 1400), "white")
    draw = ImageDraw.Draw(image)
    text = "原本は複製しません。進捗を保存して再開します。"
    if vertical:
        for index, character in enumerate(text):
            draw.text((820 - (index // 18) * 80, 80 + (index % 18) * 60), character, font=font, fill="black")
    else:
        draw.text((60, 100), "日本語の検索検証", font=font, fill="black")
        draw.text((60, 220), "原本は複製しません。", font=font, fill="black")
        draw.text((60, 340), "進捗を保存して再開します。", font=font, fill="black")
    pdf.drawImage(ImageReader(image), 0, 0, width=595, height=842)
    gold.append({"page": len(gold) + 1, "kind": "vertical_scan" if vertical else "scan", "text": text})
    pdf.showPage()
pdf.save()
(folder / "gold.json").write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
print(folder / "protocol.pdf")
