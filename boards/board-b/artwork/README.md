# Board B back silkscreen

The current PCB uses the two SVGs supplied for the back artwork:

- `pattern.svg`: unchanged copy of `Asset 6.svg`.
- `logo.svg`: unchanged copy of `Asset 5.svg`.

The pattern fills the back-view left area, with an unprinted strip on the right
for branding, terminal labels and the four-line specification block:

```text
zudo-pd v1
+12V : 1.2A
-12V : 0.8A
+5V : 0.5A
```

The current values are shared whole-board design targets, with physical full-load
and temperature qualification still open. The SVG
pattern is heavier than the thin-line rough mockup. Its proportions are preserved
and its top/bottom are cropped to the board. The supplied mirrored logo is split
into emblem and lettering and rotated 90 degrees. In the portrait back view
shown by the user, the emblem sits on the left and the two-line brand name on the
right; both read normally. Fine feather and fish details may merge or disappear
in physical printing.

`back-preview.png` is a native KiCad render of the actual PCB;
`back-portrait-preview.png` shows the rotated view used for the branding layout. Open
`../board-b.kicad_pcb` and view its bottom side to inspect the editable artwork.
It consists of filled `B.SilkS` polygons and four mirrored text items in the
`Board B back artwork` group. Copper, mask layers, holes, component placement,
front silkscreen and existing back voltage labels are unchanged.

The pattern has a 0.8 mm outline inset. Artwork is clipped at least 0.3 mm outside
conservative pad/mask bounding boxes, with another 0.3 mm around the complete
J5, J10 and J11 solder rows. No graphics are added to copper or solder mask.
This is decorative artwork, not an insulation or thermal treatment.

Regenerate into an ignored staging path with:

```sh
uv run scripts/pcb/apply-back-silkscreen.py \
  --branding-only \
  --output tmp/back-silk/candidate.kicad_pcb \
  --report tmp/back-silk/verification.json
```

`--branding-only` preserves the existing native pattern polygons byte-for-byte,
including manual edits. Omit it when generating the complete artwork for a fresh
layout. Existing user-edited rail-label positions and styling are always retained.

The script uses the retained SVGs, resolves nonzero SVG fills and their holes,
flattens curves, clips artwork around board pads, and uses KiCad polygon fracture
to retain internal openings. It replaces its previous generated group and the
old one-line title. It refuses any change to the remaining PCB structure.
`verification.json` records that structural check and the source/result hashes.

Inspect a bottom render and run native DRC before promoting a candidate. Refresh
PCB-dependent reports and the sole current prototype package afterward; do not
keep superseded output packages. The original local KiCad project-settings edit
is separate from this artwork change.
