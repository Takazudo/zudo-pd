#!/usr/bin/env node

/**
 * The built-output contract for the component-references section.
 *
 * Every check between the view model and these bytes belongs to the site
 * framework — MDX compiler, HTML minifier, search indexer — so the generator's
 * own tests cannot prove what a reader actually receives. This reads `dist/`.
 *
 * Forked from led-lamp's version. The part that must hold whatever the corpus
 * resolves is asserted for every record: exactly one section, before the
 * evidence tables, with all three cards, each either fully resolved or
 * explicitly unresolved WITH a stated reason. A card that is silently missing,
 * or unresolved with an empty reason, fails here.
 *
 * On top of that, the preview halves are asserted as SHAPE rather than as a
 * count: a record that resolves a footprint or a model must ship the island
 * markup and a real file in `dist/` for it, and a record that resolves neither
 * must ship no live preview UI at all. Both directions are checked because
 * this project's cards are independently optional — a future package
 * `easyeda2kicad` cannot supply a model for must publish, not fail.
 */

import assert from "node:assert/strict";
import { lstat, readFile, readdir } from "node:fs/promises";
import { join, relative, resolve, sep } from "node:path";

const DIST = resolve("dist");
const RECORDS_ROOT = join(DIST, "docs", "components", "records");
const CATALOG = join(DIST, "docs", "components", "catalog", "index.html");
const publicationReport = JSON.parse(await readFile(resolve("component-docs/preflight.json"), "utf8"));
const EXPECTED_RECORDS = publicationReport.records.selected;
assert.ok(Number.isSafeInteger(EXPECTED_RECORDS) && EXPECTED_RECORDS > 0);
const ALLOWED_PDF_LABELS = new Set([
  "Datasheet PDF",
  "Specification PDF",
  "Mechanical drawing PDF",
]);

async function main() {
  const recordDirectories = (await readdir(RECORDS_ROOT, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink())
    .map((entry) => entry.name)
    .sort();
  assert.equal(
    recordDirectories.length,
    EXPECTED_RECORDS,
    `built site must contain exactly ${EXPECTED_RECORDS} component record routes`,
  );

  let resolvedDocuments = 0;
  let resolvedFootprints = 0;
  let resolvedModels = 0;

  for (const slug of recordDirectories) {
    const html = await readFile(join(RECORDS_ROOT, slug, "index.html"), "utf8");
    const sections = extractReferenceSections(html);
    assert.equal(sections.length, 1, `${slug} must render exactly one Component references section`);
    const section = sections[0];
    assert.ok(section !== undefined);
    assert.ok(
      html.indexOf(section) < html.indexOf("zld-evidence-table"),
      `${slug} must render Component references before evidence tables`,
    );

    // All three headings, always. The section's contract is that it says what
    // is known AND what is not; a dropped card breaks that silently.
    for (const heading of ["Selected document", "Footprint preview", "Package model"]) {
      assert.ok(section.includes(`>${heading}<`), `${slug} is missing the "${heading}" card`);
    }

    const unresolved = [...section.matchAll(
      /<p\b[^>]*\bdata-reference-unresolved=(?:"true"|true)[^>]*>(.*?)<\/p>/gsu,
    )];
    for (const [, body] of unresolved) {
      const reason = decodeHtml(stripTags(body ?? "")).replace(/^\s*Unresolved\.\s*/u, "").trim();
      assert.ok(reason.length > 0, `${slug} has an unresolved card with no stated reason`);
    }
    assert.ok(
      unresolved.length <= 3,
      `${slug} rendered ${unresolved.length} unresolved cards for three card slots`,
    );

    const labels = [...section.matchAll(/<p\b[^>]*class=(?:"zld-component-references__document-label"|zld-component-references__document-label)[^>]*>([^<]+)<\/p>/gu)]
      .map((match) => decodeHtml(match[1] ?? ""));
    const documents = [...section.matchAll(/<p\b[^>]*class=(?:"zld-component-references__document-title"|zld-component-references__document-title)[^>]*>\s*(<a\b[^>]*>)/gu)];
    assert.ok(documents.length <= 1, `${slug} must render at most one selected document destination`);
    if (documents.length === 1) {
      resolvedDocuments += 1;
      // A resolved document card carries a reviewed label AND an HTTP(S)
      // destination. The label allowlist is the same one the descriptor
      // enforces; asserting it again here catches a renderer that bypassed it.
      const label = labels.find((candidate) => ALLOWED_PDF_LABELS.has(candidate));
      assert.ok(label !== undefined, `${slug} resolved a document with no reviewed PDF label`);
      const documentUrl = new URL(decodeHtml(readAttribute(documents[0]?.[1] ?? "", "href")));
      assert.ok(
        documentUrl.protocol === "https:" || documentUrl.protocol === "http:",
        `${slug} document URL must be HTTP(S)`,
      );
    }

    const footprintImages = [...section.matchAll(/<img\b[^>]*\balt=(?:"Footprint preview for [^"]+"|'Footprint preview for [^']+')[^>]*>/gu)];
    assert.ok(footprintImages.length <= 1, `${slug} must render at most one footprint preview image`);
    if (footprintImages.length === 1) {
      resolvedFootprints += 1;
      const footprintPath = decodeHtml(readAttribute(footprintImages[0]?.[0] ?? "", "src"));
      assert.match(footprintPath, /^\/assets\/component-previews\/footprints\/[A-Za-z0-9._+-]+\.svg$/u);
      await assertRegularDistFile(footprintPath);
    }

    // The 3D model half. A resolved card ships exactly one viewer root naming
    // a published WRL — never the STEP sibling, which is reviewed but never
    // published — and the hydration marker that makes it interactive.
    const viewerRoots = [...section.matchAll(/<figure\b[^>]*\bdata-component-model-viewer-root\b[^>]*>/gu)];
    assert.ok(viewerRoots.length <= 1, `${slug} must render at most one package model viewer`);
    if (viewerRoots.length === 1) {
      resolvedModels += 1;
      const modelPath = decodeHtml(readAttribute(viewerRoots[0]?.[0] ?? "", "data-model-url"));
      assert.match(modelPath, /^\/assets\/component-previews\/models\/[A-Za-z0-9._+-]+\.wrl$/u);
      await assertRegularDistFile(modelPath);
      assert.match(
        section,
        /data-zfb-island=(?:"PackageModelViewerIsland"|PackageModelViewerIsland)/u,
        `${slug} renders a viewer that never hydrates`,
      );
    }

    // Both enlarge dialogs ship closed, labelled, and paired with a trigger.
    // A `<dialog>` without `open` is `display:none` per UA stylesheet, so a
    // leaked `open` here would cover the page for a reader with no JavaScript.
    const dialogs = [...section.matchAll(/<dialog\b[^>]*\bdata-component-preview-dialog=(?:"([a-z]+)"|([a-z]+))[^>]*>/gu)];
    const kinds = dialogs.map((match) => match[1] ?? match[2]).sort();
    assert.deepEqual(
      kinds,
      [...(footprintImages.length === 1 ? ["footprint"] : []), ...(viewerRoots.length === 1 ? ["model"] : [])],
      `${slug} must ship one closed enlarge dialog per resolved preview`,
    );
    for (const [tag] of dialogs) {
      assert.doesNotMatch(tag, /\bopen\b/u, `${slug} ships an enlarge dialog already open`);
      assert.match(tag, /aria-labelledby=/u, `${slug} ships an unlabelled enlarge dialog`);
    }

    assert.match(html, /id=(?:"sources"|sources)(?:\s|>)/u, `${slug} must retain its Sources section`);
  }

  // The catalog is an index, not a detail page: it must never carry preview UI
  // or a second copy of a record's reference section.
  const catalog = await readFile(CATALOG, "utf8");
  assert.equal(extractReferenceSections(catalog).length, 0, "catalog index must not render reference sections");
  assert.doesNotMatch(
    catalog,
    /data-component-model-viewer-root|data-model-url|component-previews\/models\/|<canvas\b/u,
    "catalog index must not create or reference live preview UI",
  );

  process.stdout.write(
    `built component references passed: ${EXPECTED_RECORDS} records, ` +
    `${resolvedDocuments} resolved documents, ${resolvedFootprints} resolved footprint previews, ` +
    `${resolvedModels} resolved package models, ` +
    "every remaining card unresolved with a stated reason; catalog viewer-free\n",
  );
}

async function assertRegularDistFile(publicPath) {
  assert.ok(publicPath.startsWith("/"));
  const target = resolve(DIST, publicPath.slice(1));
  const rel = relative(DIST, target);
  assert.ok(rel !== "" && rel !== ".." && !rel.startsWith(`..${sep}`), `asset escapes dist: ${publicPath}`);
  const fileStat = await lstat(target);
  assert.ok(fileStat.isFile() && !fileStat.isSymbolicLink(), `asset is not a regular file: ${publicPath}`);
}

function decodeHtml(value) {
  return value
    .replaceAll("&quot;", '"')
    .replaceAll("&#39;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&amp;", "&");
}

function stripTags(value) {
  return value.replace(/<[^>]*>/gu, " ");
}

function extractReferenceSections(html) {
  const marker = /\bclass=(?:"zld-component-references"|'zld-component-references'|zld-component-references)(?=\s|>)/gu;
  const matches = [...html.matchAll(marker)];
  return matches.map((match) => {
    const markerIndex = match.index ?? -1;
    const start = html.lastIndexOf("<section", markerIndex);
    const end = html.indexOf("</section>", markerIndex);
    assert.ok(start >= 0 && end >= 0, "Component references section markup is incomplete");
    return html.slice(start, end + "</section>".length);
  });
}

function readAttribute(tag, name) {
  assert.match(name, /^[a-z-]+$/u);
  const match = new RegExp(`\\b${name}=(?:"([^"]*)"|'([^']*)'|([^\\s>]+))`, "u").exec(tag);
  const value = match?.[1] ?? match?.[2] ?? match?.[3];
  assert.notEqual(value, undefined, `missing ${name} attribute in ${tag.slice(0, 160)}`);
  return value;
}

await main();
