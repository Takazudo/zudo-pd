export type {
  HeaderNavItem,
  ColorModeConfig,
} from "./settings-types";
import type {
  HeaderNavItem,
  ColorModeConfig,
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
  footer: false as false,
  headerNav: [
    { label: "Overview", path: "/docs/overview", categoryMatch: "overview" },
    { label: "Components", path: "/docs/components", categoryMatch: "components" },
    { label: "Learning", path: "/docs/learning", categoryMatch: "learning" },
    { label: "How-To", path: "/docs/how-to", categoryMatch: "how-to" },
    { label: "Misc", path: "/docs/misc", categoryMatch: "misc" },
  ] satisfies HeaderNavItem[],
};
