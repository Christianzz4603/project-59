# Ghidra Mobile

An Android ARM64 reverse-engineering app built around Ghidra's real SLEIGH translator and native decompiler (upstream: https://github.com/NationalSecurityAgency/ghidra, Apache-2.0).

## Status

Phase 1 (repository and dependency audit) is done. See [docs/PHASE1_AUDIT.md](docs/PHASE1_AUDIT.md).

Nothing in this repo has been built into an APK or tested on Android yet. Each claim in the audit is marked as verified or not verified.

## Rules this project follows

- Pseudocode comes only from Ghidra's real decompiler, never from text transformation or an LLM.
- Original symbols are kept separate from names the analyzer infers.
- Unsupported formats and missing metadata are reported honestly.
- Imported files are untrusted and are never executed.
- Upstream license notices are preserved.
