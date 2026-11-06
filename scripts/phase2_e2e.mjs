/**
 * Phase-2 end-to-end browser test: upload STL -> real slice -> animate -> detach -> favorite.
 * Run under an approved full-access session because Chromium needs named-pipe IPC.
 */
import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('../frontend/node_modules/playwright-core');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const URL = process.env.PV_URL || 'http://127.0.0.1:4173/';
fs.mkdirSync('assets/previews', { recursive: true });
fs.mkdirSync('docs/reports', { recursive: true });

const browser = await chromium.launch({
  executablePath: EDGE,
  headless: true,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 980 }, deviceScaleFactor: 1 });
const errors = [];
const failed = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
page.on('response', (r) => { if (r.status() >= 400) failed.push(`${r.status()} ${r.url()}`); });

const result = { url: URL, steps: {}, screenshots: [], errors, failed };

async function statusText() {
  return (await page.locator('[data-testid="print-status"]').innerText()).trim();
}

await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForSelector('[data-testid="print-status"]', { timeout: 30000 });
await page.waitForTimeout(1200);
result.steps.initial_status = await statusText();
result.steps.initial_wallet = await page.locator('[data-testid="wallet-balance"]').innerText();
await page.screenshot({ path: 'assets/previews/phase2_scene_initial.png' });
result.screenshots.push('assets/previews/phase2_scene_initial.png');

// Real upload and slice.
await page.setInputFiles('[data-testid="upload-input"]', 'assets/test-models/cube.stl');
await page.waitForFunction(() => document.querySelector('[data-testid="print-status"]')?.textContent?.includes('READY'), null, { timeout: 120000 });
result.steps.upload_status = await statusText();
result.steps.job_notice = await page.locator('.notice-box').first().innerText().catch(() => '');
result.steps.layer_count = await page.locator('[data-testid="current-layer"]').innerText();

await page.click('[data-testid="speed-120"]');
await page.click('[data-testid="start-print"]');
await page.waitForTimeout(1400);
result.steps.mid_status = await statusText();
result.steps.mid_progress = await page.locator('[data-testid="progress-percent"]').innerText();
result.steps.mid_layer = await page.locator('[data-testid="current-layer"]').innerText();
await page.screenshot({ path: 'assets/previews/phase2_scene_printing.png' });
result.screenshots.push('assets/previews/phase2_scene_printing.png');

await page.waitForFunction(() => document.querySelector('[data-testid="print-status"]')?.textContent?.includes('COMPLETE'), null, { timeout: 60000 });
await page.waitForTimeout(1200);
result.steps.complete_status = await statusText();
result.steps.complete_progress = await page.locator('[data-testid="progress-percent"]').innerText();
result.steps.wallet_after = await page.locator('[data-testid="wallet-balance"]').innerText();
await page.screenshot({ path: 'assets/previews/phase2_scene_complete.png' });
result.screenshots.push('assets/previews/phase2_scene_complete.png');

await page.click('[data-testid="detach-object"]');
await page.waitForTimeout(500);
result.steps.detached_status = await statusText();
await page.click('[data-testid="mode-rotate"]');
await page.screenshot({ path: 'assets/previews/phase2_scene_detached.png' });
result.screenshots.push('assets/previews/phase2_scene_detached.png');

await page.click('[data-testid="favorite-print"]');
await page.waitForTimeout(1000);
result.steps.collection_items = await page.locator('[data-testid="collection-item"]').count();
result.steps.collection_open = await page.locator('[data-testid="collection-list"]').count();
await page.screenshot({ path: 'assets/previews/phase2_scene_collection.png' });
result.screenshots.push('assets/previews/phase2_scene_collection.png');

result.webgl = await page.evaluate(() => {
  const c = document.querySelector('canvas');
  const gl = c?.getContext('webgl2') || c?.getContext('webgl');
  if (!gl) return null;
  const ext = gl.getExtension('WEBGL_debug_renderer_info');
  return {
    version: gl.getParameter(gl.VERSION),
    renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
  };
});
result.ok = result.steps.upload_status === 'READY'
  && result.steps.mid_status === 'PRINTING'
  && result.steps.complete_status === 'COMPLETE'
  && result.steps.detached_status === 'DETACHED'
  && result.steps.collection_items >= 1
  && errors.length === 0;
fs.writeFileSync('docs/reports/phase2_e2e.json', JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
await browser.close();
if (!result.ok) process.exit(1);
