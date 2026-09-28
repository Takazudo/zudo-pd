#!/usr/bin/env node

/**
 * Every hand-authored `#fragment` link in the docs corpus, resolved against the
 * ids that are ACTUALLY present in the built HTML.
 *
 * ## Why this exists next to check-zfb-link-warnings.sh
 *
 * That script gates the build log. zfb's own `linkValidation` resolves
 * fragments against heading-derived anchors, cannot see the generator's
 * `<EvidenceAnchor>` ids, and — with `onBrokenLinks: "warn"` — never fails a
 * build on its own. So the log gate can only say "no warning shape I don't
 * recognise appeared". It cannot say "this fragment resolves", and in practice
 * it did not: 18 dead anchors (72 occurrences) shipped through a green
 * `pnpm b4push` and were found only by ad-hoc sweeps of `dist/`.
 *
 * ## Why this reads dist/ instead of slugifying headings
 *
 * zfb's heading-anchor plugin runs the HIERARCHICAL strategy
 * (`settings.headingIdStrategy`): an `h3` gets its parent `h2`'s slug prefixed
 * onto its own, so
 *
 *     ## Protection Stage
 *     ### PTC1 and the L7812 current-limit cascade
 *
 * renders as `id="protection-stage-ptc1-and-the-l7812-current-limit-cascade"`,
 * not the bare `#ptc1-and-the-l7812-current-limit-cascade` a human writes.
 * Unicode survives into the id (`↔ → — –  ×`), and `13.5` becomes `13-5`
 * rather than `135`. Every one of those is a rule a hand-written slugifier gets
 * wrong — they are precisely the rules the dead anchors got wrong.
 *
 * Reimplementing that strategy here would bake the same guesswork into the
 * checker meant to catch it, and would go stale the first time zfb changes the
 * strategy or the settings flip to "flat". So this parses `id=` attributes out
 * of `dist/**\/*.html` and treats those bytes as the only truth about what
 * resolves in a browser. There is no slug function in this file.
 *
 * ## What it checks, and what it deliberately does not
 *
 * Checked: every markdown link with a fragment whose destination is a docs
 * page — a relative `.md`/`.mdx` sibling, a root-absolute route, or a same-page
 * `#…`. Reported as NO_PAGE (no such built page) or NO_ANCHOR (page built, id
 * absent).
 *
 * Skipped, by design:
 *   - external destinations (`https:`, `mailto:`, protocol-relative) — nothing
 *     in `dist/` can confirm or deny a remote page's anchors;
 *   - root-absolute destinations naming a non-HTML asset (`/datasheets/x.pdf#page=3`)
 *     — `#page=3` is a PDF viewer instruction, not a DOM id;
 *   - anything inside a fenced code block, an inline code span or an HTML
 *     comment — those are samples, not links.
 *
 * `#fact-…` / `#src-…` / `#rec-…` anchors on the generated component pages are
 * NOT a tolerated exception here: those ids really do render (the generator
 * emits `<EvidenceAnchor>`), so they resolve against `dist/` like any other id.
 * They only need suppressing in the log gate, where zfb's heading-only resolver
 * is the thing being worked around.
 *
 * Usage:
 *   pnpm build                       # dist/ must be current
 *   node circuit/scripts/check-built-fragment-links.mjs
 *   node …/check-built-fragment-links.mjs --docs <dir> --dist <dir> [--quiet]
 */

import { readFile, readdir } from "node:fs/promises";
import { basename, join, relative, resolve, sep } from "node:path";
import { posix } from "node:path";
import { fileURLToPath } from "node:url";

const DOCS_ROUTE_PREFIX = "/docs";

// ---------------------------------------------------------------------------
// Reading the built site
// ---------------------------------------------------------------------------

/** Every `.html` file under `root`, as paths relative to it (posix separators). */
async function listHtmlFiles(root) {
  const found = [];
  async function walk(directory) {
    const entries = await readdir(directory, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isSymbolicLink()) continue;
      const full = join(directory, entry.name);
      if (entry.isDirectory()) {
        await walk(full);
      } else if (entry.isFile() && entry.name.endsWith(".html")) {
        found.push(relative(root, full).split(sep).join("/"));
      }
    }
  }
  await walk(root);
  return found.sort();
}

/**
 * `docs/overview/bom/index.html` -> `/docs/overview/bom`; `index.html` -> `/`.
 * Routes are normalised WITHOUT a trailing slash, matching
 * `settings.trailingSlash: false`, so both link forms compare equal.
 */
export function routeForBuiltFile(relativeHtmlPath) {
  let route = `/${relativeHtmlPath}`;
  route = route.replace(/\/index\.html$/u, "").replace(/\.html$/u, "");
  return route === "" ? "/" : route;
}

/**
 * `id` attribute values in document markup. `<script>` and `<style>` bodies are
 * cut first: a template string inside a bundle is not a rendered element, and an
 * id "found" there would make the gate accept an anchor no reader can reach.
 */
export function collectIds(html) {
  const markup = html.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/giu, " ");
  const ids = new Set();
  const pattern = /\sid\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'`=<>]+))/giu;
  for (const match of markup.matchAll(pattern)) {
    const raw = match[1] ?? match[2] ?? match[3] ?? "";
    const value = decodeHtmlEntities(raw).trim();
    if (value !== "") ids.add(value);
  }
  return ids;
}

function decodeHtmlEntities(value) {
  return value
    .replaceAll("&quot;", '"')
    .replaceAll("&#34;", '"')
    .replaceAll("&#39;", "'")
    .replaceAll("&apos;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&amp;", "&");
}

/** route -> Set(ids), for every built HTML page. */
export async function buildAnchorIndex(distRoot) {
  const index = new Map();
  for (const relativePath of await listHtmlFiles(distRoot)) {
    const html = await readFile(join(distRoot, relativePath), "utf8");
    index.set(routeForBuiltFile(relativePath), collectIds(html));
  }
  return index;
}

// ---------------------------------------------------------------------------
// Reading the source corpus
// ---------------------------------------------------------------------------

async function listMarkdownFiles(root) {
  const found = [];
  async function walk(directory) {
    const entries = await readdir(directory, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isSymbolicLink()) continue;
      const full = join(directory, entry.name);
      if (entry.isDirectory()) {
        await walk(full);
      } else if (entry.isFile() && /\.mdx?$/u.test(entry.name)) {
        found.push(relative(root, full).split(sep).join("/"));
      }
    }
  }
  await walk(root);
  return found.sort();
}

/**
 * Blank out fenced code, inline code spans and HTML comments, preserving every
 * character position so reported line numbers stay true to the file. A `](…)`
 * inside a shell sample or an escaped-anchor example is documentation, not a
 * link, and must not be resolved.
 */
export function maskNonProse(source) {
  // `split("")`, not `[...source]`: the spread iterates CODE POINTS, so one
  // astral character would collapse two array slots into one and shift every
  // offset after it out of step with `line.length` and `RegExp.index`, which
  // are UTF-16 counts. Blanking both halves of a surrogate pair is harmless —
  // they are always inside the same masked range.
  const characters = source.split("");
  const blank = (from, to) => {
    for (let index = from; index < to && index < characters.length; index += 1) {
      if (characters[index] !== "\n") characters[index] = " ";
    }
  };

  // Fenced blocks, line-oriented: an opening fence is closed only by a fence of
  // the same character and at least the same length.
  let offset = 0;
  let fence = null;
  for (const line of source.split("\n")) {
    const match = /^ {0,3}(`{3,}|~{3,})/u.exec(line);
    if (fence === null) {
      if (match) {
        fence = { char: match[1][0], length: match[1].length };
        blank(offset, offset + line.length);
      }
    } else {
      blank(offset, offset + line.length);
      if (match && match[1][0] === fence.char && match[1].length >= fence.length) {
        fence = null;
      }
    }
    offset += line.length + 1;
  }

  let masked = characters.join("");

  // HTML/MDX comments.
  masked = masked.replace(/<!--[\s\S]*?-->/gu, (block) => block.replace(/[^\n]/gu, " "));

  // Inline code spans: a run of N backticks closes on the next run of exactly N.
  const withoutInlineCode = masked.split("");
  const spanPattern = /`+/gu;
  let openMatch;
  while ((openMatch = spanPattern.exec(masked)) !== null) {
    const ticks = openMatch[0].length;
    const closer = new RegExp(`(?<!\`)\`{${ticks}}(?!\`)`, "u");
    const rest = masked.slice(spanPattern.lastIndex);
    const closeAt = rest.search(closer);
    if (closeAt < 0) continue;
    const from = openMatch.index;
    const to = spanPattern.lastIndex + closeAt + ticks;
    for (let index = from; index < to; index += 1) {
      if (withoutInlineCode[index] !== "\n") withoutInlineCode[index] = " ";
    }
    spanPattern.lastIndex = to;
  }

  return withoutInlineCode.join("");
}

/**
 * Markdown inline links, with the raw destination. Scanned rather than
 * regexed so a destination containing balanced parentheses, an angle-bracketed
 * destination, or a `"title"` suffix is read the way a markdown parser reads it.
 */
export function findMarkdownLinks(source) {
  const text = maskNonProse(source);
  const lineStarts = collectLineStarts(text);
  const links = [];

  for (let cursor = 0; cursor < text.length - 1; cursor += 1) {
    if (text[cursor] !== "]" || text[cursor + 1] !== "(") continue;
    if (cursor > 0 && text[cursor - 1] === "\\") continue;

    let index = cursor + 2;
    while (index < text.length && /\s/u.test(text[index])) index += 1;

    let destination = "";
    if (text[index] === "<") {
      const close = text.indexOf(">", index + 1);
      if (close < 0) continue;
      destination = text.slice(index + 1, close);
      index = close + 1;
    } else {
      let depth = 0;
      const start = index;
      while (index < text.length) {
        const character = text[index];
        if (character === "\\") {
          index += 2;
          continue;
        }
        if (character === "(") depth += 1;
        else if (character === ")") {
          if (depth === 0) break;
          depth -= 1;
        } else if (/\s/u.test(character)) break;
        index += 1;
      }
      destination = text.slice(start, index);
    }

    // Optional title, then the closing paren. A destination we cannot close is
    // not a link.
    while (index < text.length && /\s/u.test(text[index])) index += 1;
    if (text[index] === '"' || text[index] === "'") {
      const quote = text[index];
      const close = text.indexOf(quote, index + 1);
      if (close < 0) continue;
      index = close + 1;
      while (index < text.length && /\s/u.test(text[index])) index += 1;
    }
    if (text[index] !== ")") continue;

    links.push({
      destination,
      offset: cursor,
      line: lineFor(lineStarts, cursor),
      isImage: openerIsImage(text, cursor),
    });
    cursor = index;
  }

  return links;
}

/** Offsets of every line start, built once so line lookup is a binary search. */
function collectLineStarts(text) {
  const starts = [0];
  for (let index = 0; index < text.length; index += 1) {
    if (text[index] === "\n") starts.push(index + 1);
  }
  return starts;
}

function lineFor(lineStarts, offset) {
  let low = 0;
  let high = lineStarts.length - 1;
  while (low < high) {
    const middle = (low + high + 1) >> 1;
    if (lineStarts[middle] <= offset) low = middle;
    else high = middle - 1;
  }
  return low + 1;
}

/** Walk back to the `[` that opens this label and report whether a `!` precedes it. */
function openerIsImage(text, closeBracketIndex) {
  let depth = 0;
  for (let index = closeBracketIndex - 1; index >= 0; index -= 1) {
    if (text[index - 1] === "\\") continue;
    if (text[index] === "]") depth += 1;
    else if (text[index] === "[") {
      if (depth === 0) return text[index - 1] === "!";
      depth -= 1;
    }
  }
  return false;
}

// ---------------------------------------------------------------------------
// Resolving a destination onto a built route
// ---------------------------------------------------------------------------

export function routeForSourceFile(relativeSourcePath) {
  const withoutExtension = relativeSourcePath.replace(/\.mdx?$/u, "");
  if (withoutExtension === "index") return DOCS_ROUTE_PREFIX;
  return `${DOCS_ROUTE_PREFIX}/${withoutExtension.replace(/(^|\/)index$/u, "")}`.replace(
    /\/$/u,
    "",
  );
}

function normaliseRoute(route) {
  const trimmed = route.replace(/\/+$/u, "");
  return trimmed === "" ? "/" : trimmed;
}

/**
 * `{ route, fragment }` for a destination this gate is responsible for, or
 * `null` for one it deliberately does not resolve (see the header).
 */
export function resolveDestination(relativeSourcePath, destination) {
  const hash = destination.indexOf("#");
  if (hash < 0) return null;

  // A query string is not part of the path — `/docs/x?v=2#frag` addresses the
  // same page as `/docs/x#frag`, and leaving `?v=2` on would report NO_PAGE.
  const target = destination.slice(0, hash).split("?")[0];
  const rawFragment = destination.slice(hash + 1);
  if (rawFragment === "") return null;

  let fragment;
  try {
    fragment = decodeURIComponent(rawFragment);
  } catch {
    fragment = rawFragment;
  }

  if (target === "") {
    return { route: routeForSourceFile(relativeSourcePath), fragment };
  }
  if (/^[a-z][a-z0-9+.-]*:/iu.test(target) || target.startsWith("//")) {
    return null; // external
  }

  if (target.startsWith("/")) {
    const route = normaliseRoute(target);
    const leaf = basename(route);
    // A non-HTML asset's fragment is not a DOM id (`…​.pdf#page=3`).
    if (/\.[a-z0-9]+$/iu.test(leaf) && !/\.html?$/iu.test(leaf)) return null;
    return { route: route.replace(/\.html?$/iu, ""), fragment };
  }

  // Relative. Only a markdown sibling names a docs page; anything else is an
  // asset reference and is left to the build's own asset handling.
  if (!/\.mdx?$/u.test(target)) return null;
  const resolved = posix.normalize(posix.join(posix.dirname(relativeSourcePath), target));
  if (resolved.startsWith("..")) {
    return { route: null, fragment, escaped: resolved };
  }
  return { route: routeForSourceFile(resolved), fragment };
}

// ---------------------------------------------------------------------------
// The check
// ---------------------------------------------------------------------------

export async function checkFragmentLinks({ docsRoot, distRoot }) {
  const anchorIndex = await buildAnchorIndex(distRoot);
  const sourceFiles = await listMarkdownFiles(docsRoot);

  const failures = [];
  let checked = 0;

  for (const relativePath of sourceFiles) {
    const source = await readFile(join(docsRoot, relativePath), "utf8");
    for (const link of findMarkdownLinks(source)) {
      const resolved = resolveDestination(relativePath, link.destination);
      if (resolved === null) continue;
      checked += 1;

      const where = `${relativePath}:${link.line}`;
      if (resolved.route === null) {
        failures.push({
          where,
          destination: link.destination,
          reason: "ESCAPES_DOCS_ROOT",
          detail: resolved.escaped,
        });
        continue;
      }

      const ids = anchorIndex.get(resolved.route);
      if (ids === undefined) {
        failures.push({
          where,
          destination: link.destination,
          reason: "NO_PAGE",
          detail: resolved.route,
        });
        continue;
      }
      if (!ids.has(resolved.fragment)) {
        failures.push({
          where,
          destination: link.destination,
          reason: link.isImage ? "NO_ANCHOR_IN_IMAGE" : "NO_ANCHOR",
          detail: `${resolved.route}#${resolved.fragment}`,
        });
      }
    }
  }

  return { failures, checked, files: sourceFiles.length, pages: anchorIndex.size };
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function readOption(argv, name, fallback) {
  const at = argv.indexOf(name);
  if (at < 0) return fallback;
  const value = argv[at + 1];
  if (value === undefined) {
    process.stderr.write(`${name} needs a value\n`);
    process.exit(2);
  }
  return value;
}

async function main(argv) {
  const docsRoot = resolve(readOption(argv, "--docs", fileURLToPath(new URL("../../doc/src/content/docs", import.meta.url))));
  const distRoot = resolve(readOption(argv, "--dist", fileURLToPath(new URL("../../doc/dist", import.meta.url))));
  const quiet = argv.includes("--quiet");

  let result;
  try {
    result = await checkFragmentLinks({ docsRoot, distRoot });
  } catch (error) {
    if (error?.code === "ENOENT") {
      process.stderr.write(
        `cannot read ${error.path ?? "input"} — run \`pnpm build\` before this check\n`,
      );
      return 2;
    }
    throw error;
  }

  if (result.pages === 0) {
    process.stderr.write(`no built pages under ${distRoot} — run \`pnpm build\` first\n`);
    return 2;
  }

  if (result.failures.length > 0) {
    process.stderr.write(
      `${result.failures.length} dead fragment link(s) in ${result.files} source file(s):\n`,
    );
    for (const failure of result.failures) {
      process.stderr.write(
        `  ${failure.where}: ${failure.destination}  [${failure.reason}] -> ${failure.detail}\n`,
      );
    }
    process.stderr.write(
      "\nIds are read from the built HTML, so a NO_ANCHOR means the id is genuinely absent.\n" +
        "Heading ids are HIERARCHICAL: an h3's id is its parent h2's slug + its own\n" +
        "(`## Protection Stage` + `### PTC1 …` -> `#protection-stage-ptc1-…`). Copy the id\n" +
        "out of dist/ rather than writing the bare slug by hand.\n",
    );
    if (process.env.GITHUB_ACTIONS) {
      process.stdout.write(
        `::error::${result.failures.length} hand-authored #fragment link(s) point at ids that do not exist in the built HTML.\n`,
      );
    }
    return 1;
  }

  if (!quiet) {
    process.stdout.write(
      `fragment check: ${result.checked} fragment link(s) across ${result.files} source file(s) ` +
        `all resolve against ids in ${result.pages} built page(s)\n`,
    );
  }
  return 0;
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) {
  process.exitCode = await main(process.argv.slice(2));
}
