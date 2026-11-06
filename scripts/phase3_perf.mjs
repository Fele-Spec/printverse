import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('../frontend/node_modules/playwright-core');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const browser = await chromium.launch({ executablePath: EDGE, headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle', timeout: 120000 });
await page.waitForFunction(() => typeof window.__PV_VIEW === 'function', null, { timeout: 60000 });
await page.waitForTimeout(5000);
await page.evaluate(() => { window.__PV_FRAMES = 0; });
const raf = await page.evaluate(async () => {
  let n = 0;
  const start = performance.now();
  await new Promise((resolve) => {
    function loop(now) { n += 1; if (now - start > 3000) resolve(); else requestAnimationFrame(loop); }
    requestAnimationFrame(loop);
  });
  return { raf: n / ((performance.now() - start) / 1000), frames: window.__PV_FRAMES ?? 0 };
});
console.log(JSON.stringify({ raf: Math.round(raf.raf * 10) / 10, renderFrames: raf.frames }));
await browser.close();
