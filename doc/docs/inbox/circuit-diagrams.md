---
sidebar_position: 3
---

# Circuit Diagrams

Complete circuit configuration shown in stages.

## Diagram1: USB-PD Power Supply Section

```
USB-C Connector              CH224Q (DFN-10-EP)              LED Status Indicator
┌─────────────┐                ┌──────────────┐                 ┌─────────────┐
│VBUS (B9,A9) ├──┬─────────────┤1. VHV        │                 │  +5V Rail   │
│             │  │             │8. VBUS       │─┬─→ 15V Output  │  (from D7)  │
│CC1 (A5)     ├──┼─────────────┤7. CC1        │ │               │      │      │
│CC2 (B5)     ├──┼─────────────┤6. CC2        │ │               │    330Ω     │
│GND (B12,A12)├──┼─────────────┤GND           │ │               │   (R1)      │
└─────────────┘  │             │11. EP        │←┘               │      │      │
                 │             │              │                 │  Green LED  │
               ┌─C1            │9. CFG1       │←── GND          │   (LED1)    │
               │ 10µF/25V      │2. CFG2/SCL   │←── Open         │      │      │
               │               │3. CFG3/SDA   │←── Open         │  PG ────────┘
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
- `+5V rail (from Diagram7)` → `R1 (330Ω)` → `LED1 (Green LED)` → `CH224Q pin 10 (PG)`
- LED indicates: **Power Good** (lights up when 15V USB-PD negotiation succeeds)
- LED current: `I = (5V - 2.2V) / 330Ω ≈ 8.5mA` ✅
- **Note**: PG pin is open-drain, pulls LOW when power is good, enabling current flow from +5V through LED to GND

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

### Connection List

**Power Lines:**
- `+15V input` → `U2 (LM2596S-ADJ) pin 5 (VIN)`
- `+15V input` → `U2 pin 3 (ON)` (enable)
- `U2 pin 4 (VOUT)` → `L1 (100µH)` → `+13.5V output`

**Inductor and Diode:**
- `L1 (100µH, 4.5A)`: Between `U2 VOUT` and `+13.5V output`
- `D1 (SS34 Schottky)`: Cathode to `L1-VOUT junction`, Anode to `GND` (flyback)

**Capacitors:**
- `C3 (470µF/25V)`: `+13.5V output` ⟷ `GND` (output filter)

**Feedback Network:**
- `U2 pin 2 (FB)` → `R1 (10kΩ)` → `+13.5V output`
- `U2 pin 2 (FB)` → `R2 (1kΩ)` → `GND`
- Voltage divider ratio: `VOUT = 1.23V × (1 + R1/R2) = 13.53V`

**Ground:**
- `U2 pin 1 (GND)` → `System GND`

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

### Connection List

**Power Lines:**
- `+15V input` → `U3 (LM2596S-ADJ) pin 5 (VIN)`
- `+15V input` → `U3 pin 3 (ON)` (enable)
- `U3 pin 4 (VOUT)` → `L2 (100µH)` → `+7.5V output`

**Inductor and Diode:**
- `L2 (100µH, 4.5A)`: Between `U3 VOUT` and `+7.5V output`
- `D2 (SS34 Schottky)`: Cathode to `L2-VOUT junction`, Anode to `GND` (flyback)

**Capacitors:**
- `C4 (470µF/10V)`: `+7.5V output` ⟷ `GND` (output filter)

**Feedback Network:**
- `U3 pin 2 (FB)` → `R3 (5.1kΩ)` → `+7.5V output`
- `U3 pin 2 (FB)` → `R4 (1kΩ)` → `GND`
- Voltage divider ratio: `VOUT = 1.23V × (1 + R3/R4) = 7.50V`

**Ground:**
- `U3 pin 1 (GND)` → `System GND`

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

### Connection List

**Power Lines:**
- `+15V input` → `U4 (ICL7660M) pin 2 (V+)`
- `+15V input` → `U4 pin 8 (V+)` (tied together)
- `U4 pin 5 (V-)` → `-15V output`

**Charge Pump Capacitors:**
- `C9 (10µF Ceramic)`: `U4 pin 1 (CAP+)` ⟷ `U4 pin 4 (CAP-)` (flying capacitor)
- `C10 (10µF Ceramic)`: `-15V output` ⟷ `GND` (output filter)

**Control Pins:**
- `U4 pin 6 (LV)` → `Open` (normal voltage mode, not low voltage)
- `U4 pin 7 (OSC)` → `Open` (10kHz internal oscillator)

**Ground:**
- `U4 pin 3 (GND)` → `System GND`

**Operation:**
- Charge pump switches `C9` between `+15V` and `GND` to generate `-15V`
- Output voltage: `VOUT ≈ -(VIN - 1V) = -14V typical`

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

### Connection List

**Power Lines:**
- `-15V input` → `U5 (LM2596S-ADJ) pin 5 (VIN)`
- `-15V input` → `U5 pin 3 (ON)` (enable)
- `U5 pin 4 (VOUT)` → `L3 (100µH)` → `-13.5V output`

**Inductor and Diode:**
- `L3 (100µH, 4.5A)`: Between `U5 VOUT` and `-13.5V output`
- `D3 (SS34 Schottky)`: Cathode to `L3-VOUT junction`, Anode to `GND` (flyback)

**Capacitors:**
- `C7 (470µF/25V)`: `-13.5V output` ⟷ `GND` (output filter)

**Feedback Network:**
- `U5 pin 2 (FB)` → `R5 (10kΩ)` → `-13.5V output`
- `U5 pin 2 (FB)` → `R6 (1kΩ)` → `GND`
- Voltage divider ratio: `VOUT = -1.23V × (1 + R5/R6) = -13.53V`

**Ground:**
- `U5 pin 1 (GND)` → `System GND`

**Note:** For negative voltage regulation, all voltages are referenced to GND (0V)

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

### Connection List

**Power Lines:**
- `+13.5V input` → `U6 (LM7812) pin 1 (IN)`
- `U6 pin 3 (OUT)` → `+12V output`

**Input Capacitors:**
- `C11 (470nF)`: `+13.5V input` ⟷ `GND` (high-frequency noise filtering)
- `C17 (470µF)`: `+13.5V input` ⟷ `GND` (input stabilization)

**Output Capacitors:**
- `C14 (100nF)`: `+12V output` ⟷ `GND` (high-frequency decoupling)
- `C18 (470µF)`: `+12V output` ⟷ `GND` (output stabilization and transient response)

**LED Status Indicator:**
- `+12V output` → `R7 (1kΩ)` → `LED2 anode (Green LED)` → `LED2 cathode` → `GND`
- LED current: `I = (12V - 2V) / 1kΩ ≈ 10mA`

**Ground:**
- `U6 pin 2 (GND)` → `System GND`

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

### Connection List

**Power Lines:**
- `+7.5V input` → `U7 (LM7805) pin 1 (IN)`
- `U7 pin 3 (OUT)` → `+5V output`

**Input Capacitors:**
- `C12 (470nF)`: `+7.5V input` ⟷ `GND` (high-frequency noise filtering)
- `C19 (470µF)`: `+7.5V input` ⟷ `GND` (input stabilization)

**Output Capacitors:**
- `C15 (100nF)`: `+5V output` ⟷ `GND` (high-frequency decoupling)
- `C20 (470µF)`: `+5V output` ⟷ `GND` (output stabilization and transient response)

**LED Status Indicator:**
- `+5V output` → `R8 (1kΩ)` → `LED3 anode (Blue LED)` → `LED3 cathode` → `GND`
- LED current: `I = (5V - 2V) / 1kΩ = 3mA` (dim, consider 330Ω for brighter)

**Ground:**
- `U7 pin 2 (GND)` → `System GND`

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

### Connection List

**Power Lines:**
- `-13.5V input` → `U8 (LM7912) pin 1 (IN)`
- `U8 pin 2 (OUT)` → `-12V output`

**Input Capacitors:**
- `C13 (470nF)`: `-13.5V input` ⟷ `GND` (high-frequency noise filtering)
- `C21 (470µF)`: `-13.5V input` ⟷ `GND` (input stabilization)
  - **Polarity:** Negative terminal to `-13.5V`, positive terminal to `GND`

**Output Capacitors:**
- `C16 (100nF)`: `-12V output` ⟷ `GND` (high-frequency decoupling)
- `C22 (470µF)`: `-12V output` ⟷ `GND` (output stabilization and transient response)
  - **Polarity:** Negative terminal to `-12V`, positive terminal to `GND`

**LED Status Indicator:**
- `GND` → `LED4 anode (Red LED)` → `LED4 cathode` → `R9 (1kΩ)` → `-12V output`
- LED current: `I = (0V - (-12V) - 2V) / 1kΩ = 10mA`
- **Note:** LED is reversed compared to positive rails (anode to GND, cathode to negative)

**Ground:**
- `U8 pin 3 (GND)` → `System GND`

**Note:** LM7912 pinout differs from LM7812: pin 1=IN, pin 2=OUT, pin 3=GND

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

### Connection List

**+12V Rail Protection:**
- `+12V input` → `PTC1 (1.1A resettable fuse)` → `F1 (2A fuse)` → `+12V OUT`
- `TVS1 (SMAJ15A)`: Cathode to `+12V OUT`, Anode to `GND` (clamps overvoltage)
- `LED2 (Green)` + `R7 (1kΩ)`: Between `F1 output` and `GND` (status indicator)

**+5V Rail Protection:**
- `+5V input` → `PTC2 (0.75A resettable fuse)` → `F2 (1.5A fuse)` → `+5V OUT`
- `TVS2 (PRTR5V0U2X)`: Bidirectional protection to `GND` (clamps overvoltage)
- `LED3 (Blue)` + `R8 (1kΩ)`: Between `F2 output` and `GND` (status indicator)

**-12V Rail Protection:**
- `-12V input` → `PTC3 (0.9A resettable fuse)` → `F3 (1.5A fuse)` → `-12V OUT`
- `TVS3 (SMAJ15A)`: Cathode to `-12V OUT`, Anode to `GND` (reverse for negative rail)
- `LED4 (Red)` + `R9 (1kΩ)`: Between `GND` and `F3 output` (status indicator)

**Protection Operation:**
1. **Normal operation (&lt;rated current):**
   - PTC: Near-zero resistance, passes current
   - Fuse: Intact, passes current
   - LED: Illuminated, indicates power present

2. **Overload (current exceeds PTC rating):**
   - PTC heats up and transitions to high resistance (~1kΩ)
   - Current drops to safe level (~10mA)
   - LED dims or turns off (indicates overload)
   - Auto-resets after 30-60 seconds when cooled

3. **Short circuit (current &gt;&gt; PTC rating):**
   - PTC trips but cannot limit extreme current
   - Fuse blows (backup protection)
   - LED turns off permanently
   - Requires manual fuse replacement

**TVS Diode Operation:**
- Normally off (high impedance)
- Activates when voltage exceeds breakdown (15V for SMAJ15A, 5V for PRTR5V0U2X)
- Shunts overvoltage transients to GND
- Self-recovering (no replacement needed)

## Diagram10: Power Flow Overview

```
USB-C 15V ──┬─→ +13.5V (DC-DC) ──→ +12V (LDO) ──→ +12V OUT
            │
            ├─→ +7.5V  (DC-DC) ──→ +5V  (LDO) ──→ +5V OUT
            │
            └─→ -15V (Inverter) ──→ -13.5V (DC-DC) ──→ -12V (LDO) ──→ -12V OUT
```
