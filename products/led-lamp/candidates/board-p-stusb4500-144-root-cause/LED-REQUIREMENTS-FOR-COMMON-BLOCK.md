# LED requirements for the common STUSB4500 controller block (LED worker, 2026-10-31)

Scope: what the LED product needs from the PD worker's common block (Board P r2 controller
section). Thresholds marked *proposed* have no manufacturer or measured source yet.
Source branch: Takazudo/zudo-led-lamp `claude/project-thread-l2opxj` (phase 7 commit, see led-phase7.md).
#144 desk analysis: `ANALYSIS.md` on that branch.
STUSB4500 facts: DS12499 Rev 7 (ST GitHub usb-c/STUSB4500 @55d1109e).

## R1. #144 defect must not be inherited (hard requirements)

| ID | Requirement | Why (evidence) |
| --- | --- | --- |
| R1.1 | RESET (pin 6) tied to GND by a short dedicated connection or a 0 Ohm strap at the pin; no RESET copper under any component or within HV clearance of VBUS / VBUS_VS_DISCH / DISCH / VBEN | Ordered LED Board P runs RESET between R13 (VBUS_OUT-DISCH) pads at 0.222 mm and 0.326 mm from a VBUS_VS_DISCH via; RESET read 0.93 V (VIL max 0.35 V, VIH min 1.2 V); a ~44 k VBUS-derived leak would exceed VIH at 15 V |
| R1.2 | RESET not on a bare pogo pad; any jig reset goes through a jig-side series resistor; every test pad silk audited against its net | J2.4 = RESET with "NC" silk (#143); ESD/miswire exposure |
| R1.3 | I2C pull-ups live on the programmer rail (jig side), not on VREG_2V7 | Owner audit on #144: VREG_2V7 loading is a documented-use violation |
| R1.4 | VDD node guaranteed <= 28 V (DS abs max) at the worst-case clamp current the input protection can deliver | SMAJ20A Vc 32.4 V @ 12.3 A > 28 V; LED Board P has it on VBUS. The TPS16630 + LM74700 choice may solve this upstream; the PD worker should show the number |
| R1.5 | Per-unit NVM: dump the factory 40 bytes before writing, write, read back, power-cycle, read back again; retain all three dumps with the unit serial | No dump survived from the #144 boards (evidence gap) |
| R1.6 | NVM write/readback works with RESET hard-grounded (STUSB4500 I2C is available in normal operation; confirm in the jig procedure) | Removes any need to wire RESET to the jig |

## R2. Contract policy: 15 V only, fail-OFF otherwise

| ID | Requirement |
| --- | --- |
| R2.1 | LED NVM image: SNK_PDO_NUMB = 2, PDO2 = 15 V, POWER_ONLY_ABOVE_5V = 1, VBUS_EN_SNK only on a 15 V explicit contract. Per DS12499 a non-matching source yields a 5 V capability-mismatch contract with VBEN Hi-Z, i.e. OFF. Keep that. |
| R2.2 | PDO2 current: coordinator states 3 A. LED load is ~0.41-0.5 A at 15 V (Board L F1 is 750 mA). Requesting 3 A excludes 15 V sources rated below 3 A (match needs I(SNK) <= I(SRC)), which then fail OFF. **User decision**: 3 A (one image for all products, fewer compatible chargers for LED) vs 1.5 A or lower for the LED image. |
| R2.3 | A hardware voltage window downstream of the sink switch, independent of NVM content, so a factory or lost image (factory = 20 V/1 A highest priority, POWER_ONLY_ABOVE_5V = 0) cannot pass 5 V or 20 V to Board L. Reuse V196 FAILOFF-WINDOW numbers as *proposed* targets: OFF guaranteed at RAW <= 12.6 V, ON at RAW >= 14.0 V (O3: RMH2 187 k on the TPS3701/TPS25947 pair), OV rising minimum >= 16.49 V above the retained 15 V transient high 16.25 V, OV cut below the Board L D10 SMAJ20A conduction region. |
| R2.4 | The window must also cut on renegotiation (source drops to 5/9/12 V while VBEN stays asserted; DS disables VBUS monitoring for tSrcReady 285 ms during transitions) and on contract loss. Contract loss with VBUS still at 15 V is only covered by VBEN release: state it as a residual. |
| R2.5 | Startup and hot-plug: Board L input sees no pulse above the window before the window releases (start OFF, enable after PDO2 PS_READY + window settle). |
| R2.6 | If the common block's eFuse / LM74700 path replaces the TPS25947 window, the LED derivative still needs an equivalent 12.6 V-reject / 16.5 V-OV function on its output (common block is 20 V-capable). |
| R2.7 | Input-path drop budget: O3 needs RAW >= 14.0 V; with the 14.25 V source minimum that is 0.25 V total. Fine at 0.5 A; at 3 A it is ~83 mOhm cable+connector+switch. Size the switch for the LED current, not for 3 A, or accept a lower ON threshold with its own margin analysis. |

## R3. Board L interface (keep the 2 assembled Board Ls usable)

| ID | Requirement |
| --- | --- |
| R3.1 | Keep JOUT1 = PZ254V-11-06P (C492405), 1x6 2.54 mm, same position relative to the Board L J2 (PM254V-11-06-H85, C2832269) mating stack, same pin map: 1,2 VBUS_OUT; 3 ATT; 4 PDOK; 5,6 GND. |
| R3.2 | ATT = STUSB4500 ATTACH (LV open drain), PDOK = POWER_OK2 (HV open drain). No pull-up on Board P; Board L R25/R24 10 k pull to its V3P3. PD worker to confirm ATTACH's allowed pull-up voltage from DS12499 (not checked here). |
| R3.3 | ATT/PDOK are informational only. Board L V3P3 exists only after VBUS_OUT is live, and POWER_OK2 stays asserted after detach until re-attach/reset (DS12499), so Board L firmware must never admit power from them. Current target firmware does not read PA5/PA7; keep it that way. |
| R3.4 | VBUS_OUT current: >= 0.75 A continuous at 15 V for LED (F1 hold). Board L D10 SMAJ20A clamps V15; the Board P window OV must sit below its conduction region. |
| R3.5 | Board outline/holes compatible with the existing LED enclosure stack (27 x 40 mm Board P) or a documented mechanical delta for the user. |
