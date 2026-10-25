#!/usr/bin/env python3
"""Convert a 64-bit little-endian ELF into Ghidra's XML <binaryimage> format plus a console script.

Parsing only: it copies loadable bytes and original .symtab function symbols. It does NOT
decompile or infer anything. Function names written here come from the file's own symbol table.

Usage: elf2xml.py <elf> <language-id> <out.xml> <out.script> [function ...]
"""
import struct, sys

PT_LOAD, PF_W = 1, 2
SHT_SYMTAB, STT_FUNC = 2, 2
MAX_FILE = 64 * 1024 * 1024


def fail(msg):
    sys.exit("elf2xml: " + msg)


def main():
    if len(sys.argv) < 5:
        fail(__doc__)
    path, lang, out_xml, out_script = sys.argv[1:5]
    wanted = sys.argv[5:]
    data = open(path, "rb").read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        fail("file too large")
    if data[:4] != b"\x7fELF" or data[4] != 2 or data[5] != 1:
        fail("only ELF64 little-endian is supported")
    (e_type, e_machine, _v, e_entry, e_phoff, e_shoff, _fl, _eh, e_phentsize, e_phnum,
     e_shentsize, e_shnum, _shstr) = struct.unpack_from("<HHIQQQIHHHHHH", data, 16)

    def check(off, size):
        if off < 0 or size < 0 or off + size > len(data):
            fail("offset/length out of range (malformed ELF)")

    chunks = []
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        check(off, 56)
        p_type, p_flags, p_off, p_vaddr, _pa, p_filesz, _msz, _al = struct.unpack_from("<IIQQQQQQ", data, off)
        if p_type == PT_LOAD and p_filesz:
            check(p_off, p_filesz)
            chunks.append((p_vaddr, data[p_off:p_off + p_filesz], not (p_flags & PF_W)))

    funcs = {}
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        check(off, 64)
        _n, sh_type, _f, _a, sh_off, sh_size, sh_link, _i, _al, sh_entsize = struct.unpack_from("<IIQQQQIIQQ", data, off)
        if sh_type != SHT_SYMTAB or sh_entsize != 24:
            continue
        stroff = e_shoff + sh_link * e_shentsize
        check(stroff, 64)
        str_off, str_size = struct.unpack_from("<QQ", data, stroff + 24)
        check(str_off, str_size)
        check(sh_off, sh_size)
        for s in range(sh_size // 24):
            st_name, st_info, _o, _shndx, st_value, st_size = struct.unpack_from("<IBBHQQ", data, sh_off + s * 24)
            if (st_info & 0xF) == STT_FUNC and st_size and st_name < str_size:
                end = data.index(b"\0", str_off + st_name)
                funcs[data[str_off + st_name:end].decode("ascii", "replace")] = st_value

    with open(out_xml, "w") as f:
        f.write('<binaryimage arch="%s">\n' % lang)
        for vaddr, blob, ro in chunks:
            f.write('<bytechunk space="ram" offset="0x%x" readonly="%s">\n' % (vaddr, "true" if ro else "false"))
            hx = blob.hex()
            for k in range(0, len(hx), 64):
                f.write(hx[k:k + 64] + "\n")
            f.write("</bytechunk>\n")
        for name, addr in sorted(funcs.items(), key=lambda kv: kv[1]):
            f.write('<symbol space="ram" offset="0x%x" name="%s"/>\n' % (addr, name))
        f.write("</binaryimage>\n")

    targets = wanted or sorted(funcs, key=funcs.get)
    missing = [t for t in targets if t not in funcs]
    if missing:
        fail("function(s) not in symbol table: " + ", ".join(missing))
    with open(out_script, "w") as f:
        f.write("load file %s\n" % out_xml)
        for t in targets:
            f.write("load function %s\ndecompile\nprint C\n" % t)
        f.write("quit\n")
    print("wrote %s: %d load segments, %d function symbols, machine=0x%x" % (out_xml, len(chunks), len(funcs), e_machine))


main()
