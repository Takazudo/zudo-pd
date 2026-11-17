# Full-history workspace candidate

This branch tests pnpm 11.5.2 with the imported LED product inside the PD
workspace. It is a development candidate, not an approval for hardware,
manufacturing, publication, or the canonical migration.

## Preservation receipt

- The initial integration commit `960842535539eeef44c2835db6548724a37c4958`
  used the reviewed C4f workspace and lock bytes (SHA-256
  `c26306641fd6274d3157a8782f3b3c5767ddfe447afa59d1051d1320d3d3de76`
  and `4642e444fcfe57682deea81634073311c1ffafaf530b8f0c077247544521a6c4`).
  The current workspace SHA-256 is
  `c2d8c7aebaa86543f2e8200daca63cb9246128f829a52423a858794865965ce5`
  because it adds the local doc-history-server patch. The current lock SHA-256
  is `2bdcf718a0d746836545a0be1e18dafcf9a3d4d95331d9219398c69a52e33ff1`;
  its further changes are the patch-hash resolutions.
- The LED `packageManager` pin is the only change in its `package.json`, from
  `pnpm@10.34.1` to the root's `pnpm@11.5.2`. Its candidate SHA-256 is
  `624b990b14b18e4fe4d1a4b2c3996fde61606b8098c15df6976e9391e9a8b581`.
- The LED nested workspace manifest moved from `pnpm-workspace.yaml` to
  `pnpm-workspace.historical.yaml` without byte changes. Its SHA-256 remains
  `0f4e60757dd4c20657b2f72acf9af585587f4aeee1c2bf8f5590fec7832cbf03`.
  The historical LED lock remains at `products/led-lamp/pnpm-lock.yaml`,
  byte-identical with SHA-256
  `6987246726a2cfa4aeb01cddb6825c3224f62ac64f62b2d00c7d0f8ae91a81d3`.
- Relative to C4h `01918ba8f9acd1a82241df72bd2d8859f8461819`, the
  product-facing changes are the LED package pin and manifest rename; two
  generated PD catalog pages refreshing the already-reviewed exact
  `PESD24VS1UB,115` alias; LED's generated CLAUDE page; the LED site GitHub
  setting; and two authored LED pages that label provenance and correct five
  source-file destinations (six links); and the LED host chrome binding,
  metadata bootstrap, and rendered-history gate. The campaign test, this
  receipt, pnpm workspace/lock, and local package patch also change. Evidence-source
  files, inventory rules, CAD, BOM, DNP, and historical reports remain
  unchanged. Full Git ancestry remains available to this worktree.

The root install must use the frozen lockfile, retain the root's dependency
trust and release-age policy, and run with install scripts disabled during
validation. Actual checks and their results are recorded on campaign issue
`#308` against the exact candidate head. This receipt does not infer document
history continuity from the zero-history archive experiment.

The import merge requires `git log -m` for the relocated LED document tree;
ordinary PD paths must keep their first-parent walk because some source-era
LED paths overlap PD names. The local patch scopes the merge walk accordingly,
limits LED revisions to descendants of the import or ancestors of its exact
LED source parent, excluding divergent pre-import PD branches merged afterward,
excludes post-import merges that leave a document byte-identical to its first
parent from Compare entries and update metadata, deduplicates merge-parent
Compare entries, and follows each
imported document back to its source-era Created date in bounded batches. The LED Getting
Started page separately labels the 2026-11-16 import and the original
repository. The LED route's supported `docHistoryMeta` binding reads the
plugin-generated manifest so these dates render in built HTML. An ignored
empty manifest bootstraps clean type checks and standalone builds; the plugin
replaces it during the build. The site header targets the maintained zudo-pd repository.
Automatic View Source buttons remain disabled because zudo-doc's shared
`githubUrl` mapping omits the nested `products/led-lamp/doc` path; the six
authored source links instead target the immutable zudo-pd import commit,
whose five file blobs match the candidate exactly. Changing those links to
moving `main` paths belongs to the eventual adoption review.
