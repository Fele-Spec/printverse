/** Capture the generated BOM page with a real browser (not the official Configurator UI). */
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('../frontend/node_modules/playwright-core');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const html = 'C:\\Users\\someb\\Desktop\\printverse\\BOM_300MM.html';
const out = 'assets/previews/BOM_300MM_browser.png';
fs.mkdirSync('assets/previews', { recursive: true });
const browser = await chromium.launch({ executablePath: EDGE, headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 1600 }, deviceScaleFactor: 1 });
const errors = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
const response = await page.goto(pathToFileURL(html).href, { waitUntil: 'load', timeout: 30000 });
await page.waitForTimeout(500);
await page.screenshot({ path: out, fullPage: true });
const result = {
  ok: response !== null,
  url: pathToFileURL(html).href,
  title: await page.title(),
  rows: await page.locator('tbody tr').count(),
  heading: await page.locator('h1').innerText(),
  screenshot: out,
  bytes: fs.statSync(out).size,
  errors,
};
fs.writeFileSync('docs/reports/bom_browser_screenshot.json', JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
await browser.close();
if (!result.ok || errors.length) process.exit(1);
