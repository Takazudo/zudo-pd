import test from 'node:test';
import assert from 'node:assert/strict';
import { chmod, mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
import { root } from './compatibility-helpers.mjs';

test('CI preview gate preserves upload errors, bootstraps only a missing top-level Worker, and requires an alias URL', async () => {
  const scratch = await mkdtemp(join(tmpdir(), 'zudo-pd-preview-gate-'));
  try {
    const bin = join(scratch, 'bin');
    await mkdir(bin);
    const npx = join(bin, 'npx');
    await writeFile(npx, `#!/usr/bin/env node
import {appendFileSync,existsSync,writeFileSync} from 'node:fs';
const args=process.argv.slice(2),mode=process.env.ZUDO_PD_PREVIEW_MODE,state=process.env.ZUDO_PD_PREVIEW_STATE;
appendFileSync(process.env.ZUDO_PD_PREVIEW_CALLS,JSON.stringify(args)+'\\n');
if(args.includes('deploy')){if(mode==='deploy-fails')process.exit(9);writeFileSync(state,'created');process.exit(0);}
if(mode==='auth'){console.error('authentication denied');process.exit(7);}
if(['bootstrap','deploy-fails','retry-fails'].includes(mode)&&!existsSync(state)){console.error('You cannot upload a new version of a Worker that does not yet exist. Please run the deploy command first.');process.exit(1);}
if(mode==='retry-fails'){console.error('version upload failed after bootstrap');process.exit(6);}
console.log(mode==='no-url'?'Uploaded version with no alias URL':'Version Alias URL: https://pr-216-zudo-pd.example.workers.dev');
`);
    await chmod(npx, 0o755);
    const script = join(root, 'circuit/scripts/deploy-preview.sh');
    for (const [mode, expectedStatus, expectedCalls] of [
      ['success', 0, 1], ['bootstrap', 0, 3], ['auth', 7, 1],
      ['deploy-fails', 9, 2], ['retry-fails', 6, 3], ['no-url', 1, 1],
    ]) {
      const calls = join(scratch, `${mode}.calls`), output = join(scratch, `${mode}.output`);
      await writeFile(output, '');
      const env = { ...process.env, PATH: `${bin}:${process.env.PATH}`, GITHUB_OUTPUT: output, ZUDO_PD_PREVIEW_MODE: mode, ZUDO_PD_PREVIEW_STATE: join(scratch, `${mode}.state`), ZUDO_PD_PREVIEW_CALLS: calls };
      const result = spawnSync('bash', [script, '216'], { cwd: scratch, env, encoding: 'utf8' });
      assert.equal(result.status, expectedStatus, `${mode}: ${result.stdout}\n${result.stderr}`);
      const invocations = (await readFile(calls, 'utf8')).trim().split('\n').map(JSON.parse);
      assert.equal(invocations.length, expectedCalls, mode);
      for (const args of invocations) {
        assert.equal(args[args.indexOf('--env') + 1], '', `${mode} must target only the top-level preview Worker`);
        assert.ok(!args.includes('production'));
      }
      const recorded = await readFile(output, 'utf8');
      assert.equal(recorded, expectedStatus === 0 ? 'deploy_url=https://pr-216-zudo-pd.example.workers.dev\n' : '', mode);
    }
    const config = await readFile(join(root, 'doc/wrangler.toml'), 'utf8');
    const topLevel = config.split('[[env.production.routes]]')[0];
    assert.doesNotMatch(topLevel, /^\s*routes?\s*=/mu, 'preview bootstrap has no custom-domain route');
    assert.match(config, /\[\[env\.production\.routes\]\][\s\S]*pattern = "pd\.takazudomodular\.com"/u);
  } finally {
    await rm(scratch, { recursive: true, force: true });
  }
});
