const fs=require("fs");
const path=require("path");
const crypto=require("crypto");
const {Resvg}=require(path.join(process.env.TEMP,"pele-png-tools/node_modules/@resvg/resvg-js"));
const {chromium,webkit}=require(path.join(process.cwd(),"tests/wiki/browse/node_modules/playwright"));
const {pathToFileURL}=require("url");
const sourceDir=__dirname;
const out=process.env.PELE_COMPARE_OUT;
if (!out) throw new Error("PELE_COMPARE_OUT に空の出力ディレクトリを指定してください");
fs.mkdirSync(out,{recursive:true});
if (fs.readdirSync(out).length) throw new Error("出力ディレクトリは空にしてください");
const mode=process.env.PELE_COMPARE_MODE || "resolved";
if (!["raw","resolved"].includes(mode)) throw new Error("PELE_COMPARE_MODE は raw または resolved を指定してください");
const inputs=JSON.parse(fs.readFileSync(path.join(sourceDir,"inputs.json"),"utf8"));
for (const item of inputs) for (const theme of ["light","dark"]) {
  const name=`${item.id}-${theme}.svg`;
  fs.copyFileSync(path.join(sourceDir,name),path.join(out,name));
}
const manifest=[];
for(const item of inputs) for(const theme of ["light","dark"]) {
  const source=fs.readFileSync(path.join(out,`${item.id}-${theme}.svg`),"utf8");
  const style=source.match(/ style="([^"]*)"/)[1].replaceAll("&quot;", "'");
  const vars={};
  for(const declaration of style.split(";")) {
    const m=declaration.match(/^\s*(--[\w-]+):(.+)$/);
    if(m) vars[m[1]]=m[2];
  }
  function resolve(text) {
    for(let n=0;n<8 && /var\(/.test(text);n++) {
      text=text.replace(/var\((--[\w-]+)(?:,([^()]*))?\)/g,(_,key,fallback)=>vars[key] ?? fallback ?? "");
    }
    return text;
  }
  const svg=Buffer.from(mode === "raw" ? source : resolve(source));
  const base=new Resvg(svg,{font:{fontFiles:["C:/Windows/Fonts/YuGothR.ttc"],loadSystemFonts:false,defaultFontFamily:"Yu Gothic"}});
  for(const scale of [1,2]) {
    const render=new Resvg(svg,{fitTo:{mode:"zoom",value:scale},font:{fontFiles:["C:/Windows/Fonts/YuGothR.ttc"],loadSystemFonts:false,defaultFontFamily:"Yu Gothic"}});
    const png=render.render().asPng();
    const name=`${item.id}-${theme}-${scale}x.png`;
    fs.writeFileSync(path.join(out,name),png);
    manifest.push({id:item.id,theme,scale,svgWidth:base.width,svgHeight:base.height,pngWidth:png.readUInt32BE(16),pngHeight:png.readUInt32BE(20),bytes:png.length,sha256:crypto.createHash("sha256").update(png).digest("hex")});
  }
}
fs.writeFileSync(path.join(out,"manifest.json"),JSON.stringify(manifest,null,2));
(async()=>{
const results=[];
for(const [browserName,browserType] of [["chromium",chromium],["webkit",webkit]]) {
 const browser=await browserType.launch({headless:true});
 for(const theme of ["light","dark"]) for(const item of inputs) {
  const bg=theme==="light"?"#fff":"#1f1f1f";
  const html=`<!doctype html><meta charset="utf-8"><style>body{margin:0;background:${bg};color:${theme==="light"?"#111":"#fff"};font:16px "Yu Gothic"} section{margin:12px} img{width:min(100%,334px);height:auto} h2{margin:0;font-size:14px}</style>`+["svg","1x.png","2x.png"].map((suffix,i)=>`<section><h2>${["SVG","PNG 1x","PNG 2x"][i]}</h2><img src="${item.id}-${theme}${suffix === "svg" ? ".svg" : "-" + suffix}"></section>`).join("");
  const file=path.join(out,`view-${item.id}-${theme}.html`);fs.writeFileSync(file,html);
  const page=await browser.newPage({viewport:{width:390,height:900},deviceScaleFactor:1});
  const errors=[];page.on("pageerror",e=>errors.push(e.message));
  await page.goto(pathToFileURL(file).href);await page.locator("img").evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode())));
  const details=await page.locator("img").evaluateAll(imgs=>imgs.map(i=>({complete:i.complete,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,width:i.getBoundingClientRect().width,height:i.getBoundingClientRect().height})));
  if(details.some(i=>!i.naturalWidth)) throw Error("image failed");
  await page.screenshot({path:path.join(out,`${browserName}-${item.id}-${theme}.png`),fullPage:true});
  await page.setViewportSize({width:720,height:900});
  await page.locator("img").evaluateAll(imgs=>imgs.forEach(i=>i.style.width="668px"));
  await page.screenshot({path:path.join(out,`${browserName}-${item.id}-${theme}-zoom.png`),fullPage:true});
  results.push({browser:browserName,version:browser.version(),id:item.id,theme,details,errors});
  await page.close();
 }
 await browser.close();
}
fs.writeFileSync(path.join(out,"results.json"),JSON.stringify(results,null,2));
console.log(JSON.stringify({cases:results.length,errors:results.flatMap(x=>x.errors)}));
})().catch(e=>{console.error(e);process.exit(1)});
