/**
 * Safe MDX generation: data to AST to text, then verify the text.
 *
 * Three layers, each of which alone would be insufficient:
 *
 *   1. BUILD  — the only way to construct content is the builders below, which
 *               accept `SafeText`/`SafeUrl` and a closed node vocabulary. There
 *               is no "raw" node type, so a caller cannot inject markup even by
 *               trying.
 *   2. SERIALIZE — `mdast-util-to-markdown` with the MDX and GFM-table
 *               extensions does the escaping. The MDX extension is what
 *               escapes `{` (plain markdown does not care about braces, so
 *               without it every evidence string is a live MDX expression).
 *   3. GUARD  — `assertMdxSafe` re-reads the FINAL file text and fails the
 *               build on anything active that survived. This is the layer that
 *               catches a serializer regression or a construct the extensions
 *               do not know about (`:::` directives are enabled on this site
 *               and are not part of any escaping table).
 */

import { toMarkdown } from "mdast-util-to-markdown";
import { mdxToMarkdown } from "mdast-util-mdx";
import { gfmTableToMarkdown } from "mdast-util-gfm-table";
import type { Nodes, PhrasingContent, RootContent } from "mdast";

import { fail } from "./errors.ts";
import { SLUG_PATTERN, type Anchor } from "./ids.ts";
import type { SafeText } from "./text.ts";
import type { SafeUrl } from "./url.ts";

/**
 * The only MDX components generated pages may reference, each with the only
 * attribute names it accepts.
 *
 * `EvidenceAnchor`, `EvidenceDetails`, `EvidenceTable` and
 * `ComponentReferences` are bound in this project's
 * `doc/src/chrome-bindings.tsx`; `CategoryNav` ships globally from
 * `@takazudo/zudo-doc` and needs no binding. A name outside this map — or an
 * attribute outside its component's list — fails the guard, because an
 * unbound component renders as literal text and would silently swallow
 * content.
 *
 * led-lamp also lists `PackageModelViewer` here. It is deliberately absent:
 * `tests/presentation.test.ts` requires every name on this list to be
 * imported AND registered in the host, and the interactive 3D viewer has no
 * assets to show and no binding yet. It joins the list with its component.
 */
export const ALLOWED_COMPONENT_ATTRIBUTES = {
  EvidenceAnchor: ["id"],
  EvidenceDetails: ["label"],
  EvidenceTable: ["label"],
  ComponentReferences: ["descriptor"],
  PackageModelViewer: ["descriptor"],
  CategoryNav: ["category"],
} as const satisfies Record<string, readonly string[]>;

export type AllowedComponent = keyof typeof ALLOWED_COMPONENT_ATTRIBUTES;

export const ALLOWED_COMPONENTS: readonly string[] = Object.keys(
  ALLOWED_COMPONENT_ATTRIBUTES,
);

/**
 * The pattern every attribute VALUE must match. Evidence text can never reach
 * an attribute: this admits slug paths (slash-separated slug segments, for
 * `CategoryNav`'s nested `category`) and small integers and nothing else.
 */
export const ATTRIBUTE_VALUE_PATTERN = /^[a-z0-9][a-z0-9-]*(?:\/[a-z0-9][a-z0-9-]*)*$/u;

function allowedAttributesFor(name: string): readonly string[] | null {
  return name in ALLOWED_COMPONENT_ATTRIBUTES
    ? ALLOWED_COMPONENT_ATTRIBUTES[name as AllowedComponent]
    : null;
}

// --- builders --------------------------------------------------------------

export function text(value: SafeText): PhrasingContent {
  return { type: "text", value };
}

/**
 * A single separating space. `safeText` trims, so a caller cannot express
 * "space between these two runs" by padding a string — this builder is how
 * inline runs are spaced.
 */
export function space(): PhrasingContent {
  return { type: "text", value: " " };
}

export function code(value: SafeText): PhrasingContent {
  // KiCad active-low names such as ~{SHDN} contain MDX delimiters. The final
  // publication guard deliberately rejects those even in code spans. Preserve
  // the literal label as escaped text instead of weakening that guard.
  return /[<{]/u.test(value) ? { type: "text", value } : { type: "inlineCode", value };
}

export function strong(value: SafeText): PhrasingContent {
  return { type: "strong", children: [{ type: "text", value }] };
}

export function link(url: SafeUrl, label: SafeText): PhrasingContent {
  return { type: "link", url, children: [{ type: "text", value: label }] };
}

declare const routeBrand: unique symbol;

/**
 * An internal destination on this site: a generated route, an in-page
 * fragment, or a route plus fragment.
 *
 * Deliberately NOT a `SafeUrl`. `classifyUrl` exists to decide whether an
 * evidence-supplied absolute URL may be published, and it rejects everything
 * relative — correctly, because a relative URL from evidence would be a path
 * traversal waiting to happen. Internal destinations are the opposite kind of
 * value: this generator composes them from a slug it derived itself, and they
 * must never be reachable from provider data. Giving them their own brand
 * keeps the two apart, so an evidence string can never arrive where a route is
 * expected and vice versa.
 */
export type Route = string & { readonly [routeBrand]: true };

/** `/a/b/` — leading and trailing slash, slug segments only. */
const ROUTE_PATH_PATTERN = /^\/(?:[a-z0-9][a-z0-9-]*\/)+$/u;

/**
 * A site route, optionally targeting one anchor inside it. `fragment` is an
 * `Anchor`, so it has already passed `SLUG_PATTERN` and is a provider ID used
 * verbatim — the same value the matching `<EvidenceAnchor>` carries.
 */
export function route(path: string, fragment?: Anchor): Route {
  if (!ROUTE_PATH_PATTERN.test(path)) {
    fail("UNSAFE_VALUE", `route ${path} is not a permitted internal path`, { path });
  }
  return (fragment === undefined ? path : `${path}#${fragment}`) as Route;
}

/** A destination inside the page being rendered. */
export function fragmentRoute(fragment: Anchor): Route {
  return `#${fragment}` as Route;
}

/** A link to an internal destination. The label may be evidence text. */
export function routeLink(target: Route, label: SafeText): PhrasingContent {
  return { type: "link", url: target, children: [{ type: "text", value: label }] };
}

/** A link whose label is an exact identifier, so it renders as code. */
export function routeCodeLink(target: Route, label: SafeText): PhrasingContent {
  return { type: "link", url: target, children: [{ type: "inlineCode", value: label }] };
}

export function paragraph(children: readonly PhrasingContent[]): RootContent {
  return { type: "paragraph", children: [...children] };
}

export function heading(depth: 2 | 3 | 4, value: SafeText): RootContent {
  return { type: "heading", depth, children: [{ type: "text", value }] };
}

export function bulletList(items: readonly (readonly PhrasingContent[])[]): RootContent {
  return {
    type: "list",
    ordered: false,
    spread: false,
    children: items.map((item) => ({
      type: "listItem" as const,
      spread: false,
      children: [{ type: "paragraph" as const, children: [...item] }],
    })),
  };
}

/** One table row: an array of cells, each of which is inline content. */
export type TableRow = readonly (readonly PhrasingContent[])[];

export function table(header: readonly SafeText[], rows: readonly TableRow[]): RootContent {
  return {
    type: "table",
    children: [
      {
        type: "tableRow",
        children: header.map((value) => ({
          type: "tableCell" as const,
          children: [{ type: "text" as const, value }],
        })),
      },
      ...rows.map((row) => ({
        type: "tableRow" as const,
        children: row.map((cell) => ({
          type: "tableCell" as const,
          children: [...cell],
        })),
      })),
    ],
  };
}

/**
 * The same table, inside its own scroll container.
 *
 * A table wide enough to need this is wide because the evidence is: dropping a
 * column to fit a phone would drop a claim. So every column stays, the
 * container scrolls, and the page body does not. `label` selects the container
 * width in `global.css` and is never shown to a reader — it is a slug, because
 * an attribute value is all evidence text is forbidden to be.
 *
 * Defined here rather than in a renderer so the wrapper and the table it wraps
 * cannot drift apart: there is one way to emit a scrollable table.
 */
export function scrollableTable(
  label: string,
  header: readonly SafeText[],
  rows: readonly TableRow[],
): RootContent {
  return containerComponent("EvidenceTable", { label }, [table(header, rows)]);
}

/**
 * Re-check a component's attributes at build time. The guard checks the same
 * thing again on the final text; this one exists so the failure names the
 * calling renderer instead of a byte offset.
 */
function assertComponentAttributes(
  name: AllowedComponent,
  attributes: Readonly<Record<string, string>>,
): void {
  const allowed = allowedAttributesFor(name);
  if (allowed === null) {
    fail("UNSAFE_MDX", `component ${name} is not on the allow-list`, { name });
  }
  for (const [key, value] of Object.entries(attributes)) {
    if (!allowed.includes(key)) {
      fail("UNSAFE_MDX", `attribute ${key} is not allowed on ${name}`, {
        name,
        attribute: key,
      });
    }
    // The one escape hatch: a `descriptor` is hex-encoded JSON, which the slug
    // pattern would reject on length alone. Hex is a strictly narrower
    // alphabet than the slug pattern's, so this widens the LENGTH, not the
    // character set — and the payload is re-validated as a descriptor by
    // `assertComponentReferencesDescriptor` on both encode and decode.
    const safeValue = name === "ComponentReferences" && key === "descriptor"
      ? /^(?:[0-9a-f]{2})+$/u.test(value) && value.length <= 8192
      : ATTRIBUTE_VALUE_PATTERN.test(value);
    if (!safeValue) {
      fail("UNSAFE_MDX", `attribute ${key} has an unpublishable value`, {
        name,
        attribute: key,
        value,
      });
    }
  }
}

function jsxAttributes(attributes: Readonly<Record<string, string>>) {
  return Object.entries(attributes).map(([key, value]) => ({
    type: "mdxJsxAttribute" as const,
    name: key,
    value,
  }));
}

/** A void JSX element from the whitelist. Attribute values are re-checked here. */
export function component(
  name: AllowedComponent,
  attributes: Readonly<Record<string, string>> = {},
): RootContent {
  assertComponentAttributes(name, attributes);
  // `mdxJsxFlowElement` is an MDX node, not core mdast, so it is not a member
  // of mdast's `RootContent` union; `mdast-util-mdx` is what serialises it.
  return {
    type: "mdxJsxFlowElement",
    name,
    attributes: jsxAttributes(attributes),
    children: [],
  } as unknown as RootContent;
}

/**
 * The same element in an inline position — inside a paragraph or a table cell.
 *
 * A table cell takes phrasing content, so the flow builder above cannot put an
 * anchor next to a fact ID in a row. Without this, evidence rendered as a table
 * could not be deep-linked at all, and the alternative (one heading per fact,
 * 59 of them on the largest record) would bury the page's real structure.
 */
export function inlineComponent(
  name: AllowedComponent,
  attributes: Readonly<Record<string, string>> = {},
): PhrasingContent {
  assertComponentAttributes(name, attributes);
  return {
    type: "mdxJsxTextElement",
    name,
    attributes: jsxAttributes(attributes),
    children: [],
  } as unknown as PhrasingContent;
}

/**
 * A JSX element that wraps generated blocks.
 *
 * The wrapped content is ordinary markdown and stays in the serialized file, so
 * it reaches the built HTML and the search index either way — a container may
 * change how content is presented, never whether it exists.
 */
export function containerComponent(
  name: AllowedComponent,
  attributes: Readonly<Record<string, string>>,
  children: readonly RootContent[],
): RootContent {
  assertComponentAttributes(name, attributes);
  return {
    type: "mdxJsxFlowElement",
    name,
    attributes: jsxAttributes(attributes),
    children: [...children],
  } as unknown as RootContent;
}

/** An anchor target that survives heading-text edits. */
export function evidenceAnchor(id: Anchor): RootContent {
  return component("EvidenceAnchor", { id });
}

/** The same anchor target, for a table cell or a run of inline content. */
export function inlineEvidenceAnchor(id: Anchor): PhrasingContent {
  return inlineComponent("EvidenceAnchor", { id });
}

// --- serialize -------------------------------------------------------------

/**
 * Two constructs the bundled escaping tables do not cover, both only active at
 * the start of a line:
 *
 *   - `:::` opens a remark-directive container. `remark-directive` is a
 *     project dependency and admonitions use it, so evidence text beginning a
 *     line with `:::` would become an admonition. `\:` is a valid CommonMark
 *     backslash escape and renders as a literal colon.
 *   - `import`/`export` as the first token of a line is MDX ESM. Backslash
 *     cannot escape a letter, so `mdast-util-to-markdown` emits a numeric
 *     character reference instead (`&#x69;mport`), which renders as the
 *     original word. The lookahead keeps ordinary words such as "importantly"
 *     untouched.
 */
const PROJECT_UNSAFE = [
  { atBreak: true, character: ":", after: ":" },
  { atBreak: true, character: "i", after: "mport(?:[\\s{*'\"]|$)" },
  { atBreak: true, character: "e", after: "xport(?:[\\s{*'\"]|$)" },
];

export function serializeBody(children: readonly RootContent[]): string {
  const tree: Nodes = { type: "root", children: [...children] };
  return toMarkdown(tree, {
    extensions: [mdxToMarkdown(), gfmTableToMarkdown()],
    unsafe: PROJECT_UNSAFE,
    bullet: "-",
    emphasis: "_",
    strong: "*",
    fence: "`",
    fences: true,
    rule: "-",
    // Always `[text](url)`, never the autolink form `<url>`.
    //
    // The serializer prefers an autolink whenever a link's text equals its URL,
    // which is exactly what a citation looks like — and an autolink opens with
    // a bare `<`, which `assertNoActiveDelimiters` rejects because it cannot
    // tell one from the start of live JSX. Left at `false`, publishing a source
    // link labelled with its own URL fails the build. The two layers have to
    // agree, and they agree here rather than by loosening the guard.
    resourceLink: true,
  });
}

// --- guard -----------------------------------------------------------------

/** Opening/closing tag of a whitelisted component, with only allowed attributes. */
const JSX_TAG =
  /^<\/?(?<name>[A-Z][A-Za-z0-9]*)(?<attrs>(?:\s+[a-zA-Z][a-zA-Z0-9]*="[^"<>]*")*)\s*\/?>/u;
const JSX_ATTR = /([a-zA-Z][a-zA-Z0-9]*)="([^"<>]*)"/gu;

/**
 * Verify final MDX file text. `body` excludes the frontmatter block; the
 * caller passes the frontmatter separately so a `---` inside content is always
 * an error rather than an ambiguous second document boundary.
 */
export function assertMdxSafe(body: string, where: string): void {
  const lines = body.split("\n");

  for (const [index, line] of lines.entries()) {
    const at = { file: where, line: index + 1 };

    if (/^\s{0,3}(?:import|export)\s/u.test(line)) {
      fail("UNSAFE_MDX", `${where}:${index + 1}: line begins an MDX import/export`, at);
    }
    if (/^\s{0,3}:::/u.test(line)) {
      fail("UNSAFE_MDX", `${where}:${index + 1}: line opens a directive`, at);
    }
    if (/^\s{0,3}-{3,}\s*$/u.test(line)) {
      fail("UNSAFE_MDX", `${where}:${index + 1}: line looks like a frontmatter fence`, at);
    }
    // Unlike the `{`/`<` checks below, this one is NOT escape-aware: it refuses
    // `\<!--` as well. That is the settled decision (#64), not an oversight.
    //
    // MDX has no HTML comment syntax — `<!--` is a parse error there rather
    // than a comment — so it has no well-defined inert form the way `\<` does.
    // Accepting the escaped spelling would mean relying on backslash handling
    // staying identical across future remark/MDX majors, and comment handling
    // is precisely where that has moved before. The cost of the strictness is a
    // build that stops with a file, a line and a reason, on a corpus where
    // nothing triggers it; the remedy is an evidence decision by the evidence
    // owner. The alternative failure — a page whose meaning depends on the
    // compiler version — is silent. Relaxing this is a publication decision.
    if (line.includes("<!--")) {
      fail("UNSAFE_MDX", `${where}:${index + 1}: line contains an HTML comment`, at);
    }
  }

  assertNoActiveDelimiters(body, where);
  assertOnlyAllowedJsx(body, where);
}

/**
 * `{` opens an MDX expression and `<` opens JSX/HTML. Either is safe only when
 * backslash-escaped. "Escaped" means preceded by an ODD number of backslashes:
 * `\\<` is an escaped backslash followed by a LIVE `<`.
 */
function assertNoActiveDelimiters(body: string, where: string): void {
  for (let index = 0; index < body.length; index += 1) {
    const character = body[index];
    if (character !== "{" && character !== "<") continue;
    if (isBackslashEscaped(body, index)) continue;
    if (character === "<" && JSX_TAG.test(body.slice(index))) continue;

    fail("UNSAFE_MDX", `${where}: unescaped '${character}' at offset ${index}`, {
      file: where,
      offset: index,
      character,
      context: body.slice(Math.max(0, index - 40), index + 40),
    });
  }
}

function assertOnlyAllowedJsx(body: string, where: string): void {
  for (let index = 0; index < body.length; index += 1) {
    if (body[index] !== "<" || isBackslashEscaped(body, index)) continue;
    const match = JSX_TAG.exec(body.slice(index));
    if (!match?.groups) continue;

    const name = match.groups.name as string;
    const allowed = allowedAttributesFor(name);
    if (allowed === null) {
      fail("UNSAFE_MDX", `${where}: component ${name} is not on the allow-list`, {
        file: where,
        name,
      });
    }
    for (const attribute of (match.groups.attrs ?? "").matchAll(JSX_ATTR)) {
      const [, key = "", value = ""] = attribute;
      if (!allowed.includes(key)) {
        fail("UNSAFE_MDX", `${where}: attribute ${key} is not allowed on ${name}`, {
          file: where,
          name,
          attribute: key,
        });
      }
      if (!ATTRIBUTE_VALUE_PATTERN.test(value)) {
        fail("UNSAFE_MDX", `${where}: attribute ${key} has an unpublishable value`, {
          file: where,
          name,
          attribute: key,
          value,
        });
      }
    }
  }
}

function isBackslashEscaped(body: string, index: number): boolean {
  let backslashes = 0;
  for (let cursor = index - 1; cursor >= 0 && body[cursor] === "\\"; cursor -= 1) {
    backslashes += 1;
  }
  return backslashes % 2 === 1;
}

/** Re-exported so page assembly and the guard agree on one anchor pattern. */
export const ANCHOR_PATTERN = SLUG_PATTERN;
