# V196 open-risk extraction (desk record)

This file lists what evidence exists for each risk and what is missing. It closes
nothing. Sources: V196 schematic netlist (`evidence/rerun-20261031/V196-schematic-netlist.net`),
the V15 packet `candidates/husb238/` records (`POWER-PATH.md`, `ADMISSION-DECISION.md`,
`REQUIREMENTS-CHALLENGE.md`, `release-status.json`, `monitor-integration/README.md`),
the V196 `primary-evidence/`, the V197 README, repo owner skills, and issues #52, #143,
#144 and #145.

Classes: **TU** = technical uncertainty, **EG** = access/evidence gap,
**UD** = user decision, **EP** = explicit permission.

## Circuit as built in V196 (from the native netlist)

RAW_USB_VBUS → U2 TPS259474LRPWR IN; U2 OUT → SWITCHED_OUTPUT → JOUT1.1/.2 (COUT
4.7 µF, RBLEED 2.2 kΩ). U2 EN/UVLO is driven by three things: the RUVH 97.6 k / RUVL
10 k divider, the QINH collector, and the UMON TPS3701 OUTA. OVLO uses ROVH 133 k /
ROVL 10 k, ILM uses RILM 1.27 k, and DVDT uses RSLEW 100 Ω + CSLEW 22 nF C0G. U2 PG
and ITIMER are NC; PGTH is GND.

The HUSB238 GATE drives the net `CONTRACT_GATE_N`. When GATE is released, RG 100 k
pulls the QINH base high and EN is held low. When GATE sinks, QINH turns off. UMON
senses RAW through 133 k + 180 k / 10 k. VSET 14 k gives 15 V; ISET 22.6 k gives 3 A.
JOUT1.3/.4 are NC, so no ATT/PDOK is driven, and JOUT1.5/.6 are GND. U1 SDA/SCL are
NC (no I2C).

## Risk table

| # | Risk | Evidence that exists | Missing / next step | Class |
| --- | --- | --- | --- | --- |
| R1 | Exact HUSB orderable | BOM `HUSB238_006DD` / C55013903; the retained Rev2.5 excerpt (pp4–9) states the GATE default is "after POR", with other options from Hynetek; V15 records state that _006DD is the "During Contract" GATE / "Next PDO" variant | Full Rev2.5 PDF not in transfer (hash known); a variant table binding _006DD → GATE option to the JLC C55013903 listing is not in the imported evidence; the U1 land is an engineered draft (no manufacturer land) | EG |
| R2 | eFuse / protection values | TPS25947-family thresholds in POWER-PATH.md: UV rise 12.64–13.25 V / fall 11.49–12.09 V; OV rise 16.79–17.62 V / fall 15.27–16.08 V; ILM screen 2.316–2.947 A (nominal ≈2.625 A); 0.35 % resistor model only | Reflow/aging; QINH leakage (1 µA assumed, not guaranteed); OVLO pin below the recommended range at 5 V; the downstream must tolerate up to 17.62 V plus overshoot, and Board L tolerance is not established. No input TVS on V196 (none in netlist); input transient/ESD protection is not reviewed | TU |
| R3 | Fail-OFF for non-15 V sources, startup, hot-plug, renegotiation | Static design: released GATE → QINH → EN low. TPS3701 window added for the 12 V-fallback case | Startup: HUSB, TPS3701 (output undefined below valid VDD) and QINH have no guaranteed pulse-free OFF. Contract loss: no maximum GATE release delay. 12 V fallback: U2 UV falling (11.49–12.09 V) alone may stay ON at 12 V; the TPS3701 falling threshold 12.73–13.11 V (0.35 %) rejects ≤ 12.6 V with 0.13 V margin, but only 0.006 V at the 0.85 % model, and its rising threshold misses the 13.5 V floor at 0.85 % (13.57 V). Stale-low GATE is an architectural limitation. release-status.json still says `REJECTED_PENDING_ADMISSION_SAFETY` | TU (+ UD if the window cannot close: wider tolerance parts vs. tighter supported-source scope) |
| R4 | ATT/PDOK-equivalent output semantics | #145 B-plan approved by the owner (2026-10-20): drop strict ATT/PDOK compatibility and keep 15 V/3 A. V196 leaves JOUT1.3/.4 NC; Board L R24/R25 pull PA5/PA7 up to local V3P3 | Board L firmware must treat PA5/PA7 as unused (analog mode). The power-switch doc's "check PD status at startup" must be rewritten. No status signal exists for diagnostics | UD already made; firmware spec work remains (TU) |
| R5 | Board L connection | JOUT1 PZ254V-11-06P male ↔ Board L J2 PM254V-11-06 female; logical map 1/2 = 15 V, 3/4 = NC, 5/6 = GND (V15 `board-l-interface.csv`); V197: CAD hole/header alignment and polarity supported | Spacer height, backside/plug clearance, mating force and per-contact current sharing are not measured. Reversal is not keyed or safe. SWD/UART backfeed into an unpowered P is unreviewed | TU / physical |
| R6 | Capacitor effective capacitance and footprints | C1 CL10A105KB8NNNC 0603 X5R 50 V ("EFFECTIVE C OPEN"); COUT CL31B475KBHNNNE 1206 X7R ("effective C qualified typical only"); CSLEW C0G (no bias loss); HUSB VIN needs 1 µF decoupling (excerpt) | DC-bias effective C at 15 V for C1 (HUSB VIN) and COUT has no guaranteed value; total RAW capacitance vs USB-PD sink limits is not computed; the COUT 1206 and CSLEW footprints are "TRIAL"/manufacturer-example lands | TU / EG |
| R7 | Thermal / current | eFuse dissipation 0.016 W at 0.41 A (illustrative LED load), 0.25 W at 2.3 A (POWER-PATH.md, TI 74.5 °C/W JEDEC example, not this layout); V196 RAW feeder +0.066 mΩ arithmetic | No measured Board L input current; no layout thermal model; JOUT1 contact rating not bound; the ILM upper corner leaves 53 mA under a 3 A contract | TU |
| R8 | J1 connector tolerance / assemblability | GCT USB4105 printed pattern; USB4105-15-A STEP (standard 0.95 mm stake); CC1 via 0.45 mm nominal clear of the STEP projection; 2 × 0.1751 mm GND/NPTH gaps | Exact MPN (GF vs 15 plating bridge not accepted); no placement/finish tolerance stack; mixed SMT + shell-THT process not confirmed by the assembler | EG + UD (waiver, see DRC-CLASSIFICATION.md) |
| R9 | AP63203 (Board L 3.3 V buck) startup | Owner facts: EN open, internal pull-up auto-start; soft-start 4 ms *typical* (NEEDS BENCH); VIN 32 V recommended max. The V196 DVDT ramp is nominal 0.091 V/ms, so 0 → 15 V takes about 165 ms | EN/UVLO thresholds and startup behaviour on a slow ramp are not guaranteed in retained evidence (HTTP 403, not bypassed). V159–V163 assessment missing. Safety then rests on Board L CTRL default-OFF (33 kΩ pull-down) plus firmware. Options to compare without assuming a guarantee: (a) keep the ramp and bench-capture V3P3/NRST/CTRL during a slow ramp; (b) a faster Board P ramp (smaller CSLEW) to shorten the undefined window, traded against inrush; (c) accept Board L's hardware default-OFF as the safety basis and test it. Board L hardware change is excluded (reuse) | EG + TU |
| R10 | #52 LED peak current vs 90 mA absolute max | Reproduced arithmetic: 0.104 V / 0.198 Ω × 1.2 = 0.6303 A over 8 branches with 33 Ω ±1 % gives 80.18 mA matched; with a 0.30 V Vf spread, 88.19 mA (98 %); limit reached at 0.3677 V. No pulsed rating retained for C210315 | Pulsed-current rating not retrieved (option 3). If CTRL is effectively analog (RC-filtered PWM), a firmware duty ceiling lowers peak current too. If CTRL is chopped PWM, the on-time peak is unchanged and only RS1/ballast hardware helps. Board L CTRL network behaviour must be confirmed before counting firmware as mitigation. Changing RS1 on reused Board Ls is rework (needs approval) | UD + EG |
| R11 | Existing Board P (#144) / silk (#143) | #144: both STUSB Board Ps fail to hold 15 V, RESET 0.93 V, cause unconfirmed; desk audit proposed rework (not performed). #143: J2.4 silk "NC" is RESET, J3.5 "RST" is GND | Not V196 issues, but they mean the two delivered Board Ls were never powered through a working P. Board L health is unknown. Keep the #143 caution for anyone probing old boards | physical / EP |
| R12 | Board L existing record: logic inductor | Owner fact `fact-fnr-irated-margin` = −0.7 A (2 A rated vs 2.7 A required for the AP63203 peak-limit headroom) | Existing Board L design record, not a V196 change; relevant to "reuse as-is" acceptance | TU |
