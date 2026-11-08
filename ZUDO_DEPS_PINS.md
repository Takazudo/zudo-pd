# Zudo dependency pins

| Path | Source | Full commit / version | Date | Track | Sync | Reason |
|---|---|---|---|---|---|---|
| Scaffold-derived paths | Takazudo/zudo-circuit-doc create-zudo-circuit-doc@0.2.1 | 388fca9da838ffb6c10a83ef3fac4a0c006542b0 | 2026-11-08 | releases | run the initializer into a separate scratch directory, diff and merge per doc/SCAFFOLD.md | Reviewed host integration |
| doc host scaffold | zudolab/zudo-doc packages/create-zudo-doc/templates/base | 054c1dabb5810afa24485a5431bce094b14fae21 (create-zudo-doc@9.1.4 npm gitHead) | 2026-11-08 | releases | external scaffold diff; preserve project bindings | SSR, routes, CSS, history |
| root/doc manifests and root lock | @takazudo/zudo-circuit-doc registry | 0.3.0 (^0.3.0), tag v0.3.0 = ff278409c693be0efe43f043f0e40d2c56af1e47 | 2026-11-08 | releases | update both consumers together; root lock records the registry integrity | Evidence/publication parity |
| root/doc manifests and root lock | @takazudo/zfb, runtime, md-wasm, adapter-cloudflare registry | 5.2.2 | 2026-11-08 | releases | align family together, frozen root install, guarded integration build | Cloudflare host and island support |
| root/doc manifests and root lock | @takazudo/zudo-doc, history-server registry | 9.1.4 | 2026-11-08 | releases | align together; verify sumi/history | Host chrome |
| patches/@takazudo__zudo-circuit-doc@0.3.0.patch | Project #210; upstream report pending | Reviewed project bridge over the 0.3.0 tarball | 2026-11-08 | project bridge | Remove when a released checker accepts a document-unavailable record's own model link | One `scan/built-references.js` branch |

Registry versions are exact pins except the requested runtime caret. Node is `>=24 <25`;
Python stays 3.12; pnpm stays 11.5.2. Registry-only dependencies have no vendored file copy;
source commits are recorded where the scaffold supplies them. See doc/SCAFFOLD.md for every
copied/derived path. Never change the KiCad renderer pin while updating host dependencies
without separate byte/hash review.

## Retired bridges

The 0.1.0 circuit-runtime patch (upstream #103–#109) and the `@takazudo/zudo-doc@5.27.0`
heading-extractor patch (zudolab/zudo-doc #4428, project #211) were deleted with this upgrade.
The released 0.3.0 and 9.1.4 packages passed the retained regressions that each patch was
kept for: placement fit, candidates, finite MPN exceptions, document availability,
deny/scan/hash parity, the foreground browser launcher, long-identity viewer CSS and the
built-heading parity fixtures. The enlarged-image alt bridge (#110) stays removed.

## 0.3.0 checker bridge

`zudo-circuit-doc check-built` 0.3.0 rejects any link inside the Component references section
of a document-unavailable record other than the footprint SVG. Its own model card renders an
"Open model file" link, so record c335982 (document unavailable, WRL declared) fails the
released checker. The bridge also allows that section's own declared `data-model-url` WRL;
every other destination, including another WRL or any document URL, still fails. See
`patches/README.md` and https://github.com/Takazudo/zudo-pd/issues/210.
