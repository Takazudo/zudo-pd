# Printed accessories

The current [adhesive-leg prototype](adhesive-leg/README.md) supports Board B at
its four existing corner holes. Each leg has an 18 mm PCB seating height, a
14 × 14 × 2 mm adhesive base and a straight Ø7 mm pole. A screw
enters from the PCB back into the user's proven, untapped M3 aperture: the exact
27-vertex profile forms a 4.5 mm blind bore. There is no taper or larger lower
cavity. Start with an M3 × 5 mm screw: through the 1.6 mm PCB it inserts 3.4 mm,
leaving a nominal 1.1 mm gap to the blind floor. The previous M3 × 8 mm
recommendation does not apply to this shorter bore.

This taller prototype addresses the nominal height conflict of the earlier 11 mm
HC-11 support. Printing, adhesive strength, M3 passage and retention still require
physical checks. The existing PCB corner holes remain nominally 3.0 mm, giving
zero nominal diametral clearance for an M3 screw. The accessory does not change
the PCB or the frozen JLCPCB package. See its README and verification artifacts
for the prototype's scope and limits.

## Historical accessories

The current 110 × 85 mm Board B uses two top-side WJ500V-5.08-2P / C8465 screw-terminal
blocks and shrouded DEALON synth headers. It requires neither the old printed socket
guards nor the later underside Faston guard.

These files remain intact for revision history:

- [Faston guard](faston-cover/README.md): the superseded four-terminal guard,
  retaining caps, J8 shutter, fit coupons and rounded T-notch contract. Its generated
  PCB preview and verification reports apply only to that earlier revision.
- [Box-header accessories](box-header/README.md): historical printed synth-socket
  parts from the combined-board design.

Do not apply these edge cutouts, assembly models or fit results to the current
plain-edge screw-terminal board. Preserve the old source and generated files;
current manufacturing work belongs in `manufacturing/releases/corner-support-review/`.
