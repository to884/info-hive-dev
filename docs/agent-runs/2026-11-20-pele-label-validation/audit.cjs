// 保存した SVG と PNG のラベルを、位置と描画の寄与から検査する。
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium, webkit } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright'));
const { PNG } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright-core/lib/utilsBundle'));
const { Resvg } = require(path.join(process.env.TEMP, 'pele-png-tools/node_modules/@resvg/resvg-js'));
const source = path.resolve(process.env.PELE_LABEL_FIXTURE || 'docs/agent-runs/2026-11-19-pele-png-compatibility/results');
const out = process.env.PELE_LABEL_OUT;
if (!out) throw Error('PELE_LABEL_OUT に空の出力先を指定してください');
fs.mkdirSync(out, { recursive: true });
if (fs.readdirSync(out).length) throw Error('出力先は空にしてください');
const corpus = JSON.parse(fs.readFileSync(path.join(source, 'results.json'), 'utf8'));
const fonts = corpus.fonts.map(x => x.file);
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
for (const font of corpus.fonts) {
  if (hash(fs.readFileSync(font.file)) !== font.sha256) throw Error('フォントが変わった');
}
const fontCss = fonts.map((file, i) => '@font-face{font-family:ComparisonNoto;font-weight:' + (i ? 700 : 400) + ';src:url(data:font/otf;base64,' + fs.readFileSync(file).toString('base64') + ')}').join('') + 'svg,svg *{font-family:ComparisonNoto!important}';

function contribution(full, empty, bounds, scale) {
  const left = Math.max(0, Math.floor((bounds.x - 1) * scale));
  const top = Math.max(0, Math.floor((bounds.y - 1) * scale));
  const right = Math.min(full.width, Math.ceil((bounds.x + bounds.width + 1) * scale));
  const bottom = Math.min(full.height, Math.ceil((bounds.y + bounds.height + 1) * scale));
  let count = 0;
  for (let y = top; y < bottom; y++) for (let x = left; x < right; x++) {
    const offset = (y * full.width + x) * 4;
    if ([0, 1, 2].some(c => Math.abs(full.data[offset + c] - empty.data[offset + c]) > 16)) count++;
  }
  return count;
}

(async () => {
  const observations = [];
  const rendering = [];
  for (const [browserName, type] of [['chromium', chromium], ['webkit', webkit]]) {
    const browser = await type.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1800, height: 1500 }, deviceScaleFactor: 1 });
    for (const item of corpus.prepared) {
      const svg = fs.readFileSync(path.join(source, item.id + '-normalized.svg'), 'utf8');
      const background = item.theme === 'dark' ? '#1f1f1f' : '#ffffff';
      await page.setContent('<meta charset="utf-8"><style>body{margin:0;background:' + background + '}' + fontCss + '</style>' + svg);
      await page.evaluate(async () => {
        await Promise.all([document.fonts.load('400 16px ComparisonNoto', '日本語ABC'), document.fonts.load('700 16px ComparisonNoto', '日本語ABC')]);
        await document.fonts.ready;
      });
      const geometry = await page.evaluate(() => {
        const root = document.querySelector('svg');
        const viewport = root.getBoundingClientRect();
        const texts = [...root.querySelectorAll('text')].filter(x => x.textContent.trim());
        const boxOf = element => {
          const b = element.getBoundingClientRect();
          return { x: b.x - viewport.x, y: b.y - viewport.y, width: b.width, height: b.height };
        };
        const contains = (shape, point) => {
          const local = new DOMPoint(point.x + viewport.x, point.y + viewport.y).matrixTransform(shape.getScreenCTM().inverse());
          return shape.isPointInFill(local);
        };
        const nodeSelector = '.pele-node,.pele-task,.pele-note,.pele-participant';
        const labels = texts.map((text, labelIndex) => {
          const owner = text.closest(nodeSelector + ',.pele-edge-label,.pele-frame');
          const shapes = owner ? [...owner.children].filter(x => ['rect', 'polygon', 'circle', 'ellipse'].includes(x.localName)) : [];
          const shape = shapes.sort((a, b) => b.getBoundingClientRect().width * b.getBoundingClientRect().height - a.getBoundingClientRect().width * a.getBoundingClientRect().height)[0];
          const bounds = boxOf(text);
          const chars = [];
          const content = text.textContent;
          for (let index = 0; index < text.getNumberOfChars(); index++) {
            const b = text.getExtentOfChar(index);
            const matrix = text.getScreenCTM();
            const points = [[b.x,b.y],[b.x+b.width,b.y],[b.x+b.width,b.y+b.height],[b.x,b.y+b.height]].map(([x,y]) => new DOMPoint(x,y).matrixTransform(matrix));
            const x = Math.min(...points.map(p => p.x)) - viewport.x;
            const y = Math.min(...points.map(p => p.y)) - viewport.y;
            const width = Math.max(...points.map(p => p.x)) - viewport.x - x;
            const height = Math.max(...points.map(p => p.y)) - viewport.y - y;
            chars.push({ index, char: content[index], x, y, width, height });
          }
          const corners = [{x:bounds.x,y:bounds.y},{x:bounds.x+bounds.width,y:bounds.y},{x:bounds.x+bounds.width,y:bounds.y+bounds.height},{x:bounds.x,y:bounds.y+bounds.height}];
          return { index: labelIndex, text: content, bounds, chars,
            charCountMatches: content.length === chars.length,
            ownerClass: owner?.getAttribute('class') || null,
            shape: shape ? { tag: shape.localName, bounds: boxOf(shape) } : null,
            envelopeOutsideShape: shape ? corners.some(p => !contains(shape, p)) : null };
        });
        const overlaps = [];
        for (let i = 0; i < labels.length; i++) for (let j = i + 1; j < labels.length; j++) {
          const a = labels[i].bounds, b = labels[j].bounds;
          if (Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x) <= 1 || Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y) <= 1) continue;
          let count = 0;
          for (const ca of labels[i].chars.filter(c => c.char && !/\s/.test(c.char))) for (const cb of labels[j].chars.filter(c => c.char && !/\s/.test(c.char))) {
            if (Math.min(ca.x+ca.width,cb.x+cb.width)-Math.max(ca.x,cb.x)>1 && Math.min(ca.y+ca.height,cb.y+cb.height)-Math.max(ca.y,cb.y)>1) count++;
          }
          if (count) overlaps.push({ first: i, second: j, intersectingCharBoxes: count });
        }
        const textless = root.cloneNode(true);
        textless.querySelectorAll('text').forEach(x => x.remove());
        return { labels, overlaps, textless: new XMLSerializer().serializeToString(textless) };
      });
      if (browserName === 'chromium') {
        for (const scale of [1, 2]) {
          const image = item.images.find(x => x.scale === scale);
          const saved = fs.readFileSync(path.join(source, image.file));
          if (hash(saved) !== image.sha256) throw Error('入力画像のハッシュが不一致');
          const options = { background, fitTo: { mode: 'zoom', value: scale }, font: { fontFiles: fonts, loadSystemFonts: false, defaultFontFamily: 'Noto Sans JP' } };
          const reproduced = new Resvg(svg, options).render().asPng();
          if (hash(reproduced) !== image.sha256) throw Error('PNG の再生成が不一致');
          const emptyPng = new Resvg(geometry.textless, options).render().asPng();
          fs.writeFileSync(path.join(out, item.id + '-textless-' + scale + 'x.png'), emptyPng);
          const full = PNG.sync.read(saved), empty = PNG.sync.read(emptyPng);
          rendering.push({ id: item.id, scale, inputSha256: image.sha256, labelContributions: geometry.labels.map(label => ({ index: label.index, text: label.text, pixels: contribution(full, empty, label.bounds, scale), chars: label.chars.filter(c => c.char && !/\s/.test(c.char)).map(c => ({ index: c.index, char: c.char, pixels: contribution(full, empty, c, scale) })) })) });
        }
      }
      fs.writeFileSync(path.join(out, browserName + '-' + item.id + '.png'), await page.locator('svg').screenshot());
      observations.push({ browser: browserName, version: browser.version(), id: item.id, labels: geometry.labels, overlaps: geometry.overlaps });
      console.log(browserName + ' ' + item.id);
    }
    await browser.close();
  }
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ observations, rendering }, null, 2));
})().catch(error => { console.error(error); process.exit(1); });
