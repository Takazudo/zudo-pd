# Isolated native Mac KiCad 10.0.6 capability

The official exact-version universal DMG was acquired and verified by published SHA-256/size, deep strict code signing and notarization. See the acquisition/capability JSON files beside this document. The installed `/Applications/KiCad/KiCad.app` remains 10.0.0 and is not acceptance tooling.

The read-only task-local mount and wrappers are under `tmp/kicad-macos-10.0.6/`. The explicit CLI wrapper sets `KICAD_CONFIG_HOME`, `KICAD_DOCUMENTS_HOME` and `KICAD_CACHE_HOME` to separate task-local directories before executing the mounted app's `Contents/MacOS/kicad-cli`. Isolating only configuration initially crashed in PCM library traversal; that failed smoke is retained locally. Isolating all three documented locations resolved the crash without user-configuration changes or disabled security controls.

Actual ARM64 smoke verified CLI and pcbnew 10.0.6, bundled Python 3.9.13, wx 4.2.2a1 / wxWidgets 3.2.8, and a 320×240 high-quality synthetic render under both machine guards. This is capability evidence, not product acceptance. Final project commands use Python 3.12 for CadQuery/verification, the explicit Mac CLI, and the already verified pinned Docker pcbnew Python where the project scripts require it. The pinned Docker generator workflow remains unchanged.

Every native workflow must still hold the machine-wide heavy guard and `/tmp/kicad-native.lock`. A successful smoke does not replace the final source-bound assembly/export runs. The full product command and artifact hashes are recorded separately when executed. No Windows ST GUI execution is implied.
