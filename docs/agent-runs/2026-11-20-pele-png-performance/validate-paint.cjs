// 画像取得の反復一致と、現行 SVG・今回の SVG 試作の表示一致を照合する。
const fs = require('fs');
const path = require('path');
const { PNG } = require(path.join(process.cwd(),'tests/wiki/browse/node_modules/playwright-core/lib/utilsBundle'));
const directory = process.env.PELE_PERF_RUN || __dirname;
function equalImages(first,second) {
  const a=PNG.sync.read(fs.readFileSync(path.join(directory,'paint',first)));
  const b=PNG.sync.read(fs.readFileSync(path.join(directory,'paint',second)));
  return a.width===b.width && a.height===b.height && a.data.equals(b.data);
}
const repeats=[];
for(const format of ['pele','normalized','png1x','png2x']) for(const theme of ['light','dark']) {
  const equal=equalImages(format+'-1-'+theme+'.png',format+'-2-'+theme+'.png');
  if(!equal)throw Error('画像の反復が不一致');
  repeats.push({format,theme,equal});
}
const sourceNormalized=[];
for(const theme of ['light','dark']) for(const repeat of [1,2]) {
  const equal=equalImages('pele-'+repeat+'-'+theme+'.png','normalized-'+repeat+'-'+theme+'.png');
  if(!equal)throw Error('現行 SVG と試作 SVG の先頭画像の表示が不一致');
  sourceNormalized.push({theme,repeat,equal});
}
fs.writeFileSync(path.join(directory,'paint/validation.json'),JSON.stringify({repeats,sourceNormalized,manualObservation:'先頭図の明暗の代表画像で「入力 0」「判定」「保存」と矢印を目視した。'},null,2));
console.log('16 枚の画像の反復一致と、現行 SVG・試作 SVG の先頭画像一致を確認');
