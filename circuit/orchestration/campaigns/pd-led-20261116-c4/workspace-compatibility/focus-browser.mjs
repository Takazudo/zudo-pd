import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, realpath } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [unified, separate, chromium] = process.argv.slice(2);
if (![unified, separate, chromium].every(Boolean)) {
  throw new Error('usage: node focus-browser.mjs UNIFIED SEPARATE CHROMIUM');
}
const server = createServer((request, response) => {
  response.writeHead(200, { 'content-type': 'text/html' });
  response.end('<!doctype html><html><title>LED focus probe</title><body>LED focus probe</body></html>');
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
try {
  for (const [label, root, nested] of [['unified', unified, true], ['separate', separate, false]]) {
    const packageRoot = await realpath(join(root, nested
      ? 'products/led-lamp/node_modules/@takazudo/zudo-circuit-doc'
      : 'node_modules/@takazudo/zudo-circuit-doc'));
    const source = await readFile(join(packageRoot, 'lib/browser-smoke/chrome.js'), 'utf8');
    assert.equal(source.includes('Emulation.setFocusEmulationEnabled'), nested);
    const { launchChrome } = await import(pathToFileURL(join(packageRoot, 'lib/browser-smoke/chrome.js')).href);
    const { navigate, evaluate } = await import(pathToFileURL(join(packageRoot, 'lib/browser-smoke/cdp.js')).href);
    const browser = await launchChrome(chromium);
    try {
      await navigate(browser.cdp, origin, '/docs/led-lamp/');
      assert.equal(await evaluate(browser.cdp, 'document.visibilityState'), 'visible');
      assert.equal(await evaluate(browser.cdp, 'document.title'), 'LED focus probe');
      console.log(`${label}: CDP launch/navigate visible PASS`);
    } finally {
      await browser.close();
    }
  }
} finally {
  await new Promise((resolve) => server.close(resolve));
}
