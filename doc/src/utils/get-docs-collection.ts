import { getCollection, type CollectionKey } from "astro:content";
import type { DocsEntry } from "@/types/docs-entry";

/**
 * Typed wrapper around getCollection() for docs collections.
 */
export async function getDocsCollection(name: CollectionKey | string): Promise<DocsEntry[]> {
  return await getCollection(name as CollectionKey) as unknown as DocsEntry[];
}
