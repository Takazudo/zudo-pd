import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, describe, it } from "node:test";

import { ComponentDocsError } from "../core/errors.ts";
import { literal } from "../core/text.ts";
import { runPipeline } from "../core/pipeline.ts";
import { VIEW_MODEL_VERSION, type PublicViewModel } from "../core/view-model.ts";
import { createCircuitAdapter } from "../adapters/circuit/index.ts";
import { createPythonValidator } from "../adapters/circuit/validate.ts";
import { GENERATED_ROOT, PREFLIGHT_FILE } from "../adapters/circuit/paths.ts";
import { serializeReport } from "../cli/run.ts";

let scratch = "";

before(async () => {
  scratch = await mkdtemp(join(tmpdir(), "component-docs-pipeline-"));
});

after(async () => {
  await rm(scratch, { recursive: true, force: true });
});

describe("the real circuit adapter", () => {
  it("runs the canonical Python validator and projects the corpus", async () => {
    const result = await runPipeline(createCircuitAdapter(), {
      generatedRoot: join(scratch, "generated"),
      dryRun: false,
    });

    // Corpus figures the epic states. A mismatch means evidence moved and the
    // committed selection needs review — exactly what should fail a build.
    assert.equal(result.report.records.available, 60);
    assert.equal(result.report.records.selected, 60);
    assert.equal(result.report.sources.available, 154);
    assert.equal(result.report.sources.selected, 154);
    assert.equal(result.report.viewModelVersion, VIEW_MODEL_VERSION);
    assert.equal(result.report.provider.id, "circuit-component-spec");

    // Ten cross-component rules, the same way: the ruleset lives outside every
    // owner bundle, so nothing else in this report would notice it shrinking.
    assert.equal(result.report.counts.publishedIntegrationRules, 11);

    // The landing page, the catalog, the records index, the integration page,
    // and one page per selected record. A change in this count means a renderer
    // was added or a record stopped being published — both worth failing on.
    const paths = result.pages.map((page) => page.relativePath);
    assert.equal(paths.length, result.report.records.selected + 4);
    assert.ok(paths.includes("index.mdx"));
    assert.ok(paths.includes("catalog/index.mdx"));
    assert.ok(paths.includes("records/index.mdx"));
    assert.ok(paths.includes("integration/index.mdx"));
    assert.ok(paths.includes("records/stusb4500qtr/index.mdx"));
    // `emit` reports in path order; the renderers produce inventory order.
    assert.deepEqual([...(result.emitted?.written ?? [])].sort(), [...paths].sort());
  });

  it("is idempotent — a second run writes nothing", async () => {
    const result = await runPipeline(createCircuitAdapter(), {
      generatedRoot: join(scratch, "generated"),
      dryRun: false,
    });
    assert.deepEqual(result.emitted?.written, []);
    assert.deepEqual(
      [...(result.emitted?.unchanged ?? [])].sort(),
      result.pages.map((page) => page.relativePath).sort(),
    );
  });

  it("emits identical bytes on repeated runs (no timestamps, no locale order)", async () => {
    const first = await runPipeline(createCircuitAdapter(), {
      generatedRoot: join(scratch, "a"),
      dryRun: false,
    });
    const second = await runPipeline(createCircuitAdapter(), {
      generatedRoot: join(scratch, "b"),
      dryRun: false,
    });

    assert.equal(first.pages[0]?.contents, second.pages[0]?.contents);
    assert.equal(serializeReport(first.report), serializeReport(second.report));
  });

  it("denies every field the matrix denies, and withholds nothing it publishes", async () => {
    const result = await runPipeline(createCircuitAdapter(), {
      generatedRoot: join(scratch, "c"),
      dryRun: true,
    });

    for (const field of result.report.fields) {
      if (field.decision === "PUBLISH") {
        assert.equal(field.withheld, 0, `${field.key} withheld a value while set to PUBLISH`);
      } else {
        assert.equal(field.emitted, 0, `${field.key} emitted a value while set to DENY`);
      }
    }
  });

  it("reports drift in check mode without writing", async () => {
    const generatedRoot = join(scratch, "drift");
    await runPipeline(createCircuitAdapter(), { generatedRoot, dryRun: false });

    const target = join(generatedRoot, "index.mdx");
    const original = await readFile(target, "utf8");
    await writeFile(target, `${original}\nedited by hand\n`, "utf8");

    const result = await runPipeline(createCircuitAdapter(), { generatedRoot, dryRun: true });
    assert.deepEqual(result.drift, ["changed: index.mdx"]);
    assert.match(await readFile(target, "utf8"), /edited by hand/u);
  });
});

describe("validator failure propagation", () => {
  it("aborts before projecting when the validator exits nonzero", async () => {
    const failing = join(scratch, "always-fails.py");
    await writeFile(failing, 'import sys\nsys.stderr.write("FAIL: seeded\\n")\nsys.exit(3)\n');

    const adapter = {
      ...createCircuitAdapter(),
      validate: createPythonValidator({ scriptPath: failing }),
    };

    await assert.rejects(
      runPipeline(adapter, { generatedRoot: join(scratch, "never"), dryRun: false }),
      (error: unknown) => {
        assert.ok(error instanceof ComponentDocsError);
        assert.equal(error.code, "VALIDATION_FAILED");
        assert.equal(error.detail.exitCode, 3);
        assert.match(String(error.detail.stderr), /FAIL: seeded/u);
        return true;
      },
    );
  });

  it("aborts when the interpreter is missing", async () => {
    const adapter = {
      ...createCircuitAdapter(),
      validate: createPythonValidator({ pythonBin: "python3-does-not-exist" }),
    };

    await assert.rejects(
      runPipeline(adapter, { generatedRoot: join(scratch, "never"), dryRun: false }),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "VALIDATION_FAILED",
    );
  });
});

describe("adapter contract", () => {
  it("refuses an adapter that cannot produce this view-model version", async () => {
    const adapter = { ...createCircuitAdapter(), supportedViewModelVersions: [] };
    await assert.rejects(
      runPipeline(adapter, { generatedRoot: join(scratch, "never"), dryRun: true }),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "ADAPTER_CONTRACT",
    );
  });

  it("refuses an adapter that skipped the selection freshness check", async () => {
    const base = createCircuitAdapter();
    const adapter = {
      ...base,
      project: async (): Promise<PublicViewModel> => ({
        version: VIEW_MODEL_VERSION,
        provider: { id: literal("skips-the-check"), contractVersion: 1 },
        corpus: {
          ownerBundles: 0,
          records: 0,
          standaloneRecords: 0,
          subordinateRecords: 0,
          sources: 0,
          facts: 0,
          coverageDomains: 0,
          interactions: 0,
          pinMaps: 0,
          pins: 0,
          inventoryLines: 0,
          fittedLines: 0,
          dnpOrHandFitLines: 0,
        },
        records: [],
        integration: [],
      }),
    };

    await assert.rejects(
      runPipeline(adapter, { generatedRoot: join(scratch, "never"), dryRun: true }),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "ADAPTER_CONTRACT",
    );
  });
});

describe("committed output", () => {
  it("matches the committed generated tree and preflight report", async () => {
    const result = await runPipeline(createCircuitAdapter(), {
      generatedRoot: GENERATED_ROOT,
      dryRun: true,
    });
    assert.deepEqual(result.drift, []);
    assert.equal(await readFile(PREFLIGHT_FILE, "utf8"), serializeReport(result.report));
  });
});
