import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('../frontend/node_modules/playwright-core');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const browser = await chromium.launch({
  executablePath: EDGE,
  headless: false,
  args: ['--use-angle=d3d11', '--window-position=-1800,0', '--window-size=1440,980', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows'],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle', timeout: 120000 });
await page.waitForFunction(() => typeof window.__PV_VIEW === 'function', null, { timeout: 60000 });
await page.waitForTimeout(5000);
const info = await page.evaluate(() => {
  const gl = document.querySelector('canvas')?.getContext('webgl2');
  const ext = gl?.getExtension('WEBGL_debug_renderer_info');
  return { renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'none' };
});
await page.evaluate(() => { window.__PV_FRAMES = 0; });
const r = await page.evaluate(async () => {
  let n = 0; const s = performance.now();
  await new Promise((resolve) => { function loop(t) { n += 1; if (t - s > 3000) resolve(); else requestAnimationFrame(loop); } requestAnimationFrame(loop); });
  return { raf: n / ((performance.now() - s) / 1000), frames: window.__PV_FRAMES ?? 0 };
});
console.log(JSON.stringify({ info, ...r }));
await browser.close();
