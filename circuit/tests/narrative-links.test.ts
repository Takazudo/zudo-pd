/**
 * Hand-authored sources that link into the generated component tree.
 *
 * `core/links.ts` proves the links the GENERATOR emits. It cannot see the other
 * direction, and there are now two of those:
 *
 *   - the BOM, the decisions log and the ratings matrix cite canonical record
 *     pages and fact anchors, and nothing in the generation pipeline reads them;
 *   - each owner bundle's `SKILL.md` carries a "Human component reference"
 *     section linking its own record pages. That closes the two-way path with
 *     the record pages' own link back to `/docs/claude-skills/<bundle>/`, and
 *     it is read from `.claude/` — a tree this feature otherwise only reads
 *     evidence JSON from.
 *
 * Both directions rot the same way. A record slug is a stable published route,
 * but a record ID rename in the evidence would leave these pointing at a page
 * that no longer exists — silently, since a browser does not report a missing
 * fragment and a 404 on an internal link is nobody's build failure. zfb's own
 * `linkValidation` cannot cover the fragments either: it resolves them against
 * heading-derived anchors only, so every `<EvidenceAnchor>` id is invisible to
 * it (see `core/links.ts`).
 *
 * So the check lives here, on the committed files, and fails the suite rather
 * than warning. Deliberately narrow: it validates `/docs/components/` targets
 * and nothing else, because that tree is the only one this feature owns.
 */

import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { join, relative } from "node:path";
import { describe, it } from "node:test";

import { DOC_ROOT, GENERATED_ROOT } from "./project-context.mjs";

const CONTENT_ROOT = join(DOC_ROOT, "src", "content", "docs");

/** `[label](/docs/components/…)` — the only targets this suite is about. */
const COMPONENT_LINK = /\]\((\/docs\/components\/[^)\s]*)\)/gu;
const EVIDENCE_ANCHOR = /<EvidenceAnchor id="([^"]+)"/gu;

async function mdxFiles(root: string): Promise<string[]> {
  const entries = await readdir(root, { withFileTypes: true });
  const found = await Promise.all(
    entries.map(async (entry) => {
      const path = join(root, entry.name);
      if (entry.isDirectory()) return mdxFiles(path);
      return entry.isFile() && entry.name.endsWith(".mdx") ? [path] : [];
    }),
  );
  return found.flat();
}

/**
 * `<generated root>/records/stusb4500qtr/index.mdx` →
 * `/docs/components/records/stusb4500qtr/`.
 *
 * `GENERATED_ROOT` is `components/`, matching led-lamp — see
 * `core/links.ts` `GENERATED_ROUTE_PREFIX`.
 */
function routeOf(path: string): string {
  const rel = relative(GENERATED_ROOT, path).split("\\").join("/");
  const dir = rel.slice(0, rel.length - "index.mdx".length);
  return `/docs/components/${dir}`;
}

async function anchorsByRoute(): Promise<Map<string, Set<string>>> {
  const pages = await mdxFiles(GENERATED_ROOT);
  const byRoute = new Map<string, Set<string>>();
  for (const path of pages) {
    const contents = await readFile(path, "utf8");
    byRoute.set(
      routeOf(path),
      new Set([...contents.matchAll(EVIDENCE_ANCHOR)].map((match) => match[1] as string)),
    );
  }
  return byRoute;
}

/** Resolve one `/docs/components/…` target; `null` when it lands. */
function unresolved(target: string, byRoute: ReadonlyMap<string, ReadonlySet<string>>): string | null {
  const hash = target.indexOf("#");
  const route = hash === -1 ? target : target.slice(0, hash);
  const fragment = hash === -1 ? null : target.slice(hash + 1);
  const anchors = byRoute.get(route);
  if (anchors === undefined) return "no such generated page";
  if (fragment !== null && !anchors.has(fragment)) return "no such anchor on that page";
  return null;
}

describe("hand-authored pages linking into the generated tree", () => {
  it("resolves every /docs/components/ page and fragment they cite", async () => {
    const byRoute = await anchorsByRoute();
    const authored = (await mdxFiles(CONTENT_ROOT)).filter(
      (path) => !path.startsWith(GENERATED_ROOT),
    );

    const broken: string[] = [];
    let checked = 0;
    for (const path of authored) {
      const contents = await readFile(path, "utf8");
      for (const match of contents.matchAll(COMPONENT_LINK)) {
        const target = match[1] as string;
        checked += 1;
        const reason = unresolved(target, byRoute);
        if (reason !== null) broken.push(`${relative(CONTENT_ROOT, path)} → ${target} (${reason})`);
      }
    }

    assert.deepEqual(broken, []);
    // A guard against the guard: if the narrative links were ever stripped, an
    // empty sweep would pass silently and this suite would prove nothing.
    // zudo-pd's narrative docs do not yet cross-reference the generated
    // tree the way led-lamp's do (no `SKILL.md` "Human component reference"
    // sections point at it either — see the note above); today the only
    // citation is this port's own note on `components/index.mdx`. The floor
    // is set to what actually exists rather than a round number, so it stays
    // a real guard instead of a vacuous one that happens to pass.
    assert.ok(checked >= 1, `expected the narrative pages to cite the component tree, saw ${checked}`);
  });

  // led-lamp's "cites the integration rules from the pages that state their
  // conditioned arithmetic" test, and the whole "owner bundles linking back
  // to their record pages" describe block below it, are CONTENT assertions —
  // they require specific narrative pages (`architecture/decisions.mdx`,
  // `power/ratings-matrix.mdx`) and specific `calc-*`/`rule-*` citations in
  // prose, and require every owner-skill `SKILL.md`'s "## Human component
  // reference" section to already point at the newly-generated
  // `/docs/components/records/<slug>/` pages. Those narrative files
  // do not exist in zudo-pd, and all 20 `SKILL.md` files' reference sections
  // were authored BEFORE this engine existed — they deliberately point at
  // the pre-existing hand-written `/docs/components/<slug>` pages instead
  // ("zudo-pd does not yet generate per-record component pages..."). Neither
  // is a doc-engine porting task; updating the 20 `SKILL.md` files to link
  // the new generated pages is follow-up content work (a natural fit for
  // #126), not part of this port.
});
