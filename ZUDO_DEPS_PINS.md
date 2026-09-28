# Zudo dependency pins

| Path | Source | Full commit / version | Date | Track | Sync | Reason |
|---|---|---|---|---|---|---|
| Scaffold-derived paths | Takazudo/zudo-circuit-doc create-zudo-circuit-doc@0.1.0 | 5d0e2b630776489d394be341586b889dfe0d1cb8 | 2026-09-29 | releases | external initializer, diff/merge per doc/SCAFFOLD.md | Reviewed host integration |
| doc host scaffold | zudolab/zudo-doc packages/create-zudo-doc/templates/default/app | 50cbd5c6c9e5a795d72a74a855e105e4939d4eab (5.27.0) | 2026-09-29 | releases | external scaffold diff; preserve project bindings | SSR, routes, CSS, history |
| root/doc manifests and root lock | @takazudo/zudo-circuit-doc registry | 0.1.0 (^0.1.0), source 5d0e2b630776489d394be341586b889dfe0d1cb8 | 2026-09-29 | releases | update both consumers and retain #210 bridge until tested release | Evidence/publication parity |
| root/doc manifests and root lock | @takazudo/zfb, runtime, md-wasm, adapter-cloudflare registry | 2.21.0 | 2026-09-29 | releases | align family together, frozen root install, guarded integration build | Cloudflare host and island support |
| root/doc manifests and root lock | @takazudo/zudo-doc, history-server registry | 5.27.0 | 2026-09-29 | releases | align together; verify sumi/history | Host chrome |
| patches/@takazudo__zudo-circuit-doc@0.1.0.patch | Project #205, #210; upstream #103–107 | Reviewed project bridge over source 5d0e2b630776489d394be341586b889dfe0d1cb8 | 2026-09-29 | project bridge | Follow #210 removal procedure, compare real tarball behavior | DNP, candidates, finite MPN exceptions, availability, deny/scan/hash parity |

Registry versions are exact pins except the requested runtime caret; the root lock fixes its
patched 0.1.0 resolution. Registry-only dependencies have no vendored file copy; source commits
are recorded where the scaffold supplies them. See doc/SCAFFOLD.md for every copied/derived
path, deliberate sitemap disablement and initializer README #102 correction. Never change
the KiCad renderer pin while updating host dependencies without separate byte/hash review.

Additional runtime bridge source: https://github.com/Takazudo/zudo-circuit-doc/issues/108
(headless foreground launcher restoration); still tracked under project #210.

| Path | Source | Full commit / version | Date | Track | Sync | Reason |
|---|---|---|---|---|---|---|
| patches/@takazudo__zudo-doc@5.27.0.patch; root workspace/lock | zudolab/zudo-doc registry, shipped dist/extract-headings/index.js | 5.27.0; source pin 50cbd5c6c9e5a795d72a74a855e105e4939d4eab | 2026-09-29 | temporary project bridge | Inspect released native-heading parity; remove only after #211 checks | Complete protected entity decoding and correct code fences; upstream #4428 |

Both root/doc consumers resolve this same patched SDK. This bridge is independent of runtime
#210; see https://github.com/Takazudo/zudo-pd/issues/211 and
https://github.com/zudolab/zudo-doc/issues/4428 for release prerequisites. All exported
synchronous helper signatures and declarations are unchanged.

Additional runtime CSS bridge source: https://github.com/Takazudo/zudo-circuit-doc/issues/109
(long package-caption intrinsic sizing). The controlled live-CSS experiment preserves full
identity while containing the model at375px; remove only when published CSS and unchanged
48-case browser assertions pass per runtime tracker #210.

Footprint modal accessibility correction:
https://github.com/Takazudo/zudo-circuit-doc/issues/110 records intentional SDK design.
The temporary enlarged-image alt bridge was removed. The named modal supplies the exact
inline image description, and its child image stays decorative. The project browser and
installed-island contracts now verify that complete identity and no removed-title reference.
There is no #110 patch hunk or removal prerequisite under runtime tracker #210.
