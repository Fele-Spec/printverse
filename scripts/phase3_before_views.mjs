import { createRequire } from 'node:module';
import fs from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('../frontend/node_modules/playwright-core');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const out = 'BEFORE_AFTER_SCREENSHOTS';
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ executablePath: EDGE, headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForFunction(() => typeof window.__PV_VIEW === 'function', null, { timeout: 30000 });
await page.waitForTimeout(1200);
const views = [
  ['front', [620, -1080, 680], [0, 0, 270]],
  ['side', [1050, -80, 330], [0, 0, 270]],
  ['interior', [260, -520, 360], [0, 0, 295]],
  ['top', [0, -420, 1120], [0, 0, 270]],
];
for (const [name, position, target] of views) {
  await page.evaluate(([p, t]) => window.__PV_VIEW(p, t), [position, target]);
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${out}/before_${name}.png` });
}
const metrics = await page.evaluate(() => ({ status: document.querySelector('[data-testid="print-status"]')?.textContent }));
console.log(JSON.stringify({ ok: true, screenshots: views.map(([n]) => `${out}/before_${n}.png`), metrics }));
await browser.close();
