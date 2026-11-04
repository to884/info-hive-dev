"""表・数式・低解像度・縦書きの既知の文字列で OCR の限界を確認する。"""
import argparse
import json
import os
import sys
import time
import unicodedata
from contextlib import closing
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config,write_json
from rag_pdf import inspect_page,ocr_page

WORK=ROOT/'.rag-poc-data/ocr-remaining-20261104'
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'
FONT=r'C:\Windows\Fonts\meiryo.ttc'
CASES=[
    ('two_columns',['検索の検証','原本は変更しません。','進捗を保存します。','再開の検証','次回の起動で続行します。','出典のページを表示します。']),
    ('table',['項目','設定値','処理方法','検索件数','8件','再ランキング','保存先','ローカル','原本の参照']),
    ('formula',['数式の検証','E = mc²','x² + y² = 25','√16 = 4','Σ ai = 10']),
    ('low_resolution',['低解像度の資料','原本は変更しません。','進捗を保存して再開します。']),
    ('vertical',['縦書きの検証','原本は変更しません。','進捗を保存して再開します。']),
    ('native_vertical',['縦書きの検証','原本は変更しません。','進捗を保存して再開します。']),
]


def create():
    from PIL import Image,ImageDraw,ImageFont
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    WORK.mkdir(parents=True,exist_ok=True)
    pdfmetrics.registerFont(TTFont('MeiryoOCR',FONT))
    pdf=canvas.Canvas(str(WORK/'complex-cases.pdf'),pagesize=(595,842))
    for kind,lines in CASES:
        if kind=='native_vertical':
            pdf.setFont('MeiryoOCR',22)
            for column,line in enumerate(lines):
                for number,char in enumerate(line):
                    pdf.drawString(530-column*65,780-number*28,char)
        else:
            image=Image.new('RGB',(1200,1698),'white')
            draw=ImageDraw.Draw(image)
            font=ImageFont.truetype(FONT,48)
            if kind=='two_columns':
                font=ImageFont.truetype(FONT,36)
                for i,line in enumerate(lines):
                    draw.text((50+(i//3)*600,100+(i%3)*150),line,fill='black',font=font)
            elif kind=='table':
                for r in range(4): draw.line((40,100+r*160,1160,100+r*160),fill='black',width=3)
                for c in range(4): draw.line((40+c*373,100,40+c*373,580),fill='black',width=3)
                for i,line in enumerate(lines): draw.text((65+(i%3)*373,140+(i//3)*160),line,fill='black',font=font)
            elif kind=='vertical':
                for column,line in enumerate(lines):
                    for number,char in enumerate(line): draw.text((1040-column*150,80+number*60),char,fill='black',font=font)
            else:
                for i,line in enumerate(lines): draw.text((70,100+i*150),line,fill='black',font=font)
            if kind=='low_resolution': image=image.resize((250,354))
            image.save(WORK/f'{kind}.png')
            pdf.drawImage(ImageReader(image),0,0,width=595,height=842)
        pdf.showPage()
    pdf.save()
    import pypdfium2 as pdfium
    with pdfium.PdfDocument(WORK/'complex-cases.pdf') as doc:
        for i in range(len(doc)):
            with closing(doc[i]) as page:
                bitmap=page.render(scale=1)
                bitmap.to_pil().save(WORK/f'preview-{i+1}.png')
                bitmap.close()


def distance(a,b):
    previous=list(range(len(b)+1))
    for i,char in enumerate(a,1):
        current=[i]
        for j,other in enumerate(b,1): current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(char!=other)))
        previous=current
    return previous[-1]


def run(config_file,direct=False):
    import pypdfium2 as pdfium
    baseline=Path(config_file)
    values=json.loads(baseline.read_text(encoding='utf-8'))
    values.update(data_dir=str(WORK/'data'),ocr_dpi=200,uv_cache_dir=str(ROOT/'.rag-poc-data/uv-cache-ocr'))
    cfg=Config(values)
    results=[]
    if direct:
        import subprocess
        from unittest.mock import patch
        original_run=subprocess.run
        def local(command,**options):
            if command[:2]==['uv','run']:
                script=command.index('--script')
                command=[sys.executable,str(Path(__file__).with_name('ocr_local_runtime.py'))]+command[script+2:]
            return original_run(command,**options)
        guard=patch('rag_pdf.subprocess.run',local)
        guard.start()
    normalized=lambda s:''.join(unicodedata.normalize('NFKC',s).split())
    with pdfium.PdfDocument(WORK/'complex-cases.pdf') as doc:
        for i,(kind,lines) in enumerate(CASES):
            with closing(doc[i]) as page:
                native,quality=inspect_page(page)
                started=time.perf_counter()
                try:
                    text=ocr_page(page,cfg,WORK)
                    gold=normalized(''.join(lines))
                    actual=normalized(text)
                    row={'case':kind,'quality':quality,'seconds':time.perf_counter()-started,'normalized_cer':distance(gold,actual)/len(gold),'expected_characters':len(gold),'all_lines_present':all(normalized(line) in actual for line in lines),'recognized_text':text,'expected_text':'\n'.join(lines)}
                except Exception as e:
                    row={'case':kind,'quality':quality,'error':str(e),'seconds':time.perf_counter()-started}
                results.append(row)
                write_json(OUT/'ocr-complex-results.json',{'cases':results,'runtime':'prepared_local_libraries' if direct else 'product_uv','config_file':str(baseline),'gold':'自作した文字列。人手の実資料全文転記ではない。','normalization':'NFKC と空白除去。表・段組みの読み順の違いも CER に含む。'})
                print(json.dumps({k:v for k,v in row.items() if k not in {'recognized_text','expected_text'}},ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('stage',choices=['create','run']); p.add_argument('--config'); p.add_argument('--direct-runtime',action='store_true'); a=p.parse_args()
    if a.stage=='create': create()
    elif a.config: run(a.config,a.direct_runtime)
    else: p.error('OCR 実行時は --config が必要です。')
