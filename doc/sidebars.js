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
  overviewSidebar: [
    'overview/index',
    'overview/overview',
    'overview/circuit-diagrams',
    'overview/bom',
    'overview/mechanical-design',
    'overview/usb-pd-adapter',
  ],
  inboxSidebar: [
    'inbox/index',
    'inbox/current-status',
    'inbox/quick-reference',
    'inbox/pcba-v1-debug',
    'inbox/nvm-programming',
  ],
  componentsSidebar: [
    'components/index',
    'components/usb-c-connector',
    'components/stusb4500',
    'components/ao3401a',
    'components/usblc6-2sc6',
    'components/esda25l',
    'components/ch224d',
    'components/lm2596s-adj',
    'components/l7812cv',
    'components/l7805abd2t',
    'components/cj7912',
    'components/ptc-12v',
    'components/ptc-5v',
    'components/ptc-12v-neg',
    'components/smaj15a',
    'components/sd05',
    'components/faston-terminal',
  ],
  learningSidebar: [
    'learning/index',
    'learning/gnd-component-placement',
    'learning/gndd-gnda-split-ground',
    'learning/ch224d-usb-pd-controller',
    'learning/usb-type-c-pinout',
    'learning/usb-pd-vs-traditional-usb',
    'learning/open-drain-pg-pin',
    'learning/p-channel-mosfet-load-switch',
    'learning/esd-protection-tvs-diodes',
    'learning/buck-converter-feedback',
    'learning/inductor-voltage-reversal',
    'learning/pcb-layout-power-circuits',
    'learning/trace-width-copper-weight',
    'learning/transformer-polarity-flyback',
    'learning/linear-regulator-capacitors',
    'learning/two-stage-dc-dc-ldo-architecture',
    'learning/protection-fuse-strategy',
    'learning/eurorack-power-distribution',
  ],
  howToSidebar: [
    'how-to/index',
    'how-to/kicad-workflow',
    'how-to/kicad-parts-download',
    'how-to/create-footprint-svg',
    'how-to/create-circuit-svg',
  ],
  miscSidebar: ['misc/index', 'misc/footprint-preview'],
};

export default sidebars;
