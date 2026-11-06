import { createRequire } from 'node:module';
import fs from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('../frontend/node_modules/playwright-core');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const out = 'BEFORE_AFTER_SCREENSHOTS';
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ executablePath: EDGE, headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
await page.bringToFront();
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
const t0 = Date.now();
await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle', timeout: 120000 });
await page.waitForFunction(() => typeof window.__PV_VIEW === 'function', null, { timeout: 60000 });
await page.waitForTimeout(7000);
const loadedMs = Date.now() - t0;

await page.screenshot({ path: `${out}/after_front.png` });
for (const [name, position, target] of [
  ['interior', [260, -540, 350], [0, 0, 225]],
  ['toolhead', [205, -330, 310], [0, 0, 158]],
  ['top', [0, -520, 1030], [0, 0, 220]],
  ['z', [520, -520, 260], [0, 0, 130]],
  ['bed', [240, -380, 220], [0, 0, 80]],
]) {
  if (name === 'interior' || name === 'toolhead') {
    await page.click(`[data-testid="view-${name}"]`);
  } else {
    await page.evaluate(([p, t]) => window.__PV_VIEW(p, t), [position, target]);
  }
  await page.waitForTimeout(3800);
  await page.screenshot({ path: `${out}/after_${name}.png` });
}

await page.evaluate(() => window.__PV_VIEW([620, -1080, 650], [0, 0, 225]));
await page.click('[data-testid="panel-clear"]');
await page.waitForTimeout(1800);
await page.screenshot({ path: `${out}/after_clear.png` });

await page.click('[data-testid="view-exploded"]');
await page.waitForTimeout(900);
await page.evaluate(() => {
  const input = document.querySelector('.explode-row input');
  if (input) { input.value = '0.65'; input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true })); }
});
await page.waitForTimeout(3000);
await page.screenshot({ path: `${out}/after_exploded.png` });

const fps = await page.evaluate(async () => {
  let n = 0;
  const start = performance.now();
  await new Promise((resolve) => {
    function loop(now) {
      n += 1;
      if (now - start > 3000) resolve(); else requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
  });
  return n / ((performance.now() - start) / 1000);
});

const resources = await page.evaluate(() => performance.getEntriesByType('resource').filter((r) => r.name.includes('/modules/')).map((r) => ({ name: r.name.split('/').pop(), transfer: r.transferSize, duration: Math.round(r.duration) })));
console.log(JSON.stringify({ loaded_ms: loadedMs, fps: Math.round(fps * 10) / 10, errors, resources }));
await browser.close();
