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
    sitemap: true,
    dynamicPageTransition: true,
    // The publication matrix exposes reviewed component evidence, not raw skills.
    claudeResources: false,
    headerNav: [
      { label: "Getting Started", path: "/docs/getting-started", categoryMatch: "getting-started" },
      { label: "Architecture", path: "/docs/architecture", categoryMatch: "architecture" },
      { label: "Components", path: "/docs/components", categoryMatch: "components" },
      { label: "How-To", path: "/docs/how-to", categoryMatch: "how-to" },
      {
        label: "Archive",
        path: "/docs/archive",
        children: [
          { label: "Archive Guide", path: "/docs/archive", categoryMatch: "archive" },
          { label: "Previous Design", path: "/docs/overview", categoryMatch: "overview" },
          { label: "Diagnosis & Decisions", path: "/docs/inbox", categoryMatch: "inbox" },
          { label: "Learning Notes", path: "/docs/learning", categoryMatch: "learning" },
          { label: "Legacy Resources", path: "/docs/misc", categoryMatch: "misc" },
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
