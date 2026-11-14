"""Board P r3 20 V / 5 A STUSB4500 NVM intent and partial desk image (never written or read back).

usage: python3 scripts/pcb/board-p/nvm-intent-20v.py [--check]

Writes boards/board-p/nvm/stusb4500-20v-intent.json. --check rebuilds it in memory and fails if the committed file
differs. Byte handling and field positions are imported unchanged from scripts/pcb/board-p15/nvm-image.py, so the
base bytes, the third-party field map and the DS12499 Rev 7 default cross-check are the same ones used for P15.

Status is BLOCKED, not a finished image. Research of 2026-11-08 (manufacturing/pd20-evidence-research.md):
- TDISPAR0V is located: ST technical note "TNxxx STUSB4500 NVM registers" (ST-authored draft, no revision, posted by
  an ST moderator on ST Community) puts DISCHARGE_TIME_TO_0V at NVM 0xCA = sector 1 byte 2 bits [7:4], default 0x9C
  (9 and TDISPARPDO 12, matching DS12499). TDISPAR0V = 15 is set (0xFC), chosen 2026-11-14 under owner delegation.
- Capability mismatch is answered by DS12499 Rev 8 section 3.3.2 (owner-supplied copy, 2026-11-08): a PDO match needs
  I(SNK_PDO) <= I(SRC_PDO), so a 20 V source offering under 5 A gives no PDO2 match and a 5 V contract; with
  POWER_ONLY_ABOVE_5V = 1, VBUS_EN_SNK then stays Hi-Z (Table 6).
- New conflict: the same ST note marks 0xE6 bits [3:0] RESERVED, while POWER_ONLY_ABOVE_5V at 0xE6 bit 3 rests on the
  third-party map and a non-ST community GUI diff only. This bit also carries the P15 image.
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
    assert P15.BASE[1][2] == 0x9C
    P15.setbits(s, 1, 2, 4, 4, 15)     # TDISPAR0V = 15 at 0xCA [7:4] (ST TNxxx draft note); 0x9C -> 0xFC
    d = P15.decode(s)
    assert s[1][2] == 0xFC and d['SNK_PDO_NUMB'] == 2 and d['PDO2']['V'] == 20.0 and d['PDO2']['A'] == 5.0 and d['POWER_ONLY_ABOVE_5V'] == 1
    raw = bytes(b for row in s for b in row)
    changed = [{'sector': i, 'byte': j, 'from': f'0x{P15.BASE[i][j]:02X}', 'to': f'0x{s[i][j]:02X}'}
               for i in range(5) for j in range(8) if P15.BASE[i][j] != s[i][j]]
    return {
        '_comment': 'INTENT RECORD and PARTIAL desk bytes for the Board P r3 20 V / 5 A unit (dec PWR-D3 = D3-A, '
                    'PWR-D5 = D5-1). Not an image to program: status BLOCKED. Never written to any part or read back.',
        'status': 'BLOCKED (POWER_ONLY_ABOVE_5V position conflicts with the ST note; no reviewed image). '
                  'TDISPAR0V = 15 is set (dec-pd20-tdispar0v-15)',
        'intent': {
            'SNK_PDO_NUMB': '2 (PDO1 5 V, PDO2 20 V)',
            'PDO2': '20.00 V, 5.00 A; needs a 5 A e-marked cable and a source offering 20 V / 5 A',
            'POWER_ONLY_ABOVE_5V': '1 (Q1 stays off at 5 V)',
            'TDISPAR0V': '15 (0xCA = 0xFC; min 1.050 s, 16 % margin over the 0.906 s the 2 kOhm VBUS_VS_DISCH feed needs '
                         'to reach vSafe0V; default 9 gives >= 630 ms, too short)',
            'accept_or_refuse': 'VBUS_OUT only on a 20 V contract at 5 A; any lower-current 20 V contract must leave '
                                'Q1 off (no degraded mode)',
            'other fields': 'Rev 7 defaults, unchanged',
        },
        'field_evidence': [
            {'item': 'TDISPAR0V', 'status': 'LOCATED (ST-authored draft note)',
             'position': 'NVM 0xCA = sector 1 byte 2, bits [7:4] DISCHARGE_TIME_TO_0V; bits [3:0] '
                         'VBUS_DISCH_TIME_TO_PDO (TDISPARPDO); default 0x9C',
             'source': 'ST technical note TNxxx "STUSB4500 NVM registers, description and generic access", pages 5 '
                       'and 22; PDF sha256 a1f35ffea672cef0a32bbd818dd7f5795cfe4bd641960bbf70a5b2374a3927e4; '
                       'attached by an ST technical moderator, ST Community thread 157984 (2025-10-13)',
             'candidates': {'13': '0xDC: TDISUSB0V min 0.910 s against 0.906 s needed (0.4 % margin)',
                            '14': '0xEC: min 0.980 s (8 % margin)',
                            '15': '0xFC: min 1.050 s (16 % margin), max 1.500 s'},
             'applied': '15 (0xFC), chosen by Claude on 2026-11-14 under the owner\'s delegation ("continue by your '
                        'decision"); reversible desk byte only, never written to a part'},
            {'item': 'capability mismatch', 'status': 'ANSWERED (DS12499 Rev 8)',
             'finding': 'DS12499 section 3.3.2: a match needs V(SNK_PDOi) = V(SRC_PDOj) and I(SNK_PDOi) <= '
                        'I(SRC_PDOj). A 20 V offer below 5 A does not match PDO2 = 20 V / 5 A, so the contract falls '
                        'to 5 V (PDO1, or a mismatch RDO at 5 V). With POWER_ONLY_ABOVE_5V = 1, VBUS_EN_SNK stays Hi-Z '
                        'without a PDO2 or PDO3 contract (Table 6, section 6.1.2), so Q1 stays off.',
             'source': 'DS12499 Rev 8 (2022-11), sections 2.2.10 (Table 6), 3.3.2 and 6.1.2; owner-supplied copy '
                       '2026-11-08, sha256 82d6080e6d3e994f0969f4f018039d1f0871db9f6793c80c09e63e80325029e8, '
                       'byte-identical to the retained src-stusb-ds12499 mirror. Rev 2 (Farnell mirror, sha256 '
                       '650afb8f...) carries the same text',
             'residual': 'A source that later re-advertises 20 V below 5 A during a 20 V contract: the transition '
                         'behaviour of VBUS_EN_SNK is not stated (bench T8)'},
            {'item': 'POWER_ONLY_ABOVE_5V position', 'status': 'CONFLICT',
             'finding': 'Set here and in the P15 image at 0xE6 = sector 4 byte 6 bit 3 (third-party map). The ST note '
                        'lists 0xE6 [3:0] as RESERVED 0x0; the only other location statement is a non-ST user GUI '
                        'diff (ST Community thread 32193, 2023-11-02). Needs an ST statement or a bench readback of a '
                        'GUI-exported image.'},
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
