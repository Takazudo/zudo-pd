---
sidebar_position: 6
---

# Mechanical Design

Physical dimensions and mechanical considerations for PCB layout and enclosure design.

## Component Heights

Physical height reference for PCB layout and enclosure design.

### Power Components

| Component         | Designator                | Package         | Height     | Notes                  |
| ----------------- | ------------------------- | --------------- | ---------- | ---------------------- |
| **LM2596S-ADJ**   | U2, U3, U4                | TO-263-5        | **4.5mm**  | DC-DC converters       |
| **L7812CD2T-TR**  | U6                        | TO-263-2        | **4.5mm**  | +12V linear regulator  |
| **L7805ABD2T-TR** | U7                        | TO-263-2        | **4.5mm**  | +5V linear regulator   |
| **CJ7912**        | U8                        | TO-252-3 (DPAK) | **2.3mm**  | -12V linear regulator  |
| **CYA1265-100UH** | L1, L2, L3                | SMD 13.8x12.8mm | **~6-7mm** | Power inductors        |
| **1217754-1**     | J3, J4, J5, J6            | FASTON 250 THT  | **8.89mm** | Power terminals        |
| **470uF 25V**     | C3, C11, C20-C21, C24-C25 | D10xL10.2mm     | **10.2mm** | Electrolytic (tallest) |
| **470uF 16V**     | C4                        | D6.3xL7.7mm     | **7.7mm**  | Electrolytic           |
| **470uF 10V**     | C22, C23                  | D6.3xL7.7mm     | **7.7mm**  | Electrolytic           |
| **100uF 25V/50V** | C5, C7, C9                | D6.3xL7.7mm     | **7.7mm**  | Electrolytic           |

### Height Profile

```mermaid
xychart-beta
    title "Component Height Profile"
    x-axis ["TO-252 (U8)", "TO-263 (U2-U7)", "Inductors (L1-L3)", "Small Caps", "FASTON (J3-J6)", "470uF 25V"]
    y-axis "Height (mm)" 0 --> 12
    bar [2.3, 4.5, 6.5, 7.7, 8.89, 10.2]
```

### PCB Design Implications

- **Tallest components**: 470uF 25V electrolytic caps (10.2mm)
- **Second tallest**: FASTON terminals J3-J6 (8.89mm)
- **Third tallest**: Smaller electrolytics &amp; inductors (7.7mm / ~6-7mm)
- **Total board height**: ~12mm including PCB thickness (1.6mm)
- **Clearance**: Keep space around TO-263 packages for thermal dissipation
- **CJ7912 advantage**: Lower profile (2.3mm) allows flexible placement
- **FASTON placement**: Position at board edge for cable access
- **Capacitor placement**: Consider grouping tall caps for enclosure fit

## PCB Dimensions

_To be determined based on component placement._

## Enclosure Considerations

_To be added._
