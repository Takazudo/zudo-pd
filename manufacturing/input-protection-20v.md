# 20 V input protection for Board P: clamp vs STUSB4500 limits (L7 screen)

**Status: desk analysis only. Nothing here is adopted.** No schematic, PCB, BOM, NVM or part selection changes. Every schematic and PCB stays an unvalidated draft. **Nothing on this page is measured.** This page serves the OSC-recommended direction D3-A (20 V contract at ≥ 3.38 A, preferably 20 V / 5 A) with D5-1 (accept or refuse, no partial supply). That direction is a recommendation pending the user's decision. It is not adopted.

Figures come from [`../scripts/pcb/calculate-input-ovp-20v.py`](../scripts/pcb/calculate-input-ovp-20v.py). This page extends [`input-clamp-fix.md`](input-clamp-fix.md) (PD-CLAMP-2 scope) and bounds, but does not close, GAP-1 in [`design-gaps-20v.md`](design-gaps-20v.md). GAP-2 is bounded but not closed.

Evidence classes: **G** guaranteed in a manufacturer table retrieved from the manufacturer's public site, with bytes and hash recorded below · **G-U** guaranteed, but read only from a mirror or a summarizing fetch · **TYP** typical · **PA** project assumption · **UNAV** unavailable.

## 1. Limits and requirement

| Item | Value | Class |
|---|---|---|
| STUSB4500 VDD, VBUS_EN_SNK, VBUS_VS_DISCH, DISCH, POWER_OK2 absolute maximum | 28 V | G-U (DS12499 Rev 8 Table 20, owner-bundle mirror; st.com refused direct download again on 2026-10-31) |
| STUSB4500 CC1/CC2/CC1DB/CC2DB absolute maximum | 22 V | G-U, same source |
| Highest legitimate VBUS on a 20 V PDO | 21.0 V (±5 %) | PA (no USB PD primary text retained) |
| Requirement (not relaxed) | Every 28 V-group pin stays ≤ 28 V across the surge envelope and temperature. CC stays ≤ 22 V for a single CC-to-VBUS fault | Project gate GAP-1 / GAP-2 |

The surge envelope (waveform, energy, source and cable inductance, repetition) is still undefined. Margins below hold for the stated mechanism only.

## 2. Topologies compared

| ID | Topology | Exact candidates | Bound on the 28 V-group pins | Verdict |
|---|---|---|---|---|
| T1 | One passive TVS on VBUS (lower clamp) | TI **TVS2200** (DRV, VRWM 22 V, VBR 24.6–27.6 V at 1 mA, VC ≤ 28.0 V at 40 A 8/20 µs 27 °C, **≤ 28.35 V at 35 A, VIN = VRWM before surge, 125 °C**; G). TI TVS2700 (SLVSED6A) has a higher clamp, so it is worse | 28.35 V hot | **FAIL** (−0.35 V hot; 0.00 V at 27 °C). No passive part with VBR ≥ 21 V and a guaranteed hot clamp ≤ 28 V was found |
| T2 | T1 plus a per-pin series R and zener (b′) | TVS2200 + 470 Ω + BZX84-C24 on VDD / VBUS_VS_DISCH / DISCH / VBEN | 25.7–27.8 V (PA model) | **EDGE**: +0.2 to +1.4 V hot. It depends on the PA zener model. BZX84 hot leakage cannot be closed from the datasheet. The Nexperia PDF returned 403 on 2026-10-31, so the 2026-10-20 reading (no bytes retained) stands |
| T3 | **Active OVP eFuse ahead of the whole of Board P** (STUSB4500 supply and sense pins, Q1, Board B), with a connector-side TVS taking the surge energy and bulk capacitance on the protected node | TI **TPS26630RGER** (TPS2663x, SLVSE94G, G; orderable Active per the datasheet addendum); connector TVS: TVS2200 (G) or a higher-energy SMA TVS with VC ≤ 60 V (no exact part retrieved, UNAV) | 24.7 V at C_eff 100 µF on TYP fast-trip and PA ESR; 27.7–29.6 V at 80 µF with ESR 0.3–0.5 Ω; guaranteed only to the TVS clamp, 28.35 V hot | **BLOCKING** (L7): the margin rests on TYP and PA terms; see 2.1 |
| T3′ | As T3 with TI TPS16630 (SLVSET9G, G): same OVP, I(OL), timing and RON, but no reverse-current blocking | TPS16630 | as T3 | As T3, without the R7.3 back-feed block |
| T4 | Controller with OVP and back-to-back NFETs, no current limit | TI LM74502 (SNOSDE5A, G): OV threshold 1.165 / 1.25 / 1.333 V (±6.8 %) | Trip window ±6.8 % → the minimum trip of 21.5 V puts the maximum near 24.6 V, before overshoot. No current limit to bound the overshoot charge | Worse than T3; not recommended |
| T5 | Different sink controller (VBUS-side 30 V class) | Infineon CYPD3177 (CC 22 V), Diodes AP33772S | Moves the VBUS limit only | Controller decision (PD-003-D3), outside L7; not re-screened |

### 2.1 T3 mechanism and arithmetic

In T3, the STUSB4500 is powered and senses VBUS **behind** the eFuse. The eFuse stays enabled from attach at 5 V, so negotiation works. Q1 (or its successor) still gates Board B through VBUS_EN_SNK. The protected node is bounded in two stages:
1. The OVP comparator turns the FET off after the input crosses the trip.
2. Until then, the eFuse current regulation limits the charge pushed into the protected-node bulk.

| Quantity | Value | Class |
|---|---|---|
| OVP comparator V(OVPR) | 1.176 / 1.2 / 1.224 V (±2 %) | G (SLVSE94G §6.5) |
| OVP falling threshold V(OVPF) | 1.09 / 1.122 / 1.15 V | G |
| OVP_tOFF(dly), OVP rising to FLT low | 8.5 / 11 / **14 µs** | G. That the FET is off by FLT low is PA |
| I(OL) at R(ILIM) = 4.02 kΩ | 4.185 / 4.5 / 4.815 A | G |
| Fast-trip threshold | 2 × I(OL) (TPS26630/TPS26632) | TYP column |
| Short-circuit fast trip | I(SCP) 45 A, turn-off about 1 µs | TYP |
| RON | 19 / 30.44 / 53 mΩ (−40…125 °C) | G |
| Reverse-current comparator | V(REVTH) −20 / −15 / −9 mV; fast turn-off 0.17 / 0.37 µs (external blocking NFET on B_GATE) | G |
| Absolute maximum | IN_SYS −60…67 V | G |
| Divider error, two 0.1 % resistors | ±0.2 % | PA |
| Bulk ESR on the protected node | 30 mΩ | PA |

Calculated results:
- **Trip window.** With the minimum trip set to 21.0 V + 0.5 V guard (PA), the nominal is 21.98 V and the trip lies at **21.50–22.47 V**.
- **Overshoot charge.** At most 2 × 4.815 A × 14 µs = 134.8 µC through the window, plus 45 A × 1 µs = 45 µC for a fast trip (TYP). The load current that discharges the node at the same time is ignored, which is conservative.
- **Protected node.** Trip maximum + Q / C_eff + I_peak × ESR, capped by the connector clamp:

| C_eff on the protected node (after DC bias and temperature) | ΔV | Node maximum | Margin to 28 V |
|---:|---:|---:|---:|
| 47 µF | 4.11 V | 26.68 V | +1.32 V |
| 100 µF | 2.09 V | 24.65 V | +3.35 V |
| 220 µF | 1.11 V | 23.67 V | +4.33 V |

These rows start from the fitted 174k/10k trip maximum, 22.57 V. They are **not a bound**:
I(SCP) 45 A and the 1 µs hot-short response are TYP with no maximum, and the 30 mΩ ESR is a
project assumption with no RVT1H101M0810 ESR fact in the owner bundle. At the 80 µF
minimum of the fitted C3 (independent review finding 4, recomputed by the script):

| Case at C_eff 80 µF | Node maximum | Margin to 28 V |
|---|---:|---:|
| TYP charge, ESR 30 mΩ (PA) | 25.10 V | +2.90 V |
| TYP charge, ESR 0.3 Ω | 27.70 V | +0.30 V |
| TYP charge, ESR 0.5 Ω | 29.63 V | **−1.63 V** |
| Soft-short response 4.5 µs maximum (SLVSE94G EC table) at I(SCP) TYP | 27.07 V | +0.93 V |

**Gate L7 stays BLOCKING.** The only guaranteed bound is the connector node at the
TVS2200 clamp, 28.0 V at 27 °C and 28.35 V at 125 °C: 0.00 V and −0.35 V of margin.
Closing L7 needs a guaranteed C3 ESR (or a low-ESR bulk with a datasheet ESR row) and a
bounded short-circuit current, or a node clamp with a guaranteed hot clamp at or below 28 V.

- **Before the contract, Q1 is off and Board B's bulk is not on the node.** Board P carries only C1 10 µF today, so T3 needs its own bulk of at least 100 µF effective on the protected node: a size and part choice that is UNAV. A small node clamp (for example TVS2200, VBR min 24.6 V) is optional. It only acts in the ΔV region and never conducts at 21 V.
- **Current limit vs contract.** At the 20 V / 5 A PDO, the 4.02 kΩ setting is 4.185–4.815 A. That lies above the 3.38 A worst legitimate draw (+0.805 A, calc on PA efficiencies) and below the 5 A contract and cable rating. The eFuse therefore also enforces the input contract. At a 3.5 A PDO no ±7 % setting fits between 3.38 and 3.5 A, so the charger's OCP would remain the contract limit.
- **Loss and other parts.** Loss at 3.38 A is 0.61 W at RON maximum. On the JEDEC RθJA of 31.4 °C/W (SLVSE94G, RGE package) that is about a 19 °C rise; installed θJA is UNAV. Q1 and the Board B input see at most the node bound, which also removes the AO3401A 30 V VDS concern. The connector side only has to stay below 67 V, so a higher-energy SMA TVS becomes admissible there.
- **OV recovery.** After an OV event, the eFuse re-enables only when the input falls below V(OVPF): 19.93–21.1 V for this divider. A source sitting at 20.5–21 V may therefore stay off until re-plug. This acts like a latch, which suits D5-1 and requirement R6.4, but it is not guaranteed either way.

### 2.1a Phase 8: r3 front end (TPS16630 + LM74700) on guaranteed figures only

`front_end_r3_guaranteed` in `scripts/pcb/calculate-input-ovp-20v.py` keeps only G rows. The TYP
rows above remain as `front_end_r2_typ_sensitivity`.

**L7 is FAIL on guaranteed figures.** VBUS_P is bounded only through the forward path:
VBUS_P ≤ VBUS_IN ≤ the TVS2200 clamp. PCB inductive overshoot is not quantified.

| TVS2200 row (SLVSED5C 7.6, VIN 0 V before surge) | VBUS_P bound | Margin to 28 V |
|---|---:|---:|
| 24 A 8/20 µs, 27 °C | 27.70 V | +0.30 V |
| 40 A 8/20 µs, 27 °C | 28.00 V | 0.00 V |
| 35 A 8/20 µs, 125 °C | 28.35 V | **−0.35 V** |

- **Guaranteed-ESR bulk does not close it.** A polymer or ceramic bank with a datasheet ESR maximum
  supplies only the R term. The charge term still needs a guaranteed current through U2 during
  OVP_toff. SLVSET9G gives I(FASTTRIP) and I(SCP) as TYP only, and OVP_toff is 14 µs maximum.
- **A second clamp stage does not close it.** A second TVS2200 behind U2 has the same table rows.
  No TI flat-clamp sibling fits. TVS1800 has an 18 V standoff, below the 21 V normal high. TVS2700
  clamps at 32.5 V.
- **New gap: the OVP trip exceeds the STUSB4500 VDD operating maximum.** The fitted 174k/10k trip is
  21.60–22.56 V (22.67 V with TCR), up to 0.56 V above the 22 V maximum. A ratio of 16.94 would cap
  the trip at 22.0 V, but its 21.06 V minimum leaves only 0.06 V over the 21 V normal high.
- **Closing part (single fact).** A connector clamp with a guaranteed VC,max ≤ about 27.5 V at 35 A
  8/20 µs and 125 °C, with VBR,min ≥ 22.7 V. No such part is retrieved.
- **Closing decision (single decision).** Define the qualification surge as ≤ 24 A at 27 °C. The
  27.7 V row then gives +0.30 V, at 27 °C only.
- **VDD-local isolation.** Superseded by §2.1b. The pin limit closes on zener rows, and only the 5 V
  attach headroom still needs the active-mode IDD maximum.
- **LED per-product OVP 133k/10k (LED phase 11 §a), reviewed.** The trip becomes 16.79–17.54 V
  (17.62 V with TCR). As a common-block parameter it changes only a resistor value; the footprint and
  net stay the same.
  - It is **not applicable to PD**: the trip maximum is below the 19.0 V minimum of PD's 20 V contract.
  - For LED it is valid only with an NVM image whose highest PDO is 15 V. A 20 V contract would trip OVP
    and brown out the STUSB4500.
  - It does not change the guaranteed bound, which is still the clamp row. LED's 29.6 V → 24.6 V figure
    at 80 µF / 0.5 Ω uses TYP charge and is a sensitivity.
  - It does put the LED trip well below the 22 V VDD operating maximum, which closes that gap for LED.

### 2.1b Phase 9: STUSB4500 pins on local small-current clamps (drawn, `dec-p-stusb-local-clamp`)

The 28 V limit applies to the STUSB4500 high-voltage pins, which draw only small currents. Each
pin now has its own series resistor and zener clamp, so the surge path (TVS2200, U2, Q1, Board B)
no longer has to stay at or below 28 V. `stusb_local_clamp` in
`scripts/pcb/calculate-input-ovp-20v.py` computes these rows with VBUS_P at the 28.35 V
TVS2200 row (35 A, 125 °C).

| Pin | Feed | Clamp | Pin maximum, −40 to 125 °C | Margin to 28 V |
|---|---|---|---:|---:|
| VDD (U1.24, VDD_LOC, C38 1 µF) | R29 1k + R30 470R (phase 10; was 2 × 1k) | D9 BZT52C18-7-F C192739 | 20.794 V | **+7.21 V** |
| VBUS_VS_DISCH (U1.18) | R14 + R28, 2 × 1k | D10 BZT52C20-7-F C260890 | 23.0 V | **+5.0 V** |
| DISCH (U1.9) | R13 4.7k | D12 BZT52C18-7-F | 20.7 V | +7.3 V |
| VBUS_EN_SNK (U1.16) | Q6 BSS138-7-F cascode, gate at VDD_LOC / 2 | D11 BZT52C18-7-F | 20.7 V | +7.3 V |

**L7 is PASS on guaranteed zener figures.** Each bound is the DS18004 VZ maximum at IZT 5 mA plus
the TC maximum above 25 °C. The TC minimum, 12.4 mV/°C, is positive, so cold rows are bounded by
the 25 °C maximum. Where the clamp current exceeds IZT, ZZT maximum is used as the slope. That
covers at most 3.65 mA on VDD at −40 °C and adds at most 0.16 V. It is a project linearisation
(PA), and the margins of 5 V or more would absorb a slope of several kilohms. The STUSB4500
limits keep their mirror-source trust limitation (`fact-stusb-vbus-pin-absolute-max`,
`fact-stusb-vdd-absolute-max`). The rule rows are `calc-p20-stusb-local-clamp-vdd` and
`calc-p20-stusb-local-clamp-vs-disch` in `rule-tvs-clamp-vs-absmax`.

These margins are scenario-conditioned. They assume VBUS_P at the 28.35 V TVS2200 connector-node row,
and §2.1a explains why that row is not a guaranteed VBUS_P transient bound. Each pin holds 28 V for any
VBUS_P up to the level at which VZ + ZZT × (I − IZT) would reach 28 V. On the linearisation that is far above
28.35 V, but no guaranteed figure covers that region.

| Check (DS12499 Rev 7 copy; Rev 8 Table 22 not re-read) | Result | Status |
|---|---|---|
| VDD operating ≤ 22 V | ≤ 20.38 V at 105 °C | **PASS**: closes the 22.56 V > 22 V gap of §2.1a |
| VDD ≥ 4.1 V at a 5 V attach (VBUS ≥ 4.72 V), feed 1.47 kΩ (phase 10) | ≥ 4.373 V at the 210 µA idle maximum (+0.273 V); ≥ 4.209 V at 320 µA, twice the 160 µA idle typical (+0.109 V); IDD may reach 394 µA | **PASS at the idle maximum and the 2× typical sizing target (PA)**; active-communication and hot IDD maximum OPEN: no other DS12499 revision was reachable (st.com refused the download, 2026-10-31) |
| VBUS_VS_DISCH reads above VMONUSBL at 20 V | ≥ 17.63 V (C20 at −40 °C) vs 16.0 V | PASS on the default 20 V window |
| VBUS_VS_DISCH discharge current ≤ 50 mA | ≤ 10.6 mA | PASS |
| Discharge 120 µF, 21 V → 0.5 V (VTH0V minimum), through 2.02 kΩ | 0.906 s against TDISUSB0V ≥ 0.63 s (default TDISPAR0V 9) | **FAIL with the default NVM**; PASS with TDISPAR0V ≥ 13 in the factory image (13 gives 0.91 s minimum, only 4 ms over; 14 leaves 74 ms) |
| VBUS_VS_DISCH operating 22 V | above 22 V only at TA > ~67 °C with VBUS_P in the 22.0–22.56 V OVP band | OPEN (edge) |
| Q6 VGS | ≤ 10.29 V vs ±20 V | PASS |
| Q6 turn-on at a 5 V attach | VG ≥ 2.10 V vs VGS(th) maximum 1.5 V (25 °C row) | PASS at 25 °C only |
| Q1 off-state with Q6 off | needs Q6 hot leakage; DS30144 gives IDSS 0.5 µA at 25 °C only | OPEN |

Consequences:

- **The STUSB4500 overvoltage monitor no longer works.** VMONUSBH for PDO2 is 22 V, which the
  VBUS_VS_DISCH clamp may hold below. U2 OVP (21.60–22.56 V) is the only slow-overvoltage
  protection, as in §2.1a.
- **The main path is now limited by Q1.** DMP3036SFG-7 is rated −30 V VDS, 1.65 V above the
  28.35 V row. U2 (67 V), Q3 (60 V) and the 50 V input capacitors have more margin. Board B must still
  be screened against the 28.35 V row. TVS2200 stays.
- **CC pins are unchanged** (§2.2). The local clamps do not change CC exposure.
- **Normal operation draws clamp current.** At 21 V, D9 can draw up to 2.6 mA and D10 up to 1.7 mA
  (−40 °C, VZ minimum). That is a few tens of milliwatts and changes no budget.

### 2.2 CC pins (GAP-2): bounded, not closed

- **Single fault.** A CC-to-VBUS short at 21 V gives **+1.0 V** to the 22 V limit. That is thin, but within the limit.
- **Double fault.** A CC short during a surge exposes CC to the connector clamp, which is above 22 V with any VBUS TVS. The eFuse does not protect CC.
- **Retrieved hardware path.** The only one is ST TCPP03-M20 (CC connector side 24 V absolute maximum, CC OVP 5.5–6.0 V; G-U from the 2026-10-20 reading). st.com refused the download again on 2026-10-31, so it stays **G-U** and needs a primary retrieval and an owner bundle before any use. Its STUSB4500 compatibility is not documented by ST.

## 3. Recommendation (marked; not adopted)

**T3:**
- TPS26630 eFuse ahead of all of Board P, with OVP set to a 21.5 V minimum trip, I(OL) 4.5 A (R(ILIM) 4.02 kΩ) and an external blocking NFET for reverse current;
- connector-side TVS for the surge energy;
- ≥ 100 µF effective bulk on the protected node;
- STUSB4500 VDD / VBUS_VS_DISCH / DISCH / VBEN and Q1 all on the protected node;
- CC protection evaluated separately (TCPP03-M20 path, after primary retrieval).

T2 (b′) remains the lower-cost fallback at an EDGE margin. T1 is rejected for 20 V.

**Residual risks of T3:**
1. FET-off timing is taken as equal to FLT timing (PA).
2. The fast-trip multiple and the I(SCP) / 1 µs terms are typical, not guaranteed.
3. C_eff under DC bias and temperature, and the bulk part itself, are undefined.
4. The surge envelope is undefined.
5. The CC 22 V double fault is still open.
6. 4 × 4 mm VQFN placement, thermal path and loss on the 27 × 40 mm Board P: layout not screened.
7. The dVdT inrush ramp on attach must not upset STUSB4500 start-up or VBUS monitoring. The protected-node offset (≤ 3.38 A × 53 mΩ = 0.18 V) sits inside the default −15 % monitor window (G-U), but this is NOT RUN.
8. Discharge: with reverse-current blocking, STUSB4500 DISCH discharges only the protected node, not the connector side. Whether that meets the sink-side discharge expectation is UNAV.
9. None of TPS26630, TVS2200 or TCPP03-M20 has an owner bundle in this repository. Stock and price are UNAV.
10. This changes the canonical 15 V Board P only if a 20 V product is adopted. The built LED Board P (SMAJ20A) and the unbuilt 15 V PD Board P are untouched.

## 4. Sources retrieved 2026-10-31

| Document | URL | Bytes | SHA-256 |
|---|---|---:|---|
| TI TPS2663x SLVSE94G (Sep 2018, rev. Jun 2024) | https://www.ti.com/lit/ds/symlink/tps2663.pdf | 5728602 | `bb61314ace65ed37684bd07f541fc676081d7cf81cb24020e7c5c2065bfe16b2` |
| TI TPS1663x SLVSET9G (Sep 2018, rev. Apr 2026) | https://www.ti.com/lit/ds/symlink/tps1663.pdf | 4853428 | `8f91a0db2daf2da35abd335420ff9f8b4ac9a99c93dac93e215e0a75e9a866fe` |
| TI TVS2200 SLVSED5C (Dec 2017, rev. Aug 2023) | https://www.ti.com/lit/ds/symlink/tvs2200.pdf | 1627089 | `84c986c9cc4f323fdb0c6840bff455438802dd6df9af5fd89c73b8bce4dced9e` |
| TI TVS2700 SLVSED6A (Dec 2017, rev. Mar 2018) | https://www.ti.com/lit/ds/symlink/tvs2700.pdf | 1261602 | `d37c60e9abedade6cba8cb5e44b94861f6720e3a2b22d895dfbb2a9263e8b1bf` |
| TI LM74502 SNOSDE5A (Dec 2021, rev. May 2022) | https://www.ti.com/lit/ds/symlink/lm74502.pdf | 1745602 | `4badd940619090052b7260a88d7e32788f201d67ce97913b059ae6b1ed2d8bad` |

Not retrieved on 2026-10-31 (download refused or reset): ST DS12499 (st.com and the web.archive mirror recorded in the owner bundle), ST TCPP03-M20, Nexperia BZX84, ADI LTC4367. The PDF bytes are held only in the worker scratch space. They are not committed: these candidates have no owner bundles, and retaining them in the repository would be separate evidence work.
