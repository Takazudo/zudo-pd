#!/usr/bin/env node

// Real Chrome regression for the private six-category site. Run after pnpm build.
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { extname, join, normalize, resolve, sep } from "node:path";

const dist = resolve(new URL("../../doc/dist", import.meta.url).pathname);
const routeMap = resolve(new URL("../orchestration/campaigns/pd-led-20261116-c1/route-map.tsv", import.meta.url).pathname);
const categories = [
  ["Project", "/docs/project", "Start Here"], ["Shared P15", "/docs/shared-p15", "Shared P15 r1"],
  ["PD15", "/docs/pd15", "PD15"], ["PD20", "/docs/pd20", "PD20"],
  ["LED Lamp", "/docs/led-lamp", "LED Lamp"], ["Components", "/docs/catalog", "Components catalog"],
];
const mime = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };
const delay = (ms) => new Promise((done) => setTimeout(done, ms));
function assert(ok, message) { if (!ok) throw new Error(message); }

async function main() {
  await stat(join(dist, "docs", "led-lamp", "index.html"));
  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url ?? "/", "http://127.0.0.1");
      const relative = normalize(decodeURIComponent(url.pathname)).replace(/^[/\\]+/u, "");
      let file = resolve(dist, relative);
      if (file !== dist && !file.startsWith(`${dist}${sep}`)) throw new Error("path traversal");
      if (url.pathname.endsWith("/") || extname(file) === "") file = join(file, "index.html");
      const bytes = await readFile(file);
      response.writeHead(200, { "content-type": mime[extname(file)] ?? "application/octet-stream" });
      response.end(bytes);
    } catch { response.writeHead(404); response.end("Not found"); }
  });
  await new Promise((done) => server.listen(0, "127.0.0.1", done));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const profile = await mkdtemp(join(tmpdir(), "zpd-site-navigation-"));
  const chrome = spawn(process.env.CHROME_BIN ?? (process.platform === "darwin" ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" : "google-chrome"), [
    "--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-extensions",
    "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });
  let cdp;
  try {
    let stderr = "";
    for await (const chunk of chrome.stderr) {
      stderr += chunk.toString();
      const match = /DevTools listening on ws:\/\/127\.0\.0\.1:(\d+)\//u.exec(stderr);
      if (match) { chrome.stderr.resume(); cdp = await connectCdp((await (await fetch(`http://127.0.0.1:${match[1]}/json/list`)).json()).find((target) => target.type === "page").webSocketDebuggerUrl); break; }
    }
    assert(cdp, `Chrome failed to start: ${stderr.slice(-1000)}`);
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Page.bringToFront");
    await cdp.send("Emulation.setFocusEmulationEnabled", { enabled: true });
    for (const width of [1440, 375]) {
      await cdp.send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width === 375 });
      await navigate(cdp, `${origin}/docs/led-lamp/`);
      if (width === 375) {
        await click(cdp, `document.querySelector('button[aria-label="Open sidebar"]')`);
        await waitFor(cdp, `document.querySelector('input[aria-label="Filter navigation"]')?.getBoundingClientRect().width > 0`);
        await delay(300);
        await click(cdp, `Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Back to main menu')`);
        await waitFor(cdp, `Array.from(document.querySelectorAll('header a[href], nav a[href]')).some(a => a.textContent.trim() === 'Project' && a.getBoundingClientRect().width > 0)`);
      }
      const links = await evaluate(cdp, `Array.from(document.querySelectorAll('header a[href], nav a[href]')).filter(a => a.getBoundingClientRect().width > 0).map(a => [a.textContent.trim(), a.getAttribute('href')])`);
      for (const [label, path] of categories) assert(links.some(([text, href]) => text === label && href === path), `${width}px: missing ${label} → ${path}; visible links ${JSON.stringify(links)}`);
      // Follow actual user-facing category links, not direct Page.navigate.
      for (const [label, path, heading] of categories) {
        await navigate(cdp, `${origin}/docs/led-lamp/`);
        if (width === 375) {
          await click(cdp, `document.querySelector('button[aria-label="Open sidebar"]')`);
          await waitFor(cdp, `document.querySelector('input[aria-label="Filter navigation"]')?.getBoundingClientRect().width > 0`);
          await delay(300);
          const categoryVisible = await evaluate(cdp, `Array.from(document.querySelectorAll('header a[href], nav a[href]')).some(a => a.textContent.trim() === ${JSON.stringify(label)} && a.getAttribute('href') === ${JSON.stringify(path)} && a.getBoundingClientRect().width > 0)`);
          if (!categoryVisible) await click(cdp, `Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Back to main menu' && b.getBoundingClientRect().width > 0)`);
        }
        await click(cdp, `Array.from(document.querySelectorAll('header a[href], nav a[href]')).find(a => a.textContent.trim() === ${JSON.stringify(label)} && a.getAttribute('href') === ${JSON.stringify(path)} && a.getBoundingClientRect().width > 0)`);
        await waitFor(cdp, `location.pathname.replace(/\\/$/, '') === ${JSON.stringify(path)}`);
        await waitFor(cdp, `document.querySelector('main h1')?.textContent.includes(${JSON.stringify(heading)})`);
      }
      await navigate(cdp, `${origin}/docs/catalog/lines/`);
      await waitFor(cdp, `document.querySelectorAll('main table tbody tr').length === 168`);
      await evaluate(cdp, `(() => { const select = document.querySelector('#catalog-line-status'); select.value = 'LED'; select.dispatchEvent(new Event('change', { bubbles: true })); })()`);
      await waitFor(cdp, `document.querySelector('#catalog-line-count')?.textContent === 'Showing 35 of 168 lines'`);
      assert(await evaluate(cdp, `Array.from(document.querySelectorAll('main table tbody tr:not([hidden])')).every(row => row.cells[0].textContent.trim().startsWith('LED:'))`), `${width}px: LED filter leaked PD lines`);
      await evaluate(cdp, `(() => { const query = document.querySelector('#catalog-line-query'); query.value = 'STUSB4500'; query.dispatchEvent(new Event('input', { bubbles: true })); })()`);
      await waitFor(cdp, `document.querySelector('#catalog-line-count')?.textContent === 'Showing 1 of 168 lines'`);
      assert(await evaluate(cdp, `document.querySelector('main table tbody tr:not([hidden])')?.cells[0].textContent.trim() === 'LED:line-c2678061'`), `${width}px: scoped LED conflict row missing`);
      await evaluate(cdp, `(() => { const select = document.querySelector('#catalog-line-status'); select.value = 'PD'; select.dispatchEvent(new Event('change', { bubbles: true })); })()`);
      await waitFor(cdp, `document.querySelector('#catalog-line-count')?.textContent === 'Showing 1 of 168 lines'`);
      assert(await evaluate(cdp, `document.querySelector('main table tbody tr:not([hidden])')?.cells[0].textContent.trim() === 'PD:line-c2678061'`), `${width}px: scoped PD conflict row missing`);
      if (width === 1440) {
        const authored = (await readFile(routeMap, 'utf8')).trim().split('\n').slice(1)
          .map((line) => line.split('\t')).filter((row) => row[4] === 'authored');
        assert(authored.length === 34, `Expected 34 authored routes, got ${authored.length}`);
        for (const [, oldRoute, proposedRoute] of authored) {
          await navigate(cdp, `${origin}${proposedRoute}`);
          await waitFor(cdp, `document.querySelector('main')?.textContent.includes('Historical LED page')`);
          const original = await evaluate(cdp, `Array.from(document.querySelectorAll('main a')).find(a => a.textContent.trim() === 'original LED page')?.href`);
          assert(original === `https://zudo-led-lamp.takazudomodular.com${oldRoute}`, `Authored route ${proposedRoute} lost source link: ${original}`);
        }
        for (const oldRoute of ['/docs/architecture/', '/docs/architecture/board-p/', '/docs/research/']) {
          await navigate(cdp, `${origin}${oldRoute}`);
          assert(await evaluate(cdp, `document.querySelector('main h1') !== null && !Array.from(document.querySelectorAll('main a')).some(a => a.textContent.trim() === 'original LED page')`), `PD collision route displaced: ${oldRoute}`);
        }
        console.log('PASS: 34 authored LED routes and 3 preserved PD collision routes');
      }
      console.log(`PASS: ${width}px 168-line scoped catalog filter`);
      await navigate(cdp, `${origin}/docs/led-lamp/`);
      await click(cdp, `document.querySelector('site-search button[aria-label="Search"]')`);
      await waitFor(cdp, `document.querySelector('site-search dialog')?.open === true`);
      await evaluate(cdp, `(() => { const input = document.querySelector('site-search dialog input'); input.value = 'board-p'; input.dispatchEvent(new Event('input', { bubbles: true })); })()`);
      await waitFor(cdp, `document.querySelector('site-search dialog a[href*="/docs/led-lamp/architecture/board-p"]')`, 15_000);
      const searchLinks = await evaluate(cdp, `Array.from(document.querySelectorAll('site-search dialog [data-search-results] a[href]')).map(a => new URL(a.href).pathname)`);
      assert(searchLinks.slice(0, 10).includes('/docs/architecture/board-p') && searchLinks.slice(0, 10).includes('/docs/led-lamp/architecture/board-p'), `${width}px: broad board-p query did not expose both PD and LED Board P pages in first batch: ${JSON.stringify(searchLinks)}`);
      await click(cdp, `document.querySelector('site-search dialog a[href*="/docs/led-lamp/architecture/board-p"]')`);
      await waitFor(cdp, `location.pathname.replace(/\\/$/, '') === '/docs/led-lamp/architecture/board-p'`);
      await waitFor(cdp, `Array.from(document.querySelectorAll('main a')).some(a => a.textContent.trim() === 'original LED page')`);
      const original = await evaluate(cdp, `Array.from(document.querySelectorAll('main a')).find(a => a.textContent.trim() === 'original LED page')?.href`);
      assert(original === "https://zudo-led-lamp.takazudomodular.com/docs/architecture/board-p/", `${width}px: incorrect original-page link ${original}`);
      const maintained = await evaluate(cdp, `Array.from(document.querySelectorAll('main a')).find(a => a.textContent.trim() === 'Maintained source')?.href`);
      assert(maintained?.includes("/Takazudo/zudo-pd/blob/") && maintained.endsWith("/products/led-lamp/doc/src/content/docs/architecture/board-p.mdx"), `${width}px: incorrect maintained-source link ${maintained}`);
      console.log(`PASS: ${width}px six categories, search → LED Board P, original and maintained source links`);
    }
  } finally {
    cdp?.close(); chrome.kill(); server.close();
    await Promise.race([new Promise((done) => chrome.once("exit", done)), delay(2000)]);
    await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 }).catch(() => {});
  }
}

async function connectCdp(url) {
  const socket = new WebSocket(url);
  await new Promise((done, reject) => { socket.addEventListener("open", done, { once: true }); socket.addEventListener("error", reject, { once: true }); });
  let nextId = 0; const pending = new Map();
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data); const entry = pending.get(message.id);
    if (!entry) return; pending.delete(message.id);
    if (message.error) entry.reject(new Error(`${entry.method}: ${message.error.message}`)); else entry.resolve(message.result);
  });
  return { send(method, params = {}) { const id = ++nextId; return new Promise((resolveSend, reject) => { pending.set(id, { resolve: resolveSend, reject, method }); socket.send(JSON.stringify({ id, method, params })); }); }, close() { socket.close(); } };
}
async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
  return result.result.value;
}
async function click(cdp, expression) {
  const target = await evaluate(cdp, `(() => { const element = ${expression}; if (!element) return null; element.scrollIntoView({ block: 'center', inline: 'center' }); const bounds = element.getBoundingClientRect(); const x = bounds.left + bounds.width / 2; const y = bounds.top + bounds.height / 2; return { x, y, width: bounds.width, height: bounds.height, hit: element === document.elementFromPoint(x, y) || element.contains(document.elementFromPoint(x, y)) }; })()`);
  assert(target?.width > 0 && target.height > 0 && target.hit, `Pointer target unavailable: ${expression}; ${JSON.stringify(target)}`);
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x: target.x, y: target.y, button: "left", clickCount: 1 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: target.x, y: target.y, button: "left", clickCount: 1 });
}
async function waitFor(cdp, expression, timeout = 10_000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) { if (await evaluate(cdp, `Boolean(${expression})`)) return; await delay(50); }
  throw new Error(`Timed out waiting for ${expression}; page=${await evaluate(cdp, "location.href")}; search=${JSON.stringify(await evaluate(cdp, "document.querySelector('site-search dialog')?.innerText?.slice(0, 1500)"))}`);
}
async function navigate(cdp, url) {
  await cdp.send("Page.navigate", { url });
  await waitFor(cdp, `location.pathname === ${JSON.stringify(new URL(url).pathname)} && document.readyState === 'complete'`);
}
await main();
