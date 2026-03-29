---
title: Quick Reference
sidebar_position: 5
---

# Quick Reference

A cheat sheet of frequently referenced information during design.

## 🎯 Basic Specifications (At a Glance)

| Item            | Specification                   |
| --------------- | ------------------------------- |
| **Input**       | USB-C PD 15V 3A (Max 45W)       |
| **+12V Output** | 1.5A (max)                      |
| **-12V Output** | 1.0A (max)                      |
| **+5V Output**  | 1.5A (max)                      |
| **Ripple**      | \<1mVp-p                        |
| **Efficiency**  | 75-80%                          |
| **Protection**  | PTC auto-recovery + Fuse backup |

## ⚡ Power Flow (Architecture)

```
USB-C        DC-DC        LDO          Output
15V    →   +13.5V   →   +12V    →   +12V/1.5A
  ↓
  ├──  →   +7.5V    →   +5V     →   +5V/1.5A
  ↓
  └──  →   -13.5V   →   -12V    →   -12V/1.0A
      (Inverting Buck-Boost)
```

## 🔧 Main ICs and Their Roles

| IC           | Part Number   | JLCPCB P/N | Stock   | Role                      | Qty |
| ------------ | ------------- | ---------- | ------- | ------------------------- | --- |
| **USB-PD**   | STUSB4500     | C2678061   | -       | PD Negotiation (15V)      | 1   |
| **DC-DC**    | LM2596S-ADJ   | C347423    | 12,075  | Buck Converter (U2, U3)   | 2   |
| **DC-DC**    | LM2596S-ADJ   | C347423    | 12,075  | Inverting Buck-Boost (U4) | 1   |
| **+12V LDO** | L7812CD2T-TR  | C13456     | 158,795 | +13.5V → +12V             | 1   |
| **+5V LDO**  | L7805ABD2T-TR | C86206     | 272,379 | +7.5V → +5V               | 1   |
| **-12V LDO** | CJ7912        | C94173     | 3,386   | -13.5V → -12V             | 1   |

## 📐 DC-DC Feedback Resistor Values (Voltage Setting)

| Output Voltage | R_upper | R_lower | Actual Output |
| -------------- | ------- | ------- | ------------- |
| **+13.5V**     | 10kΩ    | 1kΩ     | 13.53V        |
| **+7.5V**      | 5.1kΩ   | 1kΩ     | 7.50V         |
| **-13.5V**     | 10kΩ    | 1kΩ     | -13.53V       |

**Formula**: `Vout = 1.23V × (1 + R_upper/R_lower)`

## 🛡️ Protection Circuit Ratings

| Voltage Line | PTC Rating | JLCPCB P/N | Fuse Rating | JLCPCB P/N | TVS Model | Operation                         |
| ------------ | ---------- | ---------- | ----------- | ---------- | --------- | --------------------------------- |
| **+12V**     | 1.1A       | C883148    | 2A          | C5183824   | SMAJ15A   | Overload→PTC / Short circuit→Fuse |
| **+5V**      | 1.1A       | C70119     | 1.5A        | C95352     | SD05      | Same as above                     |
| **-12V**     | 1.1A       | C883148    | 1.5A        | C95352     | SMAJ15A   | Same as above                     |

### Protection Operation Sequence

1. **Normal**: LED on ✅
2. **Overload (110-180% of rating)**: PTC trip → LED off → Recovery after 30 seconds 🔄
3. **Short circuit (200%+ of rating)**: Fuse blown → Repair required ❌

## 🔌 Connectors and Packages

| Component        | Package         | Notes                            |
| ---------------- | --------------- | -------------------------------- |
| STUSB4500        | QFN-24          | USB-PD IC                        |
| USB-C            | USB-TYPE-C-009  | 6-pin (Power only)               |
| LM2596S          | TO-263-5        | Surface mount, large thermal pad |
| L7812/L7805      | TO-220/TO-263-2 | Heatsink compatible              |
| CJ7912           | TO-252-2L       | Surface mount                    |
| Inductor         | SMD 13.8x12.8mm | 100µH 4.5A                       |
| Electrolytic Cap | φ6.3mm / φ10mm  | Select by diameter               |

## 💰 Cost Breakdown (Per Board)

| Stage       | Content              | Cost      |
| ----------- | -------------------- | --------- |
| **Stage 1** | USB-PD Power Section | $0.43     |
| **Stage 2** | DC-DC Converters     | $2.09     |
| **Stage 3** | Linear Regulators    | $0.37     |
| **Stage 4** | Protection Circuits  | $1.79     |
| **Total**   | Component Cost       | **$4.68** |

※ PCB manufacturing and assembly costs are separate (approx. $15-20/board for 10-piece order)

## 📊 Component Stock Status (JLCPCB)

| Component Category               | Minimum Stock     | Availability   |
| -------------------------------- | ----------------- | -------------- |
| Basic Parts Resistors/Capacitors | **1,000,000+**    | ✅ Very Stable |
| STUSB4500 (USB-PD)               | -                 | ✅ Stable      |
| LM2596S (DC-DC)                  | **12,075**        | ✅ Stable      |
| L7812/L7805/CJ7912 (LDO)         | **3,386~272,379** | ✅ Very Stable |
| Inductor (100µH)                 | **2,763**         | ✅ Stable      |
| SS34 (Diode)                     | **1,859,655**     | ✅ Very Stable |

## 🔬 Detailed Performance Specifications

### Ripple Noise Target

| Stage        | Expected Ripple | Countermeasure               |
| ------------ | --------------- | ---------------------------- |
| DC-DC Output | ~50mVp-p        | 470µF electrolytic capacitor |
| LDO Output   | **\<1mVp-p**    | LDO + 470µF×2                |

### Efficiency Calculation

| Stage       | Efficiency | Loss Example                    |
| ----------- | ---------- | ------------------------------- |
| LM2596S     | 85-90%     | 15V→13.5V: 1.5V × 1A = 1.5W     |
| LM7812      | ~90%       | 13.5V→12V: 1.5V × 1A = 1.5W     |
| LM7805      | ~67%       | 7.5V→5V: 2.5V × 0.5A = 1.25W    |
| LM7912      | ~89%       | -13.5V→-12V: 1.5V × 0.8A = 1.2W |
| **Overall** | **75-80%** | Max loss ~10W                   |

## 🌡️ Thermal Design Estimation

### Maximum Heat-Generating Components

| IC           | Max Loss | Package | Thermal Resistance | Temperature Rise |
| ------------ | -------- | ------- | ------------------ | ---------------- |
| LM2596S (×3) | 1.5W     | TO-263  | ~10℃/W             | +15℃             |
| LM7805       | 1.25W    | TO-220  | ~5℃/W              | +6℃              |
| LM7812       | 1.5W     | TO-220  | ~5℃/W              | +7.5℃            |
| LM7912       | 1.2W     | TO-220  | ~5℃/W              | +6℃              |

※ Approx. 40-50℃ max at 25℃ ambient (within acceptable range)

## 🛠️ PCB Design Guidelines

### Layout Principles

1. **Separate high-noise and low-noise sections**
- DC-DC section: Left side of board
- LDO section: Right side of board
- Consider GND plane separation

2. **Make high-current paths thick and short**
- USB input: Minimum 1mm width
- +12V/-12V: Minimum 0.8mm width
- +5V: Minimum 0.5mm width

3. **Thermal via placement**
- LM2596S (TO-263): 4-6 vias under pad
- LM78xx/79xx: As needed

4. **Capacitor placement**
- Input capacitors: Close to IC
- Output capacitors: Near load terminals
- Electrolytic capacitors: Mind polarity

### Recommended Layer Stack (4-layer board)

| Layer           | Purpose             | Notes              |
| --------------- | ------------------- | ------------------ |
| **L1 (Top)**    | Signal + Components | SMD component side |
| **L2 (GND)**    | GND Plane           | Solid GND          |
| **L3 (Power)**  | Power Plane         | +15V/+12V/+5V/-12V |
| **L4 (Bottom)** | Signal              | Routing auxiliary  |

## 📝 Open Items Checklist

- [x] ~~PTC1: 1.1A 16V (1812)~~ - **C883148 (BSMD1812-110-16V)** ✅
- [x] ~~PTC2: 0.75A 16V (1206)~~ - **C883128 (BSMD1206-075-16V)** ✅
- [x] ~~PTC3: 0.9A 16V (1812)~~ - **C883148 (BSMD1812-110-16V) ※Using 1.1A** ✅
- [x] ~~F1: 2A 250V SMD fuse~~ - **C5183824 (6125FA2A)** ✅
- [x] ~~Stock optimization~~ - **All components changed to high-stock parts** ✅
  - USB-PD: STUSB4500
  - LDO: L7812/L7805/CJ7912 (3K~272K stock)
- [ ] PCB design (KiCad) - Not started
- [ ] Prototype order - Not implemented
- [ ] Performance testing (ripple/efficiency/thermal) - Not implemented

**🎉 All JLCPCB part numbers confirmed and optimized for high-stock parts! PCB design is next.**

## 🔗 Reference Links

### JLCPCB

- Parts Library: https://jlcpcb.com/parts
- SMT Assembly: https://jlcpcb.com/smt-assembly
- Design Rules: https://jlcpcb.com/capabilities/pcb-capabilities

### Datasheets

- STUSB4500: STMicroelectronics (15V support confirmed)
- LM2596S: Texas Instruments
- L7812/L7805: STMicroelectronics
- CJ7912: CJ (Changjiang Micro-Electronics)

### KiCad

- Official website: https://www.kicad.org/
- JLCPCB library: GitHub search "JLCPCB KiCad library"

## 💡 Frequently Asked Questions (FAQ)

### Q: Why use 2-stage DC-DC and LDO?

**A**: To balance efficiency and noise

- DC-DC only: Good efficiency (85%+) but high ripple (50mVp-p)
- LDO only: Low noise (\<1mVp-p) but poor efficiency (50-60%), high heat
- **2-stage**: DC-DC for efficiency + LDO for noise reduction = 75%+ efficiency with \<1mVp-p ripple ✨

### Q: Why use LM2596S inverting buck-boost for -12V?

**A**: Simpler and more reliable than flyback converters

- **Current requirement**: -12V rail needs 800mA (charge pumps like ICL7660 only provide ~100mA)
- **Inverting buck-boost advantages**:
  - Uses same LM2596S IC as other DC-DC stages (reduces BOM complexity)
  - Single-stage conversion (+15V → -13.5V directly)
  - No flyback transformer required (simpler, lower cost)
  - No FB pin voltage violations (previous LM2586 flyback design had this issue)
- **Trade-off**: Slightly lower efficiency (~75%) vs regular buck, but much simpler than flyback
- Alternative charge pumps insufficient: ICL7660 (100mA), TPS63700 (360mA but 5.5V max input) ❌

### Q: Is 2-stage protection with PTC and fuse really necessary?

**A**: Very important for beginner users

- **PTC**: Auto-recovery during overload (too many modules) → User can resolve
- **Fuse**: Final defense during short circuit → Fire prevention
- Cost increase: Only $0.50/board → Worth it for safety ✅

### Q: Is 4-layer board necessary? Can't use 2-layer?

**A**: 2-layer is possible, but 4-layer recommended

- **2-layer**: Difficult noise control, complex routing
- **4-layer**: GND/Power planes reduce noise, easier routing
- Cost difference: About $5-10/board → Worth it for performance
- **Recommendation**: 4-layer for prototype, consider 2-layer for production

### Q: What should I start with right now?

**A**: Start from "Step 3" in [Project Status and Plan](current-status.md)!

1. ~~Search JLCPCB Parts Library for PTC~~ ✅ **Done!**
2. ~~Add to `/notes/parts.md`~~ ✅ **Done!**
3. Install KiCad (15 minutes) ← **This is next!**
4. Start schematic entry (1-2 hours)

**→ All components confirmed! Let's start "PCB Design Preparation"!** 🚀
