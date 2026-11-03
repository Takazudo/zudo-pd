"""Board P r3 20 V / 5 A STUSB4500 NVM intent and partial desk image (never written or read back).

usage: python3 scripts/pcb/board-p/nvm-intent-20v.py [--check]

Writes boards/board-p/nvm/stusb4500-20v-intent.json. --check rebuilds it in memory and fails if the committed file
differs. Byte handling and field positions are imported unchanged from scripts/pcb/board-p15/nvm-image.py, so the
base bytes, the third-party field map and the DS12499 Rev 7 default cross-check are the same ones used for P15.

Status is BLOCKED, not a finished image. Two required settings cannot be expressed from retained evidence:
- TDISPAR0V >= 13 (board-p.md, calculate-input-ovp-20v.py): the third-party field map has no discharge-time field and
  no ST NVM map document is retained, so its sector/byte/bit position is UNAVAILABLE.
- Accept or refuse (dec PWR-D5 = D5-1, no degraded mode): with PDO2 = 20 V / 5 A the sink must not enable VBUS_OUT on a
  20 V contract below 5 A (for example a 3 A cable). How the STUSB4500 requests and flags a capability mismatch, and
  whether VBUS_EN_SNK still asserts then, is not stated in the retained evidence; it is UNKNOWN.
No .bin is written, so the partial bytes cannot be mistaken for a programmable image.
"""
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'boards/board-p/nvm/stusb4500-20v-intent.json'
_spec = importlib.util.spec_from_file_location('p15_nvm', ROOT / 'scripts/pcb/board-p15/nvm-image.py')
P15 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P15)


def build():
    base_decoded = P15.decode(P15.BASE)
    mismatch = P15.check_defaults(base_decoded)
    if mismatch:
        raise SystemExit('base bytes do not decode to the Rev 7 defaults: ' + '; '.join(mismatch))
    s = [row[:] for row in P15.BASE]
    P15.setbits(s, 3, 2, 1, 2, 2)      # SNK_PDO_NUMB = 2: PDO1 5 V + PDO2; PDO3 never advertised
    v = 400                            # PDO2 voltage code in 50 mV steps: 20.00 V
    P15.setbits(s, 4, 0, 6, 2, v & 0x03)
    s[4][1] = v >> 2
    P15.setbits(s, 3, 4, 0, 4, 15)     # I_SNK_PDO2 = 1111b = 5.00 A (DS12499 Rev 7 Table 17)
    P15.setbits(s, 4, 6, 3, 1, 1)      # POWER_ONLY_ABOVE_5V = 1: VBUS_EN_SNK only after a PDO2 contract
    d = P15.decode(s)
    assert d['SNK_PDO_NUMB'] == 2 and d['PDO2']['V'] == 20.0 and d['PDO2']['A'] == 5.0 and d['POWER_ONLY_ABOVE_5V'] == 1
    raw = bytes(b for row in s for b in row)
    changed = [{'sector': i, 'byte': j, 'from': f'0x{P15.BASE[i][j]:02X}', 'to': f'0x{s[i][j]:02X}'}
               for i in range(5) for j in range(8) if P15.BASE[i][j] != s[i][j]]
    return {
        '_comment': 'INTENT RECORD and PARTIAL desk bytes for the Board P r3 20 V / 5 A unit (dec PWR-D3 = D3-A, '
                    'PWR-D5 = D5-1). Not an image to program: status BLOCKED. Never written to any part or read back.',
        'status': 'BLOCKED (TDISPAR0V position unavailable; capability-mismatch behaviour unknown)',
        'intent': {
            'SNK_PDO_NUMB': '2 (PDO1 5 V, PDO2 20 V)',
            'PDO2': '20.00 V, 5.00 A; needs a 5 A e-marked cable and a source offering 20 V / 5 A',
            'POWER_ONLY_ABOVE_5V': '1 (Q1 stays off at 5 V)',
            'TDISPAR0V': '>= 13 so the 2 kOhm VBUS_VS_DISCH feed reaches vSafe0V (default 9 gives >= 630 ms, too short)',
            'accept_or_refuse': 'VBUS_OUT only on a 20 V contract at 5 A; any lower-current 20 V contract must leave '
                                'Q1 off (no degraded mode)',
            'other fields': 'Rev 7 defaults, unchanged',
        },
        'blocked': [
            {'item': 'TDISPAR0V', 'status': 'UNAVAILABLE',
             'reason': 'No retained field map gives its sector/byte/bit (third-party map has no discharge-time field; '
                       'no ST NVM map document retained). Needed: an ST-authored NVM map or the ST GUI export format.'},
            {'item': 'capability mismatch', 'status': 'UNKNOWN',
             'reason': 'Retained evidence does not state whether VBUS_EN_SNK asserts after a PDO2 request granted below '
                       '5 A or with the capability-mismatch bit set. Until a primary ST statement or a bench test '
                       'closes it, accept-or-refuse cannot rely on the NVM alone. Board-side alternative: refuse '
                       'through the B20 VIN UV and current limits, which do not detect a 3 A contract.'},
        ],
        'partial_sectors_hex': [' '.join(f'{b:02X}' for b in row) for row in s],
        'partial_sha256': hashlib.sha256(raw).hexdigest(),
        'changes_from_base': changed,
        'decoded': d,
        'base_and_field_map': 'scripts/pcb/board-p15/nvm-image.py (BASE, decode, setbits; THIRD_PARTY map, Rev 7 '
                              'default cross-check PASS)',
    }


def main():
    text = json.dumps(build(), indent=1) + '\n'
    if '--check' in sys.argv:
        ok = OUT.is_file() and OUT.read_text() == text
        print('nvm-intent-20v: ' + ('PASS' if ok else 'FAIL (committed intent differs; rerun without --check)'))
        sys.exit(0 if ok else 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
