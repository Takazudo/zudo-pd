"""Prove V198 differs from V196 only by (property ...) elements.

Strips every balanced `(property "...` element from both files and compares the
remaining bytes. Usage: python3 -I check_field_only.py <v196_file> <v198_file>
"""
import sys


def strip_props(t):
    out, i, n = [], 0, len(t)
    key = '(property "'
    while i < n:
        j = t.find(key, i)
        if j < 0:
            out.append(t[i:])
            break
        out.append(t[i:j])
        depth, k, instr = 0, j, False
        while k < n:
            c = t[k]
            if instr:
                if c == "\\":
                    k += 1
                elif c == '"':
                    instr = False
            elif c == '"':
                instr = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        i = k + 1
        if i < n and t[i] == " ":
            i += 1
    return "".join(out)


a, b = (open(p).read() for p in sys.argv[1:3])
sa, sb = strip_props(a), strip_props(b)
ok = sa == sb
print("field_only_change:", ok, "| bytes", len(a), "->", len(b))
sys.exit(0 if ok else 1)
