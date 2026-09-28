import assert from "node:assert/strict";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { after, before, describe, it } from "node:test";

import {
  checkFragmentLinks,
  collectIds,
  findMarkdownLinks,
  maskNonProse,
  resolveDestination,
  routeForBuiltFile,
  routeForSourceFile,
} from "../scripts/check-built-fragment-links.mjs";

let fixtureRoot: string;

before(async () => {
  fixtureRoot = await mkdtemp(join(tmpdir(), "zpd-fragment-links-"));
});

after(async () => {
  await rm(fixtureRoot, { recursive: true, force: true });
});

async function write(root: string, relativePath: string, contents: string): Promise<void> {
  const target = join(root, relativePath);
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, contents, "utf8");
}

describe("ids read off the built HTML", () => {
  it("reads every attribute form and decodes entities", () => {
    const ids = collectIds(
      `<h2 id="protection-stage">a</h2>` +
        `<h3 id='protection-stage-ptc1'>b</h3>` +
        `<span id=fact-c17513-resistance>c</span>` +
        `<a id="r&amp;d">d</a>`,
    );
    assert.deepEqual(
      [...ids].sort(),
      ["fact-c17513-resistance", "protection-stage", "protection-stage-ptc1", "r&d"],
    );
  });

  it("ignores ids inside script and style bodies", () => {
    // A template string in a bundle is not a rendered element. Counting it
    // would let the gate accept an anchor no reader can reach.
    const ids = collectIds(
      `<h2 id="real">a</h2>` +
        `<script>const t = '<div id="from-a-bundle"></div>';</script>` +
        `<style>#styled { color: red }</style>` +
        `<style type="text/css">div[id="also-not-real"] {}</style>`,
    );
    assert.deepEqual([...ids], ["real"]);
  });

  it("keeps the unicode zfb's hierarchical slugger preserves", () => {
    const ids = collectIds(`<h3 id="diagram5-13-5v-→-12v-linear-regulator-l7812-u6">x</h3>`);
    assert.ok(ids.has("diagram5-13-5v-→-12v-linear-regulator-l7812-u6"));
  });
});

describe("routes", () => {
  it("maps a built file onto the trailing-slash-free route the corpus links by", () => {
    assert.equal(routeForBuiltFile("docs/overview/bom/index.html"), "/docs/overview/bom");
    assert.equal(routeForBuiltFile("docs/overview/index.html"), "/docs/overview");
    assert.equal(routeForBuiltFile("index.html"), "/");
    assert.equal(routeForBuiltFile("404.html"), "/404");
  });

  it("maps a source file onto the same route space", () => {
    assert.equal(routeForSourceFile("overview/bom.md"), "/docs/overview/bom");
    assert.equal(routeForSourceFile("overview/circuit-diagrams.mdx"), "/docs/overview/circuit-diagrams");
    assert.equal(routeForSourceFile("overview/index.mdx"), "/docs/overview");
    assert.equal(routeForSourceFile("components/records/c17513/index.mdx"), "/docs/components/records/c17513");
    assert.equal(routeForSourceFile("index.md"), "/docs");
  });
});

describe("what counts as a link", () => {
  it("blanks fenced code, inline code and comments without moving any line", () => {
    const source = [
      "before",
      "```md",
      "[x](./gone.md#nope)",
      "```",
      "`[y](./gone.md#nope)`",
      "<!-- [z](./gone.md#nope) -->",
      "after",
    ].join("\n");
    const masked = maskNonProse(source);
    assert.equal(masked.split("\n").length, source.split("\n").length);
    assert.equal(masked.length, source.length);
    assert.doesNotMatch(masked, /gone\.md/u);
    assert.match(masked, /before/u);
    assert.match(masked, /after/u);
    assert.deepEqual(findMarkdownLinks(source), []);
  });

  it("closes a fence only on a fence of the same character and length", () => {
    const source = ["````md", "```", "[x](./gone.md#nope)", "````", "[y](./real.md#ok)"].join("\n");
    assert.deepEqual(
      findMarkdownLinks(source).map((link) => link.destination),
      ["./real.md#ok"],
    );
  });

  it("reads angle-bracketed destinations, titles and balanced parens, and reports the line", () => {
    const source = [
      "one [a](./x.md#one)",
      'two [b](./y.md#two "a title")',
      "three [c](<./z.md#three>)",
      "four [d](./w.md#a(b)c)",
    ].join("\n");
    assert.deepEqual(
      findMarkdownLinks(source).map((link) => [link.destination, link.line]),
      [
        ["./x.md#one", 1],
        ["./y.md#two", 2],
        ["./z.md#three", 3],
        ["./w.md#a(b)c", 4],
      ],
    );
  });

  it("keeps offsets aligned when an astral character precedes the link", () => {
    // The masking pass indexes by UTF-16 unit. Iterating by code point instead
    // would collapse this emoji into one slot and shift every later offset,
    // silently blanking the wrong span.
    const source = ["🔧 a fence follows", "```", "[x](./gone.md#nope)", "```", "[y](./real.md#ok)"].join("\n");
    const masked = maskNonProse(source);
    assert.equal(masked.length, source.length);
    assert.doesNotMatch(masked, /gone\.md/u);
    assert.deepEqual(
      findMarkdownLinks(source).map((link) => [link.destination, link.line]),
      [["./real.md#ok", 5]],
    );
  });

  it("tells an image apart from a link", () => {
    const links = findMarkdownLinks("![alt](/circuits/x.svg#frag) and [label](./y.md#frag)");
    assert.deepEqual(
      links.map((link) => [link.destination, link.isImage]),
      [
        ["/circuits/x.svg#frag", true],
        ["./y.md#frag", false],
      ],
    );
  });
});

describe("which destinations this gate owns", () => {
  const from = "overview/bom.md";

  it("resolves same-page, relative and root-absolute docs destinations", () => {
    assert.deepEqual(resolveDestination(from, "#protection-stage"), {
      route: "/docs/overview/bom",
      fragment: "protection-stage",
    });
    assert.deepEqual(resolveDestination(from, "./board-b-synth-power.md#protection-stage"), {
      route: "/docs/overview/board-b-synth-power",
      fragment: "protection-stage",
    });
    assert.deepEqual(resolveDestination(from, "../learning/index.mdx#x"), {
      route: "/docs/learning",
      fragment: "x",
    });
    assert.deepEqual(resolveDestination(from, "/docs/components/integration/#rule-rail-envelope"), {
      route: "/docs/components/integration",
      fragment: "rule-rail-envelope",
    });
  });

  it("drops a query string rather than folding it into the route", () => {
    assert.deepEqual(resolveDestination(from, "/docs/overview/bom?v=2#protection-stage"), {
      route: "/docs/overview/bom",
      fragment: "protection-stage",
    });
  });

  it("percent-decodes a fragment before comparing it to a raw id", () => {
    // Editors and browsers escape the unicode zfb keeps in the id verbatim.
    assert.deepEqual(resolveDestination(from, "./circuit-diagrams.mdx#diagram5-13-5v-%E2%86%92-12v"), {
      route: "/docs/overview/circuit-diagrams",
      fragment: "diagram5-13-5v-→-12v",
    });
  });

  it("declines destinations whose anchors dist/ cannot speak for", () => {
    for (const destination of [
      "https://example.com/page#frag",
      "//example.com/page#frag",
      "mailto:someone@example.com#frag",
      "/datasheets/stusb4500.pdf#page=12",
      "./diagram.svg#layer",
      "./sibling.md",
    ]) {
      assert.equal(resolveDestination(from, destination), null, destination);
    }
  });

  it("flags a relative destination that climbs out of the docs root", () => {
    const resolved = resolveDestination("overview/bom.md", "../../../secrets.md#x");
    assert.equal(resolved?.route, null);
  });
});

describe("the gate, end to end", () => {
  // The exact shape that shipped 18 dead anchors: hierarchical heading ids,
  // unicode kept, `13.5` -> `13-5`, and non-heading EvidenceAnchor ids.
  async function fixture(name: string, sources: Record<string, string>) {
    const root = join(fixtureRoot, name);
    const docsRoot = join(root, "docs");
    const distRoot = join(root, "dist");

    for (const [path, contents] of Object.entries(sources)) {
      await write(docsRoot, path, contents);
    }

    await write(
      distRoot,
      "docs/overview/board-b-synth-power/index.html",
      `<h2 id="protection-stage">Protection Stage</h2>` +
        `<h3 id="protection-stage-ptc1-and-the-l7812-current-limit-cascade">PTC1</h3>`,
    );
    await write(
      distRoot,
      "docs/overview/circuit-diagrams/index.html",
      `<h2 id="diagram5-13-5v-→-12v-linear-regulator-l7812-u6">Diagram 5</h2>`,
    );
    await write(
      distRoot,
      "docs/components/records/c17513/index.html",
      `<span id="fact-c17513-resistance"></span>`,
    );
    await write(distRoot, "docs/overview/index.html", `<h2 id="on-the-index">Index</h2>`);

    return { docsRoot, distRoot };
  }

  it("passes links that name the id the build actually emitted", async () => {
    const roots = await fixture("good", {
      "overview/index.mdx": [
        "[a](./board-b-synth-power.md#protection-stage)",
        "[b](./board-b-synth-power.md#protection-stage-ptc1-and-the-l7812-current-limit-cascade)",
        "[c](./circuit-diagrams.mdx#diagram5-13-5v-%E2%86%92-12v-linear-regulator-l7812-u6)",
        "[d](/docs/components/records/c17513/#fact-c17513-resistance)",
        "[e](#on-the-index)",
        "[f](https://example.com/x#whatever)",
      ].join("\n\n"),
    });

    const result = await checkFragmentLinks(roots);
    assert.deepEqual(result.failures, []);
    assert.equal(result.checked, 5);
  });

  it("fails the bare slug where the id is hierarchical, and says which file", async () => {
    const roots = await fixture("bare-slug", {
      "overview/index.mdx": "see [PTC1](./board-b-synth-power.md#ptc1-and-the-l7812-current-limit-cascade)",
    });

    const result = await checkFragmentLinks(roots);
    assert.equal(result.failures.length, 1);
    assert.equal(result.failures[0].reason, "NO_ANCHOR");
    assert.equal(result.failures[0].where, "overview/index.mdx:1");
    assert.match(result.failures[0].detail, /ptc1-and-the-l7812-current-limit-cascade$/u);
  });

  it("fails an anchor that dropped the unicode or flattened the decimal", async () => {
    const roots = await fixture("mangled", {
      "overview/index.mdx": [
        "[a](./circuit-diagrams.mdx#diagram5-13-5v-12v-linear-regulator-l7812-u6)",
        "[b](./circuit-diagrams.mdx#diagram5-135v-→-12v-linear-regulator-l7812-u6)",
      ].join("\n\n"),
    });

    const result = await checkFragmentLinks(roots);
    assert.equal(result.failures.length, 2);
    assert.ok(result.failures.every((failure: { reason: string }) => failure.reason === "NO_ANCHOR"));
  });

  it("fails a fragment on a page the build never produced", async () => {
    const roots = await fixture("no-page", {
      "overview/index.mdx": "[a](./ghost.md#anything)",
    });

    const result = await checkFragmentLinks(roots);
    assert.equal(result.failures.length, 1);
    assert.equal(result.failures[0].reason, "NO_PAGE");
    assert.equal(result.failures[0].detail, "/docs/overview/ghost");
  });
});
