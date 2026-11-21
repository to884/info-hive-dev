"""同じ図表を載せた講演PDFでも点が画像に焼き込まれているかを確かめる。"""

from contextlib import closing
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
spec=spec_from_file_location("point_drawing_in_presenter_version",HERE/"run.py")
source=module_from_spec(spec)
spec.loader.exec_module(source)
URL="https://www.glocom.ac.jp/wp-content/uploads/2025/09/GCQ20250919whitepaper_01_kato.pdf"
PAGE=15
HASH="2cf17b1ee74bac08e73b536b319475e56c62241c5424ca15d90b163523e138ff"
POINT=(880,938,885,944)
SCALE=150/72

def main(path):
    trace=source.launch.source.verify_vertical.trace
    data=path.read_bytes()
    if trace.sha(data)!=HASH:
        raise ValueError("確認した講演資料の版が変化")
    with closing(trace.pypdfium2.PdfDocument(data)) as doc, closing(doc[PAGE-1]) as page:
        height=page.get_height()
        with closing(page.render(scale=SCALE)) as pix:
            fixed=np.asarray(pix.to_pil().convert("RGB"))
    asset={"sha":{"150_origin":[0,height],"150_matrix":[[SCALE,0],[0,-SCALE]]}}
    evidence=source.diagnostic(trace,data,PAGE,fixed,POINT,asset)
    record={"scope":"development-only","url":URL,"pdf_sha256":HASH,"physical_page":PAGE,
            "printed_slide":14,"point_at_150_dpi":POINT,**evidence}
    source.core.save_once(HERE/"presenter-slide.json", source.core.encoded(record))
    print(record,flush=True)

if __name__=="__main__":
    main(Path(sys.argv[1]))
