// OCR 不一致ラベルの拡大画像を、Playwright で一覧にする。
const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright'));
const { PNG } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright-core/lib/utilsBundle'));
const directory = path.resolve(process.env.PELE_LABEL_RUN || 'docs/agent-runs/2026-11-20-pele-label-validation');
const source = path.resolve('docs/agent-runs/2026-11-19-pele-png-compatibility/results');
const audit = JSON.parse(fs.readFileSync(path.join(directory,'results/results.json'),'utf8'));
const mismatches = JSON.parse(fs.readFileSync(path.join(directory,'ocr/mismatches.json'),'utf8'));
const escape = value => value.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1400,height:1000},deviceScaleFactor:1});
  for(let start=0;start<mismatches.length;start+=12) {
    const cards=[];
    for(const row of mismatches.slice(start,start+12)) {
      const label=audit.observations.find(x=>x.browser==='chromium'&&x.id===row.id).labels[row.index];
      const original=PNG.sync.read(fs.readFileSync(path.join(source,row.id+'-2x.png')));
      const b=label.bounds;
      const x=Math.max(0,Math.floor(b.x*2)-8),y=Math.max(0,Math.floor(b.y*2)-8);
      const width=Math.min(original.width-x,Math.ceil((b.x+b.width)*2)+8-x);
      const height=Math.min(original.height-y,Math.ceil((b.y+b.height)*2)+8-y);
      const cropped=new PNG({width,height});
      PNG.bitblt(original,cropped,x,y,width,height,0,0);
      const image=PNG.sync.write(cropped);
      cards.push('<section><p>'+escape(row.id+' / '+row.index)+'</p><p>'+escape(row.expected)+'</p><img src="data:image/png;base64,'+image.toString('base64')+'"></section>');
    }
    await page.setContent('<!doctype html><meta charset="utf-8"><style>body{margin:12px;display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start;font:14px sans-serif}section{border:1px solid #aaa;padding:10px;min-width:0}p{margin:4px}img{max-width:100%;height:auto;display:block}</style>'+cards.join(''));
    await page.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(img=>img.decode())));
    await page.screenshot({path:path.join(directory,'ocr/review-'+(start/12+1)+'.png'),fullPage:true});
  }
  await browser.close();
  console.log('OCR 不一致画像を一覧にした '+mismatches.length+' ラベル');
})().catch(error=>{console.error(error);process.exit(1);});
