#!/usr/bin/env bash
# Builds Ghidra's real console decompiler (upstream sources, unmodified) WITHOUT libbfd.
# It reads binaries in Ghidra's XML <binaryimage> format, so no GPL loader is involved.
# Usage: bash build_console.sh <ghidra-checkout> <output-dir>
set -euo pipefail
SRC="${1:?ghidra checkout}"; OUT="${2:?output dir}"
CPP="$SRC/Ghidra/Features/Decompiler/src/decompile/cpp"
mkdir -p "$OUT/obj"
cd "$CPP"

# Excluded: Java bridge (*_ghidra, ghidra_*), other programs' mains, the SLEIGH spec compiler.
ls *.cc | grep -vE '(_ghidra\.cc|^ghidra_.*\.cc|^sleighexample\.cc|^test\.cc|^slgh_compile\.cc|^slghparse\.cc|^slghscan\.cc)$' > "$OUT/sources.all"

# Excluded automatically: any source that includes libbfd (GPL, not available on Android).
grep -lE 'bfd\.h|loadimage_bfd|bfd_arch' *.cc *.hh | sort -u > "$OUT/bfd_users.txt" || true
grep -vxFf "$OUT/bfd_users.txt" "$OUT/sources.all" > "$OUT/sources.txt"
# analyzesigs/codedata form the bfd-based signature analysis tool; nothing else uses them.
grep -vE '^(analyzesigs|codedata)\.cc$' "$OUT/sources.txt" > "$OUT/sources.final"
mv "$OUT/sources.final" "$OUT/sources.txt"
echo "libbfd users excluded: $(tr '\n' ' ' < "$OUT/bfd_users.txt")"

echo "compiling $(wc -l < "$OUT/sources.txt") files with $(nproc) jobs"
CXX="${CXX:-g++}"
compile() { f="$1"; "$CXX" -std=c++11 -O1 -D__TERMINAL__ -Wno-sign-compare -c "$f" -o "$OUT/obj/${f%.cc}.o"; }
export -f compile; export CXX OUT
xargs -P "$(nproc)" -I{} bash -c 'compile {}' < "$OUT/sources.txt"
"$CXX" -o "$OUT/decomp_console" "$OUT"/obj/*.o -lz
echo "built $OUT/decomp_console"
