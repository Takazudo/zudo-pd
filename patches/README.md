# Circuit-doc 0.3.0 checker bridge

Removal tracker: [zudo-pd #210](https://github.com/Takazudo/zudo-pd/issues/210).
The runtime request is `^0.3.0`. The root lock resolves the npm 0.3.0 tarball with its
registry integrity and this patch's hash. The patch edits one **shipped** module,
`lib/scan/built-references.js`, and nothing else.

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

## Removal

Remove the patch when a released checker accepts the model card's own link on a
document-unavailable record. Then delete the file, drop `patchedDependencies` from
`pnpm-workspace.yaml`, refresh the lock, and update `circuit/tests/runtime.test.mjs` to
assert an unpatched install. Run `pnpm check:site` and `pnpm test:compatibility`.

## Retired 0.1.0 and 5.27.0 patches

The 0.1.0 runtime patch (upstream #103–#109) and the zudo-doc 5.27.0 heading-extractor
patch (zudolab/zudo-doc #4428, project #211) were deleted at this upgrade. Their last
reviewed contents remain in Git history. The released packages passed the retained
regressions that each one was kept for; `ZUDO_DEPS_PINS.md` lists them.
