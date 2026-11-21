import asyncio,json,re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse,unquote
from playwright.async_api import async_playwright
FILE=Path('C:/Works/info-hive-dev/docs/research/info-hive-mykg-architecture-visual-2026-11-20.html')
OUT=Path(__file__).parent
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='a':self.links.append(attrs.get('href',''))
async def main():
    parser=Parser();parser.feed(FILE.read_text(encoding='utf-8'))
    assert all(count==1 for count in Counter(parser.ids).values())
    for link in parser.links:
        if link.startswith('#'):assert link[1:] in parser.ids
        elif not urlparse(link).scheme:assert (FILE.parent/unquote(link)).resolve().is_file(),link
    results=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
        for width,scheme in [(1440,'light'),(375,'light'),(360,'light'),(1024,'light'),(1440,'dark')]:
            page=await browser.new_page(viewport={'width':width,'height':1000},color_scheme=scheme)
            errors=[];external=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None)
            await page.goto(FILE.as_uri())
            assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'body overflow {width}'
            if width in (1440,375):await page.screenshot(path=str(OUT/f'view-{width}-{scheme}.png'),full_page=True)
            for layer in ['raw','write','read','all']:
                button=page.locator(f'button[data-view="{layer}"]');await button.click()
                assert await button.get_attribute('aria-pressed')=='true'
            for mode in ['publication','live']:
                button=page.locator(f'[data-mode="{mode}"]');await button.focus();await page.keyboard.press('Enter')
                assert await button.get_attribute('aria-pressed')=='true'
                expected='語彙検索（BM25）' if mode=='publication' else 'ハイブリッド検索'
                assert await page.locator('#mode-search').inner_text()==expected
                if width==1440 and scheme=='light':await page.locator('.read-map').screenshot(path=str(OUT/f'mode-{mode}.png'))
            for value in ['resume','orphan','vocabulary']:
                button=page.locator(f'[data-proposal="{value}"]');await button.click()
                assert await page.locator('.proposal:visible').count()==1
                assert await page.locator(f'#proposal-{value}').is_visible()
                assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'proposal overflow {width}'
                if width in (1440,375) and scheme=='light':await page.locator(f'#proposal-{value}').screenshot(path=str(OUT/f'proposal-{value}-{width}.png'))
            for detail in await page.locator('details').all():
                await detail.locator('summary').click();assert await detail.get_attribute('open') is not None
            assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'expanded overflow {width}'
            if width<650:
                await page.locator('.table-wrap').first.focus();await page.keyboard.press('ArrowRight');await page.wait_for_timeout(150)
                assert await page.locator('.table-wrap').first.evaluate('e=>e.scrollLeft>0')
            await page.locator('#theme').click()
            assert await page.locator('html').get_attribute('data-theme')==('dark' if scheme=='light' else 'light')
            if width==1440 and scheme=='light':
                await page.locator('#theme').click()
                for selector,name in [('#architecture','overview'),('.compare-frame','comparison'),('.current-facts','reassessment')]:await page.locator(selector).screenshot(path=str(OUT/f'{name}.png'))
            if scheme=='dark':
                await page.locator('#theme').click();await page.emulate_media(media='print')
                assert await page.locator('body').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(255, 255, 255)'
                assert await page.locator('.proposal:visible').count()==3
            assert not errors,errors
            assert not external,external
            results.append({'width':width,'scheme':scheme,'overflow':False,'controls':'pass','consoleErrors':errors,'externalRequests':external})
            await page.close()
        await browser.close()
    (OUT/'verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False))
asyncio.run(main())
