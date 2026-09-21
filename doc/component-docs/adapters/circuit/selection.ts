/**
 * The committed instance-level publication selection for this circuit.
 *
 * Default-zero means this list, not a filter: a record or source that does not
 * appear here is never read into the view model, whatever the repository makes
 * visible. Every ID is spelled out so that adding a component to the project
 * does NOT silently add a public page — the reviewed `expect` assertions fail
 * the build until someone explicitly updates this selection and its counts.
 *
 * The `expect` counts also reject unreviewed corpus growth or shrinkage.
 * The provider selects inventory line-holder records; replacement candidates
 * stay outside publication until they are explicitly promoted and reviewed.
 *
 * `documentSelections` and `documentExceptions` are the curated document audit
 * Together they partition `recordIds` exactly — 59 records name one
 * reviewed PDF-representing source, 1 names why it has none — and
 * `core/publication.ts`'s `PublicationPolicy` constructor refuses a record
 * that appears in neither or in both. So the audit is per-record opt-in
 * without being partial: a component added tomorrow fails the build until
 * someone decides which of the two lists it belongs in.
 *
 * `linkableSourceIds` is a SEPARATE, narrower opt-in: selecting a source
 * publishes its title, revision, locator and availability; it does not by
 * itself publish an outbound link. Every entry here was checked to carry an
 * absolute `http:`/`https:` `authoritative_url` — including sources
 * recorded as SOURCE UNAVAILABLE, which still publish their (unreachable)
 * URL next to the stated unavailability.
 */

import type { InstanceSelection } from "../../core/publication.ts";

/**
 * Evidence for the document-card selections. Builds stay offline and check the
 * retained source metadata and hashes. Individually retrieved PDF IDs below
 * record additional byte/content review; they do not turn all legacy metadata
 * into a fresh online audit. Mirrors and gated documents remain explicit.
 */
export const CIRCUIT_DOCUMENT_VERIFICATION = {
  checkedOn: "2026-09-20",
  individuallyRetrievedPdfSourceIds: ["src-c8465-drawing", "src-c74561-primary", "src-c3024223-primary", "src-dw254p-drawing", "src-c492405-drawing", "src-c2832269-drawing"],
  expectedContent: "PDF",
  method: "EVIDENCE_BUNDLE_METADATA",
  /**
   * Selected sources that are MANUFACTURER_MIRROR rather than
   * MANUFACTURER_PRIMARY. Each is the best document that exists for its part,
   * and each record's card publishes `authorityClass` verbatim, so the page
   * tells the reader it is reading a mirror. Listed here because "why is this
   * one not primary?" is the first question a re-auditor will ask.
   */
  mirrorSourceIds: [
    "src-c74561-primary",
    "src-c8465-drawing",
    "src-grm32er71h106ka12l-datasheet",
    "src-c107286-mirror",
    "src-c666307-mirror",
    "src-dw254p-drawing",
    "src-stusb-ds12499",
    "src-usb-type-c-009-mirror-spec",
  ],
  /**
   * Selected sources whose `sources.json` records a per-source `Referer` — the
   * host serves them only when the request carries it, so a reader following
   * the published link directly may be refused. Exactly one source in the
   * whole corpus is in this state. It is selected anyway because the same URL
   * is already published in that record's Sources list, so withholding the
   * reviewed label would hide the manufacturer's only document without
   * sparing the reader the gate. Revisit if an ungated mirror appears.
   */
  refererGatedSourceIds: ["src-usb-type-c-009-mirror-spec", "src-type-c-primary-drawing"],
  /** Records the audit deliberately left without a document — see below. */
  unresolvedRecordIds: ["rec-c335982"],
} as const;

export const CIRCUIT_SELECTION: InstanceSelection = {
  recordIds: [
    "rec-c74561",
    "rec-c3024223",

    "rec-ap63201wu-7",
    "rec-aspi-0630lr-100m-t15",
    "rec-grm32er71h106ka12l",
    "rec-rt0603bre07158kl",
    "rec-rt0603brd0710kl",

    // User-authorized renewal linear stages and dividers.
    "rec-c107286",
    "rec-c666307",
    "rec-c110776",
    "rec-c861589",
    "rec-c861519",
    "rec-c861371",
    "rec-c861332",
    "rec-c861077",
    "rec-c23159",
    "rec-c136280",
    // Reviewed reusable PD-module records.
    "rec-type-c-31-m-17",
    "rec-c492405",
    "rec-c2832269",
    "rec-c14663",
    "rec-c22807",
    "rec-c17414",
    // component-stusb4500qtr
    "rec-stusb4500qtr",
    // component-usb-type-c-009-c456012
    "rec-usb-type-c-009-c456012",
    // component-umw-ao3401a-c347476
    "rec-umw-ao3401a-c347476",
    // component-high-diode-smaj20a-c571370
    "rec-high-diode-smaj20a-c571370",
    // component-project-passives
    "rec-c25803",
    "rec-c23206",
    "rec-c23179",
    "rec-c23162",
    "rec-c21190",
    "rec-c17513",
    "rec-c23186",
    "rec-c21189",
    "rec-c13585",
    "rec-c15849",
    "rec-c1711",
    "rec-c1623",
    "rec-c1729",
    "rec-c2983319",
    "rec-c335982",
    "rec-c970687",
    "rec-c22387780",
    "rec-c2289",
    "rec-c2288",
    "rec-c2286",
    // component-jst-b6b-xh-a
    "rec-jst-b6b-xh-a",
    // component-pesd24vs1ub-c85382
    "rec-pesd24vs1ub-c85382",
    // component-bzt52c11-c92321 (decision e: D8 gate-clamp zener)
    "rec-bzt52c11-c92321",
    // component-lm2596s-adj-c347423
    "rec-lm2596s-adj-c347423",
    // component-cya1265-100uh-c19268674
    "rec-cya1265-100uh-c19268674",
    // component-ss34-c8678
    "rec-ss34-c8678",
    // component-l7812cd2t-c13456
    // component-l7805abd2t-c86206
    // component-cj7912-c94173
    // component-ptc-smd1210p200tf-c20808 (decision g replacement: RUILON SMD1210P150TF/16, C7529589)
    "rec-ptc-smd1210p150tf16-c7529589",
    // component-ptc-msmd110-33v-c70119
    "rec-ptc-msmd110-33v-c70119",
    // component-ptc-bsmd1206-150-16v-c883133
    "rec-ptc-bsmd1206-150-16v-c883133",
    // component-smaj15a-c571368
    "rec-smaj15a-c571368",
    // component-sd05-c502527 (decision a replacement: Brightking SMAJ6.5A, C87267)
    "rec-cand-smaj6-5a-c87267",
    // component-kangnex-wj500v-5-08-2p-c8465
    "rec-c8465",
    // component-dealon-dw254p-2x8-l0-c4749189
    "rec-dealon-dw254p-2x8-l0-c4749189",
  ],

  sourceIds: [
    "src-c7529589-model-review",
    "src-c70119-model-review",
    "src-c883133-model-review",
    "src-c8465-catalog",
    "src-c8465-drawing",
    "src-c8465-project",
    "src-c8465-model",
    "src-c74561-primary",
    "src-c74561-identity",
    "src-c3024223-primary",
    "src-c3024223-identity",

    "src-ap63201wu-7-datasheet",
    "src-ap63201wu-7-catalog",
    "src-ap63201wu-7-project",
    "src-aspi-0630lr-100m-t15-datasheet",
    "src-aspi-0630lr-100m-t15-catalog",
    "src-aspi-0630lr-100m-t15-project",
    "src-aspi-0630lr-100m-t15-manufacturer-step-attempt",
    "src-aspi-0630lr-100m-t15-model-generator",
    "src-grm32er71h106ka12l-datasheet",
    "src-grm32er71h106ka12l-catalog",
    "src-grm32er71h106ka12l-project",
    "src-rt0603bre07158kl-datasheet",
    "src-rt0603bre07158kl-catalog",
    "src-rt0603bre07158kl-project",
    "src-rt0603brd0710kl-datasheet",
    "src-rt0603brd0710kl-catalog",
    "src-rt0603brd0710kl-project",

    "src-c107286-mirror",
    "src-c107286-primary-attempt",
    "src-c107286-identity",
    "src-c666307-mirror",
    "src-c666307-primary-attempt",
    "src-c666307-identity",
    "src-c110776-primary",
    "src-c110776-identity",
    "src-c861589-primary",
    "src-c861589-identity",
    "src-c861519-primary",
    "src-c861519-identity",
    "src-c861371-primary",
    "src-c861371-identity",
    "src-c861332-primary",
    "src-c861332-identity",
    "src-c861077-primary",
    "src-c861077-identity",
    "src-c23159-primary",
    "src-c23159-identity",
    "src-c136280-panasonic",
    "src-c136280-identity",
    // Reviewed reusable PD-module records.
    "src-type-c-c283540",
    "src-type-c-primary-page",
    "src-type-c-primary-drawing",
    "src-type-c-board-p-generator",
    "src-c492405-drawing",
    "src-c492405-page",
    "src-c492405-lcsc",
    "src-c2832269-drawing",
    "src-c2832269-page",
    "src-c2832269-lcsc",
    "src-c14663-yageo",
    "src-c14663-generator",
    "src-c22807-uniroyal",
    "src-c22807-generator",
    "src-c17414-uniroyal",
    "src-c17414-generator",
    // component-stusb4500qtr
    "src-stusb-ds12499", // rec-stusb4500qtr
    "src-stusb-ds12499-ratings", // rec-stusb4500qtr
    "src-stusb-um2650", // rec-stusb4500qtr
    "src-stusb-um2398", // rec-stusb4500qtr  // SOURCE UNAVAILABLE
    "src-stusb-stsw004", // rec-stusb4500qtr  // SOURCE UNAVAILABLE
    "src-stusb-ds12499-primary-attempt", // rec-stusb4500qtr  // SOURCE UNAVAILABLE
    "src-stusb-um2650-primary-attempt", // rec-stusb4500qtr  // SOURCE UNAVAILABLE
    "src-stusb-board-a-baseline", // rec-stusb4500qtr
    // component-usb-type-c-009-c456012
    "src-usb-type-c-009-mirror-spec", // rec-usb-type-c-009-c456012
    "src-usb-type-c-009-lcsc-catalog", // rec-usb-type-c-009-c456012
    "src-usb-type-c-009-primary-attempt", // rec-usb-type-c-009-c456012  // SOURCE UNAVAILABLE
    "src-usb-type-c-009-kicad-footprint", // rec-usb-type-c-009-c456012
    "src-usb-type-c-009-kicad-symbol", // rec-usb-type-c-009-c456012
    "src-usb-type-c-009-board-a-baseline", // rec-usb-type-c-009-c456012
    "src-usb-type-c-009-bom-v040", // rec-usb-type-c-009-c456012
    // component-umw-ao3401a-c347476
    "src-umw-ao3401a-c347476-datasheet", // rec-umw-ao3401a-c347476
    "src-ao3401a-board-a-baseline", // rec-umw-ao3401a-c347476
    "src-ao3401a-usb-pd-input-sch", // rec-umw-ao3401a-c347476
    // component-high-diode-smaj20a-c571370
    "src-smaj20a-c571370-distributor", // rec-high-diode-smaj20a-c571370
    "src-smaj20a-c571370-primary", // rec-high-diode-smaj20a-c571370
    "src-smaj20a-board-a-baseline", // rec-high-diode-smaj20a-c571370
    // component-project-passives
    "src-c25803-uniroyal", // rec-c25803
    "src-c25803-boardadoc", // rec-c25803
    "src-c23206-uniroyal", // rec-c23206
    "src-c23206-boardadoc", // rec-c23206
    "src-c23179-uniroyal", // rec-c23179
    "src-c23179-boardadoc", // rec-c23179
    "src-c23162-uniroyal", // rec-c23162
    "src-c23162-boardadoc", // rec-c23162
    "src-c21190-uniroyal", // rec-c21190
    "src-c21190-boardadoc", // rec-c21190
    "src-c17513-uniroyal", // rec-c17513
    "src-c17513-boardadoc", // rec-c17513
    "src-c23186-uniroyal", // rec-c23186
    "src-c23186-boardadoc", // rec-c23186
    "src-c21189-uniroyal", // rec-c21189
    "src-c21189-boardadoc", // rec-c21189
    "src-c13585-page", // rec-c13585
    "src-c13585-catalog", // rec-c13585
    "src-c13585-boardadoc", // rec-c13585
    "src-c15849-page", // rec-c15849
    "src-c15849-catalog", // rec-c15849
    "src-c15849-boardadoc", // rec-c15849
    "src-c1711-yageo", // rec-c1711
    "src-c1711-boardadoc", // rec-c1711
    "src-c1623-page", // rec-c1623
    "src-c1623-catalog", // rec-c1623
    "src-c1623-boardbdoc", // rec-c1623
    "src-c1729-page", // rec-c1729
    "src-c1729-catalog", // rec-c1729
    "src-c1729-boardbdoc", // rec-c1729
    "src-c2983319-datasheet", // rec-c2983319
    "src-c2983319-boardbdoc", // rec-c2983319
    "src-c335982-identity", // rec-c335982
    "src-c970687-datasheet", // rec-c970687
    "src-c970687-boardbdoc", // rec-c970687
    "src-c22387780-datasheet", // rec-c22387780
    "src-c22387780-boardbdoc", // rec-c22387780
    "src-c2289-datasheet", // rec-c2289
    "src-c2289-boardbdoc", // rec-c2289
    "src-c2288-datasheet", // rec-c2288
    "src-c2288-boardbdoc", // rec-c2288
    "src-c2286-datasheet", // rec-c2286
    "src-c2286-boardbdoc", // rec-c2286
    // component-jst-b6b-xh-a
    "src-jst-xh-catalog", // rec-jst-b6b-xh-a
    "src-jst-xh-header", // rec-jst-b6b-xh-a
    "src-jst-board-split-decision", // rec-jst-b6b-xh-a
    // component-pesd24vs1ub-c85382
    "src-pesd24vs1ub-nexperia-primary", // rec-pesd24vs1ub-c85382
    "src-pesd24vs1ub-lcsc-identity", // rec-pesd24vs1ub-c85382
    // component-bzt52c11-c92321 (decision e: D8 gate-clamp zener)
    "src-bzt52c11-diodes-primary", // rec-bzt52c11-c92321
    "src-bzt52c11-lcsc-identity", // rec-bzt52c11-c92321
    // component-lm2596s-adj-c347423
    "src-lm2596-umw-ds", // rec-lm2596s-adj-c347423
    "src-lm2596-schematic-dcdc", // rec-lm2596s-adj-c347423
    "src-lm2596-board-b-baseline", // rec-lm2596s-adj-c347423
    // component-cya1265-100uh-c19268674
    "src-cya1265-datasheet", // rec-cya1265-100uh-c19268674
    // component-ss34-c8678
    "src-ss34-datasheet", // rec-ss34-c8678
    // component-l7812cd2t-c13456
    // component-l7805abd2t-c86206
    // component-cj7912-c94173
    // component-ptc-smd1210p200tf-c20808 (decision g replacement)
    "src-ptc1b-smd1210-datasheet", // rec-ptc-smd1210p150tf16-c7529589
    // component-ptc-msmd110-33v-c70119
    "src-ptc2-msmd110-datasheet", // rec-ptc-msmd110-33v-c70119
    // component-ptc-bsmd1206-150-16v-c883133
    "src-ptc3-bsmd1206-datasheet", // rec-ptc-bsmd1206-150-16v-c883133
    // component-smaj15a-c571368
    "src-smaj15a-hdiode-primary", // rec-smaj15a-c571368
    "src-smaj15a-lcsc-identity", // rec-smaj15a-c571368
    // component-sd05-c502527 (decision a replacement)
    "src-cand-smaj6-5a-brightking-primary", // rec-cand-smaj6-5a-c87267
    "src-cand-smaj6-5a-lcsc-identity", // rec-cand-smaj6-5a-c87267
    // component-kangnex-wj500v-5-08-2p-c8465
    // component-dealon-dw254p-2x8-l0-c4749189
    "src-dw254p-drawing", // rec-dealon-dw254p-2x8-l0-c4749189
    "src-dw254p-catalog", // rec-dealon-dw254p-2x8-l0-c4749189
    "src-dw254p-project", // rec-dealon-dw254p-2x8-l0-c4749189
    "src-dw254p-step-normalization",
    "src-dw254p-doepfer", // rec-dealon-dw254p-2x8-l0-c4749189
  ],

  // Only reviewed absolute http(s) URLs are outbound links. Local generator
  // and model-transform evidence remains published without a synthetic URL.
  linkableSourceIds: [
    "src-c8465-catalog",
    "src-c8465-drawing",
    "src-c74561-primary",
    "src-c74561-identity",
    "src-c3024223-primary",
    "src-c3024223-identity",

    "src-ap63201wu-7-datasheet",
    "src-ap63201wu-7-catalog",
    "src-aspi-0630lr-100m-t15-datasheet",
    "src-aspi-0630lr-100m-t15-catalog",
    "src-aspi-0630lr-100m-t15-manufacturer-step-attempt",
    "src-grm32er71h106ka12l-datasheet",
    "src-grm32er71h106ka12l-catalog",
    "src-rt0603bre07158kl-datasheet",
    "src-rt0603bre07158kl-catalog",
    "src-rt0603brd0710kl-datasheet",
    "src-rt0603brd0710kl-catalog",

    "src-c107286-mirror",
    "src-c107286-primary-attempt",
    "src-c107286-identity",
    "src-c666307-mirror",
    "src-c666307-primary-attempt",
    "src-c666307-identity",
    "src-c110776-primary",
    "src-c110776-identity",
    "src-c861589-primary",
    "src-c861589-identity",
    "src-c861519-primary",
    "src-c861519-identity",
    "src-c861371-primary",
    "src-c861371-identity",
    "src-c861332-primary",
    "src-c861332-identity",
    "src-c861077-primary",
    "src-c861077-identity",
    "src-c23159-primary",
    "src-c23159-identity",
    "src-c136280-panasonic",
    "src-c136280-identity",
    // Reviewed reusable PD-module records.
    "src-type-c-c283540",
    "src-type-c-primary-page",
    "src-type-c-primary-drawing",
    "src-c492405-drawing",
    "src-c492405-page",
    "src-c492405-lcsc",
    "src-c2832269-drawing",
    "src-c2832269-page",
    "src-c2832269-lcsc",
    "src-c14663-yageo",
    "src-c22807-uniroyal",
    "src-c17414-uniroyal",
    // component-stusb4500qtr
    "src-stusb-ds12499",
    "src-stusb-ds12499-ratings",
    "src-stusb-um2650",
    "src-stusb-um2398",
    "src-stusb-stsw004",
    "src-stusb-ds12499-primary-attempt",
    "src-stusb-um2650-primary-attempt",
    "src-stusb-board-a-baseline",
    // component-usb-type-c-009-c456012
    "src-usb-type-c-009-mirror-spec",
    "src-usb-type-c-009-lcsc-catalog",
    "src-usb-type-c-009-primary-attempt",
    "src-usb-type-c-009-kicad-footprint",
    "src-usb-type-c-009-kicad-symbol",
    "src-usb-type-c-009-board-a-baseline",
    "src-usb-type-c-009-bom-v040",
    // component-umw-ao3401a-c347476
    "src-umw-ao3401a-c347476-datasheet",
    "src-ao3401a-board-a-baseline",
    "src-ao3401a-usb-pd-input-sch",
    // component-high-diode-smaj20a-c571370
    "src-smaj20a-c571370-distributor",
    "src-smaj20a-c571370-primary",
    "src-smaj20a-board-a-baseline",
    // component-project-passives
    "src-c25803-uniroyal",
    "src-c25803-boardadoc",
    "src-c23206-uniroyal",
    "src-c23206-boardadoc",
    "src-c23179-uniroyal",
    "src-c23179-boardadoc",
    "src-c23162-uniroyal",
    "src-c23162-boardadoc",
    "src-c21190-uniroyal",
    "src-c21190-boardadoc",
    "src-c17513-uniroyal",
    "src-c17513-boardadoc",
    "src-c23186-uniroyal",
    "src-c23186-boardadoc",
    "src-c21189-uniroyal",
    "src-c21189-boardadoc",
    "src-c13585-page",
    "src-c13585-catalog",
    "src-c13585-boardadoc",
    "src-c15849-page",
    "src-c15849-catalog",
    "src-c15849-boardadoc",
    "src-c1711-yageo",
    "src-c1711-boardadoc",
    "src-c1623-page",
    "src-c1623-catalog",
    "src-c1623-boardbdoc",
    "src-c1729-page",
    "src-c1729-catalog",
    "src-c1729-boardbdoc",
    "src-c2983319-datasheet",
    "src-c2983319-boardbdoc",
    "src-c335982-identity",
    "src-c970687-datasheet",
    "src-c970687-boardbdoc",
    "src-c22387780-datasheet",
    "src-c22387780-boardbdoc",
    "src-c2289-datasheet",
    "src-c2289-boardbdoc",
    "src-c2288-datasheet",
    "src-c2288-boardbdoc",
    "src-c2286-datasheet",
    "src-c2286-boardbdoc",
    // component-jst-b6b-xh-a
    "src-jst-xh-catalog",
    "src-jst-xh-header",
    "src-jst-board-split-decision",
    // component-pesd24vs1ub-c85382
    "src-pesd24vs1ub-nexperia-primary",
    "src-pesd24vs1ub-lcsc-identity",
    // component-bzt52c11-c92321 (decision e: D8 gate-clamp zener)
    "src-bzt52c11-diodes-primary",
    "src-bzt52c11-lcsc-identity",
    // component-lm2596s-adj-c347423
    "src-lm2596-umw-ds",
    "src-lm2596-schematic-dcdc",
    "src-lm2596-board-b-baseline",
    // component-cya1265-100uh-c19268674
    "src-cya1265-datasheet",
    // component-ss34-c8678
    "src-ss34-datasheet",
    // component-l7812cd2t-c13456
    // component-l7805abd2t-c86206
    // component-cj7912-c94173
    // component-ptc-smd1210p200tf-c20808 (decision g replacement)
    "src-ptc1b-smd1210-datasheet",
    // component-ptc-msmd110-33v-c70119
    "src-ptc2-msmd110-datasheet",
    // component-ptc-bsmd1206-150-16v-c883133
    "src-ptc3-bsmd1206-datasheet",
    // component-smaj15a-c571368
    "src-smaj15a-hdiode-primary",
    "src-smaj15a-lcsc-identity",
    // component-sd05-c502527 (decision a replacement)
    "src-cand-smaj6-5a-brightking-primary",
    "src-cand-smaj6-5a-lcsc-identity",
    // component-kangnex-wj500v-5-08-2p-c8465
    // component-dealon-dw254p-2x8-l0-c4749189
    "src-dw254p-drawing",
    "src-dw254p-catalog",
    "src-dw254p-project",
    "src-dw254p-doepfer",
  ],

  /**
   * The reviewed document per record, in `recordIds` order.
   *
   * `documentKind` is hand-curated here and lives in no skill file, because it
   * is a claim about what the document IS, and the evidence bundles record
   * what it SAYS. It follows the document's own self-description, never the
   * source ID's suffix: `src-cya1265-datasheet` is a "Specification For
   * Approval" and `src-ptc2-msmd110-datasheet` is a "Specification Sheet", so
   * both are `specification` despite the `-datasheet` in their IDs.
   */
  documentSelections: [
    { recordId: "rec-c74561", sourceId: "src-c74561-primary", documentKind: "datasheet" },
    { recordId: "rec-c3024223", sourceId: "src-c3024223-primary", documentKind: "datasheet" },
    { recordId: "rec-ap63201wu-7", sourceId: "src-ap63201wu-7-datasheet", documentKind: "datasheet" },
    { recordId: "rec-aspi-0630lr-100m-t15", sourceId: "src-aspi-0630lr-100m-t15-datasheet", documentKind: "datasheet" },
    { recordId: "rec-grm32er71h106ka12l", sourceId: "src-grm32er71h106ka12l-datasheet", documentKind: "datasheet" },
    { recordId: "rec-rt0603bre07158kl", sourceId: "src-rt0603bre07158kl-datasheet", documentKind: "specification" },
    { recordId: "rec-rt0603brd0710kl", sourceId: "src-rt0603brd0710kl-datasheet", documentKind: "specification" },

    { recordId: "rec-c107286", sourceId: "src-c107286-mirror", documentKind: "datasheet" },
    { recordId: "rec-c666307", sourceId: "src-c666307-mirror", documentKind: "datasheet" },
    { recordId: "rec-c110776", sourceId: "src-c110776-primary", documentKind: "specification" },
    { recordId: "rec-c861589", sourceId: "src-c861589-primary", documentKind: "specification" },
    { recordId: "rec-c861519", sourceId: "src-c861519-primary", documentKind: "specification" },
    { recordId: "rec-c861371", sourceId: "src-c861371-primary", documentKind: "specification" },
    { recordId: "rec-c861332", sourceId: "src-c861332-primary", documentKind: "specification" },
    { recordId: "rec-c861077", sourceId: "src-c861077-primary", documentKind: "specification" },
    { recordId: "rec-c23159", sourceId: "src-c23159-primary", documentKind: "specification" },
    { recordId: "rec-c136280", sourceId: "src-c136280-panasonic", documentKind: "datasheet" },
    { recordId: "rec-type-c-31-m-17", sourceId: "src-type-c-primary-drawing", documentKind: "drawing" },
    { recordId: "rec-c492405", sourceId: "src-c492405-drawing", documentKind: "drawing" },
    { recordId: "rec-c2832269", sourceId: "src-c2832269-drawing", documentKind: "drawing" },
    { recordId: "rec-c14663", sourceId: "src-c14663-yageo", documentKind: "specification" },
    { recordId: "rec-c22807", sourceId: "src-c22807-uniroyal", documentKind: "datasheet" },
    { recordId: "rec-c17414", sourceId: "src-c17414-uniroyal", documentKind: "datasheet" },
    // component-stusb4500qtr
    // DS12499 Rev 8 via a web.archive.org `id_` raw-byte replay of ST's own
    // PDF path. Two dated direct-from-st.com attempts failed (2026-08-02,
    // 2026-08-14) with control fetches proving egress was up, so the document
    // is blocked, not withdrawn. The selected source retains its mirror status.
    { recordId: "rec-stusb4500qtr", sourceId: "src-stusb-ds12499", documentKind: "datasheet" },
    // component-usb-type-c-009-c456012
    // Manufacturer-authored "FOR APPROVAL" sheet hosted by the distributor.
    // sohantech.com publishes no TYPE-C 6P page and no PDF at all, so this is
    // not a convenience copy of a primary — it is the only manufacturer
    // document that exists. See `refererGatedSourceIds` above.
    { recordId: "rec-usb-type-c-009-c456012", sourceId: "src-usb-type-c-009-mirror-spec", documentKind: "specification" },
    // component-umw-ao3401a-c347476
    { recordId: "rec-umw-ao3401a-c347476", sourceId: "src-umw-ao3401a-c347476-datasheet", documentKind: "datasheet" },
    // component-high-diode-smaj20a-c571370
    { recordId: "rec-high-diode-smaj20a-c571370", sourceId: "src-smaj20a-c571370-primary", documentKind: "datasheet" },
    // component-project-passives
    // The nine UNI-ROYAL lines share one "Thick Film Chip Resistors" spec
    // document; each record cites it under its own source ID, so each selects
    // its own. Same document, same kind, nine reviewed entries — matching
    // led-lamp, which classifies this exact document as a specification.
    { recordId: "rec-c25803", sourceId: "src-c25803-uniroyal", documentKind: "specification" },
    { recordId: "rec-c23206", sourceId: "src-c23206-uniroyal", documentKind: "specification" },
    { recordId: "rec-c23179", sourceId: "src-c23179-uniroyal", documentKind: "specification" },
    { recordId: "rec-c23162", sourceId: "src-c23162-uniroyal", documentKind: "specification" },
    { recordId: "rec-c21190", sourceId: "src-c21190-uniroyal", documentKind: "specification" },
    { recordId: "rec-c17513", sourceId: "src-c17513-uniroyal", documentKind: "specification" },
    { recordId: "rec-c23186", sourceId: "src-c23186-uniroyal", documentKind: "specification" },
    { recordId: "rec-c21189", sourceId: "src-c21189-uniroyal", documentKind: "specification" },
    // The four Samsung MLCCs each cite a per-part reference sheet (`-page`)
    // and the family MLCC catalog (`-catalog`). The per-part sheet is the
    // record's own document; the catalog describes the series.
    { recordId: "rec-c13585", sourceId: "src-c13585-page", documentKind: "specification" },
    { recordId: "rec-c15849", sourceId: "src-c15849-page", documentKind: "specification" },
    { recordId: "rec-c1711", sourceId: "src-c1711-yageo", documentKind: "specification" },
    { recordId: "rec-c1623", sourceId: "src-c1623-page", documentKind: "specification" },
    { recordId: "rec-c1729", sourceId: "src-c1729-page", documentKind: "specification" },
    { recordId: "rec-c2983319", sourceId: "src-c2983319-datasheet", documentKind: "datasheet" },
    // rec-c335982 is excepted — see `documentExceptions`.
    { recordId: "rec-c970687", sourceId: "src-c970687-datasheet", documentKind: "datasheet" },
    { recordId: "rec-c22387780", sourceId: "src-c22387780-datasheet", documentKind: "datasheet" },
    { recordId: "rec-c2289", sourceId: "src-c2289-datasheet", documentKind: "datasheet" },
    { recordId: "rec-c2288", sourceId: "src-c2288-datasheet", documentKind: "datasheet" },
    { recordId: "rec-c2286", sourceId: "src-c2286-datasheet", documentKind: "datasheet" },
    // component-jst-b6b-xh-a
    // Both cited sources are the same eXH.pdf at different locators; the
    // general-specifications one is the document, the header-dimensions one a
    // fragment of it. led-lamp classifies this same PDF as a specification.
    { recordId: "rec-jst-b6b-xh-a", sourceId: "src-jst-xh-catalog", documentKind: "specification" },
    // component-pesd24vs1ub-c85382
    { recordId: "rec-pesd24vs1ub-c85382", sourceId: "src-pesd24vs1ub-nexperia-primary", documentKind: "datasheet" },
    // component-bzt52c11-c92321 (decision e: D8 gate-clamp zener)
    { recordId: "rec-bzt52c11-c92321", sourceId: "src-bzt52c11-diodes-primary", documentKind: "datasheet" },
    // component-lm2596s-adj-c347423
    { recordId: "rec-lm2596s-adj-c347423", sourceId: "src-lm2596-umw-ds", documentKind: "datasheet" },
    // component-cya1265-100uh-c19268674 — "Specification For Approval"
    { recordId: "rec-cya1265-100uh-c19268674", sourceId: "src-cya1265-datasheet", documentKind: "specification" },
    // component-ss34-c8678
    { recordId: "rec-ss34-c8678", sourceId: "src-ss34-datasheet", documentKind: "datasheet" },
    // component-l7812cd2t-c13456 / component-l7805abd2t-c86206
    // Six fragments each, all of ST's DS0422. The ordering-information
    // fragment is the one that binds the exact order code to the record, so
    // it stands for the datasheet.
    // component-cj7912-c94173 — same six-fragment shape, one JSCJ PDF
    // The three PTCs land on two kinds because their documents describe
    // themselves differently: SMD1210 and BSMD1206 are series datasheets,
    // mSMD110-33V is a "Specification Sheet".
    { recordId: "rec-ptc-smd1210p150tf16-c7529589", sourceId: "src-ptc1b-smd1210-datasheet", documentKind: "datasheet" },
    { recordId: "rec-ptc-msmd110-33v-c70119", sourceId: "src-ptc2-msmd110-datasheet", documentKind: "specification" },
    { recordId: "rec-ptc-bsmd1206-150-16v-c883133", sourceId: "src-ptc3-bsmd1206-datasheet", documentKind: "datasheet" },
    // component-smaj15a-c571368
    { recordId: "rec-smaj15a-c571368", sourceId: "src-smaj15a-hdiode-primary", documentKind: "datasheet" },
    // component-sd05-c502527 (decision a replacement)
    { recordId: "rec-cand-smaj6-5a-c87267", sourceId: "src-cand-smaj6-5a-brightking-primary", documentKind: "datasheet" },
    // component-kangnex-wj500v-5-08-2p-c8465
    // Manufacturer-authored C8465 drawing, retrieved from the exact JLC listing.
    { recordId: "rec-c8465", sourceId: "src-c8465-drawing", documentKind: "drawing" },
    // component-dealon-dw254p-2x8-l0-c4749189
    // A single-sheet engineering drawing — dimensions, PCB layout and a notes
    // block, published as a `drawing`. It covers
    // the DEALON DW254P family with an explicit 16P dimension row; identity is
    // bound by the distributor source, which stays in Sources.
    { recordId: "rec-dealon-dw254p-2x8-l0-c4749189", sourceId: "src-dw254p-drawing", documentKind: "drawing" },
  ],

  /**
   * The one record the audit could not honestly give a document.
   *
   * `rec-c335982` (ROQANG RVT1A471M0607, the 470 µF bulk electrolytic) cites
   * exactly one source in the whole corpus: an LCSC product-detail page,
   * `DISTRIBUTOR_IDENTITY`, retained as raw HTML for its JSON-LD identity
   * block. There is no manufacturer document behind it — not gated, not
   * mirrored, not stale: absent. A distributor listing is not a datasheet, and
   * none of the three `DOCUMENT_LABELS` would be true of it.
   *
   * The two shortcuts that would make this card resolve are both refused on
   * purpose. Widening the label allowlist would let a catalog row be presented
   * as the component's authoritative document on every future record too.
   * Deriving a PDF URL from `C335982` is forbidden outright — `core/url.ts`
   * publishes only URLs the evidence recorded, never ones the projection
   * guessed. So the card states the gap, and the LCSC page stays visible under
   * Sources where its authority class is printed next to it.
   */
  documentExceptions: [
    {
      recordId: "rec-c335982",
      reason:
        "No manufacturer document exists for this part in the project's evidence. " +
        "Its only source is an LCSC distributor product listing, which records the " +
        "part's identity but is not a datasheet or specification. It is published in " +
        "full under Sources.",
    },
  ],

  // PD additions use retained manufacturer extracts; current retrieval audit is in
  // boards/board-p/README.md. Local generator sources are deliberately not outbound links.
  expect: {
    records: 60,
    sources: 154,
    integrationRules: 11,
    // Read by references.ts, so a changed package set requires the same
    // explicit review as a changed record or source selection.
    footprintPackages: 34,
  },
};
