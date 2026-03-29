import type { Root, Node as MdastNode } from "mdast";
import { visit, SKIP } from "unist-util-visit";

interface ContainerDirective extends MdastNode {
  type: "containerDirective";
  name: string;
  children: DirectiveChild[];
  data?: Record<string, unknown>;
  attributes?: MdxJsxAttribute[];
}

interface DirectiveChild {
  type: string;
  value?: string;
  children?: DirectiveChild[];
  data?: { directiveLabel?: boolean; [key: string]: unknown };
}

interface MdxJsxAttribute {
  type: "mdxJsxAttribute";
  name: string;
  value: string;
}

const ADMONITION_TYPES = new Set(["note", "tip", "info", "warning", "danger"]);

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function extractText(node: DirectiveChild): string {
  if (typeof node.value === "string") return node.value;
  if (Array.isArray(node.children)) {
    return node.children.map(extractText).join("");
  }
  return "";
}

export function remarkAdmonitions() {
  return (tree: Root) => {
    visit(tree, (node: MdastNode) => {
      if (
        node.type === "containerDirective" &&
        "name" in node &&
        ADMONITION_TYPES.has((node as ContainerDirective).name)
      ) {
        const directive = node as ContainerDirective;
        const componentName = capitalize(directive.name);

        const label = directive.children?.[0];
        const isLabel = label?.data?.directiveLabel === true;
        const title = isLabel ? extractText(label) : "";

        const attributes: MdxJsxAttribute[] = [];
        if (title) {
          attributes.push({
            type: "mdxJsxAttribute",
            name: "title",
            value: title,
          });
        }

        (directive as unknown as Record<string, unknown>).type = "mdxJsxFlowElement";
        (directive as unknown as Record<string, unknown>).name = componentName;
        directive.attributes = attributes;
        delete directive.data;

        if (isLabel) {
          directive.children = directive.children.slice(1);
        }

        return SKIP;
      }
    });
  };
}
