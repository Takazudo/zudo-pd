import type { CollectionKey } from "astro:content";
import { settings } from "./settings";

/** Default locale code (always "en"). */
export const defaultLocale = "en" as const;

/** All supported locale codes. */
export const locales = [defaultLocale] as const;
export type Locale = (typeof locales)[number];

/** Get the content directory for a locale. */
export function getContentDir(locale: Locale | string): string {
  return settings.docsDir;
}

/** Get the Astro content collection name for a locale. */
export function getCollectionName(locale: Locale | string): CollectionKey {
  return "docs";
}

/** Get the display label for a locale. */
export function getLocaleLabel(locale: Locale | string): string {
  return "EN";
}

/** Detect locale from a URL pathname (after base stripping). */
export function detectLocaleFromPath(_path: string): Locale {
  return defaultLocale;
}

/** UI string translations */
const translations: Record<string, Record<string, string>> = {
  en: {
    "nav.previous": "Previous",
    "nav.next": "Next",
    "toc.title": "On this page",
    "nav.backToMenu": "Back to main menu",
    "doc.editPage": "Edit this page",
  },
};

/** Get a translated UI string */
export function t(key: string, locale: Locale | string = defaultLocale): string {
  return translations[locale]?.[key] ?? translations[defaultLocale]?.[key] ?? key;
}
