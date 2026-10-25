#!/bin/sh
# Decompiles the bundled AArch64 sample with Ghidra's real decompiler.
cd "$(dirname "$0")" || exit 1
./decomp_console -s "$PWD/specs" < samples/sample_aarch64.script
