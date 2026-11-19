// 保存済みの Pele SVG と CSS の対照図を、フォントを固定して比較する。
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { pathToFileURL } = require('url');
const { Resvg } = require(path.join(process.env.TEMP, 'pele-png-tools/node_modules/@resvg/resvg-js'));
const { chromium, webkit } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright'));
const { PNG } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright-core/lib/utilsBundle'));
const out = process.env.PELE_COMPAT_OUT;
if (!out) throw Error('PELE_COMPAT_OUT に空の出力先を指定してください');
fs.mkdirSync(out, { recursive: true });
if (fs.readdirSync(out).length) throw Error('出力先は空にしてください');
const inputs = JSON.parse(fs.readFileSync(path.join(__dirname, 'inputs.json'), 'utf8'));
const fontFiles = ['C:/Windows/Fonts/NotoSansJP-Regular.otf', 'C:/Windows/Fonts/NotoSansJP-Bold.otf'];
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const fontCss = fontFiles.map((file, i) => '@font-face{font-family:ComparisonNoto;font-weight:' + (i ? 700 : 400) + ';src:url(data:font/otf;base64,' + fs.readFileSync(file).toString('base64') + ')}').join('') + 'svg,svg *{font-family:ComparisonNoto!important}';
const fixtures = [];
for (const item of inputs.cases.filter(x => x.rendered)) {
  for (const theme of ['light', 'dark']) fixtures.push({ id: item.id + '-' + theme, theme, svg: fs.readFileSync(path.join(__dirname, item.id + '-' + theme + '.svg'), 'utf8') });
}
const controls = {
  cascade: '<style>g{--shade:#c36;--curve:8px}.node{fill:var(--missing,var(--shade));rx:var(--curve);stroke:currentColor} .node{--shade:#3a7!important}</style><g color="#246"><rect class="node" x="10" y="10" width="170" height="70"/><text x="20" y="50">継承と上書き</text></g>',
  cycle: '<g style="--a:var(--b);--b:var(--a)"><rect x="10" y="10" width="170" height="70" style="fill:var(--a,#b73);rx:var(--a,12px)"/><text x="20" y="50">循環と代替値</text></g>',
  percent: '<rect x="10" y="10" width="170" height="70" style="--r:8%;rx:var(--r);ry:4px;fill:rgb(215,230,245);stroke:#123;stroke-width:2px"/><text x="20" y="50">百分率と複数指定</text>',
};
for (const [id, body] of Object.entries(controls)) fixtures.push({ id: 'control-' + id, theme: 'light', svg: '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="100" viewBox="0 0 240 100">' + body + '</svg>' });
fs.writeFileSync(path.join(out, 'control-inputs.json'), JSON.stringify(controls, null, 2));

// ブラウザが解決した各要素の描画値を属性に固定する。今回扱う要素に限定する。
async function inspect(page, svg) {
  await page.setContent('<!doctype html><meta charset="utf-8"><style>body{margin:0}' + fontCss + '</style>' + svg);
  await page.evaluate(async () => {
    await Promise.all([
      document.fonts.load('400 16px ComparisonNoto', '日本語ABC'),
      document.fonts.load('700 16px ComparisonNoto', '日本語ABC'),
    ]);
    await document.fonts.ready;
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  });
  return page.evaluate(() => {
    const root = document.querySelector('svg');
    const sourceElements = [root, ...root.querySelectorAll('*')];
    const clone = root.cloneNode(true);
    const targetElements = [clone, ...clone.querySelectorAll('*')];
    const rootRect = root.getBoundingClientRect();
    const labels = [];
    const paint = ['fill', 'stroke', 'color', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'stroke-dasharray', 'stroke-dashoffset', 'opacity', 'fill-opacity', 'stroke-opacity', 'font-size', 'font-weight', 'font-style', 'text-anchor', 'dominant-baseline', 'letter-spacing', 'word-spacing', 'visibility', 'display', 'stop-color', 'stop-opacity'];
    for (let i = 0; i < sourceElements.length; i++) {
      const source = sourceElements[i];
      const target = targetElements[i];
      const css = getComputedStyle(source);
      target.removeAttribute('style');
      for (const property of paint) target.setAttribute(property, css.getPropertyValue(property));
      target.setAttribute('font-family', 'Noto Sans JP');
      if (source.localName === 'rect') {
        for (const property of ['rx', 'ry']) {
          const value = css.getPropertyValue(property);
          if (value === 'auto') target.removeAttribute(property);
          else target.setAttribute(property, value);
        }
      }
      if (source.localName === 'text' && source.textContent.trim()) {
        const box = source.getBoundingClientRect();
        labels.push({ text: source.textContent, size: css.fontSize, weight: css.fontWeight,
          outsideViewport: box.left < rootRect.left - 1 || box.top < rootRect.top - 1 || box.right > rootRect.right + 1 || box.bottom > rootRect.bottom + 1,
          width: box.width, height: box.height });
      }
    }
    clone.querySelectorAll('style').forEach(el => el.remove());
    return { svg: new XMLSerializer().serializeToString(clone), labels, width: rootRect.width, height: rootRect.height };
  });
}

function difference(a, b) {
  const left = PNG.sync.read(a);
  const right = PNG.sync.read(b);
  if (left.width !== right.width || left.height !== right.height) return { dimensionMismatch: true };
  let changed = 0;
  let sum = 0;
  for (let i = 0; i < left.data.length; i += 4) {
    let max = 0;
    for (let c = 0; c < 3; c++) {
      const delta = Math.abs(left.data[i + c] - right.data[i + c]);
      max = Math.max(max, delta);
      sum += delta;
    }
    if (max > 16) changed++;
  }
  return { fractionOver16: changed / (left.width * left.height), meanChannelDifference: sum / (left.width * left.height * 3) };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1800, height: 1400 }, deviceScaleFactor: 1 });
  const prepared = [];
  for (const fixture of fixtures) {
    const info = await inspect(page, fixture.svg);
    if (info.width > 1700 || info.height > 2500) throw Error('画像が試験上限を超過');
    const background = fixture.theme === 'dark' ? '#1f1f1f' : '#ffffff';
    const images = [];
    for (const scale of [1, 2]) {
      const image = new Resvg(info.svg, { background, fitTo: { mode: 'zoom', value: scale }, font: { fontFiles, loadSystemFonts: false, defaultFontFamily: 'Noto Sans JP' } }).render().asPng();
      const name = fixture.id + '-' + scale + 'x.png';
      fs.writeFileSync(path.join(out, name), image);
      images.push({ scale, file: name, bytes: image.length, sha256: hash(image), width: image.readUInt32BE(16), height: image.readUInt32BE(20) });
    }
    fs.writeFileSync(path.join(out, fixture.id + '-original.svg'), fixture.svg);
    fs.writeFileSync(path.join(out, fixture.id + '-normalized.svg'), info.svg);
    prepared.push({ ...fixture, ...info, images, original: fixture.svg });
  }
  await browser.close();
  const observations = [];
  for (const [name, type] of [['chromium', chromium], ['webkit', webkit]]) {
    const current = await type.launch({ headless: true });
    const currentPage = await current.newPage({ viewport: { width: 1800, height: 1400 }, deviceScaleFactor: 1 });
    for (const fixture of prepared) {
      const bg = fixture.theme === 'dark' ? '#1f1f1f' : '#ffffff';
      const original = await inspect(currentPage, fixture.original);
      await currentPage.evaluate(color => document.body.style.background = color, bg);
      const before = await currentPage.locator('svg').screenshot();
      fs.writeFileSync(path.join(out, name + '-' + fixture.id + '-svg.png'), before);
      const normalized = await inspect(currentPage, fixture.svg);
      await currentPage.evaluate(color => document.body.style.background = color, bg);
      const after = await currentPage.locator('svg').screenshot();
      fs.writeFileSync(path.join(out, name + '-' + fixture.id + '-normalized.png'), after);
      const png = fs.readFileSync(path.join(out, fixture.id + '-1x.png'));
      observations.push({ browser: name, version: current.version(), id: fixture.id,
        labels: original.labels, normalizedLabels: normalized.labels,
        normalization: difference(before, after), png1x: difference(before, png) });
      console.log(name, fixture.id);
    }
    await current.close();
  }
  const result = { fonts: fontFiles.map(file => ({ file, sha256: hash(fs.readFileSync(file)) })),
    prepared: prepared.map(({ original, svg, ...rest }) => rest), observations };
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(result, null, 2));
})().catch(error => { console.error(error); process.exit(1); });
