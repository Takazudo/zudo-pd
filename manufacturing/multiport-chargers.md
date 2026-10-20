# Multiport chargers: Anker A2683 screen

**Status: screening analysis only. Nothing here is adopted, measured or qualified.** No charger is approved or recommended for purchase. Every schematic and PCB stays an unvalidated draft. The test matrix below is a proposal; it has **not** been run, and running it needs hardware and the owner's explicit approval.

Owner request: zudo-pd#218 comment 6286606035, item 3. Evidence classes follow the other screens: **G** guaranteed by an official manufacturer document, **G-U** official but incomplete or unresolved in reading, **PA** project assumption, **UNAV** not available. Sources were retrieved on 2026-10-20.

## 1. Sources

| Source | Content used | Class |
|---|---|---|
| [Anker product description, A2683](https://service.anker.com/eu/product-description/a08J1000000Xkc2IAC) | Product name "Anker Prime Charger (200W, 6 Port, GaN)", port order, single-port outputs, "N Ports in Use: Up to … W Max" | G (official) |
| [A2683 User Guide PDF](https://salesforce-knowledge-download.s3.us-west-2.amazonaws.com/000017576/en_US/000017576.pdf) (linked from that page) | Input 100–240 V~, 3.2–2.5 A; output text identical to the page; ActiveShield note | G |
| [A2683 Output Power Distribution PDF](https://salesforce-knowledge-download.s3.us-west-2.amazonaws.com/000017032/en_US/000017032.pdf) (linked from that page) | Watts per port for each combination | G-U: the PDF is a drawing; the text layer gives the watt values per combination, but which physical port receives which value is drawn graphically and was not resolved from text |
| Amazon B0D3GG4M9N | Not used for any value (secondary listing only) | — |

## 2. Published facts

**Port order** (G): "Sequence from Left to Right (A1-A2, C1-C4)".

**Single-port output** (G, verbatim):
- USB-C1 / C2 / C3 / C4: 5.0V 3.0A, 15.0W / 9.0V 3.0A, 27.0W / 10.0V 2.25A, 22.5W / 15.0V 3.0A, 45.0W / 20.0V 5.0A, 100.0W (100.0W Max).
- USB-A1 / A2: 5.0V 3.0A / 9.0V 2.0A / 10.0V 2.25A / 12.0V 1.5A (22.5W Max).
- PPS support is mentioned in marketing text only; PPS ranges are **UNAV**.

**Totals** (G): two to four ports "Up to 200.0W Max"; five or six ports "Up to 199.0W Max"; total "Up to 200.0W Max". A total is not a per-port guarantee.

**Distribution by combination** (G-U; watt values from the PDF text layer, port positions not resolved):

| Ports in use | Watts per port | 20 V-capable ports ≥ 60 W | ≥ 70 W |
|---|---|---|---|
| 1 C | 100 | 1 | 1 |
| 2 C | 100 + 100 | 2 | 2 |
| 1 C + 1 A | 100 + 22.5 | 1 | 1 |
| 3 C | 100 + 70 + 30 | 2 | 2 |
| 2 C + 1 A | 100 + 70 + 22.5 | 2 | 2 |
| 4 C | 65 + 65 + 45 + 25 | 2 | **0** |
| 3 C + 1 A | 65 + 65 + 45 + 22.5 | 2 | **0** |
| 2 C + 2 A | 100 + 70 + 12 + 12 | 2 | 2 |
| 4 C + 1 A | 65 + 45 + 45 + 25 + 22.5 | **1** | **0** |
| 3 C + 2 A | 65 + 65 + 45 + 12 + 12 | 2 | **0** |
| 4 C + 2 A | 65 + 45 + 45 + 20 + 12 + 12 | **1** | **0** |

**Not published (UNAV):**
- The PDO list each port advertises at a reduced allocation. A "70 W" port may advertise 20 V / 3.5 A, or only 20 V / 3.25 A plus lower PDOs; a "45 W" port may or may not advertise 15 V / 3 A; a "65 W" port presumably advertises 20 V / 3.25 A, but that is not stated. **A PD analyzer capture of Source_Capabilities per port and per combination is needed** before any compatibility statement is more than arithmetic.
- How reallocation is carried out when a port is plugged or unplugged: new Source_Capabilities with a re-contract, a hard reset, or a VBUS interruption. None of this is stated.
- Which physical port receives 100 / 70 / 30 W in a three-C combination, and whether it depends on insertion order.
- **Thermal derating** (G-U, User Guide): "ActiveShield™ … adjusting power output … High temperatures will reduce charging speed and restrict power". The charger can therefore lower a port's offer during operation, independent of other ports. The trigger and the PDOs offered after derating are UNAV.
- Whether the C ports share one output return (see section 5).

## 3. Compatibility per model (arithmetic on published watts; PDOs per allocation UNAV)

**Watt allocation alone is not compatibility proof.** Only the single-port PDO list is published (G). In every multi-port combination the advertised PDOs are UNAV, so each "candidate" below is conditional on observing the required PDO on that port (MP1). A port is a candidate only if its allocation could cover the model's contract at the exact voltage. The STUSB4500 matches only on exact voltage and I(SNK) ≤ I(SRC) (DS12499 §3.3.2, G-U; product-lineup.md STUSB4500 facts).

| Model and contract | Required PDO on the port | Candidate allocations, **conditional** on observing the required PDO (MP1); single-port use is covered by the published list | Allocations ruled out by arithmetic |
|---|---|---|---|
| Current 15 V model, PDO2 15 V / 3 A | 15 V ≥ 3 A (45 W) | Single port: yes (15 V / 3 A published, G). In combinations: 100, 70, 65, 45 only if 15 V / 3 A is observed | 30, 25, 22.5, 20, 12 (all USB-A ports) |
| zudo-PD-60W, 20 V / 3 A | 20 V ≥ 3 A (60 W) | Single port: yes (20 V / 5 A published, G). In combinations: 100, 70, 65 only if 20 V ≥ 3 A is observed | 45 and below |
| Full OSC C2, PDO2 20 V / 3.5 A (+ 5 A e-marked cable) | 20 V ≥ 3.5 A (70 W) | Single port: yes (G). In combinations: 100 and 70 only if 20 V ≥ 3.5 A is observed | 65 (3.25 A) and below |
| Full OSC C2, PDO2 20 V / 4–5 A | 20 V ≥ 4–5 A (80–100 W) | Single port: yes (G). In combinations: 100 only, if 20 V ≥ 4–5 A is observed | All others |

Consequences (arithmetic on watt allocations; every multi-port case stays conditional on MP1; no physical test has been run):
- **Two products on two C ports** get 100 + 100 W: every model is a candidate on both (C2 with the 5 A cable), if the required PDO is observed on each port.
- **Three C ports in use** give 100 + 70 + 30 W. The 30 W port is ruled out for every model. At most two ports are candidates: for full OSC C2 the 100 W port, and the 70 W port only if it advertises 20 V / 3.5 A; for the other models both ports, each conditional on the observed PDO.
- **Four C ports in use** give 65 + 65 + 45 + 25 W. **No port reaches 70 W**, so full OSC C2 fails on every port, even with the 200 W total. Two ports (65, 65) are candidates for zudo-PD-60W if 20 V ≥ 3 A is observed; three ports (65, 65, 45) are candidates for the current 15 V model if 15 V / 3 A is observed on each.
- **Plugging a phone into a USB-A port** changes the allocation. Two C ports give 100 + 100 W; adding one A port gives 100 + 70 + 22.5 W, so one C port drops from 100 W to 70 W. A full-OSC C2 unit on that port loses its contract if its PDO2 is 4–5 A, or if the 70 W port does not advertise 20 V / 3.5 A (UNAV). Likewise 3 C → 3 C + 1 A drops 100 + 70 + 30 W to 65 + 65 + 45 W. A unit running at 100 W can lose its contract because of an unrelated device.
- Anker's own figures confirm the owner's note: **200 W total does not give three 60 W contracts.** The three-C row offers 100 + 70 + 30 W.

## 4. Downgrade and renegotiation behaviour of the sink (STUSB4500)

Facts used (G-U, DS12499 via product-lineup.md):
- Matching: exact voltage, then I(SNK_PDO) ≤ I(SRC_PDO); first match wins.
- Mismatch: the contract ends at 5 V with the capability-mismatch bit set.
- With `POWER_ONLY_ABOVE_5V = 1` (the intended Board P setting, boards/board-p/README.md), VBUS_EN_SNK is enabled only at a PDO2/PDO3 contract.
- POWER_OK pins stay asserted at detach (POWER_OK_CFG 2, the default) and reinitialize after new attachment or reset.
- After a hard reset with broken communication, error recovery de-asserts VBUS_EN_SNK, POWER_OK2 and POWER_OK3. **Timing is not stated.**

Expected behaviour on a downgrade. **This is an inference from the STUSB4500 facts above, not a measurement and not stated by ST; timing is UNAV, and every multiport physical test is NOT RUN:**
1. If the new offer still contains the needed PDO at sufficient current, the contract is kept. The rails see nothing, or a short VBUS transient if the charger interrupts VBUS.
2. If it does not, the STUSB4500 re-contracts to 5 V. With `POWER_ONLY_ABOVE_5V = 1` it should disable VBUS_EN_SNK, so Q1 turns off. Inferred: the rails would then decay on their own bulk capacitance at different rates, not together. **That would be a non-coordinated shutdown and could brown out a load (OSC) rail by rail.** No rail-drop sequence has been measured.
3. Inferred: if VBUS_EN_SNK is not disabled fast enough, Board B sees VBUS fall from 15 / 20 V towards 5 V with the regulators still enabled: a brownout, not a shutdown.
4. POWER_OK alone cannot be trusted as a "power good" signal across these events, because of its latch behaviour at detach.

**Proposed requirement (unchanged, already in the gate register; a design requirement, not a measured behaviour):** any downgrade, re-contract, hard reset, thermal derating or detach must end in a **safe, simultaneous all-rail shutdown** that stays off until a valid contract is re-established, with no rail out of band while another is on. This is GAP-6 (UVLO and coordinated all-rail enable) and GAP-9 (insufficient-source indication) in [`design-gaps-20v.md`](design-gaps-20v.md), and M6 in [`power-limit-60w.md`](power-limit-60w.md). A multiport charger makes these events routine rather than rare, so the gate is mandatory for any product sold for use on one.

Indication: the user needs to see why a unit went off (insufficient source after reallocation). That is GAP-9; every method needs a Board P change.

## 5. Grounding, return paths and noise (separate from power capability)

Sharing one charger or one enclosure does not establish a common-ground topology or low noise.

- **Port returns.** Whether the four C ports share one return (common negative on one transformer secondary, with per-port buck stages) or are isolated from each other is **UNAV** for the A2683. The usual multiport architecture shares the negative, but it is not documented here and must not be assumed.
- **If the returns are common:** two units powered from the same charger and also connected by patch cables form a loop: unit A GND → USB-C cable return → charger common → cable return → unit B GND → patch-cable shield back to unit A. The cable return resistance (tens of mΩ per cable, PA) carries each unit's full supply current, so the two GND references differ by I × R(cable). At 2–3 A that is tens of mV (PA), which appears in series with every patch signal between the two units. Audio-band supply-current changes appear as signal error, and charger switching ripple can couple into the loop.
- **If the returns are isolated:** each unit floats relative to the other until a patch cable connects them. The first patch cable then carries the units' Y-capacitor leakage and charger common-mode noise (switching frequency and harmonics). The patch connection becomes the ground reference.
- **Either way, inside one enclosure,** the bus board and module grounds (zudo-bus, OSC) also tie the units together. The loop area and the impedance of that tie decide the coupled noise. This is an enclosure-level design question, not a charger property.

Proposed measurements (not executed; each needs hardware-test approval):
- G1: DC resistance between the C-port returns of an unloaded, unplugged-from-mains charger (four-wire). Then repeat powered with dummy loads. Establishes common or isolated returns.
- G2: Ground-offset voltage between two units' GND on one charger at 0 / 1 / 3 A load each, with and without a patch cable, in the audio band and at the charger switching frequency.
- G3: Patch-signal error: a known signal from unit A to unit B; measure the error spectrum versus load steps on either unit.
- G4: Common-mode current in a patch-cable shield (current probe) with the charger on mains.
- G5: Repeat G2–G4 with each unit on its own charger, as a reference.

## 6. Proposed multiport test matrix (not executed; needs owner approval and hardware)

This extends M5 (source OCP behaviour) and M6 (all-rail behaviour) in [`power-limit-60w.md`](power-limit-60w.md#5-measurement-plan-not-executed-requires-owner-approval). Their methods and criteria apply; they are not copied here. Every row records Source_Capabilities and the contract with a PD analyzer, VBUS at the sink, VBUS_EN_SNK, POWER_OK2, every rail, and the time to all-rail off.

| ID | Case | Variations | Pass criterion (candidate) |
|---|---|---|---|
| MP1 | Per-port PDO capture | Each C port alone; every combination in section 2; each cable (3 A, 5 A e-marked) | Records the advertised PDOs; fills the UNAV cells in sections 2–3 |
| MP2 | Insertion order | The product first, then other devices; other devices first, then the product; which port gets 100 / 70 / 30 W | Contract and port allocation recorded; no rail out of band during attach |
| MP3 | Other-port plug and unplug | With the product at full load, plug and unplug a phone (USB-A), a laptop (USB-C) and a second product on every other port | If the contract survives: rails stay in band. If not: all rails off together within t_skew, latched, indication shown |
| MP4 | Renegotiation and downgrade | Forced reallocation from 100 W to 70, 65, 45 W; hard reset; VBUS interruption | As MP3; no rail ever left on while another is off; no partial brownout |
| MP5 | Thermal derating | Charger at the upper end of its stated operating temperature, 0–25 ℃ (32–77 ℉) per the User Guide (G-U: value read from the guide's text layer next to the Operating Temperature heading), with all ports loaded (ActiveShield) | As MP3 |
| MP6 | Recovery | After each MP3–MP5 event: return to an allocation that covers the contract | Restart only after a valid contract and the common start sequence; never auto-restart into a marginal contract |
| MP7 | Grounding | G1–G5 in section 5 | Recorded; acceptance limits set by OSC |

## 7. What this screen concludes

- **All multiport physical tests are NOT RUN.** Every multi-port verdict here is arithmetic on Anker's watt allocations and stays conditional on observing the required PDO on the port (15 V / 3 A for the current model, 20 V / 3 A for zudo-PD-60W, 20 V ≥ 3.5 A for C2).
- On that condition the A2683 has **two** candidate ports for full-OSC C2 units (two C ports, 100 + 100 W, 5 A e-marked cables). With three C devices, the 100 W port is a candidate and the 70 W port only if it advertises 20 V / 3.5 A. With four C devices, **none** is (65 W maximum).
- Usable capability depends on what else is plugged in, in what order, and on charger temperature. The rail behaviour on a downgrade is inferred, not measured. A product sold for multiport chargers needs the all-rail shutdown, latch and indication gates (GAP-6, GAP-9, M6) closed, and the MP1–MP6 matrix run.
- Charger-side facts that would change these verdicts are UNAV until MP1 is captured: per-allocation PDOs, the 70 W port's 20 V current, the 45 W port's 15 V current, port-position mapping, and reallocation mechanics.
- Grounding is a separate question. No low-noise or common-ground claim follows from a shared charger.
