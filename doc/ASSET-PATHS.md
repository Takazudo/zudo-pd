# Asset Paths

zfb serves `doc/public/` at the site root, so a file at `doc/public/circuits/foo.svg` is available at URL `/circuits/foo.svg`.

## Old → New path mapping

| Asset type | Old path | New `doc/public/` path | Public URL |
|---|---|---|---|
| Circuit SVGs | `doc/static/circuits/<name>.svg` | `doc/public/circuits/<name>.svg` | `/circuits/<name>.svg` |
| Footprint SVGs | `doc/docs/_fragments/footprints/<name>.svg` | `doc/public/footprints/<name>.svg` | `/footprints/<name>.svg` |
| Footprint PNGs | `doc/static/footprints/<name>.png` | `doc/public/footprint-imgs/<name>.png` | `/footprint-imgs/<name>.png` |
| Datasheets | `doc/static/datasheets/<name>` | `doc/public/datasheets/<name>` | `/datasheets/<name>` |
| Images | `doc/static/img/<name>` | `doc/public/img/<name>` | `/img/<name>` |
| KiCad assets | `doc/static/kicad/<name>` | `doc/public/kicad/<name>` | `/kicad/<name>` |
| Favicon | `doc/static/favicon.ico` | `doc/public/favicon.ico` | `/favicon.ico` |

## IMPORTANT: Footprint SVG vs Footprint PNG — two separate dirs

Content tasks must use the correct URL depending on asset type:

- **`/footprints/<name>.svg`** — footprint layout diagrams as SVGs (54 files, formerly in `doc/docs/_fragments/footprints/`). These are the detailed pad-layout vector drawings.
- **`/footprint-imgs/<name>.png`** — footprint preview screenshots as PNGs (11 files, formerly in `doc/static/footprints/`). These are component package photos/renders.

These are intentionally in **separate directories** to avoid filename collisions (e.g., both had a `CH224D` file in different formats).

## `doc/public/` contents summary

| Directory | Count | Notes |
|---|---|---|
| `doc/public/circuits/` | 9 SVGs | Circuit stage diagrams |
| `doc/public/footprints/` | 54 SVGs | Footprint layout diagrams |
| `doc/public/footprint-imgs/` | 11 PNGs | Footprint preview images |
| `doc/public/datasheets/` | 12 files | PDF datasheets |
| `doc/public/img/` | 5 files | Site images (logo, favicon copy, enlarge icon) |
| `doc/public/kicad/` | 3 files | KiCad setup screenshots |
| `doc/public/favicon.ico` | 1 | Site favicon |

## Not moved (S7/S8 handle these)

The following files remain in `doc/static/` and are handled by later waves:
- `doc/static/netlify.toml` — S8 deletes
- `doc/static/_redirects` — S8 deletes
- `doc/static/.nojekyll` — S7 cleans up

## Diagram MDX fragments (NOT moved)

The 7 `.mdx` diagram fragments in `doc/docs/_fragments/` are **not** assets — they are content fragments inlined by content waves (S3+). They remain at their original location:
- `doc/docs/_fragments/buck-u2-diagram.mdx`
- `doc/docs/_fragments/buck-u3-diagram.mdx`
- `doc/docs/_fragments/buck-u5-diagram.mdx`
- `doc/docs/_fragments/inverter-u4-diagram.mdx`
- `doc/docs/_fragments/ldo-u6-diagram.mdx`
- `doc/docs/_fragments/ldo-u7-diagram.mdx`
- `doc/docs/_fragments/ldo-u8-diagram.mdx`
