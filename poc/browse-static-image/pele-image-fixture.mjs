// 画素寸法と CSS 表示寸法を分け、4 方式を同じ表示条件で比較する。
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
export const imageFormats = ['pele','normalized','png1x','png2x'];
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
export function loadStaticImageFixture(root) {
 const manifestPath=join(root,'manifest.json'),pagePath=join(root,'page.html');
 const manifest=JSON.parse(readFileSync(manifestPath,'utf8'));
 assert.equal(manifest.format,2);
 const files=[manifestPath,pagePath,join(root,'images.css')];
 for(const font of manifest.fonts) { assert.equal(digest(readFileSync(font.file)),font.sha256);files.push(font.file); }
 for(const color of ['light','dark']) {
  assert.equal(manifest.images[color].length,manifest.count);
  for(const [index,row] of manifest.images[color].entries()) {
   assert.equal(row.index,index);
   assert.ok([row.width,row.height].every(n=>Number.isSafeInteger(n)&&n>0));
   for(const type of imageFormats) {
    const asset=row[type];
    assert.equal(asset.path,color+'/'+index+'-'+type+(type.startsWith('png')?'.png':'.svg'));
    const file=join(root,asset.path),bytes=readFileSync(file);
    assert.equal(bytes.length,asset.bytes);assert.equal(digest(bytes),asset.sha256);
    assert.equal(asset.width,row.width*(type==='png2x'?2:1));assert.equal(asset.height,row.height*(type==='png2x'?2:1));files.push(file);
   }
  }
 }
 return {manifest,pagePath,files};
}
export async function showStaticImages(page,images,type,color) {
 return page.evaluate(async({images,type,color})=>{
  const start=performance.now();document.documentElement.dataset.theme=color;
  const elements=images.map(row=>{
   const img=document.createElement('img');img.className='fig-img';img.alt='図 '+row.index;
   img.width=row.width;img.height=row.height;img.src=row[type].path;return img;
  });
  document.querySelector('main').replaceChildren(...elements);
  const first=elements[0].decode().then(()=>performance.now()-start);
  const [,firstDecodeMs]=await Promise.all([Promise.all(elements.slice(1).map(img=>img.decode())),first]);
  const decodeMs=performance.now()-start;
  for(const [index,img] of elements.entries()) {
   const row=images[index],asset=row[type],rect=img.getBoundingClientRect();
   if(img.naturalWidth!==asset.width||img.naturalHeight!==asset.height||img.width!==row.width||img.height!==row.height||rect.width!==row.width||rect.height!==row.height||img.currentSrc!==new URL(asset.path,location.href).href)throw Error('画像の寸法・URL が一致しない');
  }
  return {firstDecodeMs,decodeMs,images:elements.length,documentId:window.__documentId};
 },{images,type,color});
}
