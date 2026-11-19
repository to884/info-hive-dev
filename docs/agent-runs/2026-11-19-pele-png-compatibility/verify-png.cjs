// 生成済みの PNG を同じ CSS 寸法で表示し、2 倍画像の縮小表示も記録する。
const fs = require('fs');
const path = require('path');
const { chromium, webkit } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright'));
const { PNG } = require(path.join(process.cwd(), 'tests/wiki/browse/node_modules/playwright-core/lib/utilsBundle'));
const dir = process.env.PELE_COMPAT_OUT;
if (!dir) throw Error('PELE_COMPAT_OUT を指定してください');
const result = JSON.parse(fs.readFileSync(path.join(dir, 'results.json'), 'utf8'));
(async () => {
  const checks = [];
  for (const [name, type] of [['chromium', chromium], ['webkit', webkit]]) {
    const browser = await type.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1800, height: 1400 }, deviceScaleFactor: 1 });
    for (const item of result.prepared) {
      const images = item.images.map(image => {
        const src = 'data:image/png;base64,' + fs.readFileSync(path.join(dir, image.file)).toString('base64');
        return '<img width="' + item.width + '" height="' + item.height + '" src="' + src + '">';
      }).join('');
      const bg = item.theme === 'dark' ? '#1f1f1f' : '#ffffff';
      await page.setContent('<style>body{margin:0;background:' + bg + '}img{display:block}</style>' + images);
      const decoded = await page.locator('img').evaluateAll(imgs => Promise.all(imgs.map(async img => {
        await img.decode();
        return { width: img.naturalWidth, height: img.naturalHeight };
      })));
      const screenshot = await page.locator('img').nth(1).screenshot();
      fs.writeFileSync(path.join(dir, name + '-' + item.id + '-png2x-downsampled.png'), screenshot);
      const original = PNG.sync.read(fs.readFileSync(path.join(dir, name + '-' + item.id + '-svg.png')));
      const scaled = PNG.sync.read(screenshot);
      if (original.width !== scaled.width || original.height !== scaled.height) throw Error('比較寸法が不一致');
      let changed = 0;
      for (let i = 0; i < original.data.length; i += 4) {
        if ([0, 1, 2].some(c => Math.abs(original.data[i + c] - scaled.data[i + c]) > 16)) changed++;
      }
      checks.push({ browser: name, id: item.id, decoded, png2xFractionOver16: changed / (original.width * original.height) });
    }
    await browser.close();
  }
  fs.writeFileSync(path.join(dir, 'png-browser-checks.json'), JSON.stringify(checks, null, 2));
  console.log('PNG のブラウザ表示を確認 ' + checks.length + ' 条件');
})().catch(error => { console.error(error); process.exit(1); });
