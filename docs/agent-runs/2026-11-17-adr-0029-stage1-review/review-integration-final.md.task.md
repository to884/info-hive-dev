同じレビューの続き。今回の差分だけを読み、残る重大な欠陥または既存仕様の後退があるか確認してください。変更禁止、委譲不要、大規模テストとCI待機は不要です。
差分は integration-final-fixes.diff です。
1. 根の下のディレクトリを外から指す別名にも、解決済みの祖先から同じ根の実体を探すことで根の規則を引き継ぎます。根を見つけると残りを article_path で検査します。実ケースの case_variant_root 試験に、外の view が WIKI/concepts を指す入力も追加しました。
2. refused_link の照合だけを posix_rel で、build_page_index と同じ鍵にしました。OS上のファイルの読み取りパスは変えません。
3. classify_source_ref に任意の link_warnings を追加し、lint とbrowse が共通で refused を扱います。リンクを missing にしません。
4. Core.resolve は拒否した候補を先に判定し、同じスラッグの読める別のページへ黙って結び付けません。明示した別のパスなら解決します。
5. ディレクトリそのものへの wikilink は採用しません。[[concepts/jump]] は規約上 concepts/jump.md のページを指すので、リンクのディレクトリ concepts/jump 自体の存在では、そのページの存在や拒否を確定できません。jump.md がない場合のリンク切れを消すと本当の欠落を隠します。concepts/jump/x のように拒否した道の下を指す場合は refused です。この区別をテストにも記録しました。
この方針と差分の実装が食い違う箇所だけを指摘してください。前回の Mac 根そのもののケースは CI run 44112975529、macOS で skip なしの69件が通りました。新しい下位ディレクトリ別名のケースは今回のCIで確認します。
