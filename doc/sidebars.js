// @ts-check

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.

 @type {import('@docusaurus/plugin-content-docs').SidebarsConfig}
 */
const sidebars = {
  inboxSidebar: [
    'inbox/index',
    'inbox/current-status',
    'inbox/overview',
    'inbox/circuit-diagrams',
    'inbox/footprint-preview',
    'inbox/quick-reference',
  ],
  partsSidebar: [
    'parts/index',
    'parts/bom',
    'parts/ch224d',
    'parts/lm2596s-adj',
    'parts/icl7660m',
    'parts/l7812cv',
    'parts/l7805abd2t',
    'parts/cj7912',
    'parts/smaj15a',
    'parts/prtr5v0u2x',
  ],
  learningSidebar: [
    'learning/index',
    'learning/open-drain-pg-pin',
    'learning/buck-converter-feedback',
  ],
  knowledgeSidebar: [
    'knowledge/index',
    'knowledge/kicad-footprint-generation',
    'knowledge/create-footprint-svg',
    'knowledge/create-circuit-svg',
  ],
};

export default sidebars;
