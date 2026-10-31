import sys
t = open(sys.argv[1]).read()
out, i, depth, start = [], 0, 0, None
# top-level children of (kicad_pcb ...) start at depth 1
res = []; i = 0; n = len(t); depth = 0; last = 0; drop = 0
spans = []
instr = False
while i < n:
    ch = t[i]
    if instr:
        if ch == '\\': i += 2; continue
        if ch == '"': instr = False
    elif ch == '"': instr = True
    elif ch == '(':
        depth += 1
        if depth == 2: start = i
    elif ch == ')':
        if depth == 2:
            head = t[start + 1:start + 12].split()[0]
            if head in ('segment', 'via', 'arc', 'zone') or (head == 'footprint' and '(property "Reference" "MH' not in t[start:i]) or (head.startswith('gr_') and '"Edge.Cuts"' not in t[start:i]):
                spans.append((start, i + 1))
        depth -= 1
    i += 1
o = []; last = 0
for a, b in spans:
    o.append(t[last:a]); last = b
o.append(t[last:])
open(sys.argv[2], 'w').write(''.join(o))
print(len(spans), 'removed')
