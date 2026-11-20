import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

const [root, mode] = process.argv.slice(2);
if (!root || !['aligned-only', 'flat'].includes(mode)) {
  throw new Error('usage: node verify-layout.mjs SCRATCH_ROOT aligned-only|flat');
}
const expected = {
  'pnpm-workspace.yaml': 'c26306641fd6274d3157a8782f3b3c5767ddfe447afa59d1051d1320d3d3de76',
  'pnpm-lock.yaml': '4642e444fcfe57682deea81634073311c1ffafaf530b8f0c077247544521a6c4',
  'products/led-lamp/package.json': '624b990b14b18e4fe4d1a4b2c3996fde61606b8098c15df6976e9391e9a8b581',
  'products/led-lamp/pnpm-lock.yaml': '6987246726a2cfa4aeb01cddb6825c3224f62ac64f62b2d00c7d0f8ae91a81d3',
};
const historicalWorkspace = '0f4e60757dd4c20657b2f72acf9af585587f4aeee1c2bf8f5590fec7832cbf03';
const digest = (path) => createHash('sha256').update(readFileSync(join(root, path))).digest('hex');
for (const [path, hash] of Object.entries(expected)) {
  assert.equal(digest(path), hash, `${path} source binding`);
}
const nested = 'products/led-lamp/pnpm-workspace.yaml';
const archived = 'products/led-lamp/pnpm-workspace.historical.yaml';
assert.equal(existsSync(join(root, nested)), mode === 'aligned-only');
assert.equal(existsSync(join(root, archived)), mode === 'flat');
assert.equal(digest(mode === 'flat' ? archived : nested), historicalWorkspace);
const packageManager = JSON.parse(readFileSync(join(root, 'products/led-lamp/package.json'), 'utf8')).packageManager;
assert.equal(packageManager, 'pnpm@11.5.2');

const pnpm = spawnSync('corepack',
  ['pnpm', '--dir', 'products/led-lamp', '-r', 'list', '--depth', '-1', '--json'],
  { cwd: root, encoding: 'utf8' });
assert.equal(pnpm.status, 0, pnpm.stderr);
const members = JSON.parse(pnpm.stdout).map((item) => item.name).sort();
assert.deepEqual(members, mode === 'flat'
  ? ['doc', 'zudo-led-lamp-workspace', 'zudo-pd', 'zudo-pd-workspace']
  : ['doc', 'zudo-led-lamp-workspace']);

const routing = 'products/led-lamp/node_modules/@takazudo/zudo-circuit-doc/python/circuit_evidence/routing.py';
assert.equal(digest(routing), mode === 'flat'
  ? 'efd532f2f48992026e93f2651c0ba6768eea78f60b6c08e860590bea96854bea'
  : '0ef884503557a755f3b8c468e377fa5040bac8fe8aa24ea5bf0458df3c32e19e',
`${routing} installed patch binding`);
console.log(`${mode}: ${members.length} discovered importers; circuit-doc patch state bound; source locks unchanged`);
