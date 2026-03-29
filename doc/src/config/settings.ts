export type {
  HeaderNavItem,
  ColorModeConfig,
  FooterConfig,
} from "./settings-types";
import type {
  HeaderNavItem,
  ColorModeConfig,
  FooterConfig,
} from "./settings-types";

export const settings = {
  colorScheme: "Default Dark",
  colorMode: {
    defaultMode: "dark",
    lightScheme: "Default Light",
    darkScheme: "Default Dark",
    respectPrefersColorScheme: true,
  } as ColorModeConfig | false,
  siteName: "zudo-pd",
  siteDescription: "USB-PD powered modular synthesizer power supply documentation" as string,
  base: "/pj/zudo-pd/",
  trailingSlash: false as boolean,
  docsDir: "src/content/docs",
  locales: {} as Record<string, never>,
  mermaid: true,
  sitemap: false,
  docMetainfo: false,
  docTags: false,
  llmsTxt: false,
  math: false,
  onBrokenMarkdownLinks: "warn" as "warn" | "error" | "ignore",
  aiAssistant: false,
  docHistory: false,
  colorTweakPanel: false,
  sidebarResizer: true,
  sidebarToggle: false,
  noindex: false as boolean,
  editUrl: false as string | false,
  siteUrl: "https://takazudomodular.com",
  versions: false as false,
  claudeResources: {
    claudeDir: ".claude",
  } as { claudeDir: string; projectRoot?: string } | false,
  footer: {
    links: [
      {
        title: "Documentation",
        items: [
          { label: "Overview", href: "/docs/overview" },
          { label: "Components", href: "/docs/components" },
          { label: "Learning", href: "/docs/learning" },
        ],
      },
      {
        title: "Resources",
        items: [
          { label: "How-To Guides", href: "/docs/how-to" },
          { label: "Quick Reference", href: "/docs/inbox" },
        ],
      },
      {
        title: "Project",
        items: [
          { label: "GitHub", href: "https://github.com/Takazudo/zudo-pd" },
        ],
      },
    ],
    copyright: "\u00a9 2026 Takazudo Modular",
  } as FooterConfig | false,
  headerNav: [
    { label: "Overview", path: "/docs/overview", categoryMatch: "overview" },
    { label: "Components", path: "/docs/components", categoryMatch: "components" },
    { label: "Learning", path: "/docs/learning", categoryMatch: "learning" },
    { label: "How-To", path: "/docs/how-to", categoryMatch: "how-to" },
    { label: "Misc", path: "/docs/misc", categoryMatch: "misc" },
  ] satisfies HeaderNavItem[],
};
