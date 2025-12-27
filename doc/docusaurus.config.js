// @ts-check
import { themes as prismThemes } from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'USB-PD Modular Synth Power',
  tagline: 'USB-PD powered modular synthesizer power supply documentation',
  favicon: 'img/favicon.ico',

  // Future flags
  future: {
    v4: true,
  },

  // Set the production url of your site here
  url: 'https://zudo-power-usb-pd.example.com',
  baseUrl: '/',

  // Don't add trailing slash
  trailingSlash: false,

  onBrokenLinks: 'throw',

  // English locale
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  // Enable Mermaid diagrams
  markdown: {
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          routeBasePath: '/docs',
          editUrl: undefined,
          // Show last update time and author from git history
          showLastUpdateTime: true,
          showLastUpdateAuthor: true,
          // Add remark plugin to inject creation dates
          beforeDefaultRemarkPlugins: [[require('./plugins/remark-creation-date.js'), {}]],
        },
        // Disable blog feature
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Force dark mode and disable theme switching
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: true,
        respectPrefersColorScheme: false,
      },
      navbar: {
        title: 'USB-PD Synth Power',
        logo: {
          alt: 'USB-PD Synth Power Logo',
          src: 'img/logo.svg',
          width: 32,
          height: 32,
        },
        items: [
          {
            type: 'doc',
            docId: 'inbox/index',
            position: 'left',
            label: 'INBOX',
          },
        ],
      },
      footer: {
        style: 'dark',
        copyright: `Copyright © ${new Date().getFullYear()} USB-PD Synth Power. Documentation built with Docusaurus.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.oneDark,
      },
    }),
};

export default config;
