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
