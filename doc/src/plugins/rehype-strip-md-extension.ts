import type { Root, Element } from 'hast';
import { visit } from 'unist-util-visit';

/**
 * Rehype plugin that strips .md and .mdx extensions from relative link hrefs.
 */
export function rehypeStripMdExtension() {
  return (tree: Root) => {
    visit(tree, 'element', (node: Element) => {
      if (node.tagName !== 'a') return;
      const href = node.properties?.href;
      if (typeof href !== 'string') return;

      if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith('#')) return;

      const replaced = href.replace(
        /\.mdx?(#.*)?$/,
        (_match, hash) => hash ?? '',
      );
      if (replaced !== href) {
        node.properties.href = replaced;
      }
    });
  };
}
