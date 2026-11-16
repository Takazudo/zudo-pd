// Run under the local Playwright guard. Set PLAYWRIGHT_MODULE if Playwright is
// supplied by an external tooling install rather than this project's node_modules.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const origin = process.env.ENCLOSURE_ORIGIN || "http://127.0.0.1:4387";
const output = resolve("public/assets/enclosure");
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const errors = [];
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 1 });
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("response", (response) => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
  await page.goto(`${origin}/assets/enclosure/index.html`);
  await page.waitForSelector('#viewport[data-ready="true"]', { timeout: 120000 });
  assert.equal(await page.locator("#layers-value").textContent(), "6 / 6");
  assert.equal(await page.locator("#viewport").getAttribute("data-visible-parts"), "25");
  await page.locator("#hardware").uncheck();
  assert.equal(await page.locator("#viewport").getAttribute("data-visible-parts"), "22");
  await page.locator("#hardware").check();
  for (const view of ["assembled", "exploded", "base", "underside"]) {
    await page.locator(`#${view}`).click();
    await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))));
    if (view === "exploded") assert.equal(await page.locator("#viewport").getAttribute("data-separation"), "4");
    if (view === "base") assert.equal(await page.locator("#layers-value").textContent(), "0 / 6");
    await page.locator(".stage").screenshot({ path: `${output}/${view}.png` });
  }
  await page.locator("#assembled").click();
  await page.locator("#part").selectOption("04-band");
  assert.equal(await page.locator("#viewport").getAttribute("data-visible-parts"), "1");
  assert.equal(await page.locator("#part-download").getAttribute("href"), "stl/04-band.stl");
  const download = page.waitForEvent("download");
  await page.locator("#part-download").click();
  assert.equal((await download).suggestedFilename(), "04-band.stl");
  await page.locator("#part").selectOption("post-01-flat");
  assert.match(await page.locator("#part-note").textContent(), /85\.4 × 4\.0 × 4\.0 mm/);
  await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))));
  await page.locator(".stage").screenshot({ path: `${output}/post-flat.png` });
  await page.locator("#assembled").click();
  await page.locator("#section").check();
  await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))));
  await page.locator(".stage").screenshot({ path: `${output}/section.png` });
  await page.setViewportSize({ width: 375, height: 850 });
  await page.locator("#assembled").click();
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "Mobile horizontal overflow");
  await page.screenshot({ path: `${output}/mobile.png`, fullPage: true });
  assert.deepEqual(errors, []);
  console.log("PASS: model loading, assembly/explosion/base presets, part isolation, STL download, section and mobile layout; no page/resource errors");
} finally {
  await browser.close();
}
