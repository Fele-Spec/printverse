import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('../frontend/node_modules/playwright-core');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const browser = await chromium.launch({ executablePath: EDGE, headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const errors = [];
page.on('pageerror', (e) => { errors.push(String(e.stack || e)); console.log('PAGEERROR', e.stack || e); });
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle', timeout: 120000 });
await page.waitForTimeout(3500);

// 1. Generate colour GLB from an image.
await page.click('[data-testid="open-image3d"]');
await page.setInputFiles('[data-testid="image3d-file"]', 'assets/test-models/image3d/01_cube.png');
await page.selectOption('[data-testid="image3d-provider"]', 'mock_relief');
await page.click('[data-testid="image3d-run"]');
await page.waitForFunction(() => {
  const el = document.querySelector('[data-testid="image3d-result"]');
  return el && /completed|failed/.test(el.textContent || '');
}, null, { timeout: 30000 });
const genText = await page.locator('[data-testid="image3d-result"]').innerText();
await page.screenshot({ path: 'BEFORE_AFTER_SCREENSHOTS/phase5_color_result.png' });

// 2. Hand the derived STL to the print flow while preserving colour GLB.
await page.click('text=用于虚拟打印');
await page.waitForFunction(() => (document.body.textContent || '').includes('准备打印'), null, { timeout: 60000 });
const printCard = await page.locator('.print-card').innerText();
await page.click('[data-testid="start-print"]');
await page.click('[data-testid="speed-300"]');
await page.waitForFunction(() => (document.body.textContent || '').includes('打印完成'), null, { timeout: 30000 });
await page.waitForTimeout(2500);
await page.screenshot({ path: 'BEFORE_AFTER_SCREENSHOTS/phase5_finished_color.png' });
await page.click('[data-testid="detach-object"]');
await page.click('[data-testid="favorite-print"]');
await page.waitForTimeout(1200);
const collection = await page.locator('[data-testid="collection-list"]').innerText().catch(() => '');

// 3. Open the transparent desktop-pet view.
await page.goto('http://127.0.0.1:4173/?pet=1', { waitUntil: 'networkidle', timeout: 120000 });
await page.waitForTimeout(3500);
await page.screenshot({ path: 'BEFORE_AFTER_SCREENSHOTS/phase5_pet.png' });
const petText = await page.locator('[data-testid="pet-stage"]').innerText().catch(() => '');
console.log(JSON.stringify({ genText: genText.slice(0, 400), printCard: printCard.slice(0, 400), collection: collection.slice(0, 300), petText: petText.slice(0, 200), errors }));
await browser.close();
