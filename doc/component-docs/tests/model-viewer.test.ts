/**
 * The 3D package model viewer: descriptor, publication, and both render paths.
 *
 * ## Why the unresolved path gets as much attention as the resolved one
 *
 * The current inductor has no reviewed 3D model. Both the real gap and synthetic
 * gaps must keep publishing the component with an explicit reason.
 *
 * ## Why the rendered markup is asserted as source text
 *
 * The test runner is `node --experimental-strip-types`, which strips type
 * annotations but does not compile JSX, so a `.tsx` UI module cannot be
 * imported here at all. `ui/component-references.tsx` is therefore read as
 * text — the same technique `presentation.test.ts` uses for the host bindings.
 */

import assert from "node:assert/strict";
import { realpath, mkdtemp, readFile, symlink, unlink, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";
import { afterEach, before, describe, it } from "node:test";

import { Object3D } from "three";

import { planModelAssets, syncModelAssets } from "../adapters/circuit/model-assets.ts";
import { projectIndex, readEvidenceIndex } from "../adapters/circuit/index.ts";
import { CIRCUIT_PUBLICATION_MATRIX } from "../adapters/circuit/matrix.ts";
import { CIRCUIT_SELECTION } from "../adapters/circuit/selection.ts";
import type { CircuitPackageReference } from "../adapters/circuit/references.ts";
import { ComponentDocsError } from "../core/errors.ts";
import { PublicationPolicy } from "../core/publication.ts";
import {
  decodeComponentReferencesDescriptor,
  type ComponentReferencesDescriptor,
} from "../core/reference-descriptor.ts";
import {
  decodeModelDescriptor,
  encodeModelDescriptor,
  MODEL_ASSET_BASE,
  type ModelViewerDescriptor,
} from "../core/model-descriptor.ts";
import { renderRecord } from "../core/render/record.ts";
import { buildRecordIndex } from "../core/render/shared.ts";
import { applyModelTransform, createOnDemandInvalidator } from "../../src/component-model-viewer/viewer-runtime.ts";
import { setViewerState } from "../../src/component-model-viewer/viewer-state.ts";
import type { PublicViewModel } from "../core/view-model.ts";
import { fixtureModel } from "./fixtures.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const UI_ROOT = join(HERE, "..", "ui");

const descriptor: ModelViewerDescriptor = {
  version: 1,
  packageId: "SOT-23-3_L2.9-W1.3-P0.95-LS2.4-BR",
  packageLabel: "SOT-23-3_L2.9-W1.3-P0.95-LS2.4-BR",
  modelUrl: `${MODEL_ASSET_BASE}SOT-23-3_L2.9-W1.3-P0.95-LS2.4-BR.wrl`,
  offset: { x: 1, y: -2, z: 3 },
  rotation: { x: 10, y: 20, z: 30 },
  scale: { x: 1, y: 2, z: 3 },
};

const originalRaf = globalThis.requestAnimationFrame;
const originalCancel = globalThis.cancelAnimationFrame;

afterEach(() => {
  globalThis.requestAnimationFrame = originalRaf;
  globalThis.cancelAnimationFrame = originalCancel;
});

let model: PublicViewModel;

before(async () => {
  model = projectIndex(
    await readEvidenceIndex(),
    new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, CIRCUIT_SELECTION),
  );
});

/** The one `<ComponentReferences descriptor="…">` tag on a rendered page. */
function referenceDescriptorOn(page: string): ComponentReferencesDescriptor {
  const tags = [...page.matchAll(/<ComponentReferences descriptor="([0-9a-f]+)" \/>/gu)];
  assert.equal(tags.length, 1, "a record page carries exactly one reference block");
  return decodeComponentReferencesDescriptor(tags[0]?.[1] ?? "");
}

function packageFixture(name: string, withModel: boolean): CircuitPackageReference {
  const identity = {
    packageId: name,
    footprintName: name,
    footprintPath: `footprints/kicad/zudo-power.pretty/${name}.kicad_mod`,
    recordIds: [`rec-${name.toLowerCase()}`],
  };
  return withModel
    ? {
      ...identity,
      model: {
        modelPath: `footprints/kicad/zudo-pd.3dshapes/${name}.wrl`,
        offset: { x: 0, y: 0, z: 0 },
        rotation: { x: 0, y: 0, z: 0 },
        scale: { x: 1, y: 1, z: 1 },
      },
    }
    : { ...identity, modelUnresolvedReason: "The KiCad footprint names no 3D model." };
}

describe("model viewer descriptor", () => {
  it("serializes deterministically and round-trips only the closed schema", () => {
    const encoded = encodeModelDescriptor(descriptor);
    assert.match(encoded, /^(?:[0-9a-f]{2})+$/u);
    assert.equal(encoded, encodeModelDescriptor(descriptor));
    assert.deepEqual(decodeModelDescriptor(encoded), descriptor);
    assert.throws(() => decodeModelDescriptor("../model.wrl"));
    assert.throws(() => encodeModelDescriptor({ ...descriptor, modelUrl: "https://evil.invalid/model.wrl" }));
    // The STEP half of each reviewed pair is never published, so it must never
    // become a descriptor URL either.
    assert.throws(() => encodeModelDescriptor({
      ...descriptor,
      modelUrl: `${MODEL_ASSET_BASE}SOT-23-3_L2.9-W1.3-P0.95-LS2.4-BR.step`,
    }));
  });

  it("projects current records onto reviewed local package models and preserves rotations", () => {
    assert.equal(model.records.length, CIRCUIT_SELECTION.expect.records);
    const packageIds = new Set(model.records.map((record) => String(record.reference.footprint.packageId)));
    assert.equal(packageIds.size, CIRCUIT_SELECTION.expect.footprintPackages);
    assert.ok(model.records.some((record) => {
      const rotation = record.reference.footprint.model?.rotation;
      return rotation !== undefined && Object.values(rotation).some((value) => value !== 0);
    }));
  });
});

describe("the resolved model reaches the page as a viewer descriptor", () => {
  it("gives every reviewed visualization its published WRL URL", () => {
    const index = buildRecordIndex(model);
    const published = new Set(
      model.records.filter((record) => record.reference.footprint.model !== null)
        .map((record) => String(record.reference.footprint.model?.modelPath).split("/").at(-1)),
    );
    assert.equal(published.size, CIRCUIT_SELECTION.expect.footprintPackages);
    for (const record of model.records) {
      const card = referenceDescriptorOn(renderRecord(record, index).contents).model;
      assert.ok(card.resolved, `${record.identity.recordId} has no reviewed visualization`);
      const viewer = decodeModelDescriptor(card.descriptor);
      assert.ok(viewer.modelUrl.startsWith(MODEL_ASSET_BASE));
      assert.ok(published.has(viewer.modelUrl.slice(MODEL_ASSET_BASE.length)));
      assert.equal(String(record.reference.footprint.footprintName), viewer.packageLabel);
    }
  });
});

describe("a package with no reviewed model still renders, and still publishes", () => {
  it("plans only the packages that carry a model, and asserts the package count alone", () => {
    const expected = CIRCUIT_SELECTION.expect.footprintPackages;
    // Three of the reviewed packages resolve no model. That is a smaller
    // publication, not a failure.
    const packages = Array.from({ length: expected }, (_, position) =>
      packageFixture(`FIXTURE-PKG-${position}`, position >= 3));
    const plan = planModelAssets(packages);
    assert.equal(plan.length, expected - 3);
    assert.ok(plan.every((entry) => entry.name.endsWith(".wrl")));

    // The PACKAGE count is still fatal when it drifts — dropping a package is
    // a selection change, dropping its model is not.
    assert.throws(
      () => planModelAssets(packages.slice(1)),
      (error: unknown) => error instanceof ComponentDocsError && error.code === "ADAPTER_CONTRACT",
    );
    assert.throws(
      () => planModelAssets(undefined),
      (error: unknown) => error instanceof ComponentDocsError && error.code === "ADAPTER_CONTRACT",
    );
  });

  it("renders the record page with an unresolved model card that names its reason", () => {
    // Every fixture record carries `model: null` plus a reason, which is the
    // shape `readPackage()` returns for a footprint with no `(model …)` line.
    const fixtures = fixtureModel();
    const index = buildRecordIndex(fixtures);
    assert.ok(fixtures.records.length > 0);
    for (const record of fixtures.records) {
      assert.equal(record.reference.footprint.model, null);
      // Generation must not fail: the page renders, in full.
      const card = referenceDescriptorOn(renderRecord(record, index).contents).model;
      assert.equal(card.resolved, false);
      assert.ok(!card.resolved && card.reason.length > 0, "an unresolved card must state its reason");
    }
  });

  it("branches the card on `resolved`, so an unresolved package never mounts a viewer", async () => {
    const source = await readFile(join(UI_ROOT, "component-references.tsx"), "utf8");
    const card = /function ModelCard\(\{[\s\S]*?\n\}/u.exec(source)?.[0] ?? "";
    assert.notEqual(card, "", "ui/component-references.tsx has no ModelCard");
    assert.match(card, /model\.resolved\s*\n?\s*\?\s*<PackageModelViewer descriptor=\{model\.descriptor\}\s*\/>/u);
    assert.match(card, /:\s*<Unresolved reason=\{model\.reason\}\s*\/>/u);
    // The viewer is reachable only through the resolved branch: it must not be
    // rendered anywhere else in this module.
    assert.equal([...source.matchAll(/<PackageModelViewer\b/gu)].length, 1);
  });
});

describe("model asset publication", () => {
  it("copies byte-identically and reports missing, changed, and extra output", async () => {
    const temp = await realpath(await mkdtemp(join(tmpdir(), "zpd-model-assets-")));
    const source = join(temp, "source.wrl");
    const output = join(temp, "public");
    await writeFile(source, "#VRML V2.0 utf8\nShape {}\n");
    const plan = [{ name: "source.wrl", source }];

    assert.deepEqual((await syncModelAssets(plan, output, true)).drift, ["missing: source.wrl"]);
    assert.deepEqual((await syncModelAssets(plan, output, false)).written, ["source.wrl"]);
    assert.equal(await readFile(join(output, "source.wrl"), "utf8"), await readFile(source, "utf8"));
    assert.deepEqual((await syncModelAssets(plan, output, true)).drift, []);

    await writeFile(join(output, "source.wrl"), "stale");
    assert.deepEqual((await syncModelAssets(plan, output, true)).drift, ["changed: source.wrl"]);
    await writeFile(join(output, "extra.wrl"), "extra");
    assert.deepEqual((await syncModelAssets(plan, output, true)).drift, ["changed: source.wrl", "extra: extra.wrl"]);
    await assert.rejects(() => syncModelAssets([{ name: "source.step", source }], output, true));

    await unlink(join(output, "source.wrl"));
    await symlink(source, join(output, "source.wrl"));
    // The lstat guard: a symlink planted at the publication target must fail
    // rather than be followed and overwritten.
    await assert.rejects(() => syncModelAssets(plan, output, true));
  });

  it("publishes an empty plan without touching an empty output root", async () => {
    // The floor of the best-effort path: a corpus where nothing resolved a
    // model publishes nothing and reports no drift.
    const temp = await realpath(await mkdtemp(join(tmpdir(), "zpd-model-empty-")));
    const result = await syncModelAssets([], join(temp, "public"), true);
    assert.deepEqual(result.drift, []);
    assert.equal(result.expected, 0);
  });
});

describe("viewer lifecycle helpers", () => {
  it("applies offset, degree rotations, and scale without losing non-zero axes", () => {
    const object = new Object3D();
    applyModelTransform(object, descriptor.offset, descriptor.rotation, descriptor.scale);
    assert.deepEqual(object.position.toArray(), [1, -2, 3]);
    assert.ok(Math.abs(object.rotation.x - Math.PI / 18) < 1e-12);
    assert.ok(Math.abs(object.rotation.z - Math.PI / 6) < 1e-12);
    assert.deepEqual(object.scale.toArray(), [1, 2, 3]);
  });

  it("coalesces invalidations and cancels pending work", () => {
    let nextFrame = 0;
    const callbacks = new Map<number, FrameRequestCallback>();
    globalThis.requestAnimationFrame = (callback) => {
      nextFrame += 1;
      callbacks.set(nextFrame, callback);
      return nextFrame;
    };
    globalThis.cancelAnimationFrame = (id) => void callbacks.delete(id);
    let renders = 0;
    const invalidator = createOnDemandInvalidator(() => renders += 1);
    invalidator.invalidate();
    invalidator.invalidate();
    assert.equal(callbacks.size, 1);
    const first = callbacks.get(1);
    callbacks.delete(1);
    first?.(0);
    assert.equal(renders, 1);
    invalidator.invalidate();
    invalidator.cancel();
    assert.equal(callbacks.size, 0);
  });

  it("keeps fallback copy meaningful for failure states", () => {
    const status = { textContent: "" } as unknown as Element;
    const root = {
      dataset: {} as DOMStringMap,
      querySelector: () => status,
    };
    setViewerState(root, "unavailable", "WebGL is unavailable. The package identity remains available.");
    assert.equal(root.dataset.viewerState, "unavailable");
    assert.match(status.textContent ?? "", /package identity/u);
  });
});

describe("the island owns the abort, and the runtime requires it", () => {
  it("passes an AbortController signal as mountModelViewer's third argument", async () => {
    const island = await readFile(
      join(HERE, "..", "..", "src", "component-model-viewer", "package-model-viewer-island.tsx"),
      "utf8",
    );
    assert.match(island, /const abort = new AbortController\(\)/u);
    assert.match(island, /mountModelViewer\(root, descriptor, abort\.signal\)/u);
    assert.match(island, /abort\.abort\(\)/u);

    const runtime = await readFile(
      join(HERE, "..", "..", "src", "component-model-viewer", "viewer-runtime.ts"),
      "utf8",
    );
    // Required, not optional: a caller that forgets the signal must not compile.
    assert.match(runtime, /descriptor: ModelViewerDescriptor,\n\s*signal: AbortSignal,/u);
    // An abort is teardown, not a failure a reader is told about.
    assert.match(runtime, /if \(\(error as Error\)\.name !== "AbortError"\)/u);
  });

  it("publishes `ready` only after the first synchronous render", async () => {
    const runtime = await readFile(
      join(HERE, "..", "..", "src", "component-model-viewer", "viewer-runtime.ts"),
      "utf8",
    );
    // The status line is layout-affecting, so its text must be set BEFORE the
    // render that measures the viewport, and `ready` published only after.
    // Reordering these three regresses the dialog viewer's initial sizing.
    const ordering = /setViewerMessage\(root,[\s\S]*?\);\n\s*invalidator\.cancel\(\);\n\s*render\(\);\n\s*root\.dataset\.viewerState = "ready";/u;
    assert.match(runtime, ordering);
  });
});
