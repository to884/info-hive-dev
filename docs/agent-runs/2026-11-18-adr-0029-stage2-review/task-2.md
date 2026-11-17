# 第1回の修正の敵対的レビュー

同じ段階2の依頼の続きです。第1回の重大1〜3と軽微の対応を、現在のコードで確かめてください。編集・再委譲は不要です。対象の分担と規範は前回と同じで、新しい範囲の要求ではありません。

対応の内容は review-1-disposition.md。今回の主な差分は wiki_raw.py の _raw_meta と身元照合・外の原本、wiki_captions.py の raw_warnings と動画に関わる findings の分離、wiki_youtube.py の cmd_verify、wiki_session.py の保存直後の resolve_raw、wiki_lint.py の文脈の保持と raw_outside、tests/wiki/test_raw_links.py と test_wiki_youtube.py と test_wiki_session.py の追加試験です。

身元の欄がない原本は、明示的な不一致ではなく未確認として version_unverified に残します。読めない I/O は unknown のままです。字幕の拒否・不確かさ・途中の未検査・版未検証は raw_warnings に残し、動画の欄か定義があるページ、または verify の対象の raw を指すページの拒否を findings にします。訂正の根拠は check_definition が使う時点で検査します。raw_warnings は無関係な原本だけで取り込みを止める理由にはしません。

実際のプロジェクトの wiki の missing_raw は2件から0件に戻りました。関連とセッションの全体324件（skip7）、MCP5件、および最後の実行の追加試験を含む raw / YouTube / セッション保存後105件（skip1）が成功しています。根の記録の作成と読み込み、raw_sha256 の全書き手への移行、書き込みの部品は後続段階です。raw の根を渡さないと、途中の検査ができないことは明示して返します。外の原本の例外と、操作ごとの起点の決定は作者が承認した規範のままです。

各指摘の閉鎖を再現と根拠で判定し、今回の修正が導入した欠陥があれば挙げてください。重大には発生の度合い A〜D を添え、実測・mock・推論を分けてください。レビューの範囲を全プラグインの未移行の書き手へ広げず、今回の読み手と呼び出し元の整合性を対象にしてください。
