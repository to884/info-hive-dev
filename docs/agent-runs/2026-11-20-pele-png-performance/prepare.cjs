// 製品の Pele SVG から、前回検証した方法で比較用の SVG と PNG を作る。
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require(path.join(process.cwd(),'tests/wiki/browse/node_modules/playwright'));
const { Resvg } = require(path.join(process.env.TEMP,'pele-png-tools/node_modules/@resvg/resvg-js'));
const resvgVersion = require(path.join(process.env.TEMP,'pele-png-tools/node_modules/@resvg/resvg-js/package.json')).version;
if (resvgVersion !== '2.6.2') throw Error('resvg-js 2.6.2 を指定してください');
const directory = __dirname;
const inputFixture = path.join(directory,'fixture');
const fixture = path.resolve(process.env.PELE_PERF_FIXTURE || inputFixture);
if (fs.existsSync(path.join(fixture,'manifest.json'))) throw Error('生成済みの試料を上書きしないよう、PELE_PERF_FIXTURE に新しい出力先を指定してください');
for (const theme of ['light','dark']) fs.mkdirSync(path.join(fixture,theme),{recursive:true});
const fontFiles = ['C:/Windows/Fonts/NotoSansJP-Regular.otf','C:/Windows/Fonts/NotoSansJP-Bold.otf'];
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const css = fontFiles.map((file,index)=>'@font-face{font-family:ComparisonNoto;font-weight:'+(index?700:400)+';src:url(data:font/otf;base64,'+fs.readFileSync(file).toString('base64')+')}').join('')+'svg,svg *{font-family:ComparisonNoto!important}body{margin:0}';
(async()=>{
 const browser = await chromium.launch({headless:true});
 const page = await browser.newPage({viewport:{width:1200,height:900}});
 const manifest = {format:2,count:50,sourceSha256:hash(fs.readFileSync(path.join(directory,'sources.json'))),fonts:fontFiles.map(file=>({file,sha256:hash(fs.readFileSync(file))})),images:{light:[],dark:[]}};
 const nativeBinary = require.resolve('@resvg/resvg-js-win32-x64-msvc',{paths:[path.join(process.env.TEMP,'pele-png-tools')]});
 manifest.preparation = {
  resvgVersion, nativeSha256:hash(fs.readFileSync(nativeBinary)),
  chromiumVersion:browser.version(), prepareScriptSha256:hash(fs.readFileSync(__filename)),
  pluginCommit:require('node:child_process').execFileSync('git',['-C','info-hive-wiki','rev-parse','HEAD'],{encoding:'utf8'}).trim(),
 };
 const properties = ['fill','stroke','color','stroke-width','stroke-linecap','stroke-linejoin','stroke-miterlimit','stroke-dasharray','stroke-dashoffset','opacity','fill-opacity','stroke-opacity','font-size','font-weight','font-style','text-anchor','dominant-baseline','letter-spacing','word-spacing','visibility','display','stop-color','stop-opacity'];
 for(const theme of ['light','dark']) for(let index=0;index<50;index++) {
  const original = fs.readFileSync(path.join(inputFixture,theme,index+'-pele.svg'));
  await page.setContent('<!doctype html><style>'+css+'</style>'+original.toString('utf8'));
  await page.evaluate(async()=>{
   await Promise.all([document.fonts.load('400 16px ComparisonNoto','日本語ABC'),document.fonts.load('700 16px ComparisonNoto','日本語ABC')]);
   await document.fonts.ready;
  });
  const normalized = await page.evaluate(({properties,theme})=>{
   const root=document.querySelector('svg');const clone=root.cloneNode(true);
   const before=[root,...root.querySelectorAll('*')],after=[clone,...clone.querySelectorAll('*')];
   for(let i=0;i<before.length;i++) {
    const css=getComputedStyle(before[i]),target=after[i];target.removeAttribute('style');
    for(const name of properties) target.setAttribute(name,css.getPropertyValue(name));
    target.setAttribute('font-family','Noto Sans JP');
    if(target.localName==='rect') for(const name of ['rx','ry']) {
     const value=css.getPropertyValue(name);if(value==='auto')target.removeAttribute(name);else target.setAttribute(name,value);
    }
   }
   clone.querySelectorAll('style').forEach(el=>el.remove());
   const background=document.createElementNS('http://www.w3.org/2000/svg','rect');
   background.setAttribute('width',root.width.baseVal.value);background.setAttribute('height',root.height.baseVal.value);background.setAttribute('fill',theme==='light'?'#ffffff':'#1f1f1f');
   clone.prepend(background);
   return {svg:new XMLSerializer().serializeToString(clone),width:root.width.baseVal.value,height:root.height.baseVal.value};
  },{properties,theme});
  const row={index,width:normalized.width,height:normalized.height};
  const files={pele:original,normalized:Buffer.from(normalized.svg)};
  for(const scale of [1,2])files['png'+scale+'x']=new Resvg(normalized.svg,{fitTo:{mode:'zoom',value:scale},font:{fontFiles,loadSystemFonts:false,defaultFontFamily:'Noto Sans JP'}}).render().asPng();
  for(const [key,data] of Object.entries(files)) {
   const relative=theme+'/'+index+'-'+key+(key.startsWith('png')?'.png':'.svg');fs.writeFileSync(path.join(fixture,relative),data);
   row[key]={path:relative,bytes:data.length,sha256:hash(data),width:key==='png2x'?normalized.width*2:normalized.width,height:key==='png2x'?normalized.height*2:normalized.height};
  }
  manifest.images[theme].push(row);
 }
 await browser.close();
 fs.writeFileSync(path.join(fixture,'manifest.json'),JSON.stringify(manifest,null,2));
 fs.writeFileSync(path.join(fixture,'images.css'),'body{margin:24px;background:#fff}html[data-theme="dark"] body{background:#1f1f1f}.fig-img{display:block}');
 fs.writeFileSync(path.join(fixture,'page.html'),'<!doctype html><html lang="ja"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\'; style-src \'self\'"><title>Pele 画像比較</title><link rel="stylesheet" href="images.css"><main></main>');
 console.log('50 原稿の明暗各 4 方式を生成');
})().catch(error=>{console.error(error);process.exit(1);});
