#!/usr/bin/env python3
"""Fixed-fee delta of double-sided vs single-sided JLCPCB assembly for the r-next candidate.

Public pricing pages only (no quote, no upload, no account). Values transcribed from:
  https://jlcpcb.com/help/article/pcb-assembly-price ("Last updated on Oct 22, 2026"),
  https://jlcpcb.com/capabilities/pcb-assembly-capabilities, both retrieved 2026-10-31.
Per-joint SMT rates are the same for both services and cancel. PCB fabrication of the
panel that Standard PCBA needs (70 x 70 mm minimum) and the Basic/Extended class of each
part are not on these pages: they stay gaps.
Usage: python3 tools/assembly_cost.py > checks/assembly-cost.json
"""
import json
import runpy
import sys
from pathlib import Path

CAND = Path(__file__).resolve().parents[1]
PAGES = {"price": {"url": "https://jlcpcb.com/help/article/pcb-assembly-price", "sha256_html": "7b421c338f5fc6dee2f6fa43db13f1ec7dcac2a1c333969e083f62890a61838f"},
         "capabilities": {"url": "https://jlcpcb.com/capabilities/pcb-assembly-capabilities", "sha256_html": "bf6db4e087d7fb702363a3c1822f8392403223d7b64c16f48c308216d2d621cc"}}
ECONOMIC = {"assembly_types": "single sided placement only", "single_pcb_min_mm": [10, 10], "order_volume": "2-50 pcs",
            "setup": 8.18, "stencil": 1.53, "feeder_per_extended_type": 3.07, "fixture": 0.0}
STANDARD_DOUBLE = {"assembly_types": "single and double sided", "single_pcb_min_mm": [70, 70], "panel_min_mm": [70, 70],
                   "setup": 51.12, "stencil": 16.42, "feeder_per_type": 1.53, "fixture_1_29pcs": 16.42}


def main():
    spec = runpy.run_path(str(CAND / "board_p_rnext_spec.py"))
    fitted = {(c[1], c[2]) for r, c in spec["COMPONENTS"].items() if not r.startswith("#") and not c[4] and c[2]}
    types = len(fitted)
    eco_base = ECONOMIC["setup"] + ECONOMIC["stencil"]
    std = STANDARD_DOUBLE["setup"] + STANDARD_DOUBLE["stencil"] + STANDARD_DOUBLE["fixture_1_29pcs"] + STANDARD_DOUBLE["feeder_per_type"] * types
    rows = [{"extended_types": e, "economic_single_usd": round(eco_base + ECONOMIC["feeder_per_extended_type"] * e, 2),
             "standard_double_usd": round(std, 2), "delta_usd": round(std - eco_base - ECONOMIC["feeder_per_extended_type"] * e, 2)}
            for e in (0, types // 2, types)]
    out = {"status": "public list prices, per order, 1-29 boards; not a quote", "pages": PAGES, "economic": ECONOMIC,
           "standard_double_sided": STANDARD_DOUBLE, "fitted_part_types_with_lcsc": types, "fixed_fee_rows": rows,
           "gaps": ["Basic/Extended class per part (sets the Economic feeder fee)",
                    "panel fabrication cost: a 27 x 40 mm board is below the 70 x 70 mm Standard PCBA minimum, so it needs a panel",
                    "handling fee >= 14.93 USD applies only when both services are offered for one order"],
           "reading": "double-sided assembly forces Standard PCBA and a panel; the fixed fees alone add the delta below per order"}
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
