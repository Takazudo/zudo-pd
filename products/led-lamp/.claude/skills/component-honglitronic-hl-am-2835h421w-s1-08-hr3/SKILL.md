---
name: component-honglitronic-hl-am-2835h421w-s1-08-hr3
description: Resolve the exact Honglitronic HL-AM-2835H421W-S1-08-HR3 LED and subordinate FOJAN FRC2512F33R0TS ballast resistor used on Board L. Use for polarity, optical bins, current/voltage limits, thermal/reflow constraints, branch sharing, and resistor stress.
---

# Board L LED string and ballast

Run the central validator and read every local JSON file before using these records. Official primary specifications support the Honglitronic base-MPN LED limits and the exact FOJAN order code and ballast ratings. Available LCSC JSON-LD confirms only the C210315-to-exact-MPN/2800–3100 K/3000 K distributor identity; the bare MPN spans multiple CCT rows. Incoming reel/label/bin acceptance and real eight-branch current sharing remain open.

The LED drawing defines pad 2 as anode and pad 1 as cathode. Exact 3000 K output is 27 lm minimum / 29 lm typical at 60 mA, with Ra at least 80 and forward voltage 2.6 to 3.2 V. Absolute maxima are not operating targets. Follow the assembly section's maximum two reflow cycles; a reliability-test condition mentioning three cycles is not process authorization.

Board L has eight parallel branches, each one 33 ohm ballast followed by three series LEDs. Do not infer total current or current sharing without the driver state, supply waveform, LED bin/Vf distribution, resistor tolerance/temperature, thermal coupling, PWM duty, layout and bench data. An open LED removes its branch; a short or unequal heating redistributes stress. Use the included nominal 60 mA calculations only as arithmetic context, not proof of the design operating point.

## Human component reference

Human projection of this bundle: [rec-c210315](/docs/components/records/c210315/), [rec-c2934070](/docs/components/records/c2934070/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
