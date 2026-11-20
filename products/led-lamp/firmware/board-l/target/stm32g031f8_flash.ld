/* STM32G031F8P6 memory map for the Board L target skeleton.
 * FLASH_BASE 0x08000000 and SRAM_BASE 0x20000000: ST stm32g031xx.h (see stm32g031_regs.h).
 * 64 KB flash and 8 KB RAM for STM32G031F8: ST STM32_open_pin_data
 * mcu/STM32G031F(4-6-8)Px.xml (Flash 16/32/64 KB per variant, Ram 8 KB), and
 * SRAM_SIZE_MAX 0x2000 in stm32g031xx.h. */
ENTRY(Reset_Handler)

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 64K
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 8K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);
_min_stack = 0x400;

SECTIONS
{
  .isr_vector :
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector))
    . = ALIGN(4);
  } > FLASH

  .text :
  {
    . = ALIGN(4);
    *(.text .text.*)
    *(.rodata .rodata.*)
    . = ALIGN(4);
  } > FLASH

  .ARM.exidx : { *(.ARM.exidx* .gnu.linkonce.armexidx.*) } > FLASH

  _sidata = LOADADDR(.data);

  .data :
  {
    . = ALIGN(4);
    _sdata = .;
    *(.data .data.*)
    . = ALIGN(4);
    _edata = .;
  } > RAM AT > FLASH

  .bss (NOLOAD) :
  {
    . = ALIGN(4);
    _sbss = .;
    *(.bss .bss.*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;
  } > RAM

  /* Reset-cause latch record: never loaded or zeroed, survives non-power resets. */
  .noinit (NOLOAD) :
  {
    . = ALIGN(4);
    *(.noinit .noinit.*)
    . = ALIGN(4);
    _enoinit = .;
  } > RAM

  ASSERT(_enoinit + _min_stack <= _estack, "RAM overflow: less than 1 KB left for the stack")

  /DISCARD/ : { *(.ARM.attributes.discard) }
}
