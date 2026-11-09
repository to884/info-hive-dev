"""描画を目視して転記した短い抜粋を、既存の実資料 OCR 出力と照合する。"""
import json
import os
import sys
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import write_json

old=(Path(os.environ['LOCALAPPDATA'])/'info-hive/rag-poc/2026-11-04').resolve()
normalize=lambda s:''.join(unicodedata.normalize('NFKC',s).split())
references={
    'scan-0-12':['80年代のニーズ','ハードウェア仕様','ソフトウェア仕様'],
    'vertical-5-24':['ウェーブアイが安心できるセットプランをご提案','そして確かな商品をお届けいたします。','お支払は','お得なクレジット','全国配送!!','お見積りサービス','下取り・買取もOK','各種ソフトインストール(有料)','登録方法は','お電話で0462-60-0999'],
}
results=[]
for name,lines in references.items():
    recognized=normalize((old/'real-ocr-output'/f'{name}.txt').read_text(encoding='utf-8-sig'))
    rows=[{'expected':line,'present':normalize(line) in recognized} for line in lines]
    results.append({'image':name,'lines':rows,'exact_lines_present':sum(row['present'] for row in rows),'lines_checked':len(lines),'expected_characters':sum(len(normalize(line)) for line in lines)})
private=POC_DATA/'ocr-remaining-20261104'
write_json(private/'real-excerpt-details.json',results)
write_json(ROOT/'docs/research/rag-validation-remaining-2026-11-04/real-ocr-excerpts.json',{'method':'同じ OCR 出力から正解文字列を作らず、描画画像を AI が目視して短い抜粋を転記し、既存の固定版 NDLOCR-Lite 出力と完全一致で照合した。','human_transcription':False,'full_page_cer_measured':False,'results':[{k:v for k,v in row.items() if k!='lines'} for row in results],'limitations':'2ページの短い抜粋のみ。OCR の全文精度や表構造の復元精度を保証しない。縦書きと分類された広告ページは目視では横書き中心だった。'})
