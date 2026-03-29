import type { Root, Element, ElementContent, Text } from "hast";
import GithubSlugger from "github-slugger";
import { visit } from "unist-util-visit";

/** Recursively extract plain text from a HAST node tree. */
function extractText(node: Element | ElementContent | Text): string {
  if (node.type === "text") return node.value;
  if (node.type === "element") {
    return node.children.map((c) => extractText(c)).join("");
  }
  return "";
}

const headingTags = new Set(["h2", "h3", "h4", "h5", "h6"]);

export function rehypeHeadingLinks() {
  return (tree: Root) => {
    const slugger = new GithubSlugger();

    visit(tree, "element", (node: Element) => {
      if (!headingTags.has(node.tagName)) return;

      const text = node.children
        .map((c) => extractText(c))
        .join("");

      const id =
        (node.properties?.id as string | undefined) || slugger.slug(text);

      if (!node.properties) node.properties = {};
      if (!node.properties.id) node.properties.id = id;

      const link: Element = {
        type: "element",
        tagName: "a",
        properties: {
          href: `#${id}`,
          className: ["hash-link"],
          "aria-label": `Direct link to ${text}`,
        },
        children: [],
      };

      node.children.push(link);
    });
  };
}
