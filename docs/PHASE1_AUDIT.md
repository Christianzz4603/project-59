# Phase 1: Repository and Dependency Audit

Upstream audited: NationalSecurityAgency/ghidra, commit `164003036607e669226647bd0f7bedaf281e56a6` (2026-10-21), `application.version=12.3`, release name `DEV`.

Legend: **[verified]** = observed directly in source or by running a command. **[not verified]** = reasoned from file names or structure, not yet confirmed.

## 1. Headline findings

1. **The decompiler and SLEIGH are standalone C++ and are separable from Ghidra's Java.** [verified] They live in `Ghidra/Features/Decompiler/src/decompile/cpp` (240 files) and are built by `Ghidra/Features/Decompiler/buildNatives.gradle`. This is the part that can realistically run on Android.
2. **Ghidra's Java side cannot be ported as-is.** [verified] `Ghidra/application.properties` requires Java 25 and Gradle 9.1+. Android runs ART, not a desktop JVM, so the Java loaders, auto-analysis, program database, and data-type manager do not run on a phone. This is the main limitation and the app must say so honestly.
3. **No Android target exists upstream.** [verified] `buildNatives.gradle` lists win, linux, mac, freebsd and openbsd for x86_64 and arm_64. Android/bionic is not among them, and the Makefile has a TODO about arm64 detection. A Linux ARM64 binary cannot be assumed to run on Android.
4. **The console decompiler (`decomp_opt`) is not usable on Android.** [verified] It needs GNU `libbfd` (`loadimage_bfd.cc`, `-lbfd`). The build failed in my sandbox on missing `bfd.h`. libbfd is GPL and not in the NDK. The app will supply its own loader instead.

## 2. What was actually built and run

All on a Debian x86_64 sandbox, g++ 14.2, `-std=c++11 -O1`. This is a host build, **not** an Android build.

| Step | Result |
|---|---|
| `make sleigh_opt` (real SLEIGH compiler from upstream source) | Built, 914,176 bytes [verified] |
| `sleigh_opt AARCH64.slaspec AARCH64.sla` using Ghidra's own spec | Produced a 495,266-byte `AARCH64.sla` with only optimizer warnings [verified] |
| `make decomp_opt` | Failed: `bfd.h` not found [verified] |
| Decompiling any binary | **Not done yet** |
| NDK cross-compile for arm64-v8a | **Not done yet** |
| Anything on an Android device | **Not done yet** |

I have not yet confirmed that the generated `.sla` decodes real AArch64 code correctly. That is a Phase 2 test.

## 3. Code path: from bytes to pseudocode

Desktop Ghidra's path is: Java loader (`ghidra.app.util.opinion.ElfLoader`, `ElfProgramBuilder`) builds a Program, Java auto-analysis finds functions, then the Java decompiler client talks to a native `decompile` process over stdin/stdout, which calls back into Java for bytes, symbols and types. [partly verified: `ElfLoader.java` exists in Features/Base; the callback behavior is inferred from the `*_ghidra.cc` file names in the build list, which I have not read in detail]

The native side, by role:

| Role | Files (all verified to exist) |
|---|---|
| Core p-code, decompiler analysis | `architecture.cc`, `funcdata*.cc`, `heritage.cc`, `coreaction.cc`, `ruleaction.cc`, `flow.cc`, `block*.cc`, `type*.cc`, `fspec.cc`, `database.cc` |
| C output | `printc.cc`, `printlanguage.cc`, `prettyprint.cc` (also `printjava.cc`) |
| SLEIGH translator (machine code to p-code) | `sleigh.cc`, `sleighbase.cc`, `slghsymbol.cc`, `slghpattern*.cc`, `slaformat.cc`, `compression.cc` |
| Spec compiler | `slgh_compile.cc`, `slghparse.cc`, `slghscan.cc`, `pcodeparse.cc` |
| Embedding API | `libdecomp.hh`: `startDecompilerLibrary(sleighhome)` and `shutdownDecompilerLibrary()` |
| Byte supply interface | `loadimage.hh` (abstract `LoadImage`); `sleighexample.cc` shows a minimal custom `LoadImage` feeding bytes to SLEIGH |
| Java bridge, **not needed on Android** | `ghidra_arch.cc`, `ghidra_process.cc`, `loadimage_ghidra.cc`, `database_ghidra.cc`, `typegrp_ghidra.cc`, `cpool_ghidra.cc`, `comment_ghidra.cc`, `string_ghidra.cc`, `inject_ghidra.cc`, `signature_ghidra.cc` |

Processor specs for AARCH64 exist at `Ghidra/Processors/AARCH64/data/languages/` (`AARCH64.slaspec`, `.ldefs`, `.pspec`, `.cspec` plus Apple/Go/ILP32/Windows variants). [verified] `.sla` files are not in git; they are generated from `.slaspec` by the SLEIGH compiler. [verified]

## 4. Proposed Android architecture

```
Kotlin UI (Compose, Material 3)
   |
Kotlin analyzers: ELF/APK/DEX/XML/resources/strings/symbols (own parsers)
   |  JNI
libghidra_decomp.so  (C++, NDK, arm64-v8a)
   = upstream decompiler + SLEIGH sources, unmodified where possible
   + custom LoadImage subclass (reads mapped ELF segments)
   + custom Architecture setup that points at bundled .ldefs/.pspec/.cspec/.sla
   + thin JNI/marshal layer for: translate to p-code, disassemble, decompile function
```

The build compiles the upstream core and SLEIGH sources but leaves out the `*_ghidra.cc` bridge and `loadimage_bfd.cc`. `.sla` files are generated at build time by a host `sleigh_opt` and bundled as assets, so the phone never compiles specs. [design; not yet implemented]

## 5. What this design can and cannot do

**Can, using the real engine (planned):**
- Machine code to p-code (SLEIGH) and disassembly for architectures whose specs are bundled.
- Decompilation of a function to C-like pseudocode by Ghidra's real decompiler, given bytes, an entry address, and a language/compiler spec.

**Cannot, because it depends on the Java framework:**
- Ghidra's auto-analysis suite (analyzers such as non-returning function detection, stack analysis, data-type archive application, Function ID).
- Ghidra's ELF/PE/Mach-O loaders and program database.
- Function ID databases (`.fidb`), which are consumed by Java.

**Consequence:** function discovery, symbols, relocations and type information come from this project's own Kotlin parsers, not from Ghidra's analyzers. Names from the file will be labeled as original, and anything the app infers will be labeled as inferred. Decompiler output quality will be lower than desktop Ghidra on stripped binaries because the full analyzer pipeline is absent. The app must state this. Function signature databases and DWARF/PDB type import need separate work and are unproven.

## 6. Licensing

- Ghidra is Apache-2.0 with a NOTICE file. [verified] `LICENSE` and `NOTICE` must ship with the app, and file headers must be preserved.
- `GPL/` in upstream holds GPL components (for example `DemanglerGnu`, `GnuDisassembler`) with their own licenses. [verified directory contents; license terms not yet reviewed per file] These must not be linked into the app without a license review. The same applies to libbfd.
- Any DEX decompiler or parser library added later needs its own license and Android-compatibility check before use.

## 7. Open questions and risks

1. Does upstream C++ compile cleanly under the NDK clang and libc++ for arm64-v8a? [not verified; no NDK build attempted]
2. Memory: how large is the decompiler working set on a 4 GB Android 12 device for big functions? [not measured]
3. The decompiler needs function entry points, symbol and type information injected through its C++ interfaces. The exact minimal set to get readable output on an unstripped `.so` is not yet determined.
4. x86 and ARM32 specs: they exist upstream but have not been compiled here. Only AARCH64 was.
5. The `.sla` produced here was not validated against real code.

## 8. Next step (Phase 2)

Smallest credible proof, in this order:

1. A GitHub Actions workflow that builds `sleigh_opt` on the runner and generates `AARCH64.sla`.
2. A small C++ harness against `libdecomp` with a custom `LoadImage` that decompiles one function from a known ELF, run on the CI host first. This validates the pipeline logic, but is **not** an Android test.
3. Cross-compile the same sources with the NDK for arm64-v8a, then run on a real ARM64 Android device. Only that result counts as Phase 2 success.

No UI work until step 2 produces real pseudocode.
