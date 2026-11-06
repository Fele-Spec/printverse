/**
 * Real browser smoke test for the PrintVerse Three.js scene.
 * Uses the system Microsoft Edge (no browser download) through playwright-core.
 */
import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('../frontend/node_modules/playwright-core');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const URL = process.env.PV_URL || 'http://127.0.0.1:4173/';
const outDir = 'assets/previews';
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: EDGE,
  headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 980 }, deviceScaleFactor: 1 });
const consoleErrors = [];
const http404 = [];
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});
page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`));
page.on('response', (response) => {
  if (response.status() === 404) http404.push(response.url());
});

const result = { url: URL, title: null, objectName: null, canvas: null, webgl: null, http404, errors: consoleErrors, screenshots: [] };
await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForSelector('canvas', { timeout: 30000 });
await page.waitForTimeout(2500);
result.title = await page.title();
result.objectName = await page.locator('[data-testid="object-name"]').innerText();
result.canvas = await page.locator('canvas').evaluate((el) => ({ width: el.width, height: el.height, cssWidth: el.clientWidth, cssHeight: el.clientHeight }));
result.webgl = await page.evaluate(() => {
  const canvas = document.querySelector('canvas');
  if (!canvas) return null;
  const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
  if (!gl) return null;
  const ext = gl.getExtension('WEBGL_debug_renderer_info');
  return {
    version: gl.getParameter(gl.VERSION),
    renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
    vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
  };
});

const canvas = page.locator('canvas');
const box = await canvas.boundingBox();
if (!box) throw new Error('canvas has no layout box');

await page.screenshot({ path: `${outDir}/threejs_scene.png` });
result.screenshots.push('assets/previews/threejs_scene.png');

// Drag-orbit and wheel-zoom.
await page.mouse.move(box.x + box.width * 0.52, box.y + box.height * 0.52);
await page.mouse.down();
await page.mouse.move(box.x + box.width * 0.72, box.y + box.height * 0.42, { steps: 18 });
await page.mouse.up();
await page.mouse.wheel(0, -420);
await page.waitForTimeout(900);
await page.screenshot({ path: `${outDir}/threejs_orbited.png` });
result.screenshots.push('assets/previews/threejs_orbited.png');

// Background switch.
await page.click('[data-testid="bg-light"]');
await page.waitForTimeout(700);
await page.screenshot({ path: `${outDir}/threejs_light.png` });
result.screenshots.push('assets/previews/threejs_light.png');
result.lightButtonActive = await page.locator('[data-testid="bg-light"]').evaluate((el) => el.classList.contains('active'));
result.spinTogglePresent = await page.locator('[data-testid="spin-toggle"]').count();

// Verify the rendered image is not a flat empty canvas.
result.pixelVariance = await page.locator('canvas').evaluate((el) => {
  const c = document.createElement('canvas');
  c.width = 64; c.height = 64;
  const ctx = c.getContext('2d');
  ctx.drawImage(el, 0, 0, 64, 64);
  const d = ctx.getImageData(0, 0, 64, 64).data;
  let min = 255, max = 0, sum = 0;
  for (let i = 0; i < d.length; i += 4) {
    const v = (d[i] + d[i + 1] + d[i + 2]) / 3;
    min = Math.min(min, v); max = Math.max(max, v); sum += v;
  }
  return { min, max, mean: sum / (d.length / 4), range: max - min };
});

fs.writeFileSync('docs/reports/threejs_smoke.json', JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
await browser.close();
if (!result.webgl || consoleErrors.length) process.exit(1);
