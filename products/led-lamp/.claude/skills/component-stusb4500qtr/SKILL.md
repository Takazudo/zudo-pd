---
name: component-stusb4500qtr
description: Audit the exact STUSB4500QTR USB-PD sink controller, PESD24VS1UB,115 CC protectors, and 0603WAF5101T5E external Rd option. Use for Board P power, USB-C, NVM, pin, reset, protection, DNP, bring-up, or substitution work.
---

# STUSB4500QTR bundle

Run the central offline validator, then read all seven local JSON artifacts. Resolve the controller and both DNP subordinates independently. Cite source and fact IDs with their conditions and locators.

Exact DS12499 Rev 8 and UM2650 Rev 3 bytes are reproducibly retained as `MANUFACTURER_MIRROR`. Their dependent controller claims remain `UNSOURCED` under the primary-only trust policy; programmed and as-built state remain open. The UNI-ROYAL external-Rd family specification and Nexperia protector specification are independently available, but they do not close controller behavior. Direct manufacturer-primary retrieval attempts from st.com were made on 2026-08-02 (canonical DS12499/UM2650 resource paths, the STUSB4500 product page, a legacy UM2650 URL, and a community.st.com mirror link: every st.com path timed out and the community.st.com link redirected to its forum homepage instead of the file) and again on 2026-08-14 (direct curl: HTTP/2 to the canonical DS12499 path failed with a stream error, and HTTP/1.1 retries of the DS12499 PDF, UM2650 PDF, and product page all timed out with 0 bytes while control fetches to other domains returned HTTP 200), so both sources stay `MANUFACTURER_MIRROR`/`SOURCE UNAVAILABLE` at primary and every dependent verdict stays `UNSOURCED`. Do not re-attempt from memory or treat these dated failures as permanent; a future session may retry the same URLs.

Pin 23 (VREG_2V7) is documented decoupling-only, but Board P's generator loads it with R15/R16 4.7k I2C pull-ups and exposes it on debug pogo pad J3.3 (net `U1.23 C30.2 R15.2 R16.2 J3.3`, fact `fact-stusb-vreg2v7-load`). This is an explicit open coverage item (`cov-stusb-vreg2v7-load`) requiring a manufacturer-primary locator authorizing external DC loading of this pin, or a re-route decision, plus confirmation that the NVM-programming jig's logic levels match 2.7 V; it must close before any NVM-programming bench work begins.

For controller work, separate unpowered/dead-battery, reset, configuration-load, normal attached, explicit-contract, fault/recovery, and disconnect states. Treat open-drain `0` as asserted and Hi-Z as deasserted. Do not infer the programmed NVM image: require a normalized 40-byte artifact, byte-for-byte readback, reset reload, full power-cycle reload, and negotiated-output bench evidence. Record the as-received factory image before any write. Check the current ST endurance limit before authorizing repeated writes; the retained record deliberately leaves endurance open.

Provision only with a current-limited source that satisfies the documented VDD or VSYS operating range and with a common-ground I2C programmer using the board pogo interface. Keep the load disconnected for first power and verify VBUS, gate polarity, discharge timing, CC state, and fault registers in stages. Volatile register edits are not persistent NVM proof.

Apply the netlist assertions in `interactions.json` exactly. A deterministic wrong pin, missing series discharge resistor, wrong PMOS polarity, or unsafe voltage is a blocker; state-dependent negotiation, timing, thermal behavior, ESD performance, and as-built NVM contents require bench evidence.

## Human component reference

Human projection of this bundle: [rec-stusb4500qtr](/docs/components/records/stusb4500qtr/), [rec-pesd24vs1ub](/docs/components/records/pesd24vs1ub/), [rec-rd-0603waf5101t5e](/docs/components/records/rd-0603waf5101t5e/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
