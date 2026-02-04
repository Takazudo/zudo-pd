# JLCPCB Order Files - Ready for Production

Generated: 2026-02-04

## Files Overview

### ✅ PCB Fabrication Files (Gerbers)
Location: `../gergers/`

**Gerber layers (9 files):**
- `zudo-pd-F_Cu.gbr` - Front copper layer
- `zudo-pd-B_Cu.gbr` - Back copper layer
- `zudo-pd-F_Mask.gbr` - Front soldermask
- `zudo-pd-B_Mask.gbr` - Back soldermask
- `zudo-pd-F_Paste.gbr` - Front solder paste (for stencil)
- `zudo-pd-B_Paste.gbr` - Back solder paste
- `zudo-pd-F_Silkscreen.gbr` - Front silkscreen
- `zudo-pd-B_Silkscreen.gbr` - Back silkscreen
- `zudo-pd-Edge_Cuts.gbr` - Board outline

**Drill files (2 files):**
- `zudo-pd-PTH.drl` - Plated through holes
- `zudo-pd-NPTH.drl` - Non-plated through holes

**Job file:**
- `zudo-pd-job.gbrjob` - Gerber job description

### ✅ PCBA Assembly Files (This Directory)

**BOM (Bill of Materials):**
- `jlcpcb-bom-with-lcsc.csv` - **USE THIS FILE** for JLCPCB order
  - 38 unique component types
  - All LCSC part numbers included
  - Test points excluded (TP1-TP5)

**CPL (Component Placement List):**
- `jlcpcb-cpl.csv` - **USE THIS FILE** for JLCPCB order
  - 72 total components (top + bottom)
  - Coordinates converted for JLCPCB format
  - Y-axis negated from KiCad coordinates
  - Rotation angles normalized (0-360°)

## Component Summary

### Total Components: 38 types, 72 placements

**By Stage:**
- Stage 1 (USB-PD): 10 components
- Stage 2 (DC-DC): 15 components
- Stage 3 (Linear Regulators): 9 components
- Stage 4 (Protection): 9 components
- Stage 5 (Output Connectors): 6 components

**Through-Hole Components (Hand Solder Required):**
- J6, J7, J8, J9 (FASTON terminals) - 4 units
- J10, J11 (16-pin headers) - 2 units

All other components are SMD and will be assembled by JLCPCB.

## JLCPCB Ordering Steps

### 1. Upload Gerber Files
- Go to https://jlcpcb.com/quote
- Upload: `../gergers/` as a ZIP file (or upload individual files)
- **PCB Specification:**
  - Layers: 2
  - PCB Qty: 5-10 (recommended for cost optimization)
  - PCB Thickness: 1.6mm
  - Surface Finish: HASL (lead-free) or ENIG
  - Copper Weight: 1 oz (35 μm)
  - Remove Order Number: Yes (optional)

### 2. Enable SMT Assembly
- Toggle "SMT Assembly" to ON
- Select: Top Side + Bottom Side (if components on both sides)
- Assembly side: Both sides
- Tooling holes: Added by JLCPCB

### 3. Upload Assembly Files
- **BOM File:** Upload `jlcpcb-bom-with-lcsc.csv`
- **CPL File:** Upload `jlcpcb-cpl.csv`

### 4. Review BOM
- JLCPCB will match components to their library
- Verify all 38 component types are matched
- Check for any warnings or missing parts
- **Expected Result:** All parts should auto-match (100% availability)

### 5. Review Component Placement
- Use JLCPCB's placement viewer
- Verify component orientations (especially polarized parts):
  - Electrolytic capacitors (C3, C4, C5, etc.)
  - Diodes (D1-D4, TVS1-TVS3)
  - ICs (U1-U8)
  - LEDs (LED2-LED4)
- Confirm no components overlap or are misplaced

### 6. Checkout
- Review total cost (PCB + Assembly + Components)
- Expected cost: ~¥2,600/board for 10 boards
- Add to cart and proceed to payment

## Post-Order Assembly

After receiving the PCBs from JLCPCB, you'll need to hand-solder:

**Through-Hole Components:**
1. J6-J9 (FASTON terminals) - ×4
2. J10-J11 (16-pin headers) - ×2

**Tools Required:**
- Soldering iron
- Solder wire
- Flux (optional but recommended)

## Important Notes

### Component Orientation
Pay special attention to:
- **U1 (STUSB4500):** Pin 1 indicator - top left
- **Electrolytic Capacitors:** Negative terminal marking
- **LEDs:** Cathode marking (check footprint orientation)
- **Diodes:** Cathode band orientation
- **ICs:** Pin 1 dot/notch alignment

### Test Points
The following test points are NOT assembled (for manual probing):
- TP1: +15V USB-PD
- TP2: GND
- TP3: +13.5V
- TP4: +7.5V
- TP5: -13.5V

### Known Limitations
- JLCPCB may adjust component placements slightly during manufacturing
- Some footprints may show warnings - verify they match JLCPCB's library
- Rotation angles have been normalized but may need manual verification

## Troubleshooting

**If BOM upload fails:**
- Check CSV format (no special characters in designators)
- Verify LCSC part numbers are valid (all start with 'C')
- Re-export from this directory

**If CPL upload fails:**
- Verify coordinate format (must include "mm" suffix)
- Check rotation values (must be 0-360)
- Ensure Layer field is "Top" or "Bottom" (capitalized)

**If components don't match:**
- Some LCSC parts may be out of stock temporarily
- Check JLCPCB's suggested alternatives
- Refer to BOM documentation: `/doc/docs/overview/bom.md`

## File Integrity Check

**MD5 Checksums:** (Generate before ordering)
```bash
md5sum jlcpcb-bom-with-lcsc.csv
md5sum jlcpcb-cpl.csv
```

## Version History

- **2026-02-04:** Initial release
  - 38 component types
  - 72 component placements
  - All LCSC part numbers verified
  - Coordinates converted for JLCPCB format

## Support

For questions or issues:
- GitHub: https://github.com/Takazudo/zudo-pd
- Documentation: https://takazudomodular.com/pj/zudo-pd/
- BOM Reference: `/doc/docs/overview/bom.md`
