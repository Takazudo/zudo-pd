---
name: component-renewal-input-protection
description: Use to audit exact SMAJ16A C74561 and SDT5A60SA-13 C3024223, their TVS clamp and diode voltage/current/thermal conditions, cathode orientation, manufacturer-derived footprints, and prototype-only protection scope.
---

# Prototype input protection components

Read all JSON files in this owner and run the central component validator.
Use circuit-spec-integration for whole-chain voltage, capacitor, gate, startup,
NVM and transient questions. The Diodes primary PDF and Littelfuse manufacturer-authored mirror were reviewed.
Littelfuse primary web text independently agrees, but direct binary retrieval was
denied; the registry retains that primary-binary evidence gap. Catalog identity
does not prove current stock.

SMAJ16A has 16 V standoff and a maximum 26 V clamp at 15.4 A,
10/1000 us, 25 C. Its typical VBR temperature coefficient is not a guaranteed bound or
VC coefficient. Do not represent 26 V as an unconditional rail ceiling.
The first NVM-programming attachment must use 5 V-only power; verify the
15 V-only policy before normal use. 20 V operation is unsupported. A pulse
power rating is not a continuous dissipation rating.

SDT5A60SA-13 has a 60 V reverse rating. Use the 0.52 V maximum forward drop
at 5 A and 25 C, not the catalog's 0.46 V typical figure. Its 5 A rating,
125 C leakage and thermal data have specific conditions.

Both parts map project pin 1 to the banded cathode at local negative X and
pin 2 to the anode. Their new canonical footprints follow their own
manufacturer mounting drawings; do not restore the generic imported lands.
The standard SMA model is illustrative and does not establish land geometry.

## Human component reference

[SMAJ16A](/docs/components/records/c74561/) and
[SDT5A60SA-13](/docs/components/records/c3024223/).
See the [catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/). The JSON bundle is authoritative.
