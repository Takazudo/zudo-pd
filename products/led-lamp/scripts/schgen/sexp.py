import re

def tokenize(s):
    tokens = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace(): i += 1
        elif c == '(': tokens.append('('); i += 1
        elif c == ')': tokens.append(')'); i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n:
                if s[j] == '\\' and j + 1 < n:
                    buf.append(s[j+1]); j += 2
                elif s[j] == '"': break
                else: buf.append(s[j]); j += 1
            tokens.append(('str', ''.join(buf))); i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()"': j += 1
            tokens.append(('atom', s[i:j])); i = j
    return tokens

def parse(tokens):
    def helper(idx):
        assert tokens[idx] == '('
        idx += 1
        out = []
        while tokens[idx] != ')':
            if tokens[idx] == '(':
                node, idx = helper(idx)
                out.append(node)
            else:
                out.append(tokens[idx]); idx += 1
        return out, idx + 1
    node, _ = helper(0)
    return node

def load(path):
    return parse(tokenize(open(path).read()))

def atom(x):
    return x[1] if isinstance(x, tuple) else x

def find_all(node, name):
    return [c for c in node if isinstance(c, list) and c and atom(c[0]) == name]
