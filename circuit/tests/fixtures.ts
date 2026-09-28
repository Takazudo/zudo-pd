/**
 * Renderer fixtures.
 *
 * The renderers are written against the frozen view-model types, not against
 * the circuit adapter, so they are exercised here on data shaped like the real
 * corpus but built in this file. That is deliberate and not a stopgap: it is
 * what lets a page be tested for a state the current evidence does not happen
 * to contain — an open domain with no blocker, a source that could not be
 * retrieved, a record carrying two pin maps — without waiting for the evidence
 * to grow one.
 *
 * Every shape here was read off the real bundles under `.claude/skills/` before
 * it was written down, so the fixtures are representative rather than
 * convenient:
 *
 *   - verdicts, provenance values, fact classes, authority classes and
 *     availability strings are the exact strings the corpus uses;
 *   - `fact-fixture-current-max` depends on a fact owned by a DIFFERENT record,
 *     matching the seven real cross-record calculations;
 *   - `fact-fixture-identity` carries a structured object flattened to text,
 *     matching the three real dict-valued facts;
 *   - one record carries two pin maps, matching `rec-jst-b6b-xh-a`;
 *   - one source is `SOURCE UNAVAILABLE` with no publishable URL, matching the
 *     twelve real unavailable sources.
 *
 * Everything is built through `safeText`/`anchor`/`recordSlug`, so a fixture
 * that could not be published for real cannot be published here either.
 */

import { anchor, recordSlug } from "@takazudo/zudo-circuit-doc";
import { literal, safeText, type SafeText } from "@takazudo/zudo-circuit-doc";
import { assertSafeUrl } from "@takazudo/zudo-circuit-doc";
import { VIEW_MODEL_VERSION } from "@takazudo/zudo-circuit-doc";
import type {
  CorpusSummary,
  PublicCoverage,
  PublicFact,
  PublicIntegrationRule,
  PublicInteraction,
  PublicPinMap,
  PublicRecord,
  PublicRecordIdentity,
  PublicRecordReference,
  PublicSource,
  PublicViewModel,
} from "@takazudo/zudo-circuit-doc";

function t(value: string): SafeText {
  return safeText(value, { field: "fixture" });
}

/**
 * Text a hostile or merely unlucky evidence string can legitimately contain.
 *
 * None of this is rejected by `safeText` — braces, angle brackets, pipes,
 * backslashes and directive markers are ordinary punctuation in a datasheet
 * locator, and rejecting them would make the sanitiser refuse real evidence.
 * They are exactly the characters that turn into live MDX if the serializer
 * ever stops escaping them, so a fixture carries all of them at once.
 */
export const HOSTILE_TEXT =
  "brace {expr} angle <Tag> pipe | backslash \\ fence --- directive :::note " +
  "esm import x from \"y\" backtick ` dollar ${x}";

/**
 * The one construct the guard refuses outright, escaped or not.
 *
 * `assertMdxSafe` fails on any line containing `<!--`, without asking whether
 * the `<` was escaped — so an evidence string carrying an HTML comment cannot
 * be published even though the serializer has already neutralised it. That is a
 * false positive, but it fails CLOSED: the build stops and a human decides,
 * rather than a page shipping something unexpected. Nothing in the current
 * corpus contains it. Kept separate from `HOSTILE_TEXT` so the rejection can be
 * asserted deliberately instead of blocking every other hostile-input test.
 */
export const GUARD_REJECTED_TEXT = "an evidence locator quoting <!-- an HTML comment -->";

/** A long single value, at the scale of the longest real coverage reason. */
export const LONG_TEXT = `${"Retrieval attempted repeatedly against the vendor's own site; ".repeat(
  12,
)}and the document remains unobtainable.`;

// --- builders --------------------------------------------------------------

type IdentityInput = {
  readonly recordId: string;
  readonly kind: "standalone" | "subordinate";
  readonly parentRecordId?: string;
  readonly mpn: string;
  readonly manufacturer?: string;
  readonly lcsc?: string;
  readonly packageName?: string;
  readonly function?: string;
  readonly identityState?: string;
  readonly sourceState?: string;
  readonly dnp?: boolean;
  readonly ownerSkill?: string;
  readonly placements?: readonly (readonly [board: string, refdes: string])[];
};

function identity(input: IdentityInput): PublicRecordIdentity {
  const parentRecordId = input.parentRecordId ?? null;
  return {
    recordId: t(input.recordId),
    slug: recordSlug(input.recordId),
    anchor: anchor(input.recordId),
    kind: input.kind,
    parentRecordId: parentRecordId === null ? null : t(parentRecordId),
    parentSlug: parentRecordId === null ? null : recordSlug(parentRecordId),
    lineId: t(input.recordId.replace(/^rec-/u, "line-")),
    ownerSkill: t(input.ownerSkill ?? "component-fixture-bundle"),
    mpn: t(input.mpn),
    manufacturer: t(input.manufacturer ?? "Fixture Semiconductor"),
    lcsc: t(input.lcsc ?? "C000001"),
    packageName: t(input.packageName ?? "SOT-23-6"),
    function: t(input.function ?? "fixture part"),
    identityState: t(input.identityState ?? "UNRESOLVED"),
    sourceState: t(input.sourceState ?? "SOURCE UNAVAILABLE"),
    dnp: input.dnp ?? false,
    placements: (input.placements ?? [["board-l", "U1"]]).map(([board, refdes]) => ({
      board: t(board),
      refdes: t(refdes),
      dnp: input.dnp ?? false,
    })),
  };
}

/**
 * A structured fact value as the adapter publishes it: ordered key/value pairs,
 * sorted `byCodeUnit` on the key. Three real facts carry one — the
 * distributor-identity bindings, `{lcsc, manufacturer, mpn, variant}` — and the
 * evidence contract forbids flattening them to a string.
 */
type FixtureValueEntry = { readonly key: string; readonly value: number | string };

type FactInput = {
  readonly factId: string;
  readonly recordId: string;
  readonly sourceId: string;
  readonly factClass: string;
  readonly value: number | string | readonly FixtureValueEntry[];
  readonly unit?: string;
  readonly conditions: string;
  readonly locator: string;
  readonly provenance: string;
  readonly verdict: string;
  readonly dependsOn?: readonly string[];
  readonly expression?: string;
};

function factValue(value: FactInput["value"]): PublicFact["value"] {
  if (typeof value === "number") return value;
  if (typeof value === "string") return t(value);
  return value.map((entry) => ({
    key: t(entry.key),
    value: typeof entry.value === "number" ? entry.value : t(entry.value),
  }));
}

function fact(input: FactInput): PublicFact {
  return {
    factId: t(input.factId),
    anchor: anchor(input.factId),
    recordId: t(input.recordId),
    sourceId: t(input.sourceId),
    factClass: t(input.factClass),
    value: factValue(input.value),
    unit: t(input.unit ?? "NONE"),
    conditions: t(input.conditions),
    locator: t(input.locator),
    provenance: t(input.provenance),
    verdict: t(input.verdict),
    dependsOn: (input.dependsOn ?? []).map(t),
    expression: safeText(input.expression ?? "", { field: "fixture", allowEmpty: true }),
  };
}

type SourceInput = {
  readonly sourceId: string;
  readonly documentTitle: string;
  readonly documentNumber?: string;
  readonly revision?: string;
  readonly authorityClass?: string;
  readonly availability?: string;
  readonly locator: string;
  readonly url?: string;
};

function source(input: SourceInput): PublicSource {
  return {
    sourceId: t(input.sourceId),
    anchor: anchor(input.sourceId),
    documentTitle: t(input.documentTitle),
    documentNumber: t(input.documentNumber ?? "not stated"),
    revision: t(input.revision ?? "not stated"),
    documentDate: t("2026-04"),
    retrievalDate: t("2026-08-02"),
    authorityClass: t(input.authorityClass ?? "MANUFACTURER_PRIMARY"),
    availability: t(input.availability ?? "AVAILABLE"),
    locator: t(input.locator),
    printedPageLabel: t("2 of 18"),
    url: input.url === undefined ? null : assertSafeUrl(input.url, "fixture url"),
  };
}

/**
 * A record's curated references.
 *
 * Both optional halves default to unresolved so the renderer's stated-reason
 * branch is exercised without a caller opting in. This is the ONLY corpus that
 * still reaches that branch on the model half: since wave 7 sourced a pair for
 * all 27 packages, the real corpus resolves every model, and these fixtures
 * are what keeps the unresolved path from rotting (see `model-viewer.test.ts`).
 * The document half is unresolved for `rec-c335982` alone in the real corpus;
 * passing `document` exercises the resolved branch the other 40 records take.
 */
function referenceFor(
  input: {
    readonly recordId: string;
    readonly footprintName?: string;
    readonly document?: {
      readonly sourceId: string;
      readonly documentTitle: string;
      readonly label: "Datasheet PDF" | "Specification PDF" | "Mechanical drawing PDF";
      readonly authorityClass: string;
      readonly url: string;
      readonly availability: string;
      readonly documentKind: "datasheet" | "specification" | "drawing";
    };
  },
): PublicRecordReference {
  const footprintName = input.footprintName ?? "FIXTURE-PKG-8";
  return {
    document: input.document === undefined
      ? null
      : {
        sourceId: t(input.document.sourceId),
        documentTitle: t(input.document.documentTitle),
        label: t(input.document.label),
        authorityClass: t(input.document.authorityClass),
        url: assertSafeUrl(input.document.url, `${input.recordId} fixture document url`),
        availability: t(input.document.availability),
        documentKind: input.document.documentKind,
      },
    documentUnresolvedReason: input.document === undefined
      ? t("No single document has been reviewed as this component's authoritative PDF yet.")
      : null,
    footprint: {
      packageId: t(footprintName),
      footprintName: t(footprintName),
      footprintPath: t(`footprints/kicad/zudo-power.pretty/${footprintName}.kicad_mod`),
      model: null,
      modelUnresolvedReason: t("The KiCad footprint names no 3D model."),
    },
  };
}

type CoverageInput = {
  readonly coverageId: string;
  readonly recordId: string;
  readonly domain: string;
  readonly status: "COVERED" | "OPEN";
  readonly reason: string;
  readonly factIds?: readonly string[];
  readonly blockingFactIds?: readonly string[];
};

function coverage(input: CoverageInput): PublicCoverage {
  return {
    coverageId: t(input.coverageId),
    anchor: anchor(input.coverageId),
    recordId: t(input.recordId),
    domain: t(input.domain),
    status: input.status,
    reason: t(input.reason),
    factIds: (input.factIds ?? []).map(t),
    blockingFactIds: (input.blockingFactIds ?? []).map(t),
  };
}

function interaction(input: {
  readonly interactionId: string;
  readonly recordIds: readonly string[];
  readonly factIds?: readonly string[];
  readonly conditions: string;
  readonly verdict: string;
}): PublicInteraction {
  return {
    interactionId: t(input.interactionId),
    anchor: anchor(input.interactionId),
    recordIds: input.recordIds.map(t),
    factIds: (input.factIds ?? []).map(t),
    conditions: t(input.conditions),
    verdict: t(input.verdict),
  };
}

function pinMap(input: {
  readonly pinMapId: string;
  readonly recordId: string;
  readonly symbol: string;
  readonly footprint: string;
  readonly pins: readonly (readonly [pin: string, name: string, pad: string, fn: string])[];
}): PublicPinMap {
  return {
    pinMapId: t(input.pinMapId),
    anchor: anchor(input.pinMapId),
    recordId: t(input.recordId),
    symbol: t(input.symbol),
    footprint: t(input.footprint),
    pins: input.pins.map(([symbolPin, name, footprintPad, fn]) => ({
      symbolPin: t(symbolPin),
      name: t(name),
      footprintPad: t(footprintPad),
      function: t(fn),
    })),
  };
}

function corpus(records: readonly PublicRecord[]): CorpusSummary {
  const sum = (pick: (record: PublicRecord) => number): number =>
    records.reduce((total, record) => total + pick(record), 0);

  return {
    ownerBundles: 2,
    records: records.length,
    standaloneRecords: records.filter((r) => r.identity.kind === "standalone").length,
    subordinateRecords: records.filter((r) => r.identity.kind === "subordinate").length,
    sources: sum((r) => r.sources.length),
    facts: sum((r) => r.facts.length),
    coverageDomains: sum((r) => r.coverage.length),
    interactions: sum((r) => r.interactions.length),
    pinMaps: sum((r) => r.pinMaps.length),
    pins: sum((r) => r.pinMaps.reduce((n, map) => n + map.pins.length, 0)),
    inventoryLines: records.length,
    fittedLines: records.filter((r) => !r.identity.dnp).length,
    dnpOrHandFitLines: records.filter((r) => r.identity.dnp).length,
  };
}

function model(
  records: readonly PublicRecord[],
  integration: readonly PublicIntegrationRule[] = [],
): PublicViewModel {
  return {
    version: VIEW_MODEL_VERSION,
    provider: { id: t("fixture-provider"), contractVersion: 1 },
    corpus: corpus(records),
    records,
    integration,
  };
}

/**
 * Cross-component rules covering every shape the integration page renders.
 *
 * The three between them exercise: a calculation evaluated at several inputs, a
 * calculation with a single bare result and no varied input, an evidence chain
 * containing a stage with no facts at all, a rule with neither calculations nor
 * a chain, and a rule whose free text is MDX-active throughout — the last one
 * matters because a refusal is the longest untrusted string on the page and is
 * the one thing the page may never fail to render.
 */
export function fixtureIntegration(): PublicIntegrationRule[] {
  return [
    {
      ruleId: t("rule-fixture-power-stage"),
      anchor: anchor("rule-fixture-power-stage"),
      ownerSkill: t("circuit-fixture-integration"),
      domain: t("fixture-power-stage"),
      recordIds: [t(FIXTURE_IDS.driverRecord), t(FIXTURE_IDS.senseRecord)],
      factIds: [t("fact-fixture-current-max"), t("fact-fixture-sense-resistance")],
      conditions: t("sense tolerance, driver hysteresis and the assembled thermal path"),
      verdict: t("NEEDS BENCH"),
      refusal: t("Do not promote nominal arithmetic to a guaranteed assembled-stage PASS."),
      calculations: [
        {
          calculationId: t("calc-fixture-current"),
          anchor: anchor("calc-fixture-current"),
          factIds: [t("fact-fixture-sense-resistance")],
          expression: t("0.096 / r_sense_ohm"),
          resultKey: t("current_a"),
          conditions: t("nominal division only; excludes hysteresis, TCR and self-heating"),
          cases: [
            { inputs: [{ key: t("r_sense_ohm"), value: 0.198 }], value: 0.48484848484848486 },
            { inputs: [{ key: t("r_sense_ohm"), value: 0.21 }], value: 0.45714285714285713 },
          ],
        },
        {
          calculationId: t("calc-fixture-margin"),
          anchor: anchor("calc-fixture-margin"),
          factIds: [],
          expression: t("fact_fixture_vin_max - 32.4"),
          resultKey: t("margin_v"),
          conditions: t("conditioned subtraction at one table point; not a waveform measurement"),
          cases: [{ inputs: [], value: 9.6 }],
        },
      ],
      evidenceChain: [],
    },
    {
      ruleId: t("rule-fixture-chain"),
      anchor: anchor("rule-fixture-chain"),
      ownerSkill: t("circuit-fixture-integration"),
      domain: t("fixture-source-to-bench-chain"),
      recordIds: [t(FIXTURE_IDS.driverRecord)],
      // A fact the model does not publish: the reference must still be printed,
      // marked as unpublished, rather than silently dropped or linked to a 404.
      factIds: [t("fact-fixture-current-max"), t("fact-fixture-absent")],
      conditions: t("trace each claim from the vendor document through to a measurement"),
      verdict: t("NEEDS BENCH"),
      refusal: t("A completed upstream stage never implies a later measured stage."),
      calculations: [],
      evidenceChain: [
        {
          stage: t("official-source"),
          status: t("MIXED"),
          factIds: [t("fact-fixture-current-max")],
        },
        { stage: t("bench"), status: t("OPEN"), factIds: [] },
      ],
    },
    {
      ruleId: t("rule-fixture-hostile"),
      anchor: anchor("rule-fixture-hostile"),
      ownerSkill: t("circuit-fixture-integration"),
      domain: t(HOSTILE_TEXT),
      recordIds: [t(FIXTURE_IDS.hostileRecord)],
      factIds: [],
      conditions: t(HOSTILE_TEXT),
      verdict: t("UNSOURCED"),
      refusal: t(HOSTILE_TEXT),
      calculations: [],
      evidenceChain: [],
    },
  ];
}

// --- the records -----------------------------------------------------------

/** Every published ID the main fixture uses, so tests can assert against them. */
export const FIXTURE_IDS = {
  driverRecord: "rec-fixture-driver",
  senseRecord: "rec-fixture-sense",
  hostileRecord: "rec-fixture-hostile",
  driverSlug: "fixture-driver",
  senseSlug: "fixture-sense",
  crossRecordFact: "fact-fixture-current-max",
  foreignDependency: "fact-fixture-sense-resistance",
  unpublishedDependency: "fact-fixture-not-published",
  structuredValueFact: "fact-fixture-identity",
  openWithBlockers: "cov-fixture-thermal",
  openWithoutBlockers: "cov-fixture-led",
  covered: "cov-fixture-pins",
  unavailableSource: "src-fixture-unreachable",
  availableSource: "src-fixture-datasheet",
  firstPinMap: "pinmap-fixture-driver",
  secondPinMap: "pinmap-fixture-driver-harness",
  interaction: "int-fixture-control",
  /** The default `identity()` applies when a record does not name its own. */
  ownerSkill: "component-fixture-bundle",
} as const;

/**
 * A standalone driver: facts across several classes and every verdict the
 * corpus uses, a retrievable source and an unretrievable one, all three
 * coverage states, two pin maps, and a calculation that reaches into the
 * subordinate record below.
 */
function driverRecord(): PublicRecord {
  return {
    // The one fixture whose document card resolves: the real corpus has no
    // curated `documentSelections` yet, so without this the resolved branch
    // of the renderer would never be exercised at all.
    reference: referenceFor({
      recordId: FIXTURE_IDS.driverRecord,
      footprintName: "MSOP-8_L3.0-W3.0-P0.65-LS4.9-BL-EP1.8",
      document: {
        sourceId: "src-fixture-driver-ds",
        documentTitle: "FX8860MP-13 datasheet",
        label: "Datasheet PDF",
        authorityClass: "MANUFACTURER_PRIMARY",
        url: "https://example.invalid/fx8860mp-13.pdf",
        availability: "AVAILABLE",
        documentKind: "datasheet",
      },
    }),
    identity: identity({
      recordId: FIXTURE_IDS.driverRecord,
      kind: "standalone",
      mpn: "FX8860MP-13",
      manufacturer: "Fixture Semiconductor",
      lcsc: "C100001",
      packageName: "MSOP-8EP",
      function: "buck LED driver",
      identityState: "VERIFIED",
      sourceState: "AVAILABLE",
      placements: [
        ["board-l", "U2"],
        ["board-p", "U7"],
      ],
    }),
    aliases: {
      mpn: [t("FX8860MP-13"), t("FX8860")],
      lcsc: [t("C100001")],
      manufacturer: [t("Fixture Semiconductor")],
      function: [t("buck LED driver")],
    },
    sources: [
      source({
        sourceId: FIXTURE_IDS.availableSource,
        documentTitle: "FX8860 40V 1.5A Buck LED Driver",
        documentNumber: "DS39014",
        revision: "Rev. 8-2",
        locator: "Absolute Maximum and Electrical Characteristics tables",
        url: "https://example.invalid/datasheet/FX8860.pdf",
      }),
      source({
        sourceId: FIXTURE_IDS.unavailableSource,
        documentTitle: "FX8860 vendor site retrieval attempt",
        authorityClass: "MANUFACTURER_MIRROR",
        availability: "SOURCE UNAVAILABLE",
        locator: LONG_TEXT,
      }),
    ],
    facts: [
      fact({
        factId: "fact-fixture-vin-absolute-max",
        recordId: FIXTURE_IDS.driverRecord,
        sourceId: FIXTURE_IDS.availableSource,
        factClass: "ABSOLUTE_MAXIMUM",
        value: 42,
        unit: "V",
        conditions: "absolute maximum, not an operating condition",
        locator: `${FIXTURE_IDS.availableSource}: Absolute Maximum Ratings table row VIN`,
        provenance: "PRIMARY-SPEC",
        verdict: "PASS - primary-source confirmed",
      }),
      fact({
        factId: "fact-fixture-vin-recommended-max",
        recordId: FIXTURE_IDS.driverRecord,
        sourceId: FIXTURE_IDS.availableSource,
        factClass: "RECOMMENDED_OPERATION",
        value: 40,
        unit: "V",
        conditions: "functional input range, TA=25 C unless specified",
        locator: `${FIXTURE_IDS.availableSource}: Recommended Operating Conditions row VIN`,
        provenance: "PRIMARY-SPEC",
        verdict: "PASS - primary-source confirmed",
      }),
      fact({
        factId: "fact-fixture-isat",
        recordId: FIXTURE_IDS.driverRecord,
        sourceId: FIXTURE_IDS.unavailableSource,
        factClass: "GUARANTEED_ELECTRICAL",
        value: 2.1,
        unit: "A",
        conditions: "mirror-only max-design column; primary document shows typical only",
        locator: `${FIXTURE_IDS.unavailableSource}: saturation current column`,
        provenance: "UNVERIFIED",
        verdict: "UNSOURCED",
      }),
      fact({
        factId: "fact-fixture-thermal-rise",
        recordId: FIXTURE_IDS.driverRecord,
        sourceId: FIXTURE_IDS.availableSource,
        factClass: "THERMAL_SOA",
        value: "unresolved at the installed copper area and ambient",
        conditions: "installed board, still air, LED string at full current",
        locator: "CALCULATED: requires bench measurement",
        provenance: "PROJECT-CHOICE",
        verdict: "NEEDS BENCH",
      }),
      // The cross-record calculation. Its second input is owned by the
      // subordinate record, which is what makes the dependency links leave the
      // page instead of resolving inside it.
      fact({
        factId: FIXTURE_IDS.crossRecordFact,
        recordId: FIXTURE_IDS.driverRecord,
        sourceId: FIXTURE_IDS.availableSource,
        factClass: "PROJECT_STATE",
        value: 0.5252525252525252,
        unit: "A",
        conditions: "maximum sense threshold over minimum initial sense resistance at 25 C",
        locator: "CALCULATED: fact-fixture-sense-max divided by fact-fixture-sense-resistance",
        provenance: "CALCULATED",
        verdict: "NEEDS BENCH",
        dependsOn: [
          "fact-fixture-sense-max",
          FIXTURE_IDS.foreignDependency,
          FIXTURE_IDS.unpublishedDependency,
        ],
        expression: "fact_fixture_sense_max / fact_fixture_sense_resistance",
      }),
      fact({
        factId: "fact-fixture-sense-max",
        recordId: FIXTURE_IDS.driverRecord,
        sourceId: FIXTURE_IDS.availableSource,
        factClass: "GUARANTEED_ELECTRICAL",
        value: 0.104,
        unit: "V",
        conditions: "upper sense threshold over the full temperature range",
        locator: `${FIXTURE_IDS.availableSource}: Electrical Characteristics row VSENSE`,
        provenance: "PRIMARY-SPEC",
        verdict: "PASS - primary-source confirmed",
      }),
      // A distributor-identity fact whose recorded value is a structured object,
      // flattened by the adapter into one published string.
      fact({
        factId: FIXTURE_IDS.structuredValueFact,
        recordId: FIXTURE_IDS.driverRecord,
        sourceId: FIXTURE_IDS.availableSource,
        factClass: "PROJECT_STATE",
        // Entries arrive sorted byCodeUnit on the key, as the adapter emits them.
        value: [
          { key: "lcsc", value: "C100001" },
          { key: "manufacturer", value: "Fixture Semiconductor" },
          { key: "mpn", value: "FX8860MP-13" },
          { key: "variant", value: "exact orderable driver" },
        ],
        conditions: "stable distributor identity binding; supplies no electrical authority",
        locator: `${FIXTURE_IDS.availableSource}: title block and distributor row C100001`,
        provenance: "DISTRIBUTOR-IDENTITY",
        verdict: "CONFIRMED - distributor identity only",
      }),
      fact({
        factId: "fact-fixture-not-relevant",
        recordId: FIXTURE_IDS.driverRecord,
        sourceId: FIXTURE_IDS.availableSource,
        factClass: "TRANSIENT",
        value: "no inrush limiter is fitted on this rail",
        conditions: "as-built design",
        locator: `${FIXTURE_IDS.availableSource}: Application Information`,
        provenance: "PROJECT-CHOICE",
        verdict: "NOT APPLICABLE",
      }),
      // A class this renderer has no gloss for, to prove new evidence
      // vocabulary still publishes.
      fact({
        factId: "fact-fixture-future-class",
        recordId: FIXTURE_IDS.driverRecord,
        sourceId: FIXTURE_IDS.availableSource,
        factClass: "ACOUSTIC_EMISSION",
        value: "not characterised",
        conditions: "audible range under PWM dimming",
        locator: `${FIXTURE_IDS.availableSource}: not covered`,
        provenance: "UNVERIFIED",
        verdict: "SOMETHING ENTIRELY NEW",
      }),
    ],
    coverage: [
      coverage({
        coverageId: FIXTURE_IDS.covered,
        recordId: FIXTURE_IDS.driverRecord,
        domain: "pin-topology-and-ep",
        status: "COVERED",
        reason: "The pin map and the exposed-pad handling are confirmed against the datasheet.",
        factIds: ["fact-fixture-vin-absolute-max", "fact-fixture-vin-recommended-max"],
      }),
      coverage({
        coverageId: FIXTURE_IDS.openWithBlockers,
        recordId: FIXTURE_IDS.driverRecord,
        domain: "thermal-derating-and-copper-area",
        status: "OPEN",
        reason:
          "The mirror's max-design saturation column is absent from the primary document, so " +
          "the current margin cannot be closed from documents alone.",
        factIds: ["fact-fixture-isat", "fact-fixture-thermal-rise"],
        blockingFactIds: ["fact-fixture-isat", "fact-fixture-thermal-rise"],
      }),
      // The no-applicable-blocker state: open, but what is missing has not been
      // reduced to a recorded fact, so there is nothing to link.
      coverage({
        coverageId: FIXTURE_IDS.openWithoutBlockers,
        recordId: FIXTURE_IDS.driverRecord,
        domain: "led-string-voltage-temperature",
        status: "OPEN",
        reason:
          "Exact LED forward voltage against current and temperature requires the LED record " +
          "and a bench waveform.",
      }),
    ],
    interactions: [
      interaction({
        interactionId: FIXTURE_IDS.interaction,
        recordIds: [FIXTURE_IDS.driverRecord, FIXTURE_IDS.senseRecord],
        factIds: [FIXTURE_IDS.crossRecordFact, FIXTURE_IDS.foreignDependency],
        conditions: "CTRL driven by the controller PWM with the sense resistor at 25 C",
        verdict: "NEEDS BENCH",
      }),
    ],
    // Two maps on one record: the same part documented in two contexts.
    pinMaps: [
      pinMap({
        pinMapId: FIXTURE_IDS.firstPinMap,
        recordId: FIXTURE_IDS.driverRecord,
        symbol: "FX8860MP-13",
        footprint: "MSOP-8_L3.0-W3.0-P0.65-LS4.9-BL-EP1.8",
        pins: [
          ["1", "SET", "1", "sense input"],
          ["2", "GND", "2", "ground"],
          ["4", "CTRL", "4", "PWM/analog control"],
          ["8", "VIN", "8", "V15 input"],
          ["9", "EP", "9", "GND thermal pad, not a current-return substitute"],
        ],
      }),
      pinMap({
        pinMapId: FIXTURE_IDS.secondPinMap,
        recordId: FIXTURE_IDS.driverRecord,
        symbol: "FX8860MP-13-HARNESS",
        footprint: "MSOP-8_L3.0-W3.0-P0.65-LS4.9-BL-EP1.8",
        pins: [
          ["1", "SET", "1", "harness context: sense input"],
          ["4", "CTRL", "4", "harness context: dimming input"],
        ],
      }),
    ],
  };
}

/** The subordinate: owns the fact the driver's calculation reaches for. */
function senseRecord(): PublicRecord {
  return {
    reference: referenceFor({ recordId: FIXTURE_IDS.senseRecord, footprintName: "R2512" }),
    identity: identity({
      recordId: FIXTURE_IDS.senseRecord,
      kind: "subordinate",
      parentRecordId: FIXTURE_IDS.driverRecord,
      mpn: "RLP25FEER200",
      manufacturer: "Fixture Passives",
      lcsc: "C459674",
      packageName: "R2512",
      function: "200 mOhm current-sense resistor",
      placements: [["board-l", "RS1"]],
    }),
    aliases: {
      mpn: [t("RLP25FEER200"), t("RLP25FEER200TS")],
      lcsc: [t("C459674")],
      manufacturer: [t("TA-I")],
      function: [],
    },
    sources: [
      source({
        sourceId: "src-fixture-sense-datasheet",
        documentTitle: "Current sense resistor RLP series",
        authorityClass: "DISTRIBUTOR_IDENTITY",
        locator: "Ordering information table",
      }),
    ],
    facts: [
      fact({
        factId: FIXTURE_IDS.foreignDependency,
        recordId: FIXTURE_IDS.senseRecord,
        sourceId: "src-fixture-sense-datasheet",
        factClass: "GUARANTEED_ELECTRICAL",
        value: 0.198,
        unit: "Ohm",
        conditions: "minimum initial resistance at 25 C, 1% tolerance",
        locator: "src-fixture-sense-datasheet: tolerance table",
        provenance: "PRIMARY-SPEC",
        verdict: "PASS - primary-source confirmed",
      }),
    ],
    coverage: [
      coverage({
        coverageId: "cov-fixture-sense-tcr",
        recordId: FIXTURE_IDS.senseRecord,
        domain: "temperature-coefficient-and-self-heating",
        status: "OPEN",
        reason: "TCR and self-heating at the installed current are not on record.",
      }),
    ],
    // Deliberately EMPTY while the driver record attaches the interaction they
    // share. That is the one-record attachment case, and it is what makes the
    // renderer's reverse index load-bearing: read naively, this page would show
    // no interactions at all despite taking part in one.
    interactions: [],
    pinMaps: [],
  };
}

/**
 * A record whose every free-text field carries MDX-active punctuation.
 *
 * If the serializer or the guard ever regresses, this record is what fails
 * first — and it fails at build time rather than by publishing a live
 * expression into a page.
 */
function hostileRecord(): PublicRecord {
  return {
    reference: referenceFor({ recordId: FIXTURE_IDS.hostileRecord, footprintName: "SOD-523" }),
    identity: identity({
      recordId: FIXTURE_IDS.hostileRecord,
      kind: "standalone",
      mpn: "PESD24VS1UB,115",
      manufacturer: `Nexperia ${HOSTILE_TEXT}`,
      lcsc: "C000999",
      packageName: "SOD-523",
      function: HOSTILE_TEXT,
      dnp: true,
      placements: [["board-p", "D1"]],
    }),
    aliases: { mpn: [], lcsc: [], manufacturer: [], function: [] },
    sources: [
      source({
        sourceId: "src-fixture-hostile",
        documentTitle: HOSTILE_TEXT,
        documentNumber: HOSTILE_TEXT,
        revision: HOSTILE_TEXT,
        availability: "SOURCE UNAVAILABLE",
        locator: HOSTILE_TEXT,
      }),
    ],
    facts: [
      fact({
        factId: "fact-fixture-hostile",
        recordId: FIXTURE_IDS.hostileRecord,
        sourceId: "src-fixture-hostile",
        factClass: "ABSOLUTE_MAXIMUM",
        value: HOSTILE_TEXT,
        unit: "V",
        conditions: HOSTILE_TEXT,
        locator: HOSTILE_TEXT,
        provenance: "UNVERIFIED",
        verdict: "UNSOURCED",
      }),
    ],
    coverage: [
      coverage({
        coverageId: "cov-fixture-hostile",
        recordId: FIXTURE_IDS.hostileRecord,
        domain: HOSTILE_TEXT,
        status: "OPEN",
        reason: HOSTILE_TEXT,
      }),
    ],
    interactions: [],
    pinMaps: [],
  };
}

/** The main fixture: driver, its subordinate, and the hostile-text record. */
export function fixtureModel(): PublicViewModel {
  return model([driverRecord(), senseRecord(), hostileRecord()], fixtureIntegration());
}

/**
 * The state of the corpus on this branch today: identity projected, every other
 * array still empty. The pages must be complete and honest in this state, not
 * merely not crash — an absent section and an empty one mean different things.
 */
export function emptyArraysModel(): PublicViewModel {
  const stripped: PublicRecord = {
    reference: referenceFor({ recordId: "rec-fixture-bare" }),
    identity: identity({
      recordId: "rec-fixture-bare",
      kind: "standalone",
      mpn: "BARE-1",
      placements: [],
    }),
    aliases: { mpn: [], lcsc: [], manufacturer: [], function: [] },
    sources: [],
    facts: [],
    coverage: [],
    interactions: [],
    pinMaps: [],
  };
  return model([stripped]);
}

/**
 * The catalog-density case: more records than the real corpus, each with the
 * full identity payload, so the index table is exercised at a size where a bad
 * layout decision actually shows.
 */
export function denseModel(recordCount = 64): PublicViewModel {
  const records: PublicRecord[] = [];
  for (let n = 0; n < recordCount; n += 1) {
    const recordId = `rec-fixture-dense-${n}`;
    records.push({
      reference: referenceFor({ recordId, footprintName: "TYPE-C-SMD_TYPE-C-6P" }),
      identity: identity({
        recordId,
        kind: n % 4 === 3 ? "subordinate" : "standalone",
        parentRecordId: n % 4 === 3 ? `rec-fixture-dense-${n - 1}` : undefined,
        mpn: `DENSE-${n}-LONG-PART-NUMBER-SUFFIX`,
        lcsc: `C${900000 + n}`,
        packageName: "USB-C-SMD_10P-P1.00-L6.8-W8.9",
        function: `dense fixture part number ${n} with a long function description`,
        dnp: n % 8 === 5,
        // One line placed 24 times, matching the worst real case.
        placements: Array.from({ length: n === 0 ? 24 : 2 }, (_unused, index) => [
          index % 2 === 0 ? "board-p" : "board-l",
          `C${index + 1}`,
        ] as const),
      }),
      aliases: { mpn: [], lcsc: [], manufacturer: [], function: [] },
      sources: [],
      facts: [],
      coverage:
        n % 3 === 0
          ? [
              coverage({
                coverageId: `cov-fixture-dense-${n}`,
                recordId,
                domain: `dense-domain-${n}`,
                status: n % 6 === 0 ? "OPEN" : "COVERED",
                reason: "Dense fixture coverage.",
              }),
            ]
          : [],
      interactions: [],
      pinMaps: [],
    });
  }
  return model(records);
}
