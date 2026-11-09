# Circuit-doc 0.3.0 checker and Mac browser bridges

Removal tracker: [zudo-pd #210](https://github.com/Takazudo/zudo-pd/issues/210).
The runtime request is `^0.3.0`. The root lock resolves the npm 0.3.0 tarball with its
registry integrity and this patch's hash. The patch retains the reviewed `lib/scan/built-references.js` checker branch and
adds only active-page setup in `lib/browser-smoke/chrome.js` and its visibility
precondition in `lib/browser-smoke/cdp.js`. Dependency versions are unchanged.

## Why it exists

`checkRecordPage` in 0.3.0 handles a record whose selected document is unavailable by
requiring every `<a>` in the Component references section to point at the footprint SVG.
The same release's model card renders an "Open model file" link to the record's declared
WRL. A document-unavailable record that also has a model therefore always fails
`check-built`. In this corpus that is c335982: its only source is an LCSC listing (the
reviewed document exception), and its footprint declares a WRL.

The bridge extends the allowed set by exactly the section's own `data-model-url` values that
match the package's model-asset pattern. The later model checks in the same function still
require exactly one declared model with a safe path. A link to any other WRL, a document URL,
or a site route still fails. `circuit/tests/compatibility.test.mjs` covers both directions.

## Mac active-page lifecycle (2026-11-09)

The official package checker on source revision `336a2c1` failed its footprint
backdrop-close assertion on Mac Chrome: the native dialog was closed but its
image remained, and the second native `close` event was not delivered while
`document.visibilityState` was `hidden`. `Page.bringToFront` and existing
background-throttling flags did not establish an active page.

An isolated diagnostic importing the installed package launcher and dialog check
reproduced that failure. Adding CDP `Emulation.setFocusEmulationEnabled` alone made
the page visible and all Escape/backdrop/button close events and cleanup
assertions pass. The bridge applies that setup and explicitly rejects hidden
pages after navigation. It changes no product dialog, cleanup assertion, timeout,
representative, or dependency pin. Focused installed-code tests cover protocol
failure teardown and rejection of a hidden page. The official package CLI and
full project browser remain required acceptance checks; the diagnostic is not a
substitute. See [Chrome's active-page emulation API](https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setFocusEmulationEnabled).

## Removal

Remove each bridge only when a released package passes its retained regression.
The checker must accept the unavailable-document record's own model link, and the
Mac browser launcher must establish an active page without weakening cleanup checks.
Keep #210 open while either bridge remains. When both are retired, delete the file, drop `patchedDependencies` from
`pnpm-workspace.yaml`, refresh the lock, and update `circuit/tests/runtime.test.mjs` to
assert an unpatched install. Run `pnpm check:site` and `pnpm test:compatibility`.

## Retired 0.1.0 and 5.27.0 patches

The 0.1.0 runtime patch (upstream #103–#109) and the zudo-doc 5.27.0 heading-extractor
patch (zudolab/zudo-doc #4428, project #211) were deleted at this upgrade. Their last
reviewed contents remain in Git history. The released packages passed the retained
regressions that each one was kept for; `ZUDO_DEPS_PINS.md` lists them.
