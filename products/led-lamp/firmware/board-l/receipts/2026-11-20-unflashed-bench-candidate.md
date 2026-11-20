# Board L firmware: UNFLASHED BENCH CANDIDATE (built 2026-11-20)

**Status: UNFLASHED BENCH CANDIDATE.** Build-only. Not flashed, not run, not option-byte-verified,
not validated or released. Programming or energizing any Board L needs separate explicit owner
permission and [`BEFORE-PROGRAMMING-CHECKLIST.md`](../BEFORE-PROGRAMMING-CHECKLIST.md).

## Identity

| Item | Value |
| --- | --- |
| Source | zudo-led-lamp `dd4cb00ab3f5a9fe0024e3ca5e4a5cd5b8437aaa` (main), fresh clone, `repository_dirty` false, `firmware_dirty` false |
| Same tree in zudo-pd candidate | `products/led-lamp/firmware` tree `dba59a4a…` on `origin/codex/c5-asset-provenance-20261117-01` (`c3d13892`) = LED main |
| Target toolchain | `arm-none-eabi-gcc (15:13.2.rel1-2) 13.2.1 20231009`; apt `gcc-arm-none-eabi 15:13.2.rel1-2`, `libnewlib-arm-none-eabi 4.4.0.20231231-2`, `binutils-arm-none-eabi 2.42-1ubuntu1+23` (Ubuntu 24.04.5). `matches_pin` true (pin 13.2.1) |
| Host compiler | gcc 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1) |
| Profile / options | `default-rs1-200mohm`, `BOARD_DEFS` empty, `BOARD_L_PRODUCTION` not defined; CFLAGS `-mcpu=cortex-m0plus -mthumb -std=c11 -Os -g -Wall -Wextra -Werror -pedantic -ffreestanding -ffunction-sections -fdata-sections`; LDFLAGS `--specs=nano.specs --specs=nosys.specs -nostartfiles -T stm32g031f8_flash.ld -Wl,--gc-sections`; config_id `71633366…f55e8` |

## Constants found in code

| Constant | Value | Where |
| --- | --- | --- |
| `CTRL_FULL_CCR` | **2407u** (75.22 %), `adopted_default` true; Makefile `cap-check` refuses any other effective value without `ACCEPT_NONDEFAULT_CAP=1` | `target/board_l_proposal.h:19` (sha256 `84e6e29c…5c021`) |
| `CTRL_PERIOD_TICKS` / `CTRL_MIN_CCR` | 3200u (20 kHz) / 518u | `board_l_proposal.h:9,11` |
| RS1 | **No code constant.** 200 mΩ appears only in comments (`board_l_proposal.h:12-17`) and as receipt field `ctrl_ceiling.assumed_rs1_mohm` = 200. The physical value must be read four-wire (checklist 1.1) | — |
| Ramp / latch / IWDG / BOR | `LAMP_RAMP_INCREMENT` 26u (~2.5 s), `RESET_LATCH_COUNT` 3u, `RESET_HEALTHY_TICKS` 10000u, IWDG /32 reload 99, BOR level field 3 | `board_l_proposal.h` |
| Noise / gamma | NULL noise (steady), no transfer (linear): the current image's conservative choice, **not an approved product decision** (OPEN-PRODUCT-DECISIONS D1/D2) | `target/main.c` |

## Artifacts (not committed; hashes only)

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `board-l-skeleton.bin` (raw loadable image, `objcopy -O binary`) | 10908 | `421e5b6d5626355170491edf257844d774d93b3c89e32ab20f3982cd1fec2a9e` |
| `board-l-skeleton.hex` (Intel HEX of the same ELF; convenience) | 30738 | `b8e6952d678a8d971ecec29e664014ecc33756d6e7dc3f339b78d2bbc322a36a` |
| `board-l-skeleton.elf` (path-dependent debug data) | — | `ae3158556e408ca5881ebba5ffa19c39b49bb9473c727dcc8100bb2b4cc9a2e9` |
| `board-l-skeleton.map` | — | `f513a65ff911ff57d20217aa1786c7398d89f8716e3d6f9af0e97923a5e1d248` |
| `board-l-skeleton.receipt.json` (repo tool output) | — | `422f18df73fe775637021412a03d15168657c17466d04002d73b71b931327f51` |

- The loadable image equals the receipt's `loadable_image_sha256`/`loadable_image_bytes` and the value
  recorded on 2026-11-08 in `firmware/board-l/target/README.md:88` (`421e5b6d…2a9e`).
- Readback range: `[0x08000000, 0x08000000 + 10908)`. The image contains a 4-byte zero gap at
  `0x080000BC–0x080000BF` between `.isr_vector` (188 B) and `.text` (at `0x080000C0`).
- Memory: `size` text 10904 B, data 0, bss 984 B (`.bss` 968 + `.noinit` 16). Linker FLASH 10908 B / 64 KB, RAM 984 B / 8 KB.

## Commands and outcomes (in the clone's `firmware/board-l/target/`)

| Command | Exit | Outcome |
| --- | --- | --- |
| `make host-test target-host-test` | 0 | PASS 44 (V72 knob averaging); PASS 5430 (lamp_target); PASS 106 (boot policy); PASS 71053 (sample chain) |
| `make clean && make` | 0 | Receipt `UNFLASHED BENCH CANDIDATE`, profile `default-rs1-200mohm`, `CTRL_FULL_CCR` 2407 |
| CI identity step (`objcopy -O binary` + Python compare) | 0 | PASS raw binary 10908 B, `421e5b6d…2a9e` |
| `make v72-objects` | 0 | 33/33 V72 units cross-compiled (not linked) |
| `TMPDIR=… make check-incremental` | 0 | 12/12 PASS (no-op, header/Makefile/V72-header touches, cap refusal, nondefault rebuild, BOARD_DEFS switch, `-DCTRL_FULL_CCR=3200` refused, incremental = clean) |

These checks were not run: `make verify-regs` and `verify/check_vectors.py` need ST/ARM headers and ST's startup file from outside the repo. The README mutation runs were also not repeated. No flashing, option-byte access, readback or energizing was done. Build logs and binary images were kept outside the repository and are not committed. The machine-readable copy is [`2026-11-20-unflashed-bench-candidate.json`](2026-11-20-unflashed-bench-candidate.json).
