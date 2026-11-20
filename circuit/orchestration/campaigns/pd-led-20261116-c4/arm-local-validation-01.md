# C4c local Board L ARM validation and package pin

- Parent: [#308](https://github.com/Takazudo/zudo-pd/issues/308); Moya retains
  integration authority. This isolated follow-up is based on independently
  accepted C4b `4a51b12626a2ecdbabab1dfcfdbbffc8bfa49b5d`.
- Branch: `codex/c4c-led-arm-pin-20261116-01`. The only source edit is the
  version-qualified Ubuntu apt installation in the new root LED firmware
  workflow. Historical LED source, Makefile, evidence, #307 and publication
  files are unchanged.
- Git tree ID of `products/led-lamp/firmware/board-l/`:
  `2b03d2780ddbafa8468a8876dce2c452970fc668`.
  Imported workflow SHA256:
  `5c4bb2c617825572b48c810b5f44d43c5391750ef158d758faa779548e7dc1af`.
  Target Makefile SHA256:
  `f4d8e33d2a17e5d55c5c89b99195e892ee238a9973726ccfc03c33380c68b1b1`.

No existing `workflow_dispatch` job runs LED firmware. The three available
manual workflows are dedicated to PD20 rebuild, B20 field sync and phase33
reference extraction. C4b's workflow is not on default `main`, and no PR was
opened. To verify its unrun ARM job, a disposable container used the official
Ubuntu 24.04 image at
`sha256:73b999393d07f2bf65a40373778a44dc9a6d54ad7718d29247d8ff9413c4d6a8`.
It mounted the Board L source read-only and built a copy under `/tmp`. Docker
enforced two CPUs and a 4 GiB memory limit; peak aggregate usage was not
measured. This local run is not a GitHub Actions result.

Ubuntu 24.04's package index supplied `gcc-arm-none-eabi`
`15:13.2.rel1-2`, `binutils-arm-none-eabi` `2.42-1ubuntu1+23`, and
`libnewlib-arm-none-eabi` `4.4.0.20231231-2`. The first and third were installed
with exact versions; binutils arrived as their dependency at the stated
version. C4c pins all three in the workflow so a future package change fails
explicitly. The Makefile still independently requires GCC 13.2.1 and the
default `CTRL_FULL_CCR = 2407` for the unchanged 200 mOhm RS1 assumption.

Local results on the copied source:

- Clean target build and receipt: **PASS**, compiler 13.2.1, status
  `UNFLASHED BENCH CANDIDATE`; flash 10,908/65,536 bytes, static RAM
  984/8,192 bytes.
- Independent `arm-none-eabi-objcopy` image comparison: **PASS**, 10,908
  bytes, SHA256
  `421e5b6d5626355170491edf257844d774d93b3c89e32ab20f3982cd1fec2a9e`.
- All V72 units cross-compile and `make check-incremental`: **PASS**,
  including header/configuration rebuild and nondefault ceiling refusal.

The scratch-copy build receipt could not record a Git revision because the
copy had no `.git`; the source tree ID above binds the inspected firmware
inputs. This does not prove the exact GitHub runner image or a future apt
mirror. Independent exact-head review and eventual exact-integration-head CI
remain required. No CI, PR, merge, deploy, flash, CAD or physical action ran.
