#!/usr/bin/env node
/**
 * Replays the official Voron V2.4 configurator JavaScript locally.
 * Baseline: V2.4 / 300mm / New Build / Direct Feed / Blind Joints / Generic Cable Chains.
 *
 * The configurator is a static page; this executes its published logic rather than
 * guessing a BOM. Output keeps the official quantities and records every parameter.
 */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const root = process.cwd();
const bomDir = path.join(root, 'assets/source/voron-v2.4r2-300/BOM');
const rawDir = path.join(bomDir, 'raw');
const outDir = path.join(root, 'docs/reports');
fs.mkdirSync(outDir, { recursive: true });

const config = {
  printer: 'V2.4',
  size: '300mm Spec',
  buildType: 'New Build',
  feed: 'Direct Feed',
  frameJoints: 'Blind Joints',
  cableManagement: 'Generic Cable Chains',
  source: 'https://www.vorondesign.com/voron2.4',
  generator_js: 'https://www.vorondesign.com/js/configurator_2.4.js',
  bom_js: 'https://www.vorondesign.com/js/bom_2.4.js',
  captured_at: new Date().toISOString(),
};

const values = {
  '#build-x': '300',
  '#build-y': '300',
  '#build-z': '280',
  '#frame-x': '460',
  '#frame-y': '460',
  '#frame-z': '480',
};
const radios = {
  'upgrade-options': 'build',
  'size-options': '300',
  'feed-options': 'direct',
  'joint-options': 'blind',
  'chain-options': 'generic',
};

function jq(selector) {
  if (selector in values) {
    return {
      val(v) { if (v !== undefined) values[selector] = String(v); return values[selector]; },
      html() { return this; }, attr() { return this; }, show() {}, hide() {},
    };
  }
  const m = /^input\[name=([^\]]+)\](?::checked)?$/.exec(selector);
  if (m) {
    return {
      val(v) { if (v !== undefined) radios[m[1]] = String(v); return radios[m[1]]; },
      html() { return this; }, attr() { return this; }, show() {}, hide() {},
    };
  }
  return { val() { return undefined; }, html() { return this; }, attr() { return this; }, show() {}, hide() {} };
}
jq.each = function (obj, fn) {
  for (const key of Object.keys(obj)) if (fn(key, obj[key]) === false) break;
};

const sandbox = { $: jq, console, Math, Number, parseInt, Object, Blob: class {}, URL: { createObjectURL: () => '' } };
vm.createContext(sandbox);
vm.runInContext(`
  function get_screws_per_rail(rail_length) { return Math.round(rail_length / 40) + 1; }
  function convert_to_inch(mm) { return Math.round(mm * 0.03937007874); }
  function convert_to_ft(mm) { mm = mm * 0.00328084; return Math.round((mm + Number.EPSILON) * 100) / 100; }
  function get_heater_wattage(build_x, build_y) {
    var raw_watts = Math.round(0.0055 * (build_x * build_y));
    var specs = [200,250,300,350,400,450,500,550,600,650,700,750];
    var value = 750;
    for (var i = 0; i < specs.length; i++) { if (specs[i] - raw_watts > -50) { value = specs[i]; break; } }
    return value;
  }
`, sandbox);
for (const file of ['bom_2.4.js', 'configurator_2.4.js']) {
  vm.runInContext(fs.readFileSync(path.join(rawDir, file), 'utf8'), sandbox, { filename: file });
}
vm.runInContext("populate_bom('build');", sandbox, { filename: 'replay' });
const bom = sandbox.bom;

const rows = [];
for (const [category, parts] of Object.entries(bom)) {
  for (const [description, qty] of Object.entries(parts)) {
    rows.push({ category, description, qty: Number(qty) });
  }
}
if (!rows.length) throw new Error('BOM replay produced no rows');

// Official browser CSV shape (semicolon separated; category only on first row).
let official = 'Category;Description;Qty;Notes\n';
for (const [category, parts] of Object.entries(bom)) {
  let first = true;
  for (const [description, qty] of Object.entries(parts)) {
    official += `${first ? category : ''};${description};${qty};\n`;
    first = false;
  }
}
fs.writeFileSync(path.join(bomDir, 'BOM_300MM_official_raw.csv'), official.replace(/\n/g, '\r\n'));

// Enriched, UTF-8 BOM for Excel compatibility.
const esc = (v) => `"${String(v ?? '').replaceAll('"', '""')}"`;
const enriched = [
  'Category,Part Description,Qty,Notes,Source,Source URL,Config Verified',
  ...rows.map((r) => [
    r.category, r.description, r.qty,
    r.category === 'Fasteners' ? 'Listed quantities are minimum; buy extra' : '',
    'Official Voron V2.4 configurator replay', config.source,
    'V2.4 / 300 / New Build / Direct / Blind / Generic',
  ].map(esc).join(',')),
];
fs.writeFileSync(path.join(root, 'BOM_300MM.csv'), '\ufeff' + enriched.join('\r\n') + '\r\n');

const summary = {
  config,
  derived_geometry_mm: {
    build_volume: { x: Number(values['#build-x']), y: Number(values['#build-y']), z: Number(values['#build-z']) },
    frame_outer: { x: Number(values['#frame-x']), y: Number(values['#frame-y']), z: Number(values['#frame-z']) },
  },
  categories: Object.fromEntries(Object.entries(bom).map(([k, v]) => [k, Object.keys(v).length])),
  line_items: rows.length,
  total_quantity: rows.reduce((a, r) => a + r.qty, 0),
  zero_quantity_lines: rows.filter((r) => r.qty === 0).length,
  rows,
};
fs.writeFileSync(path.join(bomDir, 'BOM_300MM.json'), JSON.stringify(summary, null, 2));
console.log(`BOM rows=${rows.length} categories=${Object.keys(bom).length} totalQty=${summary.total_quantity}`);
console.log(`wrote BOM_300MM.csv, BOM_300MM_official_raw.csv, BOM_300MM.json`);
