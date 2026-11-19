// 文字枠の警告を実際の描画画素で確認し、別ノードへの侵入も調べる。
const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright'));
const { PNG } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright-core/lib/utilsBundle'));
const { Resvg } = require(path.join(process.env.TEMP, 'pele-png-tools/node_modules/@resvg/resvg-js'));
const directory = path.resolve(process.env.PELE_LABEL_RUN || 'docs/agent-runs/2026-11-20-pele-label-validation');
const source = path.resolve('docs/agent-runs/2026-11-19-pele-png-compatibility/results');
const audit = JSON.parse(fs.readFileSync(path.join(directory, 'results/results.json'), 'utf8'));
const corpus = JSON.parse(fs.readFileSync(path.join(source, 'results.json'), 'utf8'));
const results = [];
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1800, height: 1500 } });
  for (const observation of audit.observations.filter(x => x.browser === 'chromium')) {
    const svg = fs.readFileSync(path.join(source, observation.id + '-normalized.svg'), 'utf8');
    await page.setContent('<style>body{margin:0}</style>' + svg);
    const shapeMasks = await page.evaluate(labels => {
      const root = document.querySelector('svg');
      const texts = [...root.querySelectorAll('text')].filter(x => x.textContent.trim());
      const viewport = root.getBoundingClientRect();
      const nodes = [...root.querySelectorAll('.pele-node,.pele-task,.pele-note,.pele-participant')];
      const closedShapes = node => [...node.children].filter(x => ['rect', 'circle', 'ellipse', 'polygon'].includes(x.localName));
      const masks = [];
      const foreignNodes = [];
      for (const label of labels) {
        const text = texts[label.index];
        const owner = text.closest('.pele-node,.pele-task,.pele-note,.pele-participant,.pele-edge-label,.pele-frame');
        if (label.envelopeOutsideShape) {
          const shape = closedShapes(owner).sort((a,b) => b.getBoundingClientRect().width*b.getBoundingClientRect().height-a.getBoundingClientRect().width*a.getBoundingClientRect().height)[0];
          const copy = shape.cloneNode(true);
          const m = shape.getCTM();
          copy.setAttribute('transform', 'matrix(' + [m.a,m.b,m.c,m.d,m.e,m.f].join(' ') + ')');
          copy.setAttribute('fill', '#ffffff');
          copy.setAttribute('fill-opacity', '1');
          copy.setAttribute('stroke', 'none');
          copy.setAttribute('opacity', '1');
          masks.push({ index: label.index, svg: '<svg xmlns="http://www.w3.org/2000/svg" width="' + root.width.baseVal.value + '" height="' + root.height.baseVal.value + '">' + new XMLSerializer().serializeToString(copy) + '</svg>' });
        }
        for (const node of nodes) {
          if (node.contains(text)) continue;
          for (const shape of closedShapes(node)) {
            const inv = shape.getScreenCTM().inverse();
            const hits = label.chars.filter(c => c.char && !/\s/.test(c.char)).filter(c => {
              return [0,0.5,1].some(dx => [0,0.5,1].some(dy => {
                const point = new DOMPoint(viewport.x+c.x+c.width*dx,viewport.y+c.y+c.height*dy).matrixTransform(inv);
                return shape.isPointInFill(point);
              }));
            });
            if (hits.length) foreignNodes.push({ index: label.index, nodeClass: node.getAttribute('class'), chars: hits.map(c => c.char).join('') });
          }
        }
      }
      return { masks, foreignNodes };
    }, observation.labels);
    const full = PNG.sync.read(fs.readFileSync(path.join(source, observation.id + '-2x.png')));
    const empty = PNG.sync.read(fs.readFileSync(path.join(directory, 'results', observation.id + '-textless-2x.png')));
    const warnings = [];
    for (const mask of shapeMasks.masks) {
      const image = PNG.sync.read(new Resvg(mask.svg, { background: '#000000', fitTo: { mode: 'zoom', value: 2 } }).render().asPng());
      const label = observation.labels[mask.index];
      const b = label.bounds;
      let total = 0, outside = 0;
      for (let y = Math.max(0,Math.floor(b.y*2)); y < Math.min(full.height,Math.ceil((b.y+b.height)*2)); y++) {
        for (let x = Math.max(0,Math.floor(b.x*2)); x < Math.min(full.width,Math.ceil((b.x+b.width)*2)); x++) {
          const offset = (y*full.width+x)*4;
          if (![0,1,2].some(c => Math.abs(full.data[offset+c]-empty.data[offset+c])>16)) continue;
          total++;
          let inside = false;
          for (let dy=-2;dy<=2;dy++) for (let dx=-2;dx<=2;dx++) {
            const nx=x+dx,ny=y+dy;
            if (nx>=0 && ny>=0 && nx<image.width && ny<image.height && image.data[(ny*image.width+nx)*4]>127) inside=true;
          }
          if (!inside) outside++;
        }
      }
      warnings.push({ index: label.index, text: label.text, ownerClass: label.ownerClass, contributionPixels: total, outsidePixels: outside });
    }
    results.push({ id: observation.id, warnings, foreignNodes: shapeMasks.foreignNodes });
  }
  await browser.close();
  fs.writeFileSync(path.join(directory, 'results/refinement.json'), JSON.stringify(results,null,2));
  console.log(JSON.stringify({ outside: results.flatMap(x=>x.warnings.filter(w=>w.outsidePixels).map(w=>({id:x.id,...w}))), foreign:results.flatMap(x=>x.foreignNodes.map(w=>({id:x.id,...w}))) }));
})().catch(error=>{console.error(error);process.exit(1);});
