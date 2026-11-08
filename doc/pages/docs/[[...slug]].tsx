// Package-shaped host route from create-zudo-doc 9.1.4: retain DocHistory's
// explicit host binding and seed the package preview islands through the
// static route import graph.

import type { JSX } from "@takazudo/zfb/zudo-react/jsx-runtime";
import { routeContext } from "virtual:zudo-doc-route-context";
import {
  createRouteContext,
  type RouteContextPayload,
} from "@takazudo/zudo-doc/route-context";
import { createChrome } from "@takazudo/zudo-doc/chrome";
import { DocHistoryBoundary as DocHistory } from "@takazudo/zudo-doc/doc-history-area";
import { defineChromeBindings } from "@takazudo/zudo-doc/chrome-bindings";
import { chromeBindings } from "virtual:zudo-doc-chrome-bindings";
import "../lib/_circuit-doc-islands";

const ctx = routeContext as unknown as RouteContextPayload;
const routeCtx = createRouteContext(ctx);
const { renderDocPage } = createChrome(routeCtx, {
  ...chromeBindings,
  ...defineChromeBindings({ DocHistory }),
});

export const frontmatter = { title: "Docs" };

export function paths(): Array<{ params: { slug: string[] }; props: unknown }> {
  const locale = routeCtx.defaultLocale;
  const source = routeCtx.resolveNavSource(locale, undefined);
  return routeCtx.buildDocRouteEntries({
    source,
    locale,
    routeSig: `docs;${locale}`,
  }).map((item) => ({
    params: { slug: item.slugParams },
    props: item.props,
  }));
}

type PageArgs = { params: { slug: string[] } } & Record<string, unknown>;

export default function DocsPage(props: PageArgs): JSX.Element {
  return renderDocPage(props as never, {
    locale: routeCtx.defaultLocale,
    docHistoryContentDir: routeCtx.settings.docsDir,
  });
}
