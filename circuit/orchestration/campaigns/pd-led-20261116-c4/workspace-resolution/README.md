# C4f dependency-resolution experiment

This is a review-only candidate based on independently accepted C4e
`ea29271d5a73dff3a54359cab89af2acb159783f`. It does not change either
active `package.json`, `pnpm-workspace.yaml` or `pnpm-lock.yaml`, or the
historical LED lock. [The candidate workspace file](candidate-pnpm-workspace.yaml)
only adds `products/led-lamp` and `products/led-lamp/doc` to the PD root's
package list. [The candidate lock](candidate-pnpm-lock.yaml) was generated in
disposable scratch from that file and the existing manifests/patch.

## Source and execution binding

| Input | SHA256 |
| --- | --- |
| PD root `package.json` | `dee2dac7542c77b294c547cf9342b750bbd871c3df89df3d522c98d5a7bf34b5` |
| PD root `pnpm-workspace.yaml` | `003027ca71f6b38b4b61a0d8ba53617faab32e432629638bdf0ca72d56ab19a6` |
| PD root `pnpm-lock.yaml` | `0cfc99232bcf94ff625900330524d5e296b3e734e7d6deeabc745be11cf85b8c` |
| LED `package.json` | `9215f46cf79f84922b6b70147958971b1a962b0f52878f98ab5d937155860951` |
| LED `pnpm-workspace.yaml` | `0f4e60757dd4c20657b2f72acf9af585587f4aeee1c2bf8f5590fec7832cbf03` |
| LED historical `pnpm-lock.yaml` | `6987246726a2cfa4aeb01cddb6825c3224f62ac64f62b2d00c7d0f8ae91a81d3` |
| LED `doc/package.json` | `6d84f5b90ea2d32dbf5a662c20893ce41eb534429e9037fd9eec1e913211a627` |
| PD circuit-doc patch | `7991370866d4019bc1c7b2411e9421c18ba701a850f580c49c4d098e8b005e6c` |

The scratch run used Node 24.22.3 in image
`sha256:9d266751ca3d7fdbe651c878ffd5ad0a42fed49a18c283509267c97f025b7496`,
Corepack pnpm 11.5.2 for the unified candidate, and pnpm 10.34.1 for the
unchanged separate LED workspace. Docker enforced two CPUs and 4 GiB memory;
aggregate peak was not measured. All `pnpm install` commands used
`--ignore-scripts`, and no install lifecycle script or hook ran. The first
host attempt under a 4 GiB *address-space* limit failed when Node reserved a
worker code range at about 111 MiB sampled RSS; it made no lockfile claim.
The first container attempt could not fetch pnpm without the environment's
proxy. Both setup failures were resolved using cached Corepack and the proxy
certificate. No repository file was changed by either attempt.

The candidate root ran `pnpm install --lockfile-only --ignore-scripts
--no-frozen-lockfile`, then a frozen lockfile-only check and a full frozen
install with scripts disabled. All passed. The frozen install reported the
root supply-chain policy passed for **422 entries**. The PD root policy was
not relaxed; specifically, no `minimumReleaseAge: 0` was added to it. The
historical nested LED workspace retains its own existing setting, which was
not treated as a root exemption. Its lock stayed byte-identical in scratch.

## Resolution differences to review

- The unified lock has four importers, 422 package entries and 438 snapshot
  entries. All 329 PD package and snapshot entries are unchanged; every direct PD and LED
  dependency retains its existing version, except that both LED importers now
  reference the **PD-patched** circuit-doc 0.3.0 snapshot.
- Shared transitive resolution changes three LED references: `hono`
  `4.13.17 → 4.13.16`, `parse5` `8.1.1 → 8.1.0`, and
  `@jridgewell/resolve-uri` `3.1.2 → 3.1.3`. The associated shared
  `zfb-runtime`, `zudo-doc` and trace-mapping snapshots change their
  dependency pointers. These are compatible-range choices, not proof of
  identical LED runtime behavior. No unrelated direct dependency was upgraded.
- Actual installed LED circuit-doc routing differs: unified/patched
  `routing.py` SHA256
  `efd532f2f48992026e93f2651c0ba6768eea78f60b6c08e860590bea96854bea`;
  separate/original SHA256
  `0ef884503557a755f3b8c468e377fa5040bac8fe8aa24ea5bf0458df3c32e19e`.
  Against the retained LED STUSB bundle, both resolve
  `PESD24VS1UB,115`; the patched instance rejects `PESD24VS1UB,125` and
  `PESD24VS1UB, 115 from OtherVendor`, while the historical instance
  resolves both to `rec-pesd24vs1ub`. The global PD patch also contains
  browser-focus and built-reference policy changes; their LED impact still
  needs focused review before adoption.
- A root `pnpm --filter './products/led-lamp/doc'` command selected the LED
  doc package. A root Corepack pnpm 11.5.2 invocation using
  `--dir products/led-lamp` was rejected by the nested `packageManager:
  pnpm@10.34.1` field. Root scripts must use path-scoped filters or a
  separately reviewed nested package-manager alignment.

The **separate-workspace option** passed a frozen lockfile-only check and a
full scripts-disabled frozen install under its existing pnpm 10.34.1. It
preserves the original LED lock and unpatched circuit-doc behavior. It also
retains two package-manager versions, two active locks and the nested
workspace's existing `minimumReleaseAge: 0`; that exception must not become a
global PD policy. Separate installation is a bounded transition path, not the
accepted one-workspace outcome.

No full build, native/CAD check, browser check, CI, PR, merge, deployment or
physical validation ran. A safe unified integration needs an explicit review
of the global patch and three transitive choices, plus a decision on root
commands versus nested package-manager alignment. Then a single integrator
can apply a reviewed root lock/workspace change and run full checks on its
exact integration head. This experiment does not adopt that change.
