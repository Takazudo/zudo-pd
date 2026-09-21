# Renewal power-chain screening

The machine-readable report is `power-budget.json`; regenerate it with
`python3 scripts/pcb/calculate-power-budget.py`. It separates the rated output target
(26.5 W total) from prototype qualification. The negative divider selects R5 RT0603BRD0710K5L (C861077) and R6 RT0603BRD071KL
(C110776), both 0.1%. The report retains the earlier alternatives for comparison and
checks whether those exact identities have reached the current schematic spec. The
positive converter selects AP63201; its high-duty low-line operation and whole-chain
qualification remain open.

For the retained inverting LM2596 stage, a 10.5 kΩ / 1 kΩ divider with both resistors
at 0.1% gives a nominal −14.145 V intermediate rail. Full-temperature reference and
opposed resistor tolerances give magnitudes of 13.545–14.747 V. That leaves 0.545 V
above the LT3015-12's 13 V input guarantee boundary before rail ripple and wiring
loss. Including a 25 ppm/°C resistor TCR over a 100 °C excursion expands the
negative range to 13.484–14.814 V, retaining 0.484 V before ripple and wiring loss. The initial-tolerance comparison using a 10.6 kΩ top resistor (also 0.1%,
without the TCR addition) gives a nominal magnitude of 14.268 V and a lower bound
of 13.663 V, with slightly more dissipation.

The exact 100 µH inductor has a 4.5 A heat-rating current and an 8.5 A saturation
criterion; those are distinct manufacturer test conditions. The report evaluates
minimum inductance and oscillator frequency, maximum switch saturation and the new
SDT5A60SA-13 diode's 0.52 V maximum at 5 A / 25 °C, and a 14 V input screening
point. The catalog's 0.46 V is typical and is not used as the maximum. The updated
CCM duty calculation includes the inductor's maximum 25 °C winding resistance;
ripple copper loss is also included in the input-power screen. It includes both the
0.8 A load alone and a more conservative load with the LDO ground-current bracket,
sense current and feedback-divider current. At 14 V with the 0.883913 A intermediate-load screen, inductor RMS current is
2.040 A and peak current is 2.395 A, leaving 1.005 A below the 3.4 A minimum
switch-current limit. The conduction model gives 1.146 A input current and losses
of 0.770 W in the winding, 1.718 W in the switch and 0.460 W in diode forward
conduction. It omits hot winding resistance, core/switching/quiescent losses,
bias-dependent inductance, diode reverse leakage and measured transients, so these
figures are not upper bounds or measured efficiency. D3's 0.5 mA reverse-leakage
maximum is specified at 60 V / 25 °C; the 50 mA figure at 60 V / 125 °C is only
typical. Actual hot reverse loss requires measurement.

For the selected 10.5 kΩ divider, use the report's full-chain thermal screen:
14.814410 V negative intermediate magnitude includes the TCR allowance, and the
0.812490 A LDO output load includes the indicator. Against the LT3015's 11.76 V
minimum output magnitude, series-pass loss is about 2.482 W. Its published
1.5 A/dropout ground-current maximum of 70 mA contributes another 1.037 W as a
conservative screening bracket, not an interpolated guarantee at the target load.
The resulting 3.519 W requires effective junction-to-ambient thermal resistance
below 24.157 °C/W at 40 °C ambient to remain below 125 °C.

The simpler initial-tolerance-only, 0.8 A load comparison remains in the JSON at
3.422 W and 24.841 °C/W; it omits the TCR and indicator additions and must not be
substituted for the full-chain screen. Filled copper areas are not thermal
qualification; actual layout, shared heat paths and temperature rise must be
verified. The 14 °C/W headline DD-Pak value uses a specific 2500 mm² test board
with copper on both sides.

The new regulator selection must satisfy output-capacitor requirements with exact
part evidence: LT3015 requires at least 10 µF effective capacitance and ESR no more
than 0.5 Ω; LT1963A requires at least 10 µF and ESR no more than 3 Ω. A nominal
capacitor value alone does not close ESR, bias, temperature or load-step stability.

The current protection pair is Board P D5 **Littelfuse SMAJ16A (C74561)** and
Board B D3 **Diodes SDT5A60SA-13 (C3024223)**. The prototype permits normal source
input of **15 V ±5%**, or 14.25–15.75 V. The TVS's 16 V standoff leaves only 0.25 V
above that normal high endpoint. **20 V is unsupported.**

First power and programming must use a current-limited **5 V-only source**, with
Board B disconnected. Resolve programming-jig voltage and VREG_2V7 pull-up loading,
then program and retain readback of the 15 V-only NVM policy before connecting any
15 V-capable PD source. An unknown factory configuration must not be allowed to
request 20 V from that source.

The new TVS's maximum 26 V clamp is specified at 15.4 A, a 10/1000 µs waveform and
25 °C. Adding the 14.814410 V negative-rail screen gives 40.814410 V. The resulting
conditioned margins are:

| Limit being compared | Margin at that table point |
| --- | ---: |
| STUSB4500 28 V absolute maximum | 2.000 V |
| Q1 30 V drain-source magnitude | 4.000 V |
| U4 45 V absolute maximum | 4.186 V |
| D3 60 V reverse rating | 19.186 V |
| C9 50 V bridge-capacitor rating | 9.186 V |
| 35 V / 50 V input-capacitor ratings | 9.000 V / 24.000 V |

The STUSB limit retains its documented mirror-source trust limitation. U4's 40 V
operating ceiling is exceeded at this conditioned event; the comparison does not
claim regulation through it. The ideal asserted Q1 gate voltage is −10.4 V at
26 V, but its transient waveform is not established. The 26 V table point is not
a universal ceiling at elevated temperature or in the installed circuit. The
published VBR temperature coefficient describes breakdown, not a formula for VC.
Clamp current, temperature, wiring inductance, switch-node ringing and actual
waveforms remain prototype qualification work.

The former SMAJ20A 32.4 V / SS34 40 V comparison is retained as **retired** evidence.
At the nominal 14.145 V negative rail it gave 46.545 V, exceeding the old U4/D3
limits; that historical arithmetic has not been reclassified as passing. The
current parts remove that specified table-point rating mismatch. They do not
establish complete surge qualification.

The LM2596 inverting startup can still demand about 4.5 A for at least 2 ms against
a 3 A PD contract. Neither the revised conduction model nor clean DRC demonstrates
that the assembled source starts and sustains the rated loads.

The positive AP63201 divider targets 13.44 V. With the published 0.792–0.808 V
reference, 158 kΩ/10 kΩ resistors, initial 0.1% tolerance and respective 50/25 ppm/°C
TCR over 65 °C, the arithmetic range is 13.220–13.662 V. At an assumed 14.0 V
board input the upper setpoint leaves 0.338 V for switch, winding and wiring drop.
This is a useful low-line acceptance constraint, not a guaranteed converter dropout
claim; the actual high-duty behavior and path losses must be checked.

The full-chain report also includes indicator and feedback-divider loads. Using
conservative higher-load ground-current brackets, the intermediate rails require
about 35.7 W before converter losses. At the assumed 14 V board input and 3 A
contract, this needs a weighted converter efficiency above about 85%. It is an
acceptance budget, not a proven efficiency. LDO dissipation screens are approximately
4.23 W on +12 V, 1.95 W on +5 V, and 3.52 W on −12 V; these include the ground-current
brackets and conditional output-voltage corners. At 40 °C ambient, the corresponding
effective θJA limits are approximately 20.1, 43.5, and 24.2 °C/W. Actual normal
losses may be lower; qualification must measure them with all rails loaded together.

The filled-layout report, `power-layout.json`, records the PCB hash, all 48 thermal
vias and the dedicated output traces. Its `negative_filled_zone_areas` entries give the actual U4/U8 areas for the
current PCB hash. Use those values when reviewing this report; footprint and
routing revisions can change filled area even when the zone rectangles are
unchanged. The earlier 1,280 mm²-per-side proposal is not an achieved-area claim.

U6 and U7 share the connected system-ground copper. That shared area cannot be
credited independently to each regulator as an isolated heatsink. The report
checks polygon connectivity, specified ground stitches, aggregate sampled ground
width and the largest individual run. Aggregate width is not one continuous strip;
neither area nor via count
establishes thermal resistance. Re-run the filled-layout check before regenerating
the budget after any PCB change; stale PCB hashes are rejected.


The current screw-terminal board retains the 110 × 85 mm outline and the same
rail targets. Its two top-side terminal blocks replace the four Fastons and printed
guard. This mechanical change does not establish electrical or thermal performance.
Use the current source-locked filled areas in the JSON reports; earlier layouts and
manufacturer single-device test boards cannot qualify this assembly's coupled
temperatures. Repeat full-load measurements with Board B front-down on its legs,
Board P in the front-side stack, and the final wiring and enclosure. Earlier
orientations do not establish cooling in this installed configuration.
The current PD translation and fourth independent corner support do not resolve
the HC-11 floor-height conflict: an 11 mm support is shorter than P's 12.7 mm
back substrate plane and the terminal drawing's 14.2 mm maximum. See
[the retained support record](../boards/board-b/supports/README.md). The selected
[18 mm printed-leg prototype](../3dp-files/adhesive-leg/README.md) addresses that
nominal height conflict. Its separate CAD verification does not qualify printing,
adhesive retention or thermal behavior. Check the actual accessory and enclosure
before treating the installed configuration as a thermal-test setup.
