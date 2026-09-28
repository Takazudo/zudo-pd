import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, describe, it } from "node:test";

import {
  ComponentDocsError,
  CIRCUIT_SELECTION,
  createCircuitAdapter,
  createPythonValidator,
  literal,
  PREFLIGHT_FILE,
  REPO_ROOT,
  runPipeline,
  VIEW_MODEL_VERSION,
  type PublicViewModel,
} from "./project-context.mjs";

let scratch = "";

before(async () => {
  scratch = await mkdtemp(join(tmpdir(), "zudo-pd-pipeline-"));
});

after(async () => {
  await rm(scratch, { recursive: true, force: true });
});

function projectValidator(scriptPath = join(
  REPO_ROOT,
  ".claude/skills/component-spec-audit/scripts/validate.py",
)) {
  return createPythonValidator({
    pythonBin: "python3",
    scriptPath,
    cwd: REPO_ROOT,
    args: ["--strict"],
    minVersion: { major: 3, minor: 12 },
  });
}

function projectAdapter(validator = projectValidator()) {
  return createCircuitAdapter({ validator });
}

describe("the installed package pipeline on this project's corpus", () => {
  it("validates before projecting and locks the published corpus", async () => {
    const generatedRoot = join(scratch, "generated");
    const result = await runPipeline(projectAdapter(), { generatedRoot, dryRun: false });

    assert.equal(result.report.records.available, 60);
    assert.equal(result.report.records.selected, 60);
    assert.equal(result.report.sources.available, 154);
    assert.equal(result.report.sources.selected, 154);
    assert.equal(result.report.viewModelVersion, VIEW_MODEL_VERSION);
    assert.equal(result.report.provider.id, "circuit-component-spec");
    assert.equal(result.report.counts.publishedIntegrationRules, 11);

    const paths = result.pages.map((page) => page.relativePath);
    assert.equal(paths.length, result.report.records.selected + 4);
    assert.ok(paths.includes("index.mdx"));
    assert.ok(paths.includes("catalog/index.mdx"));
    assert.ok(paths.includes("records/index.mdx"));
    assert.ok(paths.includes("integration/index.mdx"));
    assert.ok(paths.includes("records/stusb4500qtr/index.mdx"));
    assert.deepEqual([...(result.emitted?.written ?? [])].sort(), [...paths].sort());
  });

  it("is idempotent when the same project output is generated again", async () => {
    const generatedRoot = join(scratch, "idempotent");
    const first = await runPipeline(projectAdapter(), { generatedRoot, dryRun: false });
    const second = await runPipeline(projectAdapter(), { generatedRoot, dryRun: false });

    assert.deepEqual(second.emitted?.written, []);
    assert.deepEqual(
      [...(second.emitted?.unchanged ?? [])].sort(),
      first.pages.map((page) => page.relativePath).sort(),
    );
  });

  it("emits deterministic page bytes and report content in separate roots", async () => {
    const first = await runPipeline(projectAdapter(), {
      generatedRoot: join(scratch, "first"),
      dryRun: false,
    });
    const second = await runPipeline(projectAdapter(), {
      generatedRoot: join(scratch, "second"),
      dryRun: false,
    });

    assert.deepEqual(
      first.pages.map((page) => [page.relativePath, page.contents]),
      second.pages.map((page) => [page.relativePath, page.contents]),
    );
    assert.equal(JSON.stringify(first.report), JSON.stringify(second.report));
  });

  it("keeps every matrix decision honest in the preflight accounting", async () => {
    const result = await runPipeline(projectAdapter(), {
      generatedRoot: join(scratch, "accounting"),
      dryRun: true,
    });

    for (const field of result.report.fields) {
      if (field.decision === "PUBLISH") {
        assert.equal(field.withheld, 0, `${field.key} withheld data while set to PUBLISH`);
      } else {
        assert.equal(field.emitted, 0, `${field.key} emitted data while set to DENY`);
      }
    }
    await assert.rejects(stat(join(scratch, "accounting")), { code: "ENOENT" });
  });

  it("reports changed files in check mode without overwriting them", async () => {
    const generatedRoot = join(scratch, "drift");
    await runPipeline(projectAdapter(), { generatedRoot, dryRun: false });

    const target = join(generatedRoot, "index.mdx");
    const original = await readFile(target, "utf8");
    await writeFile(target, `${original}\nedited by hand\n`, "utf8");

    const result = await runPipeline(projectAdapter(), { generatedRoot, dryRun: true });
    assert.deepEqual(result.drift, ["changed: index.mdx"]);
    assert.match(await readFile(target, "utf8"), /edited by hand/u);
  });

  it("matches the committed preflight contract", async () => {
    const result = await runPipeline(projectAdapter(), {
      generatedRoot: join(scratch, "preflight-contract"),
      dryRun: true,
    });
    assert.deepEqual(JSON.parse(await readFile(PREFLIGHT_FILE, "utf8")), result.report);
    assert.equal(result.report.records.selected, CIRCUIT_SELECTION.expect.records);
    assert.equal(result.pages.length, result.report.records.selected + 4);
  });
});

describe("project validation runs before generated output can be written", () => {
  it("stops on a strict validator failure before creating generated files", async () => {
    const failing = join(scratch, "always-fails.py");
    await writeFile(failing, 'import sys\nsys.stderr.write("FAIL: seeded\\n")\nsys.exit(3)\n');
    const generatedRoot = join(scratch, "must-not-exist");

    await assert.rejects(
      runPipeline(projectAdapter(projectValidator(failing)), { generatedRoot, dryRun: false }),
      (error: unknown) => {
        assert.ok(error instanceof ComponentDocsError);
        assert.equal(error.code, "VALIDATION_FAILED");
        assert.equal(error.detail.exitCode, 3);
        assert.match(String(error.detail.stderr), /FAIL: seeded/u);
        return true;
      },
    );
    await assert.rejects(stat(generatedRoot), { code: "ENOENT" });
  });

  it("rejects an adapter that omits the expected provider identity", async () => {
    const base = projectAdapter();
    const adapter = {
      ...base,
      project: async (): Promise<PublicViewModel> => ({
        version: VIEW_MODEL_VERSION,
        provider: { id: literal("skips-the-project-provider"), contractVersion: 1 },
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
      runPipeline(adapter, { generatedRoot: join(scratch, "bad-adapter"), dryRun: true }),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "ADAPTER_CONTRACT",
    );
  });
});
