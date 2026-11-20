// デコード計測と、先頭画像のスクリーンショット取得完了までを別々に残す。
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { imageFormats, loadStaticImageFixture, showStaticImages } from '../../../poc/browse-static-image/pele-image-fixture.mjs';
const require=createRequire(join(process.cwd(),'tests/wiki/browse/package.json'));
const {webkit}=require('playwright');
const {PNG}=require('playwright-core/lib/utilsBundle');
const fixture=loadStaticImageFixture(resolve(process.env.STATIC_IMAGE_FIXTURE));
const out=resolve(process.env.PAINT_OUT);
mkdirSync(out);
const results=[];
for(let repeat=1;repeat<=2;repeat++) {
 for(const format of repeat===1?imageFormats:imageFormats.toReversed()) {
  const browser=await webkit.launch({headless:true});
  try {
   const page=await browser.newPage({viewport:{width:1200,height:900},deviceScaleFactor:1});
   await page.goto(pathToFileURL(fixture.pagePath).href);
   const row={repeat,format,version:browser.version()};
   for(const color of ['light','dark']) {
    const start=performance.now();
    const decoded=await showStaticImages(page,fixture.manifest.images[color],format,color);
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    const screenshot=await page.locator('img.fig-img').first().screenshot();
    const screenshotCompletedMs=performance.now()-start;
    const file=format+'-'+repeat+'-'+color+'.png';writeFileSync(join(out,file),screenshot);
    const image=PNG.sync.read(screenshot),background=color==='light'?[255,255,255]:[31,31,31];
    let visiblePixels=0;
    for(let i=0;i<image.data.length;i+=4)if([0,1,2].some(c=>Math.abs(image.data[i+c]-background[c])>16))visiblePixels++;
    if(visiblePixels<50)throw Error('先頭画像の描画を確認できない');
    row[color]={...decoded,screenshotCompletedMs,file,visiblePixels,width:image.width,height:image.height};
   }
   results.push(row);
   writeFileSync(join(out,'results.json'),JSON.stringify({definition:'API 呼び出しから全画像のデコード、2 回の animation frame、先頭画像の screenshot 取得完了まで。初めて画面に出た時刻とは異なる。',results},null,2));
  } finally {await browser.close();}
 }
}
console.log('初回描画を 8 ケース・明暗で確認');
