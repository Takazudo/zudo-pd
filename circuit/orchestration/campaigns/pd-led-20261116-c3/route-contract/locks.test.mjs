import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { verifyLockedCorpus } from './locks.mjs';

const sha256 = (value) => createHash('sha256').update(value).digest('hex');
const manifest = '.claude/skills/component-a/manifest.json';

function fixture(run) {
  const root = mkdtempSync(join(tmpdir(), 'zudo-c3e-locks-'));
  const bytes = '{"records":[{"record_id":"rec-a"}]}\n';
  mkdirSync(dirname(join(root, manifest)), { recursive: true });
  writeFileSync(join(root, manifest), bytes);
  const locks = { [manifest]: sha256(bytes) };
  const sourceSet = sha256(JSON.stringify(locks));
  try { run({ root, locks, sourceSet }); }
  finally { rmSync(root, { recursive: true, force: true }); }
}

test('locked manifest bytes and discovered set pass before use', () => fixture(({ root, locks, sourceSet }) => {
  const result = verifyLockedCorpus(root, locks, sourceSet);
  assert.equal(result.locked_source_files_verified, 1);
  assert.equal(result.locked_pd_manifest_files_verified, 1);
  assert.equal(JSON.parse(result.verifiedBytes.get(manifest)).records[0].record_id, 'rec-a');
}));

test('changed manifest bytes fail closed', () => fixture(({ root, locks, sourceSet }) => {
  writeFileSync(join(root, manifest), '{"records":[{"record_id":"rec-z"}]}\n');
  assert.throws(() => verifyLockedCorpus(root, locks, sourceSet), /locked input changed/);
}));

test('added manifest fails the discovered-set comparison', () => fixture(({ root, locks, sourceSet }) => {
  const added = join(root, '.claude/skills/component-b/manifest.json');
  mkdirSync(dirname(added), { recursive: true });
  writeFileSync(added, '{"records":[]}\n');
  assert.throws(() => verifyLockedCorpus(root, locks, sourceSet), /PD manifest set drift: added=/);
}));

test('removed manifest fails the discovered-set comparison', () => fixture(({ root, locks, sourceSet }) => {
  rmSync(join(root, manifest));
  assert.throws(() => verifyLockedCorpus(root, locks, sourceSet), /PD manifest set drift:.*removed=/);
}));

test('proposal source-set digest must match its lock table', () => fixture(({ root, locks }) => {
  assert.throws(() => verifyLockedCorpus(root, locks, '0'.repeat(64)), /source-set digest mismatch/);
}));
