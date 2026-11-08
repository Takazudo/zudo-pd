import type { CircuitConfig } from "@takazudo/zudo-circuit-doc/config";

export default {
  configVersion: 1,
  project: {
    name: "zudo-pd",
    title: "zudo-pd",
  },
  docs: {
    root: "doc",
    generatedContent: "doc/src/content/docs/components",
    preflight: "circuit/generated/preflight.json",
    publicRoot: "doc/public",
    dist: "doc/dist",
    agentResources: false,
    generatedNotice: true,
    integrationGloss: "circuit/publication/integration-gloss.json",
  },
  evidence: {
    contractVersion: 1,
    bundlesRoot: ".claude/skills",
    ownerPrefix: "component-",
    auditSkill: "component-spec-audit",
    integrationSkill: "circuit-spec-integration",
    candidates: ".claude/skills/component-spec-audit/references/candidates.json",
    inventory: ".claude/skills/component-spec-audit/references/inventory.json",
    integrationRules: ".claude/skills/circuit-spec-integration/references/rules.json",
    directRouting: ".claude/skills/component-spec-audit/fixtures/direct-routing.json",
    vendorQualifiers: ".claude/skills/component-spec-audit/references/external-vendor-qualifiers.json",
    sourceCache: ".circuit-cache/sources",
  },
  inventoryProvider: {
    kind: "led-generator-v1",
    // DNP is recorded per placement in inventory.json; a line may mix fitted and DNP placements.
    fit: "placement",
    // C591344 was removed: no current generator input uses it, and runtime 0.3.0 rejects inert exceptions.
    mpnFromValueLcsc: ["C144397"],
    specs: [
      { path: "scripts/schgen/board_a_spec.py", board: "board-a" },
      { path: "scripts/schgen/board_b_spec.py", board: "board-b" },
      { path: "scripts/schgen/board_p_spec.py", board: "board-p" },
      { path: "scripts/schgen/board_p15_spec.py", board: "board-p15" },
      { path: "scripts/schgen/board_b20_components.py", board: "board-b20-draft" },
    ],
  },
  publication: {
    selection: "circuit/publication/selection.json",
    assets: "circuit/publication/assets.json",
    matrix: "circuit/publication/matrix.json",
  },
  cad: { enabled: true, libraryName: "zudo-pd", symbolLibraries: ["symbols/zudo-pd.kicad_sym"], footprintMasterRoot: "footprints/kicad", footprintLibraryRoot: "footprints/kicad/zudo-power.pretty", modelRoot: "footprints/kicad/zudo-pd.3dshapes", modelLocatorPrefix: "${KIPRJMOD}/../../footprints/kicad/zudo-pd.3dshapes/", previewRenderer: { image: "kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec", version: "10.0.6", platform: "linux/amd64", layers: ["F.Cu", "F.Silkscreen", "F.Fabrication", "F.Courtyard"], theme: "KiCad Default", options: ["--black-and-white"] } },
  validation: { pythonMinVersion: "3.12" },
  browserSmoke: { representatives: [
    { kind: "passive", path: "/docs/components/records/c1623/", slug: "c1623", identity: "CL10B474KA8NNNC" },
    { kind: "controller", path: "/docs/components/records/stusb4500qtr/", slug: "stusb4500qtr", identity: "STUSB4500QTR" },
    { kind: "synth connector", path: "/docs/components/records/dealon-dw254p-2x8-l0-c4749189/", slug: "dealon-dw254p-2x8-l0-c4749189", identity: "DW254P-2X8-L0" },
  ] },
  scan: {
    minimumSiteCanaries: 150,
    minimumSiteFiles: 50,
    positiveControlRecord: "stusb4500qtr",
    // Reviewed 2026-11-08 on runtime 0.3.0: authored narrative pages already publish 32
    // denied-only values (owner skill names, routing terms, three JLCPCB part URLs).
    expectedWithheld: 32,
    // The only published footprint whose canonical bytes are also a denied evidence hash
    // (src-dw254p-project); every other evidence sha256 stays a SITE canary.
    publicCanonicalFootprints: ["IDC-TH_16P-P2.54_321016RG0ABK00A01"],
  },
} satisfies CircuitConfig;
