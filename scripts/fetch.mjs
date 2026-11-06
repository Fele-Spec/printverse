#!/usr/bin/env node
/**
 * PrintVerse resilient downloader.
 * Node's HTTPS stack works in this environment where Windows schannel/Git TLS fails.
 *
 * Usage:
 *   node scripts/fetch.mjs --url <url> --out <path> [--sha256 <hex>] [--retries 4]
 *
 * Features: resume via HTTP Range, retries with backoff, SHA-256 verification,
 * atomic install, JSONL download ledger, periodic progress.
 */
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { Readable } from 'node:stream';

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

let url = arg('url');
let originUrl = arg('origin', url);
let expected = (arg('sha256', '') || '').toLowerCase();
const githubRepo = arg('github-repo');
const githubAsset = arg('github-asset');
const githubTag = arg('github-tag', 'latest');
const out = arg('out');
const retries = Number(arg('retries', '4'));
const userAgent = 'PrintVerse-Bootstrap/1.0 (+local engineering research)';
if ((!url && !(githubRepo && githubAsset)) || !out) {
  console.error('usage: node scripts/fetch.mjs (--url URL | --github-repo OWNER/REPO --github-asset NAME) --out PATH [--sha256 HEX] [--retries N]');
  process.exit(2);
}
let authHeaders = {};

// GitHub release assets are served through a different CDN than github.com, which is
// intermittently unreachable here. Resolve the asset through api.github.com instead.
if (githubRepo && githubAsset) {
  const api = `https://api.github.com/repos/${githubRepo}/releases/${githubTag === 'latest' ? 'latest' : `tags/${githubTag}`}`;
  console.log(`[fetch] resolving GitHub release asset ${githubRepo}@${githubTag} :: ${githubAsset}`);
  const rr = await fetch(api, { headers: { 'User-Agent': userAgent, Accept: 'application/vnd.github+json' } });
  if (!rr.ok) throw new Error(`GitHub release API HTTP ${rr.status}`);
  const release = await rr.json();
  const asset = release.assets?.find((a) => a.name === githubAsset);
  if (!asset) throw new Error(`asset not found: ${githubAsset}`);
  url = asset.url;
  originUrl = asset.browser_download_url;
  authHeaders = { Accept: 'application/octet-stream' };
  if (!expected && typeof asset.digest === 'string' && asset.digest.startsWith('sha256:')) {
    expected = asset.digest.slice(7).toLowerCase();
  }
  console.log(`[fetch] release ${release.tag_name}; size=${asset.size}; sha256=${expected || 'not published'}`);
}

const root = process.cwd();
const dest = path.resolve(root, out);
const part = `${dest}.part`;
await fsp.mkdir(path.dirname(dest), { recursive: true });
await fsp.mkdir(path.join(root, 'logs'), { recursive: true });

function sha256File(file) {
  return new Promise((resolve, reject) => {
    const h = crypto.createHash('sha256');
    const s = fs.createReadStream(file);
    s.on('data', (d) => h.update(d));
    s.on('error', reject);
    s.on('end', () => resolve(h.digest('hex')));
  });
}

function fmt(bytes) {
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(2)} GB`;
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
  if (bytes >= 1e3) return `${(bytes / 1e3).toFixed(1)} KB`;
  return `${bytes} B`;
}

async function existingValid() {
  try {
    const st = await fsp.stat(dest);
    if (!st.isFile() || st.size === 0) return false;
    if (!expected) return false; // without a checksum, always refresh explicit requests
    const actual = await sha256File(dest);
    if (actual === expected) {
      console.log(`[fetch] already present and verified: ${out} (${fmt(st.size)})`);
      return true;
    }
    console.log(`[fetch] existing file checksum mismatch, replacing: ${out}`);
    return false;
  } catch {
    return false;
  }
}

if (await existingValid()) process.exit(0);

let lastError;
for (let attempt = 1; attempt <= retries; attempt++) {
  let offset = 0;
  try {
    try { offset = (await fsp.stat(part)).size; } catch { offset = 0; }
    const headers = { 'User-Agent': userAgent, 'Accept': '*/*', ...authHeaders };
    if (offset > 0) headers.Range = `bytes=${offset}-`;
    console.log(`[fetch] attempt ${attempt}/${retries}: ${url}${offset ? ` (resume at ${fmt(offset)})` : ''}`);
    const res = await fetch(url, {
      headers,
      redirect: 'follow',
      signal: AbortSignal.timeout(2 * 60 * 60 * 1000),
    });
    if (res.status === 416 && offset > 0) {
      console.log('[fetch] server reports range complete');
    } else if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    } else {
      const append = res.status === 206 && offset > 0;
      if (!append) offset = 0;
      const totalHeader = res.headers.get('content-length');
      const total = totalHeader ? Number(totalHeader) + offset : 0;
      console.log(`[fetch] HTTP ${res.status}; ${total ? fmt(total) : 'unknown size'}; type=${res.headers.get('content-type')}`);
      const fh = await fsp.open(part, append ? 'a' : 'w');
      let written = offset;
      let lastReport = Date.now();
      try {
        for await (const chunk of Readable.fromWeb(res.body)) {
          await fh.write(chunk);
          written += chunk.length;
          if (Date.now() - lastReport > 5000) {
            const pct = total ? ` ${(written / total * 100).toFixed(1)}%` : '';
            console.log(`[fetch] ${fmt(written)}${pct}`);
            lastReport = Date.now();
          }
        }
      } finally {
        await fh.close();
      }
      console.log(`[fetch] body complete: ${fmt(written)}`);
    }

    const st = await fsp.stat(part);
    if (st.size === 0) throw new Error('downloaded file is empty');
    const actual = await sha256File(part);
    if (expected && actual !== expected) {
      throw new Error(`SHA256 mismatch: expected ${expected}, got ${actual}`);
    }
    await fsp.rm(dest, { force: true });
    await fsp.rename(part, dest);
    const record = {
      timestamp: new Date().toISOString(),
      url: originUrl || url,
      resolved_url: url,
      path: path.relative(root, dest).replaceAll('\\', '/'),
      bytes: st.size,
      sha256: actual,
      expected_sha256: expected || null,
      status: 'ok',
    };
    await fsp.appendFile(path.join(root, 'logs', 'downloads.jsonl'), JSON.stringify(record) + '\n');
    console.log(`[fetch] saved ${out}; ${fmt(st.size)}; sha256=${actual}`);
    process.exit(0);
  } catch (err) {
    lastError = err;
    console.error(`[fetch] attempt ${attempt} failed: ${err.message}`);
    if (attempt < retries) {
      const wait = Math.min(30000, 2000 * attempt);
      console.log(`[fetch] retrying in ${wait / 1000}s`);
      await new Promise((r) => setTimeout(r, wait));
    }
  }
}
console.error(`[fetch] FAILED after ${retries} attempts: ${lastError?.message}`);
process.exit(1);
