type MiddlewareContext = {
  request: { url: string };
  redirect: (url: string, status?: 300 | 301 | 302 | 303 | 304 | 307 | 308) => Response;
};

type MiddlewareNext = () => Response | Promise<Response>;

/**
 * When trailingSlash is enabled, redirect URLs without trailing slash
 * to the trailing-slash version via 301 redirect.
 *
 * Astro's dev server does not auto-redirect even with trailingSlash: "always",
 * so this middleware provides that behavior.
 */
export function trailingSlashHandler(
  context: MiddlewareContext,
  next: MiddlewareNext,
  trailingSlash: boolean,
): Response | Promise<Response> {
  if (!trailingSlash) {
    return next();
  }

  const url = new URL(context.request.url);
  const pathname = url.pathname;

  if (pathname.endsWith("/")) {
    return next();
  }

  // Skip Astro internal paths
  if (pathname.startsWith("/_astro/") || pathname.startsWith("/_image")) {
    return next();
  }

  // Skip paths with file extensions (static assets)
  const lastSegment = pathname.split("/").pop() || "";
  if (/\.[a-zA-Z]\w*$/.test(lastSegment)) {
    return next();
  }

  const redirectUrl = pathname + "/" + url.search;
  return context.redirect(redirectUrl, 301);
}
