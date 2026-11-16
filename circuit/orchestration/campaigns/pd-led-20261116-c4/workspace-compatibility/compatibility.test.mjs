import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir, realpath } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { verifyBindings } from './source-bindings.mjs';

const [unified, separate, ledSource] = process.argv.slice(2);
if (![unified, separate, ledSource].every(Boolean)) {
  throw new Error('usage: node compatibility.test.mjs UNIFIED SEPARATE LED_SOURCE');
}
await verifyBindings(unified, separate, ledSource);
const load = async (path) => import(pathToFileURL(path).href);
const packageRoot = async (root, nested) => realpath(join(root,
  nested ? 'products/led-lamp/node_modules/@takazudo/zudo-circuit-doc'
    : 'node_modules/@takazudo/zudo-circuit-doc'));
const unifiedPackage = await packageRoot(unified, true);
const separatePackage = await packageRoot(separate, false);
const recordPath = join(ledSource, 'doc/src/content/docs/components/records/c15849/index.mdx');
const routesPath = join(ledSource, '.claude/skills/component-stusb4500qtr/routing.json');
const page = (section) => `<main>${section}<h2 id="sources">Sources</h2><table class="zcd-evidence-table"></table></main>`;

async function references() {
  const mdx = await readFile(recordPath, 'utf8');
  const encoded = /<ComponentReferences descriptor="([0-9a-f]+)"\s*\/>/u.exec(mdx)?.[1];
  assert.ok(encoded, 'retained LED record descriptor missing');
  const descriptorModule = await load(join(unifiedPackage, 'lib/core/reference-descriptor.js'));
  const descriptor = descriptorModule.decodeComponentReferencesDescriptor(encoded);
  assert.ok(descriptor.modelDescriptor);
  const require = createRequire(join(unified, 'package.json'));
  const { build } = require('esbuild');
  const output = await build({
    stdin: {
      contents: [
        `export {ComponentReferences} from ${JSON.stringify(join(unifiedPackage, 'lib/ui/component-references.js'))};`,
        'export {h} from "@takazudo/zfb/zudo-react";',
        'import {renderToString} from "@takazudo/zfb/zudo-react/server";',
        'import {withIslandTestContext} from "@takazudo/zfb/zudo-react/testing";',
        `import {FootprintPreviewIsland} from ${JSON.stringify(join(unifiedPackage, 'lib/islands/footprint-preview-island.js'))};`,
        `import {PackageModelViewerIsland} from ${JSON.stringify(join(unifiedPackage, 'lib/islands/package-model-viewer-island.js'))};`,
        'export const render=(node)=>withIslandTestContext({components:{FootprintPreviewIsland,PackageModelViewerIsland}},()=>renderToString(node));',
      ].join('\n'),
      resolveDir: join(unified, 'products/led-lamp/doc'), loader: 'js',
    },
    bundle: true, write: false, platform: 'node', format: 'esm', logLevel: 'silent',
  });
  const ui = await import(`data:text/javascript;base64,${Buffer.from(output.outputFiles[0].text).toString('base64')}`);
  const render = (value) => ui.render(ui.h(ui.ComponentReferences, { descriptor: value }));
  return { encoded, descriptor, descriptorModule, render };
}
const referencePromise = references();

test('binding verifier rejects changed source and installed package bytes', async () => {
  const mutate = (suffix) => async (path) => {
    const bytes = await readFile(path);
    if (!path.endsWith(suffix)) return bytes;
    const changed = Buffer.from(bytes);
    changed[0] ^= 1;
    return changed;
  };
  await assert.rejects(() => verifyBindings(unified, separate, ledSource,
    mutate('components/records/c15849/index.mdx')), /source binding mismatch/u);
  await assert.rejects(() => verifyBindings(unified, separate, ledSource,
    mutate('lib/browser-smoke/chrome.js')), /source binding mismatch/u);
});

test('retained LED available-document model card passes both installed scanners', async () => {
  const { encoded, descriptor, render } = await referencePromise;
  assert.ok(descriptor.document.url && descriptor.modelDescriptor);
  const section = render(encoded);
  const record = { reference: { document: descriptor.document, documentUnavailableReason: null } };
  for (const root of [unifiedPackage, separatePackage]) {
    const { checkRecordPage } = await load(join(root, 'lib/scan/built-references.js'));
    checkRecordPage('c15849', page(section), new Set(), new Set(), true, record);
  }
});

test('hypothetical unavailable LED document retains only its real model and footprint links', async () => {
  const { descriptor, descriptorModule, render } = await referencePromise;
  const reason = 'Compatibility fixture: selected document unavailable';
  const unavailable = descriptorModule.encodeComponentReferencesDescriptor({
    ...descriptor, document: { label: descriptorModule.DOCUMENT_UNAVAILABLE_LABEL, reason },
  });
  const section = render(unavailable);
  const record = { reference: { document: null, documentUnavailableReason: reason } };
  const patched = (await load(join(unifiedPackage, 'lib/scan/built-references.js'))).checkRecordPage;
  const original = (await load(join(separatePackage, 'lib/scan/built-references.js'))).checkRecordPage;
  patched('c15849', page(section), new Set(), new Set(), true, record);
  assert.throws(() => original('c15849', page(section), new Set(), new Set(), true, record), /must not link a document/u);
  const injected = section.replace('</section>', '<a href="https://example.test/unapproved.pdf">bad</a></section>');
  assert.throws(() => patched('c15849', page(injected), new Set(), new Set(), true, record), /must not link a document/u);
});

test('actual LED order-code route changes only at the patched refusal boundary', () => {
  const program = `import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/'python'))
from circuit_evidence.routing import resolve_bundle_route
routes=json.loads(Path(sys.argv[2]).read_text())['routes']
for query in ('PESD24VS1UB,115','PESD24VS1UB,125','PESD24VS1UB, 115 from OtherVendor'):
 print(json.dumps(resolve_bundle_route(query,routes)))`;
  const results = [unifiedPackage, separatePackage].map((root) => {
    const result = spawnSync('python3', ['-c', program, root, routesPath], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    return result.stdout.trim().split('\n').map(JSON.parse);
  });
  assert.deepEqual(results[0], [['rec-pesd24vs1ub'], [], []]);
  assert.deepEqual(results[1], [['rec-pesd24vs1ub'], ['rec-pesd24vs1ub'], ['rec-pesd24vs1ub']]);
});

test('patched navigation rejects a hidden page; original navigation has no visibility assertion', async () => {
  const fake = (visibility) => ({ send: async (method, params) => method === 'Runtime.evaluate'
    ? { result: { value: params.expression === 'document.visibilityState' ? visibility : true } }
    : {} });
  const patched = (await load(join(unifiedPackage, 'lib/browser-smoke/cdp.js'))).navigate;
  const original = (await load(join(separatePackage, 'lib/browser-smoke/cdp.js'))).navigate;
  await assert.rejects(() => patched(fake('hidden'), 'http://localhost/', '/docs/led-lamp/'), /interaction test page is active/u);
  await patched(fake('visible'), 'http://localhost/', '/docs/led-lamp/');
  await original(fake('hidden'), 'http://localhost/', '/docs/led-lamp/');
});

test('three shifted transitive packages pass focused LED-path probes in both resolutions', async () => {
  const { encoded, descriptor, render } = await referencePromise;
  const modelUrl = JSON.parse(Buffer.from(descriptor.modelDescriptor, 'hex').toString()).modelUrl;
  const section = render(encoded);
  const versions = {
    unified: { hono: '4.13.16', parse5: '8.1.0', resolve: '3.1.3' },
    separate: { hono: '4.13.17', parse5: '8.1.1', resolve: '3.1.2' },
  };
  const outcomes = [];
  for (const [label, root] of [['unified', unified], ['separate', separate]]) {
    const dirs = await readdir(join(root, 'node_modules/.pnpm'));
    const packageAt = async (prefix, name) => {
      const folder = dirs.find((entry) => entry.startsWith(prefix));
      assert.ok(folder, `${label}: ${prefix} missing`);
      const path = join(root, 'node_modules/.pnpm', folder, 'node_modules', name);
      return { path, version: JSON.parse(await readFile(join(path, 'package.json'), 'utf8')).version };
    };
    const hono = await packageAt('hono@', 'hono');
    const parse5 = await packageAt('parse5@', 'parse5');
    const resolveUri = await packageAt('@jridgewell+resolve-uri@', '@jridgewell/resolve-uri');
    assert.deepEqual([hono.version, parse5.version, resolveUri.version],
      [versions[label].hono, versions[label].parse5, versions[label].resolve]);
    const { Hono } = await load(join(hono.path, 'dist/hono.js'));
    const app = new Hono().get('/docs/components/records/c15849/', (context) => context.text('LED record'));
    const response = await app.request('https://example.test/docs/components/records/c15849/');
    assert.equal(response.status, 200);
    assert.equal(await response.text(), 'LED record');
    const parsed = await load(join(parse5.path, 'dist/index.js'));
    const serialized = parsed.serialize(parsed.parseFragment(section));
    assert.match(serialized, /data-model-url/u);
    const uri = (await load(join(resolveUri.path, 'dist/resolve-uri.mjs'))).default;
    const resolved = uri(modelUrl, 'https://example.test/docs/components/records/c15849/');
    assert.equal(resolved, `https://example.test${modelUrl}`);
    outcomes.push(serialized);
  }
  assert.equal(outcomes[0], outcomes[1], 'parse5 versions changed retained LED reference markup');
});
