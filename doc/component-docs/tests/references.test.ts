/**
 * The reference contract against the reviewed current corpus.
 * Curated documents must retain their labels and exact source URLs; document
 * and model gaps must have explicit reasons. Cardinality is locked by the
 * committed publication selection, not by a historical board's part count.
 */

import assert from "node:assert/strict";
import { before, describe, it } from "node:test";

import { ComponentDocsError } from "../core/errors.ts";
import { PublicationPolicy } from "../core/publication.ts";
import { projectIndex, readEvidenceIndex } from "../adapters/circuit/index.ts";
import { CIRCUIT_PUBLICATION_MATRIX } from "../adapters/circuit/matrix.ts";
import { CIRCUIT_DOCUMENT_VERIFICATION, CIRCUIT_SELECTION } from "../adapters/circuit/selection.ts";
import {
  REFERENCE_LIMITS,
  assertReferenceSize,
  assertSafePreviewAssetName,
  assertSameBasenamePair,
  selectDocumentExceptions,
  selectDocuments,
  validateVrml,
  type CircuitReferenceContract,
} from "../adapters/circuit/references.ts";
import type { EvidenceIndex } from "../adapters/circuit/evidence.ts";
import type { PublicViewModel } from "../core/view-model.ts";

let index: EvidenceIndex;
let references: CircuitReferenceContract;
let model: PublicViewModel;

before(async () => {
  index = await readEvidenceIndex();
  references = index.references as CircuitReferenceContract;
  model = projectIndex(index, new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, CIRCUIT_SELECTION));
});

describe("reviewed document shortcuts", () => {
  it("partitions every reviewed record into a curated document or explicit exception", () => {
    assert.equal(CIRCUIT_SELECTION.documentSelections.length, 59);
    assert.equal(CIRCUIT_SELECTION.documentExceptions.length, 1);
    assert.equal(model.records.length, CIRCUIT_SELECTION.expect.records);
    const curated = new Set(CIRCUIT_SELECTION.documentSelections.map((entry) => entry.recordId));
    const excepted = new Set(CIRCUIT_SELECTION.documentExceptions.map((entry) => entry.recordId));
    assert.equal(curated.size, CIRCUIT_SELECTION.documentSelections.length);
    assert.equal(excepted.size, 1);
    for (const recordId of CIRCUIT_SELECTION.recordIds) {
      assert.equal(
        Number(curated.has(recordId)) + Number(excepted.has(recordId)),
        1,
        `${recordId} must be in exactly one of the two lists`,
      );
    }
  });

  it("gives every curated record a reviewed label and its source's own URL", () => {
    for (const record of model.records) {
      const document = record.reference.document;
      if (document === null) continue;
      assert.match(String(document.url), /^https?:\/\//u);
      assert.ok(
        ["Datasheet PDF", "Specification PDF", "Mechanical drawing PDF"].includes(String(document.label)),
        `${record.identity.recordId} has label ${String(document.label)}`,
      );
      assert.ok(String(document.sourceId).length > 0);
      assert.ok(String(document.documentTitle).length > 0);
      assert.ok(String(document.authorityClass).length > 0);
      assert.ok(String(document.availability).length > 0);
      // The published URL is the selected source's own, never derived.
      const source = index.recordById
        .get(record.identity.recordId)
        ?.sources.find((entry) => entry.source_id === String(document.sourceId));
      assert.equal(String(document.url), source?.authoritative_url);
      assert.equal(record.reference.documentUnresolvedReason, null);
    }
    assert.equal(model.records.filter((record) => record.reference.document !== null).length, CIRCUIT_SELECTION.documentSelections.length);
  });

  it("leaves rec-c335982 unresolved with a reason naming the missing document", () => {
    // The audit's one honest gap: a single DISTRIBUTOR_IDENTITY source and no
    // manufacturer document behind it. The page must say that rather than
    // present the LCSC listing as a datasheet.
    const record = model.records.find((entry) => entry.identity.recordId === "rec-c335982");
    assert.ok(record !== undefined);
    assert.equal(record.reference.document, null);
    const reason = String(record.reference.documentUnresolvedReason ?? "");
    assert.match(reason, /No manufacturer document exists/u);
    assert.match(reason, /distributor product listing/u);
    // And the LCSC page it does have stays visible, with its class printed.
    const listing = record.sources.find((entry) => String(entry.sourceId) === "src-c335982-identity");
    assert.equal(String(listing?.authorityClass), "DISTRIBUTOR_IDENTITY");
  });

  it("does not infer kind from the source ID's suffix", () => {
    // Both of these are named `-datasheet` and are not datasheets. The kind
    // follows the document's own self-description.
    for (const [recordId, expected] of [
      ["rec-cya1265-100uh-c19268674", "Specification PDF"],
      ["rec-ptc-msmd110-33v-c70119", "Specification PDF"],
      ["rec-ss34-c8678", "Datasheet PDF"],
    ] as const) {
      const record = model.records.find((entry) => entry.identity.recordId === recordId);
      assert.equal(String(record?.reference.document?.label), expected, recordId);
      assert.match(String(record?.reference.document?.sourceId), /-datasheet$/u);
    }
    const drawing = model.records.find(
      (entry) => entry.identity.recordId === "rec-dealon-dw254p-2x8-l0-c4749189",
    );
    assert.equal(String(drawing?.reference.document?.label), "Mechanical drawing PDF");
  });

  it("publishes the eight mirror selections as mirrors, not as primaries", () => {
    // Each of these is the best document that exists for its part, and the
    // card has to keep saying so — silently reading as MANUFACTURER_PRIMARY
    // would overstate the evidence.
    assert.equal(CIRCUIT_DOCUMENT_VERIFICATION.mirrorSourceIds.length, 8);
    for (const sourceId of CIRCUIT_DOCUMENT_VERIFICATION.mirrorSourceIds) {
      const record = model.records.find(
        (entry) => String(entry.reference.document?.sourceId) === sourceId,
      );
      assert.ok(record !== undefined, `${sourceId} is not a selected document`);
      assert.equal(String(record.reference.document?.authorityClass), "MANUFACTURER_MIRROR");
      assert.equal(String(record.reference.document?.availability), "AVAILABLE");
    }
    const mirrors = model.records.filter(
      (entry) => String(entry.reference.document?.authorityClass) === "MANUFACTURER_MIRROR",
    );
    assert.equal(mirrors.length, 8);
  });

  it("records how the document audit was performed, at its real strength", () => {
    // This aggregate audit checks recorded evidence metadata. Individual
    // component owners retain their own primary document retrieval evidence.
    assert.equal(CIRCUIT_DOCUMENT_VERIFICATION.checkedOn, "2026-09-20");
    assert.equal(CIRCUIT_DOCUMENT_VERIFICATION.expectedContent, "PDF");
    assert.equal(CIRCUIT_DOCUMENT_VERIFICATION.method, "EVIDENCE_BUNDLE_METADATA");
    assert.deepEqual(
      [...CIRCUIT_DOCUMENT_VERIFICATION.unresolvedRecordIds],
      CIRCUIT_SELECTION.documentExceptions.map((entry) => entry.recordId),
    );
    // What the audit could check offline, checked here too: no selected
    // document is one the evidence itself records as unreachable. (The
    // hash-lock half of the audit reads `sha256`/`refresh_policy`, which
    // `ProviderSource` deliberately does not expose — `component-spec-audit`'s
    // validator owns that contract and this file must not restate it.)
    for (const selected of CIRCUIT_SELECTION.documentSelections) {
      const source = index.recordById
        .get(selected.recordId)
        ?.sources.find((entry) => entry.source_id === selected.sourceId);
      assert.ok(source !== undefined, selected.sourceId);
      assert.equal(source.availability, "AVAILABLE", selected.sourceId);
      assert.match(source.authoritative_url, /^https?:\/\//u, selected.sourceId);
    }
  });

  it("refuses a document exception that does not resolve to a record", () => {
    assert.throws(
      () => selectDocumentExceptions(index, {
        ...CIRCUIT_SELECTION,
        documentExceptions: [{ recordId: "rec-does-not-exist", reason: "because" }],
      }),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "STALE_SELECTION",
    );
  });

  it("refuses a record that is neither curated nor excepted", () => {
    assert.throws(
      () => new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, {
        ...CIRCUIT_SELECTION,
        documentSelections: CIRCUIT_SELECTION.documentSelections.slice(1),
      }),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "PUBLICATION_POLICY",
    );
  });

  it("refuses a record listed twice, which one covering entry would satisfy", () => {
    // The uncovered-list filter alone cannot see this: both occurrences of the
    // duplicate resolve to the same covering entry.
    assert.throws(
      () => new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, {
        ...CIRCUIT_SELECTION,
        recordIds: [...CIRCUIT_SELECTION.recordIds, "rec-ss34-c8678"],
      }),
      (error: unknown) =>
        error instanceof ComponentDocsError && error.code === "PUBLICATION_POLICY",
    );
  });

  it("refuses an exception that states no reason, and one that doubles a selection", () => {
    for (const documentExceptions of [
      [{ recordId: "rec-c335982", reason: "   " }],
      [
        ...CIRCUIT_SELECTION.documentExceptions,
        { recordId: "rec-ss34-c8678", reason: "contradicts its own curated entry" },
      ],
    ]) {
      assert.throws(
        () => new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, {
          ...CIRCUIT_SELECTION,
          documentExceptions,
        }),
        (error: unknown) =>
          error instanceof ComponentDocsError && error.code === "PUBLICATION_POLICY",
      );
    }
  });

  it("refuses a document selection that does not resolve inside its record", () => {
    for (const selection of [
      { recordId: "rec-stusb4500qtr", sourceId: "src-does-not-exist" },
      // A real source, but owned by a different record.
      { recordId: "rec-stusb4500qtr", sourceId: "src-ss34-datasheet" },
      { recordId: "rec-does-not-exist", sourceId: "src-stusb-ds12499" },
    ]) {
      assert.throws(
        () => selectDocuments(index, {
          ...CIRCUIT_SELECTION,
          documentSelections: [{ ...selection, documentKind: "datasheet" }],
        }),
        (error: unknown) =>
          error instanceof ComponentDocsError && error.code === "STALE_SELECTION",
      );
    }
  });
});

describe("KiCad preview manifest", () => {
  it("maps every record to exactly one reviewed package descriptor", () => {
    assert.equal(references.packages.length, CIRCUIT_SELECTION.expect.footprintPackages);
    assert.equal(new Set(references.packages.map((entry) => entry.packageId)).size, CIRCUIT_SELECTION.expect.footprintPackages);
    assert.equal(references.packages.flatMap((entry) => entry.recordIds).length, CIRCUIT_SELECTION.expect.records);
    assert.equal(references.packageByRecordId.size, CIRCUIT_SELECTION.expect.records);
    for (const record of model.records) {
      assert.ok(String(record.reference.footprint.footprintName).length > 0);
    }
  });

  it("reads the collapse figure from the reviewed selection, not a literal", () => {
    // The reviewed package count lives in
    // `selection.ts` next to the record list it is derived from, so promoting
    // a candidate cannot change one without the other being looked at.
    assert.equal(CIRCUIT_SELECTION.expect.footprintPackages, 34);
    assert.equal(references.packages.length, CIRCUIT_SELECTION.expect.footprintPackages);
  });

  it("shares one package descriptor across every record that uses it", () => {
    // R0603 is shared by seventeen records. Each of them
    // must see the SAME descriptor carrying the complete shared-record list,
    // not a partial descriptor built for an earlier record.
    const r0603 = references.packages.find((entry) => entry.footprintName === "R0603");
    assert.ok(r0603 !== undefined);
    assert.equal(r0603.recordIds.length, 17);
    for (const recordId of r0603.recordIds) {
      assert.deepEqual(references.packageByRecordId.get(recordId)?.recordIds, r0603.recordIds);
    }
  });
});

describe("reviewed 3D models preserve their evidence limits", () => {
  it("resolves every selected visualization without claiming exact inductor CAD", () => {
    const unresolved = references.packages.filter((entry) => entry.model === undefined);
    assert.deepEqual(unresolved, []);
    for (const entry of references.packages.filter((entry) => entry.model !== undefined)) {
      assert.equal(entry.modelUnresolvedReason, undefined, `${entry.packageId} has a stale unresolved reason`);
      assert.match(String(entry.model?.modelPath), /^footprints\/kicad\/zudo-pd\.3dshapes\/[^/]+\.wrl$/u, entry.packageId);
      for (const axis of ["x", "y", "z"] as const) {
        for (const transform of [entry.model?.offset, entry.model?.rotation, entry.model?.scale]) {
          assert.equal(typeof transform?.[axis], "number", entry.packageId);
          assert.ok(Number.isFinite(transform?.[axis]), entry.packageId);
        }
      }
    }
    assert.deepEqual(model.records.filter((record) => record.reference.footprint.model === null)
      .map((record) => record.identity.recordId), []);
    for (const record of model.records) {
      assert.equal(record.reference.footprint.modelUnresolvedReason, null);
    }
    const inductor = model.records.find((record) => record.identity.recordId === "rec-aspi-0630lr-100m-t15");
    assert.ok(inductor);
    const visualization = inductor.facts.find((fact) => fact.factId === "fact-aspi-0630lr-100m-t15-visualization-envelope");
    assert.match(String(visualization?.value), /not exact manufacturer CAD/u);
    assert.equal(String(visualization?.provenance), "PROJECT-CHOICE");
    const unavailable = inductor.sources.find((source) => source.sourceId === "src-aspi-0630lr-100m-t15-manufacturer-step-attempt");
    assert.equal(String(unavailable?.availability), "SOURCE UNAVAILABLE");
  });
});

describe("preview assets fail closed", () => {
  const rejects = (fn: () => void, code: ComponentDocsError["code"]) =>
    assert.throws(fn, (error: unknown) => error instanceof ComponentDocsError && error.code === code);

  it("rejects traversal, absolute and external-looking asset names", () => {
    for (const path of ["../part.wrl", "/tmp/part.wrl", "models/part.wrl", "C:\\part.wrl", "https:part.wrl"]) {
      rejects(() => assertSafePreviewAssetName(path, "rec-hostile"), "PATH_CONTAINMENT");
    }
  });

  it("rejects resource-loading, executable and loader-unsupported VRML nodes", () => {
    for (const payload of [
      "#VRML V2.0 utf8\nInline { url \"https://evil.invalid/model.wrl\" }",
      "#VRML V2.0 utf8\nScript { url \"javascript:alert(1)\" }",
      "#VRML V2.0 utf8\nImageTexture { url \"data:image/png;base64,AA\" }",
      "#VRML V2.0 utf8\nTransform { children [] }",
      "#VRML V2.0 utf8\nShape { url \"relative-model.wrl\" }",
      "#VRML V2.0 utf8\nROUTE A.out TO B.in",
    ]) rejects(() => validateVrml(payload, "rec-hostile", "hostile.wrl"), "PUBLICATION_POLICY");
    rejects(
      () => validateVrml('#VRML V2.0 utf8\nShape { name "../../private/model.wrl" }', "rec-hostile", "hostile.wrl"),
      "PATH_CONTAINMENT",
    );
  });

  it("allows harmless URLs in generator comments but not live nodes", () => {
    assert.doesNotThrow(() => validateVrml("#VRML V2.0 utf8\n# generated by https://example.invalid\nShape { }", "rec-safe", "safe.wrl"));
  });

  it("rejects missing/mismatched format pairs and all size-cap violations", () => {
    rejects(() => assertSameBasenamePair("part.wrl", "other.step", "rec-hostile"), "ADAPTER_CONTRACT");
    rejects(() => assertSameBasenamePair("part.wrl", "part.stp", "rec-hostile"), "ADAPTER_CONTRACT");
    rejects(() => assertReferenceSize("footprint", REFERENCE_LIMITS.footprintBytes + 1, "rec-hostile"), "PUBLICATION_POLICY");
    rejects(() => assertReferenceSize("model", REFERENCE_LIMITS.modelBytes + 1, "rec-hostile"), "PUBLICATION_POLICY");
    rejects(() => assertReferenceSize("aggregate", REFERENCE_LIMITS.aggregateModelBytes + 1, "rec-hostile"), "PUBLICATION_POLICY");
  });
});
