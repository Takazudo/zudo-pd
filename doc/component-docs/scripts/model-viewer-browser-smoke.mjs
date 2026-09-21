#!/usr/bin/env node

/**
 * The browser contract for the component-reference previews, against `dist/`.
 *
 * Node tests can prove the descriptor, the publication and the render branch;
 * they cannot prove that a real engine lays the cards out without overflow,
 * compiles the WRL into a canvas, keeps the render loop idle when nothing
 * moved, tears the WebGL context down on an SPA swap, or leaves a reader
 * without JavaScript a page that still says what it knows. That is what this
 * does, over CDP against headless Chrome — a plain node script driving the
 * DevTools protocol directly, with no browser-automation dependency.
 *
 * Exercises this project's passive, controller and connector records, plus
 * the explicit document gap and illustrative inductor model provenance.
 *
 * Requires `pnpm build` first, and a Chrome on PATH (or `CHROME_BIN`).
 */

import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { extname, join, normalize, resolve, sep } from "node:path";

const DIST = resolve("dist");
const RECORD = "/docs/components/records/stusb4500qtr/";
const AWAY = "/docs/components/catalog";
const REPRESENTATIVES = [
  { kind: "passive", path: "/docs/components/records/c1623/" },
  { kind: "IC", path: RECORD },
  { kind: "synth connector", path: "/docs/components/records/dealon-dw254p-2x8-l0-c4749189/" },
  { kind: "PD connector", path: "/docs/components/records/type-c-31-m-17/" },
  { kind: "input TVS", path: "/docs/components/records/c74561/" },
  { kind: "inverting rectifier", path: "/docs/components/records/c3024223/" },
  { kind: "screw terminal", path: "/docs/components/records/c8465/" },
  { kind: "PTC1", path: "/docs/components/records/ptc-smd1210p150tf16-c7529589/" },
  { kind: "PTC2", path: "/docs/components/records/ptc-msmd110-33v-c70119/" },
  { kind: "PTC3", path: "/docs/components/records/ptc-bsmd1206-150-16v-c883133/" },
  { kind: "illustrative inductor", path: "/docs/components/records/aspi-0630lr-100m-t15/", evidenceText: "not exact manufacturer CAD" },
  // The one record in this corpus with no manufacturer document at all. Its
  // model and footprint cards must still resolve in full.
  { kind: "document-less", path: "/docs/components/records/c335982/", documentResolved: false },
];
const VIEWPORTS = [1440, 375];
const THEMES = ["light", "dark"];
const ALLOWED_PDF_LABELS = ["Datasheet PDF", "Specification PDF", "Mechanical drawing PDF"];
const MIME = new Map([
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".css", "text/css; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".svg", "image/svg+xml"],
  [".wrl", "model/vrml"],
  [".wasm", "application/wasm"],
]);

const delay = (milliseconds) => new Promise((resolveDelay) => setTimeout(resolveDelay, milliseconds));

async function main() {
  await stat(join(DIST, "docs", "components", "records", "stusb4500qtr", "index.html"));
  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url ?? "/", "http://127.0.0.1");
      const relative = normalize(decodeURIComponent(url.pathname)).replace(/^[/\\]+/u, "");
      let file = resolve(DIST, relative);
      if (file !== DIST && !file.startsWith(`${DIST}${sep}`)) throw new Error("path traversal");
      if (url.pathname.endsWith("/") || extname(file) === "") file = join(file, "index.html");
      const bytes = await readFile(file);
      response.writeHead(200, { "content-type": MIME.get(extname(file)) ?? "application/octet-stream" });
      response.end(bytes);
    } catch {
      response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
      response.end("Not found");
    }
  });
  await new Promise((resolveListen) => server.listen(0, "127.0.0.1", resolveListen));
  const address = server.address();
  if (address === null || typeof address === "string") throw new Error("smoke server did not bind TCP");
  const origin = `http://127.0.0.1:${address.port}`;

  const profile = await mkdtemp(join(tmpdir(), "zpd-model-viewer-chrome-"));
  const executable = process.env.CHROME_BIN ?? "google-chrome";
  const chrome = spawn(executable, [
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    // An occluded headless renderer can pause rAF on desktop hosts, making
    // delivered pointer events appear inert. Keep this test target active.
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-backgrounding-occluded-windows",
    // No GPU in CI: SwiftShader is what makes the WebGL path testable at all.
    "--enable-unsafe-swiftshader",
    "--remote-debugging-port=0",
    `--user-data-dir=${profile}`,
    "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });

  try {
    const debuggingPort = await readDebuggingPort(chrome);
    chrome.stderr.resume();
    const targets = await waitForJson(`http://127.0.0.1:${debuggingPort}/json/list`);
    const page = targets.find((target) => target.type === "page");
    if (page?.webSocketDebuggerUrl === undefined) throw new Error("Chrome page target was not available");
    const cdp = await connectCdp(page.webSocketDebuggerUrl);
    try {
      await cdp.send("Page.enable");
      await cdp.send("Page.bringToFront");
      await cdp.send("Runtime.enable");
      await cdp.send("Network.enable");

      let inspected = 0;
      const lightThemeSignatures = new Map();
      for (const width of VIEWPORTS) {
        for (const theme of THEMES) {
          await setViewportAndMedia(cdp, width, theme, false);
          for (const representative of REPRESENTATIVES) {
            await navigate(cdp, origin, representative.path);
            await setDocumentTheme(cdp, theme);
            const report = await inspectReferencePage(cdp, representative, width, theme);
            const signatureKey = `${width}:${representative.kind}`;
            if (theme === "light") lightThemeSignatures.set(signatureKey, report.themeSignature);
            else assertEqual(
              report.themeSignature !== lightThemeSignatures.get(signatureKey),
              true,
              `${representative.kind} ${width} light/dark computed colors differ`,
            );
            inspected += 1;
          }
        }
      }

      await setViewportAndMedia(cdp, 375, "dark", false, 812, 2);
      await navigate(cdp, origin, RECORD);
      await setDocumentTheme(cdp, "dark");
      await revealReadyViewer(cdp);
      await exerciseDialogGeometry(cdp, 375, 812);

      await setViewportAndMedia(cdp, 1440, "light", false);
      await navigate(cdp, origin, RECORD);
      await setDocumentTheme(cdp, "light");
      await revealReadyViewer(cdp);
      await exerciseFootprintDialog(cdp);
      await exerciseModelDialog(cdp);
      await exerciseViewerInteractions(cdp);

      // No continuous animation loop: after interaction/resize settles, the
      // diagnostic render count stays unchanged without input.
      await delay(300);
      const renders = await renderCount(cdp);
      await delay(500);
      assertEqual(await renderCount(cdp), renders, "render-on-demand remains idle");

      await setViewportAndMedia(cdp, 1440, "dark", true);
      assertEqual(await evaluate(cdp, `matchMedia('(prefers-reduced-motion: reduce)').matches`), true, "reduced-motion media active");
      const reducedDurations = await evaluate(cdp, `(() => {
        const target = document.querySelector('[data-model-viewer-viewport]');
        const style = getComputedStyle(target);
        return { animation: style.animationDuration, transition: style.transitionDuration };
      })()`);
      assertDurationAtMost(reducedDurations.animation, 0.001, "reduced-motion animation duration");
      assertDurationAtMost(reducedDurations.transition, 0.001, "reduced-motion transition duration");

      await evaluate(cdp, `document.querySelector('[data-component-preview-enlarge="model"]').click()`);
      await waitFor(cdp, `document.querySelector('[data-model-viewer-instance="dialog"]')?.dataset.viewerState === 'ready'`, 20_000);
      await evaluate(cdp, `
        window.__zpdOldViewers = [...document.querySelectorAll('[data-component-model-viewer-root]')];
        window.__zpdOldCanvases = window.__zpdOldViewers.map((viewer) => viewer.querySelector('canvas'));
        document.querySelector('a[href=${JSON.stringify(AWAY)}]').click();
      `);
      await waitFor(cdp, `location.pathname === ${JSON.stringify(AWAY)}`);
      await waitFor(cdp, `window.__zpdOldViewers?.every((viewer) => viewer.dataset.viewerDisposed === 'true')`);
      assertEqual(await evaluate(cdp, `window.__zpdOldViewers?.length`), 2, "SPA navigation started with inline and dialog viewers");
      assertEqual(await evaluate(cdp, `window.__zpdOldCanvases?.every((canvas) => !canvas?.isConnected)`), true, "inline and dialog canvases detached on SPA swap");
      // The dialog itself must not survive the swap in the native top layer.
      assertEqual(await evaluate(cdp, `[...document.querySelectorAll('[data-component-preview-dialog]')].every((dialog) => !dialog.open)`), true, "SPA navigation closed the enlarge dialog");

      await evaluate(cdp, "history.back()");
      await waitFor(cdp, `location.pathname === ${JSON.stringify(RECORD)}`);
      await revealReadyViewer(cdp);
      assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-component-model-viewer-root]').length`), 1, "one viewer root after SPA back");
      assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-model-viewer-viewport] canvas').length`), 1, "one canvas after SPA back");
      assertEqual(await evaluate(cdp, `window.__zpdOldViewers?.includes(document.querySelector('[data-component-model-viewer-root]'))`), false, "fresh viewer after SPA back");

      await navigate(cdp, origin, `${RECORD}?model-viewer-model=fail`);
      await revealViewer(cdp);
      await waitFor(cdp, `document.querySelector('[data-component-model-viewer-root]')?.dataset.viewerState === 'error'`);
      assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-model-viewer-viewport] canvas').length`), 0, "no canvas after model load failure");
      // The runtime's own message is overwritten by the island's catch branch,
      // which is the one a reader actually ends up with.
      assertEqual(await evaluate(cdp, `document.querySelector('[data-model-viewer-status]')?.textContent.includes('package reference')`), true, "meaningful model-load fallback");
      assertEqual(await evaluate(cdp, `getComputedStyle(document.querySelector('[data-component-preview-enlarge="model"]')).display`), "none", "model enlarge hidden after model load failure");

      await navigate(cdp, origin, `${RECORD}?model-viewer-webgl=fail`);
      await revealViewer(cdp);
      await waitFor(cdp, `document.querySelector('[data-component-model-viewer-root]')?.dataset.viewerState === 'unavailable'`);
      assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-model-viewer-viewport] canvas').length`), 0, "no canvas after forced WebGL failure");
      assertEqual(await evaluate(cdp, `document.querySelector('[data-model-viewer-status]')?.textContent.includes('WebGL is unavailable')`), true, "meaningful WebGL fallback");
      assertEqual(await evaluate(cdp, `getComputedStyle(document.querySelector('[data-component-preview-enlarge="model"]')).display`), "none", "model enlarge hidden without WebGL");

      await cdp.send("Emulation.setScriptExecutionDisabled", { value: true });
      await navigate(cdp, origin, REPRESENTATIVES[0].path);
      await revealViewer(cdp);
      assertEqual(await evaluate(cdp, `document.querySelector('[data-component-model-viewer-root]')?.dataset.viewerState`), "no-js", "no-JS state retained");
      assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-model-viewer-viewport] canvas').length`), 0, "no canvas without JavaScript");
      assertEqual(await evaluate(cdp, `document.querySelector('[data-model-viewer-status]')?.textContent.includes('requires JavaScript and WebGL')`), true, "no-JS explanation retained");
      await waitFor(cdp, `document.querySelector('.zld-component-references__footprint img')?.complete && document.querySelector('.zld-component-references__footprint img')?.naturalWidth > 0`);
      const noJsPreviews = await evaluate(cdp, `({
        controlsHidden: [...document.querySelectorAll('[data-component-preview-enlarge]')].every((control) => getComputedStyle(control).display === 'none'),
        dialogsClosed: [...document.querySelectorAll('[data-component-preview-dialog]')].every((dialog) => !dialog.open),
        footprintLink: document.querySelector('.zld-component-references__footprint-frame > a')?.href.endsWith('.svg')
      })`);
      assertEqual(noJsPreviews.controlsHidden, true, "no-JS enlarge controls hidden");
      assertEqual(noJsPreviews.dialogsClosed, true, "no-JS dialogs closed");
      assertEqual(noJsPreviews.footprintLink, true, "no-JS footprint direct link retained");
      await cdp.send("Emulation.setScriptExecutionDisabled", { value: false });

      await setViewportAndMedia(cdp, 1440, "light", false);
      await navigate(cdp, origin, `${AWAY}/`);
      await delay(500); // wait-ok: this is an intentional absence-window assertion.
      const catalogState = await evaluate(cdp, `({
        viewers: document.querySelectorAll('[data-component-model-viewer-root]').length,
        canvases: document.querySelectorAll('canvas').length,
        previewDialogs: document.querySelectorAll('[data-component-preview-dialog]').length,
        previewTriggers: document.querySelectorAll('[data-component-preview-enlarge]').length,
        modelResources: performance.getEntriesByType('resource').filter((entry) => entry.name.includes('/assets/component-previews/models/')).length,
        modelMarkers: document.documentElement.innerHTML.includes('data-model-url')
      })`);
      assertEqual(catalogState.viewers, 0, "catalog has no viewer root");
      assertEqual(catalogState.canvases, 0, "catalog has no canvas");
      assertEqual(catalogState.previewDialogs, 0, "catalog has no preview dialogs");
      assertEqual(catalogState.previewTriggers, 0, "catalog has no preview triggers");
      assertEqual(catalogState.modelResources, 0, "catalog loads no model resource");
      assertEqual(catalogState.modelMarkers, false, "catalog has no model descriptor");

      // Nothing the viewer needs may come from another origin: `three` is a
      // bundled dependency, and the WRL is a published site asset.
      const origins = await evaluate(cdp, `[...new Set(performance.getEntriesByType('resource').map((entry) => new URL(entry.name).origin))]`);
      assertEqual(origins.every((entry) => entry === origin), true, `every resource is same-origin (saw ${JSON.stringify(origins)})`);

      process.stdout.write(`component reference browser smoke passed: ${inspected} responsive/theme cases, footprint/model dialogs, interactions, focus, on-demand idle, SPA cleanup, fallbacks, no-JS, viewer-free catalog, same-origin only\n`);
    } catch (error) {
      const diagnostics = await evaluate(cdp, `({
        href: location.href,
        state: document.querySelector('[data-component-model-viewer-root]')?.dataset.viewerState,
        status: document.querySelector('[data-model-viewer-status]')?.textContent,
        canvases: document.querySelectorAll('[data-model-viewer-viewport] canvas').length,
        readyState: document.readyState,
        marker: document.querySelector('[data-zfb-island="PackageModelViewerIsland"]')?.outerHTML.slice(0, 300),
        bounds: document.querySelector('[data-zfb-island="PackageModelViewerIsland"]')?.getBoundingClientRect().toJSON(),
        scripts: [...document.scripts].map((script) => script.src || 'inline').slice(-10),
        resources: performance.getEntriesByType('resource').map((entry) => entry.name).filter((name) => name.includes('island'))
      })`).catch(() => null);
      throw new Error(`${error.message}; browser diagnostics: ${JSON.stringify(diagnostics)}`, { cause: error });
    } finally {
      cdp.close();
    }
  } finally {
    chrome.kill("SIGTERM");
    await waitForExit(chrome);
    server.close();
    await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
  }
}

async function setViewportAndMedia(cdp, width, theme, reducedMotion, height = 900, deviceScaleFactor = 1) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor,
    mobile: false,
    screenWidth: width,
    screenHeight: height,
  });
  await cdp.send("Emulation.setEmulatedMedia", {
    media: "screen",
    features: [
      { name: "prefers-color-scheme", value: theme },
      { name: "prefers-reduced-motion", value: reducedMotion ? "reduce" : "no-preference" },
    ],
  });
}

async function navigate(cdp, origin, path) {
  const target = new URL(path, origin);
  await cdp.send("Page.navigate", { url: target.href });
  await waitFor(cdp, `location.pathname === ${JSON.stringify(target.pathname)} && location.search === ${JSON.stringify(target.search)}`);
  await waitFor(cdp, `document.readyState === 'complete'`);
}

async function setDocumentTheme(cdp, theme) {
  await evaluate(cdp, `(() => {
    document.documentElement.dataset.theme = ${JSON.stringify(theme)};
    document.documentElement.style.colorScheme = ${JSON.stringify(theme)};
  })()`);
  assertEqual(await evaluate(cdp, `document.documentElement.dataset.theme`), theme, `${theme} theme marker`);
  assertEqual(
    await evaluate(cdp, `matchMedia('(prefers-color-scheme: ${theme})').matches`),
    true,
    `${theme} color-scheme media`,
  );
}

async function inspectReferencePage(cdp, representative, width, theme) {
  await waitFor(cdp, `document.querySelector('.zld-component-references') !== null`);
  await evaluate(cdp, `document.querySelector('.zld-component-references').scrollIntoView({ block: 'start' })`);
  await waitFor(cdp, `document.querySelector('.zld-component-references__footprint img')?.complete && document.querySelector('.zld-component-references__footprint img')?.naturalWidth > 0`);
  await revealReadyViewer(cdp);
  const report = await evaluate(cdp, `(() => {
    const section = document.querySelector('.zld-component-references');
    const cards = [...section.querySelectorAll('.zld-component-references__card')];
    const footprintLink = section.querySelector('.zld-component-references__footprint-frame > a');
    const footprintImage = footprintLink.querySelector('img');
    const modelViewport = section.querySelector('[data-model-viewer-viewport]');
    const modelRoot = section.querySelector('[data-component-model-viewer-root]');
    const modelCaption = modelRoot.querySelector('.zld-model-viewer__caption');
    const footprintTrigger = section.querySelector('[data-component-preview-enlarge="footprint"]');
    const modelTrigger = section.querySelector('[data-component-preview-enlarge="model"]');
    const documentLink = section.querySelector('.zld-component-references__document-title a');
    const label = section.querySelector('.zld-component-references__document-label');
    const metadata = [...section.querySelectorAll('.zld-component-references__metadata > div')];
    const availability = metadata.find((row) => row.querySelector('dt')?.textContent.trim() === 'Availability')?.querySelector('dd')?.textContent.trim();
    const evidence = document.querySelector('.zld-evidence-table');
    const rect = (element) => {
      const value = element.getBoundingClientRect();
      return { left: value.left, right: value.right, top: value.top, bottom: value.bottom, width: value.width, height: value.height };
    };
    const sectionRect = rect(section);
    const cardRects = cards.map(rect);
    const footprintRect = rect(footprintLink);
    const imageRect = rect(footprintImage);
    const modelRect = rect(modelViewport);
    const cardStyle = getComputedStyle(cards[0]);
    const status = section.querySelector('[data-model-viewer-status]');
    const statusStyle = getComputedStyle(status);
    return {
      viewport: { inner: innerWidth, client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth },
      sectionRect,
      cardRects,
      footprintRect,
      imageRect,
      modelRect,
      captionRect: rect(modelCaption),
      captionPackage: modelCaption.textContent.replace('Shared footprint package:', '').trim(),
      captionOverflows: modelCaption.scrollWidth > modelCaption.clientWidth + 1,
      footprintTrigger: {
        rect: rect(footprintTrigger),
        display: getComputedStyle(footprintTrigger).display,
        label: footprintTrigger.getAttribute('aria-label'),
      },
      modelTrigger: {
        rect: rect(modelTrigger),
        display: getComputedStyle(modelTrigger).display,
        label: modelTrigger.getAttribute('aria-label'),
      },
      dialogs: [...section.querySelectorAll('[data-component-preview-dialog]')].map((dialog) => ({
        kind: dialog.dataset.componentPreviewDialog,
        open: dialog.open,
        labelResolves: document.getElementById(dialog.getAttribute('aria-labelledby')) !== null,
      })),
      documentLabel: label?.textContent.trim(),
      documentHref: documentLink?.href,
      unresolvedReasons: [...section.querySelectorAll('[data-reference-unresolved]')]
        .map((element) => element.textContent.replace(/^\\s*Unresolved\\.\\s*/u, '').trim()),
      availability,
      footprintObjectFit: getComputedStyle(footprintImage).objectFit,
      footprintNatural: [footprintImage.naturalWidth, footprintImage.naturalHeight],
      modelUrl: modelRoot?.dataset.modelUrl,
      viewerRoots: section.querySelectorAll('[data-component-model-viewer-root]').length,
      statusVisible: statusStyle.display !== 'none' && statusStyle.visibility !== 'hidden' && Number(statusStyle.opacity) > 0,
      cardColorsDistinct: cardStyle.color !== cardStyle.backgroundColor,
      themeSignature: [getComputedStyle(document.body).color, getComputedStyle(document.body).backgroundColor, cardStyle.color, cardStyle.backgroundColor].join('|'),
      sectionBeforeEvidence: evidence !== null && Boolean(section.compareDocumentPosition(evidence) & Node.DOCUMENT_POSITION_FOLLOWING),
      sourcesPresent: document.getElementById('sources') !== null,
      pageText: document.body.innerText,
      theme: document.documentElement.dataset.theme,
    };
  })()`);

  if (representative.evidenceText !== undefined) {
    assertEqual(report.pageText.includes(representative.evidenceText), true, `${representative.kind} retains illustrative provenance`);
  }
  assertEqual(report.viewport.inner, width, `${representative.kind} ${width}/${theme} viewport width`);
  assertEqual(report.viewport.scroll <= report.viewport.client + 1, true, `${representative.kind} ${width}/${theme} page overflow`);
  if (representative.documentResolved === false) {
    // The optional-card fork: an unresolved card names its reason and never
    // pretends to a destination.
    assertEqual(report.documentHref, undefined, `${representative.kind} unresolved document has no destination`);
    assertEqual(report.unresolvedReasons.length, 1, `${representative.kind} unresolved card count`);
    assertEqual(report.unresolvedReasons.every((reason) => reason.length > 0), true, `${representative.kind} unresolved reason is stated`);
  } else {
    assertEqual(report.unresolvedReasons.length, 0, `${representative.kind} resolves every card`);
    assertEqual(ALLOWED_PDF_LABELS.includes(report.documentLabel), true, `${representative.kind} PDF label`);
    assertEqual(/^https?:\/\//u.test(report.documentHref), true, `${representative.kind} PDF destination`);
  }
  if (representative.availability !== undefined) {
    assertEqual(report.availability, representative.availability, `${representative.kind} availability`);
  }
  assertEqual(report.footprintObjectFit, "contain", `${representative.kind} footprint containment mode`);
  assertEqual(report.footprintNatural.every((value) => value > 0), true, `${representative.kind} footprint loaded`);
  assertEqual(report.viewerRoots, 1, `${representative.kind} viewer root count`);
  assertEqual(report.modelUrl?.endsWith(".wrl"), true, `${representative.kind} selected WRL`);
  assertEqual(report.modelUrl?.toLowerCase().endsWith(".step"), false, `${representative.kind} no STEP URL`);
  assertEqual(report.footprintTrigger.display !== "none", true, `${representative.kind} footprint enlarge visible after hydration`);
  assertEqual(report.modelTrigger.display !== "none", true, `${representative.kind} model enlarge visible when ready`);
  assertEqual(report.footprintTrigger.label.startsWith("Enlarge footprint preview"), true, `${representative.kind} footprint enlarge label`);
  assertEqual(report.modelTrigger.label.startsWith("Enlarge 3D preview"), true, `${representative.kind} model enlarge label`);
  assertEqual(report.dialogs.length, 2, `${representative.kind} closed dialog shell count`);
  assertEqual(report.dialogs.every((dialog) => !dialog.open && dialog.labelResolves), true, `${representative.kind} closed dialogs are labeled`);
  assertEqual(report.statusVisible, true, `${representative.kind} visible status`);
  assertEqual(report.cardColorsDistinct, true, `${representative.kind} readable card colors`);
  assertEqual(report.sectionBeforeEvidence, true, `${representative.kind} references before evidence`);
  assertEqual(report.sourcesPresent, true, `${representative.kind} Sources retained`);
  assertEqual(report.theme, theme, `${representative.kind} ${theme} theme retained`);

  for (const [index, card] of report.cardRects.entries()) {
    assertContained(card, report.sectionRect, `${representative.kind} card ${index + 1} at ${width}/${theme}`);
  }
  const footprintCard = report.cardRects[1];
  const modelCard = report.cardRects[2];
  assertContained(report.footprintRect, footprintCard, `${representative.kind} footprint at ${width}/${theme}`);
  assertContained(report.imageRect, report.footprintRect, `${representative.kind} footprint image at ${width}/${theme}`);
  assertContained(report.modelRect, modelCard, `${representative.kind} model viewport at ${width}/${theme}`);
  assertContained(report.captionRect, modelCard, `${representative.kind} model caption at ${width}/${theme}`);
  assertEqual(report.captionOverflows, false, `${representative.kind} package name wraps within caption`);
  assertEqual(report.modelTrigger.label, `Enlarge 3D preview for ${report.captionPackage}`, `${representative.kind} wrapped package identity remains complete`);
  assertContained(report.footprintTrigger.rect, report.footprintRect, `${representative.kind} footprint enlarge at ${width}/${theme}`);
  assertContained(report.modelTrigger.rect, report.modelRect, `${representative.kind} model enlarge at ${width}/${theme}`);
  assertEqual(report.footprintTrigger.rect.width >= 44 && report.footprintTrigger.rect.height >= 44, true, `${representative.kind} footprint target size`);
  assertEqual(report.modelTrigger.rect.width >= 44 && report.modelTrigger.rect.height >= 44, true, `${representative.kind} model target size`);
  const columns = new Set(report.cardRects.map((rect) => Math.round(rect.left)));
  if (width === 375) assertEqual(columns.size, 1, `${representative.kind} cards stack at mobile width`);
  else assertEqual(columns.size >= 2, true, `${representative.kind} cards use desktop width`);

  const loaded = await evaluate(cdp, `({
    canvases: document.querySelectorAll('[data-model-viewer-viewport] canvas').length,
    ready: document.querySelector('[data-model-viewer-status]')?.textContent.includes('ready'),
    modelResources: performance.getEntriesByType('resource').map((entry) => entry.name).filter((name) => name.includes('/assets/component-previews/models/'))
  })`);
  assertEqual(loaded.canvases, 1, `${representative.kind} canvas after load`);
  assertEqual(loaded.ready, true, `${representative.kind} ready status`);
  assertEqual(loaded.modelResources.length >= 1, true, `${representative.kind} model requested`);
  assertEqual(loaded.modelResources.every((url) => url.endsWith(".wrl")), true, `${representative.kind} only WRL requested`);
  return report;
}

async function revealReadyViewer(cdp) {
  await revealViewer(cdp);
  await waitFor(cdp, `document.querySelector('[data-component-model-viewer-root]')?.dataset.viewerState === 'ready'`, 20_000);
  assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-component-model-viewer-root]').length`), 1, "one viewer root after load");
  assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-model-viewer-viewport] canvas').length`), 1, "one canvas after load");
}

async function exerciseDialogGeometry(cdp, width, height) {
  for (const kind of ["footprint", "model"]) {
    const triggerSelector = `[data-component-preview-enlarge="${kind}"]`;
    const dialogSelector = `[data-component-preview-dialog="${kind}"]`;
    await waitFor(cdp, `getComputedStyle(document.querySelector(${JSON.stringify(triggerSelector)})).display !== 'none'`);
    if (kind === "model") {
      await evaluate(cdp, `(() => {
        window.__zpdDialogReadyRenderCount = null;
        const observer = new MutationObserver(() => {
          const root = document.querySelector('[data-model-viewer-instance="dialog"]');
          if (root?.dataset.viewerState !== 'ready') return;
          window.__zpdDialogReadyRenderCount = Number(root.dataset.renderCount ?? 0);
          observer.disconnect();
        });
        observer.observe(document.querySelector(${JSON.stringify(dialogSelector)}), {
          subtree: true,
          childList: true,
          attributes: true,
          attributeFilter: ['data-viewer-state'],
        });
      })()`);
    }
    await evaluate(cdp, `document.querySelector(${JSON.stringify(triggerSelector)}).click()`);
    await waitFor(cdp, `document.querySelector(${JSON.stringify(dialogSelector)})?.open`);
    if (kind === "model") {
      await waitFor(cdp, `document.querySelector('[data-model-viewer-instance="dialog"]')?.dataset.viewerState === 'ready'`, 20_000);
      await waitFor(cdp, `window.__zpdDialogReadyRenderCount !== null`);
      // The message -> render -> `ready` ordering in `viewer-runtime.ts`, seen
      // from outside: `ready` is never published before a render happened.
      assertEqual(await evaluate(cdp, `window.__zpdDialogReadyRenderCount > 0`), true, "model ready state is published after its first render");
      await waitForCanvasSize(cdp, "dialog");
    }

    const report = await evaluate(cdp, `(() => {
      const dialog = document.querySelector(${JSON.stringify(dialogSelector)});
      const close = dialog.querySelector('.zld-preview-dialog__close');
      const content = dialog.querySelector('.zld-preview-dialog__content');
      const label = document.getElementById(dialog.getAttribute('aria-labelledby'));
      const rect = (element) => {
        const value = element.getBoundingClientRect();
        return { left: value.left, right: value.right, top: value.top, bottom: value.bottom, width: value.width, height: value.height };
      };
      const image = dialog.querySelector('img');
      const modelViewport = dialog.querySelector('[data-model-viewer-viewport]');
      const canvas = modelViewport?.querySelector('canvas');
      return {
        modal: dialog.matches(':modal'),
        labelResolved: Boolean(label?.textContent.trim()),
        viewport: { width: innerWidth, height: innerHeight },
        pageOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
        dialogOverflow: dialog.scrollWidth > dialog.clientWidth + 1,
        dialog: rect(dialog),
        close: rect(close),
        content: rect(content),
        image: image ? { rect: rect(image), objectFit: getComputedStyle(image).objectFit } : null,
        model: modelViewport && canvas ? {
          viewport: rect(modelViewport),
          clientWidth: modelViewport.clientWidth,
          clientHeight: modelViewport.clientHeight,
          canvas: rect(canvas),
          pixelWidth: canvas.width,
          pixelHeight: canvas.height,
          ratio: devicePixelRatio,
        } : null,
      };
    })()`);
    const viewportRect = { left: 0, top: 0, right: report.viewport.width, bottom: report.viewport.height, width: report.viewport.width, height: report.viewport.height };
    assertEqual(Math.round(report.viewport.width), width, `${kind} dialog visual viewport width`);
    assertEqual(Math.round(report.viewport.height), height, `${kind} dialog visual viewport height`);
    assertEqual(report.modal, true, `${kind} dialog is in the native modal top layer`);
    assertEqual(report.labelResolved, true, `${kind} dialog accessible label resolves`);
    assertEqual(report.pageOverflow, false, `${kind} dialog causes no page overflow`);
    assertEqual(report.dialogOverflow, false, `${kind} dialog causes no internal horizontal overflow`);
    assertEqual(await evaluate(cdp, `getComputedStyle(document.documentElement).overflowY`), "hidden", `${kind} dialog locks background scrolling`);
    const scrollY = await evaluate(cdp, "window.scrollY");
    await cdp.send("Input.dispatchMouseEvent", { type: "mouseWheel", x: 0, y: Math.round(height / 2), deltaX: 0, deltaY: 600 });
    await delay(100);
    assertEqual(Math.round(await evaluate(cdp, "window.scrollY")), Math.round(scrollY), `${kind} backdrop wheel leaves page scroll unchanged`);
    assertContained(report.dialog, viewportRect, `${kind} dialog at ${width}x${height}`);
    assertContained(report.close, viewportRect, `${kind} close control at ${width}x${height}`);
    assertContained(report.content, report.dialog, `${kind} dialog content at ${width}x${height}`);
    assertEqual(report.close.width >= 44 && report.close.height >= 44, true, `${kind} dialog close target is at least 44px`);
    if (kind === "footprint") {
      assertEqual(report.image?.objectFit, "contain", "enlarged footprint uses contain sizing");
      assertContained(report.image.rect, report.content, `enlarged footprint at ${width}x${height}`);
    } else {
      assertEqual(report.model !== null, true, "enlarged model has a live canvas");
      assertContained(report.model.viewport, report.content, `enlarged model viewport at ${width}x${height}`);
      assertContained(report.model.canvas, report.model.viewport, `enlarged model canvas at ${width}x${height}`);
      const expectedWidth = report.model.clientWidth * report.model.ratio;
      const expectedHeight = report.model.clientHeight * report.model.ratio;
      assertEqual(Math.abs(report.model.pixelWidth - expectedWidth) <= Math.max(4, expectedWidth * 0.01), true, "enlarged model pixel width tracks DPR2 viewport");
      assertEqual(Math.abs(report.model.pixelHeight - expectedHeight) <= Math.max(4, expectedHeight * 0.01), true, "enlarged model pixel height tracks DPR2 viewport");
    }
    await evaluate(cdp, `document.querySelector(${JSON.stringify(dialogSelector)}).querySelector('.zld-preview-dialog__close').click()`);
    await waitFor(cdp, `!document.querySelector(${JSON.stringify(dialogSelector)})?.open`);
    if (kind === "model") {
      await waitFor(cdp, `document.querySelectorAll('[data-model-viewer-instance="dialog"]').length === 0`);
    }
    await waitFor(cdp, `document.activeElement === document.querySelector(${JSON.stringify(triggerSelector)})`);
  }
}

async function exerciseFootprintDialog(cdp) {
  const triggerSelector = '[data-component-preview-enlarge="footprint"]';
  const dialogSelector = '[data-component-preview-dialog="footprint"]';
  await waitFor(cdp, `getComputedStyle(document.querySelector(${JSON.stringify(triggerSelector)})).display !== 'none'`);
  const trigger = await evaluate(cdp, `(() => {
    const element = document.querySelector(${JSON.stringify(triggerSelector)});
    const rect = element.getBoundingClientRect();
    return { tag: element.tagName, width: rect.width, height: rect.height, label: element.getAttribute('aria-label') };
  })()`);
  assertEqual(trigger.tag, "BUTTON", "footprint enlarge uses a native button");
  assertEqual(trigger.width >= 44 && trigger.height >= 44, true, "footprint enlarge target is at least 44px");
  assertEqual(trigger.label.startsWith("Enlarge footprint preview"), true, "footprint enlarge has a specific accessible name");

  assertEqual(await evaluate(cdp, `document.activeElement !== document.querySelector(${JSON.stringify(triggerSelector)})`), true, "footprint pointer-style activation begins without trigger focus");
  await evaluate(cdp, `document.querySelector(${JSON.stringify(triggerSelector)}).click()`);
  await waitFor(cdp, `document.querySelector(${JSON.stringify(dialogSelector)})?.open`);
  assertEqual(await evaluate(cdp, `document.activeElement === document.querySelector(${JSON.stringify(dialogSelector)}).querySelector('.zld-preview-dialog__close')`), true, "footprint dialog moves focus to close");
  assertEqual(await evaluate(cdp, `document.querySelector(${JSON.stringify(dialogSelector)}).matches(':modal')`), true, "footprint dialog is modal");
  assertEqual(await evaluate(cdp, `document.querySelector(${JSON.stringify(dialogSelector)}).querySelector('img')?.alt.startsWith('Footprint preview for ')`), true, "enlarged footprint retains alt text");
  const layout = await evaluate(cdp, `(() => {
    const content = document.querySelector(${JSON.stringify(dialogSelector)}).querySelector('.zld-preview-dialog__content');
    const image = content.querySelector(':scope > img');
    const rect = (element) => {
      const value = element.getBoundingClientRect();
      return { left: value.left, right: value.right, top: value.top, bottom: value.bottom, width: value.width, height: value.height };
    };
    return {
      content: rect(content),
      image: rect(image),
      overflow: content.scrollWidth > content.clientWidth + 1 || content.scrollHeight > content.clientHeight + 1,
    };
  })()`);
  assertContained(layout.image, layout.content, "desktop enlarged footprint");
  assertEqual(layout.overflow, false, "desktop enlarged footprint has no internal overflow");

  await pressKey(cdp, "Tab", "Tab", 9);
  assertEqual(await evaluate(cdp, `document.querySelector(${JSON.stringify(dialogSelector)}).contains(document.activeElement)`), true, "forward Tab remains in footprint dialog");
  await pressKey(cdp, "Tab", "Tab", 9, 8);
  assertEqual(await evaluate(cdp, `document.querySelector(${JSON.stringify(dialogSelector)}).contains(document.activeElement)`), true, "reverse Tab remains in footprint dialog");

  await pressKey(cdp, "Escape", "Escape", 27);
  await waitFor(cdp, `!document.querySelector(${JSON.stringify(dialogSelector)})?.open && !document.querySelector(${JSON.stringify(dialogSelector)})?.querySelector('img')`);
  assertEqual(await evaluate(cdp, `document.activeElement === document.querySelector(${JSON.stringify(triggerSelector)})`), true, "Escape restores footprint trigger focus");

  await evaluate(cdp, `document.querySelector(${JSON.stringify(triggerSelector)}).click()`);
  await waitFor(cdp, `document.querySelector(${JSON.stringify(dialogSelector)})?.open`);
  await clickAt(cdp, 0, 0);
  await waitFor(cdp, `!document.querySelector(${JSON.stringify(dialogSelector)})?.open && !document.querySelector(${JSON.stringify(dialogSelector)})?.querySelector('img')`);
  assertEqual(await evaluate(cdp, `document.activeElement === document.querySelector(${JSON.stringify(triggerSelector)})`), true, "backdrop close restores footprint trigger focus");

  await evaluate(cdp, `document.querySelector(${JSON.stringify(triggerSelector)}).click()`);
  await waitFor(cdp, `document.querySelector(${JSON.stringify(dialogSelector)})?.open`);
  await evaluate(cdp, `document.querySelector(${JSON.stringify(dialogSelector)}).querySelector('.zld-preview-dialog__close').click()`);
  await waitFor(cdp, `!document.querySelector(${JSON.stringify(dialogSelector)})?.open && !document.querySelector(${JSON.stringify(dialogSelector)})?.querySelector('img')`);
  assertEqual(await evaluate(cdp, `document.activeElement === document.querySelector(${JSON.stringify(triggerSelector)})`), true, "close button restores footprint trigger focus");
  assertEqual(await evaluate(cdp, `location.pathname === ${JSON.stringify(RECORD)}`), true, "footprint enlarge never navigates to the raw SVG");
}

async function exerciseModelDialog(cdp) {
  const triggerSelector = '[data-component-preview-enlarge="model"]';
  const dialogSelector = '[data-component-preview-dialog="model"]';
  await waitFor(cdp, `getComputedStyle(document.querySelector(${JSON.stringify(triggerSelector)})).display !== 'none'`);
  const trigger = await evaluate(cdp, `(() => {
    const element = document.querySelector(${JSON.stringify(triggerSelector)});
    const rect = element.getBoundingClientRect();
    return { tag: element.tagName, width: rect.width, height: rect.height, label: element.getAttribute('aria-label') };
  })()`);
  assertEqual(trigger.tag, "BUTTON", "model enlarge uses a native button");
  assertEqual(trigger.width >= 44 && trigger.height >= 44, true, "model enlarge target is at least 44px");
  assertEqual(trigger.label.startsWith("Enlarge 3D preview"), true, "model enlarge has a specific accessible name");

  assertEqual(await evaluate(cdp, `document.activeElement !== document.querySelector(${JSON.stringify(triggerSelector)})`), true, "model pointer-style activation begins without trigger focus");
  await evaluate(cdp, `document.querySelector(${JSON.stringify(triggerSelector)}).click()`);
  await waitFor(cdp, `document.querySelector(${JSON.stringify(dialogSelector)})?.open`);
  await waitFor(cdp, `document.querySelector('[data-model-viewer-instance="dialog"]')?.dataset.viewerState === 'ready'`, 20_000);
  assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-component-model-viewer-root]').length`), 2, "model dialog mounts one temporary viewer");
  assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-model-viewer-viewport] canvas').length`), 2, "model dialog mounts one temporary canvas");
  assertEqual(await evaluate(cdp, `document.activeElement === document.querySelector(${JSON.stringify(dialogSelector)}).querySelector('.zld-preview-dialog__close')`), true, "model dialog moves focus to close");

  await exerciseViewerInteractions(cdp, "dialog", false);
  await waitForRenderIdle(cdp, "enlarged model remains render-on-demand idle", "dialog");

  const beforeThemeRender = await renderCount(cdp, "dialog");
  await evaluate(cdp, `document.documentElement.dataset.theme = 'dark'`);
  await waitFor(cdp, `Number(document.querySelector('[data-model-viewer-instance="dialog"]').dataset.renderCount) > ${beforeThemeRender}`);
  await evaluate(cdp, `document.documentElement.dataset.theme = 'light'`);

  await evaluate(cdp, `
    window.__zpdClosedDialogViewer = document.querySelector('[data-model-viewer-instance="dialog"]');
    window.__zpdClosedDialogCanvas = window.__zpdClosedDialogViewer.querySelector('canvas');
    document.querySelector(${JSON.stringify(dialogSelector)}).querySelector('.zld-preview-dialog__close').click();
  `);
  await waitFor(cdp, `!document.querySelector(${JSON.stringify(dialogSelector)})?.open`);
  await waitFor(cdp, `window.__zpdClosedDialogViewer?.dataset.viewerDisposed === 'true'`);
  assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-component-model-viewer-root]').length`), 1, "closing model dialog removes temporary viewer");
  assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-model-viewer-viewport] canvas').length`), 1, "closing model dialog removes temporary canvas");
  assertEqual(await evaluate(cdp, `window.__zpdClosedDialogCanvas?.isConnected`), false, "closing model dialog detaches temporary canvas");
  assertEqual(await evaluate(cdp, `document.activeElement === document.querySelector(${JSON.stringify(triggerSelector)})`), true, "closing model dialog restores trigger focus");

  for (let cycle = 1; cycle <= 2; cycle += 1) {
    await evaluate(cdp, `document.querySelector(${JSON.stringify(triggerSelector)}).click()`);
    await waitFor(cdp, `document.querySelector('[data-model-viewer-instance="dialog"]')?.dataset.viewerState === 'ready'`, 20_000);
    await evaluate(cdp, `
      window.__zpdCycleViewer = document.querySelector('[data-model-viewer-instance="dialog"]');
      document.querySelector(${JSON.stringify(dialogSelector)}).querySelector('.zld-preview-dialog__close').click();
    `);
    await waitFor(cdp, `window.__zpdCycleViewer?.dataset.viewerDisposed === 'true'`);
    assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-component-model-viewer-root]').length`), 1, `model dialog reopen cycle ${cycle} leaves one viewer`);
    assertEqual(await evaluate(cdp, `document.querySelectorAll('[data-model-viewer-viewport] canvas').length`), 1, `model dialog reopen cycle ${cycle} leaves one canvas`);
  }
}

async function exerciseViewerInteractions(cdp, instance = "inline", testResize = true) {
  const rootSelector = `[data-model-viewer-instance="${instance}"]`;
  const canvas = await evaluate(cdp, `(() => {
    const rect = document.querySelector(${JSON.stringify(`${rootSelector} [data-model-viewer-viewport] canvas`)}).getBoundingClientRect();
    return { left: rect.left, top: rect.top, width: rect.width, height: rect.height };
  })()`);
  const x = canvas.left + canvas.width / 2;
  const y = canvas.top + canvas.height / 2;

  await waitForRenderIdle(cdp, `before ${instance} orbit input`, instance);
  let before = await renderCount(cdp, instance);
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", buttons: 1, clickCount: 1 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x + 48, y: y + 24, button: "left", buttons: 1 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x + 48, y: y + 24, button: "left", buttons: 0, clickCount: 1 });
  await waitFor(cdp, `Number(document.querySelector(${JSON.stringify(rootSelector)}).dataset.renderCount) > ${before}`);

  await waitForRenderIdle(cdp, `before ${instance} zoom input`, instance);
  before = await renderCount(cdp, instance);
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseWheel", x, y, deltaX: 0, deltaY: -180 });
  await waitFor(cdp, `Number(document.querySelector(${JSON.stringify(rootSelector)}).dataset.renderCount) > ${before}`);

  await waitForRenderIdle(cdp, `before ${instance} keyboard input`, instance);
  await evaluate(cdp, `document.querySelector(${JSON.stringify(`${rootSelector} [data-model-viewer-viewport]`)}).focus()`);
  before = await renderCount(cdp, instance);
  await cdp.send("Input.dispatchKeyEvent", { type: "rawKeyDown", key: "ArrowLeft", code: "ArrowLeft", windowsVirtualKeyCode: 37, nativeVirtualKeyCode: 37 });
  await cdp.send("Input.dispatchKeyEvent", { type: "keyUp", key: "ArrowLeft", code: "ArrowLeft", windowsVirtualKeyCode: 37, nativeVirtualKeyCode: 37 });
  await waitFor(cdp, `Number(document.querySelector(${JSON.stringify(rootSelector)}).dataset.renderCount) > ${before}`);
  const focus = await evaluate(cdp, `(() => {
    const viewport = document.querySelector(${JSON.stringify(`${rootSelector} [data-model-viewer-viewport]`)});
    const style = getComputedStyle(viewport);
    return { active: document.activeElement === viewport, outline: style.outlineStyle, width: parseFloat(style.outlineWidth) };
  })()`);
  assertEqual(focus.active, true, `${instance} viewer keyboard focus retained`);
  assertEqual(focus.outline !== "none" && focus.width >= 2, true, `${instance} viewer focus state visible`);

  if (!testResize) return;
  await waitForRenderIdle(cdp, `before ${instance} resize input`, instance);
  before = await renderCount(cdp, instance);
  await setViewportAndMedia(cdp, 1200, "light", false);
  await waitFor(cdp, `Number(document.querySelector(${JSON.stringify(rootSelector)}).dataset.renderCount) > ${before}`);
  // The first render tick can land before the ResizeObserver -> rAF backing-store update,
  // so a one-shot sample here races the resize by a frame (observed in CI as pixelWidth
  // lagging viewportWidth by a few px). Poll the settled invariant instead, like the
  // dialog path already does; on timeout, throw with the sampled diagnostics.
  try {
    await waitForCanvasSize(cdp, instance);
  } catch {
    const resized = await evaluate(cdp, `(() => {
      const canvas = document.querySelector(${JSON.stringify(`${rootSelector} [data-model-viewer-viewport] canvas`)});
      const viewport = document.querySelector(${JSON.stringify(`${rootSelector} [data-model-viewer-viewport]`)});
      return { cssWidth: canvas.clientWidth, viewportWidth: viewport.clientWidth, pixelWidth: canvas.width, ratio: devicePixelRatio };
    })()`);
    throw new Error(`viewer canvas did not resize to viewport: ${JSON.stringify(resized)}`);
  }
  await setViewportAndMedia(cdp, 1440, "light", false);
}

async function renderCount(cdp, instance = "inline") {
  return Number(await evaluate(cdp, `document.querySelector('[data-model-viewer-instance=${JSON.stringify(instance)}]')?.dataset.renderCount ?? 0`));
}

async function waitForCanvasSize(cdp, instance) {
  const rootSelector = `[data-model-viewer-instance="${instance}"]`;
  await waitFor(cdp, `(() => {
    const viewport = document.querySelector(${JSON.stringify(`${rootSelector} [data-model-viewer-viewport]`)});
    const canvas = viewport?.querySelector('canvas');
    if (!viewport || !canvas) return false;
    const ratio = Math.min(devicePixelRatio, 2);
    const expectedWidth = Math.max(1, viewport.clientWidth) * ratio;
    const expectedHeight = Math.max(1, viewport.clientHeight) * ratio;
    return Math.abs(canvas.width - expectedWidth) <= Math.max(4, expectedWidth * 0.01)
      && Math.abs(canvas.height - expectedHeight) <= Math.max(4, expectedHeight * 0.01);
  })()`);
}

async function waitForRenderIdle(cdp, label, instance = "inline") {
  await delay(150);
  const count = await renderCount(cdp, instance);
  await delay(250);
  assertEqual(await renderCount(cdp, instance), count, label);
}

async function pressKey(cdp, key, code, keyCode, modifiers = 0) {
  await cdp.send("Input.dispatchKeyEvent", { type: "rawKeyDown", key, code, modifiers, windowsVirtualKeyCode: keyCode, nativeVirtualKeyCode: keyCode });
  await cdp.send("Input.dispatchKeyEvent", { type: "keyUp", key, code, modifiers, windowsVirtualKeyCode: keyCode, nativeVirtualKeyCode: keyCode });
}

async function clickAt(cdp, x, y) {
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", buttons: 1, clickCount: 1 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", buttons: 0, clickCount: 1 });
}

function assertContained(child, parent, label) {
  const epsilon = 1;
  if (
    child.left < parent.left - epsilon || child.right > parent.right + epsilon ||
    child.top < parent.top - epsilon || child.bottom > parent.bottom + epsilon ||
    child.width <= 0 || child.height <= 0
  ) {
    throw new Error(`${label} is not contained: child=${JSON.stringify(child)} parent=${JSON.stringify(parent)}`);
  }
}

function assertDurationAtMost(value, maximumSeconds, label) {
  const durations = value.split(",").map((part) => {
    const trimmed = part.trim();
    if (trimmed.endsWith("ms")) return Number.parseFloat(trimmed) / 1000;
    if (trimmed.endsWith("s")) return Number.parseFloat(trimmed);
    return Number.NaN;
  });
  if (durations.length === 0 || durations.some((duration) => !Number.isFinite(duration) || duration > maximumSeconds)) {
    throw new Error(`${label}: expected <= ${maximumSeconds}s, got ${JSON.stringify(value)}`);
  }
}

async function waitForExit(process) {
  if (process.exitCode !== null || process.signalCode !== null) return;
  await new Promise((resolveExit) => {
    const timer = setTimeout(() => process.kill("SIGKILL"), 2_000);
    process.once("exit", () => {
      clearTimeout(timer);
      resolveExit();
    });
  });
}

async function readDebuggingPort(chrome) {
  let stderr = "";
  for await (const chunk of chrome.stderr) {
    stderr += chunk.toString();
    const match = /DevTools listening on ws:\/\/127\.0\.0\.1:(\d+)\//u.exec(stderr);
    if (match !== null) return Number(match[1]);
    if (stderr.length > 20_000) stderr = stderr.slice(-10_000);
  }
  throw new Error(`Chrome exited before opening DevTools: ${stderr.slice(-2000)}`);
}

async function waitForJson(url) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) return response.json();
    } catch {}
    await delay(50);
  }
  throw new Error(`Timed out fetching ${url}`);
}

async function connectCdp(url) {
  const socket = new WebSocket(url);
  await new Promise((resolveOpen, rejectOpen) => {
    socket.addEventListener("open", resolveOpen, { once: true });
    socket.addEventListener("error", rejectOpen, { once: true });
  });
  let nextId = 0;
  const pending = new Map();
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id === undefined) return;
    const callbacks = pending.get(message.id);
    if (callbacks === undefined) return;
    pending.delete(message.id);
    if (message.error) callbacks.reject(new Error(`${callbacks.method}: ${message.error.message}`));
    else callbacks.resolve(message.result);
  });
  return {
    send(method, params = {}) {
      const id = ++nextId;
      return new Promise((resolveSend, rejectSend) => {
        pending.set(id, { resolve: resolveSend, reject: rejectSend, method });
        socket.send(JSON.stringify({ id, method, params }));
      });
    },
    close() { socket.close(); },
  };
}

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails !== undefined) {
    throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
  }
  return result.result.value;
}

async function waitFor(cdp, expression, timeout = 10_000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await evaluate(cdp, `Boolean(${expression})`)) return;
    await delay(50);
  }
  throw new Error(`Timed out waiting for: ${expression}`);
}

async function revealViewer(cdp) {
  await waitFor(cdp, `(() => {
    const marker = document.querySelector('[data-zfb-island="PackageModelViewerIsland"]');
    if (!marker) return false;
    marker.scrollIntoView({ block: 'center' });
    const bounds = marker.getBoundingClientRect();
    return bounds.bottom > 0 && bounds.top < innerHeight;
  })()`);
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) throw new Error(`${label}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
}

await main();
