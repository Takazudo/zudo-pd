# Full-history workspace candidate

This branch tests pnpm 11.5.2 with the imported LED product inside the PD
workspace. It is a development candidate, not an approval for hardware,
manufacturing, publication, or the canonical migration.

## Preservation receipt

- The root `pnpm-workspace.yaml` is byte-identical to the reviewed C4f
  candidate file (SHA-256 `c26306641fd6274d3157a8782f3b3c5767ddfe447afa59d1051d1320d3d3de76`).
  The initial integration lock at `960842535539eeef44c2835db6548724a37c4958`
  was byte-identical to C4f (SHA-256
  `4642e444fcfe57682deea81634073311c1ffafaf530b8f0c077247544521a6c4`).
  The current lock adds only the local doc-history-server patch resolution.
- The LED `packageManager` pin is the only change in its `package.json`, from
  `pnpm@10.34.1` to the root's `pnpm@11.5.2`. Its candidate SHA-256 is
  `624b990b14b18e4fe4d1a4b2c3996fde61606b8098c15df6976e9391e9a8b581`.
- The LED nested workspace manifest moved from `pnpm-workspace.yaml` to
  `pnpm-workspace.historical.yaml` without byte changes. Its SHA-256 remains
  `0f4e60757dd4c20657b2f72acf9af585587f4aeee1c2bf8f5590fec7832cbf03`.
  The historical LED lock remains at `products/led-lamp/pnpm-lock.yaml`,
  byte-identical with SHA-256
  `6987246726a2cfa4aeb01cddb6825c3224f62ac64f62b2d00c7d0f8ae91a81d3`.
- No product, evidence, CAD, BOM, DNP, identity, or historical report files
  are changed by this candidate. The parent C4h commit is
  `01918ba8f9acd1a82241df72bd2d8859f8461819`; the full Git history is
  available to this worktree.

The root install must use the frozen lockfile, retain the root's dependency
trust and release-age policy, and run with install scripts disabled during
validation. Actual checks and their results are recorded on campaign issue
`#308` against the exact candidate head. This receipt does not infer document
history continuity from the zero-history archive experiment.

The import merge requires `git log -m` for the LED history server to see the
added files. The local package patch adds that flag to its Git walks and
deduplicates merge-parent entries before Compare renders them. The focused
test checks one current and two source-era revisions with nonempty content.
The plugin's bulk Created date still starts at the import merge; source-era
history is present in the interactive route, and the date limitation must be
resolved or accepted before publication.
