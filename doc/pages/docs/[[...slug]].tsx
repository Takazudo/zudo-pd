/** @jsxRuntime automatic */
/** @jsxImportSource preact */
// Package-shaped host route: retain DocHistory's explicit host binding and seed
// the package preview islands through the static route import graph.

import type { JSX } from "preact";
import { routeContext } from "virtual:zudo-doc-route-context";
import {
  createRouteContext,
  type RouteContextPayload,
} from "@takazudo/zudo-doc/route-context";
import { createChrome } from "@takazudo/zudo-doc/chrome";
import { DocHistory } from "@takazudo/zudo-doc/doc-history";
import { defineChromeBindings } from "@takazudo/zudo-doc/chrome-bindings";
import type {
  DocPageEntryProps,
  DocPageAutoIndexProps,
} from "@takazudo/zudo-doc/doc-page-props";
import { chromeBindings } from "virtual:zudo-doc-chrome-bindings";
import "../lib/_circuit-doc-islands.ts";

const ctx = routeContext as unknown as RouteContextPayload;
const routeCtx = createRouteContext(ctx);
const { renderDocPage } = createChrome(routeCtx, {
  ...chromeBindings,
  ...defineChromeBindings({ DocHistory }),
});

export const frontmatter = { title: "Docs" };

type DocPageProps = DocPageEntryProps | DocPageAutoIndexProps;

export function paths(): Array<{ params: { slug: string[] }; props: DocPageProps }> {
  const locale = routeCtx.defaultLocale;
  const source = routeCtx.resolveNavSource(locale, undefined);
  return routeCtx.buildDocRouteEntries({
    source,
    locale,
    routeSig: `docs;${locale}`,
  }).map((item) => ({
    params: { slug: item.slugParams },
    props: item.props as DocPageProps,
  }));
}

type PageArgs = DocPageProps & { params: { slug: string[] } };

export default function DocsPage(props: PageArgs): JSX.Element {
  return renderDocPage(props, {
    locale: routeCtx.defaultLocale,
    docHistoryContentDir: routeCtx.settings.docsDir,
  });
}
