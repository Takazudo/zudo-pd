---
name: component-stm32g031f8p6
description: Resolve the exact STM32G031F8P6 MCU, subordinate PZ254V-11-05P SWD header, and DEALON DS254P-2X10-L0 ST-LINK/V2 adapter header. Use for pin mux, reset, boot, debug, ADC, timer, UART, package-pin, adapter, and programming-header questions.
---

# STM32G031F8P6 control domain

Run the central component-spec validator and read every JSON file here before applying a claim. Route only the exact MPN/LCSC identities. `sources.json` deliberately marks the ST documents unavailable because only normalized reader extracts, not the exact official PDF bytes, were retrievable; therefore their technical statements remain `UNVERIFIED`/`UNSOURCED` even where page and table locators are retained.

## Use boundaries

Treat each TSSOP package pin as one physical bond. PA11[PA9] and PA12[PA10] are SYSCFG software-remappable names, not bonded or slash aliases. Resolve alternate functions and ADC channel/sample-time constraints before firmware assignment. Preserve PA13/PA14 SWD reset pulls, the PA14/BOOT0 sharing hazard, reset-network behavior, option-byte uncertainty, debug low-power effects, and applicable errata. Do not infer programmed option bytes, clock tree, ADC sample time, timer mode, UART error handling, or bench state from the schematic.

The subordinate J3 header is hand-fit/DNP. Its primary product page/drawing establish connector ratings and dimensions; the project generator establishes the SWDIO, SWCLK, NRST, 3V3, and GND order. The connector record does not prove target voltage compatibility, programmer behavior, or whether J3 is fitted.

The subordinate C4749199 adapter header is also hand-fit/DNP. Its available
DEALON drawing establishes the reviewed 2x10 geometry, pin-1 side, central
shroud notch, and family ratings; the distributor page binds that drawing to
the exact orderable DS254P-2X10-L0 identity. The adapter generator locks VAPP
to target sense and keeps ST-LINK pin 19 isolated. UM1075's exact table locator
is retained, but its official PDF bytes are unavailable to the frozen bundle,
so the ST interface interpretation remains `UNSOURCED` and physical mating,
continuity, target sense, and live debugging remain `NEEDS BENCH`.

Use `interactions.json` for cross-domain constraints and `coverage.json` for explicit unknowns. A claim marked `UNSOURCED` is useful audit context, never a guaranteed design limit.

## Human component reference

Human projection of this bundle: [rec-c529334](/docs/components/records/c529334/), [rec-c492404](/docs/components/records/c492404/), [rec-c4749199](/docs/components/records/c4749199/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
