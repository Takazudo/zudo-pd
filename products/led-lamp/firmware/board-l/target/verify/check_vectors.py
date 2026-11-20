"""Compare the g_vectors table in startup_stm32g031.c with ST's startup_stm32g031xx.s.

Usage: python3 -I check_vectors.py <startup_stm32g031.c> <ST startup_stm32g031xx.s>
"""
import re
import sys


def st_table(text):
    body = text[text.index("g_pfnVectors:"):]
    body = body[:body.index(".size")]
    return [w.split("/*")[0].strip() for w in re.findall(r"\.word\s+([^\n]+)", body)]


def c_table(text):
    body = text[text.index("const vector_t g_vectors[] = {") :]
    body = body[body.index("{") + 1 : body.index("};")]
    items = [x.strip() for x in body.replace("\n", " ").split(",") if x.strip()]
    return ["_estack" if "_estack" in x else x for x in items]


st = st_table(open(sys.argv[2], encoding="utf-8").read())
mine = c_table(open(sys.argv[1], encoding="utf-8").read())
if st != mine:
    for i, (a, b) in enumerate(zip(st, mine)):
        if a != b:
            print(f"entry {i}: ST {a!r} != C {b!r}")
    print(f"ST {len(st)} entries, C {len(mine)} entries")
    sys.exit(1)
print(f"PASS: {len(mine)} vector entries match ST startup_stm32g031xx.s")
