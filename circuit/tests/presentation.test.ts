import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, it } from "node:test";

import {
  ALLOWED_COMPONENT_ATTRIBUTES,
  ATTRIBUTE_VALUE_PATTERN,
  buildRecordIndex,
  CIRCUIT_PUBLICATION_MATRIX,
  CIRCUIT_SELECTION,
  PublicationPolicy,
  projectIndex,
  readEvidenceIndex,
  renderCatalog,
  renderIntegration,
  renderRecord,
} from "./project-context.mjs";
import { packageRoot, root } from "./compatibility-helpers.mjs";

const evidence = await readEvidenceIndex();
const model = projectIndex(
  evidence,
  new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, CIRCUIT_SELECTION),
);
const recordIndex = buildRecordIndex(model);
const catalogPage = renderCatalog(model).contents;
const integrationPage = renderIntegration(model, recordIndex).contents;
const recordPages = model.records.map((record) => renderRecord(record, recordIndex).contents);
const dataRecord = model.records.find((record) => record.facts.length > 0 && record.pinMaps.length > 0);
assert.ok(dataRecord, "published corpus needs a record with claims and pin assignments");
const dataPage = renderRecord(dataRecord, recordIndex).contents;
const packageStyle = await readFile(join(packageRoot, "styles.css"), "utf8");

function wideTableCount(page: string): number {
  const lines = page.split("\n");
  let count = 0;
  for (let index = 0; index < lines.length - 1; index += 1) {
    const row = lines[index] ?? "";
    const delimiter = lines[index + 1] ?? "";
    if (/^\s*\|(?:\s*:?-+:?\s*\|)+\s*$/u.test(delimiter) && row.includes("|")) {
      if (row.split("|").length - 2 > 2) count += 1;
    }
  }
  return count;
}

function disclosedBlocks(page: string): string[] {
  return [...page.matchAll(/<EvidenceDetails[^>]*>([\s\S]*?)<\/EvidenceDetails>/gu)].map(
    (match) => match[1] ?? "",
  );
}

describe("package MDX components remain connected to the host", () => {
  it("registers the installed package component set through the host binding", async () => {
    const host = await readFile(join(root, "doc", "src", "chrome-bindings.tsx"), "utf8");
    const packageBindings = await readFile(join(packageRoot, "lib", "mdx-extras.js"), "utf8");
    assert.match(host, /import\s*\{\s*circuitDocMdxExtras\s*\}\s*from\s*["']@takazudo\/zudo-circuit-doc\/mdx-extras["']/u);
    assert.match(host, /mdxExtras:\s*\{\s*\.\.\.circuitDocMdxExtras\s*\}/u);
    for (const name of Object.keys(ALLOWED_COMPONENT_ATTRIBUTES)) {
      if (name === "CategoryNav") continue;
      assert.match(
        packageBindings,
        new RegExp(`^\\s*${name},?\\s*$`, "mu"),
        `${name} is accepted by the project MDX guard but absent from the installed package registry`,
      );
    }
  });

  it("keeps the package stylesheet after framework feature styles", async () => {
    const hostStyles = await readFile(join(root, "doc", "src", "styles", "global.css"), "utf8");
    const framework = hostStyles.indexOf("@takazudo/zudo-doc/features.css");
    const circuit = hostStyles.indexOf("@takazudo/zudo-circuit-doc/styles.css");
    assert.ok(framework >= 0 && circuit > framework, "package component styles must follow zudo-doc features");
    assert.doesNotMatch(hostStyles, /\.zcd-/u, "component rules must come from the package stylesheet");
  });
});

describe("published presentation keeps evidence readable and available", () => {
  it("puts one keyboard-scrollable wrapper around each table wider than two columns", () => {
    for (const page of [catalogPage, integrationPage, ...recordPages]) {
      assert.equal(
        [...page.matchAll(/<EvidenceTable\b/gu)].length,
        wideTableCount(page),
        "every wide table needs exactly one project scroll wrapper",
      );
    }
  });

  it("keeps evidence facts and their terms in the page body", () => {
    assert.match(dataPage, /<EvidenceFact>/u);
    assert.match(dataPage, /\*\*Fact:\*\*/u);
    assert.match(dataPage, /\*\*Value:\*\*/u);
    assert.match(dataPage, /\*\*Unit:\*\*/u);
    assert.match(dataPage, /\*\*Conditions:\*\*/u);
    assert.match(dataPage, /\*\*Verdict:\*\*/u);
    assert.match(dataPage, /\*\*Provenance:\*\*/u);
    assert.match(dataPage, /\*\*Evidence:\*\*/u);
    assert.match(dataPage, /\| Symbol pin\s*\| Name\s*\| Footprint pad\s*\| Function\s*\|/u);
  });

  it("discloses only lookup pin assignments, never evidence claims", () => {
    for (const page of recordPages) {
      for (const block of disclosedBlocks(page)) {
        assert.match(block, /<EvidenceTable label="pin-assignments">/u);
        for (const forbidden of ["Conditions:", "Fact class:", "Provenance:", "Source ID", "Verdict:", "Coverage ID"]) {
          assert.ok(!block.includes(forbidden), `a disclosure conceals ${forbidden}`);
        }
      }
    }
  });

  it("uses safe authored labels and self-describing catalog links", () => {
    const authored = new Set([
      "parts-index",
      "rules-index",
      "calculation-results",
      "evidence-chain",
      "pin-assignments",
    ]);
    for (const page of [catalogPage, integrationPage, ...recordPages]) {
      for (const match of page.matchAll(/<Evidence(?:Table|Details) label="([^"]*)"/gu)) {
        const label = match[1] ?? "";
        assert.match(label, ATTRIBUTE_VALUE_PATTERN, `${label} is outside the package MDX label contract`);
        assert.ok(authored.has(label), `unexpected evidence component label ${label}`);
      }
    }
    for (const record of model.records) {
      assert.ok(
        catalogPage.includes(`[${record.identity.mpn} record details]`),
        `${record.identity.recordId} has no descriptive catalog link`,
      );
    }
  });
});

describe("installed component CSS preserves responsive and accessible controls", () => {
  it("provides one focused scroll surface with enough table width to overflow", () => {
    assert.match(packageStyle, /\.zcd-evidence-table\s*\{[^}]*overflow-x:\s*auto/u);
    assert.match(packageStyle, /\.zcd-evidence-table:focus-visible\s*\{[^}]*outline:/u);
    assert.match(packageStyle, /\.zcd-evidence-table table\s*\{[^}]*min-width:/u);
    assert.match(packageStyle, /\.zcd-evidence-table--parts-index table\s*\{[^}]*min-width:/u);
  });

  it("reflows reference cards on narrow containers and contains preview imagery", () => {
    assert.match(packageStyle, /\.zcd-component-references__document\s*\{[^}]*display:\s*grid/u);
    assert.match(packageStyle, /@container\s*\(max-width:\s*38rem\)[\s\S]*?grid-template-columns:\s*minmax\(0,\s*1fr\)/u);
    assert.match(packageStyle, /\.zcd-component-references__footprint-frame\s*>\s*a\s*\{[^}]*aspect-ratio:\s*16 \/ 9/u);
    assert.match(packageStyle, /\.zcd-component-references__footprint img\s*\{[^}]*object-fit:\s*contain/u);
  });

  it("hides inactive enlarge controls, gives controls touch targets, and keeps a visible focus ring", () => {
    assert.match(
      packageStyle,
      /\.zcd-component-references__footprint\[data-footprint-preview-state="no-js"\] \.zcd-preview-enlarge-button,[\s\S]*?\.zcd-model-viewer:not\(\[data-viewer-state="ready"\]\) \.zcd-preview-enlarge-button\s*\{[^}]*display:\s*none/u,
    );
    for (const selector of ["zcd-preview-enlarge-button", "zcd-preview-dialog__close"]) {
      const rule = new RegExp(`\\.${selector}\\s*\\{([^}]*)\\}`, "u").exec(packageStyle)?.[1] ?? "";
      assert.match(rule, /min-width:\s*44px/u, selector);
      assert.match(rule, /min-height:\s*44px/u, selector);
    }
    assert.match(packageStyle, /\.zcd-preview-enlarge-button:focus-visible,[\s\S]*?\.zcd-preview-dialog__close:focus-visible\s*\{[^}]*outline:/u);
    assert.match(packageStyle, /\.zcd-model-viewer__viewport:focus-visible\s*\{[^}]*outline:/u);
  });

  it("uses a transform-free native dialog and hides the viewer canvas when it cannot render", async () => {
    const dialogRule = /\.zcd-preview-dialog\s*\{([^}]*)\}/u.exec(packageStyle)?.[1] ?? "";
    const closeRule = /\.zcd-preview-dialog__close\s*\{([^}]*)\}/u.exec(packageStyle)?.[1] ?? "";
    assert.notEqual(dialogRule, "");
    assert.doesNotMatch(dialogRule, /transform:/u);
    assert.match(closeRule, /position:\s*fixed/u);
    const dialogSource = await readFile(join(packageRoot, "lib", "islands", "preview-enlarge-dialog.js"), "utf8");
    assert.match(dialogSource, /ENLARGE_DIALOG_STYLE/u);
    assert.match(dialogSource, /manageFocus:\s*true/u);
    for (const state of ["no-js", "error", "unavailable"]) {
      assert.match(
        packageStyle,
        new RegExp(`\\.zcd-model-viewer\\[data-viewer-state="${state}"\\] \.zcd-model-viewer__viewport`, "u"),
      );
    }
  });
});
