# Board P r3 — PD20 20 V input

Current `board-p.kicad_pcb` is the routed **20 V r3** input for **board-b20-draft only**.
`../../scripts/schgen/board_p_spec.py` owns its generated schematic. The 15 V shared module is
[`../board-p15/`](../board-p15/README.md); retired 15 V P r2 is in Git at `6cb02c8` and was never a physically built PD board.

## Interface and mechanical contract

Use [PD20 architecture](../../doc/src/content/docs/architecture/pd20.md) and exact executable nets for r3/B20.
The input intent is 20 V / 5 A with a 5 A e-marked cable and no degraded mode. Shared mounting/header positions
do not permit pairing r3 with PD15 Board B. B20 has no ATT; P1 is NC/PDOK/GND/NC.

## Circuit and configuration state

The adopted controller is STUSB4500 with r3 protection/front-end circuitry. NVM is **intent only**, no program-ready
binary: TDISPAR0V encoding and lower-current 20 V source behavior remain unresolved. The P15 15 V binary is not
an r3 provisioning recipe. See [PD20 verification](../../doc/src/content/docs/verification/pd20-verification.md).

## Checks and manufacturing state

[Current state](../../doc/src/content/docs/project/current-state.md) links revision-specific CAD/export receipts,
merged B20 fixes and open physical gates. P r3 still needs independent review. No order, programming or measurement
is established by routing or clean DRC. [Manufacturing status](../../manufacturing/pd20-status.md) retains the original
269-component B20 export receipt separately from current 270-component source.
