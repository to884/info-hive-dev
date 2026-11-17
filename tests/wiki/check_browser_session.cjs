'use strict';
// 公式拡張へ接続せず、既存タブの選別と切断だけを検査する。
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const session = require('../../info-hive-wiki/skills/info-hive/scripts/wiki_browser_session.cjs');
const request = { url: 'https://example.com/article', channel: 'msedge', timeout: 2,
  max_bytes: 10000, max_images: 0 };
let evaluated = 0;
function page(url = request.url, moved = false) {
  let reads = 0;
  return {
    url() { reads++; return moved && reads > 2 ? 'https://other.example/' : url; },
    async waitForLoadState(state) { assert.equal(state, 'domcontentloaded'); },
    async content() { evaluated++; return '<main>認証済みの本文</main>'; },
    async evaluate() { throw Error('画像がないときにページの JavaScript を実行してはいけない'); },
    goto() { throw Error('ページを移動してはいけない'); },
    close() { throw Error('ユーザーのタブを閉じてはいけない'); }
  };
}
function browser(pages) {
  return { contexts: () => [{ pages: () => pages,
    close() { throw Error('ユーザーの context を閉じてはいけない'); } }],
    async unbind() { this.unbound = true; }, async close() { this.disconnected = true; } };
}
(async () => {
  const other = page('https://other.example/');
  other.content = () => { throw Error('無関係なタブを読んではいけない'); };
  const result = await session.readPage(browser([other, page()]), request);
  assert.match(result.html, /認証済み/);
  assert.equal(evaluated, 1);
  for (const alias of ['https://EXAMPLE.com:443/article', 'https://example.com/a/../article']) {
    const normalized = await session.readPage(browser([page()]), { ...request, url: alias });
    assert.equal(normalized.final_url, request.url);
    assert.equal(normalized.request_url, alias);
    assert.equal(normalized.matched_url, request.url);
  }
  await assert.rejects(session.readPage(browser([other]), request), /1 つだけ/);
  await assert.rejects(session.readPage(browser([page(), page()]), request), /1 つだけ/);
  await assert.rejects(session.readPage(browser([page(request.url, true)]), request), /URL が変わった/);
  await assert.rejects(session.readPage(browser([page()]), { ...request, max_bytes: 1 }), /上限/);
  const attached = browser([page()]);
  const tools = { async createBrowserWithInfo(config, info, options) {
    assert.equal(config.extension, true);
    assert.equal(config.browser.launchOptions.channel, 'msedge');
    assert.equal(options.extension, true);
    return { browser: attached, ownership: 'attached' };
  } };
  await session.connectAndRead(request, tools);
  assert.equal(attached.unbound, true);
  assert.equal(attached.disconnected, true);
  const failed = browser([]);
  await assert.rejects(session.connectAndRead(request, { createBrowserWithInfo: async () =>
    ({ browser: failed, ownership: 'attached' }) }), /1 つだけ/);
  assert.equal(failed.unbound, true);
  assert.equal(failed.disconnected, true);
  const script = `require(${JSON.stringify(require.resolve('../../info-hive-wiki/skills/info-hive/scripts/wiki_browser_session.cjs'))}).writeResult({html:'x'.repeat(2 * 1024 * 1024)}).then(()=>process.exit(0))`;
  const large = spawnSync(process.execPath, ['-e', script], { encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
  assert.equal(large.status, 0);
  assert.equal(JSON.parse(large.stdout).html.length, 2 * 1024 * 1024);
  console.log('既存タブの読み取り・切断・大きい出力の 10 ケースに成功した');
})().catch(error => { console.error(error); process.exit(1); });
