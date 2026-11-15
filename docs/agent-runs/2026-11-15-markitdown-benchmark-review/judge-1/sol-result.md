```json
{
  "handbook_docx": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 4,
      "noise": 5,
      "location": 1,
      "usability": 5,
      "fatal": [],
      "comment": "judge/handbook_docx/A.md:1–61 は本文・表・質問を正しい順に保持している。33–35行の空の表見出しは余分で、ページ位置は残っていない。"
    }
  },
  "handbook_pdf": {
    "A": {
      "coverage": 5,
      "order": 4,
      "structure": 3,
      "noise": 3,
      "location": 4,
      "usability": 4,
      "fatal": [],
      "comment": "judge/handbook_pdf/A.md:23–33 は数値と対応する項目を保持するが、表の後半を別々の表見出しにし、「以内」の末尾を分離している。1・28・37行にヘッダー、26・35・52行にページ番号が残る。"
    },
    "B": {
      "coverage": 5,
      "order": 3,
      "structure": 2,
      "noise": 3,
      "location": 4,
      "usability": 3,
      "fatal": [],
      "comment": "judge/handbook_pdf/B.md:42–64 は金額・対象・備考・項目が散らばり、77–87行では「以内」の末尾がモニターの後へ移る。本文と数値は残り、66・89・121行からページを識別できる。"
    },
    "C": {
      "coverage": 5,
      "order": 3,
      "structure": 2,
      "noise": 3,
      "location": 4,
      "usability": 3,
      "fatal": [],
      "comment": "judge/handbook_pdf/C.md:26–43 の表は列ごとの列挙になり、項目と条件を対応させる作業が必要になる。11・19・50・52行では箇条書き、手順、段落も同じ行へ連結されている。"
    },
    "D": {
      "coverage": 5,
      "order": 5,
      "structure": 4,
      "noise": 3,
      "location": 5,
      "usability": 4,
      "fatal": [],
      "comment": "judge/handbook_pdf/D.md:26–36 は改ページを挟んでも表の行と金額の対応を保持し、1・30・38行にページ見出しがある。ヘッダーと元のページ番号は残るが、本文は順に読める。"
    }
  },
  "handbook-2col_pdf": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 3,
      "noise": 3,
      "location": 5,
      "usability": 4,
      "fatal": [],
      "comment": "judge/handbook-2col_pdf/A.md:5–67 は左段から右段への論理順を保持し、1・69行でページも分かる。40–60行の表はセル内の改行が多いものの、項目・金額・対象・備考の対応を追える。"
    },
    "B": {
      "coverage": 5,
      "order": 2,
      "structure": 2,
      "noise": 3,
      "location": 4,
      "usability": 2,
      "fatal": [],
      "comment": "judge/handbook-2col_pdf/B.md:8–22 は勤務手順と費用の説明を先に置き、その後で対象・申請・勤務時間へ戻る。24–38行の表も列ごとの列挙となり、節とセルの対応を復元する必要がある。"
    },
    "C": {
      "coverage": 4,
      "order": 1,
      "structure": 1,
      "noise": 3,
      "location": 4,
      "usability": 1,
      "fatal": [
        "judge/handbook-2col_pdf/C.md:5–35 は左右の段を同じ表へ取り込み、題名と勤務手順、申請条件と補助金のセルを同じ行に配置している。正解では独立した本文・手順・4列表であり、出力の5列表は誤った対応を作っている（scripts/content.py:9–50）。",
        "judge/handbook-2col_pdf/C.md:42–53 は情報の安全に関する文と勤務連絡に関する文を途中で交互に挿入し、文の連続性を壊している（scripts/content.py:30–31、56–58）。"
      ],
      "comment": "judge/handbook-2col_pdf/C.md:2–53 は文字や数値が概ね残っていても、段の混線と誤った表によって意味の対応が崩れている。60–74行の質問部分は順に読める。"
    },
    "D": {
      "coverage": 4,
      "order": 1,
      "structure": 2,
      "noise": 3,
      "location": 4,
      "usability": 1,
      "fatal": [
        "judge/handbook-2col_pdf/D.md:13–36 は「対象は、正社員と契約社員のうち、入社」とその続きの間に勤務手順・費用の説明を挿入し、さらに領収書の文と派遣社員の規程の文を交互に配置している（scripts/content.py:17、34–36、42–43）。",
        "judge/handbook-2col_pdf/D.md:62–95 は電気代の条件「週2日以上」と備考「実費は問わない」の途中に別段の本文を挿入している。87–130行では「離席」と入れる文の末尾「く。」も情報の安全の節へ離れており、条件と文の対応が壊れている（scripts/content.py:31、48）。"
      ],
      "comment": "judge/handbook-2col_pdf/D.md:13–134 は左右の段を文の途中で混ぜており、本文と表の復元が必要になる。147–174行の質問部分と136・176行のページ番号は保持されている。"
    }
  },
  "slides_pptx": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 4,
      "noise": 5,
      "location": 5,
      "usability": 5,
      "fatal": [],
      "comment": "judge/slides_pptx/A.md:1–31 は5枚のスライド、補助表、左右の本文を順に保持し、11–12行ではノートを明示的に区別している。7–9・30–31行の箇条書き記号は失われるが、項目ごとの改行は残る。"
    }
  },
  "slides_pdf": {
    "A": {
      "coverage": 5,
      "order": 2,
      "structure": 2,
      "noise": 5,
      "location": 2,
      "usability": 3,
      "fatal": [],
      "comment": "judge/slides_pdf/A.md:18–56 は表の項目と金額を列ごとに出した後、対象と備考を混在させており、行の対応を復元する必要がある。59–72行の左右の本文と問い合わせ先は読めるが、ページ番号はない。"
    },
    "B": {
      "coverage": 5,
      "order": 3,
      "structure": 3,
      "noise": 5,
      "location": 2,
      "usability": 3,
      "fatal": [],
      "comment": "judge/slides_pdf/B.md:10–18 は表を列ごとの列挙にし、見出し「費用の補助」も項目列の後へ移している。23–29行の本文は分離されているが、ページ番号と明示的なページ境界はない。"
    },
    "C": {
      "coverage": 5,
      "order": 5,
      "structure": 4,
      "noise": 5,
      "location": 5,
      "usability": 5,
      "fatal": [],
      "comment": "judge/slides_pdf/C.md:1–36 は5ページを明示し、17–21行で表の項目・金額・条件を行単位に保持している。26–30行の本文には語中の改行があるが、左右の文は混ざっていない。"
    },
    "D": {
      "coverage": 4,
      "order": 2,
      "structure": 3,
      "noise": 5,
      "location": 2,
      "usability": 2,
      "fatal": [
        "judge/slides_pdf/D.md:20–22 は始業時の文と終業時の文を横方向に連結し、「勤怠チャン」「ネルへ」と「その日の作」「業を」の間へ他方の文を挿入している。独立した2つの手順として読むために再構成が必要になる（scripts/content.py:82–83）。"
      ],
      "comment": "judge/slides_pdf/D.md:12–17 の表は正確だが、20–22行の手順の混線が利用上の大きな問題になる。2–3行では年度も逆順に分離され、ページ番号は残っていない。"
    }
  },
  "expenses_xlsx": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": 5,
      "usability": 5,
      "fatal": [],
      "comment": "judge/expenses_xlsx/A.md:1–14 はシート名、表の行列、日付を保持している。4–7行の合計24500・4500・21500・4500は正解値と一致する（scripts/content.py:87–101）。"
    }
  },
  "expenses_xls": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": 5,
      "usability": 5,
      "fatal": [],
      "comment": "judge/expenses_xls/A.md:1–14 はシート名、表の行列、日付を保持している。4–7行の合計24500・4500・21500・4500は正解値と一致する（scripts/content.py:87–101）。"
    }
  },
  "expenses_pdf": {
    "A": {
      "coverage": 5,
      "order": 2,
      "structure": 2,
      "noise": 5,
      "location": 2,
      "usability": 2,
      "fatal": [],
      "comment": "judge/expenses_pdf/A.md:9–28 は見出しの順と数値群の順が異なり、通信費の前に電気代・机と椅子の値が出るため、列の対応は出力だけでは確定しにくい。33–41行の日付表示は原本の制約として減点していない。"
    },
    "B": {
      "coverage": 5,
      "order": 5,
      "structure": 4,
      "noise": 5,
      "location": 5,
      "usability": 5,
      "fatal": [],
      "comment": "judge/expenses_pdf/B.md:3–7 は氏名と各費目・合計の対応を正しく保持し、1・9行にページ番号がある。11–18行の日別表は改行で分割されるが曜日と人数の対応は読め、日付の表示制約は減点していない。"
    },
    "C": {
      "coverage": 2,
      "order": 2,
      "structure": 1,
      "noise": 5,
      "location": 2,
      "usability": 1,
      "fatal": [
        "judge/expenses_pdf/C.md:1–6 は全員の電気代列を空欄にし、机と椅子列へ電気代を混入している。例えば3行目の青木は机と椅子が「1500 20000」、4行目の石田は机と椅子が「1500」、合計が「0 4500」となり、正解の列対応を壊している（scripts/content.py:88–95）。"
      ],
      "comment": "judge/expenses_pdf/C.md:1–6 は数値自体が残っていても、誤った列に入れた表が値の取り違えを誘う。8–12行の日別表の対応は保たれており、日付の表示制約は減点していない。"
    },
    "D": {
      "coverage": 5,
      "order": 3,
      "structure": 2,
      "noise": 5,
      "location": 2,
      "usability": 3,
      "fatal": [],
      "comment": "judge/expenses_pdf/D.md:5–37 は氏名群と数値群を分離するが、数値は人ごとの費目順を概ね維持している。40–50行でも曜日と人数が別々の列挙になり、行の対応を復元する必要がある。"
    }
  },
  "article_html": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 2,
      "location": null,
      "usability": 4,
      "fatal": [],
      "comment": "judge/article_html/A.md:3–50 は本文・リスト・表を正確に保持している。1・52–56行にはナビゲーション、広告、Cookie設定、フッターが混入している。"
    },
    "B": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": null,
      "usability": 5,
      "fatal": [],
      "comment": "judge/article_html/B.md:2–49 は見出し・段落・リスト・表と本文中のURLを保持している。本文外のナビゲーション、広告、フッターは混入していない。"
    }
  },
  "staff-utf8_csv": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": null,
      "usability": 5,
      "fatal": [],
      "comment": "judge/staff-utf8_csv/A.md:1–6 は全員の社員番号・氏名・部署・在宅日数を正しい列に保持し、文字化けもない（scripts/content.py:106–110）。"
    },
    "B": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": null,
      "usability": 5,
      "fatal": [],
      "comment": "judge/staff-utf8_csv/B.md:1–5 はCSVの行と区切りを保持し、全項目が正解と一致している。生テキストを読むLLMには列の対応が明瞭である。"
    }
  },
  "staff-cp932_csv": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": null,
      "usability": 5,
      "fatal": [],
      "comment": "judge/staff-cp932_csv/A.md:1–6 は日本語の氏名・部署を文字化けなく保持し、社員番号と在宅日数の対応も正しい（scripts/content.py:106–110）。"
    },
    "B": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": null,
      "usability": 5,
      "fatal": [],
      "comment": "judge/staff-cp932_csv/B.md:1–5 はCSVの行と区切りを保持し、CP932由来の日本語も正しく読める。全項目が正解と一致している。"
    }
  },
  "policy_json": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": null,
      "usability": 5,
      "fatal": [],
      "comment": "judge/policy_json/A.md:1–24 は階層・配列・キーと値の対応を保持し、補助金額と内線も正解に一致する（scripts/content.py:112–121）。"
    },
    "B": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": null,
      "usability": 5,
      "fatal": [],
      "comment": "judge/policy_json/B.md:1–24 は階層・配列・キーと値の対応を保持し、Aと内容が一致する（scripts/content.py:112–121）。"
    }
  },
  "policy_xml": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": null,
      "usability": 5,
      "fatal": [],
      "comment": "judge/policy_xml/A.md:1–8 は本文に加えて属性内の名称・版・金額・内線も保持し、要素の対応と順序が正しい（scripts/content.py:123–130）。"
    },
    "B": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 5,
      "location": null,
      "usability": 5,
      "fatal": [],
      "comment": "judge/policy_xml/B.md:1–8 は本文と属性値を欠落なく保持し、Aと内容が一致する（scripts/content.py:123–130）。"
    }
  },
  "story_epub": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 5,
      "noise": 4,
      "location": 5,
      "usability": 5,
      "fatal": [],
      "comment": "judge/story_epub/A.md:6–16 は2章の見出しと全段落を正しい順に保持している（scripts/content.py:133–140）。1–4行の書誌情報は明示的に区別されるが、言語・識別子は本文外の付加情報である。"
    }
  },
  "bundle_zip": {
    "A": {
      "coverage": 5,
      "order": 5,
      "structure": 4,
      "noise": 4,
      "location": 5,
      "usability": 5,
      "fatal": [],
      "comment": "judge/bundle_zip/A.md:3・67・76行のファイル名で内容の境界を識別でき、文書・CSV・JSONが保持されている。37–39行には空の表見出し、1行目には本文外のローカルパスが付く。"
    }
  }
}
```

## 総評

パスはすべて `docs/research/markitdown-benchmark-2026-11-15/` からの相対パス、行番号は1始まり。LLMがファイルの生テキストを読む前提で評価した。`coverage` は文字・数値の有無に加え、項目と値の取り違えも含む。`location` はDOCX・PDFのページ、PPTXのスライド、Excelのシートを評価し、EPUBは章、ZIPは内部ファイルを位置の単位と仮定した。

- **DOCX**：Aは本文・手順・表・質問を保持している。空の表見出しは軽微な問題だが、ページ情報は失われる（`judge/handbook_docx/A.md:1–61`）。
- **1段組みの文書PDF**：Dは表の行対応とページ位置が明瞭。Aは表の後半の構造、B・Cはセルの列挙順に問題がある（各出力の表部分：A:23–33、B:42–87、C:26–43、D:26–36）。
- **2段組みPDF**：Aは論理順を保持する。Bは段落群の順序が入れ替わり、C・Dは文の途中で左右の段が混ざるため、要約の入力として大きな問題がある（`judge/handbook-2col_pdf/` のA:5–67、B:8–38、C:2–53、D:13–134）。
- **PPTX**：Aはスライド番号、表、ノートを区別して保持する。箇条書き記号の欠落による意味への影響は小さい（`judge/slides_pptx/A.md:1–31`）。
- **スライドPDF**：Cが表・左右の本文・ページ位置を最も明瞭に保持する。Dは正確な表があっても手順の文が混線し、A・Bは表の対応を復元する必要がある（`judge/slides_pdf/` のC:14–36、D:12–22、A:18–56、B:10–18）。
- **XLSX・XLS**：両Aともシート名、日付、数式の計算済み値を保持する。合計は正解の24500・4500・21500・4500と一致する（両出力:1–14、`scripts/content.py:95`）。
- **表計算のPDF**：Bは費目と値の対応を保持する。Cは電気代を別列へ入れた誤表であり、構造があること自体は品質の保証にならない（`judge/expenses_pdf/B.md:3–18`、`C.md:1–12`）。日付の「########」は依頼で示された原本の表示制約として減点していない。
- **HTML**：両出力とも本文の構造は良好だが、Aには広告などが残り、Bは本文に絞られている（`judge/article_html/A.md:1–56`、`B.md:2–49`）。
- **CSV・JSON・XML**：今回の全出力で日本語と数値の対応は正しい。単純なCSVや元のJSON・XMLも、生テキストを読む用途では十分使える（各CSV出力:1–6または1–5、各JSON出力:1–24、各XML出力:1–8）。
- **EPUB・ZIP**：EPUBは章、ZIPは内部ファイル名が出典位置の手がかりになる。付加されたメタデータは本文と区別でき、内容の利用を妨げない（`judge/story_epub/A.md:1–16`、`judge/bundle_zip/A.md:1–101`）。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
