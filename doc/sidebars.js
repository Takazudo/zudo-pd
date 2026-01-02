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
  componentsSidebar: [
    'components/index',
    'components/bom',
    'components/usb-c-connector',
    'components/ch224d',
    'components/lm2596s-adj',
    'components/lm2586sx-adj',
    'components/l7812cv',
    'components/l7805abd2t',
    'components/cj7912',
    'components/ptc-12v',
    'components/ptc-5v',
    'components/ptc-12v-neg',
    'components/smaj15a',
    'components/prtr5v0u2x',
  ],
  learningSidebar: [
    'learning/index',
    'learning/ch224d-usb-pd-controller',
    'learning/usb-type-c-pinout',
    'learning/open-drain-pg-pin',
    'learning/buck-converter-feedback',
    'learning/transformer-polarity-flyback',
    'learning/linear-regulator-capacitors',
    'learning/two-stage-dc-dc-ldo-architecture',
    'learning/protection-fuse-strategy',
    'learning/eurorack-power-distribution',
  ],
  knowledgeSidebar: [
    'knowledge/index',
    'knowledge/kicad-footprint-generation',
    'knowledge/create-footprint-svg',
    'knowledge/create-circuit-svg',
  ],
};

export default sidebars;
