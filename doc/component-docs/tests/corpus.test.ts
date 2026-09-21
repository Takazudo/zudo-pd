/**
 * The projection against the real `.claude/skills/**` corpus.
 *
 * Snapshot of the renewed component publication. Changes to these counts require
 * reviewing the evidence selection; synthetic fixtures cover other record shapes.
 * The Python validator is exercised by pipeline.test.ts.
 */

import assert from "node:assert/strict";
import { before, describe, it } from "node:test";

import { SLUG_PATTERN } from "../core/ids.ts";
import { PublicationPolicy } from "../core/publication.ts";
import { projectIndex, readEvidenceIndex } from "../adapters/circuit/index.ts";
import { CIRCUIT_PUBLICATION_MATRIX } from "../adapters/circuit/matrix.ts";
import { CIRCUIT_SELECTION } from "../adapters/circuit/selection.ts";
import type { EvidenceIndex } from "../adapters/circuit/evidence.ts";
import type { PublicRecord, PublicViewModel } from "../core/view-model.ts";

let index: EvidenceIndex;
let model: PublicViewModel;
let policy: PublicationPolicy;

before(async () => {
  index = await readEvidenceIndex();
  policy = new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, CIRCUIT_SELECTION);
  model = projectIndex(index, policy);
});

function record(slug: string): PublicRecord {
  const found = model.records.find((entry) => entry.identity.slug === slug);
  assert.ok(found, `no published record with slug ${slug}`);
  return found;
}

describe("the corpus normalizes to the figures the epic states", () => {
  it("counts 25 bundles and 60 records, all standalone", () => {
    assert.equal(model.corpus.ownerBundles, 25);
    assert.equal(model.corpus.records, 60);
    assert.equal(model.corpus.standaloneRecords, 60);
    assert.equal(model.corpus.subordinateRecords, 0);
    assert.equal(model.corpus.inventoryLines, 60);
    assert.equal(model.corpus.fittedLines, 58);
    assert.equal(model.corpus.dnpOrHandFitLines, 2);
  });

  it("counts 154 sources, 620 facts, 175 coverage domains, 41 interactions", () => {
    assert.equal(model.corpus.sources, 154);
    assert.equal(model.corpus.facts, 620);
    assert.equal(model.corpus.coverageDomains, 175);
    assert.equal(model.corpus.interactions, 41);
  });

  it("counts 60 routes, 60 pin maps and 196 pins", () => {
    assert.equal(index.totals.routes, 60);
    assert.equal(model.corpus.pinMaps, 60);
    assert.equal(model.corpus.pins, 196);
  });

  it("publishes every instance without duplicating or dropping one", () => {
    assert.equal(model.records.length, 60);
    assert.equal(sum(model.records, (entry) => entry.sources.length), 154);
    assert.equal(sum(model.records, (entry) => entry.facts.length), 620);
    assert.equal(sum(model.records, (entry) => entry.coverage.length), 175);
    assert.equal(sum(model.records, (entry) => entry.pinMaps.length), 60);
    assert.equal(
      sum(model.records, (entry) => sum(entry.pinMaps, (map) => map.pins.length)),
      196,
    );

    // Each participant must show its involvement when an interaction spans records.
    const interactions = model.records.flatMap((entry) => entry.interactions);
    assert.equal(interactions.length, 47);
    assert.equal(new Set(interactions.map((entry) => entry.interactionId)).size, 41);
  });

  it("gives every record a unique, route-safe slug and page-unique anchors", () => {
    const slugs = model.records.map((entry) => entry.identity.slug);
    assert.equal(new Set(slugs).size, 60);
    for (const slug of slugs) assert.match(slug, SLUG_PATTERN);

    // Anchors become HTML ids, so uniqueness is a per-document invariant.
    let total = 0;
    for (const entry of model.records) {
      const anchors = [
        entry.identity.anchor,
        ...entry.sources.map((value) => value.anchor),
        ...entry.facts.map((value) => value.anchor),
        ...entry.coverage.map((value) => value.anchor),
        ...entry.interactions.map((value) => value.anchor),
        ...entry.pinMaps.map((value) => value.anchor),
      ];
      assert.equal(new Set(anchors).size, anchors.length, entry.identity.slug);
      total += anchors.length;
    }
    assert.equal(total, 60 + 154 + 620 + 175 + 47 + 60);

    // Record-scoped anchors stay globally unique — each belongs to one page.
    const scoped = model.records.flatMap((entry) => [
      entry.identity.anchor,
      ...entry.sources.map((value) => value.anchor),
      ...entry.facts.map((value) => value.anchor),
      ...entry.coverage.map((value) => value.anchor),
      ...entry.pinMaps.map((value) => value.anchor),
    ]);
    assert.equal(new Set(scoped).size, scoped.length);
  });

  it("never publishes an owner skill: claudeResources is false on this site", () => {
    // `record.ownerSkill` is denied (see `matrix.ts`) because zudo-pd runs
    // with `claudeResources: false`, so `/docs/claude-skills/<name>/` does
    // not exist as a route — every record's `ownerSkill` is `null`, not the
    // bundle name a reader might expect from `record.lineId`/`recordId`.
    for (const entry of model.records) {
      assert.equal(entry.identity.ownerSkill, null, entry.identity.slug);
    }
  });

  it("starts with the first inventory line, not with an alphabetical sort", () => {
    assert.equal(model.records[0]?.identity.slug, "stusb4500qtr");
    assert.equal(model.records[0]?.identity.lineId, index.inventory.lines[0]?.line_id);
  });
});

describe("the real records the epic calls out", () => {
  it("publishes a standalone active part with its placement and states", () => {
    const controller = record("stusb4500qtr");
    assert.equal(controller.identity.kind, "standalone");
    assert.equal(controller.identity.mpn, "STUSB4500QTR");
    assert.equal(controller.identity.lcsc, "C2678061");
    assert.equal(controller.identity.dnp, false);
    assert.deepEqual(
      controller.identity.placements.map((placement) => `${placement.board}.${placement.refdes}`),
      ["board-a.U1", "board-p.U1"],
    );
    assert.notEqual(controller.identity.identityState, "");
    assert.notEqual(controller.identity.sourceState, "");
  });

  it("publishes currently unpopulated lines as full records", () => {
    // DNP is recorded per placement; all current placements of these two
    // lines are unpopulated. Their evidence must remain available.
    const esd = record("pesd24vs1ub-c85382");
    assert.equal(esd.identity.dnp, true);
    assert.deepEqual(
      esd.identity.placements.map((placement) => `${placement.board}.${placement.refdes}`),
      ["board-a.D6", "board-a.D7", "board-p.D6", "board-p.D7"],
    );
    // A DNP line is still a full record: it keeps its evidence, not a stub.
    assert.ok(esd.facts.length > 0);
    assert.ok(esd.coverage.length > 0);

    const dnp = model.records.filter((entry) => entry.identity.dnp);
    assert.deepEqual(
      dnp.map((entry) => entry.identity.slug),
      ["c23186", "pesd24vs1ub-c85382"],
    );
  });

  it("publishes every unavailable source, with its unavailability visible", () => {
    const sources = model.records.flatMap((entry) => entry.sources);
    const unavailable = sources.filter((source) => source.availability === "SOURCE UNAVAILABLE");
    assert.equal(unavailable.length, 8);
    for (const source of unavailable) {
      assert.notEqual(source.documentTitle, "");
      assert.notEqual(source.locator, "");
    }
    assert.equal(
      sources.every(
        (source) =>
          source.availability === "AVAILABLE" || source.availability === "SOURCE UNAVAILABLE",
      ),
      true,
    );
  });

  it("publishes open coverage, both with and without applicable blockers", () => {
    const coverage = model.records.flatMap((entry) => entry.coverage);
    const open = coverage.filter((entry) => entry.status === "OPEN");
    assert.equal(coverage.filter((entry) => entry.status === "COVERED").length, 96);
    assert.equal(open.length, 79);

    const withBlockers = open.filter((entry) => entry.blockingFactIds.length > 0);
    const withoutBlockers = open.filter((entry) => entry.blockingFactIds.length === 0);
    assert.equal(withBlockers.length, 68);
    assert.equal(withoutBlockers.length, 11);

    // An open domain never publishes without saying why it is open.
    for (const entry of open) assert.notEqual(entry.reason, "");
  });

  it("preserves calculated facts, their expressions and cross-record edges", () => {
    const facts = model.records.flatMap((entry) => entry.facts);
    const factRecord = new Map<string, string>(
      facts.map((fact) => [fact.factId, fact.recordId]),
    );

    const calculated = facts.filter((fact) => fact.expression !== "");
    assert.equal(calculated.length, 43);
    assert.equal(facts.filter((fact) => fact.dependsOn.length > 0).length, 43);

    const crossRecord = facts.flatMap((fact) =>
      fact.dependsOn.filter((id) => factRecord.get(id) !== fact.recordId),
    );
    assert.equal(crossRecord.length, 5);
    for (const fact of facts) {
      for (const id of fact.dependsOn) assert.ok(factRecord.has(id), `${id} does not resolve`);
    }

    // The R7 drive-current calculation on C2289 depends on the R13-position
    // resistor's own resistance fact, published on a different record.
    const driveCurrent = facts.find((fact) => fact.factId === "fact-c2289-drive-current");
    assert.ok(driveCurrent);
    assert.deepEqual(driveCurrent.dependsOn, ["fact-c17513-resistance"]);
    assert.notEqual(driveCurrent.expression, "");
    assert.equal(factRecord.get("fact-c17513-resistance"), "rec-c17513");
  });

  it("keeps numeric, string and structured fact values in their own shapes", () => {
    const values = model.records.flatMap((entry) => entry.facts).map((fact) => fact.value);
    assert.equal(values.filter((value) => typeof value === "number").length, 333);
    assert.equal(values.filter((value) => typeof value === "string").length, 234);
    assert.equal(values.filter((value) => Array.isArray(value)).length, 53);

    const identity = model.records
      .flatMap((entry) => entry.facts)
      .find((fact) => fact.factId === "fact-high-diode-smaj20a-identity");
    assert.ok(identity);
    assert.deepEqual(identity.value, [
      { key: "lcsc", value: "C571370" },
      { key: "manufacturer", value: "High Diode" },
      { key: "mpn", value: "SMAJ20A" },
      { key: "variant", value: "unidirectional SMA package" },
    ]);
  });

  it("publishes an interaction on every record it names", () => {
    const interactions = model.records.flatMap((entry) => entry.interactions);
    const drive = interactions.find((entry) => entry.interactionId === "int-c2289-r7-drive");
    assert.ok(drive);
    assert.deepEqual(drive.recordIds, ["rec-c17513", "rec-c2289"]);
    // Both participants carry it.
    for (const slug of ["c17513", "c2289"]) {
      assert.ok(
        record(slug).interactions.some((entry) => entry.interactionId === "int-c2289-r7-drive"),
        `${slug} does not carry int-c2289-r7-drive`,
      );
    }

    // A record carries exactly the interactions its manifest lists — the
    // projection never invents an attachment and never drops one.
    for (const entry of index.records) {
      assert.deepEqual(
        record(entry.record.record_id.replace(/^rec-/u, "")).interactions.map(
          (value) => value.interactionId,
        ),
        entry.record.interaction_ids,
      );
    }

    // Every participant of every published interaction is itself published.
    const published = new Set<string>(model.records.map((entry) => entry.identity.recordId));
    for (const entry of interactions) {
      for (const id of entry.recordIds) assert.ok(published.has(id), `${id} is not published`);
    }
  });

  it("gives every record search aliases", () => {
    for (const entry of model.records) {
      assert.ok(entry.aliases.mpn.length > 0, `${entry.identity.slug} has no MPN alias`);
      assert.ok(entry.aliases.lcsc.length > 0, `${entry.identity.slug} has no LCSC alias`);
      assert.ok(entry.aliases.function.length > 0, `${entry.identity.slug} has no function alias`);
    }
    assert.ok(
      (record("stusb4500qtr").aliases.function as readonly string[]).includes(
        "USB-PD sink controller",
      ),
    );
  });

  it("carries 11 cross-component rules, each naming published records", () => {
    assert.equal(model.integration.length, 11);
    const rail = model.integration.find((rule) => rule.ruleId === "rule-rail-envelope");
    assert.ok(rail);
    assert.deepEqual(rail.recordIds, [
      "rec-stusb4500qtr", "rec-type-c-31-m-17", "rec-c492405", "rec-c2832269",
      "rec-lm2596s-adj-c347423", "rec-c861077", "rec-c110776", "rec-c23159",
      "rec-c107286", "rec-c666307", "rec-ap63201wu-7",
    ]);
    const published = new Set(model.records.map((entry) => entry.identity.recordId));
    for (const rule of model.integration) {
      for (const id of rule.recordIds) assert.ok(published.has(id), `${rule.ruleId} names ${id}`);
    }
  });
});

describe("denied evidence never reaches the public model", () => {
  /**
   * Keys the matrix denies, plus the retrieval bookkeeping a few sources carry
   * that the view model has no field for at all. Values found under these keys
   * must not appear in the projection unless they are ALSO published somewhere
   * legitimately — an alternate URL that is another source's citation, or a
   * routing prompt that is a bare LCSC code, are excluded by construction
   * rather than by an allowlist. `owner_skill` is zudo-pd's own addition to
   * the denied set (see `matrix.ts`).
   */
  const DENIED_KEYS = [
    "sha256",
    "identity_extract_sha256",
    "evidence_extract",
    "alternate_authoritative_url",
    "physical_pdf_page_index",
    "positive",
    "negative",
    "reviewed_by",
    "request_headers",
    "refresh_policy",
    "refresh_note",
    "owner_skill",
  ];

  function collectStrings(value: unknown, denied: boolean, into: [Set<string>, Set<string>]): void {
    if (typeof value === "string") {
      into[denied ? 0 : 1].add(value);
      return;
    }
    if (Array.isArray(value)) {
      for (const item of value) collectStrings(item, denied, into);
      return;
    }
    if (typeof value === "object" && value !== null) {
      for (const [key, nested] of Object.entries(value)) {
        collectStrings(nested, denied || DENIED_KEYS.includes(key), into);
      }
    }
  }

  it("omits every string that only a denied field holds", () => {
    const buckets: [Set<string>, Set<string>] = [new Set(), new Set()];
    for (const entry of index.records) {
      collectStrings(
        { s: entry.sources, r: entry.route, p: entry.pinMaps, f: entry.facts, c: entry.coverage },
        false,
        buckets,
      );
    }
    // `owner_skill` also lives on the inventory LINE, not only per-record —
    // the line-level join is what `buildIdentity()` actually reads it from.
    collectStrings({ lines: index.inventory.lines }, false, buckets);
    // Interactions are not attached to `IndexedRecord` (they live in their
    // own `interactionById` map), so they were absent from the walk above.
    // zudo-pd's evidence legitimately names an owner bundle in an
    // interaction's PUBLISHED `conditions` prose (`int-pesd24vs1ub-cc-provision`:
    // "...their component evidence lives in the component-pesd24vs1ub-c85382
    // owner...") — without this, that published mention would be
    // misclassified as a leak of the denied `owner_skill` value it happens to
    // contain as a substring.
    collectStrings({ interactions: [...index.interactionById.values()] }, false, buckets);
    // Integration conditions are another explicitly published source of prose.
    // A manufacturer + MPN can occur both there and in a denied routing prompt;
    // that legitimate occurrence must not be mistaken for a prompt leak.
    assert.equal(CIRCUIT_PUBLICATION_MATRIX["integration.conditions"], "PUBLISH");
    collectStrings(index.integrationRules.map((rule) => ({ conditions: rule.conditions })), false, buckets);

    const [denied, published] = buckets;
    // Joined with a separator no published string may contain, so a match
    // cannot straddle two of them. A denied string that already occurs
    // inside published evidence — an alternate URL that is another source's
    // citation, a routing prompt built out of the MPN — is not a leak, it is
    // the same words arriving through a field the matrix publishes.
    const publishedBlob = [...published].join("\u0000");
    const exclusivelyDenied = [...denied].filter(
      (value) => value.trim() !== "" && !publishedBlob.includes(value),
    );
    // Guard against the scan silently becoming vacuous.
    assert.ok(exclusivelyDenied.length >= 100, `only ${exclusivelyDenied.length} denied strings`);

    const serialized = JSON.stringify(model);
    for (const value of exclusivelyDenied) {
      assert.equal(serialized.includes(value), false, `view model leaked: ${value.slice(0, 60)}`);
    }
  });

  it("carries no denied key name, in the model or in the preflight report", () => {
    const report = policy.buildReport({
      viewModelVersion: model.version,
      providerId: "circuit-component-spec",
      providerContractVersion: 1,
      availableRecords: model.corpus.records,
      availableSources: model.corpus.sources,
      selectedSlugs: model.records.map((entry) => entry.identity.slug),
      counts: {},
    });

    const modelJson = JSON.stringify(model);
    for (const key of ["sha256", "evidenceExtract", "reviewedBy", "physicalPdfPageIndex"]) {
      assert.equal(modelJson.includes(key), false, `view model carries a ${key} key`);
    }
    // The report names denied FIELD KEYS by design — that is the audit trail —
    // but must never carry one of their values.
    const reportJson = JSON.stringify(report.urls) + JSON.stringify(report.records);
    for (const key of ["sha256", "evidence_extract", "reviewed_by"]) {
      assert.equal(reportJson.includes(key), false, `preflight carries a ${key} value`);
    }
  });

  it("publishes only http(s) citation URLs, and records all 154 decisions", () => {
    const report = policy.buildReport({
      viewModelVersion: model.version,
      providerId: "circuit-component-spec",
      providerContractVersion: 1,
      availableRecords: model.corpus.records,
      availableSources: model.corpus.sources,
      selectedSlugs: [],
      counts: {},
    });
    assert.equal(report.urls.length, 154);
    assert.equal(report.urls.filter((entry) => entry.decision === "ALLOW").length, 138);

    for (const source of model.records.flatMap((entry) => entry.sources)) {
      if (source.url === null) {
        assert.equal(source.authorityClass, "PROJECT_GENERATOR", String(source.sourceId));
        assert.ok(!CIRCUIT_SELECTION.linkableSourceIds.includes(String(source.sourceId)));
      } else {
        assert.match(source.url, /^https?:\/\//u);
      }
    }
  });
});

describe("repeated normalization of unchanged input is byte-stable", () => {
  it("projects identical JSON on a second pass", async () => {
    const second = projectIndex(
      await readEvidenceIndex(),
      new PublicationPolicy(CIRCUIT_PUBLICATION_MATRIX, CIRCUIT_SELECTION),
    );
    assert.equal(JSON.stringify(second), JSON.stringify(model));
  });
});

function sum<T>(values: readonly T[], size: (value: T) => number): number {
  return values.reduce((total, value) => total + size(value), 0);
}
