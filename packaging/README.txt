Ghidra Mobile - Phase 2 Android arm64 test build
================================================

What this is
  Ghidra's REAL decompiler and SLEIGH translator (upstream C++ sources, unmodified),
  cross-compiled with the Android NDK for arm64-v8a. No Ghidra Java, no libbfd.

What this is NOT
  Not the app. Not a full Ghidra. No auto-analysis: you name the functions to decompile.
  Original names come only from the file's own .symtab/.dynsym. Stripped files may have none.

Run the bundled sample (needs nothing else):
  sh run_sample.sh

Run on your own ELF (AArch64 or x86-64 only), needs python3:
  pkg install python
  sh analyze.sh /path/to/libfoo.so            # lists functions if there are many
  sh analyze.sh /path/to/libfoo.so func_a func_b

Supported inputs here: ELF64 little-endian, AArch64 or x86-64.
Spec files in specs/ are generated from Ghidra's own .slaspec files.

License: Ghidra is Apache-2.0. See LICENSE and NOTICE. Source: https://github.com/NationalSecurityAgency/ghidra
Project: https://github.com/Christianzz4603/project-59
