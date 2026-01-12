// @ts-check
import { themes as prismThemes } from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'zudo-PD',
  tagline: 'USB-PD powered modular synthesizer power supply documentation',
  favicon: 'img/favicon.ico',

  // Future flags
  future: {
    v4: true,
  },

  // Set the production url of your site here
  url: 'https://takazudomodular.com',
  baseUrl: '/pj/zudo-pd/',

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
        title: 'zudo-PD',
        items: [
          {
            type: 'doc',
            docId: 'overview/index',
            position: 'left',
            label: 'Overview',
          },
          {
            type: 'doc',
            docId: 'components/index',
            position: 'left',
            label: 'Components',
          },
          {
            type: 'doc',
            docId: 'learning/index',
            position: 'left',
            label: 'Learning',
          },
          {
            type: 'doc',
            docId: 'how-to/index',
            position: 'left',
            label: 'HowTo',
          },
          {
            type: 'doc',
            docId: 'misc/index',
            position: 'left',
            label: 'Misc',
          },
          {
            type: 'doc',
            docId: 'inbox/index',
            position: 'left',
            label: 'INBOX',
          },
          {
            type: 'html',
            position: 'right',
            value:
              '<a href="https://takazudomodular.com/" class="navbar__takazudo-modular"><img src="/pj/zudo-pd/img/logo.svg" alt="Takazudo Modular" /><span>Takazudo Modular</span></a>',
          },
        ],
      },
      footer: {
        style: 'dark',
        copyright: `Copyright © ${new Date().getFullYear()} Takazudo. Documentation built with Docusaurus.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.oneDark,
      },
    }),
};

export default config;
