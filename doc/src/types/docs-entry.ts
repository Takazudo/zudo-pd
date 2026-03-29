import type { RenderedContent } from "astro:content";

export interface DocsEntry {
  id: string;
  body?: string;
  collection: string;
  data: {
    title: string;
    description?: string;
    category?: string;
    sidebar_position?: number;
    sidebar_label?: string;
    search_exclude?: boolean;
    pagination_next?: string | null;
    pagination_prev?: string | null;
    draft?: boolean;
    unlisted?: boolean;
    hide_sidebar?: boolean;
    hide_toc?: boolean;
    standalone?: boolean;
    slug?: string;
  };
  rendered?: RenderedContent;
  filePath?: string;
}
