"""Build candidate-local owner bundles for the 9 parts the r-next draft adds.

UNADOPTED parts are not inventory lines, so these bundles live under
owner-bundles/component-*/ (same 8-file schema as .claude/skills/component-*) and are
checked by tools/validate_owner_bundles.py with the repository validator's own
validate_bundle(). Moving one into .claude/skills is the adoption step of
component-spec-audit/references/new-component-workflow.md and is not done here.

Sources
- 7 parts reuse the zudo-pd @3ac13d46 bundle evidence (manufacturer and distributor
  identity sources and their PRIMARY-SPEC / DISTRIBUTOR-IDENTITY facts) by citation.
  Each primary PDF was re-fetched on 2026-10-31 and its SHA-256 equals the PD record
  (REFETCH below). zudo-pd project facts (roles, PD lands) are not imported.
- TPS259474LRPWR and TPS3701DDCT are new records from the re-fetched TI datasheets.
Usage (LED repo root):
  python3 .../tools/build_owner_bundles.py <dir with zudo-pd skill bundles from git show>
"""
import hashlib
import json
import os
import runpy
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'owner-bundles')
REL = os.path.relpath(HERE, ROOT)
DATE = '2026-10-31'
PD = 'zudo-pd@3ac13d462bd7bdbf06a07b4716d9c94306f8bca4'

# skill, PD bundle, PD record, LED refs, function alias, LED role sentence
IMPORTED = [
    ('component-rnext-dmp3036sfg-7', 'component-diodes-dmp3036sfg-7', 'rec-c461081', ['Q1'],
     'LED r-next sink-path P-channel MOSFET',
     'Q1: STUSB4500 VBUS_EN_SNK-driven sink switch; source VBUS_P (pins 1-3), gate Q1_G (4), drain VBUS_OUT (5-9) feeding the LED voltage window U4.'),
    ('component-rnext-tps16630pwpr', 'component-board-p-r3-candidates', 'rec-c1849461', ['U2'],
     'LED r-next input efuse',
     'U2: front-end eFuse from EF_IN to the protected node VBUS_P; OVP 174k/10k, UVLO 11.5k/4.02k, ILIM 4.02k, MODE open (latch), as in the zudo-pd r3 common block.'),
    ('component-rnext-lm74700qdbvrq1', 'component-ti-board-b-limiter-candidates', 'rec-c2941042', ['U3'],
     'LED r-next ideal-diode controller',
     'U3: ideal-diode controller for Q3; ANODE and EN on VBUS_IN, CATHODE on EF_IN, GATE on EF_GATE, VCAP via C37, as in the zudo-pd r3 common block.'),
    ('component-rnext-tvs2200drvr', 'component-tvs2200drvr', 'rec-c523793', ['D5'],
     'LED r-next connector-side TVS',
     'D5: VBUS_IN clamp at the USB-C connector (pins 4-6 IN, 1-3 and 7 GND); the only guaranteed bound on the protected node (PD gate L7 OPEN).'),
    ('component-rnext-csd18543q3a', 'component-csd18543q3a', 'rec-c840100', ['Q3'],
     'LED r-next reverse-blocking N-channel MOSFET',
     'Q3: LM74700-driven reverse-blocking FET; source VBUS_IN (1-3), gate EF_GATE (4), drain EF_IN (5-9).'),
    ('component-rnext-bss138-7-f', 'component-diodes-bss138-7-f', 'rec-c40912', ['Q5'],
     'LED r-next Q1 soft-start body-diode element',
     'Q5: gate and source on Q1_MX, drain on Q1_G; body diode couples C36 Miller feedback into Q1 gate during turn-on.'),
    ('component-rnext-bzt52c11-7-f', 'component-bzt52c11-c92321', 'rec-bzt52c11-c92321', ['D8'],
     'LED r-next Q1 gate clamp zener',
     'D8: cathode (1) on VBUS_P, anode (2) on Q1_G; limits Q1 VGS magnitude to the zener window.'),
]

REFETCH = {  # LED worker re-fetch 2026-10-31 (PDF bytes, first bytes %PDF-)
    'https://www.diodes.com/assets/Datasheets/DMP3036SFG.pdf': '7d68df47a051',
    'https://www.ti.com/lit/ds/symlink/tps1663.pdf': '8f91a0db2daf',
    'https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf': 'e16b3a8c0023',
    'https://www.ti.com/lit/ds/symlink/tvs2200.pdf': '84c986c9cc4f',
    'https://www.ti.com/lit/ds/symlink/csd18543q3a.pdf': '119cdef27d2c',
    'https://www.diodes.com/assets/Datasheets/ds30144.pdf': 'c93dcb33f414',
    'https://www.diodes.com/assets/Datasheets/ds18004.pdf': '0fbd7d137524',
}


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def load(path):
    with open(path) as f:
        return json.load(f)


def write(skill, name, obj):
    os.makedirs(os.path.join(OUT, skill), exist_ok=True)
    with open(os.path.join(OUT, skill, name), 'w') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


SPEC = runpy.run_path(os.path.join(HERE, 'board_p_rnext_spec.py'))
NET_OF = {node: net for net, nodes in SPEC['NETS'].items() for node in nodes}
SPEC_PATH = os.path.join(HERE, 'board_p_rnext_spec.py')
LAND_PATH = os.path.join(HERE, 'checks', 'land-check.json')
LANDS = {row['refdes']: row for row in load(LAND_PATH)['lands']}


def symbol_pins(symbol):
    sys.path.insert(0, os.path.join(ROOT, 'scripts', 'schgen'))
    import schgen_core
    lib = schgen_core.Library(os.path.join(HERE, 'libraries', 'rnext.kicad_sym'))
    return [(p[0], p[1]) for p in lib.pins_of(symbol)]


def project_sources(key, rid):
    return [
        {'source_id': f'src-{key}-led-rnext-spec', 'record_id': rid,
         'document_title': 'LED Board P r-next candidate generator specification (UNADOPTED)',
         'document_number': 'board_p_rnext_spec.py', 'revision': 'phase-10 working tree (see git log of this file)',
         'document_date': DATE, 'authoritative_url': f'{REL}/board_p_rnext_spec.py', 'alternate_authoritative_url': '',
         'retrieval_date': DATE, 'authority_class': 'PROJECT_GENERATOR', 'sha256': sha(SPEC_PATH), 'availability': 'AVAILABLE',
         'physical_pdf_page_index': 0, 'printed_page_label': 'source', 'locator': 'COMPONENTS and NETS rows for the listed refdes',
         'evidence_extract': 'Candidate refdes, footprint and net assignment; UNADOPTED, not an inventory line.'},
        {'source_id': f'src-{key}-led-land-check', 'record_id': rid,
         'document_title': 'LED r-next manufacturer land comparison', 'document_number': 'checks/land-check.json',
         'revision': 'phase-10', 'document_date': DATE, 'authoritative_url': f'{REL}/checks/land-check.json',
         'alternate_authoritative_url': '', 'retrieval_date': DATE, 'authority_class': 'PROJECT_GENERATOR',
         'sha256': sha(LAND_PATH), 'availability': 'AVAILABLE', 'physical_pdf_page_index': 0, 'printed_page_label': 'json',
         'locator': 'lands[] row for the listed refdes', 'evidence_extract': 'Pad geometry of the selected footprint versus the manufacturer land drawing.'},
    ]


def land_summary(ref):
    rows = [r for k, r in LANDS.items() if k == ref or k == f'{ref} (selected draft)']
    sel = SPEC['COMPONENTS'][ref][3]
    chosen = next(r for r in rows if r['footprint'] == sel)
    return sel, chosen['verdict'], chosen


def project_facts(key, rid, refs, role):
    ref = refs[0]
    sel, verdict, chosen = land_summary(ref)
    diffs = [f"{c['check']}: drawing {c['expected']} vs land {c['footprint']}" for c in chosen['checks'] if c['result'] != 'MATCH']
    return [
        {'fact_id': f'fact-{key}-led-rnext-role', 'record_id': rid, 'source_id': f'src-{key}-led-rnext-spec',
         'class': 'PROJECT_STATE', 'value': role, 'unit': 'NONE',
         'conditions': 'UNADOPTED LED Board P r-next schematic draft; no PCB, no assembly, nothing energized',
         'locator': f'COMPONENTS row {ref} and NETS rows containing {ref}', 'provenance': 'PROJECT-CHOICE',
         'verdict': 'NEEDS BENCH', 'depends_on': [], 'expression': ''},
        {'fact_id': f'fact-{key}-led-land', 'record_id': rid, 'source_id': f'src-{key}-led-land-check',
         'class': 'PROJECT_STATE',
         'value': f'{sel}: {verdict} against {chosen["locator"]}' + ('' if not diffs else '; ' + '; '.join(diffs)),
         'unit': 'NONE', 'conditions': 'Pad geometry only (TOL 0.011 mm); solder mask, paste and assembly yield are not checked',
         'locator': f'lands[] row {chosen["refdes"]}', 'provenance': 'PROJECT-CHOICE', 'verdict': 'NEEDS BENCH',
         'depends_on': [], 'expression': ''},
    ]


def pin_map(key, rid, ref, symbol, footprint, reviewed):
    pins = []
    for num, name in symbol_pins(symbol):
        node = f'{ref}.{num}'
        net = NET_OF.get(node, 'NC' if node in SPEC['NO_CONNECT'] else 'UNASSIGNED')
        pins.append({'symbol_pin': num, 'name': name, 'footprint_pad': num, 'function': f'{name} / {net}'})
    return {'pin_map_id': f'pinmap-{key}', 'record_id': rid, 'symbol': symbol, 'footprint': footprint,
            'pins': pins, 'reviewed_by': reviewed}


def common_parts(skill, key, rid, refs, primary_ids, project_ids, open_extra=None, open_blocking=None):
    coverage = [
        {'coverage_id': f'cov-{key}-primary', 'record_id': rid, 'domain': 'primary-specification', 'status': 'COVERED',
         'reason': 'Manufacturer datasheet re-fetched 2026-10-31 by the LED worker; ratings and pin table read from it',
         'fact_ids': primary_ids, 'blocking_fact_ids': []},
        {'coverage_id': f'cov-{key}-led-application', 'record_id': rid, 'domain': 'led-rnext-application', 'status': 'OPEN',
         'reason': 'UNADOPTED schematic draft: placement, copper, thermal, land assembly and bench behaviour are not established',
         'fact_ids': project_ids, 'blocking_fact_ids': project_ids},
    ]
    if open_extra:
        coverage.append(open_extra)
    domains = [c['domain'] for c in coverage if c['status'] == 'OPEN']
    interactions = [{'interaction_id': f'int-{key}-led-rnext', 'record_ids': [rid], 'fact_ids': project_ids,
                     'conditions': f'{", ".join(refs)} in the LED r-next draft: verify exported netlist, land, orientation and bench behaviour before any adoption',
                     'verdict': 'NEEDS BENCH'}]
    return coverage, domains, interactions


def build_imported(pd_root, skill, pd_skill, rid, refs, function, role):
    src_all = load(os.path.join(pd_root, pd_skill, 'sources.json'))['sources']
    fact_all = load(os.path.join(pd_root, pd_skill, 'facts.json'))['facts']
    rec = next(r for r in load(os.path.join(pd_root, pd_skill, 'manifest.json'))['records'] if r['record_id'] == rid)
    sources = [dict(s) for s in src_all if s['record_id'] == rid and s['authority_class'] in ('MANUFACTURER_PRIMARY', 'DISTRIBUTOR_IDENTITY')]
    for s in sources:
        s['imported_from'] = f'{PD}:.claude/skills/{pd_skill}/sources.json#{s["source_id"]}'
        if s['authority_class'] == 'MANUFACTURER_PRIMARY':
            want = REFETCH[s['authoritative_url']]
            assert s['sha256'].startswith(want), f'{skill}: PD hash {s["sha256"][:12]} != re-fetch {want}'
            s['led_refetch'] = f'{DATE}: re-fetched by the LED worker, SHA-256 identical'
    kept = {s['source_id'] for s in sources}
    facts = [dict(f) for f in fact_all if f['record_id'] == rid and f['source_id'] in kept
             and f['provenance'] in ('PRIMARY-SPEC', 'DISTRIBUTOR-IDENTITY')]
    key = skill.replace('component-rnext-', '')
    ref = refs[0]
    symbol, _value, lcsc, footprint, _dnp, _pos = SPEC['COMPONENTS'][ref]
    sources += project_sources(key, rid)
    facts += project_facts(key, rid, refs, role)
    primary_ids = [f['fact_id'] for f in facts if f['provenance'] in ('PRIMARY-SPEC', 'DISTRIBUTOR-IDENTITY')]
    project_ids = [f'fact-{key}-led-rnext-role', f'fact-{key}-led-land']
    coverage, domains, interactions = common_parts(skill, key, rid, refs, primary_ids, project_ids)
    record = {k: rec[k] for k in ('record_id', 'kind', 'parent_record_id', 'mpn', 'manufacturer', 'lcsc')}
    record.update({'line_id': None, 'candidate_id': f'cand-rnext-{lcsc.lower()}', 'package': footprint.split(':', 1)[1],
                   'source_ids': [s['source_id'] for s in sources], 'fact_ids': [f['fact_id'] for f in facts],
                   'interaction_ids': [i['interaction_id'] for i in interactions], 'open_domains': domains,
                   'refdes': refs, 'imported_from': f'{PD}:.claude/skills/{pd_skill}/manifest.json#{rid}'})
    assert lcsc == rec['lcsc'], f'{skill}: spec LCSC {lcsc} != PD record {rec["lcsc"]}'
    routes = [{'route_id': f'route-{key}', 'record_id': rid,
               'aliases': {'mpn': [rec['mpn']], 'lcsc': [rec['lcsc']], 'manufacturer': [rec['manufacturer']], 'function': [function]},
               'positive': [rec['mpn'], rec['lcsc'], f'{rec["manufacturer"]} {rec["mpn"]}'],
               'negative': [f'{rec["mpn"]} C999999999', f'WrongVendor {rec["mpn"]}']}]
    pmap = pin_map(key, rid, ref, symbol, footprint.split(':', 1)[1],
                   f'{DATE} LED worker: rnext.kicad_sym pins of {symbol} vs pads of {footprint}; manufacturer pin table per the imported primary source locator')
    return record, sources, facts, coverage, routes, interactions, [pmap]


def ti_source(sid, rid, title, number, rev, date, url, path, page, label, locator, extract):
    return {'source_id': sid, 'record_id': rid, 'document_title': title, 'document_number': number, 'revision': rev,
            'document_date': date, 'authoritative_url': url, 'alternate_authoritative_url': '', 'retrieval_date': DATE,
            'authority_class': 'MANUFACTURER_PRIMARY', 'sha256': sha(path) if path else '', 'availability': 'AVAILABLE',
            'physical_pdf_page_index': page, 'printed_page_label': label, 'locator': locator, 'evidence_extract': extract}


def pf(fid, rid, sid, cls, value, unit, cond, loc):
    return {'fact_id': fid, 'record_id': rid, 'source_id': sid, 'class': cls, 'value': value, 'unit': unit,
            'conditions': cond, 'locator': loc, 'provenance': 'PRIMARY-SPEC', 'verdict': 'PASS - primary-source confirmed',
            'depends_on': [], 'expression': ''}


TI_SHA = {'tps25947': '8f96de389903091650d4f462dcfad3210071c3ae7093623a7978f34baf8a65b4',
          'tps3701': '27c94a6c3a243bf539e98942d26f0bd9ed979c5775c12cf86b7c1a8c3d7d9560'}
V196_BOM = os.path.join(ROOT, 'candidates/board-p-v196-unadopted/BOM-TRIAL.csv')


def build_new(skill, key, rid, ref, mpn, function, role, src, facts_spec, lcsc_note):
    symbol, _value, lcsc, footprint, _dnp, _pos = SPEC['COMPONENTS'][ref]
    sources = [src]
    sources.append({'source_id': f'src-{key}-v196-bom', 'record_id': rid, 'document_title': 'V196 trial BOM (UNADOPTED candidate)',
                    'document_number': 'BOM-TRIAL.csv', 'revision': 'as committed', 'document_date': DATE,
                    'authoritative_url': 'candidates/board-p-v196-unadopted/BOM-TRIAL.csv', 'alternate_authoritative_url': '',
                    'retrieval_date': DATE, 'authority_class': 'PROJECT_GENERATOR', 'sha256': sha(V196_BOM), 'availability': 'AVAILABLE',
                    'physical_pdf_page_index': 0, 'printed_page_label': 'csv', 'locator': lcsc_note,
                    'evidence_extract': f'{mpn} listed with LCSC {lcsc}; no distributor page retained by the LED worker.'})
    sources += project_sources(key, rid)
    facts = [pf(f'fact-{key}-manufacturer', rid, src['source_id'], 'PROJECT_STATE', 'Texas Instruments', 'NONE',
                'exact TI part; document title block', f'{src["source_id"]}: title block page 1')]
    facts += [pf(f'fact-{key}-{fid}', rid, src['source_id'], cls, val, unit, cond, loc) for fid, cls, val, unit, cond, loc in facts_spec]
    facts.append({'fact_id': f'fact-{key}-lcsc-identity', 'record_id': rid, 'source_id': f'src-{key}-v196-bom', 'class': 'PROJECT_STATE',
                  'value': f'LCSC {lcsc} carried from the V196 trial BOM', 'unit': 'NONE',
                  'conditions': 'No distributor identity page retrieved; LCSC listing, stock and assembly class unconfirmed',
                  'locator': f'BOM-TRIAL.csv row {lcsc_note}', 'provenance': 'UNVERIFIED', 'verdict': 'UNSOURCED',
                  'depends_on': [], 'expression': ''})
    facts += project_facts(key, rid, [ref], role)
    primary_ids = [f['fact_id'] for f in facts if f['provenance'] == 'PRIMARY-SPEC']
    project_ids = [f'fact-{key}-led-rnext-role', f'fact-{key}-led-land']
    extra = {'coverage_id': f'cov-{key}-distributor', 'record_id': rid, 'domain': 'distributor-identity', 'status': 'OPEN',
             'reason': f'LCSC {lcsc} is UNSOURCED: carried from the V196 trial BOM without a retained distributor page',
             'fact_ids': [f'fact-{key}-lcsc-identity'], 'blocking_fact_ids': [f'fact-{key}-lcsc-identity']}
    coverage, domains, interactions = common_parts(skill, key, rid, [ref], primary_ids, project_ids, extra)
    record = {'record_id': rid, 'line_id': None, 'candidate_id': f'cand-rnext-{lcsc.lower()}', 'kind': 'standalone',
              'parent_record_id': None, 'mpn': mpn, 'manufacturer': 'Texas Instruments', 'lcsc': lcsc,
              'package': footprint.split(':', 1)[1], 'source_ids': [s['source_id'] for s in sources],
              'fact_ids': [f['fact_id'] for f in facts], 'interaction_ids': [i['interaction_id'] for i in interactions],
              'open_domains': domains, 'refdes': [ref]}
    routes = [{'route_id': f'route-{key}', 'record_id': rid,
               'aliases': {'mpn': [mpn], 'lcsc': [lcsc], 'manufacturer': ['Texas Instruments'], 'function': [function]},
               'positive': [mpn, lcsc, f'Texas Instruments {mpn}'],
               'negative': [f'{mpn} C999999999', f'WrongVendor {mpn}']}]
    pmap = pin_map(key, rid, ref, symbol, footprint.split(':', 1)[1],
                   f'{DATE} LED worker: {src["document_number"]} pin table vs rnext.kicad_sym {symbol} and {footprint} pads')
    return record, sources, facts, coverage, routes, interactions, [pmap]


def emit(skill, parts, summary):
    record, sources, facts, coverage, routes, interactions, pin_maps = parts
    write(skill, 'manifest.json', {'schema_version': 1, 'skill': skill, 'records': [record]})
    write(skill, 'sources.json', {'schema_version': 1, 'sources': sources})
    write(skill, 'facts.json', {'schema_version': 1, 'facts': facts})
    write(skill, 'coverage.json', {'schema_version': 1, 'coverage': coverage})
    write(skill, 'routing.json', {'schema_version': 1, 'routes': routes})
    write(skill, 'interactions.json', {'schema_version': 1, 'interactions': interactions})
    write(skill, 'pin-map.json', {'schema_version': 1, 'pin_maps': pin_maps})
    with open(os.path.join(OUT, skill, 'SKILL.md'), 'w') as f:
        f.write(f'---\nname: {skill}\ndescription: UNADOPTED candidate evidence owner for {record["mpn"]} ({record["lcsc"]}) in the LED Board P r-next draft ({", ".join(record["refdes"])}). Not an inventory line. Use when reviewing or adopting this r-next part.\n---\n\n'
                f'# {record["mpn"]} — LED r-next candidate owner (UNADOPTED)\n\n{summary}\n\n'
                'The JSON files are authoritative. This bundle lives under the candidate directory because the part is not '
                'placed by a canonical generator spec; adoption moves it to `.claude/skills/` through '
                '`component-spec-audit/references/new-component-workflow.md`.\n')


def main(pd_root):
    for skill, pd_skill, rid, refs, function, role in IMPORTED:
        emit(skill, build_imported(pd_root, skill, pd_skill, rid, refs, function, role),
             f'Primary and distributor evidence imported by citation from `{PD}` `.claude/skills/{pd_skill}`; the primary PDF was re-fetched and hash-matched on {DATE}.')
    src = ti_source('src-tps259474l-primary', 'rec-tps259474l', 'TPS25947xx 2.7-V to 23-V, 5.5-A, 28-mOhm eFuse', 'SLVSFC9C',
                    'C (revised May 2026)', '2026-05-01', 'https://www.ti.com/lit/ds/symlink/tps25947.pdf', None, 6, '7',
                    'Section 4 Device Comparison Table; Table 5-1 Pin Functions; Section 6.1, 6.3 and 6.5 tables',
                    'TPS259474LRPW: OVLO, PG/PGTH, latch-off. Pins 1 EN/UVLO, 2 OVLO, 3 PG, 4 PGTH, 5 IN, 6 OUT, 7 DVDT, 8 GND, 9 ILM, 10 ITIMER. Abs max VIN 28 V; ROC VIN 2.7-23 V, OVLO 0.5-1.5 V, RILM 549-6650 Ohm, IMAX 5.5 A; VUVLO(R)/VOV(R) 1.183/1.20/1.223 V, VUVLO(F)/VOV(F) 1.076/1.09/1.116 V; ILIM 0.850/1.007/1.150 A at RILM 3.32k.')
    src['sha256'] = TI_SHA['tps25947']
    emit('component-rnext-tps259474lrpwr', build_new(
        'component-rnext-tps259474lrpwr', 'tps259474l', 'rec-tps259474l', 'U4', 'TPS259474LRPWR', 'LED r-next voltage-window efuse',
        'U4: LED voltage-window eFuse; IN on VBUS_OUT after Q1, OUT on LED_OUT to JOUT1.1/.2; EN/UVLO 97.6k/10k with U5 OUTA, OVLO 133k/10k, ILM R38 per OPTION, DVDT R30 100R + C41 22 nF.',
        src, [
            ('variant', 'PROJECT_STATE', 'TPS259474LRPW: overvoltage response OVLO, PG/PGTH outputs, latch-off fault response', 'NONE', 'Device Comparison Table row TPS259474LRPW', 'src-tps259474l-primary: Section 4 Device Comparison Table row TPS259474LRPW'),
            ('pinout', 'PROJECT_STATE', '1 EN/UVLO, 2 OVLO, 3 PG, 4 PGTH, 5 IN, 6 OUT, 7 DVDT, 8 GND, 9 ILM, 10 ITIMER', 'NONE', 'RPW 10-pin VQFN-HR', 'src-tps259474l-primary: Table 5-1 Pin Functions pins 1-10'),
            ('vin-absmax', 'ABSOLUTE_MAXIMUM', 28, 'V', 'IN pin, -40 to 125 degC TJ', 'src-tps259474l-primary: Section 6.1 table row VIN'),
            ('vin-operating', 'RECOMMENDED_OPERATION', '2.7 / 23 (min/max)', 'V', 'IN pin', 'src-tps259474l-primary: Section 6.3 table row VIN'),
            ('ovlo-pin-operating', 'RECOMMENDED_OPERATION', '0.5 / 1.5 (min/max)', 'V', 'OVLO pin', 'src-tps259474l-primary: Section 6.3 table row VOVLO'),
            ('rilm-range', 'RECOMMENDED_OPERATION', '549 / 6650 (min/max)', 'Ohm', 'ILM pin resistance', 'src-tps259474l-primary: Section 6.3 table row RILM'),
            ('uvlo-rising', 'GUARANTEED_ELECTRICAL', '1.183 / 1.20 / 1.223 (min/typ/max)', 'V', 'TJ -40 to 125 degC', 'src-tps259474l-primary: Section 6.5 table row VUVLO(R)'),
            ('uvlo-falling', 'GUARANTEED_ELECTRICAL', '1.076 / 1.09 / 1.116 (min/typ/max)', 'V', 'TJ -40 to 125 degC', 'src-tps259474l-primary: Section 6.5 table row VUVLO(F)'),
            ('ov-rising', 'GUARANTEED_ELECTRICAL', '1.183 / 1.20 / 1.223 (min/typ/max)', 'V', 'TJ -40 to 125 degC', 'src-tps259474l-primary: Section 6.5 table row VOV(R)'),
            ('ov-falling', 'GUARANTEED_ELECTRICAL', '1.076 / 1.09 / 1.116 (min/typ/max)', 'V', 'TJ -40 to 125 degC', 'src-tps259474l-primary: Section 6.5 table row VOV(F)'),
            ('ilim-3k32', 'GUARANTEED_ELECTRICAL', '0.850 / 1.007 / 1.150 (min/typ/max)', 'A', 'RILM = 3.32 kOhm exactly; resistor tolerance not included', 'src-tps259474l-primary: Section 6.5 table row ILIM, RILM = 3.32k'),
            ('ilim-1k65', 'GUARANTEED_ELECTRICAL', '1.800 / 2.028 / 2.200 (min/typ/max)', 'A', 'RILM = 1.65 kOhm exactly', 'src-tps259474l-primary: Section 6.5 table row ILIM, RILM = 1.65k'),
        ], 'row U2 TPS259474LRPWR'),
        'New record from TI SLVSFC9C (re-fetched 2026-10-31, SHA-256 matching the V196 SOURCES.json record).')
    src = ti_source('src-tps3701-primary', 'rec-tps3701', 'TPS3701 High-Voltage (36-V) Window Comparator', 'SBVS240C',
                    'C (revised February 2019)', '2019-02-01', 'https://www.ti.com/lit/ds/symlink/tps3701.pdf', None, 4, '5',
                    'Pin Functions table; Section 6.1, 6.3 and 6.5 tables',
                    'Pins 1 OUTA, 2 GND, 3 INA, 4 INB, 5 VDD, 6 OUTB. Abs max VDD 40 V; ROC VDD 1.8-36 V; VIT-(INA) 397/400/403 mV; VIT+(INA) 400/405.5/413 mV; IIN +/-25 nA at 6.5 V; ID(leak) 300 nA max at VOUT 25 V.')
    src['sha256'] = TI_SHA['tps3701']
    emit('component-rnext-tps3701ddct', build_new(
        'component-rnext-tps3701ddct', 'tps3701', 'rec-tps3701', 'U5', 'TPS3701DDCT', 'LED r-next window undervoltage monitor',
        'U5: VDD on VBUS_OUT; INA senses VBUS_OUT through R35 133k + R36 187k / R37 10k; OUTA open drain on WIN_EN_UVLO (U4 EN); INB to GND, OUTB NC.',
        src, [
            ('pinout', 'PROJECT_STATE', '1 OUTA, 2 GND, 3 INA, 4 INB, 5 VDD, 6 OUTB', 'NONE', 'DDC 6-pin SOT', 'src-tps3701-primary: Pin Functions table pins 1-6'),
            ('vdd-absmax', 'ABSOLUTE_MAXIMUM', 40, 'V', 'VDD pin', 'src-tps3701-primary: Section 6.1 table row VDD'),
            ('vdd-operating', 'RECOMMENDED_OPERATION', '1.8 / 36 (min/max)', 'V', 'VDD supply', 'src-tps3701-primary: Section 6.3 table row VDD'),
            ('ina-falling', 'GUARANTEED_ELECTRICAL', '397 / 400 / 403 (min/typ/max)', 'mV', 'VDD = 1.8 V to 36 V', 'src-tps3701-primary: Section 6.5 table row VIT-(INA)'),
            ('ina-rising', 'GUARANTEED_ELECTRICAL', '400 / 405.5 / 413 (min/typ/max)', 'mV', 'VDD = 1.8 V to 36 V', 'src-tps3701-primary: Section 6.5 table row VIT+(INA)'),
            ('iin', 'GUARANTEED_ELECTRICAL', '-25 / 25 (min/max)', 'nA', 'VINA = 6.5 V, VDD 1.8 V and 36 V', 'src-tps3701-primary: Section 6.5 table row IIN'),
            ('out-leak', 'GUARANTEED_ELECTRICAL', 300, 'nA', 'max, VDD 1.8 V and 36 V, VOUT = 25 V', 'src-tps3701-primary: Section 6.5 table row ID(leak)'),
        ], 'row UMON TPS3701DDCT'),
        'New record from TI SBVS240C (re-fetched 2026-10-31, SHA-256 matching the V196 SOURCES.json record).')
    print('wrote', sorted(os.listdir(OUT)))


if __name__ == '__main__':
    main(sys.argv[1])
