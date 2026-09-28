# CAD asset receipt

A receipt records what an acquired symbol, footprint or 3D model actually is, where it came from and what has been checked. It is a sidecar next to the v1 evidence: it does not change the owner bundle's schema, and the validator does not read it.

Write one receipt per acquired asset set as `circuit/cad-receipts/ASSET_ID.receipt.json`, starting from [cad-asset-receipt.json](./cad-asset-receipt.json). Copy this Markdown form beside it only when the JSON needs a longer explanation. Leave a field `null` until you know it; never fill a field with a guess.

## Field groups

| Group | Fields | What to enter |
| --- | --- | --- |
| Identity | `asset_id`, `record_id`, `manufacturer`, `mpn`, `package`, `variant_notes` | The exact orderable variant the asset is meant to represent, and the owner record ID |
| Acquisition | `provider`, `library_release_tag`, `source_url`, `acquired_on`, `original_filenames`, `sha256` | Where the files came from, the pinned library release tag (for KiCad official libraries), the date, the unmodified filenames and one SHA-256 per file |
| Representation | `files`, `formats`, `units`, `original_paths` | The formats kept (symbol, footprint, STEP, WRL, other), their units and where the originals are kept |
| Fidelity | `class`, `reason`, `evidence` | One of `exact-vendor`, `family`, `derived`, `unavailable`, with the reason and the evidence that supports the label |
| Derivation | `derived`, `input_sha256`, `tool`, `tool_version`, `parameters`, `output_sha256` | Only for a derived asset: the inputs, the deterministic transformation and the outputs |
| CAD use | `symbol`, `footprint`, `model_path`, `transform`, `seating_plane` | How the footprint references the model, and the offset, rotation and scale applied |
| Checks | `performed`, `remaining_physical_checks` | Each check actually done with its method and evidence (pin/pad numbering, pitch, body envelope, pin 1), and what still needs physical verification |
| Publication | `preview_selected`, `download_published`, `permitted_scope` | Whether a preview is selected in `circuit/publication/selection.json`, whether a file is listed in `circuit/publication/assets.json`, and the redistribution scope |

## Fidelity classes

| Class | Use it when |
| --- | --- |
| `exact-vendor` | The manufacturer published the asset for this exact orderable variant |
| `family` | The asset represents the package or series and is not proven for this variant |
| `derived` | The asset was produced from an original by a recorded transformation |
| `unavailable` | No usable asset exists; the state is documented and nothing is fabricated |

## Limits to state in every receipt

- A rendered preview is not dimensional proof.
- A footprint that imports cleanly does not prove pin correspondence.
- Model geometry does not prove physical seating, clearance or solderability; list those as remaining physical checks until they are observed.
