import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const meta = JSON.parse(readFileSync(resolve(root, '.zfb/doc-history-meta.json'), 'utf8'));
const cases = [
  ['getting-started/introduction', 'getting-started/introduction'],
  ['architecture', 'architecture'],
  ['research', 'research'],
];

for (const [slug, route] of cases) {
  const entry = meta[slug];
  assert.ok(entry?.createdDate && entry?.updatedDate, `${slug}: missing history dates`);
  assert.ok(new Date(entry.createdDate) < new Date('2026-11-16T11:09:13Z'), `${slug}: Created must predate the import`);
  const html = readFileSync(resolve(root, 'dist/docs', route, 'index.html'), 'utf8');
  assert.ok(html.includes(`Created: ${entry.createdDate}`), `${slug}: Created date is not rendered`);
  assert.ok(html.includes(`Updated: ${entry.updatedDate}`), `${slug}: Updated date is not rendered`);
}

const index = readFileSync(resolve(root, 'dist/docs/getting-started/index.html'), 'utf8');
assert.ok(index.includes('https://github.com/Takazudo/zudo-pd/tree/codex/c4j-history-links-20261116-01/products/led-lamp'));
assert.ok(index.includes('original zudo-led-lamp repository'));
assert.ok(index.includes('2026-11-16 import'));
assert.ok(!index.includes('/blob/HEAD/src/content/docs/'), 'nested View Source URL must remain disabled');

const current = readFileSync(resolve(root, 'dist/docs/architecture/current-state/index.html'), 'utf8');
assert.ok(!current.includes('zudo-led-lamp/blob/main/'), 'old repository source-file links remain');
const links = [...current.matchAll(/https:\/\/github\.com\/Takazudo\/zudo-pd\/blob\/2edec40d50f99fa69cbde55eb62fbd1082ee12d1\/products\/led-lamp\//gu)];
assert.equal(links.length, 6, 'preserved LED file links must render exactly six times');

console.log('Rendered history PASS: source-era Created dates, separate import note and maintained-source links');
