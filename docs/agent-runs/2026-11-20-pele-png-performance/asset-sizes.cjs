// 画像を個別に圧縮した合計を求める。HTTP の通信時間は計測しない。
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const directory = process.env.PELE_PERF_RUN || __dirname;
const fixture = process.env.STATIC_IMAGE_FIXTURE || path.join(directory,'fixture');
const manifest = JSON.parse(fs.readFileSync(path.join(fixture,'manifest.json'),'utf8'));
const results = {definition:'明暗各 50 枚の画像ファイルを個別に圧縮した合計。HTML、CSS、HTTP ヘッダーは含まない。',conditions:{}};
for (const condition of ['pele','normalized','png1x','png2x']) {
  let rawBytes=0, gzipLevel9Bytes=0, brotliQuality11Bytes=0;
  for (const theme of ['light','dark']) for (const row of manifest.images[theme]) {
    const data=fs.readFileSync(path.join(fixture,row[condition].path));
    rawBytes+=data.length;
    gzipLevel9Bytes+=zlib.gzipSync(data,{level:9}).length;
    brotliQuality11Bytes+=zlib.brotliCompressSync(data,{params:{[zlib.constants.BROTLI_PARAM_QUALITY]:11}}).length;
  }
  results.conditions[condition]={rawBytes,gzipLevel9Bytes,brotliQuality11Bytes};
}
fs.writeFileSync(path.join(directory,'asset-sizes.json'),JSON.stringify(results,null,2));
console.log(JSON.stringify(results));
