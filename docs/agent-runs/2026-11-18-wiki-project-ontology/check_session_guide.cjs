const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'../../..');
const file=path.join(root,'docs/plans/wiki-ontology-session-guide-2026-11-18.html');
const {chromium}=require(path.join(root,'tests/wiki/browse/node_modules/playwright'));
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const results=[];
 try{
  for(const [name,width] of [['desktop',1440],['mobile',412]]){
   const page=await browser.newPage({viewport:{width,height:1000}});
   await page.goto(pathToFileURL(file).href);
   const report=await page.evaluate(()=>({width:innerWidth,pageWidth:document.documentElement.scrollWidth,links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href'))}));
   if(report.width!==report.pageWidth)throw Error(JSON.stringify({name,...report,overflow:await page.evaluate(()=>[...document.querySelectorAll('main *')].filter(e=>e.getBoundingClientRect().right>innerWidth).map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right})).slice(0,12))}));
   for(const link of report.links)if(!fs.existsSync(path.resolve(path.dirname(file),decodeURIComponent(link))))throw Error('参照先がない: '+link);
   await page.screenshot({path:path.join(__dirname,'session-guide-'+name+'.png')});
   results.push({name,...report});
   await page.close();
  }
 }finally{await browser.close();}
 fs.writeFileSync(path.join(__dirname,'session-guide-verification.json'),JSON.stringify(results,null,2)+'\n','utf8');
 console.log('PC・モバイルの横幅と全リンクを確認');
})().catch(e=>{console.error(e);process.exitCode=1});
