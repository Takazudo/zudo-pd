import { defineConfig } from "zfb/config";
import { zudoDoc } from "@takazudo/zudo-doc/config";

export default defineConfig(
  zudoDoc({
    themePack: "sumi",
    siteName: "zudo-pd + LED Lamp",
    githubUrl: "https://github.com/Takazudo/zudo-pd",
    siteUrl: "https://pd.takazudomodular.com",
    logo: "/img/logo.svg",
    llmsTxt: true,
    cjkFriendly: true,
    docHistory: true,
    // Generated evidence carries its own source revision and retrieval date.
    docHistoryExclude: ["components", "components/**", "led-lamp", "led-lamp/**", "catalog", "catalog/**"],
    bodyFootUtilArea: { docHistory: true, viewSourceLink: false },
    metaTags: {
      description: true,
      keywords: false,
      ogImage: "/img/ogp.png",
      ogSiteName: true,
      twitterCard: "summary_large_image",
    },
    sidebarResizer: true,
    sidebarToggle: true,
    imageEnlarge: true,
    tocToggle: true,
    assetViewer: true,
    // Relative to public/assets; package previews keep their own publication path.
    assetViewerExclude: ["component-previews/**"],
    assetViewerIndex: false,
    assetViewerIndexing: false,
    strictContentBridge: true,
    sitemap: false,
    dynamicPageTransition: true,
    // The publication matrix exposes reviewed component evidence, not raw skills.
    claudeResources: false,
    headerNav: [
      {
        label: "Project",
        path: "/docs/project",
        children: [
          { label: "Project index", path: "/docs/project", categoryMatch: "project" },
          { label: "Architecture", path: "/docs/architecture", categoryMatch: "architecture" },
          { label: "Verification", path: "/docs/verification", categoryMatch: "verification" },
          { label: "Decisions", path: "/docs/decisions", categoryMatch: "decisions" },
          { label: "Research", path: "/docs/research", categoryMatch: "research" },
          { label: "Archive", path: "/docs/archive", categoryMatch: "archive" },
          { label: "Previous design", path: "/docs/overview", categoryMatch: "overview" },
          { label: "Diagnosis", path: "/docs/inbox", categoryMatch: "inbox" },
          { label: "Learning", path: "/docs/learning", categoryMatch: "learning" },
          { label: "Legacy resources", path: "/docs/misc", categoryMatch: "misc" },
        ],
      },
      { label: "Shared P15", path: "/docs/shared-p15", categoryMatch: "shared-p15" },
      { label: "PD15", path: "/docs/pd15", categoryMatch: "pd15" },
      { label: "PD20", path: "/docs/pd20", categoryMatch: "pd20" },
      { label: "LED Lamp", path: "/docs/led-lamp", categoryMatch: "led-lamp" },
      {
        label: "Components",
        path: "/docs/catalog",
        children: [
          { label: "Catalog entry", path: "/docs/catalog", categoryMatch: "catalog" },
          { label: "Reviewed PD records", path: "/docs/components", categoryMatch: "components" },
        ],
      },
    ],
    headerRightItems: [
      { type: "component", component: "github-link" },
      { type: "component", component: "theme-toggle" },
      { type: "component", component: "search" },
    ],
    chromeBindingsModule: "./src/chrome-bindings.tsx",
    adapter: "@takazudo/zfb-adapter-cloudflare",
  }),
);
