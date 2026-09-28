import { defineConfig } from "zfb/config";
import { zudoDoc } from "@takazudo/zudo-doc/config";

export default defineConfig(
  zudoDoc({
    themePack: "sumi",
    siteName: "zudo-pd",
    githubUrl: "https://github.com/Takazudo/zudo-pd",
    siteUrl: "https://pd.takazudomodular.com",
    logo: "/img/logo.svg",
    llmsTxt: true,
    cjkFriendly: true,
    docHistory: true,
    // Generated evidence carries its own source revision and retrieval date.
    docHistoryExclude: ["components", "components/**"],
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
        categoryMatch: "project",
        children: [
          { label: "Project Overview", path: "/docs/project" },
          { label: "Procedures", path: "/docs/project/procedures" },
          { label: "Archive Guide", path: "/docs/archive", categoryMatch: "archive" },
          { label: "Previous Design", path: "/docs/overview", categoryMatch: "overview" },
          { label: "Diagnosis & Decisions", path: "/docs/inbox", categoryMatch: "inbox" },
          { label: "Learning Notes", path: "/docs/learning", categoryMatch: "learning" },
          { label: "Legacy Resources", path: "/docs/misc", categoryMatch: "misc" },
        ],
      },
      { label: "Architecture", path: "/docs/architecture", categoryMatch: "architecture" },
      { label: "Research", path: "/docs/research", categoryMatch: "research" },
      { label: "Decisions", path: "/docs/decisions", categoryMatch: "decisions" },
      { label: "Verification", path: "/docs/verification", categoryMatch: "verification" },
      { label: "Components", path: "/docs/components", categoryMatch: "components" },
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
