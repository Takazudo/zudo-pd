# PCB Footprints and Package Specifications

This directory contains PCB footprint diagrams and package specifications for all components used in the USB-PD modular synthesizer power supply project.

## Footprint Images

| Component | File | Package | JLCPCB Part | Mount Type |
|-----------|------|---------|-------------|------------|
| **CH224D** | `CH224D.png` | QFN-20 (3×3mm) | C347423 | SMD |
| **LM2596S-ADJ** | `LM2596S-ADJ.png` | TO-263-5 | C347423 | SMD |
| **ICL7660M** | `ICL7660M.png` | SOP-8/SOIC-8 | C356724 | SMD |
| **L7812CV** | `L7812CV.png` | TO-220 | C86206 | Through-hole |
| **L7805ABD2T** | `L7805ABD2T.png` | TO-263-2 (D2PAK) | C2914 | SMD |
| **CJ7912** | `CJ7912.png` | TO-252-2L (DPAK) | C94173 | SMD |
| **SMAJ15A** | `SMAJ15A.png` | SMA (DO-214AC) | C571368 | SMD |
| **PRTR5V0U2X** | `PRTR5V0U2X.png` | SOT-143 | C5199240 | SMD |
| **USB-TYPE-C-009** | `USB-TYPE-C-009.png` | 6-pin Type-C | C456012 | SMD |

## Package Documentation (PDFs)

Reference documents for standard package types:

### Component-Specific Datasheets
- `CH224D-datasheet.pdf` - WCH CH224D USB PD controller full datasheet
- `LM2596S-datasheet.pdf` - LM2596S-ADJ DC-DC converter datasheet
- `SMAJ-datasheet.pdf` - SMAJ series TVS diode specifications

### Generic Package Specifications
- `D2PAK-package.pdf` - TO-263-2 package dimensions (L7805ABD2T)
- `DPAK-package.pdf` - TO-252 package dimensions (CJ7912)
- `SMA-package.pdf` - DO-214AC package dimensions (SMAJ15A)
- `SMA-DO214AC.pdf` - Alternate SMA package specification
- `SOT143-package.pdf` - SOT-143 package dimensions (PRTR5V0U2X)
- `SOP8-package.pdf` - SOIC-8 package dimensions (ICL7660M)
- `TO-220-package.pdf` - TO-220 package dimensions (L7812CV)

## Usage Notes

### For PCB Layout Design
1. **Footprint images** (`.png` files) show:
   - Package outline dimensions
   - Pin/pad layout and numbering
   - Recommended PCB land pattern
   - Thermal pad requirements (where applicable)

2. **Package PDFs** provide detailed specifications:
   - Precise mechanical dimensions
   - Tolerances and variations
   - Soldering recommendations
   - 3D package profiles

### Thermal Considerations
- **QFN-20 (CH224D)**: Requires exposed pad connection with thermal vias
- **TO-263/D2PAK (LM2596S-ADJ, L7805ABD2T)**: Metal tab for heat dissipation
- **TO-252/DPAK (CJ7912)**: Metal tab soldered to PCB copper pour
- **TO-220 (L7812CV)**: Through-hole with optional heatsink mounting

### SMD vs Through-Hole
- **8 SMD components**: CH224D, LM2596S-ADJ, ICL7660M, L7805ABD2T, CJ7912, SMAJ15A, PRTR5V0U2X, USB-C connector
- **1 Through-hole**: L7812CV (TO-220) - can use heatsink if needed

## Sources

Footprint images and datasheets obtained from:
- Manufacturer official websites (WCH, STMicroelectronics, Diodes Inc., Nexperia, etc.)
- JLCPCB component library
- Industry-standard package specification documents
- SnapEDA and similar PCB design resources

All footprints extracted at 200-300 DPI resolution for PCB design clarity.

---

*Last updated: 2025-12-28*
