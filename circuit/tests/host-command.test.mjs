import test from 'node:test';
import assert from 'node:assert/strict';
import { chmod, mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
import { root } from './compatibility-helpers.mjs';

test('root build and dev start the doc host without inherited workspace history context', async () => {
  const scratch = await mkdtemp(join(tmpdir(), 'zudo-pd-host-context-'));
  try {
    const bin = join(scratch, 'bin');
    await mkdir(bin);
    const pnpm = join(bin, 'pnpm');
    await writeFile(pnpm, '#!/usr/bin/env node\nprocess.stdout.write(JSON.stringify({cwd:process.cwd(),init:process.env.INIT_CWD??null,args:process.argv.slice(2)})+"\\n");\n');
    await chmod(pnpm, 0o755);
    const env = { ...process.env, PATH: `${bin}:${process.env.PATH}`, INIT_CWD: root, ZUDO_DOC_BUILD_LOG: join(scratch, 'build.log') };
    const scripts = JSON.parse(await readFile(join(root, 'package.json'), 'utf8')).scripts;
    for (const [args, command] of [
      [[join(root, 'circuit/scripts/build-doc.sh')], 'build'],
      [['-c', scripts.dev], 'dev'],
      [[join(root, 'circuit/scripts/doc-command.sh'), 'check'], 'check'],
    ]) {
      const result = spawnSync('bash', args, { cwd: root, env, encoding: 'utf8' });
      assert.equal(result.status, 0, result.stderr);
      const actual = JSON.parse(result.stdout.trim());
      assert.equal(actual.cwd, join(root, 'doc'));
      assert.equal(actual.init, null, 'workspace INIT_CWD must not reach the doc lifecycle');
      assert.deepEqual(actual.args, [command]);
    }
    const result = spawnSync('bash', [join(root, 'circuit/scripts/doc-command.sh'), 'exec', 'node', 'argument with spaces'], { cwd: scratch, env, encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(JSON.parse(result.stdout.trim()).args, ['exec', 'node', 'argument with spaces']);
  } finally {
    await rm(scratch, { recursive: true, force: true });
  }
});
