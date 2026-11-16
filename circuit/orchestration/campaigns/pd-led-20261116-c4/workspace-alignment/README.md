# C4h nested pnpm alignment and application verification

This is a bounded follow-up to independently reviewed C4g head
`7aae74a25bb09c9f49040263cb982749708c8990`. The manager reported that
C4g's six focused tests and 26 of 26 bound-file mutation negatives passed.
Those results are compatibility evidence, not approval to adopt a workspace.
This C4h branch changes only this campaign directory. All tests below used
disposable trees archived from that exact head, not an active package file.

## Source-bound scratch variants

| Input | SHA256 |
| --- | --- |
| Existing root `package.json` | `dee2dac7542c77b294c547cf9342b750bbd871c3df89df3d522c98d5a7bf34b5` |
| C4f candidate root workspace | `c26306641fd6274d3157a8782f3b3c5767ddfe447afa59d1051d1320d3d3de76` |
| C4f candidate root lock | `4642e444fcfe57682deea81634073311c1ffafaf530b8f0c077247544521a6c4` |
| Existing LED `package.json` | `9215f46cf79f84922b6b70147958971b1a962b0f52878f98ab5d937155860951` |
| Scratch LED `package.json`, pin changed only to `pnpm@11.5.2` | `624b990b14b18e4fe4d1a4b2c3996fde61606b8098c15df6976e9391e9a8b581` |
| Historical LED `pnpm-workspace.yaml` | `0f4e60757dd4c20657b2f72acf9af585587f4aeee1c2bf8f5590fec7832cbf03` |
| Historical LED lock, unchanged in both scratch trees | `6987246726a2cfa4aeb01cddb6825c3224f62ac64f62b2d00c7d0f8ae91a81d3` |

The **aligned-only** tree `/tmp/zudo-c4h-aligned-20261116` changed the LED
`packageManager` pin but retained the active nested workspace manifest. The
**flat** tree `/tmp/zudo-c4h-flat-20261116` changed that pin and renamed the
nested manifest to `pnpm-workspace.historical.yaml`, retaining its exact bytes
and the historical lock at its original path. Both used the C4f root workspace
and lock candidate. `verify-layout.mjs` checks these locks, source bytes,
discovered importer set, and installed circuit-doc routing bytes. It passed in
both modes; a changed scratch package pin failed closed and was restored.

Run the layout verifier with `COREPACK_HOME` pointing to a cached pnpm 11.5.2:

```sh
COREPACK_HOME=/tmp/zudo-c4f-corepack node circuit/orchestration/campaigns/pd-led-20261116-c4/workspace-alignment/verify-layout.mjs /tmp/zudo-c4h-aligned-20261116 aligned-only
COREPACK_HOME=/tmp/zudo-c4f-corepack node circuit/orchestration/campaigns/pd-led-20261116-c4/workspace-alignment/verify-layout.mjs /tmp/zudo-c4h-flat-20261116 flat
```

## Actual pnpm command paths

| Scratch layout | Root `pnpm -r list` | `pnpm --dir products/led-lamp -r list` | LED circuit-doc routing.py SHA256 |
| --- | --- | --- | --- |
| Aligned pin only | Four importers | **Two nested importers** | `0ef884503557a755f3b8c468e377fa5040bac8fe8aa24ea5bf0458df3c32e19e` (historical, unpatched) after nested command |
| Nested manifest deactivated | Four importers | **Four root importers** | `efd532f2f48992026e93f2651c0ba6768eea78f60b6c08e860590bea96854bea` (PD patch) |

Changing only the nested `packageManager` field is insufficient. The active
nested `pnpm-workspace.yaml` still takes precedence for `--dir` calls. After
a clean root install in aligned-only scratch, `pnpm --dir
products/led-lamp/doc exec zfb check` performed a separate 274-package nested
install and used the unpatched circuit-doc. Its existing allowlist ran esbuild
and workerd postinstall scripts in disposable scratch. The command then passed,
but it did **not** check the proposed unified dependency tree. Neither lock
changed. The earlier root-filtered LED doc check did run directly and passed.

The flat scratch tree had no `node_modules` before its frozen pnpm 11.5.2
install. `pnpm install --frozen-lockfile --ignore-scripts` checked all 422
policy entries and installed 343 packages across four importers. The root
policy was not relaxed; the historical nested `minimumReleaseAge: 0` remained
in the archived manifest and did not become a root exception. Root and LED
lock hashes remained exact. Afterward:

- `pnpm --dir products/led-lamp/doc exec zfb check` passed without a nested
  install (one collection and TypeScript).
- `pnpm --dir products/led-lamp check` passed: 35 lines, 92 placements, four
  exclusions; generated pages, preflight, 25 models and previews current; LED
  doc TypeScript passed.
- `pnpm --dir products/led-lamp build` passed: 29 enclosure print STLs,
  unchanged selected models/pages, and 198 pages built. The archive has no
  `.git`, so doc-history emitted **zero entries**; this does not verify history
  rendering. The build emitted many nonfatal `ZB001` fragment warnings.
- `pnpm --dir products/led-lamp check:site` passed: built references (35
  records, 25 SVGs, 25 models), artifact/privacy scan with zero canary hits,
  image check, strict anchors (14,134 links / 2,520 IDs), and Mermaid.
- The installed `check-browser` CLI against that built site passed locally:
  four search/LLMs representatives, 32 viewport/theme navigations and reference
  inspections, shell interaction, dialogs, model and footprint viewers, focus,
  SPA cleanup, fallbacks and no-JS checks.

The first offline clean-install attempt failed because pnpm's policy check
still fetched metadata. The retry passed using the environment's proxy and
certificate. One initial container check failed because `pnpm` was absent from
the container `PATH`; a temporary Corepack shim resolved that environment
issue. Host `pnpm test:browser` stopped before browser launch because the
container-created `node_modules` stored `/pnpm-store` as its store path and
host pnpm attempted repair under an unavailable host cache. The equivalent
installed CLI was used for the actual browser test. Its first run failed to
load a footprint SVG because container-built `dist` files inherited source
mode `0600` under a different UID. Making **only disposable `dist`** readable
resolved the cross-user artifact access; the repeated full browser smoke
passed. These failures are retained as execution limits, not counted as green
application checks.

## Resource and integration boundary

The flat install, application check, build and site check ran in a Node
24.22.3/Python 3.13.5 container pinned to
`sha256:6e5d4c38403930b420404f190be8563396dca2bd156a6cb4722707b0efcf6fc1`
with hard two-CPU/4 GiB limits. Measured cgroup aggregate memory peaks were
1,271,042,048 bytes for install, 509,444,096 for `check`, 1,688,350,720 for
build, and 525,049,856 for `check:site`. The successful host Chromium run used
CPU affinity `[0,1]` and the shared heavy-test guard, with sampled process-group
peak RSS 1,350,260 KiB over 67.674 seconds; it had no hard 4 GiB memory cap.

The reviewed integration change is therefore **three coordinated actions**:
adopt C4f's root workspace and lock, align LED's package-manager pin, and
deactivate/archive the nested workspace manifest while preserving its original
bytes and historical lock. A single integrator must apply and review those
changes on an exact head, then repeat clean install, checks, build, browser
smoke and Git-backed history verification. This experiment is not that
adoption. No canonical package/workspace/lock, evidence, CAD, publication,
deployment or hardware file changed here. #307 and all existing holds remain.
