#include "clock.h"
#include "stm32g031_regs.h"

/* HSI16 / M 2 = 8 MHz VCO input (ST LL: 4..8 MHz), x N 16 = 128 MHz VCO
 * (ST LL: 64..344 MHz), / R 2 = 64 MHz SYSCLK. 48 < HCLK <= 64 MHz needs 2 flash
 * wait states in voltage range 1 (ST LL_SetFlashLatency). Sources in stm32g031_regs.h. */
#define PLL_M_FIELD 1u   /* LL_RCC_PLLM_DIV_2 */
#define PLL_N 16u
#define PLL_R_FIELD 1u   /* LL_RCC_PLLR_DIV_2 */
#define SPIN_LIMIT 100000u

static int wait_set(volatile uint32_t *reg, uint32_t mask, uint32_t want)
{
    for (uint32_t i = 0; i < SPIN_LIMIT; i++)
        if ((*reg & mask) == want)
            return 1;
    return 0;
}

enum clock_result clock_init_64mhz(void)
{
    RCC_APBENR1 |= RCC_APBENR1_PWREN_BIT;
    (void)RCC_APBENR1;
    if ((PWR_CR1 & PWR_CR1_VOS_MSK) != PWR_CR1_VOS_RANGE1 || (PWR_SR2 & PWR_SR2_VOSF_BIT))
        return CLOCK_HSI16_NOT_RANGE1;
    if (!wait_set(&RCC_CR, RCC_CR_HSIRDY_BIT, RCC_CR_HSIRDY_BIT))
        return CLOCK_HSI16_TIMEOUT;

    FLASH_ACR = (FLASH_ACR & ~FLASH_ACR_LAT_MSK) | FLASH_LATENCY_2WS;
    if (!wait_set(&FLASH_ACR, FLASH_ACR_LAT_MSK, FLASH_LATENCY_2WS))
        return CLOCK_HSI16_TIMEOUT;

    RCC_CR &= ~RCC_CR_PLLON_BIT;
    if (!wait_set(&RCC_CR, RCC_CR_PLLRDY_BIT, 0u))
        return CLOCK_HSI16_TIMEOUT;
    RCC_PLLCFGR = RCC_PLLCFGR_SRC_HSI | (PLL_M_FIELD << RCC_PLLCFGR_M_POS)
                  | (PLL_N << RCC_PLLCFGR_N_POS) | (PLL_R_FIELD << RCC_PLLCFGR_R_POS)
                  | RCC_PLLCFGR_REN;
    RCC_CR |= RCC_CR_PLLON_BIT;
    if (!wait_set(&RCC_CR, RCC_CR_PLLRDY_BIT, RCC_CR_PLLRDY_BIT))
        return CLOCK_HSI16_TIMEOUT;

    RCC_CFGR = (RCC_CFGR & ~RCC_CFGR_SW_MSK) | RCC_CFGR_SW_PLL;
    if (!wait_set(&RCC_CFGR, RCC_CFGR_SWS_MSK, RCC_CFGR_SWS_PLL))
        return CLOCK_HSI16_TIMEOUT;
    return CLOCK_PLL_64MHZ;
}

uint32_t clock_hclk_hz(enum clock_result r)
{
    /* Mirrors ST SystemCoreClockUpdate(): HSI_VALUE 16 MHz, HSISYS = HSI16 >> HSIDIV,
     * AHB prescaler codes 0..7 divide by 1. Any other HPRE code returns 0 (unknown). */
    if (RCC_CFGR & UINT32_C(0x800))
        return 0u;
    if (r == CLOCK_PLL_64MHZ)
        return UINT32_C(64000000);
    return UINT32_C(16000000) >> ((RCC_CR & RCC_CR_HSIDIV_MSK) >> RCC_CR_HSIDIV_POS);
}
