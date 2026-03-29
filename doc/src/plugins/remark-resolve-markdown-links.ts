import type { Root, Link, Definition, Node } from "mdast";
import { visit } from "unist-util-visit";
import { resolve, dirname } from "node:path";
import { readdirSync } from "node:fs";

export interface ResolveMarkdownLinksOptions {
  rootDir: string;
  docsDir: string;
  locales: Record<string, { dir: string }>;
  versions: Array<{ slug: string; docsDir: string }> | false;
  base: string;
  trailingSlash: boolean;
  onBrokenLinks?: "warn" | "error" | "ignore";
}

function isExternal(url: string): boolean {
  return /^[a-z][a-z0-9+.-]*:/i.test(url);
}

function hasMarkdownExtension(url: string): boolean {
  const pathname = url.split(/[?#]/)[0];
  return /\.mdx?$/.test(pathname);
}

function parseUrl(url: string): {
  pathname: string;
  search: string;
  hash: string;
} {
  const hashIdx = url.indexOf("#");
  const searchIdx = url.indexOf("?");

  let pathname = url;
  let search = "";
  let hash = "";

  if (hashIdx >= 0) {
    hash = url.slice(hashIdx);
    pathname = url.slice(0, hashIdx);
  }
  if (searchIdx >= 0 && (hashIdx < 0 || searchIdx < hashIdx)) {
    search = hash ? url.slice(searchIdx, hashIdx) : url.slice(searchIdx);
    pathname = url.slice(0, searchIdx);
  }

  return { pathname, search, hash };
}

function buildDocsSourceMap(options: ResolveMarkdownLinksOptions): Map<string, string> {
  const map = new Map<string, string>();
  const { rootDir, docsDir, locales, versions, base, trailingSlash } = options;

  const normalizedBase = base.replace(/\/+$/, "");

  function applyTS(url: string): string {
    if (trailingSlash) {
      if (url.endsWith("/")) return url;
      return url + "/";
    }
    if (url !== "/" && url.endsWith("/")) {
      return url.replace(/\/+$/, "");
    }
    return url;
  }

  function withBase(path: string): string {
    const raw =
      normalizedBase === ""
        ? path
        : `${normalizedBase}${path.startsWith("/") ? path : `/${path}`}`;
    return applyTS(raw);
  }

  function scanDir(dir: string, urlPrefix: string): void {
    const absDir = resolve(rootDir, dir);
    let files: string[];
    try {
      files = readdirSync(absDir, { recursive: true })
        .map((f) => String(f))
        .filter((f) => /\.(md|mdx)$/.test(f));
    } catch {
      return;
    }
    for (const file of files) {
      const absFile = resolve(absDir, file);
      const slug = file
        .replace(/\.(md|mdx)$/, "")
        .replace(/(^|\/)index$/, "$1")
        .replace(/(^|\\)index$/, "$1")
        .replace(/\\/g, "/")
        .replace(/\/$/, "");
      const url = withBase(`${urlPrefix}/${slug}`);
      map.set(absFile, url);

      const altExt = file.endsWith(".mdx")
        ? file.replace(/\.mdx$/, ".md")
        : file.replace(/\.md$/, ".mdx");
      const altFile = resolve(absDir, altExt);
      if (!map.has(altFile)) {
        map.set(altFile, url);
      }
    }
  }

  scanDir(docsDir, "/docs");

  for (const [code, config] of Object.entries(locales)) {
    scanDir(config.dir, `/${code}/docs`);
  }

  if (versions) {
    for (const version of versions) {
      scanDir(version.docsDir, `/v/${version.slug}/docs`);
    }
  }

  return map;
}

export function remarkResolveMarkdownLinks(
  options: ResolveMarkdownLinksOptions,
) {
  const onBrokenLinks = options.onBrokenLinks ?? "warn";
  const sourceMap = buildDocsSourceMap(options);

  return (tree: Root, file: { path?: string }) => {

    const currentFilePath = file.path;
    if (!currentFilePath) return;

    const currentDir = dirname(currentFilePath);

    visit(tree, (node: Node) => {
      if (node.type !== "link" && node.type !== "definition") return;
      const linkNode = node as Link | Definition;
      const url = linkNode.url;

      if (
        !url ||
        isExternal(url) ||
        url.startsWith("#") ||
        !hasMarkdownExtension(url)
      )
        return;

      const { pathname, search, hash } = parseUrl(url);
      const resolvedPath = resolve(currentDir, pathname);
      const resolvedUrl = sourceMap.get(resolvedPath);

      if (resolvedUrl) {
        linkNode.url = resolvedUrl + search + hash;
      } else {
        const fileRelative = file.path ?? "unknown";
        const message = `Broken markdown link: "${url}" in ${fileRelative} (resolved to ${resolvedPath})`;

        if (onBrokenLinks === "error") {
          throw new Error(message);
        } else if (onBrokenLinks === "warn") {
          console.warn(`[remark-resolve-markdown-links] WARNING: ${message}`);
        }
      }
    });
  };
}
