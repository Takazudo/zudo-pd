import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
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
});
