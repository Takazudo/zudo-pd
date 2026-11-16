/* Cortex-M0+ vector table and reset entry for STM32G031.
 * Entry order follows ST cmsis_device_g0 Source/Templates/gcc/startup_stm32g031xx.s
 * (@7c77b7cbcee497dfbb5cc08f9562a80515e78013, SHA256
 * 19c2c7668ac7aa0bba11a7ec806b6ba493cd5343bdea56ea0cc011f842ca252e).
 * verify/check_vectors.py compares this table with that file. */
#include <stdint.h>
#include "board_ctrl.h"

extern uint32_t _sidata[], _sdata[], _edata[], _sbss[], _ebss[], _estack[];
int main(void);

void Reset_Handler(void);
void Default_Handler(void);
void HardFault_Handler(void);

#define WEAK_DEFAULT __attribute__((weak, alias("Default_Handler")))
void NMI_Handler(void) WEAK_DEFAULT;
void SVC_Handler(void) WEAK_DEFAULT;
void PendSV_Handler(void) WEAK_DEFAULT;
void SysTick_Handler(void) WEAK_DEFAULT;
void WWDG_IRQHandler(void) WEAK_DEFAULT;
void PVD_IRQHandler(void) WEAK_DEFAULT;
void RTC_TAMP_IRQHandler(void) WEAK_DEFAULT;
void FLASH_IRQHandler(void) WEAK_DEFAULT;
void RCC_IRQHandler(void) WEAK_DEFAULT;
void EXTI0_1_IRQHandler(void) WEAK_DEFAULT;
void EXTI2_3_IRQHandler(void) WEAK_DEFAULT;
void EXTI4_15_IRQHandler(void) WEAK_DEFAULT;
void DMA1_Channel1_IRQHandler(void) WEAK_DEFAULT;
void DMA1_Channel2_3_IRQHandler(void) WEAK_DEFAULT;
void DMA1_Ch4_5_DMAMUX1_OVR_IRQHandler(void) WEAK_DEFAULT;
void ADC1_IRQHandler(void) WEAK_DEFAULT;
void TIM1_BRK_UP_TRG_COM_IRQHandler(void) WEAK_DEFAULT;
void TIM1_CC_IRQHandler(void) WEAK_DEFAULT;
void TIM2_IRQHandler(void) WEAK_DEFAULT;
void TIM3_IRQHandler(void) WEAK_DEFAULT;
void LPTIM1_IRQHandler(void) WEAK_DEFAULT;
void LPTIM2_IRQHandler(void) WEAK_DEFAULT;
void TIM14_IRQHandler(void) WEAK_DEFAULT;
void TIM16_IRQHandler(void) WEAK_DEFAULT;
void TIM17_IRQHandler(void) WEAK_DEFAULT;
void I2C1_IRQHandler(void) WEAK_DEFAULT;
void I2C2_IRQHandler(void) WEAK_DEFAULT;
void SPI1_IRQHandler(void) WEAK_DEFAULT;
void SPI2_IRQHandler(void) WEAK_DEFAULT;
void USART1_IRQHandler(void) WEAK_DEFAULT;
void USART2_IRQHandler(void) WEAK_DEFAULT;
void LPUART1_IRQHandler(void) WEAK_DEFAULT;

typedef void (*vector_t)(void);

__attribute__((section(".isr_vector"), used))
const vector_t g_vectors[] = {
    (vector_t)(uintptr_t)_estack,
    Reset_Handler,
    NMI_Handler,
    HardFault_Handler,
    0, 0, 0, 0, 0, 0, 0,
    SVC_Handler,
    0, 0,
    PendSV_Handler,
    SysTick_Handler,
    WWDG_IRQHandler,
    PVD_IRQHandler,
    RTC_TAMP_IRQHandler,
    FLASH_IRQHandler,
    RCC_IRQHandler,
    EXTI0_1_IRQHandler,
    EXTI2_3_IRQHandler,
    EXTI4_15_IRQHandler,
    0,
    DMA1_Channel1_IRQHandler,
    DMA1_Channel2_3_IRQHandler,
    DMA1_Ch4_5_DMAMUX1_OVR_IRQHandler,
    ADC1_IRQHandler,
    TIM1_BRK_UP_TRG_COM_IRQHandler,
    TIM1_CC_IRQHandler,
    TIM2_IRQHandler,
    TIM3_IRQHandler,
    LPTIM1_IRQHandler,
    LPTIM2_IRQHandler,
    TIM14_IRQHandler,
    0,
    TIM16_IRQHandler,
    TIM17_IRQHandler,
    I2C1_IRQHandler,
    I2C2_IRQHandler,
    SPI1_IRQHandler,
    SPI2_IRQHandler,
    USART1_IRQHandler,
    USART2_IRQHandler,
    LPUART1_IRQHandler,
    0,
};

void Reset_Handler(void)
{
    /* CTRL is driven low before anything else, including RAM init. */
    board_ctrl_force_off();
    for (uint32_t *s = _sidata, *d = _sdata; d < _edata;)
        *d++ = *s++;
    for (uint32_t *d = _sbss; d < _ebss;)
        *d++ = 0u;
    (void)main();
    for (;;)
        board_ctrl_force_off();
}

/* Unexpected interrupts and faults: force CTRL low and stop without refreshing the
 * IWDG, so the watchdog resets the MCU and main.c's reset-cause latch counts it. */
void Default_Handler(void)
{
    for (;;)
        board_ctrl_force_off();
}

void HardFault_Handler(void)
{
    for (;;)
        board_ctrl_force_off();
}
