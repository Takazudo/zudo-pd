#!/usr/bin/env python3
"""
circuit-synth spike: re-model the zudo-pd `linear-regulation` sheet in Python.

This is Approach B of the "AI -> real .kicad_sch handoff" experiment (issue #75).
We model the three LDO stages of the production board as hierarchical
circuit-synth @circuit functions and emit a real KiCad project, then validate
the generated .kicad_sch headlessly with kicad-cli.

Topology mirrors /linear-regulation.kicad_sch (KiCad v10, version 20260306):

  +13.5V IN -> U6 L7812 -> (PTC1) -> +12V OUT
  +7.5V  IN -> U7 L7805 -> (PTC2) -> +5V  OUT
  -13.5V IN -> U8 7912  -> (PTC3) -> -12V OUT

Each stage: bulk electrolytic + film input cap, bulk electrolytic + 100nF HF
output cap, a series PTC resettable fuse on the output, a TVS clamp on the
labeled rail, and an indicator LED (R 1k -> LED -> GND).

NOTE on symbols: the production board uses a custom `zudo-pd:` symbol library
(L7812CD2T-TR, L7805ABD2T-TR, CJ7912_C94173). circuit-synth resolves symbols
against the *standard* KiCad symbol libraries, so this spike substitutes the
nearest standard equivalents:
    L7812  -> Regulator_Linear:L7812   (pins 3:IN 2:GND/pad 1:OUT  -- see below)
    L7805  -> Regulator_Linear:L7805
    L7912  -> Regulator_Linear:L7912   (negative reg: pin order differs)
Pin *names* (VI/GND/VO etc.) are used where possible so the netlist is robust
to pin-number differences between the standard and custom symbols.
"""

from circuit_synth import circuit, Component, Net


def regulator(symbol, ref, vin, vout, gnd,
              cin_bulk, cin_film, cout_bulk, cout_film,
              led_color, pin_in, pin_gnd, pin_out):
    """One LDO stage: reg + 4 caps + output PTC fuse + TVS clamp + indicator LED.

    `vin`/`vout`/`gnd` are the labeled rail Nets. The regulator OUT pin and its
    local caps/LED sit on an internal node; the labeled output rail is on the
    far side of the series PTC fuse (matches the production wiring).

    Pin names differ between the standard positive (78xx: IN/GND/OUT) and
    negative (79xx: VI/GND/VO, with a different *order*) symbols, so the caller
    passes the symbol's actual pin names.
    """
    reg = Component(symbol=symbol, ref=ref)

    # internal node between the regulator OUT pin and the series PTC fuse
    out_local = Net(f"{ref}_OUT_LOCAL")

    # --- regulator pins (names vary by symbol; see pin_* args) ---
    reg[pin_in] += vin
    reg[pin_gnd] += gnd
    reg[pin_out] += out_local

    # --- input bulk + film caps on the input rail ---
    c_in_b = Component(symbol="Device:C", ref="C", value=cin_bulk)
    c_in_b[1] += vin
    c_in_b[2] += gnd
    c_in_f = Component(symbol="Device:C", ref="C", value=cin_film)
    c_in_f[1] += vin
    c_in_f[2] += gnd

    # --- output bulk + HF caps on the local OUT node (before the fuse) ---
    c_out_b = Component(symbol="Device:C", ref="C", value=cout_bulk)
    c_out_b[1] += out_local
    c_out_b[2] += gnd
    c_out_f = Component(symbol="Device:C", ref="C", value=cout_film)
    c_out_f[1] += out_local
    c_out_f[2] += gnd

    # --- series PTC resettable fuse: OUT_LOCAL -> labeled rail ---
    ptc = Component(symbol="Device:Polyfuse", ref="F")
    ptc[1] += out_local
    ptc[2] += vout

    # --- TVS clamp from the labeled rail to GND ---
    tvs = Component(symbol="Device:D_TVS", ref="D")
    tvs[1] += vout
    tvs[2] += gnd

    # --- indicator: OUT_LOCAL -> R 1k -> LED -> GND ---
    r_led = Component(symbol="Device:R", ref="R", value="1k")
    led = Component(symbol="Device:LED", ref="LED", value=led_color)
    led_node = Net(f"{ref}_LED")
    r_led[1] += out_local
    r_led[2] += led_node
    led[1] += led_node   # anode
    led[2] += gnd        # cathode


@circuit(name="pos_12v_stage")
def pos_12v_stage(vin_13v5, v12_out, gnd):
    """U6 L7812: +13.5V -> +12V. Full topology (the reference stage)."""
    regulator(
        symbol="Regulator_Linear:L7812", ref="U6",
        vin=vin_13v5, vout=v12_out, gnd=gnd,
        cin_bulk="470uF", cin_film="470nF",      # C20/C14 bulk, (film on +12V uses 100nF set)
        cout_bulk="470uF", cout_film="100nF",    # C21 bulk, C17 100nF
        led_color="Green",                        # LED2
        pin_in="IN", pin_gnd="GND", pin_out="OUT",   # L7812 positive: IN/GND/OUT
    )


@circuit(name="pos_5v_stage")
def pos_5v_stage(vin_7v5, v5_out, gnd):
    """U7 L7805: +7.5V -> +5V."""
    regulator(
        symbol="Regulator_Linear:L7805", ref="U7",
        vin=vin_7v5, vout=v5_out, gnd=gnd,
        cin_bulk="470uF", cin_film="470nF",      # C22 bulk, C15 470nF
        cout_bulk="470uF", cout_film="100nF",    # C23 bulk, C18 100nF
        led_color="Blue",                         # LED3
        pin_in="IN", pin_gnd="GND", pin_out="OUT",   # L7805 positive: IN/GND/OUT
    )


@circuit(name="neg_12v_stage")
def neg_12v_stage(vin_n13v5, vn12_out, gnd):
    """U8 7912: -13.5V -> -12V (negative regulator)."""
    regulator(
        symbol="Regulator_Linear:L7912", ref="U8",
        vin=vin_n13v5, vout=vn12_out, gnd=gnd,
        cin_bulk="470uF", cin_film="470nF",      # C24 bulk, C16 470nF
        cout_bulk="470uF", cout_film="100nF",    # C25 bulk, C19 100nF
        led_color="Red",                          # LED4
        pin_in="VI", pin_gnd="GND", pin_out="VO",    # L7912 negative: GND/VI/VO (1/2/3)
    )


@circuit(name="linear_regulation")
def linear_regulation():
    """Top sheet: three LDO stages sharing GND, with the intermediate input
    rails and the final +12V/+5V/-12V output rails as named nets."""
    gnd = Net("GND")

    vin_13v5 = Net("+13.5V IN")
    vin_7v5 = Net("+7.5V IN")
    vin_n13v5 = Net("-13.5V IN")

    v12_out = Net("+12V OUT")
    v5_out = Net("+5V OUT")
    vn12_out = Net("-12V OUT")

    pos_12v_stage(vin_13v5, v12_out, gnd)
    pos_5v_stage(vin_7v5, v5_out, gnd)
    neg_12v_stage(vin_n13v5, vn12_out, gnd)


if __name__ == "__main__":
    c = linear_regulation()
    # Output goes ONLY under this experiment dir (never touches repo-root prod files).
    c.generate_kicad_project("generated_linear_regulation")
    print("generate_kicad_project() returned without raising.")
