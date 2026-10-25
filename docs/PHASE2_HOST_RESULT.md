# Phase 2 (host stage): real decompiler on a real AArch64 ELF

Status: **host proof passed. Android proof NOT done.**

CI run: https://github.com/Christianzz4603/project-59/actions/runs/40186186323 (commit `f49a10a`, upstream Ghidra pinned at `164003036607`).

## What was demonstrated (x86_64 Linux CI runner)

1. Upstream's SLEIGH compiler built from source with its own Makefile.
2. `AARCH64.slaspec` and `x86-64.slaspec` compiled to `.sla` by that compiler.
3. Upstream's decompiler sources (96 files, unmodified) built into a console binary with **no libbfd**. `build_console.sh` excludes every file that includes libbfd headers automatically.
4. A freestanding C file was cross-compiled to a real AArch64 ELF (`aarch64-linux-gnu-gcc -O1`).
5. `tools/elf2xml.py` (a plain ELF parser: segments plus original `.symtab` names) converted it to Ghidra's `<binaryimage>` XML.
6. The real decompiler loaded it as `Generic ARM64 v8.5-A LE` and produced C for all four functions, for example:

```c
int4 sum_squares(int4 param_1,int4 param_2)
{
  return param_2 * param_2 + param_1 * param_1;
}
```

The `fnv1a` output contains the correct FNV-1a offset basis `0x811c9dc5` (2166136261), which was not in the symbol table or any hint, so it came from the machine code. The same C file compiled for x86-64 gave equivalent C, as a cross-check.

## What this does and does not prove

- Proves: the real SLEIGH + decompiler logic works from our sources and spec files, fed bytes by our own parser, without libbfd or Ghidra's Java.
- Does not prove: anything about Android. Same sources have not yet been compiled with the NDK, and nothing has run on an ARM64 Android device (bionic libc, libc++, memory limits).
- Names such as `sum_squares` come from the file's original symbol table. Parameter names (`param_1`) and local names (`iVar1`) are decompiler-generated, not original.
- The test ELF is an unstripped toy program. Results on stripped real-world libraries are not yet measured.
- This stage used the console front end. The shipping app will use a JNI entry point instead.

## Next

1. NDK cross-compile of the same source list for arm64-v8a, then a small native test executable.
2. Run that executable on a real ARM64 Android device (Termux or adb). Only that counts as Phase 2 complete.
3. Replace the XML hand-off with a custom `LoadImage` fed from mapped ELF segments.
