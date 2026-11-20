#!/usr/bin/env node

// Compare rendered historical LED headings with their private namespaced copies.
// C1 fragment-map.tsv records lexical candidates; nested headings get parent
// prefixes at render time, so candidate strings are not an anchor contract.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("../..", import.meta.url)));
const map = await readFile(join(root, "circuit/orchestration/campaigns/pd-led-20261116-c1/route-map.tsv"), "utf8");
const authored = map.trim().split("\n").slice(1).map((line) => line.split("\t"))
  .filter((fields) => fields[4] === "authored");
assert.equal(authored.length, 34, "Authored LED route set changed");

function headingIds(html) {
  return [...html.matchAll(/<h[2-6]\b[^>]*\bid=(?:"([^"]*)"|'([^']*)'|([^\s>]+))[^>]*>/giu)]
    .map((match) => match[1] ?? match[2] ?? match[3]);
}

let headings = 0;
for (const [source, oldRoute, newRoute] of authored) {
  assert(oldRoute.startsWith("/docs/") && newRoute.startsWith("/docs/led-lamp/"), source);
  const oldFile = join(root, "products/led-lamp/doc/dist", oldRoute.slice(1), "index.html");
  const newFile = join(root, "doc/dist", newRoute.slice(1), "index.html");
  const original = headingIds(await readFile(oldFile, "utf8"));
  const candidate = headingIds(await readFile(newFile, "utf8"));
  assert.deepEqual(candidate, original, `${source}: historical heading fragments changed`);
  headings += original.length;
}
assert(headings > 0, "No historical headings were checked");
console.log(`PASS: ${authored.length} authored LED route pairs preserve ${headings} rendered heading fragments`);
