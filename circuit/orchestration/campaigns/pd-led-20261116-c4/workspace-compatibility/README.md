# C4g LED workspace compatibility probe

This is an isolated follow-up to the C4f dependency-resolution experiment at
`52d78cf745d983603cad4f33360a2080525551a0`. It tests the preferred
**candidate** of Node 24 and root pnpm 11.5.2 against the retained LED source.
It does not adopt the unified workspace or alter an active manifest, lock,
historical report, generated evidence, or hardware file.

## Bound inputs and execution

| Input | SHA256 |
| --- | --- |
| PD circuit-doc patch | `7991370866d4019bc1c7b2411e9421c18ba701a850f580c49c4d098e8b005e6c` |
| LED historical lock, both repository and separate scratch | `6987246726a2cfa4aeb01cddb6825c3224f62ac64f62b2d00c7d0f8ae91a81d3` |
| C4f candidate unified lock | `4642e444fcfe57682deea81634073311c1ffafaf530b8f0c077247544521a6c4` |
| Retained C15849 record | `f268aff069a8856587b7978b9262b25280e9cb8c655dfb432e8dcfa608bdd32b` |
| Retained STUSB bundle routes | `70ee838bacc3adee8eec210d80e02ea3d7b8a052008e66f15a4800b289e0c383` |

The unified scratch tree was `/tmp/zudo-c4f-unified-20261116`; the separate
historical LED tree was `/tmp/zudo-c4f-separate-20261116`. Each was installed
with scripts disabled in C4f, then received a copy of the retained LED source
for these tests. `source-bindings.mjs` verifies the five input hashes above
before behavioral probes, plus the installed circuit-doc files used by all
four patch hunks, the reference renderer/descriptor, and the three transitive
entry files. A negative test mutates source and installed-package bytes in an
injected reader and confirms that the complete verifier rejects both. No
install hook or lifecycle script ran. The checks used Node
24.22.3; the source validator also used Python 3.13.5 in the pinned trixie
image `sha256:6e5d4c38403930b420404f190be8563396dca2bd156a6cb4722707b0efcf6fc1`.
Container runs had hard `--cpus=2 --memory=4g` limits. Aggregate peak memory
for those runs was not measured. The host Chromium probe used CPU affinity
`[0,1]`, not a hard CPU quota or memory cap; sampled process-group peak RSS
was 572,352 KiB over 4.924 seconds. A 4 GiB virtual-address cap prevents
Node/Chromium startup here, so that browser run cannot claim a 4 GiB limit.
The corrected browser command passed under the machine-wide heavy-test guard
with a 563,808 KiB sampled group peak over 3.036 seconds. One preceding
unguarded repeat failed to obtain the historical Chrome page target; a guarded
retry passed, so browser launch stability remains a limitation.

Run the focused tests with `node compatibility.test.mjs UNIFIED SEPARATE
LED_SOURCE` (without `--test` before the positional paths). The browser probe
uses `node focus-browser.mjs UNIFIED SEPARATE LED_SOURCE CHROMIUM`. Both scripts
fail closed on changed bound inputs. The focused container command was:

```sh
docker run --rm --cpus=2 --memory=4g \
  -v /workspace/zudo-pd:/repo:ro \
  -v /tmp/zudo-c4f-unified-20261116:/unified:ro \
  -v /tmp/zudo-c4f-separate-20261116:/separate:ro \
  -w /repo \
  node@sha256:6e5d4c38403930b420404f190be8563396dca2bd156a6cb4722707b0efcf6fc1 \
  node /repo/circuit/orchestration/campaigns/pd-led-20261116-c4/workspace-compatibility/compatibility.test.mjs \
  /unified /separate /repo/products/led-lamp
```

## Four patch hunks against LED behavior

| Patch hunk | Bound result |
| --- | --- |
| Built-reference document/model exception | The real C15849 descriptor has an available document and model. Both installed scanners accept its rendered reference card. The patched scanner also accepts a hypothetical unavailable-document card retaining the **same real** footprint and model links; the historical scanner rejects it. The patched scanner still rejects an injected PDF link. All 35 current LED descriptors have available documents and model descriptors, so the unavailable case is prospective. |
| Routing suffix guard | Both installed routers resolve the retained bundle's `PESD24VS1UB,115` to `rec-pesd24vs1ub`. Only the patched router refuses `PESD24VS1UB,125` and `PESD24VS1UB, 115 from OtherVendor`; the historical router falsely resolves both. |
| CDP page visibility assertion | Both versions can launch local Chromium and navigate a small local page while `document.visibilityState` is `visible`. A focused fake-CDP test proves the patched `navigate` rejects a hidden page; the historical one accepts it. |
| Chrome focus emulation | The patched launch sends `Emulation.setFocusEmulationEnabled` and local Linux Chromium accepted it; the historical launch does not send it. Mac focus timing and the full LED site interaction remain unverified. |

Both installed versions passed `zfb check` on the retained LED doc: one
collection and TypeScript, no errors. Both passed offline `zudo-circuit-doc
validate --config circuit.config.ts`: 35 lines, 92 placements, four exclusions,
pin-asset check, no refreshed sources. The `compatibility.test.mjs` run passed
six tests, exercising actual installed circuit-doc code and retained LED
record/routes. The host `focus-browser.mjs` run passed both launch/navigation
probes. These are compatibility checks of this source and environment, not a
full LED build, site visual review, or canonical contract validation.

## Nested pnpm and shifted transitive dependencies

Before copying the full LED source into scratch, root pnpm 11.5.2 with
`--filter './products/led-lamp/doc'` selected the LED doc importer. A root
Corepack invocation with `--dir products/led-lamp` instead encountered the
nested `packageManager: pnpm@10.34.1` field and refused the 11.5.2 command.
Running Corepack from the nested LED directory selected pnpm 10.34.1 and its
unchanged historical lock. After the full source copy, a root-filtered `pnpm
exec zfb check` attempted dependency-status repair and stopped before `zfb`
with `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY` / fetch failure. The direct
installed `zfb` binary passed in both trees. A unified integration must settle
root versus nested invocation behavior and verify it from a clean install;
the nested historical `minimumReleaseAge: 0` is not a root exemption.

The candidate shifts three compatible-range LED transitives: `hono`
`4.13.17 → 4.13.16`, `parse5` `8.1.1 → 8.1.0`, and
`@jridgewell/resolve-uri` `3.1.2 → 3.1.3`. Both installed sets passed a
retained-record Hono route request, parse5 serialization of the real reference
section (byte-identical across versions), and resolution of its real model
URL. This narrows the compatibility concern; it does not prove all runtime
paths or visual output are identical.

No CI, PR, merge, publication, deployment, native/CAD, or physical action ran.
The next integration decision remains whether to align the nested package
manager or provide reviewed path-scoped root commands, followed by clean
candidate installation and full LED checks on the exact proposed integration
head. Historical source locks and all campaign holds remain in force.
