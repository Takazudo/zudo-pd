"""Build libraries/rnext.kicad_sym from pinned symbol sources (no symbol is edited).

Usage (from the LED repo root; the zudo-pd file is read with git show, never modified):
  git -C ../zudo-pd show 3ac13d462bd7bdbf06a07b4716d9c94306f8bca4:symbols/zudo-pd.kicad_sym > /tmp/x/zudo-pd.kicad_sym
  python3 candidates/board-p-rnext-stusb-unadopted/tools/build_library.py /tmp/x/zudo-pd.kicad_sym /tmp/x/power.kicad_sym
where power.kicad_sym is /usr/share/kicad/symbols/power.kicad_sym copied out of the pinned
KiCad 10.0.6 image (kicad/kicad@sha256:18693567...), used only for the stock PWR_FLAG.
Source priority per symbol: LED library, then V196 candidate libraries, then zudo-pd @3ac13d46.
A symbol present in more than one source must have identical pin numbers and names.
"""
import hashlib
import importlib.util
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'schgen'))
import schgen_core  # noqa: E402

PD_SYM_SHA256 = '75c1f65bcbb733d54410a8637c346a25168bfeea90a8d04ddedadc2b3a798df0'
KICAD_POWER_SHA256 = '8113f8fe90853413603d619987cc744e33dc47ff27faac19a58d7caf8c334fd0'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(pd_path, power_path):
    got = hashlib.sha256(open(power_path, 'rb').read()).hexdigest()
    assert got == KICAD_POWER_SHA256, f'KiCad power library hash {got} != pinned'
    got = hashlib.sha256(open(pd_path, 'rb').read()).hexdigest()
    assert got == PD_SYM_SHA256, f'zudo-pd symbol library hash {got} != pinned {PD_SYM_SHA256}'
    sources = [
        ('symbols/zudo-led-lamp.kicad_sym', schgen_core.Library()),
        ('candidates/board-p-v196-unadopted/libraries/retained.kicad_sym',
         schgen_core.Library(os.path.join(ROOT, 'candidates/board-p-v196-unadopted/libraries/retained.kicad_sym'))),
        ('candidates/board-p-v196-unadopted/libraries/cout-candidate.kicad_sym',
         schgen_core.Library(os.path.join(ROOT, 'candidates/board-p-v196-unadopted/libraries/cout-candidate.kicad_sym'))),
        ('zudo-pd@3ac13d46:symbols/zudo-pd.kicad_sym', schgen_core.Library(pd_path)),
        ('kicad-10.0.6-image:/usr/share/kicad/symbols/power.kicad_sym', schgen_core.Library(power_path)),
    ]
    spec_path = os.path.join(HERE, 'board_p_rnext_spec.py')
    s = importlib.util.spec_from_file_location('rnext', spec_path)
    spec = importlib.util.module_from_spec(s)
    s.loader.exec_module(spec)
    names = sorted({c[0] for c in spec.COMPONENTS.values()} |
                   {o['RILM'][0] for o in spec.OPTIONS.values()})
    blocks, origin = [], {}
    for name in names:
        found = []
        for label, lib in sources:
            if f'(symbol "{name}"' in lib.text:
                found.append((label, lib))
        assert found, f'{name}: in no source'
        pins0 = sorted((p[0], p[1]) for p in found[0][1].pins_of(name))
        for label, lib in found[1:]:
            pins = sorted((p[0], p[1]) for p in lib.pins_of(name))
            assert pins == pins0, f'{name}: pins differ between {found[0][0]} and {label}'
        origin[name] = found[0][0]
        blocks.append('\t' + found[0][1].extract_symbol_raw(name).replace('\n', '\n\t'))
    out = os.path.join(HERE, 'libraries', 'rnext.kicad_sym')
    with open(out, 'w') as f:
        f.write('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "kicad_symbol_editor")\n'
                '\t(generator_version "10.0")\n' + '\n'.join(blocks) + '\n)\n')
    with open(os.path.join(HERE, 'libraries', 'SYMBOL-ORIGINS.tsv'), 'w') as f:
        f.write('symbol\tsource\n' + ''.join(f'{k}\t{v}\n' for k, v in sorted(origin.items())))
    print(f'wrote {out}: {len(names)} symbols')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
