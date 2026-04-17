import type { Root, Element, ElementContent, Text } from "hast";
import { visit } from "unist-util-visit";

/** Recursively extract plain text from a HAST node tree. */
function extractText(node: Element | ElementContent | Text): string {
  if (node.type === "text") return node.value;
  if (node.type === "element") {
    return node.children.map((c) => extractText(c)).join("");
  }
  return "";
}

/**
 * Rehype plugin that transforms mermaid code blocks into renderable containers.
 */
export function rehypeMermaid() {
  return (tree: Root) => {
    visit(tree, "element", (node: Element, index, parent) => {
      if (
        node.tagName !== "pre" ||
        !parent ||
        index === undefined
      ) return;

      if (node.properties?.dataLanguage !== "mermaid") return;

      const text = node.children
        .map((c) => extractText(c))
        .join("");

      (parent as Element).children[index] = {
        type: "element",
        tagName: "div",
        properties: { className: ["mermaid"], "data-mermaid": true },
        children: [{ type: "text", value: text }],
      };
    });
  };
}
