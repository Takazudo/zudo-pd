import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const entry = join(root, 'circuit/scripts/check-led-p15-reference.sh');
const consumerVerifier = join(root, 'products/led-lamp/scripts/checks/verify-p15-reference.py');
const ownerVerifier = join(root, 'scripts/pcb/board-p15/verify-shared-reference.py');
const consumerRecord = join(root, 'products/led-lamp/boards/p15-r1-reference.json');
const pinned = '8af9e5569c2534c03ce132515d1ec11f4c3f83d3';
const c2 = '6945f8d4ccd969531b38cb338cecafe224bb2cfb';

function run(command, args, cwd = root) {
  return spawnSync(command, args, { cwd, encoding: 'utf8' });
}

test('root entry verifies both revisions from independent working directories', () => {
  for (const cwd of [root, tmpdir()]) {
    const result = run('bash', [entry], cwd);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, new RegExp(`Checking LED consumer and PD owner at ${pinned}`));
    assert.match(result.stdout, new RegExp(`Checking LED consumer and PD owner at ${c2}`));
    assert.equal((result.stdout.match(/SOURCE IDENTITY MATCH/g) ?? []).length, 4);
    assert.match(result.stdout, /programmed: NOT RUN/);
    assert.match(result.stdout, /measured: NOT RUN/);
  }
});

test('root entry rejects unexpected arguments', () => {
  const result = run('bash', [entry, '--local-only']);
  assert.equal(result.status, 2);
  assert.match(result.stderr, /usage:/);
});

test('consumer refuses missing owner history and mismatched pinned bytes', () => {
  const missing = run('python3', [consumerVerifier, '--pd-repo', tmpdir(), '--pd-rev', pinned]);
  assert.equal(missing.status, 1);
  assert.match(missing.stderr, /not found/);

  const temp = mkdtempSync(join(tmpdir(), 'led-p15-reference-'));
  try {
    const record = JSON.parse(readFileSync(consumerRecord, 'utf8'));
    record.pinned_artifacts[0].sha256 = '0'.repeat(64);
    const changed = join(temp, 'changed-consumer.json');
    writeFileSync(changed, JSON.stringify(record));
    const mismatch = run('python3', [consumerVerifier, '--pd-repo', root, '--pd-rev', c2, '--record', changed]);
    assert.equal(mismatch.status, 1);
    assert.match(mismatch.stderr, /LED pin .* != zudo-pd record/);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});

test('owner refuses missing revision and mismatched source lock', () => {
  const missing = run('python3', [ownerVerifier, '--repo', root, '--rev', '0'.repeat(40)]);
  assert.equal(missing.status, 1);
  assert.match(missing.stderr, /revision not found/);

  const temp = mkdtempSync(join(tmpdir(), 'pd-p15-reference-'));
  try {
    const record = JSON.parse(readFileSync(join(root, 'boards/board-p15/shared-reference.json'), 'utf8'));
    record.artifacts[0].sha256 = '0'.repeat(64);
    const changed = join(temp, 'changed-owner.json');
    writeFileSync(changed, JSON.stringify(record));
    const mismatch = run('python3', [ownerVerifier, '--repo', root, '--rev', c2, '--record', changed]);
    assert.equal(mismatch.status, 1);
    assert.match(mismatch.stderr, /sha256 .* != recorded/);
    assert.match(mismatch.stderr, /record sha256 differs from the frozen source lock/);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});
