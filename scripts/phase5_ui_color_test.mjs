import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('../frontend/node_modules/playwright-core');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const browser = await chromium.launch({ executablePath: EDGE, headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle', timeout: 120000 });
await page.waitForTimeout(3500);
await page.screenshot({ path: 'BEFORE_AFTER_SCREENSHOTS/phase5_dashboard_cn.png' });

await page.click('[data-testid="open-image3d"]');
await page.waitForTimeout(500);
await page.setInputFiles('[data-testid="image3d-file"]', 'assets/test-models/image3d/01_cube.png');
await page.selectOption('[data-testid="image3d-provider"]', 'mock_relief');
await page.click('[data-testid="image3d-run"]');
await page.waitForFunction(() => {
  const el = document.querySelector('[data-testid="image3d-result"]');
  return el && /completed|failed/.test(el.textContent || '');
}, null, { timeout: 30000 });
await page.waitForTimeout(1500);
await page.screenshot({ path: 'BEFORE_AFTER_SCREENSHOTS/phase5_color_glb_panel.png' });
const result = await page.locator('[data-testid="image3d-result"]').innerText();
console.log(JSON.stringify({ result: result.slice(0, 500), errors }));
await browser.close();
