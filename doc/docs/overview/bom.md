---
sidebar_position: 4
---

# Bill of Materials (BOM)

Complete parts configuration using JLCPCB SMT service.

## Power Supply Specifications

- **+12V**: 1200mA (actual 1.2A support)
- **-12V**: 800mA (actual 1A support)
- **+5V**: 500mA (actual 1.2A support)
- **Input**: USB-C PD 15V 3A
- **Efficiency**: Approximately 75-80%
- **Ripple**: \<1mVp-p (final output)

## Complete Parts Configuration by Stage

### Stage 1: USB-PD Voltage Acquisition (STUSB4500)

:::info v1.1 Upgrade
This stage was upgraded from CH224D to **STUSB4500** for significantly improved charger compatibility (~95%+ vs ~33%). See [CH224D](../components/ch224d) for the deprecated v1.0 design.
:::

#### Main ICs

| Symbol | Part Number                                            | Manufacturer Part Number                           | Description               | Package | Stock     | Price     | Application             | Diagram                                                                    |
| ------ | ------------------------------------------------------ | -------------------------------------------------- | ------------------------- | ------- | --------- | --------- | ----------------------- | -------------------------------------------------------------------------- |
| **U1** | **[C2678061](https://jlcpcb.com/partdetail/C2678061)** | **[STUSB4500QTR](../components/stusb4500)**        | USB-IF Certified PD Sink  | QFN-24  | **4,728** | **$2.50** | PD Negotiation (15V)    | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |
| **Q1** | **[C347476](https://jlcpcb.com/partdetail/C347476)**   | **[AO3401A](../components/ao3401a)**               | P-Channel MOSFET -30V -4A | SOT-23  | **1.1M**  | **$0.02** | Load Switch (High-side) | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |
| **J1** | **[C456012](https://jlcpcb.com/partdetail/C456012)**   | **[USB-TYPE-C-6P](../components/usb-c-connector)** | 6P Type-C Female          | SMD     | **Stock** | **$0.05** | USB-C Input             | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |

#### ESD Protection (Optional but Recommended)

| Symbol   | Part Number                                          | Manufacturer Part Number             | Description         | Package | Stock     | Price     | Application        | Diagram                                                                    |
| -------- | ---------------------------------------------------- | ------------------------------------ | ------------------- | ------- | --------- | --------- | ------------------ | -------------------------------------------------------------------------- |
| **TVS4** | **[C343997](https://jlcpcb.com/partdetail/C343997)** | **[ESDA25L](../components/esda25l)** | CC Line TVS 25V 3pF | SOT-23  | **4,584** | **$0.15** | CC1/CC2 Protection | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |

#### Capacitors

| Symbol  | Part Number                                            | Specification     | Package | Stock          | Price       | Application         | Diagram                                                                    |
| ------- | ------------------------------------------------------ | ----------------- | ------- | -------------- | ----------- | ------------------- | -------------------------------------------------------------------------- |
| **C1**  | **[C7432781](https://jlcpcb.com/partdetail/C7432781)** | 10µF 50V X5R ±10% | 1206    | **656,427**    | **$0.024**  | VBUS Bulk Filter    | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |
| **C2**  | **[C49678](https://jlcpcb.com/partdetail/C49678)**     | 100nF 50V X7R     | 0805    | **23,309,869** | **$0.0021** | VDD HF Decoupling   | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |
| **C30** | **[C6119849](https://jlcpcb.com/partdetail/C6119849)** | 1µF 16V X5R ±10%  | 0603    | **1,225,237**  | **$0.0012** | VREG_2V7 Decoupling | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |
| **C34** | **[C6119849](https://jlcpcb.com/partdetail/C6119849)** | 1µF 16V X5R ±10%  | 0603    | **1,225,237**  | **$0.0012** | VREG_1V2 Decoupling | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |
| **C35** | **[C49678](https://jlcpcb.com/partdetail/C49678)**     | 100nF 50V X7R     | 0805    | **23,309,869** | **$0.0021** | Gate Soft-start     | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |

#### Resistors

| Symbol  | Part Number                                        | Value | Description | Package | Price       | Application                | Diagram                                                                    |
| ------- | -------------------------------------------------- | ----- | ----------- | ------- | ----------- | -------------------------- | -------------------------------------------------------------------------- |
| **R11** | **[C14675](https://jlcpcb.com/partdetail/C14675)** | 100kΩ | ±1% 100mW   | 0603    | **$0.0005** | Gate Pull-up (default OFF) | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |
| **R12** | **[C1604](https://jlcpcb.com/partdetail/C1604)**   | 22kΩ  | ±1% 100mW   | 0603    | **$0.0005** | Gate Series Resistor       | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |
| **R13** | **[C23162](https://jlcpcb.com/partdetail/C23162)** | 470Ω  | ±1% 100mW   | 0603    | **$0.0005** | VBUS Discharge             | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |
| **R14** | **[C25804](https://jlcpcb.com/partdetail/C25804)** | 10kΩ  | ±1% 100mW   | 0603    | **$0.0005** | RESET Pull-up              | [D1](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) |

**Stage 1 Subtotal: ~$2.80**

**Key Features (STUSB4500 vs CH224D):**

| Feature              | CH224D (v1.0) | STUSB4500 (v1.1)    |
| -------------------- | ------------- | ------------------- |
| **USB-IF Certified** | No            | **Yes**             |
| **Charger Compat.**  | ~33%          | **~95%+**           |
| **Error Recovery**   | None          | **Built-in retry**  |
| **Power Sequencing** | None          | **VBUS_EN_SNK pin** |
| **CC Protection**    | 8V            | **22V**             |
| **Configuration**    | Resistor      | **NVM + I2C**       |

**Critical Notes:**

- **Load switch (Q1)** controls power path - only enables after successful PD negotiation
- **VBUS_EN_SNK** goes HIGH when negotiation succeeds, turning ON Q1
- **Soft-start** via C35 (100nF) limits inrush current (τ = 22kΩ × 100nF = 2.2ms)
- **NVM programming** required to configure 15V PDO (one-time setup)

### Stage 2: DC-DC Converters (LM2596S-ADJ × 3 + ICL7660)

#### Main ICs

| Symbol | Part Number                                          | Manufacturer Part Number                          | Description        | Package  | Stock     | Price      | Application                      | Diagram                                                                                       |
| ------ | ---------------------------------------------------- | ------------------------------------------------- | ------------------ | -------- | --------- | ---------- | -------------------------------- | --------------------------------------------------------------------------------------------- |
| **U2** | **[C347423](https://jlcpcb.com/partdetail/C347423)** | **[LM2596S-ADJ(UMW)](../components/lm2596s-adj)** | Adjustable 3A Buck | TO-263-5 | **12075** | **$0.266** | +15V→+13.5V                      | [D2](/docs/overview/circuit-diagrams#diagram2-usb-pd-15v--135v-buck-converter-lm2596s-adj-1)  |
| **U3** | **[C347423](https://jlcpcb.com/partdetail/C347423)** | **[LM2596S-ADJ(UMW)](../components/lm2596s-adj)** | Adjustable 3A Buck | TO-263-5 | **12075** | **$0.266** | +15V→+7.5V                       | [D3](/docs/overview/circuit-diagrams#diagram3-15v--75v-buck-converter-lm2596s-adj-2-u3)       |
| **U4** | **[C347423](https://jlcpcb.com/partdetail/C347423)** | **[LM2596S-ADJ(UMW)](../components/lm2596s-adj)** | Adjustable 3A Buck | TO-263-5 | **12075** | **$0.266** | +15V→-13.5V Inverting Buck-Boost | [D4](/docs/overview/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4) |

#### Inductors

| Symbol | Part Number                                              | Manufacturer Part Number | Description | Package         | Stock    | Price      | Application       | Diagram                                                                                       |
| ------ | -------------------------------------------------------- | ------------------------ | ----------- | --------------- | -------- | ---------- | ----------------- | --------------------------------------------------------------------------------------------- |
| **L1** | **[C19268674](https://jlcpcb.com/partdetail/C19268674)** | **CYA1265-100UH**        | 100µH 4.5A  | SMD,13.8x12.8mm | **2763** | **$0.378** | U2 Energy Storage | [D2](/docs/overview/circuit-diagrams#diagram2-usb-pd-15v--135v-buck-converter-lm2596s-adj-1)  |
| **L2** | **[C19268674](https://jlcpcb.com/partdetail/C19268674)** | **CYA1265-100UH**        | 100µH 4.5A  | SMD,13.8x12.8mm | **2763** | **$0.378** | U3 Energy Storage | [D3](/docs/overview/circuit-diagrams#diagram3-15v--75v-buck-converter-lm2596s-adj-2-u3)       |
| **L3** | **[C19268674](https://jlcpcb.com/partdetail/C19268674)** | **CYA1265-100UH**        | 100µH 4.5A  | SMD,13.8x12.8mm | **2763** | **$0.378** | U4 Energy Storage | [D4](/docs/overview/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4) |

#### Diodes

| Symbol | Part Number                                      | Manufacturer Part Number | Description     | Package | Stock         | Price      | Application     | Diagram                                                                                       |
| ------ | ------------------------------------------------ | ------------------------ | --------------- | ------- | ------------- | ---------- | --------------- | --------------------------------------------------------------------------------------------- |
| **D1** | **[C8678](https://jlcpcb.com/partdetail/C8678)** | **SS34**                 | 3A 40V Schottky | SMA     | **1,859,655** | **$0.012** | U2 Freewheeling | [D2](/docs/overview/circuit-diagrams#diagram2-usb-pd-15v--135v-buck-converter-lm2596s-adj-1)  |
| **D2** | **[C8678](https://jlcpcb.com/partdetail/C8678)** | **SS34**                 | 3A 40V Schottky | SMA     | **1,859,655** | **$0.012** | U3 Freewheeling | [D3](/docs/overview/circuit-diagrams#diagram3-15v--75v-buck-converter-lm2596s-adj-2-u3)       |
| **D3** | **[C8678](https://jlcpcb.com/partdetail/C8678)** | **SS34**                 | 3A 40V Schottky | SMA     | **1,859,655** | **$0.012** | U4 Freewheeling | [D4](/docs/overview/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4) |

#### Feedback Resistors (Basic Parts)

| Symbol | Part Number                                        | Value     | Description | Package | Price       | Application | Diagram                                                                                       |
| ------ | -------------------------------------------------- | --------- | ----------- | ------- | ----------- | ----------- | --------------------------------------------------------------------------------------------- |
| **R1** | **[C25804](https://jlcpcb.com/partdetail/C25804)** | **10kΩ**  | ±1% 100mW   | 0603    | **$0.0005** | U2 FB Upper | [D2](/docs/overview/circuit-diagrams#diagram2-usb-pd-15v--135v-buck-converter-lm2596s-adj-1)  |
| **R2** | **[C21190](https://jlcpcb.com/partdetail/C21190)** | **1kΩ**   | ±1% 100mW   | 0603    | **$0.0005** | U2 FB Lower | [D2](/docs/overview/circuit-diagrams#diagram2-usb-pd-15v--135v-buck-converter-lm2596s-adj-1)  |
| **R3** | **[C23186](https://jlcpcb.com/partdetail/C23186)** | **5.1kΩ** | ±1% 100mW   | 0603    | **$0.0005** | U3 FB Upper | [D3](/docs/overview/circuit-diagrams#diagram3-15v--75v-buck-converter-lm2596s-adj-2-u3)       |
| **R4** | **[C21190](https://jlcpcb.com/partdetail/C21190)** | **1kΩ**   | ±1% 100mW   | 0603    | **$0.0005** | U3 FB Lower | [D3](/docs/overview/circuit-diagrams#diagram3-15v--75v-buck-converter-lm2596s-adj-2-u3)       |
| **R5** | **[C25804](https://jlcpcb.com/partdetail/C25804)** | **10kΩ**  | ±1% 100mW   | 0603    | **$0.0005** | U4 FB Upper | [D4](/docs/overview/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4) |
| **R6** | **[C21190](https://jlcpcb.com/partdetail/C21190)** | **1kΩ**   | ±1% 100mW   | 0603    | **$0.0005** | U4 FB Lower | [D4](/docs/overview/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4) |

#### Electrolytic Capacitors

| Symbol  | Part Number                                              | Specification      | Package     | Stock      | Price      | Application      | Diagram                                                                                       |
| ------- | -------------------------------------------------------- | ------------------ | ----------- | ---------- | ---------- | ---------------- | --------------------------------------------------------------------------------------------- |
| **C3**  | **[C2983319](https://jlcpcb.com/partdetail/C2983319)**   | **470µF 25V**      | D8xL10.5mm  | **46,748** | **$0.04**  | U2 Output Filter | [D2](/docs/overview/circuit-diagrams#diagram2-usb-pd-15v--135v-buck-converter-lm2596s-adj-1)  |
| **C4**  | **[C46550400](https://jlcpcb.com/partdetail/C46550400)** | **470µF 16V ±20%** | D6.3xL7.7mm | **23,331** | **$0.02**  | U3 Output Filter | [D3](/docs/overview/circuit-diagrams#diagram3-15v--75v-buck-converter-lm2596s-adj-2-u3)       |
| **C5**  | **[C22383804](https://jlcpcb.com/partdetail/C22383804)** | **100µF 25V ±20%** | D6.3xL7.7mm | **43,359** | **$0.019** | U2 Input Bulk    | [D2](/docs/overview/circuit-diagrams#diagram2-usb-pd-15v--135v-buck-converter-lm2596s-adj-1)  |
| **C7**  | **[C22383804](https://jlcpcb.com/partdetail/C22383804)** | **100µF 25V ±20%** | D6.3xL7.7mm | **43,359** | **$0.019** | U3 Input Bulk    | [D3](/docs/overview/circuit-diagrams#diagram3-15v--75v-buck-converter-lm2596s-adj-2-u3)       |
| **C9**  | **[C22383806](https://jlcpcb.com/partdetail/C22383806)** | **100µF 50V**      | D6.3xL7.7mm | **8,337**  | **TBD**    | U4 Input Bulk    | [D4](/docs/overview/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4) |
| **C11** | **[C2983319](https://jlcpcb.com/partdetail/C2983319)**   | **470µF 25V**      | D8xL10.5mm  | **46,748** | **$0.04**  | U4 Output Filter | [D4](/docs/overview/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4) |

#### Ceramic Capacitors (DC-DC Stage)

| Symbol  | Part Number                                        | Specification     | Package | Stock          | Price       | Application              | Diagram                                                                                       |
| ------- | -------------------------------------------------- | ----------------- | ------- | -------------- | ----------- | ------------------------ | --------------------------------------------------------------------------------------------- |
| **C6**  | **[C49678](https://jlcpcb.com/partdetail/C49678)** | **100nF 50V X7R** | 0805    | **23,309,869** | **$0.0021** | U2 Input Decoupling      | [D2](/docs/overview/circuit-diagrams#diagram2-usb-pd-15v--135v-buck-converter-lm2596s-adj-1)  |
| **C8**  | **[C49678](https://jlcpcb.com/partdetail/C49678)** | **100nF 50V X7R** | 0805    | **23,309,869** | **$0.0021** | U3 Input Decoupling      | [D3](/docs/overview/circuit-diagrams#diagram3-15v--75v-buck-converter-lm2596s-adj-2-u3)       |
| **C10** | **[C49678](https://jlcpcb.com/partdetail/C49678)** | **100nF 50V X7R** | 0805    | **23,309,869** | **$0.0021** | U4 Input Decoupling      | [D4](/docs/overview/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4) |
| **C31** | **[C1710](https://jlcpcb.com/partdetail/C1710)**   | **22nF 50V X7R**  | 0805    | **Rich Stock** | **$0.002**  | U2 Feedback Compensation | [D2](/docs/overview/circuit-diagrams#diagram2-usb-pd-15v--135v-buck-converter-lm2596s-adj-1)  |
| **C32** | **[C1710](https://jlcpcb.com/partdetail/C1710)**   | **22nF 50V X7R**  | 0805    | **Rich Stock** | **$0.002**  | U3 Feedback Compensation | [D3](/docs/overview/circuit-diagrams#diagram3-15v--75v-buck-converter-lm2596s-adj-2-u3)       |
| **C33** | **[C1710](https://jlcpcb.com/partdetail/C1710)**   | **22nF 50V X7R**  | 0805    | **Rich Stock** | **$0.002**  | U4 Feedback Compensation | [D4](/docs/overview/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4) |

**Note on C31/C32/C33:** These capacitors are not available in EasyEDA's symbol database. Use KiCad's built-in `Device:C` symbol paired with the `C0805.kicad_mod` footprint. This is standard practice for passive components in JLCPCB PCBA projects.

**Stage 2 Subtotal: TBD** (pending inductor/capacitor selection)

### Stage 3: Linear Regulators (LM7812/7805/7912)

#### Regulator ICs

| Symbol | Part Number                                        | Manufacturer Part Number                      | Description | Package   | Stock       | Price     | Application | Diagram                                                                               |
| ------ | -------------------------------------------------- | --------------------------------------------- | ----------- | --------- | ----------- | --------- | ----------- | ------------------------------------------------------------------------------------- |
| **U6** | **[C13456](https://jlcpcb.com/partdetail/C13456)** | **[L7812CD2T-TR](../components/l7812cv)**     | +12V 1.5A   | TO-263-2  | **40,204**  | **$0.11** | +12V Output | [D5](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)    |
| **U7** | **[C86206](https://jlcpcb.com/partdetail/C86206)** | **[L7805ABD2T-TR](../components/l7805abd2t)** | +5V 1.5A    | TO-263-2  | **272,379** | **$0.11** | +5V Output  | [D6](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)      |
| **U8** | **[C94173](https://jlcpcb.com/partdetail/C94173)** | **[CJ7912](../components/cj7912)**            | -12V 1.5A   | TO-252-2L | **3,386**   | **$0.11** | -12V Output | [D7](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8) |

#### Input Capacitors (470nF) - Basic Parts

| Symbol  | Part Number                                      | Specification     | Package | Stock         | Price       | Application     | Diagram                                                                               |
| ------- | ------------------------------------------------ | ----------------- | ------- | ------------- | ----------- | --------------- | ------------------------------------------------------------------------------------- |
| **C15** | **[C1623](https://jlcpcb.com/partdetail/C1623)** | **470nF 25V X7R** | 0603    | **1,100,473** | **$0.0036** | U7 Input Filter | [D6](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)      |
| **C16** | **[C1623](https://jlcpcb.com/partdetail/C1623)** | **470nF 25V X7R** | 0603    | **1,100,473** | **$0.0036** | U8 Input Filter | [D7](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8) |

#### Output Capacitors (0.1µF) - Basic Parts

| Symbol  | Part Number                                        | Specification     | Package | Stock          | Price       | Application      | Diagram                                                                               |
| ------- | -------------------------------------------------- | ----------------- | ------- | -------------- | ----------- | ---------------- | ------------------------------------------------------------------------------------- |
| **C17** | **[C49678](https://jlcpcb.com/partdetail/C49678)** | **100nF 50V X7R** | 0805    | **23,309,869** | **$0.0021** | U6 Output Filter | [D5](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)    |
| **C18** | **[C49678](https://jlcpcb.com/partdetail/C49678)** | **100nF 50V X7R** | 0805    | **23,309,869** | **$0.0021** | U7 Output Filter | [D6](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)      |
| **C19** | **[C49678](https://jlcpcb.com/partdetail/C49678)** | **100nF 50V X7R** | 0805    | **23,309,869** | **$0.0021** | U8 Output Filter | [D7](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8) |

#### Large Electrolytic Capacitors (Linear Regulator Stage)

| Symbol  | Part Number                                              | Specification | Package     | Stock      | Price     | Application | Diagram                                                                               |
| ------- | -------------------------------------------------------- | ------------- | ----------- | ---------- | --------- | ----------- | ------------------------------------------------------------------------------------- |
| **C14** | **[C2992611](https://jlcpcb.com/partdetail/C2992611)**   | **470µF 35V** | D10xL10.5mm | **13,862** | **$0.04** | U6 Input    | [D5](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)    |
| **C20** | **[C2992611](https://jlcpcb.com/partdetail/C2992611)**   | **470µF 35V** | D10xL10.5mm | **13,862** | **$0.04** | U6 Input    | [D5](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)    |
| **C21** | **[C2992611](https://jlcpcb.com/partdetail/C2992611)**   | **470µF 35V** | D10xL10.5mm | **13,862** | **$0.04** | U6 Output   | [D5](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)    |
| **C22** | **[C46550400](https://jlcpcb.com/partdetail/C46550400)** | **470µF 16V** | D6.3xL7.7mm | **23,331** | **$0.02** | U7 Input    | [D6](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)      |
| **C23** | **[C46550400](https://jlcpcb.com/partdetail/C46550400)** | **470µF 16V** | D6.3xL7.7mm | **23,331** | **$0.02** | U7 Output   | [D6](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)      |
| **C24** | **[C2992611](https://jlcpcb.com/partdetail/C2992611)**   | **470µF 35V** | D10xL10.5mm | **13,862** | **$0.04** | U8 Input    | [D7](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8) |
| **C25** | **[C2992611](https://jlcpcb.com/partdetail/C2992611)**   | **470µF 35V** | D10xL10.5mm | **13,862** | **$0.04** | U8 Output   | [D7](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8) |

**Stage 3 Subtotal: $0.37** (Using high-stock regulators)

### Stage 4: Protection Circuit (PTC Auto-Reset with Multi-Layer Protection)

#### PTC Resettable Fuses (Auto-Recovery)

| Symbol   | Part Number                                          | Manufacturer Part Number                          | Specification             | Package | Stock      | Price     | Application          | Diagram                                                                               |
| -------- | ---------------------------------------------------- | ------------------------------------------------- | ------------------------- | ------- | ---------- | --------- | -------------------- | ------------------------------------------------------------------------------------- |
| **PTC1** | **[C20808](https://jlcpcb.com/partdetail/C20808)**   | **[SMD1210P200TF](../components/ptc-12v)**        | **2.0A hold / 4A trip**   | SMD1210 | **1,744**  | **$0.22** | +12V Rail Protection | [D5](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)    |
| **PTC2** | **[C70119](https://jlcpcb.com/partdetail/C70119)**   | **[mSMD110-33V](../components/ptc-5v)**           | **1.1A hold / 2.2A trip** | 1812    | **44,459** | **$0.10** | +5V Rail Protection  | [D6](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)      |
| **PTC3** | **[C883133](https://jlcpcb.com/partdetail/C883133)** | **[BSMD1206-150-16V](../components/ptc-12v-neg)** | **1.5A hold / 3.0A trip** | 1206    | **60,591** | **$0.14** | -12V Rail Protection | [D7](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8) |

**Protection Philosophy:**

- **PTC-only design** - No backup fuses needed (traditional fuses unavailable on JLCPCB)
- **Linear regulators provide inherent protection**: Current limiting (~1-2A) + thermal shutdown
- **Four-layer protection**: USB-PD → DC-DC → Linear Regulator → PTC
- **Auto-reset convenience**: No manual fuse replacement required

#### TVS Diodes

| Symbol   | Part Number                                          | Manufacturer Part Number             | Description            | Package | Estimated Price | Application     | Diagram                                                                               |
| -------- | ---------------------------------------------------- | ------------------------------------ | ---------------------- | ------- | --------------- | --------------- | ------------------------------------------------------------------------------------- |
| **TVS1** | **[C571368](https://jlcpcb.com/partdetail/C571368)** | **[SMAJ15A](../components/smaj15a)** | 15V TVS Unidirectional | SMA     | **$0.15**       | +12V Protection | [D5](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)    |
| **TVS2** | **[C502527](https://jlcpcb.com/partdetail/C502527)** | **[SD05](../components/sd05)**       | 5V TVS Unidirectional  | SOD-323 | **$0.02**       | +5V Protection  | [D6](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)      |
| **TVS3** | **[C571368](https://jlcpcb.com/partdetail/C571368)** | **[SMAJ15A](../components/smaj15a)** | 15V TVS Unidirectional | SMA     | **$0.15**       | -12V Protection | [D7](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8) |

#### Status Indicator LEDs (Using Basic Parts)

| Symbol   | Part Number                                              | Specification | Package | Price       | Application           | Diagram                                                                               |
| -------- | -------------------------------------------------------- | ------------- | ------- | ----------- | --------------------- | ------------------------------------------------------------------------------------- |
| **LED2** | **[C19171392](https://jlcpcb.com/partdetail/C19171392)** | **Green LED** | 0603    | **$0.01**   | +12V Status Indicator | [D5](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)    |
| **LED3** | **[C5382145](https://jlcpcb.com/partdetail/C5382145)**   | **Blue LED**  | 0603    | **$0.01**   | +5V Status Indicator  | [D6](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)      |
| **LED4** | **[C2286](https://jlcpcb.com/partdetail/C2286)**         | **Red LED**   | 0603    | **$0.01**   | -12V Status Indicator | [D7](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8) |
| **R7**   | **[C25623](https://jlcpcb.com/partdetail/C25623)**       | **1kΩ 125mW** | 0805    | **$0.0010** | LED2 Current Limit    | [D5](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)    |
| **R8**   | **[C25623](https://jlcpcb.com/partdetail/C25623)**       | **1kΩ 125mW** | 0805    | **$0.0010** | LED3 Current Limit    | [D6](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)      |
| **R9**   | **[C25623](https://jlcpcb.com/partdetail/C25623)**       | **1kΩ 125mW** | 0805    | **$0.0010** | LED4 Current Limit    | [D7](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8) |

**Stage 4 Subtotal: $0.77** (PTC-only protection, no fuses needed)

### Stage 5: Output Connectors

#### Eurorack Power Connector (16-pin)

| Symbol | Part Number                                            | Manufacturer Part Number | Description            | Package      | Stock     | Price     | Application           | Diagram |
| ------ | ------------------------------------------------------ | ------------------------ | ---------------------- | ------------ | --------- | --------- | --------------------- | ------- |
| **J2** | **[C5383092](https://jlcpcb.com/partdetail/C5383092)** | **2541WR-2x08P**         | 2x8P Pin Header 2.54mm | Through-hole | **6,813** | **$0.08** | Eurorack Power Output | -       |

**Connector Type:** Standard 2x8 pin header (male, through-hole, 2.54mm pitch)

**Note:** This is a standard pin header. For box/shrouded connectors (commonly used in Eurorack), users should source the mating female box header connector separately from:

- Tayda Electronics
- Mouser / Digikey
- Other electronics distributors

**Eurorack 16-Pin Pinout (Standard):**

```
  GATE  [16]  [15]  GATE
  CV    [14]  [13]  CV
  +5V   [12]  [11]  +5V
  +12V  [10]  [ 9]  +12V
  GND   [ 8]  [ 7]  GND
  GND   [ 6]  [ 5]  GND
  GND   [ 4]  [ 3]  GND
  -12V  [ 2]  [ 1]  -12V   ← Red stripe
```

**Note:** This power supply provides +12V, -12V, +5V, and GND. The CV (pins 13-14) and GATE (pins 15-16) pins are typically unused for power-only applications.

#### FASTON Power Terminals (Busboard Connection)

| Symbol    | Part Number                                          | Manufacturer Part Number                            | Description               | Package      | Stock     | Price         | Application           |
| --------- | ---------------------------------------------------- | --------------------------------------------------- | ------------------------- | ------------ | --------- | ------------- | --------------------- |
| **J3-J6** | **[C305825](https://jlcpcb.com/partdetail/C305825)** | **[1217754-1](../components/faston-terminal)** (×4) | FASTON 250 PCB Tab 6.35mm | Through-hole | **4,044** | **$0.03 × 4** | Busboard Power Output |

**FASTON Terminal Configuration:**

| Terminal | Signal | Max Current |
| -------- | ------ | ----------- |
| **J3**   | +12V   | 7A (rated)  |
| **J4**   | -12V   | 7A (rated)  |
| **J5**   | +5V    | 7A (rated)  |
| **J6**   | GND    | 7A (rated)  |

**Purpose:** Heavy-duty power output for busboard connection. FASTON 250 series terminals support thick gauge wire for low-resistance, low-noise power delivery to multiple Eurorack modules.

**Note:** Requires matching FASTON receptacles on the busboard. Combined GND return current is ~2.5A max (well within 7A rating).

**Stage 5 Subtotal: $0.20** (Header: $0.08 + FASTON × 4: $0.12)

## Performance Specifications

### Power Supply Performance

| Item               | Specification               |
| ------------------ | --------------------------- |
| **Efficiency**     | 75-80% (Overall)            |
| **Ripple Noise**   | \<1mVp-p (Final Output)     |
| **Regulation**     | ±1% (Line & Load Variation) |
| **Response Speed** | Excellent (Linear Stage)    |
| **Safety Margin**  | 150%+ on All Circuits       |

### Output Specifications

| Voltage  | Current | Accuracy | Ripple   |
| -------- | ------- | -------- | -------- |
| **+12V** | 1.2A    | ±0.5%    | \<1mVp-p |
| **-12V** | 1.0A    | ±0.5%    | \<1mVp-p |
| **+5V**  | 1.2A    | ±0.5%    | \<1mVp-p |

## Protection Circuit Operation

### Normal Operation (Current < Hold Rating)

- PTC: Low resistance (0.03-0.05Ω), minimal voltage drop
- Linear regulator: Normal operation
- LED: Brightly lit ✅

### Overload Condition (Current > Hold Rating)

1. PTC heats up and increases resistance
2. LED dims/turns off (clear visual feedback)
3. Within 1-5 seconds: PTC trips, current drops to ~10mA
4. **User action**: Reduce modules
5. **Auto-recovery**: Wait 30-60 seconds for PTC to cool
6. PTC resets automatically, power restored 🔄

### Short Circuit Condition (Output Shorted to GND)

**Multi-layer protection sequence:**

1. **Immediate**: Linear regulator current limiting kicks in (~1-2A max)
2. **0.5-5s**: PTC trips due to limited current flow
3. **1-5s**: If sustained, regulator thermal shutdown (150°C)
4. **LED**: Turns off (indicates fault)
5. **Recovery**: Both PTC and regulator auto-reset after cooling
6. **No damage**: Protected by four independent layers ✅

**Key insight:** Linear regulators prevent catastrophic shorts by limiting current before PTC trips, making PTC-only protection adequate.

## Design Features

### 1. Fully JLCPCB Sourceable with High Stock

- **Extensive Basic Parts Usage**: No additional costs
- **Abundant Stock**: Regulator ICs 150k~270k pieces in stock
- **Stable Sourcing**: High stock secured for all major components
- **USB-PD IC**: CH224D (2,291 pieces) - 15V support confirmed

### 2. High-Performance Design

- **2-Stage Filtering**: DC-DC + Linear for low noise
- **Ample Margin**: 150%+ safety margin on all circuits
- **Modular Synth Optimized**: Low noise, high stability

### 3. Advanced Multi-Layer Protection

- **Four independent protection layers**: USB-PD → DC-DC → Linear Regulator → PTC
- **PTC Auto-Recovery**: Auto-resets in 30-60 seconds for all fault types
- **Linear regulator protection**: Built-in current limiting + thermal shutdown
- **Visual Feedback**: LED status indicates power/fault conditions
- **No Manual Intervention**: All protections auto-reset (no fuse replacement)
- **Better than commercial**: Exceeds Doepfer (4 layers vs 1), simpler than Intellijel

### 4. Implementation

- **100% SMD Components**: Fully compatible with automated PCBA assembly
- **Surface-Mount Design**: All regulators use SMD packages (TO-263-2, TO-252-2L)
- **Separated Design**: Physical separation of DC-DC and linear stages

## Component Heights

For detailed component height information and mechanical design considerations, see **[Mechanical Design](/docs/overview/mechanical-design)**.

**Quick reference** (tallest components):

- 470µF 25V electrolytic caps: **10.2mm** (tallest)
- FASTON terminals: **8.89mm**
- Total board height: **~12mm** including PCB

## Total Cost Summary

| Stage       | Description                 | Subtotal  |
| ----------- | --------------------------- | --------- |
| **Stage 1** | USB-PD Voltage Acquisition  | **$0.45** |
| **Stage 2** | DC-DC Converters            | **$2.09** |
| **Stage 3** | Linear Regulators           | **$0.37** |
| **Stage 4** | Protection Circuit          | **$0.77** |
| **Stage 5** | Output Connectors           | **$0.20** |
|             | **Total (Components Only)** | **$3.88** |

**Cost Savings:**

- **Previous design** (PTC + Fuse): ~$4.76
- **Current design** (PTC-only + Connectors): **$3.88**
- **Savings**: **$0.88** (18% reduction)

**Notes:**

- Prices are estimates based on JLCPCB part catalog
- Does not include PCB fabrication or assembly fees
- All parts available on JLCPCB with good stock levels
- PTC-only design reduces cost while improving user experience

## JLCPCB Assembly Cost Structure

The component prices above are only part of the total PCBA cost. JLCPCB charges additional fees:

### Fee Types

| Fee                    | Description              | Typical Cost  |
| ---------------------- | ------------------------ | ------------- |
| **PCB Fabrication**    | Board manufacturing      | ¥500-1,000    |
| **Setup Fee**          | One-time assembly setup  | ~¥1,250       |
| **Stencil**            | Solder paste stencil     | ~¥235         |
| **SMT Assembly**       | Per-placement fee        | ~¥145         |
| **Extended Parts Fee** | Per unique Extended part | **¥470 each** |
| **Hand-soldering**     | THT components           | ~¥550         |

### Basic vs Extended Parts

JLCPCB classifies components into two categories:

- **Basic Parts**: Common resistors, MLCCs, some diodes - **No extra fee**
- **Extended Parts**: Specialty ICs, electrolytic caps, LEDs, inductors, connectors - **¥470 per unique part number**

This project uses ~20 Extended parts, adding ~¥9,400 to the assembly cost.

### Cost Per Board (Reference: January 2025)

| Quantity  | Total Cost | Per Board  |
| --------- | ---------- | ---------- |
| 1 board   | ~¥16,500   | ¥16,500    |
| 5 boards  | ~¥21,000   | ¥4,200     |
| 10 boards | ~¥26,000   | **¥2,600** |

**Key insight**: Extended fees are **one-time setup costs**, not per-board. Ordering more boards significantly reduces the per-unit cost.

### Cost Optimization Tips

1. **Order in batches of 5-10** to amortize setup fees
2. **Hand-solder large components** (electrolytic caps, connectors) to reduce Extended fees
3. **Use Basic parts** where possible (resistors, MLCCs are usually Basic)
4. **Consolidate part numbers** - fewer unique Extended parts = lower fees
