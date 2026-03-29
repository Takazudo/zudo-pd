import { defineConfig } from "astro/config";
import { fileURLToPath } from "node:url";
import mdx from "@astrojs/mdx";
import preact from "@astrojs/preact";
import {
  transformerMetaHighlight,
  transformerMetaWordHighlight,
} from "@shikijs/transformers";
import tailwindcss from "@tailwindcss/vite";
import { colorSchemes } from "./src/config/color-schemes";
import { settings } from "./src/config/settings";
import { claudeResourcesIntegration } from "./src/integrations/claude-resources";
import { searchIndexIntegration } from "./src/integrations/search-index";
import remarkDirective from "remark-directive";
import { remarkAdmonitions } from "./src/plugins/remark-admonitions";
import { remarkResolveMarkdownLinks } from "./src/plugins/remark-resolve-markdown-links";
import { rehypeCodeTitle } from "./src/plugins/rehype-code-title";
import { rehypeHeadingLinks } from "./src/plugins/rehype-heading-links";
import { rehypeMermaid } from "./src/plugins/rehype-mermaid";
import { rehypeStripMdExtension } from "./src/plugins/rehype-strip-md-extension";

const shikiTransformers = [
  transformerMetaHighlight(),
  transformerMetaWordHighlight(),
];

const shikiConfig = settings.colorMode
  ? {
      themes: {
        light:
          colorSchemes[settings.colorMode.lightScheme]?.shikiTheme ??
          "github-light",
        dark:
          colorSchemes[settings.colorMode.darkScheme]?.shikiTheme ?? "dracula",
      },
      defaultColor: false as const,
      transformers: shikiTransformers,
    }
  : {
      theme:
        colorSchemes[settings.colorScheme]?.shikiTheme ?? "dracula",
      transformers: shikiTransformers,
    };

export default defineConfig({
  output: "static",
  trailingSlash: settings.trailingSlash ? "always" : "never",
  base: settings.base,
  server: { port: 3800 },
  integrations: [
    mdx(),
    preact({ compat: true }),
    searchIndexIntegration(),
    ...(settings.claudeResources
      ? [claudeResourcesIntegration(settings.claudeResources)]
      : []),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
  markdown: {
    shikiConfig,
    remarkPlugins: [
      remarkDirective,
      remarkAdmonitions,
      [remarkResolveMarkdownLinks, {
        rootDir: fileURLToPath(new URL(".", import.meta.url)),
        docsDir: settings.docsDir,
        locales: {},
        versions: false,
        base: settings.base,
        trailingSlash: settings.trailingSlash,
        onBrokenLinks: settings.onBrokenMarkdownLinks,
      }],
    ],
    rehypePlugins: [
      rehypeCodeTitle,
      rehypeHeadingLinks,
      rehypeStripMdExtension,
      ...(settings.mermaid ? [rehypeMermaid] : []),
    ],
  },
});
