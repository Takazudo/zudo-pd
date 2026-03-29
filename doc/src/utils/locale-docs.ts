import type { DocsEntry } from "@/types/docs-entry";
import type { CategoryMeta } from "@/utils/docs";
import { loadCategoryMeta } from "@/utils/docs";
import { getDocsCollection } from "@/utils/get-docs-collection";
import { settings } from "@/config/settings";

export interface LocaleDocsResult {
  allDocs: DocsEntry[];
  fallbackSlugs: Set<string>;
  categoryMeta: Map<string, CategoryMeta>;
}

/** Filter drafts in production builds. */
const filterDrafts = (docs: DocsEntry[]) =>
  import.meta.env.PROD ? docs.filter((doc) => !doc.data.draft) : docs;

const cache = new Map<string, Promise<LocaleDocsResult>>();

export function loadLocaleDocs(lang: string): Promise<LocaleDocsResult> {
  const cached = cache.get(lang);
  if (cached) return cached;
  const promise = loadLocaleDocsImpl();
  cache.set(lang, promise);
  return promise;
}

async function loadLocaleDocsImpl(): Promise<LocaleDocsResult> {
  const docs = filterDrafts(await getDocsCollection("docs"));
  const categoryMeta = loadCategoryMeta(settings.docsDir);
  return { allDocs: docs, fallbackSlugs: new Set<string>(), categoryMeta };
}
