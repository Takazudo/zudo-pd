---
title: Generate JLCPCB Files with kicad-jlcpcb-tools
sidebar_position: 6
---

This guide explains how to generate JLCPCB-ready manufacturing files (Gerbers, BOM, CPL) using the `kicad-jlcpcb-tools` KiCad plugin. The plugin replaces the manual export workflow and **automatically applies rotation corrections** that JLCPCB's part library requires.

## Why This Plugin

KiCad's footprint orientation does not always match the orientation in JLCPCB's internal part library. For many packages (QFN, SOT-23-5, SOT-23-6, SOIC, etc.) this mismatch causes the chip to be soldered with the wrong pin 1, killing the board.

PCBA v2 hit this exact issue: U1 (STUSB4500QTR, QFN-24) was placed at 180° in the CPL, but JLCPCB's library expected 270°. JLCPCB caught it during pre-production review, but only because the board has a small part count.

`kicad-jlcpcb-tools` ships with a community-maintained rotation database keyed by footprint name and applies the correction at CPL-generation time. The exported file matches what JLCPCB expects on the first try.

## Installation

The plugin is distributed via KiCad's built-in Plugin and Content Manager (PCM).

### Step 1: Open the Plugin and Content Manager

1. Launch the **KiCad** main app (`/Applications/KiCad/KiCad.app`).
2. On the launcher screen, click **Plugin and Content Manager**.
- Alternatively: menu **Tools → Plugin and Content Manager**.

### Step 2: Find the Plugin

1. Click the **Plugins** tab.
2. In the search box, type `JLCPCB`.
3. Locate **JLCPCB Tools** by **Bouni**.

### Step 3: Install

1. Click **Install** on that row.
2. Click **Apply Pending Changes** at the bottom right.
3. Wait for the download to finish.
4. Close PCM. **Restart KiCad** (close all KiCad windows and reopen).

### Manual Install (Fallback)

If the plugin is not listed in PCM (e.g., not yet updated for a new KiCad major version), install manually:

```bash
cd ~/Documents/KiCad/10.0/scripting/plugins
git clone https://github.com/Bouni/kicad-jlcpcb-tools.git
```

Restart PCB Editor afterward.

## First-Time Project Setup

Open `zudo-pd.kicad_pcb` in **PCB Editor**. After install you should see a new toolbar icon for **JLCPCB Tools** (red square logo). Click it to open the plugin panel.

The panel lists every component on the PCB with columns for designator, footprint, value, LCSC part number, stock, and rotation correction.

### Assign LCSC Part Numbers

For each component:

1. Select the row.
2. Click **Select part** (or double-click the LCSC column).
3. Search by LCSC number (e.g., `C2678061`) or by part description.
4. Confirm the selection.

The plugin writes the LCSC number into the schematic as a custom field, so this is a one-time job per part. Later runs reuse the saved number.

**For this project**, the LCSC numbers are already in the BOM at:

- `dist/jlcpcb-ready/jlcpcb-bom-with-lcsc.csv` (legacy reference)
- See also the per-component pages under **Components** in this documentation site.

### Verify Rotation Corrections

The plugin shows a **Rotation** column. For each component, the plugin looks up the footprint name in its built-in rotation database and applies an offset.

- A non-zero rotation means a correction was applied automatically.
- Zero rotation means no correction was needed (or no entry exists for that footprint — confirm manually if the part is polarized).

If you find a missing or wrong correction, use the plugin's **Corrections Manager** to add or override entries — see [Gotcha: EasyEDA-Derived Footprints](#gotcha-easyeda-derived-footprints) below for a worked example.

> **Note**: corrections are stored in a single global SQLite file (`~/Documents/KiCad/<version>/3rdparty/plugins/com_github_bouni_kicad-jlcpcb-tools/jlcpcb/corrections.db`). Edits affect **every** KiCad project on this machine — there is no per-project rotation override in this plugin version. The "Use global corrections" checkbox in the Corrections Manager toggles whether the project uses these rules at all, not whether the rules are project-scoped.

## Generating JLCPCB Files

1. In the JLCPCB Tools panel, click **Generate**.
2. The plugin produces a `jlcpcb/` directory at the project root containing:

```
jlcpcb/
├── gerber/                    ← Gerber files (one per layer)
├── production_files/
│   ├── BOM-zudo-pd.csv        ← BOM with LCSC numbers
│   └── POS-zudo-pd.csv        ← Pick-and-place / CPL with corrected rotations
└── project.db                 ← Plugin local cache (SQLite)
```

3. Zip the contents of `jlcpcb/gerber/` for upload (JLCPCB expects a single `.zip` of Gerbers).
4. Upload to the JLCPCB order page:
- **Gerber**: the zip
- **BOM**: `production_files/BOM-zudo-pd.csv`
- **CPL**: `production_files/POS-zudo-pd.csv`

## Gotcha: EasyEDA-Derived Footprints

The plugin's default rotation rules target KiCad's **official** footprint libraries (`Package_TO_SOT_SMD`, `Package_QFP`, etc.). For projects that use footprints downloaded from LCSC/EasyEDA via tools like `easyeda2kicad.py`, several common rules **over-correct** the rotation and produce a CPL that would solder parts incorrectly.

### How to Recognize Affected Footprints

EasyEDA-derived footprints follow a naming pattern with a dimension descriptor and a pin-1 position suffix:

```
<package>_L<length>-W<width>-P<pitch>-LS<lead-span>-{BL|BR}
```

Examples used in this project:

- `SOT-23_L2.9-W1.3-P1.90-LS2.4-BR` (Q1 — AO3401A P-channel MOSFET)
- `SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL` (D4 — USBLC6-2SC6 ESD protection)
- `QFN-24_L4.0-W4.0-P0.50-BL-EP2.8` (U1 — STUSB4500QTR)

The `BL` / `BR` suffix encodes pin 1's position (Bottom-Left / Bottom-Right), confirming these footprints are already drawn in JLCPCB's pin-1 convention. They should **not** receive any further rotation correction.

### What the Plugin Does Wrong (Without Override)

The default plugin database contains the rule:

```
^SOT-23 → -90°
```

This regex matches everything that starts with `SOT-23`, including the EasyEDA-derived `SOT-23_L2.9-...-BR` and `SOT-23-6_L2.9-...-BL` footprints. The plugin then applies a **bogus** -90° correction, and the resulting CPL would tell JLCPCB to mount Q1 and D4 rotated 90° clockwise from their correct orientation.

JLCPCB's pre-production review may or may not catch this — they flagged U1 (QFN-24) on PCBA v2 but **did not flag** the SOT-23 / SOT-23-6 over-corrections. Don't rely on JLCPCB's review to catch this.

(For QFN-24 the plugin's `+270°` correction is **correct** — even though that footprint also has `BL` in its name. The QFN issue is unrelated to the SOT-23 over-correction. JLCPCB confirmed `270°` was right during the v2 review.)

### Fix: Add Specific Overrides

The plugin's matching logic does an "anchored" pass first (it appends `$` to each regex and tries to match against the end of the string). A more specific regex with `.*$` at the end will win over the generic `^SOT-23` rule before the unanchored fallback runs.

**Steps** (in PCB Editor with the JLCPCB Tools panel open):

1. Click the **Corrections Manager** toolbar button (or right-click any part row → "Add correction by package").
2. The dialog has an **Add / Edit** section at the top. Despite the absence of an explicit "Add" button, **clicking "Save" with a new regex creates a new row** (Save acts as upsert).
3. Add the first rule:
- **Regex**: `^SOT-23-6_L2\.9-W1\.6.*$`
- **Rotation**: `0`
- **Offset X / Y**: `0.00`
- Click **Save**.
4. Add the second rule:
- **Regex**: `^SOT-23_L2\.9-W1\.3.*$`
- **Rotation**: `0`
- Click **Save**.
5. Close the dialog. Click **Generate** in the main panel.

### Verifying the Fix

The plugin's log should now show:

```
... Fixed rotation of D4 (USBLC6-2SC6 / SOT-23-6_L2.9-W1.6-...) on Top Layer by 0 degrees
... Fixed rotation of Q1 (-30V -4A / SOT-23_L2.9-W1.3-...) on Top Layer by 0 degrees
... Fixed rotation of U1 (STUSB4500QTR / QFN-24_L4.0-W4.0-...) on Top Layer by 270 degrees
```

The `0 degrees` lines mean **your override matched and applied a no-op rotation**, blocking the generic `-90°` rule. U1's `+270°` is the QFN correction we want.

The resulting CPL should contain:

```
D4: rotation = 0    ← matches working v1/v2 orientation
Q1: rotation = 0    ← matches working v1/v2 orientation
U1: rotation = 90   ← = 270° in KiCad's convention (the value JLCPCB confirmed for v2)
```

### Why the Numbers Look Different from KiCad's Native CPL

The plugin's CPL uses JLCPCB's coordinate convention (Y-axis flipped vs. KiCad's), so rotation values do not match KiCad's native CPL export numerically — but they are equivalent physical orientations. Don't try to compare the plugin's CPL row-by-row to `dist/jlcpcb-ready/jlcpcb-cpl.csv`; verify physical correctness instead (pin 1 visual check on JLCPCB's pre-production rendering).

### Adding More Overrides as the Library Grows

Whenever you add a new EasyEDA-derived footprint to the project, check if its package family has an existing default rule in the Corrections Manager. If yes, add a more specific override (with the `_L\d` shape characteristic of EasyEDA naming) so the over-correction does not apply.

A general pattern that catches both SOT-23 variants in one rule (alternative to the two specific rules above):

```
^SOT-23(-[36])?_L\d
```

Apply the same approach to other package families if they hit the same problem (`^SOIC-`, `^SOP-`, `^TSOP-`, etc., all have default rules that may over-correct EasyEDA footprints).

## Repository Convention

The `/jlcpcb` directory is **gitignored**. Reasons:

- All output is regenerable from the `.kicad_pcb` and `.kicad_sch` (LCSC numbers live in schematic fields, not in `project.db`).
- `project.db` is binary and produces noisy diffs.
- Keeps the repository small.

If you want to retain a snapshot of a specific order, copy the relevant files into `/jlcpcb-order-snapshots/` (which is committed) following the existing folder convention there.

## Verifying Before Order

After generating, do a quick sanity check before uploading:

1. **Open `production_files/POS-zudo-pd.csv`** in a spreadsheet.
2. **Find polarized parts** (ICs, diodes, electrolytic caps, LEDs).
3. **Cross-reference rotation values** against the previous successful order in `dist/jlcpcb-ready/jlcpcb-cpl.csv` if applicable.
4. **For new ICs that were not on the previous order**, manually verify pin 1 in the JLCPCB part library page (e.g., search for the LCSC number on jlcpcb.com and inspect their footprint rendering).

This avoids the back-and-forth seen on PCBA v2 where JLCPCB had to flag U1 mid-order.

## Troubleshooting

### Plugin Toolbar Icon Missing After Install

- Confirm KiCad was fully restarted (all windows closed).
- Re-open PCB Editor (the icon only appears there, not in Schematic Editor).
- If still missing, check **PCB Editor → Tools → External Plugins** for the entry.

### "Footprint not in rotation database"

- The plugin will warn for unknown footprints. Manually verify rotation against the JLCPCB part library page.
- Add the footprint and correction to the plugin's rotation database for next time.

### Wrong Rotation Applied (Plugin Over-Corrects)

If the generated CPL has a rotation that disagrees with a previously-working order, the plugin's default regex may be matching an EasyEDA-derived footprint and over-correcting it. See [Gotcha: EasyEDA-Derived Footprints](#gotcha-easyeda-derived-footprints).

### LCSC Search Returns No Results

- Confirm internet connectivity (the plugin queries JLCPCB's API).
- Some discontinued parts no longer appear; check the LCSC number directly at `https://jlcpcb.com/parts`.

## References

- Plugin repository: [`Bouni/kicad-jlcpcb-tools`](https://github.com/Bouni/kicad-jlcpcb-tools)
- Related: [KiCad Project Workflow](./kicad-workflow.md)
- Related: [Download KiCad Footprints and Symbols](./kicad-parts-download.md)
