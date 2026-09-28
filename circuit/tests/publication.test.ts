import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { ComponentDocsError } from "@takazudo/zudo-circuit-doc";
import {
  FIELD_KEYS,
  PublicationPolicy,
  type InstanceSelection,
  type PublicationMatrix,
} from "@takazudo/zudo-circuit-doc";
import { CIRCUIT_PUBLICATION_MATRIX } from "./project-context.mjs";
import { CIRCUIT_SELECTION } from "./project-context.mjs";

const selection: InstanceSelection = {
  recordIds: ["rec-a"],
  sourceIds: ["src-a"],
  linkableSourceIds: ["src-a"],
  documentSelections: [{ recordId: "rec-a", sourceId: "src-a", documentKind: "datasheet" }],
  documentExceptions: [],
  expect: { records: 1, sources: 1, integrationRules: 0, footprintPackages: 1 },
};

function matrixOf(overrides: Partial<PublicationMatrix> = {}): PublicationMatrix {
  const base = Object.fromEntries(FIELD_KEYS.map((key) => [key, "DENY"])) as PublicationMatrix;
  return { ...base, ...overrides };
}

describe("PublicationPolicy gates", () => {
  it("withholds a denied field's value entirely", () => {
    const policy = new PublicationPolicy(matrixOf(), selection);
    assert.equal(policy.publish("fact.value", 42), undefined);
  });

  it("passes a published field through untouched", () => {
    const policy = new PublicationPolicy(matrixOf({ "fact.value": "PUBLISH" }), selection);
    assert.equal(policy.publish("fact.value", 42), 42);
  });

  it("treats a denied but structurally required field as fatal", () => {
    const policy = new PublicationPolicy(matrixOf(), selection);
    assert.throws(
      () => policy.publishRequired("record.mpn", "AL8860MP-13"),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "PUBLICATION_POLICY",
    );
  });

  it("rejects a linkable source that is not itself selected", () => {
    assert.throws(
      () =>
        new PublicationPolicy(matrixOf(), {
          ...selection,
          linkableSourceIds: ["src-unselected"],
        }),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "PUBLICATION_POLICY",
    );
  });

  it("selects nothing by default — an unlisted instance is unpublished", () => {
    const policy = new PublicationPolicy(matrixOf(), selection);
    assert.equal(policy.isRecordSelected("rec-a"), true);
    assert.equal(policy.isRecordSelected("rec-not-listed"), false);
    assert.equal(policy.isSourceSelected("src-not-listed"), false);
  });
});

describe("selection freshness", () => {
  it("fails when the selection names a record the provider lost", () => {
    const policy = new PublicationPolicy(matrixOf(), selection);
    assert.throws(
      () => policy.assertSelectionFresh(["rec-other"], ["src-a"], 0),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "STALE_SELECTION",
    );
  });

  it("fails when the corpus grew", () => {
    const policy = new PublicationPolicy(matrixOf(), selection);
    assert.throws(
      () => policy.assertSelectionFresh(["rec-a", "rec-new"], ["src-a"], 0),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "STALE_SELECTION",
    );
  });

  it("fails when the integration ruleset changed size", () => {
    const policy = new PublicationPolicy(matrixOf(), selection);
    assert.throws(
      () => policy.assertSelectionFresh(["rec-a"], ["src-a"], 1),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "STALE_SELECTION",
    );
  });

  it("records that the check ran", () => {
    const policy = new PublicationPolicy(matrixOf(), selection);
    assert.equal(policy.selectionChecked, false);
    policy.assertSelectionFresh(["rec-a"], ["src-a"], 0);
    assert.equal(policy.selectionChecked, true);
  });
});

describe("committed circuit policy", () => {
  it("records a decision for every field", () => {
    for (const key of FIELD_KEYS) {
      assert.ok(
        CIRCUIT_PUBLICATION_MATRIX[key] === "PUBLISH" ||
          CIRCUIT_PUBLICATION_MATRIX[key] === "DENY",
        `no decision for ${key}`,
      );
    }
  });

  it("denies every field the epic names as opt-in-only", () => {
    for (const key of [
      "source.sha256",
      "source.evidenceExtract",
      "source.alternateAuthoritativeUrl",
      "source.physicalPdfPageIndex",
      "routing.positivePrompts",
      "routing.negativePrompts",
      "pinMap.reviewedBy",
      "asset.binary",
    ] as const) {
      assert.equal(CIRCUIT_PUBLICATION_MATRIX[key], "DENY", `${key} must stay denied in V1`);
    }
  });

  it("keeps the instance selection free of duplicates", () => {
    assert.equal(
      new Set(CIRCUIT_SELECTION.recordIds).size,
      CIRCUIT_SELECTION.recordIds.length,
    );
    assert.equal(
      new Set(CIRCUIT_SELECTION.sourceIds).size,
      CIRCUIT_SELECTION.sourceIds.length,
    );
  });

  it("matches the asserted corpus size", () => {
    assert.equal(CIRCUIT_SELECTION.recordIds.length, CIRCUIT_SELECTION.expect.records);
    assert.equal(CIRCUIT_SELECTION.sourceIds.length, CIRCUIT_SELECTION.expect.sources);
  });

  it("produces a deterministic report", () => {
    const policy = new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, CIRCUIT_SELECTION);
    const build = (): string =>
      JSON.stringify(
        policy.buildReport({
          viewModelVersion: 1,
          providerId: "circuit-component-spec",
          providerContractVersion: 1,
          availableRecords: 32,
          availableSources: 81,
          selectedSlugs: ["b", "a"],
          counts: { z: 1, a: 2 },
        }),
      );
    assert.equal(build(), build());
    assert.match(build(), /"slugs":\["a","b"\]/u);
    assert.match(build(), /"counts":\{"a":2,"z":1\}/u);
  });
});
