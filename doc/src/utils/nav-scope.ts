import { settings } from "@/config/settings";
import type { NavNode } from "@/utils/docs";

/**
 * Given a doc's slug, return the categoryMatch value of the headerNav item it belongs to.
 */
export function getNavSectionForSlug(slug: string): string | undefined {
  const topCategory = slug.split("/")[0] ?? "";

  const explicitMatches = settings.headerNav.filter(
    (item) =>
      item.categoryMatch &&
      item.categoryMatch !== "!" &&
      topCategory.startsWith(item.categoryMatch),
  );
  if (explicitMatches.length > 0) {
    const best = explicitMatches.sort(
      (a, b) => (b.categoryMatch?.length ?? 0) - (a.categoryMatch?.length ?? 0),
    )[0];
    return best.categoryMatch;
  }

  const defaultItem = settings.headerNav.find(
    (item) => item.categoryMatch === "!",
  );
  return defaultItem?.categoryMatch;
}

/**
 * Filter top-level NavNodes by a headerNav categoryMatch value.
 */
export function getNavSubtree(
  tree: NavNode[],
  categoryMatch?: string,
): NavNode[] {
  if (!categoryMatch) return tree;

  if (categoryMatch === "!") {
    const explicitPrefixes = settings.headerNav
      .filter((item) => item.categoryMatch && item.categoryMatch !== "!")
      .map((item) => item.categoryMatch!);
    return tree.filter(
      (node) => !explicitPrefixes.some((prefix) => node.slug.startsWith(prefix)),
    );
  }

  return tree.filter((node) => node.slug.startsWith(categoryMatch));
}
