import assert from "node:assert/strict";
import { mkdtemp, cp, readFile, rm, symlink, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, describe, it } from "node:test";

import { CIRCUIT_SELECTION } from "./preview-context.mjs";
import { checkFootprintPreviews } from "./preview-context.mjs";
import { FOOTPRINT_MASTER_ROOT, FOOTPRINT_ROOT, PREVIEW_ROOT } from "./preview-context.mjs";
import { assertFootprintLibraryParity } from "./preview-context.mjs";
import { suppressFootprintText } from "./preview-context.mjs";
import type { FootprintSelection } from "./preview-context.mjs";
import { readFootprintSelections } from "./preview-context.mjs";
import { normalizeSvg, validateSvg } from "./preview-context.mjs";

const EXPECTED_PACKAGES = CIRCUIT_SELECTION.expect.packages;
const EXPECTED_RECORDS = CIRCUIT_SELECTION.expect.records;

let selections: readonly FootprintSelection[];
let fixtureRoot: string;

before(async () => {
  selections = await readFootprintSelections();
  fixtureRoot = await mkdtemp(join(tmpdir(), "zpd-preview-tests-"));
});

after(async () => {
  await rm(fixtureRoot, { recursive: true, force: true });
});

describe("footprint preview export transforms", () => {
  it("suppresses every footprint text form without changing other expressions", () => {
    const source = `(footprint "x"\n  (fp_text reference "REF**)" (at 0 0) (effects (font (size 1 1))))\n  (fp_line (start 0 0) (end 1 1))\n  (fp_text user "%R" (at 0 0))\n)`;
    const result = suppressFootprintText(source);
    assert.doesNotMatch(result, /fp_text|REF\*\*|%R/u);
    assert.match(result, /\(fp_line \(start 0 0\) \(end 1 1\)\)/u);
    assert.throws(() => suppressFootprintText("(footprint (fp_text user x)"), /unbalanced/u);
  });

  it("removes volatile metadata and emits a finite responsive root", () => {
    const normalized = normalizeSvg(`<?xml version="1.0"?><!DOCTYPE svg><svg xmlns="http://www.w3.org/2000/svg" width="2mm" height="3mm" viewBox="0 0 2 3"><title>created date 2099</title><desc>PCBNEW</desc><path d="M0 0 L1 1" /></svg>`);
    assert.doesNotMatch(normalized, /2099|DOCTYPE|<title|<desc|<\?xml/u);
    assert.match(normalized, /viewBox="0\.0000 0\.0000 2\.0000 3\.0000" width="100%" height="100%"/u);
    assert.deepEqual(validateSvg(normalized), { minX: 0, minY: 0, width: 2, height: 3 });
  });

  it("rejects scripts, event handlers, resources, traversal-shaped links, empty geometry, and bad view boxes", () => {
    for (const hostile of [
      `<svg viewBox="0 0 1 1"><script>alert(1)</script><path d="M0 0"/></svg>`,
      `<svg viewBox="0 0 1 1"><path onclick="alert(1)" d="M0 0"/></svg>`,
      `<svg viewBox="0 0 1 1"><path onload=alert(1) d="M0 0"/></svg>`,
      `<svg viewBox="0 0 1 1"><path unexpected="x" d="M0 0"/></svg>`,
      `<svg viewBox="0 0 1 1"><path style="fill:&#117;rl(evil)" d="M0 0"/></svg>`,
      `<svg viewBox="0 0 1 1">unexpected<path d="M0 0"/></svg>`,
      `<svg viewBox="0 0 1 1"><image href="https://evil.invalid/a"/></svg>`,
      `<svg viewBox="0 0 1 1"><use href="../outside.svg#x"/></svg>`,
      `<svg viewBox="0 0 1 1"><g /></svg>`,
      `<svg viewBox="0 0 1 1"><path d="M0 0"/></svg>`,
      `<svg viewBox="0 0 1 1"><g transform="translate(20 0)"><path d="M0 0"/></g></svg>`,
      `<svg viewBox="0 0 1 1"><path d="M0 0 L20 20"/></svg>`,
      `<svg viewBox="0 0 NaN 1"><path d="M0 0"/></svg>`,
      `<svg viewBox="0 0 0 1"><path d="M0 0"/></svg>`,
    ]) assert.throws(() => validateSvg(hostile));
  });
});

describe("footprint preview no-KiCad drift check", () => {
  it(`accepts the committed ${EXPECTED_PACKAGES}-package, ${EXPECTED_RECORDS}-record alias set`, async () => {
    await checkFootprintPreviews(selections);
    assert.equal(selections.length, EXPECTED_PACKAGES);
    assert.equal(new Set(selections.flatMap((entry) => entry.recordIds)).size, EXPECTED_RECORDS);
  });

  it("fails on missing, extra, stale input/output, unsafe output, and changed alias reuse", async () => {
    const makeFixture = async (name: string) => {
      const root = join(fixtureRoot, name);
      const assets = join(root, "assets");
      const footprints = join(root, "footprints");
      const master = join(root, "master");
      await cp(PREVIEW_ROOT, assets, { recursive: true });
      await cp(FOOTPRINT_ROOT, footprints, { recursive: true });
      await cp(FOOTPRINT_MASTER_ROOT, master, {
        recursive: true,
        filter: (source) => source === FOOTPRINT_MASTER_ROOT || source.endsWith(".kicad_mod"),
      });
      return { assets, footprints, master };
    };
    const first = selections[0] as FootprintSelection;

    const missing = await makeFixture("missing");
    await unlink(join(missing.assets, `${first.footprintName}.svg`));
    await assert.rejects(checkFootprintPreviews(selections, missing.assets, missing.footprints, missing.master), /missing/u);

    const extra = await makeFixture("extra");
    await writeFile(join(extra.assets, "extra.svg"), "x");
    await assert.rejects(checkFootprintPreviews(selections, extra.assets, extra.footprints, extra.master), /extra/u);

    const staleInput = await makeFixture("stale-input");
    await writeFile(join(staleInput.footprints, `${first.footprintName}.kicad_mod`), "\n", { flag: "a" });
    await writeFile(join(staleInput.master, `${first.footprintName}.kicad_mod`), "\n", { flag: "a" });
    await assert.rejects(checkFootprintPreviews(selections, staleInput.assets, staleInput.footprints, staleInput.master), /input hash/u);

    const staleOutput = await makeFixture("stale-output");
    await writeFile(join(staleOutput.assets, `${first.footprintName}.svg`), "\n", { flag: "a" });
    await assert.rejects(checkFootprintPreviews(selections, staleOutput.assets, staleOutput.footprints, staleOutput.master), /output hash/u);

    const unsafe = await makeFixture("unsafe");
    const unsafeFile = join(unsafe.assets, `${first.footprintName}.svg`);
    await writeFile(unsafeFile, (await readFile(unsafeFile, "utf8")).replace("<path ", "<path onclick=\"x\" "));
    await assert.rejects(checkFootprintPreviews(selections, unsafe.assets, unsafe.footprints, unsafe.master), /unsafe/u);

    const linked = await makeFixture("linked");
    const linkedFile = join(linked.assets, `${first.footprintName}.svg`);
    await unlink(linkedFile);
    await symlink(join(PREVIEW_ROOT, `${first.footprintName}.svg`), linkedFile);
    await assert.rejects(checkFootprintPreviews(selections, linked.assets, linked.footprints, linked.master), /regular file/u);

    const changed = selections.map((entry, index) => index === 0 ? { ...entry, recordIds: [...entry.recordIds, "rec-invented"] } : entry);
    await assert.rejects(checkFootprintPreviews(changed), /stale package selection/u);
  });

  it("fails when either dual-location footprint inventory or bytes drift", async () => {
    const root = join(fixtureRoot, "parity");
    const master = join(root, "master");
    const library = join(root, "library");
    await cp(FOOTPRINT_MASTER_ROOT, master, {
      recursive: true,
      filter: (source) => source === FOOTPRINT_MASTER_ROOT || source.endsWith(".kicad_mod"),
    });
    await cp(FOOTPRINT_ROOT, library, { recursive: true });
    await assertFootprintLibraryParity(master, library);

    const first = selections[0] as FootprintSelection;
    const path = join(master, `${first.footprintName}.kicad_mod`);
    await writeFile(path, "\n", { flag: "a" });
    await assert.rejects(assertFootprintLibraryParity(master, library), /bytes differ/u);
    await cp(join(library, `${first.footprintName}.kicad_mod`), path);
    await unlink(path);
    await assert.rejects(assertFootprintLibraryParity(master, library), /inventory differs/u);
  });
});
