import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { join, resolve } from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { tmpdir } from 'node:os';
import test from 'node:test';

const repo = resolve(import.meta.dirname, '../../../../..');
const ledDoc = resolve(repo, 'products/led-lamp/doc');
const sample = resolve(ledDoc, 'src/content/docs/getting-started/introduction.mdx');
const require = createRequire(resolve(ledDoc, 'package.json'));
const historyModule = require.resolve('@takazudo/zudo-doc-history-server/git-history');
const { getAllFilesFirstLastMetaAsync, getDocHistoryAsync } = await import(pathToFileURL(historyModule));

test('imported LED document exposes current and source Git history with content', async () => {
  const meta = await getAllFilesFirstLastMetaAsync([resolve(ledDoc, 'src/content/docs')]);
  assert.ok(meta.size >= 40, `expected nonempty LED document history, got ${meta.size}`);
  assert.ok(meta.has(sample));

  const history = await getDocHistoryAsync(sample, 'getting-started/introduction');
  const hashes = new Set(history.entries.map(({ hash }) => hash));
  assert.equal(hashes.size, history.entries.length, 'merge parents must not duplicate a Compare step');
  assert.ok(hashes.has('2edec40d50f99fa69cbde55eb62fbd1082ee12d1'));
  assert.ok(hashes.has('dfcd6d81879b978ab21bc049e1274555a385dfab'));
  assert.ok(hashes.has('63ec3458efef6c7864b5a79417ef9b59c6bf836d'));
  assert.ok(history.entries.every(({ content }) => content.length > 0));
  assert.equal(meta.get(sample).oldest.date, history.entries.at(-1).date);
  assert.equal(meta.get(sample).newest.date, history.entries[0].date);
});

test('PD history keeps its first-parent source despite the LED import merge', async () => {
  const pdDoc = resolve(repo, 'doc');
  const pdSample = resolve(pdDoc, 'src/content/docs/architecture/board-p15-programming.md');
  const meta = await getAllFilesFirstLastMetaAsync([resolve(pdDoc, 'src/content/docs')]);
  assert.ok(meta.has(pdSample));
  const history = await getDocHistoryAsync(pdSample, 'architecture/board-p15-programming');
  assert.ok(history.entries.length >= 2);
  assert.ok(history.entries.every(({ content }) => content.length > 0));
  assert.ok(!history.entries.some(({ hash }) => hash === '2edec40d50f99fa69cbde55eb62fbd1082ee12d1'));
  assert.equal(meta.get(pdSample).newest.date, history.entries[0].date);
});

test('LED rename through the import merge retains source-era revisions', async () => {
  const ledBoard = resolve(ledDoc, 'src/content/docs/architecture/board-l.mdx');
  const history = await getDocHistoryAsync(ledBoard, 'architecture/board-l');
  assert.equal(history.entries[0].hash, '2edec40d50f99fa69cbde55eb62fbd1082ee12d1');
  assert.ok(history.entries.some(({ hash }) => hash === 'ca4b2544c75b939914d0c4a00d715e4fb9fe6a1d'));
  assert.ok(history.entries.every(({ content }) => content.length > 0));
  const rename = execFileSync('git', ['log', '-m', '--find-renames', '--diff-filter=R', '--name-status', '--format=', '--',
    'doc/src/content/docs/architecture/board-l.mdx',
    'products/led-lamp/doc/src/content/docs/architecture/board-l.mdx'], { cwd: repo, encoding: 'utf8' });
  assert.match(rename, /R100\s+doc\/src\/content\/docs\/architecture\/board-l\.mdx\s+products\/led-lamp\/doc\/src\/content\/docs\/architecture\/board-l\.mdx/u);
});

test('the C1 merge does not invent an LED edit or update date', async () => {
  const c1Merge = 'e0be0beefdf4eebd7658194929e9f58145fc392d';
  const ledBoard = resolve(ledDoc, 'src/content/docs/architecture/board-l.mdx');
  const relativeBoard = 'products/led-lamp/doc/src/content/docs/architecture/board-l.mdx';
  assert.equal(spawnSync('git', ['diff', '--quiet', `${c1Merge}^1`, c1Merge, '--', relativeBoard], { cwd: repo }).status, 0,
    'the C1 merge must leave this LED document unchanged');
  const history = await getDocHistoryAsync(ledBoard, 'architecture/board-l');
  assert.ok(!history.entries.some(({ hash }) => hash === c1Merge), 'a byte-identical merge must not become a Compare step');
  assert.equal(history.entries[0].hash, '2edec40d50f99fa69cbde55eb62fbd1082ee12d1');
  const meta = await getAllFilesFirstLastMetaAsync([resolve(ledDoc, 'src/content/docs')]);
  assert.equal(meta.get(ledBoard).newest.date, '2026-11-16T11:09:13Z',
    'a byte-identical merge must not move the document update date');
});

test('a same-named PD path cannot hide the LED import snapshot', async () => {
  const file = resolve(ledDoc, 'src/content/docs/claude-skills/component-type-c-31-m-17/index.mdx');
  const history = await getDocHistoryAsync(file, 'claude-skills/component-type-c-31-m-17');
  const hashes = history.entries.map(({ hash }) => hash);
  assert.equal(hashes[0], '2edec40d50f99fa69cbde55eb62fbd1082ee12d1');
  assert.ok(hashes.includes('b11ba50295795a7d716aca0996846059b12400e0'), 'LED source-era revision missing');
  assert.ok(!hashes.includes('609c1bbcd6c5e331737e15edc121d050f393c3bc'), 'same-named PD revision leaked');
  assert.ok(!hashes.includes('e0be0beefdf4eebd7658194929e9f58145fc392d'), 'unchanged C1 merge leaked');
  const meta = await getAllFilesFirstLastMetaAsync([resolve(ledDoc, 'src/content/docs')]);
  assert.equal(meta.get(file).newest.date, '2026-11-16T11:09:13Z');
});

test('overlapping LED and PD path names stay in their own ancestry', async () => {
  const meta = await getAllFilesFirstLastMetaAsync([resolve(ledDoc, 'src/content/docs')]);
  const isAncestor = (a, b) => spawnSync('git', ['merge-base', '--is-ancestor', a, b], { cwd: repo }).status === 0;
  for (const slug of ['architecture/index', 'research/index']) {
    const file = resolve(ledDoc, `src/content/docs/${slug}.mdx`);
    const history = await getDocHistoryAsync(file, slug);
    assert.ok(history.entries.length >= 2, slug);
    for (const { hash } of history.entries) {
      assert.ok(isAncestor('2edec40d50f99fa69cbde55eb62fbd1082ee12d1', hash) ||
        isAncestor(hash, '88cb17409cf16a0391e8eadf0ad8a43d60a37356'), `${slug}: unrelated PD commit ${hash}`);
    }
    assert.equal(meta.get(file).oldest.date, history.entries.at(-1).date);
    assert.equal(meta.get(file).newest.date, history.entries[0].date);
  }
});

test('a divergent PD merge cannot add a pre-import branch to LED history', () => {
  const fixture = mkdtempSync(join(tmpdir(), 'pd-led-history-dag-'));
  try {
    execFileSync('git', ['clone', '--quiet', '--shared', '--no-checkout', repo, fixture]);
    const git = (args, options = {}) => execFileSync('git', args, { cwd: fixture, encoding: 'utf8', ...options }).trim();
    const env = {
      ...process.env,
      GIT_AUTHOR_NAME: 'History fixture',
      GIT_AUTHOR_EMAIL: 'history@example.invalid',
      GIT_COMMITTER_NAME: 'History fixture',
      GIT_COMMITTER_EMAIL: 'history@example.invalid',
    };
    const importCommit = '2edec40d50f99fa69cbde55eb62fbd1082ee12d1';
    const base = 'ea0a4a80e6d7268bb3df1e80c57408d672909244';
    const head = git(['rev-parse', 'HEAD']);
    const path = 'products/led-lamp/doc/src/content/docs/architecture/index.mdx';
    const blob = git(['hash-object', '-w', '--stdin'], { input: 'Divergent PD branch fixture\n' });

    const commitTree = (index, parent) => {
      const indexed = { ...env, GIT_INDEX_FILE: join(fixture, index) };
      git(['read-tree', parent], { env: indexed });
      git(['update-index', '--add', '--cacheinfo', '100644', blob, path], { env: indexed });
      return git(['write-tree'], { env: indexed });
    };
    const sideTree = commitTree('side-index', base);
    const side = git(['commit-tree', sideTree, '-p', base, '-m', 'divergent PD edit'], { env });
    const mergeTree = commitTree('merge-index', head);
    const merge = git(['commit-tree', mergeTree, '-p', head, '-p', side, '-m', 'merge divergent PD edit'], { env });
    git(['update-ref', 'refs/heads/divergent-fixture', merge]);
    git(['symbolic-ref', 'HEAD', 'refs/heads/divergent-fixture']);

    assert.ok(git(['rev-list', `${importCommit}..HEAD`]).split('\n').includes(side));
    assert.ok(git(['log', '-m', '--follow', '--format=%H', '--', path]).split('\n').includes(side));
    const probe = `import { pathToFileURL } from 'node:url'; import { resolve } from 'node:path';
      const { getDocHistoryAsync } = await import(pathToFileURL(${JSON.stringify(historyModule)}));
      const history = await getDocHistoryAsync(resolve(${JSON.stringify(path)}), 'architecture');
      process.stdout.write(JSON.stringify(history.entries.map((entry) => entry.hash)));`;
    const hashes = JSON.parse(execFileSync(process.execPath, ['--input-type=module', '-e', probe], {
      cwd: fixture,
      encoding: 'utf8',
    }));
    assert.ok(hashes.includes(merge), 'fixture merge should remain in LED history');
    assert.ok(!hashes.includes(side), 'unrelated pre-import PD branch leaked into LED history');
  } finally {
    rmSync(fixture, { recursive: true, force: true });
  }
});

test('maintained source links resolve to preserved bytes and origin stays labeled', () => {
  const config = readFileSync(resolve(ledDoc, 'zfb.config.ts'), 'utf8');
  assert.match(config, /githubUrl: "https:\/\/github\.com\/Takazudo\/zudo-pd"/u);
  assert.match(config, /viewSourceLink: false/u);
  const index = readFileSync(resolve(ledDoc, 'src/content/docs/getting-started/index.mdx'), 'utf8');
  assert.match(index, /current consolidation candidate/u);
  assert.match(index, /original zudo-led-lamp repository/u);
  const currentState = readFileSync(resolve(ledDoc, 'src/content/docs/architecture/current-state.mdx'), 'utf8');
  assert.doesNotMatch(currentState, /zudo-led-lamp\/blob\/main\//u);
  const paths = [...currentState.matchAll(/https:\/\/github\.com\/Takazudo\/zudo-pd\/blob\/2edec40d50f99fa69cbde55eb62fbd1082ee12d1\/(products\/led-lamp\/[^)]+)\)/gu)].map((match) => match[1]);
  assert.equal(paths.length, 6);
  for (const path of new Set(paths)) {
    const imported = execFileSync('git', ['rev-parse', `2edec40:${path}`], { cwd: repo, encoding: 'utf8' });
    const current = execFileSync('git', ['rev-parse', `HEAD:${path}`], { cwd: repo, encoding: 'utf8' });
    assert.equal(imported, current, path);
  }
});

test('preservation receipt names the current workspace and lock bytes', () => {
  const receipt = readFileSync(resolve(import.meta.dirname, 'FULL_HISTORY_CANDIDATE.md'), 'utf8');
  for (const path of ['pnpm-workspace.yaml', 'pnpm-lock.yaml']) {
    const actual = createHash('sha256').update(readFileSync(resolve(repo, path))).digest('hex');
    assert.ok(receipt.includes(actual), `${path} receipt is stale`);
  }
});
