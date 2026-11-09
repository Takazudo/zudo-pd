// Doc-history progress lines in both zfb shapes pass the build-log gate; anything else still fails.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

const SCRIPT = new URL('../scripts/check-zfb-link-warnings.sh', import.meta.url).pathname;
const DOCS = '/w/zudo-pd/doc/src/content/docs';

function gate(lines) {
  const dir = mkdtempSync(join(tmpdir(), 'zfb-gate-test-'));
  const log = join(dir, 'build.log');
  writeFileSync(log, ['build start', ...lines, 'build done', ''].join('\n'));
  const env = { ...process.env };
  delete env.GITHUB_ACTIONS;
  return spawnSync('bash', [SCRIPT, log], { encoding: 'utf8', env });
}

const progress = (p) => [
  `zfb warn: ${p}doc-history-server: content-dir resolved to ${DOCS}`,
  `zfb warn: ${p}Processing default: 79 files in ${DOCS}`,
  `zfb warn: ${p}Generated 79 history files in 4.7s`,
];

test('accepts the three doc-history progress messages in the zfb 2.x shape', () => {
  assert.equal(gate(progress('[plugin-host stdout] ')).status, 0);
});

test('accepts the three doc-history progress messages in the zfb 5 ZB006 shape', () => {
  const r = gate(progress('ZB006 plugin-host:stdout: '));
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /suppressed\s+3 doc-history progress/u);
});

test('rejects plugin stderr, other ZB006 output and unprefixed or changed messages', () => {
  for (const line of [
    'zfb warn: ZB006 plugin-host:stderr: doc-history-server: INIT_CWD candidate "/w/src/content/docs" does not exist; falling back to process.cwd()',
    'zfb warn: ZB006 plugin-host:stdout: something else entirely',
    'zfb warn: ZB007 plugin-host:stdout: Generated 79 history files in 4.7s',
    'zfb warn: Generated 79 history files in 4.7s',
    `zfb warn: ZB006 plugin-host:stdout: Processing default: 79 files in /w/elsewhere`,
  ]) {
    assert.equal(gate([line]).status, 1, line);
  }
});
