---
title: Project Status and Plan
sidebar_position: 2
---

# Project Status and Plan

Current progress and future plans for the USB-PD powered modular synthesizer power supply.

## 🎯 Project Goal

**Low-noise power module supplying ±12V/+5V for modular synths from USB-C PD 15V input**

- Protection circuit safe for modular synth beginners
- All parts available from JLCPCB (stable supply, low cost)
- Low-noise design with &lt;1mVp-p ripple
- Easy to use with USB-C PD

## ✅ Completed Items

### 1. Circuit Design (100% Complete)

**4-Stage Architecture Completed**:

```
USB-C 15V ──┬─→ +13.5V (DC-DC) ──→ +12V (LDO) ──→ +12V OUT
            │
            ├─→ +7.5V  (DC-DC) ──→ +5V  (LDO) ──→ +5V OUT
            │
            └─→ -15V (Inverter) ──→ -13.5V (DC-DC) ──→ -12V (LDO) ──→ -12V OUT
```

- ✅ Stage 1: USB-PD Power Supply (STUSB4500)
- ✅ Stage 2: DC-DC Converters (LM2596S × 3 + LM2586 inverted SEPIC)
- ✅ Stage 3: Linear Regulators (LM7812/7805/7912)
- ✅ Stage 4: Protection Circuit (PTC + Fuse + TVS)

### 2. Parts Selection (100% Complete) ✅

**All parts confirmed**: All JLCPCB part numbers finalized

- ✅ USB-PD Controller: STUSB4500 (C2678061)
- ✅ DC-DC Converter: LM2596S-ADJ × 3 (C347423)
- ✅ Voltage Inverter: LM2586SX-ADJ/NOPB (C181324)
- ✅ Linear Regulators: L7812CV-DG (C2914) / L7805ABD2T-TR (C86206) / CJ7912 (C94173)
- ✅ Inductors: 100µH 4.5A × 3 (C19268674)
- ✅ TVS Diodes: SMAJ15A, SD05
- ✅ Fuses: 1.5A × 2 confirmed (C95352)

~~**Unconfirmed Parts**~~ **→ All Confirmed!** ✅

- ✅ PTC Resettable Fuses × 3
  - PTC1: 1.1A 16V (1812) → **C883148** (BSMD1812-110-16V)
  - PTC2: 0.75A 16V (1206) → **C883128** (BSMD1206-075-16V)
  - PTC3: 0.9A→1.1A 16V (1812) → **C883148** (BSMD1812-110-16V) ※
- ✅ 2A SMD Fuse × 1 (for +12V) → **C5183824** (6125FA2A)

**※** 0.9A part out of stock. 1.1A provides sufficient protection margin for -12V actual load of 800mA.

### 3. Documentation (100% Complete)

- ✅ Complete circuit diagrams (all 10 stages)
- ✅ Detailed BOM (with JLCPCB part numbers)
- ✅ Design philosophy and architecture explanation
- ✅ Protection circuit operation description

### 4. Cost Estimation (100% Complete) ✅

**Total with all parts confirmed**: **$4.68/board**

- Stage 1: $0.43
- Stage 2: $2.09
- Stage 3: $0.37
- Stage 4: $1.79 (all parts confirmed price)

## 🔄 Current Status

### Where Are We Now?

**Circuit design and parts selection phases complete** → **Next: PCB design phase**

Current state:

1. ✅ Circuit design complete - Working design finalized
2. ✅ **All parts selection complete** - JLCPCB part numbers confirmed (100%), optimized to high-stock parts
3. ✅ **BOM fully confirmed** - Cost $4.68/board
4. ⏳ PCB design not started - KiCad board design is next ← **This is next!**
5. ⏳ Prototype not manufactured - JLCPCB order not yet placed

### What's Next?

**All parts confirmed! KiCad PCB design is the next step**

Ready to proceed:

1. ✅ **Complete BOM** - All parts have JLCPCB part numbers (all optimized to high-stock parts)
- Benefit: Footprint assignment possible
- Benefit: Accurate Gerber/BOM generation in one shot
- Benefit: All parts have 158K~272K stock for long-term procurement stability

2. ✅ **Cost confirmed** - $4.68/board
- Prototype order estimates can be calculated accurately

3. 📐 **Next Action**: Create KiCad project
- Schematic entry → Footprint assignment → PCB layout

## 📋 Next Steps (Priority Order)

### 🔴 Priority: High - Do Immediately

#### ~~Step 1: Search for Unconfirmed Parts~~ ✅ **Complete!**

**Parts found**:

1. ✅ PTC Resettable Fuses × 3 types
- PTC1 (1.1A 16V, 1812): **C883148** - Stock: 11,029
- PTC2 (0.75A 16V, 1206): **C883128** - Stock: 51,532
- PTC3 (1.1A 16V, 1812): **C883148** - Stock: 11,029 ※0.9A part unavailable

2. ✅ SMD Fuse (2A 250V)
- **C5183824** (6125FA2A, 2410 package) - Stock: 744

#### ~~Step 2: Finalize BOM~~ ✅ **Complete!**

- ✅ Part numbers added to `/notes/parts.md`
- ✅ Final cost calculated: **$4.68/board**
- ✅ Reflected in `/doc/do../components/bom.md`
- ✅ All parts optimized to high-stock items (CH224D, L7812/7805, CJ7912)

### 🟡 Priority: Medium - Do Next

#### Step 3: Prepare PCB Design (Time: 2-3 hours) ← **We are here!**

**KiCad Project Setup**:

1. Create new KiCad project
2. Enter circuit in schematic editor
3. Add JLCPCB footprint library
4. Assign footprints to all parts

**Required footprints**:

- `/footprints/CH224D.png` - Already available
- `/footprints/USB-TYPE-C-009.png` - Already available
- Other standard footprints use KiCad standard library

#### Step 4: PCB Board Design (Time: 1-2 days)

**Layout Policy**:

1. **4-Layer Board Structure**:
- Layer 1 (Top): Signals + component placement
- Layer 2 (Inner): GND plane
- Layer 3 (Inner): Power plane (+15V, +12V, etc.)
- Layer 4 (Bottom): Signals

2. **Power Layout**:
- Place USB-PD → DC-DC → LDO in sequence
- Physically separate high-noise (DC-DC) and low-noise (LDO) sections
- Make high-current paths thick and short

3. **Thermal Design**:
- LM2596S (TO-263) → Place thermal vias
- LM78xx/79xx (TO-220) → Reserve heatsink area
- Consider electrolytic capacitor heat dissipation

4. **JLCPCB Design Rules**:
- Minimum trace width: 6mil (0.15mm)
- Minimum clearance: 6mil
- Via diameter: 0.3mm (hole 0.2mm)

### 🟢 Priority: Low - Pre-Prototype Preparation

#### Step 5: Generate Manufacturing Files (Time: 1 hour)

- Generate Gerber files
- Generate Drill files
- Generate BOM file (JLCPCB format)
- Generate CPL file (component placement data)

#### Step 6: Get JLCPCB Quote (Time: 30 minutes)

**Quote contents**:

- PCB manufacturing: 5 or 10 boards
- SMT assembly: both sides or single side
- Parts procurement cost
- Shipping

**Estimated Cost** (for 10 boards):

- PCB manufacturing: ~$30
- SMT assembly: ~$50-100
- Parts cost: ~$50 (for 10 boards)
- Shipping: ~$20
- **Total: $150-200** (10 boards = $15-20 per board)

#### Step 7: Order Prototype (Time: 15 min order + 2 weeks manufacturing)

**Recommended Initial Order**:

- Quantity: 5-10 boards
- SMT assembly: All parts installed
- Delivery: DHL (2-3 weeks)

## PCBA v1 Failure Findings

The first prototype PCBA (v1) failed during testing. The STUSB4500 USB-PD controller did not negotiate power delivery. Root cause analysis identified three issues:

### Issues Found

1. **Pin 18 (VBUS_VS_DISCH) not connected** - This pin was left as NC but must be connected to VBUS_IN via a 470ohm series resistor for VBUS voltage sensing. This is a critical connection required by the datasheet.

2. **Pin 22 (VSYS) floating** - After cutting the incorrect VSYS-to-VREG_2V7 trace, VSYS was left floating. The datasheet requires VSYS to be connected to GND when not used.

3. **Pin 22 (VSYS) shorted to Pin 23 (VREG_2V7)** - A routing error in the original schematic connected these pins together, overloading the internal 2.7V regulator. Fixed by cutting the trace on the PCBA.

### Required Schematic Fixes Before Next Order

- [ ] Add R14 (470ohm) from VBUS_IN to VBUS_VS_DISCH (pin 18)
- [ ] Connect VSYS (pin 22) to GND
- [ ] Verify VREG_2V7 (pin 23) decoupling is correct (C30 only)
- [ ] Run DRC and review all STUSB4500 connections

See the full [PCBA v1 Debug Report](/docs/inbox/pcba-v1-debug) for detailed analysis, bodge wire instructions, and reference design comparison.

## 🤔 Design Concerns and Considerations

### Issues Resolved in Current Design

1. ✅ **Noise countermeasure**: DC-DC + LDO 2-stage design expected to achieve &lt;1mVp-p
2. ✅ **Beginner-friendly**: PTC auto-reset for automatic recovery from overload
3. ✅ **Cost**: Parts cost under $5 using many Basic Parts
4. ✅ **Procurement stability**: All parts have abundant JLCPCB stock

### Items Not Yet Verified (Confirm with Prototype)

1. ⚠️ **Thermal design**: Is LM2596S heat dissipation sufficient?
- Maximum loss: Each 1.5V × 1A = 1.5W
- TO-263 package should handle it but needs actual measurement

2. ⚠️ **Ripple noise**: Can actual measurement achieve &lt;1mVp-p?
- Design should be fine but needs measurement

3. ⚠️ **Efficiency**: Can actual measurement achieve 75-80%?
- LM2596S: 85-90%
- LDO loss: 10-15%
- Calculated overall efficiency: 75-80%

4. ⚠️ **EMI/EMC**: DC-DC switching noise impact?
- Countermeasures with input/output filters but needs measurement

## 📝 Design Philosophy Review

### Why This Design?

1. **DC-DC + LDO 2-Stage Method**
- Reason: Balance efficiency and noise
- DC-DC only: Efficient but high ripple
- LDO only: Low noise but poor efficiency (high heat)
- **2-stage**: Best of both worlds ✨

2. **USB-C PD 15V Input**
- Reason: Can use generic chargers
- No AC adapter needed → Easy to carry
- Any PD-compatible charger works
- 15V voltage optimal for generating ±12V

3. **All Parts from JLCPCB**
- Reason: Stable supply, low cost, automated assembly
- Many Basic Parts → No extra fees
- Abundant stock → Long-term procurement possible
- SMT automated assembly → No hand soldering needed

4. **PTC Auto-Reset Protection**
- Reason: Safe for beginners
- Module overload → Notice when LED goes out
- Auto-reset after 30 seconds → No repair needed
- Fuse for short circuits → Safety ensured

## 🎯 Project Goals

### Final Goal

**"Manufacture beginner-friendly modular synth power supply with JLCPCB for under $20/board"**

### Achievement Criteria

- [ ] Ripple noise &lt;1mVp-p (measured)
- [ ] Efficiency 75-80% (measured)
- [ ] Output voltage accuracy ±1% (measured)
- [ ] Overload protection operation confirmed (LED off → auto-reset)
- [ ] Short circuit protection operation confirmed (fuse blown)
- [ ] Manufacturing cost under $20/board (when ordering 10 boards)

### Secondary Goals

- 📖 Comprehensive English documentation → Contribute to international Maker community
- 🔧 Open-source KiCad project
- 📝 Write build article (Blog/Medium)
- 🎓 Share JLCPCB SMT utilization know-how

## 💡 What You Can Do Now

**After reading this document, you can immediately start**:

1. ~~**5 minutes**: Search for parts~~ ✅ **Complete!**
2. ~~**30 minutes**: Update BOM~~ ✅ **Complete!**
3. **1 hour**: Install KiCad and create new project ← **Start here!**
4. **1 day**: Enter complete circuit in schematic editor

**All parts confirmed! Start with "Step 3: Prepare PCB Design"!** 🚀
