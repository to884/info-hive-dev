```json
{
  "judge_digest": "8d95a04e33da7b7cf9f30612044828327e0a4862c0d1ca67bdf9d08116cf31c3",
  "bert-p1": {
    "A": {
      "coverage": 5, "order": 4, "table": null, "legibility": 4, "usability": 5,
      "fatal": [],
      "comment": "bert-p1/A.txt:48–137は、画像の要旨、左段の導入、右段の順に本文を保持している。8–44では欄外の書誌情報が逆順の1文字改行になるが、本文の解釈への影響は小さい。"
    },
    "B": {
      "coverage": 5, "order": 5, "table": null, "legibility": 4, "usability": 5,
      "fatal": [],
      "comment": "bert-p1/B.txt:12–70は本文と主要な数値を正しい順で保持している。19のtaskspecificや60のleft-torightなど、行末ハイフンの除去に伴う軽微な単語の接合がある。"
    },
    "C": {
      "coverage": 5, "order": 5, "table": null, "legibility": 3, "usability": 4,
      "fatal": [
        "bert-p1/C.txt:7のrepresentaとtionの間、9のRadとfordの間などにU+FFFEが入り、原画像の行末ハイフンに相当する箇所で単語が繰り返し崩れている。"
      ],
      "comment": "bert-p1/C.txt:7–60は本文の内容と段の順を保持している。異常文字は多いが、主要な主張と性能値は読み取れる。"
    },
    "D": {
      "coverage": 5, "order": 5, "table": null, "legibility": 4, "usability": 5,
      "fatal": [],
      "comment": "bert-p1/D.txt:8–15は画像の本文を段落単位で正しく並べ、性能値も保持している。8のtaskspeciﬁc、14のleft-torightなどに軽微な接合がある。"
    }
  },
  "bert-p6": {
    "A": {
      "coverage": 5, "order": 3, "table": 3, "legibility": 4, "usability": 3,
      "fatal": [
        "bert-p6/A.txt:51–69ではBERTBASEとBERTLARGEの行名、両者のMNLI値、そのほかの値が分離しているため、行ごとの連続した値として読めない。",
        "bert-p6/A.txt:100–103ではsoftmaxの分数と総和記号が崩れ、原画像のP_i = exp(S·T_i)/Σ_j exp(S·T_j)をそのまま復元できない。",
        "bert-p6/A.txt:77–83では、passage fromとWikipediaの間に脚注9・10が挿入され、本文の文が中断する。"
      ],
      "comment": "bert-p6/A.txt:71–147には本文と表の主要な情報が揃っている。表の混在した走査順と数式の崩れには補正が必要である。"
    },
    "B": {
      "coverage": 5, "order": 4, "table": 5, "legibility": 3, "usability": 4,
      "fatal": [
        "bert-p6/B.txt:49–55では指数、分母、総和記号の対応が崩れ、softmaxの式が通常の文字列として読めない。",
        "bert-p6/B.txt:16のfineとtuningの間など、多数の単語内にU+FFFEが入っている。",
        "bert-p6/B.txt:36–41では脚注9・10が本文のpassage fromとWikipediaの間に入る。"
      ],
      "comment": "bert-p6/B.txt:1–7は列見出しと各モデルの値が行ごとに並び、表の対応が明確である。本文の要約には使えるが、数式を正確に説明する用途には不足がある。"
    },
    "C": {
      "coverage": 5, "order": 4, "table": 4, "legibility": 4, "usability": 4,
      "fatal": [
        "bert-p6/C.txt:144–155ではsoftmaxの分数構造が失われ、総和記号に相当する(cid:80)が式から離れて出力されている。",
        "bert-p6/C.txt:124–133では脚注9・10が本文のpassage fromとWikipediaの間に入る。"
      ],
      "comment": "bert-p6/C.txt:3–78の表は列単位で出るが、各列の値の順が一定なので復元できる。49–62ではSTS-BとMRPCの見出しが先にまとまり、対応の確認に注意が要る。"
    },
    "D": {
      "coverage": 5, "order": 4, "table": 4, "legibility": 4, "usability": 4,
      "fatal": [
        "bert-p6/D.txt:126–130では指数の一部が本文より前に出て、softmaxの分数と総和の対応が崩れている。",
        "bert-p6/D.txt:112–121では脚注9・10が本文のpassage fromとWikipediaの間に入る。"
      ],
      "comment": "bert-p6/D.txt:3–77の表は最初の列以外が列単位になるが、モデル順と値の個数から復元できる。本文は概ね自然に読める。"
    }
  },
  "bert-p7": {
    "A": {
      "coverage": 5, "order": 3, "table": 2, "legibility": 5, "usability": 3,
      "fatal": [
        "bert-p7/A.txt:22–35では表2のモデル名が先に列挙され、その後の数値が列単位と行単位で混在しているため、各モデルのDev・Test値の対応が不明瞭である。",
        "bert-p7/A.txt:104–107ではBERTBASEとBERTLARGEに対して81.6 86.6 86.3と続き、原画像にあるBERTBASEのTest欠測記号がなく、列を取り違えるおそれがある。",
        "bert-p7/A.txt:84–120では、継続する本文の式の間に脚注12と表4が挿入される。"
      ],
      "comment": "bert-p7/A.txt:77–149の本文は読めるが、表2と表4の値をこのテキストだけから引用するのは難しい。文字自体の大きな崩れはない。"
    },
    "B": {
      "coverage": 5, "order": 4, "table": 5, "legibility": 3, "usability": 4,
      "fatal": [
        "bert-p7/B.txt:17のcheckとpointsの間、37のquesとtionsの間などにU+FFFEが入っている。",
        "bert-p7/B.txt:40–57では、継続する本文の式の間に脚注12と表4が挿入される。"
      ],
      "comment": "bert-p7/B.txt:1–28と45–54では表の行名と値がまとまり、3表とも対応を読み取れる。本文の要点は保持されるが、異常文字が繰り返し現れる。"
    },
    "C": {
      "coverage": 5, "order": 3, "table": 3, "legibility": 5, "usability": 3,
      "fatal": [
        "bert-p7/C.txt:73–77ではunetとSLQA+の行名が先にまとまり、Publishedと欠測記号、両行の値が分離している。",
        "bert-p7/C.txt:102–104ではBERTBASEとBERTLARGEに対して81.6 86.6 86.3と続き、BERTBASEのTest欠測位置が明示されない。",
        "bert-p7/C.txt:90–114では、継続する本文の式の間に脚注12と表4が挿入される。"
      ],
      "comment": "bert-p7/C.txt:35–49の表2のBERT各行は対応が明確である。表3の一部と表4では、行と列の復元に不確実性が残る。"
    },
    "D": {
      "coverage": 5, "order": 3, "table": 2, "legibility": 5, "usability": 3,
      "fatal": [
        "bert-p7/D.txt:43–59ではTriviaQA併用モデルの行が先に現れ、その後に別の3モデルの数値と欠測記号が出るため、直前の行名へ誤って値を結び付けるおそれがある。",
        "bert-p7/D.txt:137–155ではモデル名、列見出し、値、欠測記号が別々に並び、表4の対応が不明瞭である。",
        "bert-p7/D.txt:128–170では、継続する本文の式の間に脚注12と表4が挿入される。"
      ],
      "comment": "bert-p7/D.txt:116–212の本文は概ね正しく読める。表の値は揃っていても、その所属を安全に判断しにくい。"
    }
  },
  "whitepaper-point-p1": {
    "A": {
      "coverage": 5, "order": 3, "table": null, "legibility": 5, "usability": 3,
      "fatal": [
        "whitepaper-point-p1/A.txt:13–24では第2章の題名「進展するデジタルがもたらす課題」が第3章の章番号より後に出ており、章番号・題名・本文の対応が崩れている。"
      ],
      "comment": "whitepaper-point-p1/A.txt:1–45に本文は揃っている。第Ⅰ部の第2章と第3章の区切りは画像による確認が必要である。"
    },
    "B": {
      "coverage": 5, "order": 5, "table": null, "legibility": 5, "usability": 5,
      "fatal": [],
      "comment": "whitepaper-point-p1/B.txt:2–14は部、章、説明の順が画像と一致し、所属も明確である。行の接合時に入る空白は意味の理解を妨げない。"
    },
    "C": {
      "coverage": 5, "order": 5, "table": null, "legibility": 5, "usability": 4,
      "fatal": [],
      "comment": "whitepaper-point-p1/C.txt:3–37は章と本文の対応を正しく保持している。39–45には画像の本文外の版下ファイル名と日時が重複して出ている。"
    },
    "D": {
      "coverage": 5, "order": 2, "table": null, "legibility": 5, "usability": 4,
      "fatal": [
        "whitepaper-point-p1/D.txt:2–10では第Ⅱ部が第Ⅰ部より先に出る。",
        "whitepaper-point-p1/D.txt:17–21では第Ⅰ部の第3章が第2章より先に出る。"
      ],
      "comment": "whitepaper-point-p1/D.txt:2–21では各章の題名と説明は保たれるが、部と章の順序が画像と異なる。構成順を説明する要約では補正が必要である。"
    }
  },
  "whitepaper-summary-p2": {
    "A": {
      "coverage": 5, "order": 5, "table": null, "legibility": 5, "usability": 5,
      "fatal": [],
      "comment": "whitepaper-summary-p2/A.txt:5–35は、第Ⅰ部、第Ⅱ部、データ集の順と各章の所属を保持している。本文に意味を変える崩れは見当たらない。"
    },
    "B": {
      "coverage": 5, "order": 5, "table": null, "legibility": 4, "usability": 5,
      "fatal": [],
      "comment": "whitepaper-summary-p2/B.txt:5–18は本文と構成順を保持している。9では第2章と第3章の見出しが同じ行になるが、章番号から区別できる。"
    },
    "C": {
      "coverage": 5, "order": 2, "table": null, "legibility": 5, "usability": 4,
      "fatal": [
        "whitepaper-summary-p2/C.txt:2–12では第Ⅱ部と末尾のデータ集が第Ⅰ部より先に出ており、原画像の構成順が逆転している。"
      ],
      "comment": "whitepaper-summary-p2/C.txt:2–19に各部の説明と章見出しは揃っている。各ブロック内の対応は保たれるため、内容の要約には使える。"
    },
    "D": {
      "coverage": 5, "order": 5, "table": null, "legibility": 5, "usability": 5,
      "fatal": [],
      "comment": "whitepaper-summary-p2/D.txt:2–22は画像の上から下への順序と、部・章・説明の対応を保持している。本文をそのまま要約に使える。"
    }
  },
  "whitepaper-summary-p4": {
    "A": {
      "coverage": 5, "order": 3, "table": 3, "legibility": 4, "usability": 3,
      "fatal": [
        "whitepaper-summary-p4/A.txt:30–39では右上の図の題名と吹き出しが、左上の図の2014年と2024年の値の間に入る。",
        "whitepaper-summary-p4/A.txt:43の「そ新の聞ほ社かのニュースサイト」は文字列が混線しており、凡例の項目を正しく読めない。",
        "whitepaper-summary-p4/A.txt:52–117では利用率、ニュース源としての利用率、年代、媒体名が分離し、個々の百分率の所属が明確でない。"
      ],
      "comment": "whitepaper-summary-p4/A.txt:3–4の要点は保持される。127–167の表は列単位と行単位の並びが混在し、対応の復元に注意が要る。"
    },
    "B": {
      "coverage": 5, "order": 2, "table": 4, "legibility": 5, "usability": 3,
      "fatal": [
        "whitepaper-summary-p4/B.txt:65–164では左下の利用率グラフの途中に、右下の信頼度表の見出し・説明・列名が入り、複数の図表が混線している。",
        "whitepaper-summary-p4/B.txt:23–48では2014年・2024年のラベルと値が分散し、2014年の48.5%や12.8%を2024年の値と誤読するおそれがある。"
      ],
      "comment": "whitepaper-summary-p4/B.txt:5–8の本文要点は正しい。174–252の信頼度表は年代ごとに4値が続くので復元できるが、テレビの列名が116まで離れている。"
    },
    "C": {
      "coverage": 5, "order": 2, "table": 5, "legibility": 5, "usability": 3,
      "fatal": [
        "whitepaper-summary-p4/C.txt:1–23では左下グラフの数値と凡例がページ題名より先に出て、対応するグラフ題名は31まで離れている。",
        "whitepaper-summary-p4/C.txt:58–75では左上グラフの値が系列単位で出る一方、年と凡例が後に分離し、通常の行として読むと値の所属を誤り得る。"
      ],
      "comment": "whitepaper-summary-p4/C.txt:44–52は信頼度表の列名と各年代の4値が揃い、表として最も明瞭である。ページ全体では図の要素が本文の前後へ大きく分散している。"
    },
    "D": {
      "coverage": 5, "order": 3, "table": 4, "legibility": 5, "usability": 3,
      "fatal": [
        "whitepaper-summary-p4/D.txt:87–159では左下グラフの値、年代、系列名が別々に出ており、各値を年代と媒体に結び付ける根拠が弱い。",
        "whitepaper-summary-p4/D.txt:165–169では右上グラフの吹き出しと出典が左下グラフの後に現れ、元の図との対応が失われている。"
      ],
      "comment": "whitepaper-summary-p4/D.txt:5–9の要点と、175–263の信頼度表の全値は保持される。表は8年代分の値が列単位で並ぶため復元できるが、グラフの詳細値の利用は難しい。"
    }
  },
  "whitepaper-summary-p7": {
    "A": {
      "coverage": 5, "order": 2, "table": null, "legibility": 5, "usability": 3,
      "fatal": [
        "whitepaper-summary-p7/A.txt:95–160では左下の年代別グラフの見出し・目盛りの後に、右上の国別企業グラフの値と凡例が入る。",
        "whitepaper-summary-p7/A.txt:174–210では20代の44.7%と残りの年代別値の間に、大企業の値や別図の吹き出しが入り、年代と数値の対応が崩れている。",
        "whitepaper-summary-p7/A.txt:84–86では中国の2023年度56.3%が2024年度81.2%より先に出ており、先行する年度表示順と一致しない。"
      ],
      "comment": "whitepaper-summary-p7/A.txt:5–17の主要な説明は正しい。図の詳細値は複数の図をまたいで混在し、そのまま引用しにくい。"
    },
    "B": {
      "coverage": 5, "order": 2, "table": null, "legibility": 5, "usability": 2,
      "fatal": [
        "whitepaper-summary-p7/B.txt:15–54では国別個人利用の図から26.7%などが離れ、26.7%は152に、ドイツと中国の表示は154–157に出ている。",
        "whitepaper-summary-p7/B.txt:127–161では企業規模別の見出しの後に、年代別の44.7%と20歳～29歳、国別個人利用の81.2%と56.3%、国別企業図の見出しが混ざる。",
        "whitepaper-summary-p7/B.txt:138の4.3%は、日本の企業方針の値だが、中国の個人利用の81.2%・56.3%の直前に現れ、図の所属を取り違えるおそれがある。"
      ],
      "comment": "whitepaper-summary-p7/B.txt:5–14の本文だけなら要点を要約できる。グラフ部分は国・年代・企業規模の混線が大きく、詳細値の利用には適さない。"
    },
    "C": {
      "coverage": 5, "order": 2, "table": null, "legibility": 5, "usability": 3,
      "fatal": [
        "whitepaper-summary-p7/C.txt:1–62では3図の数値・目盛り・凡例が題名より先に出て、個人利用の国名は79–82まで離れている。",
        "whitepaper-summary-p7/C.txt:45–61の個人利用値は日本、米国、ドイツ、中国の順だが、79–82の国名は中国、米国、ドイツ、日本の順であり、出現順で対応させると国を取り違える。"
      ],
      "comment": "whitepaper-summary-p7/C.txt:64–71の本文要点と、99–109の年代別の値は保持される。国別・企業規模別の図では系列と対象の関係を補う必要がある。"
    },
    "D": {
      "coverage": 5, "order": 3, "table": null, "legibility": 5, "usability": 3,
      "fatal": [
        "whitepaper-summary-p7/D.txt:33–43では米国の値68.8%・46.3%がドイツのラベルの後に出て、ドイツ自身の値も年度表示と逆順の34.6%、59.2%になる。",
        "whitepaper-summary-p7/D.txt:126–131では年代が20代から60代の順なのに、数値は23.8%、29.6%、19.9%、15.5%、44.7%となり、出現順で対応させると年代を取り違える。",
        "whitepaper-summary-p7/D.txt:63–114では国別企業グラフの値と凡例が入り交じり、日本や米国の各方針別の値を連続した行として読めない。"
      ],
      "comment": "whitepaper-summary-p7/D.txt:5–9の本文と、154–174の企業規模別の値は比較的読みやすい。国別と年代別の詳細値には順序の誤りが残る。"
    }
  },
  "whitepaper-summary-p11": {
    "A": {
      "coverage": 5, "order": 5, "table": 5, "legibility": 5, "usability": 5,
      "fatal": [],
      "comment": "whitepaper-summary-p11/A.txt:7–14は3つの社会課題を画像どおりに並べ、18–36では課題名と百分率が交互に対応している。本文と表を安全に要約できる。"
    },
    "B": {
      "coverage": 5, "order": 4, "table": 5, "legibility": 5, "usability": 4,
      "fatal": [
        "whitepaper-summary-p11/B.txt:9–15では表の最初の行が災害対応の本文末尾に接合され、表の題名と百分率の定義が全5行の後に出る。"
      ],
      "comment": "whitepaper-summary-p11/B.txt:9–13は各課題名と値の対応を保持している。表題を後から読んで数値の意味を補う必要がある。"
    },
    "C": {
      "coverage": 5, "order": 5, "table": 5, "legibility": 5, "usability": 5,
      "fatal": [],
      "comment": "whitepaper-summary-p11/C.txt:5–19は本文から表題への順序が正しく、20–38では課題名と数値の対応が明確である。意味を変える崩れは見当たらない。"
    },
    "D": {
      "coverage": 5, "order": 4, "table": 4, "legibility": 5, "usability": 4,
      "fatal": [],
      "comment": "whitepaper-summary-p11/D.txt:5–27の本文と表題は正しい。29–47では5つの課題名の後に5値がまとまるが、双方の順序が一致するため復元できる。"
    }
  },
  "kanpo-p1-p1": {
    "A": {
      "coverage": 5, "order": 1, "table": null, "legibility": 1, "usability": 1,
      "fatal": [
        "kanpo-p1-p1/A.txt:5–90では日本語教育の項目の途中から始まり、別項目や行の続きが原画像の右から左への順と異なる順で並ぶ。",
        "kanpo-p1-p1/A.txt:432–555では省令の題名の前半と後半の間に、水産資源や国家試験など別項目の断片が入る。",
        "kanpo-p1-p1/A.txt:3・430の年月日・号数には私用領域文字が入り、92などの参照ページは(cid:25505)のような文字列になる。"
      ],
      "comment": "kanpo-p1-p1/A.txtには目次の本文がほぼ揃うが、大部分が1文字ずつの改行である。文字の存在量に対して文章の復元が難しく、要約には使えない。"
    },
    "B": {
      "coverage": 1, "order": 1, "table": null, "legibility": 1, "usability": 1,
      "fatal": [
        "kanpo-p1-p1/B.txt:1–5には判読不能な数字相当の私用領域文字、7–40には「採」「探」「掠掟」などが出るだけで、原画像の目次本文が出ていない。"
      ],
      "comment": "kanpo-p1-p1/B.txt:1–40から省令や告示の題名を取得できない。ページの内容を要約する根拠がない。"
    },
    "C": {
      "coverage": 1, "order": 1, "table": null, "legibility": 1, "usability": 1,
      "fatal": [
        "kanpo-p1-p1/C.txt:1–4から日本語が多数の異なる文字体系の文字へ置き換わっており、年月日や項目名を読めない。",
        "kanpo-p1-p1/C.txt:121–209では複数項目の文字列が混在し、原画像の目次の並びを復元できない。"
      ],
      "comment": "kanpo-p1-p1/C.txtは文字列の量はあるが、本文として判読できる情報がほぼない。網羅は読める本文が残っているかで判定した。"
    },
    "D": {
      "coverage": 5, "order": 2, "table": null, "legibility": 3, "usability": 2,
      "fatal": [
        "kanpo-p1-p1/D.txt:12–14では「犯罪被害財産支給手続開始決定、建」から始まる項目の縦の行が逆順になっている。",
        "kanpo-p1-p1/D.txt:44–50では日本語教育の項目が「る件」から始まり、題名の先頭が49まで後置される。",
        "kanpo-p1-p1/D.txt:63–72では水産資源の長い項目の縦の行が逆順になり、文をそのまま読めない。",
        "kanpo-p1-p1/D.txt:7の年月日・号数は私用領域文字で、28・51などの参照ページも「採」「探」などへ置き換わっている。"
      ],
      "comment": "kanpo-p1-p1/D.txtは各縦行の内部では日本語を読め、目次本文もほぼ揃う。縦行の接続と項目の配置が崩れ、誤解せずに要約するには画像が必要である。"
    }
  },
  "kanpo-p2-p1": {
    "A": {
      "coverage": 5, "order": 1, "table": 1, "legibility": 1, "usability": 1,
      "fatal": [
        "kanpo-p2-p1/A.txt:11–43では告示末尾の適用日・署名が先に出て、告示番号と導入文は57–163に後置される。",
        "kanpo-p2-p1/A.txt:219–579では改正後と改正前の条文の断片が交互に現れ、各側の文の続きも逆順になるため、変更内容を取り違えるおそれがある。",
        "kanpo-p2-p1/A.txt:2391–2448ではページ右上の省令番号と根拠条文が末尾近くに出ており、ページの読む順が大きく崩れている。",
        "kanpo-p2-p1/A.txt:1777–1825などには(cid:23075)が多数挿入され、本文のほぼ全体が1文字単位の改行になっている。"
      ],
      "comment": "kanpo-p2-p1/A.txtには条文の文字はほぼ揃っている。改正前後の所属と文章の接続を保持していないため、法令の変更点の要約には使えない。"
    },
    "B": {
      "coverage": 1, "order": 1, "table": 1, "legibility": 1, "usability": 1,
      "fatal": [
        "kanpo-p2-p1/B.txt:1から日本語が異なる文字体系の文字へ置き換わり、19–65などの省令・告示の導入も判読できない。",
        "kanpo-p2-p1/B.txt:37–45などでは隣接する縦行の断片が同一行に混ざり、1130–1154の改正前後の見出しに相当する文字列も壊れている。"
      ],
      "comment": "kanpo-p2-p1/B.txtは条文を正しい日本語として読めない。改正前後のセル対応も復元できない。"
    },
    "C": {
      "coverage": 1, "order": 1, "table": 1, "legibility": 1, "usability": 1,
      "fatal": [
        "kanpo-p2-p1/C.txt:1–11には私用領域文字と「挮」だけが出ており、省令・告示の本文と改正対照表が欠落している。"
      ],
      "comment": "kanpo-p2-p1/C.txtから本文の内容を読み取れない。表の改正前後の対応も評価できる形で残っていない。"
    },
    "D": {
      "coverage": 1, "order": 1, "table": 1, "legibility": 5, "usability": 1,
      "fatal": [
        "kanpo-p2-p1/D.txt:1は「（このページは OCR が要る: vertical）」という通知だけで、省令・告示の本文と改正対照表を出力していない。"
      ],
      "comment": "kanpo-p2-p1/D.txt:1の通知自体には文字の崩れがないためlegibilityは5とした。本文がないため、内容の要約には使えない。"
    }
  }
}
```

## 総評

- 参照パスはすべて `docs/research/adr-0024-verification-2026-11-15/judge/` からの相対パスで、行番号は空行を含む。図だけのページでは `table` を `null` とし、全写しで欠ける画像内文字は、依頼の説明に従って減点対象から除外した。
- **英語論文の本文**は段組みの読み順を概ね保持している。一方、`bert-p1/C.txt:7–57`、`bert-p6/B.txt:10–77`、`bert-p7/B.txt:17–75` には単語内のU+FFFEが繰り返し現れる。
- **論文の表と数式**には別の問題がある。`bert-p6/B.txt:1–7`、`bert-p7/B.txt:1–28` は行と値の対応が明瞭だが、ほかには行名・数値・欠測記号の分離がある。p6のsoftmax式は4写しとも分数構造が崩れている。
- **日本語の構成説明**は、文字が正しくても見出しの順序が崩れる。`whitepaper-point-p1/A.txt:13–24` は章番号と題名の対応、同Dの2–21と `whitepaper-summary-p2/C.txt:2–19` は部・章の順に問題がある。
- **複数グラフを置くスライド**では、本文の要点より詳細値の利用が難しい。特に `whitepaper-summary-p7/D.txt:126–131` は年代と値の順が一致せず、Cの45–61と79–82も国名を出現順で対応させると誤る。p4の信頼度表はCの44–52が明瞭である。
- **単純な2列表**は良好で、`whitepaper-summary-p11/A.txt:18–36` とCの20–38は課題名と値が明確に対応する。Dの29–47も、双方の順序を照合すれば復元できる。
- **縦書き官報**は、本文の文字が揃うことと要約に使えることの差が大きい。`kanpo-p1-p1/D.txt:44–50` の縦行の逆順、`kanpo-p2-p1/A.txt:219–579` の改正前後の混線は意味の復元を妨げる。OCR通知だけの同Dは文字として明瞭だが、本文の代替にはならない。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
