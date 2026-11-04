# タスク：破綻しないディレクトリ構成案を考える

## 作者の指示

> 破綻しないディレクトリ構成案を考えて

対象は、info-hive の Claude Code プラグイン（既存の `wiki` と、これから作る日々の記録のプラグイン `log`）が読み書きする、利用者の作業領域のディレクトリ構成である。このリポジトリ（`info-hive-dev`）自体の構成ではない。

## これまでに作者が決めたこと（作者の言葉のまま）

### 日々の記録の機能について

> 1. 保存先の既定をどれにするか。プロジェクト直下の daily/、グローバルの ~/daily/、両方を選べるようにする、の 3 つから選びます。私は両方を選べるようにし、既定をグローバルにする案にする
> 2. 時刻をどう書くか。09:12-10:40 を 1 行に持つ
> 3. 直接 Wiki に昇格せずに、 notes/ ディレクトリにノートを記述してノウハウなどをユーザーが編集できるようにする
> 4. フックによる自動記録を、保留にする
>
> * 作業メモとタスク（前日からの繰り越し、本日のタスク、次回への繰り返し）は別に記述できるようにする。これは作業メモは簡潔に記述し、詳細については、タスクで記述するため
> * daily のテンプレートは Foam のテンプレート置き場に配置する
> * その日に発生した問題や突発的なイベントについて記述する欄を追加する

「次回への繰り返し」は、のちに作者が「繰り越しで合っている」と確認した。

> info-hive-log にします

（リポジトリ名を `info-hive-log`、プラグイン名を `log` とする解釈で ADR-0006 に記録済み）

### ディレクトリ構成について

> 以下のようなディレクトリ構成にしたい。ディレクトリ名は仮だが、先頭に二桁の英数字とアンダースコアを付ける

```
~/info-hive/（またはプロジェクトルート）
├─.foam
│  └─templates
├─.github
│  └─instructions
├─00_Inbox
│  └─ADR
├─10_Assets
├─20_Daily
│  └─2026
│      └─04
├─30_Weekly
├─40_Projects
├─50_Knowledge
├─60_Output
├─90_Wiki
├─91_Raw
└─A0_Archive
```

> 1. `00_Inbox/ADR` は不要。プロジェクトごとの info-hive なら XX_ADR（XX は任意の数字）でルートのすぐ下に置く
> 2. `RAW_ROOT` の下の assets に Wiki 用の画像を置く。`XX_Assets` は Wiki 以外の用途で使用する
> 3. プロジェクトルートの下にプロジェクト名で作成した info-hive のディレクトリを置き、プロジェクトで開発するコード（info-hive 関連のコードではない）は、サブモジュールとして配置する

## 読むべき文書とコード

- `AGENTS.md`（リポジトリの役割、日本語と機械が読む文字列の方針、プラグインを足す手順）
- `docs/adr/0003-split-marketplace-repo.md`、`docs/adr/0005-wiki-figures-use-mermaid-and-svg.md`、`docs/adr/0006-daily-journal-is-separate-plugin.md`（0004 と 0005 はまだコミットされていないが、作業ツリーにある）
- `docs/research/daily-journal-methodology-options.md`、`docs/research/daily-journal-decision-matrix.md`
- `info-hive-wiki/skills/info-hive/SKILL.md`（wiki の探し方）、`info-hive-wiki/commands/init.md`、`info-hive-wiki/skills/info-hive/scripts/init_wiki.py`（`--wiki-dir`、`--raw-dir`）、`info-hive-wiki/skills/info-hive/scripts/wiki_lint.py`（走査の除外と孤立の判定）
- Foam の文書：https://raw.githubusercontent.com/foambubble/foam/master/docs/user/features/templates.md 、https://raw.githubusercontent.com/foambubble/foam/master/docs/user/features/daily-notes.md

## 成果に含めるもの

1. グローバル（`~/info-hive/`）とプロジェクトの両方の場合の、ディレクトリ構成案（ツリー）
2. 各ディレクトリの役割、誰が（人、どのプラグインのどのコマンド）書くか、ファイルの命名
3. 「破綻」として何を想定したか、それぞれの場面で構成がどう持ちこたえるか（例：名前の変更、年をまたぐ、ファイル数の増加、プラグインの追加、wiki との境界、VS Code・Foam・Git との関係、Windows と macOS・Linux の違い）
4. プラグインが作業領域とディレクトリの場所をどう見つけるか
5. 作者の決定や既存の ADR、wiki の現在のコードと食い違う点と、その扱いの提案
6. 作者が決める必要のある未決事項

リポジトリのファイルは書き換えないこと。成果は日本語で書く。
