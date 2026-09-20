import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { ComponentDocsError } from "../core/errors.ts";
import {
  assertMdxSafe,
  bulletList,
  component,
  code,
  evidenceAnchor,
  heading,
  link,
  paragraph,
  serializeBody,
  table,
  text,
} from "../core/mdx.ts";
import { anchor } from "../core/ids.ts";
import { literal, safeText } from "../core/text.ts";
import { assertSafeUrl } from "../core/url.ts";

/** Serialize one paragraph of provider text and guard it, as a page would. */
function round(raw: string): string {
  const body = serializeBody([
    paragraph([text(safeText(raw, { field: "value", allowNewlines: true }))]),
  ]);
  assertMdxSafe(body, "test.mdx");
  return body;
}

describe("serializeBody escapes MDX-active syntax", () => {
  it("preserves KiCad active-low pin labels without weakening the delimiter guard", () => {
    const body = serializeBody([paragraph([code(literal("~{SHDN}"))])]);
    assertMdxSafe(body, "pin-map.mdx");
    assert.ok(body.includes("\\{SHDN}"));
    assert.deepEqual(code(literal("VIN")), { type: "inlineCode", value: "VIN" });
  });

  it("escapes braces so evidence never becomes an MDX expression", () => {
    const out = round("threshold {vref} volts");
    assert.match(out, /\\\{vref\}/u);
  });

  it("escapes a template-literal-looking value", () => {
    assert.match(round("delay ${t} ms"), /\$\\\{t\}/u);
  });

  it("escapes angle brackets so evidence never becomes JSX or HTML", () => {
    const out = round("VIN < 40 V");
    assert.match(out, /\\</u);
    assert.doesNotMatch(out, /(?<!\\)</u);
  });

  it("escapes a script tag", () => {
    const out = round("<script>alert(1)</script>");
    assert.doesNotMatch(out, /(?<!\\)</u);
  });

  it("escapes emphasis and code markers", () => {
    const out = round("**not bold** and `not code`");
    assert.match(out, /\\\*\\\*not bold/u);
    assert.match(out, /\\`not code\\`/u);
  });

  it("escapes a leading ::: so evidence cannot open a directive", () => {
    const out = round("line one\n:::danger\nline three");
    assert.doesNotMatch(out, /^\s{0,3}:::/mu);
  });

  it("escapes a setext/thematic-break line", () => {
    const out = round("above\n---\nbelow");
    assert.doesNotMatch(out, /^\s{0,3}-{3,}\s*$/mu);
  });

  it("escapes a heading marker", () => {
    assert.doesNotMatch(round("above\n# not a heading"), /^\s{0,3}#/mu);
  });

  it("escapes a pipe inside a table cell", () => {
    const body = serializeBody([
      table(
        [literal("Field"), literal("Value")],
        [[[text(literal("note"))], [text(safeText("a | b", { field: "v" }))]]],
      ),
    ]);
    assertMdxSafe(body, "test.mdx");
    assert.match(body, /a \\\| b/u);
  });

  it("escapes a line-leading import so evidence cannot become MDX ESM", () => {
    const out = round("import a from 'b'");
    assert.match(out, /&#x69;mport a from/u);
    assert.doesNotMatch(out, /^\s{0,3}import\s/mu);
  });

  it("escapes a line-leading export", () => {
    assert.match(round("export const x = 1"), /&#x65;xport const x/u);
  });

  it("leaves ordinary words that merely start with those letters alone", () => {
    assert.match(round("importantly, the rail stays open"), /^importantly, the rail/mu);
    assert.match(round("exports of this part are unrestricted"), /^exports of this part/mu);
  });
});

describe("assertMdxSafe rejects text the serializer did not produce", () => {
  const cases: [string, string][] = [
    ["import", "import x from 'y'\n"],
    ["export", "export const x = 1\n"],
    ["expression", "value is {x}\n"],
    ["jsx", "<div>hi</div>\n"],
    ["html comment", "text <!-- hidden --> text\n"],
    ["directive", ":::danger\nboom\n:::\n"],
    ["frontmatter fence", "text\n---\ntitle: injected\n"],
    ["double-escaped backslash before <", "trailing backslash \\\\<div>\n"],
    ["unlisted component", "<Danger id=\"x\" />\n"],
    ["unlisted attribute", "<EvidenceAnchor onClick=\"x\" />\n"],
    ["attribute belonging to another component", "<EvidenceAnchor category=\"x\" />\n"],
    ["bad attribute value", "<EvidenceAnchor id=\"a b\" />\n"],
  ];

  for (const [name, body] of cases) {
    it(`rejects ${name}`, () => {
      assert.throws(
        () => assertMdxSafe(body, "test.mdx"),
        (error: unknown) =>
          error instanceof ComponentDocsError && error.code === "UNSAFE_MDX",
      );
    });
  }

  it("accepts a whitelisted component", () => {
    assert.doesNotThrow(() => assertMdxSafe('<EvidenceAnchor id="fact-x" />\n', "test.mdx"));
  });
});

describe("component builders", () => {
  it("rejects an unlisted component name", () => {
    assert.throws(
      () => component("Danger" as "EvidenceAnchor"),
      (error: unknown) => error instanceof ComponentDocsError && error.code === "UNSAFE_MDX",
    );
  });

  it("rejects an attribute that belongs to a different component", () => {
    assert.throws(
      () => component("EvidenceAnchor", { category: "components" }),
      (error: unknown) => error instanceof ComponentDocsError && error.code === "UNSAFE_MDX",
    );
  });

  it("rejects an attribute value outside the slug charset", () => {
    assert.throws(
      () => component("EvidenceAnchor", { id: "not a slug" }),
      (error: unknown) => error instanceof ComponentDocsError && error.code === "UNSAFE_MDX",
    );
  });

  it("emits a guard-clean anchor", () => {
    const body = serializeBody([evidenceAnchor(anchor("fact-al8860-vin-absolute-max"))]);
    assertMdxSafe(body, "test.mdx");
    assert.match(body, /<EvidenceAnchor id="fact-al8860-vin-absolute-max"/u);
  });
});

describe("structural builders stay guard-clean", () => {
  it("serializes headings, lists, links and tables", () => {
    const body = serializeBody([
      heading(2, literal("Sources")),
      bulletList([[text(literal("one"))], [text(literal("two"))]]),
      paragraph([
        link(assertSafeUrl("https://example.com/a.pdf", "url"), literal("Datasheet")),
      ]),
      table([literal("A")], [[[text(literal("b"))]]]),
    ]);
    assertMdxSafe(body, "test.mdx");
    assert.match(body, /^## Sources$/mu);
    assert.match(body, /\[Datasheet\]\(https:\/\/example\.com\/a\.pdf\)/u);
  });
});
