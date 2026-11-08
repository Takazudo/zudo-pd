# P15 r1 prototype order: owner handoff (2026-11-08)

This is the order-day checklist for the owner. It is desk preparation only: nothing has been ordered, quoted,
uploaded, programmed or energized, and no file below is validated, qualified or released. The full reasoning is in
the [2026-11-03 decision packet](p15-order-decision-packet.md); this page does not repeat or replace it.

## Upload exactly these P15 files from the fixed package

Package: `manufacturing/releases/corner-support-review/` (manifest `git_base` `3b9821b48cf4c77e8512ce653cada3db962d2c88`,
`SHA256SUMS` 151 entries). Only the `board-p15/` files are needed for this order.

| File | SHA-256 |
| --- | --- |
| `board-p15/board-p15-gerbers.zip` | `e68a133e2a3fa610758ed0e183fb9c4e77e4a4bfff7a9a6bac5cd1ab7f8c14ae` |
| `board-p15/bom.csv` | `23d6e2902307ce3920c405abe3296600610bcd5b54f0cca67ee0a8291ecfd59f` |
| `board-p15/cpl.csv` | `a9116d1b9f1d7f092531173a7c8f4d49f4a4c282b9a88f449a89b0da3e030ce6` |
| `board-p15/excluded.csv` (not uploaded; DNP D6/D7/R17/R18 and bare pads J2/J3) | `16d6146bd3ca6f3fbca8adbc4ddcddb176659dcd5d016a27a699b41467e9f616` |

Before uploading, run from the repository root:

```sh
(cd manufacturing/releases/corner-support-review && sha256sum -c SHA256SUMS)
python3 scripts/pcb/board-p15/verify-shared-reference.py --rev HEAD   # or the exact commit you order from
```

The first must report 151/151 OK. The second confirms that the P15 PCB, spec, NVM image and population files at that
revision are the ones recorded in [`boards/board-p15/shared-reference.json`](../boards/board-p15/shared-reference.json).
It is a byte-identity check only. Its frozen-lock line reports later repository changes as information; the
fabrication paths (PCB, spec, NVM) must match.

## Order two assembled P15 and reuse the existing boards

| Item | Quantity | Source |
| --- | --- | --- |
| P15 r1, assembled (PCBA) | **2** | New. JLCPCB PCBA minimum is 2 sets (owner rule 2026-11-03) |
| Board L | 0 new | Reuse the two 2026-09-19 boards (RS1 200 mΩ, MCU believed blank) |
| Board B | 0 new | Reuse the 2026-09-20 S3 board; count and condition are not yet recorded |

There is no spare: the first P15 that passes NVM acceptance is also an LED unit. The PD15 build receives an accepted
P15 after the LED stack. Do not substitute zudo-pd `boards/board-p/` (20 V Board P r3) or the LED repository's
historical `boards/board-p/`.

## Check D5 and D9 in the JLC placement preview

| Ref | Part | Must show |
| --- | --- | --- |
| D5 | SMAJ16A C74561 | Cathode stripe on the VBUS_IN pad (smaller X) |
| D9 | BZT52C18 C192739 | Cathode band on the VDD_LOC pad (smaller X) |

JLC places with its own library footprint, so the local result in
`manufacturing/readiness/p15-first-placement-orientation.json` does not prove the placed orientation. Check every
other polarized part in the same preview. If either is reversed, stop and correct the rotation in JLC's tool; do not
edit the frozen package.

## Re-check dated stock and cost on the order day

The latest evidence is the read-only catalog snapshot of **2026-11-03 19:12Z**
(`manufacturing/readiness/jlc-snapshot-2026-11-03-p15.json`, priced by `scripts/pcb/p15-order-scenarios.py`):
scenario A (2 × P15, no new Board B) is **USD 39.94 parts plus assembly**. PCB fabrication, shipping and duty were
UNKNOWN. Every P15 line covered 5 boards; the lowest was TYPE-C-31-M-17 C283540 at 1,165. Stock and prices are
five days old at this writing and must be read again at the order step.

## Run the arrival tests in this order (all NOT RUN)

1. Incoming, unpowered, each unit: D5 stripe and D9 band against silk, U1 and J1 seating, no bridges at U1.
2. NVM provisioning on a current-limited 5 V-only source with Board L and Board B disconnected: P15-NVM-1 to -5 and
   -7 in [Board P15 NVM Programming](../doc/src/content/docs/architecture/board-p15-programming.md). Pass is a
   power-cycle readback equal to SHA-256 `76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb`.
3. No-load PD acceptance (P15-NVM-6) on a PD source that also offers 20 V: 15 V contract, and VBUS_OUT measured off
   during the 5 V phase of attach. That measurement is required: the POWER_ONLY_ABOVE_5V bit position is third-party
   and an ST draft note marks it reserved (`manufacturing/pd20-evidence-research.md`).
4. Only then mate a passing unit with a Board L (zudo-led-lamp `firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md`
   first) or, later, with Board B after its unpowered check (`manufacturing/board-b-unpowered-check.md`).

Record each result with the unit identity in the current-state page. P15's missing hardware voltage window or eFuse
(R2.3, R2.4, R2.6 FAIL; R2.5 UNKNOWN) stays an accepted prototype residual, not a pass.
