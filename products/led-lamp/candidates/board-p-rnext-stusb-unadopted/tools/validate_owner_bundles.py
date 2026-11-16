#!/usr/bin/env python3
"""Validate the candidate-local r-next owner bundles (UNADOPTED).

Checks, per bundle under ../owner-bundles/component-rnext-*:
  1. the repository's own component-spec-audit validate_bundle() with schema.json;
  2. SKILL.md frontmatter name equals the directory name;
  3. source/fact/record/route/pin-map/coverage/interaction IDs are unique across
     these bundles and the canonical .claude/skills bundles;
  4. every pin-map symbol pin exists in libraries/rnext.kicad_sym with the same name,
     every footprint pad exists in the footprint the spec assigns to that part, and
     every footprint pad is mapped;
  5. every PROJECT_GENERATOR source path exists and its sha256 equals the file now.
Exit 0 on success; prints one line per bundle.
"""
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

CAND = Path(__file__).resolve().parents[1]
ROOT = CAND.parents[1]
AUDIT = ROOT / ".claude/skills/component-spec-audit"


def load_validator():
    spec = importlib.util.spec_from_file_location("audit_validate", AUDIT / "scripts/validate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lib_table():
    table = {}
    for name, uri in re.findall(r'\(lib \(name "?([^")\s]+)"?\).*?\(uri "([^"]+)"\)', (CAND / "fp-lib-table").read_text()):
        table[name] = Path(uri.replace("${KIPRJMOD}", str(CAND))).resolve()
    return table


def footprint_pads(lib_id, table):
    nick, name = lib_id.split(":", 1)
    text = (table[nick] / f"{name}.kicad_mod").read_text()
    return name, {p for p in re.findall(r'\(pad "?([^"\s)]+)"?\s', text) if p}


def symbol_pins(symbol):
    text = (CAND / "libraries/rnext.kicad_sym").read_text()
    start = text.index(f'(symbol "{symbol}"')
    depth, end = 0, start
    for end in range(start, len(text)):
        depth += text[end] == "("
        depth -= text[end] == ")"
        if depth == 0:
            break
    block = text[start:end]
    return {num: name for name, num in re.findall(r'\(pin \w+ \w+.*?\(name "([^"]*)".*?\(number "([^"]+)"', block, re.S)}


def spec_components():
    sys.path.insert(0, str(CAND))
    try:
        import board_p_rnext_spec as spec  # noqa: E402
    finally:
        sys.path.pop(0)
    return spec.COMPONENTS


def main():
    v = load_validator()
    schema = v.load(AUDIT / "references/schema.json")
    table = lib_table()
    components = spec_components()
    canonical_ids = set()
    for skill in sorted((ROOT / ".claude/skills").glob("component-*")):
        if (skill / "manifest.json").exists():
            b = v.load_skill_bundle(skill)
            canonical_ids |= {r["record_id"] for r in b["records"]} | {s["source_id"] for s in b["sources"]} | {f["fact_id"] for f in b["facts"]}
    seen, failures = set(), 0
    for skill in sorted((CAND / "owner-bundles").glob("component-rnext-*")):
        errs = []
        try:
            bundle = v.load_skill_bundle(skill)
            v.validate_bundle(bundle, schema)
            v.frontmatter(skill / "SKILL.md", skill.name)
        except Exception as exc:  # report and continue with the next bundle
            errs.append(f"validate_bundle: {exc}")
            print(f"FAIL {skill.name}: {'; '.join(errs)}")
            failures += 1
            continue
        ids = [r["record_id"] for r in bundle["records"]] + [s["source_id"] for s in bundle["sources"]] + [f["fact_id"] for f in bundle["facts"]]
        ids += [x["coverage_id"] for x in bundle["coverage"]] + [x["route_id"] for x in bundle["routes"]]
        ids += [x["interaction_id"] for x in bundle["interactions"]] + [x["pin_map_id"] for x in bundle["pin_maps"]]
        dup = (set(ids) & seen) | (set(ids) & canonical_ids)
        if dup:
            errs.append(f"IDs collide with other bundles: {sorted(dup)[:5]}")
        seen |= set(ids)
        for record in bundle["records"]:
            refs = [ref for ref, row in components.items() if row[1] == record["mpn"] or row[2] == record["lcsc"]]
            if not refs:
                errs.append(f"{record['record_id']}: no spec component for {record['mpn']}")
                continue
            lib_ids = {components[ref][3] for ref in refs}
            symbols = {components[ref][0] for ref in refs}
            if len(lib_ids) != 1 or len(symbols) != 1:
                errs.append(f"{record['record_id']}: refs {refs} disagree on symbol/footprint")
                continue
            fp_name, pads = footprint_pads(lib_ids.pop(), table)
            pins = symbol_pins(symbols.pop())
            for mapping in (m for m in bundle["pin_maps"] if m["record_id"] == record["record_id"]):
                if mapping["footprint"] != fp_name:
                    errs.append(f"{mapping['pin_map_id']}: footprint {mapping['footprint']} != spec {fp_name}")
                mapped_pads = {p["footprint_pad"] for p in mapping["pins"]}
                if mapped_pads != pads:
                    errs.append(f"{mapping['pin_map_id']}: pads mapped {sorted(mapped_pads)} vs footprint {sorted(pads)}")
                for pin in mapping["pins"]:
                    if pins.get(pin["symbol_pin"]) != pin["name"]:
                        errs.append(f"{mapping['pin_map_id']}: symbol pin {pin['symbol_pin']} name {pin['name']} != {pins.get(pin['symbol_pin'])}")
        for source in bundle["sources"]:
            if source["authority_class"] != "PROJECT_GENERATOR":
                continue
            path = ROOT / source["authoritative_url"]
            if not path.is_file():
                errs.append(f"{source['source_id']}: missing {source['authoritative_url']}")
            elif sha(path) != source["sha256"]:
                errs.append(f"{source['source_id']}: sha256 stale for {source['authoritative_url']}")
        failures += bool(errs)
        print(("FAIL " if errs else "PASS ") + skill.name + (": " + "; ".join(errs) if errs else f" ({len(bundle['facts'])} facts)"))
    print(f"bundles={len(list((CAND / 'owner-bundles').glob('component-rnext-*')))} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
