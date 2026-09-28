/** @jsxRuntime automatic */
/** @jsxImportSource preact */

import { defineChromeBindings } from "@takazudo/zudo-doc/chrome-bindings";
import { circuitDocMdxExtras } from "@takazudo/zudo-circuit-doc/mdx-extras";

export const chromeBindings = defineChromeBindings({
  // Trailing item of the home hero link row, `/`-separated from the Overview
  // and GitHub links the package renders. Project-specific brand link
  // established in #1453; the package hero has no setting for it, so it comes
  // back through this slot.
  homeExtras: () => (
    <a
      href="https://x.com/Takazudo"
      class="text-fg underline hover:text-accent"
      target="_blank"
      rel="noopener noreferrer"
    >
      @Takazudo
    </a>
  ),
  mdxExtras: { ...circuitDocMdxExtras },
});
