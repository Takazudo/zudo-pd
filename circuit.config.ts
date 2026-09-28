// Target config: evidence.candidates and inventoryProvider.mpnFromValueLcsc require the #205 patch.
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
  inventoryProvider: { kind: "led-generator-v1", mpnFromValueLcsc: ["C144397", "C591344"], specs: [{path: "scripts/schgen/board_a_spec.py"}, {path: "scripts/schgen/board_b_spec.py"}, {path: "scripts/schgen/board_p_spec.py"}] },
  publication: {
    selection: "circuit/publication/selection.json",
    assets: "circuit/publication/assets.json",
    matrix: "circuit/publication/matrix.json",
  },
  cad: { enabled: true, libraryName: "zudo-pd", symbolLibraries: ["symbols/zudo-pd.kicad_sym"], footprintMasterRoot: "footprints/kicad", footprintLibraryRoot: "footprints/kicad/zudo-power.pretty", modelRoot: "footprints/kicad/zudo-pd.3dshapes", modelLocatorPrefix: "${KIPRJMOD}/../../footprints/kicad/zudo-pd.3dshapes/", previewRenderer: { image: "kicad/kicad@sha256:e638b79b0321f29395a5b783e94bb9f3c73303e8da15da27b8f5cb4b67a37729", version: "9.0.9", platform: "linux/amd64", layers: ["F.Cu", "F.Silkscreen", "F.Fabrication", "F.Courtyard"], theme: "KiCad Default", options: ["--black-and-white"] } },
  validation: { pythonMinVersion: "3.12" },
  scan: { minimumSiteCanaries: 150, minimumSiteFiles: 50, positiveControlRecord: "stusb4500qtr" },
} satisfies CircuitConfig;
