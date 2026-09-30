"""Minimal two-pass assembler for the instructions used by the scroll patch.

Contains no game disassembly or cartridge data.
"""

def assemble(src, origin):
    lines = []
    for raw in src.splitlines():
        s = raw.split(";")[0].strip()
        if s:
            lines.append(s)
    labels = {}
    out = b""
    for strict in (False, True):
        pc = origin
        buf = []
        for s in lines:
            if s.endswith(":"):
                labels[s[:-1]] = pc
                continue
            b = encode(s, pc, labels, strict)
            buf.extend(b)
            pc += len(b)
        out = bytes(buf)
    return out, labels


def encode(s, pc, labels, strict):
    parts = s.replace(",", " ").split()
    op = parts[0].lower()
    a = parts[1:]

    def imm8(x):
        return u8(val(x, labels, strict))

    def imm16(x):
        v = val(x, labels, strict) & 0xFFFF
        return [v & 255, (v >> 8) & 255]

    def rel(x):
        if x not in labels:
            if strict:
                raise SystemExit(f"label em falta: {x}")
            return 0
        t = labels[x]
        d = t - (pc + 2)
        if not -128 <= d <= 127:
            raise SystemExit(f"salto longo {s} em {pc:04X} -> {t:04X}")
        return d & 255

    R = {"b": 0, "c": 1, "d": 2, "e": 3, "h": 4, "l": 5, "(hl)": 6, "a": 7}
    RR = {"bc": 0, "de": 1, "hl": 2, "sp": 3}
    CC = {"nz": 0, "z": 1, "nc": 2, "c": 3}
    if op == "nop":
        return [0x00]
    if op == "ret" and not a:
        return [0xC9]
    if op == "ret" and a and a[0] in CC:
        return [0xC0 + CC[a[0]] * 8]
    if op == "ei":
        return [0xFB]
    if op == "di":
        return [0xF3]
    if op == "ldir":
        return [0xED, 0xB0]
    if op == "neg":
        return [0xED, 0x44]
    if op == "outi":
        return [0xED, 0xA3]
    if op == "scf":
        return [0x37]
    if op == "ex" and a[0] == "de" and a[1] == "hl":
        return [0xEB]
    if op == "push" and a[0] == "af":
        return [0xF5]
    if op == "pop" and a[0] == "af":
        return [0xF1]
    if op == "push":
        return [0xC5 + RR[a[0]] * 16]
    if op == "pop":
        return [0xC1 + RR[a[0]] * 16]
    if op == "inc" and a[0] in RR:
        return [0x03 + RR[a[0]] * 16]
    if op == "dec" and a[0] in RR:
        return [0x0B + RR[a[0]] * 16]
    if op == "inc" and a[0] in R:
        return [0x04 + R[a[0]] * 8]
    if op == "dec" and a[0] in R:
        return [0x05 + R[a[0]] * 8]
    if op == "ld" and a[0] in RR and len(a) == 2 and not a[1].startswith("("):
        return [0x01 + RR[a[0]] * 16] + imm16(a[1])
    if op == "ld" and a == ["a", "(de)"]:
        return [0x1A]
    if op == "ld" and a == ["(de)", "a"]:
        return [0x12]
    if op == "ld" and a[0] == "a" and a[1].startswith("(") and a[1].endswith(")") and a[1][1:-1] not in ("hl", "bc", "de"):
        return [0x3A] + imm16(a[1][1:-1])
    if op == "ld" and a[0].startswith("(") and a[0].endswith(")") and a[0][1:-1] not in ("hl", "bc", "de") and a[1] == "a":
        return [0x32] + imm16(a[0][1:-1])
    if op == "ld" and a[0] in R and a[1] in R:
        return [0x40 + R[a[0]] * 8 + R[a[1]]]
    if op == "ld" and a[0] in R and len(a) == 2:
        return [0x06 + R[a[0]] * 8, imm8(a[1])]
    if op == "add" and a[0] == "hl" and a[1] in RR:
        return [0x09 + RR[a[1]] * 16]
    if op == "add" and a[0] == "a":
        return [0x80 + R[a[1]]] if a[1] in R else [0xC6, imm8(a[1])]
    if op == "sub" and len(a) == 1:
        return [0x90 + R[a[0]]] if a[0] in R else [0xD6, imm8(a[0])]
    if op == "and" and len(a) == 1:
        return [0xA0 + R[a[0]]] if a[0] in R else [0xE6, imm8(a[0])]
    if op == "or" and len(a) == 1:
        return [0xB0 + R[a[0]]] if a[0] in R else [0xF6, imm8(a[0])]
    if op == "xor" and len(a) == 1:
        return [0xA8 + R[a[0]]] if a[0] in R else [0xEE, imm8(a[0])]
    if op == "cp" and len(a) == 1:
        return [0xB8 + R[a[0]]] if a[0] in R else [0xFE, imm8(a[0])]
    if op == "jp" and a[0] == "(hl)":
        return [0xE9]
    if op == "jp" and a[0] in CC:
        return [0xC2 + CC[a[0]] * 8] + imm16(a[1])
    if op == "jp":
        return [0xC3] + imm16(a[0])
    if op == "call" and a[0] in CC:
        return [0xC4 + CC[a[0]] * 8] + imm16(a[1])
    if op == "call":
        return [0xCD] + imm16(a[0])
    if op == "jr" and a[0] in CC:
        return [0x20 + CC[a[0]] * 8, rel(a[1])]
    if op == "jr":
        return [0x18, rel(a[0])]
    if op == "djnz":
        return [0x10, rel(a[0])]
    if op == "rlca":
        return [0x07]
    if op == "rrca":
        return [0x0F]
    if op == "rla":
        return [0x17]
    if op == "rra":
        return [0x1F]
    if op == "sla" and a[0] in R:
        return [0xCB, 0x20 + R[a[0]]]
    if op == "srl" and a[0] in R:
        return [0xCB, 0x38 + R[a[0]]]
    if op == "rl" and a[0] in R:
        return [0xCB, 0x10 + R[a[0]]]
    if op == "rr" and a[0] in R:
        return [0xCB, 0x18 + R[a[0]]]
    if op == "bit" and a[1] in R:
        return [0xCB, 0x40 + int(a[0]) * 8 + R[a[1]]]
    if op == "out" and a[0].startswith("(") and a[1] == "a":
        port = a[0][1:-1]
        if port == "c":
            return [0xED, 0x79]
        return [0xD3, imm8(port)]
    if op == "in" and a[0] == "a" and a[1].startswith("("):
        port = a[1][1:-1]
        if port == "c":
            return [0xED, 0x78]
        return [0xDB, imm8(port)]
    raise SystemExit(f"nao sei montar: {s}")


def val(x, labels, strict):
    x = x.strip()
    if x in labels:
        return labels[x]
    if x.startswith("$"):
        return int(x[1:], 16)
    if x[:2].lower() == "0x":
        return int(x, 16)
    if x[-1:] in "hH" and x[:-1] and all(c in "0123456789abcdefABCDEF" for c in x[:-1]):
        return int(x[:-1], 16)
    if all(c in "0123456789" for c in x):
        return int(x)
    if strict:
        raise SystemExit(f"label em falta: {x}")
    return 0


def u8(v):
    if not 0 <= v <= 255:
        raise SystemExit(f"fora de byte: {v}")
    return v
