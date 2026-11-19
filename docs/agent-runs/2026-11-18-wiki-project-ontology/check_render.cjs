// ローカル設計書だけを、独立した headless ブラウザで確認する。
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const root = path.resolve(__dirname, '../../..');
const { chromium } = require(path.join(root, 'tests/wiki/browse/node_modules/playwright'));
const source = path.join(root, 'docs/plans/wiki-project-ontology-2026-11-18.html');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const results = [];
  try {
    for (const [label, viewport] of [['desktop', {width: 1440, height: 1050}], ['mobile', {width: 412, height: 915}]]) {
      const context = await browser.newContext({viewport, locale: 'ja-JP', colorScheme: 'light'});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.goto(pathToFileURL(source).href);
      await page.screenshot({path: path.join(__dirname, `${label}-overview.png`)});
      const dimensions = await page.evaluate(() => ({
        viewport: innerWidth,
        pageWidth: document.documentElement.scrollWidth,
        tables: document.querySelectorAll('table').length,
        headingCount: document.querySelectorAll('h2').length,
        scripts: document.scripts.length,
      }));
      if (dimensions.pageWidth > dimensions.viewport || errors.length || dimensions.headingCount !== 11 || dimensions.scripts) {
        throw new Error(JSON.stringify({label, dimensions, errors}));
      }
      const anchor = page.locator('nav a').filter({hasText: '5. 関係の定義'});
      const expectedHash = await anchor.getAttribute('href');
      await anchor.click();
      await page.screenshot({path: path.join(__dirname, `${label}-relations.png`)});
      if (decodeURIComponent(new URL(page.url()).hash) !== decodeURIComponent(expectedHash)) throw new Error('目次から関係の定義へ移動できない');
      results.push({label, ...dimensions, navigation: 'passed', pageErrors: errors});
      if (label === 'desktop') await page.locator('figure.model').screenshot({path: path.join(__dirname, 'ontology-model.png')});
      await context.close();
    }
    fs.writeFileSync(path.join(__dirname, 'browser-verification.json'), JSON.stringify({date:'2026-11-18',browser:'Edge / Playwright 1.56.1',results}, null, 2)+'\n', 'utf8');
    console.log(JSON.stringify(results));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
