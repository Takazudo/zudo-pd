// ADR-016 seam: registers the package's MDX components (EvidenceAnchor,
// EvidenceDetails, EvidenceFact, EvidenceTable, ComponentReferences,
// PackageModelViewer) with zudo-doc's chrome, so generated component pages
// can use them with no import. Referenced by `zfb.config.ts`'s
// `chromeBindingsModule`.
import { defineChromeBindings } from "@takazudo/zudo-doc/chrome-bindings";
import { circuitDocMdxExtras } from "@takazudo/zudo-circuit-doc/mdx-extras";

export const chromeBindings = defineChromeBindings({
  mdxExtras: { ...circuitDocMdxExtras },
});
