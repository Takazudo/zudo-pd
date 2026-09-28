/**
 * The joins, and every way they are allowed to fail.
 *
 * `parseBundle` and `indexEvidence` are pure, so each case here is a plain
 * object rather than a doctored copy of the evidence tree — the real
 * `.claude/skills/` is read-only to this feature and must stay that way.
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { ComponentDocsError, type ErrorCode } from "@takazudo/zudo-circuit-doc";
import {
  indexEvidence,
  parseBundle,
  PROVIDER_SCHEMA_VERSION,
  type ProviderBundle,
} from "@takazudo/zudo-circuit-doc";
import { BUNDLE_FILES, type BundleFile } from "./project-context.mjs";
import {
  bundleFiles,
  fixtureBundle,
  fixtureIntegrationRules,
  fixtureInventory,
} from "./provider-fixtures.ts";

type Overrides = Parameters<typeof fixtureBundle>[0];

function rejects(
  build: () => unknown,
  code: ErrorCode,
  message: RegExp,
  label = "",
): void {
  assert.throws(
    build,
    (error: unknown) => {
      assert.ok(error instanceof ComponentDocsError, `${label}: not a ComponentDocsError`);
      assert.equal(error.code, code, `${label}: ${error.message}`);
      assert.match(error.message, message, label);
      return true;
    },
    label,
  );
}

function indexing(overrides: Overrides = {}, inventoryOverrides = {}): () => unknown {
  return () =>
    indexEvidence(
      fixtureInventory(inventoryOverrides),
      [fixtureBundle(overrides)],
      fixtureIntegrationRules(),
    );
}

describe("the fixture corpus indexes cleanly", () => {
  it("resolves every relationship", () => {
    const index = indexEvidence(fixtureInventory(), [fixtureBundle()], fixtureIntegrationRules());
    assert.equal(index.records.length, 3);
    assert.deepEqual(index.totals, {
      sources: 4,
      facts: 5,
      coverage: 4,
      interactions: 1,
      routes: 3,
      pinMaps: 3,
      pins: 5,
    });
    assert.deepEqual(index.recordById.get("rec-handfit")?.pinMaps.length, 2);
    assert.deepEqual(index.recordById.get("rec-driver")?.route.route_id, "route-driver");
  });
});

describe("schema versions", () => {
  it("refuses a bundle file that declares an unsupported version", () => {
    for (const file of BUNDLE_FILES) {
      const files = { ...bundleFiles(fixtureBundle()) } as Record<BundleFile, unknown>;
      files[file] = { ...(files[file] as object), schema_version: PROVIDER_SCHEMA_VERSION + 1 };
      rejects(
        () => parseBundle("component-fixture", files),
        "ADAPTER_CONTRACT",
        /unsupported schema_version/u,
        file,
      );
    }
  });

  it("refuses a bundle file with no version at all", () => {
    const files = { ...bundleFiles(fixtureBundle()) } as Record<BundleFile, unknown>;
    files["facts.json"] = { facts: [] };
    rejects(
      () => parseBundle("component-fixture", files),
      "ADAPTER_CONTRACT",
      /unsupported schema_version/u,
    );
  });

  it("refuses a bundle file whose entry array is missing", () => {
    const files = { ...bundleFiles(fixtureBundle()) } as Record<BundleFile, unknown>;
    files["coverage.json"] = { schema_version: PROVIDER_SCHEMA_VERSION };
    rejects(
      () => parseBundle("component-fixture", files),
      "ADAPTER_CONTRACT",
      /no entry array/u,
    );
  });

  it("accepts the fixture bundle at the supported version", () => {
    const parsed = parseBundle("component-fixture", bundleFiles(fixtureBundle()));
    assert.equal(parsed.records.length, 3);
    assert.equal(parsed.pinMaps.length, 3);
  });

  it("refuses an inventory that declares an unsupported version", () => {
    const inventory = { ...fixtureInventory(), schema_version: PROVIDER_SCHEMA_VERSION + 1 };
    rejects(
      () => indexEvidence(inventory, [fixtureBundle()], fixtureIntegrationRules()),
      "ADAPTER_CONTRACT",
      /inventory schema_version/u,
    );
  });
});

describe("duplicate ids", () => {
  it("refuses two records with the same id", () => {
    rejects(
      indexing({ records: (records) => [...records, { ...records[0] }] }),
      "ADAPTER_CONTRACT",
      /duplicate record id/u,
    );
  });

  it("refuses two sources with the same id", () => {
    rejects(
      indexing({ sources: (sources) => [...sources, { ...sources[0] }] }),
      "ADAPTER_CONTRACT",
      /duplicate source id/u,
    );
  });

  it("refuses two facts with the same id", () => {
    rejects(
      indexing({ facts: (facts) => [...facts, { ...facts[0] }] }),
      "ADAPTER_CONTRACT",
      /duplicate fact id/u,
    );
  });

  it("refuses two coverage domains with the same id", () => {
    rejects(
      indexing({ coverage: (coverage) => [...coverage, { ...coverage[0] }] }),
      "ADAPTER_CONTRACT",
      /duplicate coverage domain id/u,
    );
  });

  it("refuses two pin maps with the same id", () => {
    rejects(
      indexing({ pinMaps: (pinMaps) => [...pinMaps, { ...pinMaps[0] }] }),
      "ADAPTER_CONTRACT",
      /duplicate pin map id/u,
    );
  });

  it("refuses two interactions with the same id, even in different bundles", () => {
    const other: ProviderBundle = {
      ...emptyBundle("component-other"),
      interactions: fixtureBundle().interactions,
    };
    rejects(
      () => indexEvidence(fixtureInventory(), [fixtureBundle(), other], fixtureIntegrationRules()),
      "ADAPTER_CONTRACT",
      /duplicate interaction id/u,
    );
  });

  it("refuses a record that lists the same source twice", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-driver"
              ? { ...record, source_ids: [...record.source_ids, "src-driver-primary"] }
              : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /lists the same source twice/u,
    );
  });
});

describe("unresolved and orphaned ids", () => {
  it("refuses a record whose inventory line does not exist", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-driver" ? { ...record, line_id: "line-gone" } : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /unknown inventory line/u,
    );
  });

  it("refuses a record the inventory assigns to a different owner skill", () => {
    rejects(
      indexing({}, { lines: (lines: { owner_skill: string }[]) =>
        lines.map((line, position) =>
          position === 0 ? { ...line, owner_skill: "component-elsewhere" } : line,
        ),
      }),
      "ADAPTER_CONTRACT",
      /the inventory does not assign it to/u,
    );
  });

  it("refuses a manifest that lists a source the provider does not have", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-driver"
              ? { ...record, source_ids: [...record.source_ids, "src-gone"] }
              : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /lists a source the provider does not have/u,
    );
  });

  it("refuses a manifest that lists a fact the provider does not have", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-driver"
              ? { ...record, fact_ids: [...record.fact_ids, "fact-gone"] }
              : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /lists a fact the provider does not have/u,
    );
  });

  it("refuses a source whose record does not exist", () => {
    rejects(
      indexing({
        sources: (sources) => [...sources, { ...sources[0], source_id: "src-orphan", record_id: "rec-gone" }],
      }),
      "ADAPTER_CONTRACT",
      /source names a record the provider does not have/u,
    );
  });

  it("refuses a coverage domain whose record does not exist", () => {
    rejects(
      indexing({
        coverage: (coverage) => [
          ...coverage,
          { ...coverage[0], coverage_id: "cov-orphan", record_id: "rec-gone" },
        ],
      }),
      "ADAPTER_CONTRACT",
      /coverage domain names a record the provider does not have/u,
    );
  });

  it("refuses a source its own record's manifest never lists", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-driver"
              ? { ...record, source_ids: ["src-driver-primary"] }
              : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /source is not listed by the record that owns it/u,
    );
  });

  it("refuses a fact its own record's manifest never lists", () => {
    rejects(
      indexing({
        facts: (facts) => [...facts, { ...facts[1], fact_id: "fact-driver-unlisted" }],
      }),
      "ADAPTER_CONTRACT",
      /fact is not listed by the record that owns it/u,
    );
  });

  it("refuses an entity held by a bundle that does not own its record", () => {
    const other: ProviderBundle = {
      ...emptyBundle("component-other"),
      pinMaps: [
        {
          pin_map_id: "pinmap-elsewhere",
          record_id: "rec-driver",
          symbol: "X",
          footprint: "Y",
          pins: [],
        },
      ],
    };
    rejects(
      () => indexEvidence(fixtureInventory(), [fixtureBundle(), other], fixtureIntegrationRules()),
      "ADAPTER_CONTRACT",
      /held by a bundle that does not own its record/u,
    );
  });

  it("refuses a fact citing a source the provider does not have", () => {
    rejects(
      indexing({
        facts: (facts) =>
          facts.map((entry) =>
            entry.fact_id === "fact-driver-vin-max" ? { ...entry, source_id: "src-gone" } : entry,
          ),
      }),
      "ADAPTER_CONTRACT",
      /cites a source the provider does not have/u,
    );
  });

  it("refuses a fact citing another record's source", () => {
    rejects(
      indexing({
        facts: (facts) =>
          facts.map((entry) =>
            entry.fact_id === "fact-driver-vin-max"
              ? { ...entry, source_id: "src-sense-primary" }
              : entry,
          ),
      }),
      "ADAPTER_CONTRACT",
      /cites a source owned by another record/u,
    );
  });

  it("refuses a coverage domain naming a fact the provider does not have", () => {
    rejects(
      indexing({
        coverage: (coverage) =>
          coverage.map((entry) =>
            entry.coverage_id === "cov-driver-thermal"
              ? { ...entry, blocking_fact_ids: ["fact-gone"] }
              : entry,
          ),
      }),
      "ADAPTER_CONTRACT",
      /coverage domain names a fact the provider does not have/u,
    );
  });

  it("refuses an interaction naming a record the provider does not have", () => {
    rejects(
      indexing({
        interactions: (values) =>
          values.map((entry) => ({ ...entry, record_ids: [...entry.record_ids, "rec-gone"] })),
      }),
      "ADAPTER_CONTRACT",
      /interaction names a record the provider does not have/u,
    );
  });

  it("refuses an interaction naming a fact the provider does not have", () => {
    rejects(
      indexing({
        interactions: (values) =>
          values.map((entry) => ({ ...entry, fact_ids: [...entry.fact_ids, "fact-gone"] })),
      }),
      "ADAPTER_CONTRACT",
      /interaction names a fact the provider does not have/u,
    );
  });

  it("refuses an interaction that names no records at all", () => {
    rejects(
      indexing({
        records: (records) => records.map((record) => ({ ...record, interaction_ids: [] })),
        interactions: (values) => values.map((entry) => ({ ...entry, record_ids: [] })),
      }),
      "ADAPTER_CONTRACT",
      /interaction names no records/u,
    );
  });

  it("refuses a manifest whose interaction_ids disagree with the interactions", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-sense" ? { ...record, interaction_ids: [] } : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /manifest interaction_ids disagree/u,
    );
  });

  it("refuses a record without exactly one routing entry", () => {
    rejects(
      indexing({ routes: (routes) => routes.slice(1) }),
      "ADAPTER_CONTRACT",
      /exactly one routing entry/u,
    );
  });
});

describe("parent and subordinate structure", () => {
  it("refuses a subordinate with no parent", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-sense" ? { ...record, parent_record_id: null } : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /no parent_record_id/u,
    );
  });

  it("refuses a subordinate whose parent does not exist", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-sense"
              ? { ...record, parent_record_id: "rec-gone" }
              : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /names a parent the provider does not have/u,
    );
  });

  it("refuses a standalone that names a parent", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-handfit"
              ? { ...record, parent_record_id: "rec-driver" }
              : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /kind and parent_record_id disagree/u,
    );
  });

  it("refuses a subordinate parented to another subordinate", () => {
    rejects(
      indexing({
        records: (records) =>
          records.map((record) =>
            record.record_id === "rec-handfit"
              ? { ...record, kind: "subordinate" as const, parent_record_id: "rec-sense" }
              : record,
          ),
      }),
      "ADAPTER_CONTRACT",
      /kind and parent_record_id disagree/u,
    );
  });
});

describe("calculated dependencies", () => {
  it("refuses a dependency on a fact the provider does not have", () => {
    rejects(
      indexing({
        facts: (facts) =>
          facts.map((entry) =>
            entry.fact_id === "fact-driver-current-min"
              ? { ...entry, depends_on: ["fact-gone"] }
              : entry,
          ),
      }),
      "ADAPTER_CONTRACT",
      /depends on a fact the provider does not have/u,
    );
  });

  it("refuses a self-referencing dependency", () => {
    rejects(
      indexing({
        facts: (facts) =>
          facts.map((entry) =>
            entry.fact_id === "fact-driver-vin-max"
              ? { ...entry, depends_on: ["fact-driver-vin-max"] }
              : entry,
          ),
      }),
      "ADAPTER_CONTRACT",
      /form a cycle/u,
    );
  });

  it("refuses a cycle that crosses records", () => {
    rejects(
      indexing({
        facts: (facts) =>
          facts.map((entry) =>
            entry.fact_id === "fact-sense-resistance-max"
              ? { ...entry, depends_on: ["fact-driver-current-min"] }
              : entry,
          ),
      }),
      "ADAPTER_CONTRACT",
      /form a cycle/u,
    );
  });

  it("accepts a diamond — a shared dependency is not a cycle", () => {
    const index = indexEvidence(fixtureInventory(), [
      fixtureBundle({
        facts: (facts) =>
          facts.map((entry) =>
            entry.fact_id === "fact-driver-vin-max"
              ? { ...entry, depends_on: ["fact-sense-resistance-max"] }
              : entry,
          ),
      }),
    ], fixtureIntegrationRules());
    assert.equal(index.factById.get("fact-driver-vin-max")?.depends_on.length, 1);
  });

  it("names the cycle it found", () => {
    try {
      indexing({
        facts: (facts) =>
          facts.map((entry) =>
            entry.fact_id === "fact-sense-resistance-max"
              ? { ...entry, depends_on: ["fact-driver-current-min"] }
              : entry,
          ),
      })();
      assert.fail("expected a cycle failure");
    } catch (error) {
      assert.ok(error instanceof ComponentDocsError);
      const cycle = error.detail.cycle as readonly string[];
      assert.ok(cycle.includes("fact-driver-current-min"));
      assert.ok(cycle.includes("fact-sense-resistance-max"));
    }
  });
});

function emptyBundle(skill: string): ProviderBundle {
  return {
    skill,
    records: [],
    sources: [],
    facts: [],
    coverage: [],
    routes: [],
    interactions: [],
    pinMaps: [],
  };
}
