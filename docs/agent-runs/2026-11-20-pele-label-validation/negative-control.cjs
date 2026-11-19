// 既知の欠陥を加えた対照図で、検出器が反応することを確認する。
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');
const { Resvg } = require(path.join(process.env.TEMP,'pele-png-tools/node_modules/@resvg/resvg-js'));
const run = process.env.PELE_LABEL_RUN || __dirname;
const fixture = path.join(run,'negative-fixture');
const out = path.join(run,'negative-results');
if (fs.existsSync(fixture) || fs.existsSync(out)) throw Error('対照試験の出力先が存在する');
fs.mkdirSync(fixture);
const fonts = JSON.parse(fs.readFileSync('docs/agent-runs/2026-11-19-pele-png-compatibility/results/results.json','utf8')).fonts;
const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="120"><g class="pele-node"><rect x="10" y="10" width="50" height="40" fill="#eef"/><text x="15" y="35" font-size="16">はみ出す文字列</text><text x="15" y="35" font-size="16">重なる</text></g><text x="240" y="90" font-size="16" opacity="0">欠</text></svg>';
fs.writeFileSync(path.join(fixture,'negative-light-normalized.svg'),svg);
const images = [1,2].map(scale=>{
  const png = new Resvg(svg,{background:'#ffffff',fitTo:{mode:'zoom',value:scale},font:{fontFiles:fonts.map(f=>f.file),loadSystemFonts:false,defaultFontFamily:'Noto Sans JP'}}).render().asPng();
  const file='negative-light-'+scale+'x.png';fs.writeFileSync(path.join(fixture,file),png);
  return {scale,file,sha256:crypto.createHash('sha256').update(png).digest('hex')};
});
fs.writeFileSync(path.join(fixture,'results.json'),JSON.stringify({fonts,prepared:[{id:'negative-light',theme:'light',images}]},null,2));
const child=spawnSync(process.execPath,[path.join(__dirname,'audit.cjs')],{env:{...process.env,PELE_LABEL_FIXTURE:fixture,PELE_LABEL_OUT:out},stdio:'inherit'});
if(child.status!==0)throw Error('対照試験の実行に失敗');
const result=JSON.parse(fs.readFileSync(path.join(out,'results.json'),'utf8'));
for(const browser of result.observations){
  if(!browser.labels[0].envelopeOutsideShape || !browser.overlaps.length)throw Error('既知のはみ出し・重なりを検出できない');
}
for(const image of result.rendering){
  const missing=image.labelContributions.find(label=>label.text==='欠');
  if(missing.pixels!==0 || missing.chars[0].pixels!==0)throw Error('既知の非表示文字を検出できない');
}
console.log('両ブラウザで既知のはみ出し・重なり、1 倍・2 倍で非表示文字を検出した');
