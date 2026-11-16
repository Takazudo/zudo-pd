# C4b root LED firmware gate — isolated review candidate

- Parent: [#308](https://github.com/Takazudo/zudo-pd/issues/308). Moya remains
  the sole manager and integrator. This is a bounded C4 workflow candidate,
  based on independently accepted C3h
  `3d8de928e03edf576f8bbf4977a3b8c0788cc2b5`.
- Branch: `codex/c4b-led-firmware-workflow-20261116-01`.
- Exclusive writes: the new root
  `.github/workflows/led-firmware-checks.yml` and this receipt. The imported
  LED workflow, firmware source, Makefile, receipts and #307 are untouched.
- Imported workflow SHA256:
  `5c4bb2c617825572b48c810b5f44d43c5391750ef158d758faa779548e7dc1af`.
  Target Makefile SHA256:
  `f4d8e33d2a17e5d55c5c89b99195e892ee238a9973726ccfc03c33380c68b1b1`.

The imported firmware workflow is nested under `products/led-lamp/` and inactive
as a repository workflow. This root workflow makes its Board L host tests and
build-only ARM checks discoverable for future PRs and `main` changes to LED
firmware. It preserves the imported two-job sequence, checkout pin, host
compiler checks, 13.2.1-enforced target build, receipt/image identity check,
V72 cross-compile and incremental/configuration-switch check. Paths are
adjusted to the imported subtree. The workflow cannot flash a board and has
read-only repository permission. Topic branch pushes do not match its `push`
trigger; no PR was opened here.

## Checks and limits

- YAML parsed; triggers are PRs targeting `main` or `base/**` and pushes to
  `main`, restricted to LED firmware or this workflow. Both imported job step
  lists match the root job step lists: **PASS**.
- `make -C products/led-lamp/firmware/board-l/target host-test target-host-test`:
  **PASS** (44 explicit-window scenarios, 5,430 off-by-default checks, 106
  boot-policy checks, 71,053 ADC checks; zero failures). This ran with two-CPU
  affinity and a 4 GiB per-process address-space limit; sampled process-group
  peak RSS was 23,456 KiB.
- `pnpm circuit:check`: **PASS**, with the same affinity/limit; sampled group
  peak RSS was 255,864 KiB. Sampled peaks are not a hard aggregate ceiling.
- ARM image/receipt, V72 cross-compile and incremental checks: **NOT RUN**
  locally because `arm-none-eabi-gcc` is absent. CI was not dispatched. Native
  CAD, browser, full build, PR, merge, deployment and hardware checks were
  **NOT RUN**. Future CI must prove the ARM path on the exact integration head.

Independent exact-head review is required before Moya considers integration.
This branch does not approve a package-toolchain change, LED evidence adoption,
public site change or physical firmware acceptance.
