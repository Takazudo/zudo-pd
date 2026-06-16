import { z } from "zod";
import { defineConfig } from "zfb/config";
import { settings } from "./src/config/settings";
import { buildDocsSchema } from "./src/config/docs-schema";

const docsSchema = buildDocsSchema();

const docsSchemaJson = z.toJSONSchema(docsSchema) as Record<string, unknown>;

interface CollectionEntryShape {
  name: string;
  path: string;
  schema: Record<string, unknown>;
}

const collections: CollectionEntryShape[] = [];

collections.push({ name: "docs", path: settings.docsDir, schema: docsSchemaJson });

for (const [code, config] of Object.entries(settings.locales)) {
  collections.push({ name: `docs-${code}`, path: config.dir, schema: docsSchemaJson });
}

if (settings.versions) {
  for (const version of settings.versions) {
    collections.push({
      name: `docs-v-${version.slug}`,
      path: version.docsDir,
      schema: docsSchemaJson,
    });
    if (version.locales) {
      for (const [code, config] of Object.entries(version.locales)) {
        collections.push({
          name: `docs-v-${version.slug}-${code}`,
          path: config.dir,
          schema: docsSchemaJson,
        });
      }
    }
  }
}

const localeArray = Object.entries(settings.locales).map(([code, locale]) => ({
  code,
  dir: locale.dir,
}));
const localeRecord = Object.fromEntries(
  Object.entries(settings.locales).map(([code, locale]) => [code, { dir: locale.dir }]),
);

const integrationPlugins = [
  ...(settings.claudeResources
    ? [
        {
          name: "./plugins/claude-resources-plugin.mjs",
          options: {
            claudeDir: settings.claudeResources.claudeDir,
            projectRoot: settings.claudeResources.projectRoot,
            docsDir: settings.docsDir,
          },
        },
      ]
    : []),
  ...(settings.docHistory
    ? [
        {
          name: "./plugins/doc-history-plugin.mjs",
          options: {
            docsDir: settings.docsDir,
            locales: localeRecord,
            base: settings.base,
          },
        },
      ]
    : []),
  {
    name: "./plugins/search-index-plugin.mjs",
    options: {
      docsDir: settings.docsDir,
      locales: localeRecord,
      base: settings.base,
    },
  },
  {
    name: "./plugins/copy-public-plugin.mjs",
    options: {
      publicDir: "public",
    },
  },
];

export default defineConfig({
  framework: "preact",
  // Pin the dev/preview port — zfb defaults to 3000, but the generated
  // CLAUDE.md and the Tauri dev wrappers assume 4321.
  port: 4321,
  tailwind: { enabled: true },
  // Dual-theme syntect highlighting (zfb next.47 / zudo-doc 0.2.8). Both names
  // are SYNTECT built-ins (NOT Shiki names); setting the pair makes the engine
  // color tokens with `--shiki-light`/`--shiki-dark` CSS custom props instead of
  // a single inline `color:`, which `src/styles/global.css` resolves via
  // `light-dark()`. Without this the default single `base16-ocean.dark` theme
  // renders near-invisible code on the light site theme.
  codeHighlight: {
    themeLight: "base16-ocean.light",
    themeDark: "base16-ocean.dark",
  },
  collections,
  stripMdExt: true,
  resolveMarkdownLinks: {
    enabled: true,
    dirs: [
      { dir: settings.docsDir, routePrefix: "/docs/" },
      ...Object.entries(settings.locales).map(([code, locale]) => ({
        dir: locale.dir,
        routePrefix: `/${code}/docs/`,
      })),
      // Versioned collections: each version's EN dir + per-locale dirs.
      ...(settings.versions
        ? settings.versions.flatMap((version) => [
            { dir: version.docsDir, routePrefix: `/v/${version.slug}/docs/` },
            ...Object.entries(version.locales ?? {}).map(([code, locale]) => ({
              dir: locale.dir,
              routePrefix: `/v/${version.slug}/${code}/docs/`,
            })),
          ])
        : []),
    ],
    onBrokenLinks: "warn",
  },
  base: settings.base,
  trailingSlash: settings.trailingSlash,
  markdown: {
    features: {
      // Former-Core features (were always-on before zfb next.12).
      // imageEnlarge was a former-Core feature but was hard-removed in zfb
      // next.18 — it is now re-implemented via an MDX p-override.
      //
      // Admonitions recipe: register the :::name directive vocabulary
      // (note/tip/info/warning/danger/caution/details) → components.
      //
      // KNOWN-BROKEN (zfb next.49): the native engine accepts this map (the
      // loader validates the key + deserializes the entries) but does NOT
      // transform `:::name` container directives into the mapped components —
      // they leak through as literal `<p>:::tip[...]</p>` text. `githubAlerts`
      // (the `> [!NOTE]` path) works, so only the user-directive path is dead.
      // Upstream bug: Takazudo/zudo-front-builder#1085. Until that lands,
      // admonitions in the corpus are authored as `<Note>` / `<Tip title="…">`
      // JSX (which renders correctly) — see doc/CLAUDE.md "Admonitions".
      // This map is kept so re-enabling `:::` authoring is a one-line revert
      // once the engine is fixed.
      directives: {
        note: "Note",
        tip: "Tip",
        info: "Info",
        warning: "Warning",
        danger: "Danger",
        caution: "Caution",
        details: "Details", // collapsible — routes to DetailsWrapper
      },
      mermaid: true,
      headingMarkerToc: true,
      // Safe opt-in features.
      githubAlerts: true,
      readingTime: true,
      codeEnrichment: {},
      codeTabs: true,
      imageDimensions: {},
      // warn-only link validation — failOnBroken: false never fails the build.
      linkValidation: { failOnBroken: false },
      // Heading-ID (anchor) strategy — single source of truth in
      // settings.headingIdStrategy, also mirrored by the host TOC builder
      // (pages/lib/_extract-headings.ts) so TOC anchors match rendered ids.
      headingIds: { strategy: settings.headingIdStrategy },
    },
  },
  // Cloudflare adapter — wraps the SSR bundle into `dist/_worker.js` (the
  // explicit main entry for Workers static assets) plus a sidecar
  // `dist/_zfb_inner.mjs`. Required so `pnpm build` emits a worker for the
  // CF Workers static-assets deploy (see doc/wrangler.toml + main-deploy.yml).
  adapter: "@takazudo/zfb-adapter-cloudflare",
  plugins: integrationPlugins,
});
