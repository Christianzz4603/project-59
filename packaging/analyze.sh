#!/bin/sh
# Decompile functions from your own ELF (AArch64 or x86-64, 64-bit little-endian).
# Usage: sh analyze.sh <elf> [function ...]
# Needs python3 (Termux: pkg install python).
set -e
[ -n "$1" ] || { echo "usage: sh analyze.sh <elf> [function ...]"; exit 1; }
case "$1" in /*) ELF="$1" ;; *) ELF="$PWD/$1" ;; esac
shift
cd "$(dirname "$0")"
mkdir -p work
python3 tools/elf2xml.py "$ELF" auto work/img.xml work/img.script "$@"
./decomp_console -s "$PWD/specs" < work/img.script
