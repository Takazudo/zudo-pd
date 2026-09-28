import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, rm, symlink, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, isAbsolute, relative, join } from "node:path";
import { after, before, describe, it } from "node:test";

import {
  buildModelAssetPlan,
  buildRecordIndex,
  CIRCUIT_PUBLICATION_MATRIX,
  CIRCUIT_SELECTION,
  createPythonValidator,
  decodeComponentReferencesDescriptor,
  decodeModelDescriptor,
  encodeModelDescriptor,
  MODEL_ASSET_BASE,
  mapped,
  PublicationPolicy,
  projectIndex,
  readEvidenceIndex,
  renderRecord,
  REPO_ROOT,
  syncModelAssets,
  type ModelViewerDescriptor,
} from "./project-context.mjs";
import { fixtureModel } from "./fixtures.ts";
import { packageRoot } from "./compatibility-helpers.mjs";

let scratch = "";

before(async () => {
  scratch = await mkdtemp(join(tmpdir(), "zudo-pd-model-viewer-"));
});

after(async () => {
  await rm(scratch, { recursive: true, force: true });
});

const descriptor: ModelViewerDescriptor = {
  version: 1,
  packageId: "SOT-23-3_L2.9-W1.3-P0.95-LS2.4-BR",
  packageLabel: "SOT-23-3_L2.9-W1.3-P0.95-LS2.4-BR",
  modelUrl: `${MODEL_ASSET_BASE}SOT-23-3_L2.9-W1.3-P0.95-LS2.4-BR.wrl`,
  offset: { x: 1, y: -2, z: 3 },
  rotation: { x: 10, y: 20, z: 30 },
  scale: { x: 1, y: 2, z: 3 },
};

function referenceDescriptorOn(page: string) {
  const tags = [...page.matchAll(/<ComponentReferences descriptor="([0-9a-f]+)"\s*\/>/gu)];
  assert.equal(tags.length, 1, "a generated record carries one package reference descriptor");
  return decodeComponentReferencesDescriptor(tags[0]?.[1] ?? "");
}

function projectValidator() {
  return createPythonValidator({
    pythonBin: "python3",
    scriptPath: join(REPO_ROOT, ".claude/skills/component-spec-audit/scripts/validate.py"),
    cwd: REPO_ROOT,
    args: ["--strict"],
    minVersion: { major: 3, minor: 12 },
  });
}

describe("model descriptors projected from the installed package", () => {
  it("round-trips the closed local-WRL schema and rejects other URLs or formats", () => {
    const encoded = encodeModelDescriptor(descriptor);
    assert.match(encoded, /^(?:[0-9a-f]{2})+$/u);
    assert.equal(encoded, encodeModelDescriptor(descriptor));
    assert.deepEqual(decodeModelDescriptor(encoded), descriptor);
    assert.throws(() => decodeModelDescriptor("../model.wrl"));
    assert.throws(() => encodeModelDescriptor({ ...descriptor, modelUrl: "https://example.invalid/model.wrl" }));
    assert.throws(() => encodeModelDescriptor({
      ...descriptor,
      modelUrl: `${MODEL_ASSET_BASE}SOT-23-3_L2.9-W1.3-P0.95-LS2.4-BR.step`,
    }));
  });

  it("projects every selected local package model with its reviewed transform", async () => {
    const evidence = await readEvidenceIndex();
    const selected = mapped.selection;
    const viewModel = projectIndex(
      evidence,
      new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, CIRCUIT_SELECTION),
    );
    const recordIndex = buildRecordIndex(viewModel);
    const packages = new Set(
      viewModel.records
        .map((record) => record.reference.footprint?.packageId)
        .filter((packageId): packageId is NonNullable<typeof packageId> => packageId !== undefined),
    );
    const modelPaths = new Set(
      viewModel.records
        .map((record) => record.reference.footprint?.modelPath)
        .filter((path): path is NonNullable<typeof path> => path !== undefined && path !== null),
    );

    assert.equal(viewModel.records.length, selected.expect.records);
    assert.equal(packages.size, selected.expect.packages);
    assert.equal(modelPaths.size, selected.expect.packages);

    for (const record of viewModel.records) {
      const references = referenceDescriptorOn(renderRecord(record, recordIndex).contents);
      const footprint = record.reference.footprint;
      if (footprint === null) {
        assert.equal(references.footprint, null);
        assert.equal(references.modelDescriptor, null);
        continue;
      }

      assert.equal(references.footprint?.name, footprint.footprintName);
      assert.ok(footprint.modelPath, `${record.identity.recordId} has a selected package model`);
      assert.ok(references.modelDescriptor, `${record.identity.recordId} carries a model descriptor`);
      const viewer = decodeModelDescriptor(references.modelDescriptor);
      assert.equal(viewer.packageId, footprint.packageId);
      assert.equal(viewer.packageLabel, footprint.footprintName);
      assert.equal(viewer.modelUrl, `${MODEL_ASSET_BASE}${basename(footprint.modelPath)}`);
      assertAxes(viewer.offset, footprint.offset);
      assertAxes(viewer.rotation, footprint.rotation);
      assertAxes(viewer.scale, footprint.scale);
    }

    const inductor = viewModel.records.find(
      (record) => record.identity.recordId === "rec-aspi-0630lr-100m-t15",
    );
    assert.ok(inductor, "the selected illustrative inductor record remains published");
    assert.match(String(inductor.reference.footprint?.modelPath), /ASPI-0630LR_MaxEnvelope/u);
  });

  it("builds its model plan from validated project paths and uses only real WRL files", async () => {
    const validation = await projectValidator()();
    assert.equal(validation.ok, true, validation.stderr);
    const plan = await buildModelAssetPlan({
      paths: mapped.paths,
      selection: mapped.selection,
      reference: mapped.reference,
      policy: new PublicationPolicy(mapped.matrix, mapped.selection),
      validation,
    });

    assert.equal(plan.length, CIRCUIT_SELECTION.expect.packages);
    assert.ok(plan.every((entry) => entry.name.endsWith(".wrl")));
    for (const entry of plan) {
      assert.ok(isAbsolute(entry.source), entry.source);
      const withinModelRoot = relative(mapped.paths.modelRoot, entry.source);
      assert.ok(!withinModelRoot.startsWith(".."), `${entry.source} escaped the selected model root`);
      await readFile(entry.source);
    }
  });

  it("keeps a fixture with no selected model publishable and explicitly unresolved", () => {
    const fixture = fixtureModel();
    const recordIndex = buildRecordIndex(fixture);
    assert.ok(fixture.records.length > 0);
    for (const record of fixture.records) {
      assert.equal(record.reference.footprint?.modelPath ?? null, null);
      const references = referenceDescriptorOn(renderRecord(record, recordIndex).contents);
      assert.equal(references.modelDescriptor, null);
    }
  });

  it("keeps unresolved package markup out of the viewer branch", async () => {
    const componentReferences = await readFile(
      join(packageRoot, "lib", "ui", "component-references.js"),
      "utf8",
    );
    assert.match(componentReferences, /modelDescriptor\s*===\s*null/u);
    assert.match(componentReferences, /Package model unavailable\./u);
    assert.match(componentReferences, /PackageModelViewer/u);
  });
});

describe("model asset publication", () => {
  it("copies exact bytes and reports missing, changed and extra output", async () => {
    const projectRoot = join(scratch, "copy-project");
    const source = join(projectRoot, "source.wrl");
    const output = join(projectRoot, "public");
    await mkdir(projectRoot, { recursive: true });
    await writeFile(source, "#VRML V2.0 utf8\nShape {}\n");
    const plan = [{ name: "source.wrl", source }];

    assert.deepEqual((await syncModelAssets(plan, projectRoot, output, true)).drift, ["missing: source.wrl"]);
    assert.deepEqual((await syncModelAssets(plan, projectRoot, output, false)).written, ["source.wrl"]);
    assert.equal(await readFile(join(output, "source.wrl"), "utf8"), await readFile(source, "utf8"));
    assert.deepEqual((await syncModelAssets(plan, projectRoot, output, true)).drift, []);

    await writeFile(join(output, "source.wrl"), "stale");
    assert.deepEqual((await syncModelAssets(plan, projectRoot, output, true)).drift, ["changed: source.wrl"]);
    await writeFile(join(output, "extra.wrl"), "extra");
    assert.deepEqual(
      (await syncModelAssets(plan, projectRoot, output, true)).drift,
      ["changed: source.wrl", "extra: extra.wrl"],
    );
    await assert.rejects(() => syncModelAssets([{ name: "source.step", source }], projectRoot, output, true));

    await unlink(join(output, "source.wrl"));
    await symlink(source, join(output, "source.wrl"));
    await assert.rejects(() => syncModelAssets(plan, projectRoot, output, true));
  });

  it("accepts an empty output plan without creating an output directory", async () => {
    const projectRoot = join(scratch, "empty-project");
    const output = join(projectRoot, "public");
    const result = await syncModelAssets([], projectRoot, output, true);
    assert.equal(result.expected, 0);
    assert.deepEqual(result.drift, []);
  });
});

function assertAxes(actual: { x: number; y: number; z: number }, expected: { x: number; y: number; z: number }): void {
  for (const axis of ["x", "y", "z"] as const) {
    assert.ok(Math.abs(actual[axis] - expected[axis]) < 1e-12, `${axis} axis differs`);
  }
}
