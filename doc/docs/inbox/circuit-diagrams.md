---
sidebar_position: 3
---

# Circuit Diagrams

Complete circuit configuration shown in stages.

## Diagram1: USB-PD Power Supply Section

```
USB-C Connector              CH224Q (DFN-10-EP)              LED Status Indicator
┌─────────────┐                ┌──────────────┐                 ┌─────────────┐
│VBUS (B9,A9) ├──┬─────────────┤1. VHV        │                 │   VDD 3.3V  │
│             │  │             │8. VBUS       │─┬─→ 15V Output  │      │      │
│CC1 (A5)     ├──┼─────────────┤7. CC1        │ │               │    330Ω     │
│CC2 (B5)     ├──┼─────────────┤6. CC2        │ │               │   (R1)      │
│GND (B12,A12)├──┼─────────────┤GND           │ │               │      │      │
└─────────────┘  │             │11. EP        │←┘               │   Red LED   │
                 │             │              │                 │   (LED1)    │
               ┌─C1            │9. CFG1       │←── GND          │      │      │
               │ 10µF/25V      │2. CFG2/SCL   │←── Open         │  PG ────────┘
               │               │3. CFG3/SDA   │←── Open         │
               └─┬───          │10. PG        │─────────────────┘
                 │             │4. DP         │    (N/C)
               ┌─C2            │5. DM         │    (N/C)
               │ 10µF/25V      └──────────────┘
               │                      │
               └─┬────────────────────┘
                 │
                GND
```

### Connection List

**Power Lines:**
- `USB-C VBUS (B9, A9)` → `CH224Q pin 1 (VHV)`
- `USB-C VBUS (B9, A9)` → `CH224Q pin 8 (VBUS)`
- `CH224Q pin 8 (VBUS)` → `15V Output`

**Communication Lines:**
- `USB-C CC1 (A5)` → `CH224Q pin 7 (CC1)`
- `USB-C CC2 (B5)` → `CH224Q pin 6 (CC2)`

**Ground:**
- `USB-C GND (B12, A12)` → `CH224Q GND`
- `USB-C GND (B12, A12)` → `CH224Q pin 11 (EP)`
- `C1 negative` → `GND`
- `C2 negative` → `GND`

**Capacitors:**
- `C1 (10µF/25V)`: `VBUS` ⟷ `GND` (input filter)
- `C2 (10µF/25V)`: `VBUS` ⟷ `GND` (input filter)

**Configuration Pins:**
- `CH224Q pin 9 (CFG1)` → `GND` (15V config)
- `CH224Q pin 2 (CFG2/SCL)` → `Open` (15V config)
- `CH224Q pin 3 (CFG3/SDA)` → `Open` (15V config)

**LED Status Indicator Circuit:**
- `VDD 3.3V` → `R1 (330Ω)` → `LED1 (Red LED)` → `CH224Q pin 10 (PG)`

**Not Connected:**
- `CH224Q pin 4 (DP)` - N/C
- `CH224Q pin 5 (DM)` - N/C

## Diagram2: USB-PD +15V → +13.5V Buck Converter (LM2596S-ADJ #1)

```
+15V ─────┬─── L1: 100µH ──┬─── D1 ──┬─── C3: 470µF/25V ──┬─→ +13.5V/1.3A
          │    (4.5A)      │   SS34  │   (Input Filter)   │
          │                │    ↓    │                    │
          │           ┌────┴─────────┴──┐                 │
          │           │5  VIN      VOUT │4────────────────┤
          └───────────┤3  ON        FB  │2────────┬───────┘
                      │1  GND           │         │
                      └─────────────────┘         │
                              │                   │
                             GND              ┌────┴───┐
                                              │ R1     │ 10kΩ (actual 13.53V)
                                              │ 10kΩ   │
                                              └────┬───┘
                                              ┌────┴───┐
                                              │ R2     │ 1kΩ
                                              │ 1kΩ    │
                                              └────┬───┘
                                                   │
                                                  GND
```

## Diagram3: +15V → +7.5V Buck Converter (LM2596S-ADJ #2)

```
+15V ─────┬─── L2: 100µH ──┬─── D2 ──┬─── C4: 470µF/10V ──┬─→ +7.5V/0.6A
          │    (4.5A)      │   SS34  │   (Input Filter)   │
          │                │    ↓    │                    │
          │           ┌────┴─────────┴──┐                 │
          │           │5  VIN      VOUT │4────────────────┤
          └───────────┤3  ON        FB  │2────────┬───────┘
                      │1  GND           │         │
                      └─────────────────┘         │
                              │                   │
                             GND              ┌────┴───┐
                                              │ R3     │ 5.1kΩ (actual 7.50V)
                                              │ 5.1kΩ  │
                                              └────┬───┘
                                              ┌────┴───┐
                                              │ R4     │ 1kΩ
                                              │ 1kΩ    │
                                              └────┬───┘
                                                   │
                                                  GND
```

## Diagram4: +15V → -15V Voltage Inverter (ICL7660)

```
+15V ─────┬─────────────────────────────────────────┬─→ +15V (to other circuits)
          │                                         │
          │           ICL7660M/TR                   │
          │         ┌──────────────┐                │
          └─────────┤2,8  V+   CAP+│1──┐            │
                    │              │   │            │
           GND ─────┤3   GND   CAP-│4──┼─┐          │
                    │              │   │ │          │
          OPEN ─────┤6   LV    V-  │5──┼─┼──────────┴─→ -15V
                    │              │   │ │
          OPEN ─────┤7   OSC       │   │ │
                    └──────────────┘   │ │
                                       │ │
                     C9: 10µF Ceramic  │ │
                    ┌───────────────────┘ │
                    │                     │
                    └─────────────────────┘

                    C10: 10µF Ceramic
                    ┌─────────────────────────┐
                    │                         │
            -15V ───┼─────────────────────────┼─── GND
                    │                         │
                    └─────────────────────────┘
```

**Flying capacitor (C9) connects directly between PIN1 and PIN4**

```
      Flying Capacitor C9 (10µF)
           ┌─────────┐
PIN1 ──────┤+       -├────── PIN4
(CAP+)     └─────────┘     (CAP-)
```

## Diagram5: -15V → -13.5V Buck Converter (LM2596S-ADJ #3)

```
-15V ─────┬─── L3: 100µH ──┬─── D3 ──┬─── C7: 470µF/25V ──┬─→ -13.5V/0.9A
          │    (4.5A)      │   SS34  │   (Input Filter)   │
          │                │    ↓    │                    │
          │           ┌────┴─────────┴──┐                 │
          │           │5  VIN      VOUT │4────────────────┤
          └───────────┤3  ON        FB  │2────────┬───────┘
                      │1  GND           │         │
                      └─────────────────┘         │
                              │                   │
                             GND              ┌────┴───┐
                                              │ R5     │ 10kΩ (actual -13.53V)
                                              │ 10kΩ   │
                                              └────┬───┘
                                              ┌────┴───┐
                                              │ R6     │ 1kΩ
                                              │ 1kΩ    │
                                              └────┬───┘
                                                   │
                                                  GND
```

## Diagram6: +13.5V → +12V Linear Regulator

```
+13.5V ──┬─── C11: 470nF ───┬─── LM7812 ───┬─── C14: 100nF ───┬─→ +12V/1.2A
         │                  │   (TO-220)   │                  │
         │                  │    ┌─────┐   │                  │
         │                  └────│1 IN │3──┴──────────────────┤
         │                       │     │                      │
         │                    ┌──│2 GND│                      │
         │                    │  └─────┘                      │
         │                    │     │                         │
         └─── C17: 470µF ─────┼─────┼─── C18: 470µF ──────────┤
              (Input Stab)    │     │    (Output Stab)        │
                              │     │                         │
                             GND   GND                        │
                                                              │
                     ┌────────────────────────────────────────┘
                     │
               ┌─────┴─────┐  1kΩ (R7)
               │    LED2   │ ──────┬─→ +12V Status (Green LED)
               │  (Green)  │       │
               └─────┬─────┘       │
                     │            GND
                    GND
```

## Diagram7: +7.5V → +5V Linear Regulator

```
+7.5V ───┬─── C12: 470nF ───┬─── LM7805 ───┬─── C15: 100nF ───┬─→ +5V/1.2A
         │                  │  (TO-220F-3) │                  │
         │                  │    ┌─────┐   │                  │
         │                  └────│1 IN │3──┴──────────────────┤
         │                       │     │                      │
         │                    ┌──│2 GND│                      │
         │                    │  └─────┘                      │
         │                    │     │                         │
         └─── C19: 470µF ─────┼─────┼─── C20: 470µF ──────────┤
              (Input Stab)    │     │    (Output Stab)        │
                              │     │                         │
                             GND   GND                        │
                                                              │
                     ┌────────────────────────────────────────┘
                     │
               ┌─────┴─────┐  1kΩ (R8)
               │    LED3   │ ──────┬─→ +5V Status (Blue LED)
               │  (Blue)   │       │
               └─────┬─────┘       │
                     │            GND
                    GND
```

## Diagram8: -13.5V → -12V Linear Regulator

```
-13.5V ──┬─── C13: 470nF ───┬─── LM7912 ───┬─── C16: 100nF ───┬─→ -12V/1.0A
         │                  │   (TO-220)   │                  │
         │                  │    ┌─────┐   │                  │
         │                  └────│1 IN │2──┴──────────────────┤
         │                       │     │                      │
         │                    ┌──│3 GND│                      │
         │                    │  └─────┘                      │
         │                    │     │                         │
         └─── C21: 470µF ─────┼─────┼─── C22: 470µF ──────────┤
              (Input Stab)    │     │    (Output Stab)        │
                              │     │                         │
                             GND   GND                        │
                                                              │
                     ┌────────────────────────────────────────┘
                     │
               ┌─────┴─────┐  1kΩ (R9)
               │    LED4   │ ──────┬─→ -12V Status (Red LED)
               │  (Red)    │       │
               └─────┬─────┘       │
                     │            GND
                    GND
```

## Diagram9: Protection Circuit (Beginner-Friendly, 2-Stage Protection)

```
+12V ──┬─── PTC1: 1.1A ──┬─── F1: 2A ───┬─── TVS1: SMAJ15A ───┬─→ +12V OUT
       │  (Auto-Reset)   │   (Backup)   │   (15V Unidirect)   │
       │                 │              │      ↓              │
       │                 │              └─────GND─────────────┤
       │                 │                                    │
       │                 └─── LED2: Green ──[R7: 1kΩ]──┬─→ Power Status
       │                                                │
       │                                               GND
       │
       └─── Staged Protection:
            1. Overload (1.2-2A) → PTC trips → Auto-reset after 30s ✅
            2. Short (>2A) → Fuse blows → Repair required ❌

+5V ───┬─── PTC2: 0.75A ─┬─── F2: 1.5A ──┬─── TVS2: PRTR5V0U2X ─┬─→ +5V OUT
       │  (Auto-Reset)   │   (Backup)    │   (5V Bidirect)      │
       │                 │              │      ↕               │
       │                 │              └─────GND──────────────┤
       │                 │                                    │
       │                 └─── LED3: Blue ──[R8: 1kΩ]──┬─→ Power Status
       │                                               │
       │                                              GND
       │
       └─── Staged Protection (same as above)

-12V ──┬─── PTC3: 0.9A ──┬─── F3: 1.5A ──┬─── TVS3: SMAJ15A ───┬─→ -12V OUT
       │  (Auto-Reset)   │   (Backup)    │  (15V Unidirect Rev)│
       │                 │              │      ↑              │
       │                 │              └─────GND─────────────┤
       │                 │                                    │
       │                 └─── LED4: Red ──[R9: 1kΩ]──┬─→ Power Status
       │                                              │
       │                                             GND
       │
       └─── Staged Protection (same as above)

※ TVS3 for negative voltage protection: cathode to -12V rail, anode to GND
※ PTC has near-zero resistance normally, becomes high resistance on overcurrent
※ Fuse protects against sudden shorts that PTC cannot handle
※ If LED goes out → overload → reduce modules and wait 30 seconds
```

## Diagram10: Power Flow Overview

```
USB-C 15V ──┬─→ +13.5V (DC-DC) ──→ +12V (LDO) ──→ +12V OUT
            │
            ├─→ +7.5V  (DC-DC) ──→ +5V  (LDO) ──→ +5V OUT
            │
            └─→ -15V (Inverter) ──→ -13.5V (DC-DC) ──→ -12V (LDO) ──→ -12V OUT
```
