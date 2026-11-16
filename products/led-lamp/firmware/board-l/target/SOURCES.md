# Sources for the target skeleton's manufacturer facts

ST's RM0444 and the STM32G031 datasheet could not be fetched from st.com: both attempts
returned an empty reply, and this was not bypassed. Every register, field value and
memory size used here instead comes from ST's and ARM's official public source
repositories, cloned with one ordinary shallow clone each on 2026-10-31. Nothing is taken
from memory. These sources are not vendored into the repository.

| Source | Commit | File | SHA256 | Used for |
| --- | --- | --- | --- | --- |
| github.com/STMicroelectronics/cmsis_device_g0 (Apache-2.0) | `7c77b7cbcee497dfbb5cc08f9562a80515e78013` | `Include/stm32g031xx.h` | `336a1cdbbb54593c0d78c4c9440914deac58a523021883b7c96a76e7613f0a90` | Base addresses, register offsets, bit masks, `SRAM_SIZE_MAX` |
| same | same | `Source/Templates/gcc/startup_stm32g031xx.s` | `19c2c7668ac7aa0bba11a7ec806b6ba493cd5343bdea56ea0cc011f842ca252e` | Vector table order |
| same | same | `Source/Templates/system_stm32g0xx.c` | (read only) | HSI_VALUE 16 MHz; HSIDIV/HPRE clock computation |
| github.com/STMicroelectronics/stm32g0xx_hal_driver | `289ef6c8ff0922878e99d253f29be76851f8f28e` | `Src/stm32g0xx_ll_utils.c` | `2958dc3b2b62c81632f627162c245321a04ebc794e02cc71fb160fe8a1026d5f` | PLL VCO input 4–8 MHz and output 64–344 MHz; flash latency 2 WS for 48 < HCLK ≤ 64 MHz (range 1) |
| same | same | `Inc/stm32g0xx_ll_{rcc,pwr,tim,gpio,system}.h` | (checked by `verify-regs`) | PLLM/PLLR codes, range-1 VOS code, PWM mode 1 semantics, GPIO mode/pull/AF codes |
| github.com/STMicroelectronics/STM32_open_pin_data | `7d1f1514ed5583ec5007ad91236b4e1d377295b1` | `mcu/STM32G031F(4-6-8)Px.xml` | `73990654d1843ac7764948675638723faca06f0742f651a2ce0516723ec316b2` | TSSOP20; PA6 = pin 13; Flash 16/32/64 KB, RAM 8 KB, 64 MHz |
| same | same | `mcu/IP/GPIO-STM32G03x_gpio_v1_0_Modes.xml` | `66180bd8c0ebc0a9576f9524279c738e15bc9f4af27bacfb7509bf0e8b88b782` | PA6 TIM3_CH1 = `GPIO_AF1_TIM3` |
| github.com/ARM-software/CMSIS_5 | `55b19837f5703e418ca37894d5745b1dc05e4c91` | `CMSIS/Core/Include/core_cm0plus.h` | `05c1ad27fa722d82f3a2babe15f80d62c737cbdc37678e85f33fbd1a26f33f4e` | SysTick address and fields |

To re-check, clone those commits outside the repository and run:

```sh
make verify-regs ST_DEVICE_INC=<cmsis_device_g0>/Include \
  ST_LL_INC=<stm32g0xx_hal_driver>/Inc CMSIS_CORE_INC=<CMSIS_5>/CMSIS/Core/Include
python3 -I verify/check_vectors.py startup_stm32g031.c \
  <cmsis_device_g0>/Source/Templates/gcc/startup_stm32g031xx.s
```

These are manufacturer code repositories, not RM0444 itself. Electrical timing,
option-byte behaviour and errata stay with RM0444, the datasheet and the errata sheet,
none of which is retained (see `.claude/skills/component-stm32g031f8p6/`).
