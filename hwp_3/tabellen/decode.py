#!/usr/bin/env python3
import sys

# opcode -> (length, opcode_display, operand_base, operand_type)
# operand_type: 'addr' | 'const' | None
ADDR = {
    0xC3: "JMP", 0x3A: "LDA", 0x32: "STA", 0xCA: "JZ", 0xC2: "JNZ",
    0xDA: "JC", 0xD2: "JNC", 0xCD: "CALL", 0xCC: "CZ", 0xC4: "CNZ",
    0xDC: "CC", 0xD4: "CNC", 0xDB: "IN", 0xD3: "OUT",
}
# const operand: (base, opcode_display)
CONST = {
    0x31: ("LXI SP", "LXI SP,n"), 0x3E: ("MVI A", "MVI A,n"),
    0x2E: ("MVI L", "MVI L,n"), 0xC6: ("ADI", "ADI n"),
    0xD6: ("SUI", "SUI n"), 0xFE: ("CPI", "CPI n"),
    0xE6: ("ANI", "ANI n"), 0xF6: ("ORI", "ORI n"), 0xEE: ("XRI", "XRI n"),
}
ONE = {
    0x6F: "MOV L,A", 0x6E: "MOV L,M", 0x7D: "MOV A,L", 0x7E: "MOV A,M",
    0x77: "MOV M,A", 0x3C: "INR A", 0x2C: "INR L", 0x3D: "DCR A",
    0x2D: "DCR L", 0x87: "ADD A", 0x85: "ADD L", 0x86: "ADD M",
    0x97: "SUB A", 0x95: "SUB L", 0x96: "SUB M", 0xBF: "CMP A",
    0xBD: "CMP L", 0xBE: "CMP M", 0xA7: "ANA A", 0xA5: "ANA L",
    0xA6: "ANA M", 0xB7: "ORA A", 0xB5: "ORA L", 0xB6: "ORA M",
    0xAF: "XRA A", 0xAD: "XRA L", 0xAE: "XRA M", 0xC9: "RET",
    0xF5: "PUSH A", 0xE5: "PUSH L", 0xED: "PUSH FL", 0xF1: "POP A",
    0xE1: "POP L", 0xFD: "POP FL", 0x76: "HLT", 0x00: "NOP",
    0xFB: "EI", 0xF3: "DI",
}

def b8(v):
    s = format(v, "08b")
    return s[:4] + " " + s[4:]

def lookup(op):
    if op in ONE:
        return (1, ONE[op], None, None)
    if op in ADDR:
        return (2, ADDR[op], ADDR[op], "addr")
    if op in CONST:
        base, disp = CONST[op]
        return (2, disp, base, "const")
    return (1, "DB", None, "data")

def main(path):
    with open(path) as f:
        raw = f.read().strip()
    mem = [int(x, 16) for x in raw.replace("\n", ",").split(",") if x.strip()]
    if len(mem) != 256:
        print(f"WARN: {len(mem)} Bytes statt 256")

    # last non-zero index
    last_nz = -1
    for i, v in enumerate(mem):
        if v != 0:
            last_nz = i
    limit = last_nz + 1  # decode 0..last_nz inclusive

    rows = []
    instr_count = 0
    i = 0
    while i < limit:
        op = mem[i]
        length, disp, base, otype = lookup(op)
        instr_count += 1
        # opcode row
        if otype == "data":
            mnem = "DB"
            comm = "Daten/unbekannt"
        else:
            mnem = disp
            comm = "Opcode"
        rows.append((i, op, mnem, comm))
        # operand row (only if 2-byte and operand still inside limit)
        if length == 2 and i + 1 < limit:
            operand = mem[i + 1]
            kind = "Zieladresse" if otype == "addr" else "Konstante"
            rows.append((i + 1, operand, f"{base} → 0x{operand:02X}",
                         f"Operand ({kind})"))
            i += 2
        else:
            i += 1

    # build table
    H = ("Adresse", "HEX", "Binär", "Schalter (A7..A0 / D7..D0)", "Mnemonik", "Kommentar")
    lines = []
    for addr, val, mnem, comm in rows:
        lines.append((f"0x{addr:02X}", f"{val:02X}", b8(val),
                      f"A: {b8(addr)}  D: {b8(val)}", mnem, comm))

    widths = [max(len(H[c]), max((len(r[c]) for r in lines), default=0)) for c in range(6)]
    def fmt(cols):
        return " | ".join(cols[c].ljust(widths[c]) for c in range(6))
    print(fmt(H))
    print("-+-".join("-" * widths[c] for c in range(6)))
    for r in lines:
        print(fmt(r))
    print()
    print(f"Gesamt: {limit} Bytes Programm (ohne Trailing-NOPs), davon {instr_count} Befehle")

if __name__ == "__main__":
    main(sys.argv[1])
