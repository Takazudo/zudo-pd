import type { AstroIntegration } from "astro";
import { mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { settings } from "../config/settings";
import { stripMarkdown, collectMdFiles, slugToUrl, parseMarkdownFile, isExcluded } from "../utils/content-files";

const MAX_BODY_LENGTH = 300;

export interface SearchIndexEntry {
  id: string;
  title: string;
  body: string;
  url: string;
  description: string;
}

function truncateBody(text: string): string {
  return text.length > MAX_BODY_LENGTH
    ? text.substring(0, MAX_BODY_LENGTH)
    : text;
}

function buildEntries(contentDir: string): SearchIndexEntry[] {
  const absDir = resolve(contentDir);
  const files = collectMdFiles(absDir);
  const entries: SearchIndexEntry[] = [];

  for (const { filePath, slug } of files) {
    const parsed = parseMarkdownFile(filePath);
    if (!parsed) continue;
    const { data, content } = parsed;

    if (isExcluded(data)) continue;

    entries.push({
      id: slug,
      title: data.title ?? slug,
      body: truncateBody(stripMarkdown(content)),
      url: slugToUrl(slug, null),
      description: data.description ?? "",
    });
  }

  return entries;
}

export function collectSearchEntries(): SearchIndexEntry[] {
  return buildEntries(settings.docsDir);
}

export function searchIndexIntegration(): AstroIntegration {
  return {
    name: "search-index",
    hooks: {
      "astro:build:done": async ({ dir, logger }) => {
        const outDir = fileURLToPath(dir);
        const entries = collectSearchEntries();
        const jsonPath = join(outDir, "search-index.json");
        mkdirSync(outDir, { recursive: true });
        writeFileSync(jsonPath, JSON.stringify(entries));
        logger.info(
          `Generated search index with ${entries.length} entries`,
        );
      },

      "astro:config:setup": ({ updateConfig, command }) => {
        if (command !== "dev") return;

        updateConfig({
          vite: {
            plugins: [
              {
                name: "search-index-dev",
                configureServer(server) {
                  server.middlewares.use((req, res, next) => {
                    const match =
                      req.url === "/search-index.json" ||
                      req.url?.endsWith("/search-index.json");
                    if (!match) {
                      next();
                      return;
                    }

                    try {
                      const entries = collectSearchEntries();
                      res.setHeader("Content-Type", "application/json");
                      res.end(JSON.stringify(entries));
                    } catch (err) {
                      res.statusCode = 500;
                      res.setHeader("Content-Type", "application/json");
                      res.end(
                        JSON.stringify({
                          error:
                            err instanceof Error
                              ? err.message
                              : "Internal error",
                        }),
                      );
                    }
                  });
                },
              },
            ],
          },
        });
      },
    },
  };
}
