"""Build and decode the board-p15 15 V STUSB4500 NVM image (desk image; never written or read back).

usage: python3 scripts/pcb/board-p15/nvm-image.py [--check]

Writes boards/board-p15/nvm/stusb4500-15v.bin (40 bytes, sectors 0-4) and stusb4500-15v.json. --check rebuilds
both in memory and fails if the committed files differ.

Provenance (kept in the JSON):
- Base bytes: the default_sector table of the SparkFun STUSB4500 Arduino library (MIT), commit 7f76188b,
  src/SparkFun_STUSB4500.cpp sha256 0d047860...; THIRD_PARTY, not an ST document.
- Field positions: the same library's NVM getters/setters (THIRD_PARTY). ST's own NVM map document is not retained.
- Cross-check: decoding the base bytes with those positions gives every Table 16/17/18 default of DS12499 Rev 7
  (sha256 407ee676..., byte-identical to Doc/stusb4500_datasheet_v7.pdf in ST's usb-c/STUSB4500 repository at
  55d1109e). The field positions are therefore checked only for the fields this image reads or changes.
"""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'boards/board-p15/nvm'

BASE = [[0x00, 0x00, 0xB0, 0xAA, 0x00, 0x45, 0x00, 0x00],
        [0x10, 0x40, 0x9C, 0x1C, 0xFF, 0x01, 0x3C, 0xDF],
        [0x02, 0x40, 0x0F, 0x00, 0x32, 0x00, 0xFC, 0xF1],
        [0x00, 0x19, 0x56, 0xAF, 0xF5, 0x35, 0x5F, 0x00],
        [0x00, 0x4B, 0x90, 0x21, 0x43, 0x00, 0x40, 0xFB]]

LUT = {1: 0.50, 2: 0.75, 3: 1.00, 4: 1.25, 5: 1.50, 6: 1.75, 7: 2.00, 8: 2.25, 9: 2.50, 10: 2.75, 11: 3.00,
       12: 3.50, 13: 4.00, 14: 4.50, 15: 5.00}   # DS12499 Rev 7 Table 17; 0 selects I_SNK_PDO_FLEX


def bits(s, sec, byte, lo, n):
    return (s[sec][byte] >> lo) & ((1 << n) - 1)


def setbits(s, sec, byte, lo, n, v):
    m = ((1 << n) - 1) << lo
    s[sec][byte] = (s[sec][byte] & ~m & 0xFF) | ((v << lo) & m)


def decode(s):
    v2 = (s[4][1] << 2) | (s[4][0] >> 6)
    v3 = ((s[4][3] & 0x03) << 8) | s[4][2]
    flex = ((s[4][4] & 0x0F) << 6) | ((s[4][3] & 0xFC) >> 2)
    cur = lambda c: LUT.get(c, 'FLEX')
    return {
        'SNK_PDO_NUMB': bits(s, 3, 2, 1, 2),
        'PDO1': {'V': 5.0, 'I_SNK_PDO1_code': bits(s, 3, 2, 4, 4), 'A': cur(bits(s, 3, 2, 4, 4))},
        'PDO2': {'V_code': v2, 'V': v2 / 20, 'I_SNK_PDO2_code': bits(s, 3, 4, 0, 4), 'A': cur(bits(s, 3, 4, 0, 4))},
        'PDO3': {'V_code': v3, 'V': v3 / 20, 'I_SNK_PDO3_code': bits(s, 3, 5, 4, 4), 'A': cur(bits(s, 3, 5, 4, 4))},
        'I_SNK_PDO_FLEX_A': flex / 100,
        'POWER_ONLY_ABOVE_5V': bits(s, 4, 6, 3, 1),
        'REQ_SRC_CURRENT': bits(s, 4, 6, 4, 1),
        'POWER_OK_CFG': bits(s, 4, 4, 5, 2),
        'GPIO_CFG': bits(s, 1, 0, 4, 2),
        'SNK_UNCONS_POWER': bits(s, 3, 2, 3, 1),
        'USB_COMM_CAPABLE': bits(s, 3, 2, 0, 1),
        'SHIFT_VBUS_HL1_pct': bits(s, 3, 3, 4, 4),
        'SHIFT_VBUS_LL2_pct': bits(s, 3, 4, 4, 4),
        'SHIFT_VBUS_HL2_pct': bits(s, 3, 5, 0, 4),
        'SHIFT_VBUS_LL3_pct': bits(s, 3, 6, 0, 4),
        'SHIFT_VBUS_HL3_pct': bits(s, 3, 6, 4, 4),
    }


REV7_DEFAULTS = {'SNK_PDO_NUMB': 3, 'PDO1': (5.0, 1.5), 'PDO2': (15.0, 1.5), 'PDO3': (20.0, 1.0),
                 'I_SNK_PDO_FLEX_A': 2.0, 'POWER_ONLY_ABOVE_5V': 0, 'REQ_SRC_CURRENT': 0, 'POWER_OK_CFG': 2,
                 'GPIO_CFG': 1, 'SNK_UNCONS_POWER': 0, 'USB_COMM_CAPABLE': 0, 'SHIFT_VBUS_HL1_pct': 10,
                 'SHIFT_VBUS_LL2_pct': 15, 'SHIFT_VBUS_HL2_pct': 5, 'SHIFT_VBUS_LL3_pct': 15, 'SHIFT_VBUS_HL3_pct': 5}


def check_defaults(d):
    bad = []
    for k, want in REV7_DEFAULTS.items():
        got = (d[k]['V'], d[k]['A']) if isinstance(want, tuple) else d[k]
        if got != want:
            bad.append(f'{k}: decoded {got}, Rev 7 default {want}')
    return bad


def build():
    base_decoded = decode(BASE)
    mismatch = check_defaults(base_decoded)
    if mismatch:
        raise SystemExit('base bytes do not decode to the Rev 7 defaults: ' + '; '.join(mismatch))
    s = [row[:] for row in BASE]
    setbits(s, 3, 2, 1, 2, 2)      # SNK_PDO_NUMB = 2: PDO3 (20 V) is never advertised
    setbits(s, 3, 4, 0, 4, 11)     # I_SNK_PDO2 = 1011b = 3.00 A at 15 V
    setbits(s, 4, 6, 3, 1, 1)      # POWER_ONLY_ABOVE_5V = 1: VBUS_EN_SNK only after a PDO2/PDO3 contract
    raw = bytes(b for row in s for b in row)
    d = decode(s)
    assert d['SNK_PDO_NUMB'] == 2 and d['PDO2']['V'] == 15.0 and d['PDO2']['A'] == 3.0 and d['POWER_ONLY_ABOVE_5V'] == 1
    changed = [{'sector': i, 'byte': j, 'from': f'0x{BASE[i][j]:02X}', 'to': f'0x{s[i][j]:02X}'}
               for i in range(5) for j in range(8) if BASE[i][j] != s[i][j]]
    doc = {
        '_comment': 'DESK IMAGE for board-p15 (dec-p15-reset-subset, dec-p15-i2c-pulldowns). Not written to any part and not '
                    'read back: status NOT RUN. The field positions come from a third-party library and are checked only '
                    'against the Rev 7 defaults listed under cross_check. Write it with the procedure in '
                    'doc/src/content/docs/architecture/board-p15-programming.md and accept it only on a power-cycle readback '
                    'equal to these 40 bytes.',
        'status': 'NOT RUN (never written or read back)',
        'file': 'stusb4500-15v.bin',
        'sha256': hashlib.sha256(raw).hexdigest(),
        'sectors_hex': [' '.join(f'{b:02X}' for b in row) for row in s],
        'changes_from_base': changed,
        'decoded': d,
        'intent': {'SNK_PDO_NUMB': '2 (PDO1 5 V + PDO2 15 V; 20 V never requested)', 'PDO2': '15.00 V, 3.00 A',
                   'POWER_ONLY_ABOVE_5V': '1 (Q1 stays off at 5 V)', 'other fields': 'Rev 7 defaults, unchanged'},
        'base': {'bytes_hex': [' '.join(f'{b:02X}' for b in row) for row in BASE],
                 'source': 'SparkFun_STUSB4500_Arduino_Library src/SparkFun_STUSB4500.cpp default_sector, commit '
                           '7f76188b7900d930aeb7908319d463b6446257c6, file sha256 '
                           '0d047860c8bed18c071115c4b8a79d9ceecf01e7faeb1d73653f2dcef21db48a (MIT)',
                 'authority': 'THIRD_PARTY'},
        'field_map': {'source': 'same library, NVM getters and setters (sector/byte/bit positions)', 'authority': 'THIRD_PARTY',
                      'st_map_document': 'UNAVAILABLE: no ST NVM map is retained in this repository'},
        'cross_check': {'reference': 'DS12499 Rev 7 Table 16 defaults, Table 17 current LUT, Table 18 default PDOs',
                        'rev7_sha256': '407ee6767128cc4075926e01d945fe846440f932359ed81f45a957485778399e',
                        'rev7_copy': "byte-identical to Doc/stusb4500_datasheet_v7.pdf in ST's usb-c/STUSB4500 GitHub "
                                     'repository at commit 55d1109e7ef0cffc2ffef2494095d23306594601',
                        'base_decodes_to_rev7_defaults': 'PASS', 'checked_fields': sorted(REV7_DEFAULTS),
                        'not_checked': 'every other bit of the 40 bytes (left at the base value)'},
        'st_example_not_used': {'source': 'usb-c/STUSB4500 NVM_Flasher/Src/NVM/STUSB_NVM.h at 55d1109e, sha256 '
                                          '7505a77235f1259d657af3443b5506d6ff12ab4407e3ab6e9370044906d05006',
                                'note': 'an ST example image, not the factory default (it differs from the Rev 7 defaults)'},
    }
    return raw, json.dumps(doc, indent=1) + '\n'


def main():
    raw, text = build()
    if '--check' in sys.argv:
        ok = (OUT / 'stusb4500-15v.bin').read_bytes() == raw and (OUT / 'stusb4500-15v.json').read_text() == text
        print('nvm-image: ' + ('PASS' if ok else 'FAIL (committed image differs; rerun without --check)'))
        sys.exit(0 if ok else 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'stusb4500-15v.bin').write_bytes(raw)
    (OUT / 'stusb4500-15v.json').write_text(text)
    print('wrote', OUT / 'stusb4500-15v.bin', hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    main()
