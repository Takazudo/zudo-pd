#include "board_adc.h"
#include "stm32g031_regs.h"

#define ADC_SPIN_LIMIT 100000u
#define KNOB_PIN 0u
#define NTC_PIN 4u

static bool wait_flag(volatile uint32_t *reg, uint32_t mask, uint32_t want)
{
    for (uint32_t i = 0; i < ADC_SPIN_LIMIT; i++)
        if ((*reg & mask) == want)
            return true;
    return false;
}

static void pin_analog(unsigned pin)
{
    GPIOA_MODER |= GPIO_MODE_ANALOG << (2u * pin);
}

/* Order follows ST LL usage: clock mode with ADEN = 0, regulator on and its
 * startup time (tADCVREG_STUP, [DS] not retained; 2 ms is used), calibration,
 * configuration with ADEN = 0, CHSELR + CCRDY, then enable and wait ADRDY. */
bool board_adc_init(void (*delay_ms)(uint32_t))
{
    if (!delay_ms)
        return false;
    RCC_IOPENR |= RCC_IOPENR_GPIOAEN_BIT;
    RCC_APBENR2 |= RCC_APBENR2_ADCEN_BIT;
    (void)RCC_APBENR2;
    pin_analog(KNOB_PIN);
    pin_analog(NTC_PIN);
    if (ADC1_CR & ADC_CR_ADEN_BIT)
        return false;
    /* PCLK/2 = 32 MHz at 64 MHz; the ADC clock limit is [DS]. */
    ADC1_CFGR2 = ADC_CFGR2_CKMODE_PCLK_DIV2 << ADC_CFGR2_CKMODE_POS;
    ADC1_CR = ADC_CR_ADVREGEN_BIT;
    delay_ms(2u);
    ADC1_CR = ADC_CR_ADVREGEN_BIT | ADC_CR_ADCAL_BIT;
    if (!wait_flag(&ADC1_CR, ADC_CR_ADCAL_BIT, 0u))
        return false;
    /* 12-bit, right-aligned, single scan, upward order, fixed channel mode. */
    ADC1_CFGR1 = 0u;
    /* 160.5 cycles for the ~3.35 kOhm knob and up to ~44 kOhm NTC source
     * (board-l.mdx, owner bring-up). */
    ADC1_SMPR = ADC_SMPR_SMP1_160CYC5;
    ADC1_ISR = ADC_ISR_CCRDY_BIT;
    ADC1_CHSELR = (UINT32_C(1) << KNOB_PIN) | (UINT32_C(1) << NTC_PIN);
    if (!wait_flag(&ADC1_ISR, ADC_ISR_CCRDY_BIT, ADC_ISR_CCRDY_BIT))
        return false;
    ADC1_ISR = ADC_ISR_ADRDY_BIT;
    ADC1_CR = ADC_CR_ADVREGEN_BIT | ADC_CR_ADEN_BIT;
    return wait_flag(&ADC1_ISR, ADC_ISR_ADRDY_BIT, ADC_ISR_ADRDY_BIT);
}

bool board_adc_convert(void *ctx, struct raw_pair *out)
{
    (void)ctx;
    *out = (struct raw_pair){0};
    if (!(ADC1_CR & ADC_CR_ADEN_BIT) || (ADC1_CR & ADC_CR_ADSTART_BIT))
        return false;
    ADC1_ISR = ADC_ISR_EOC_BIT | ADC_ISR_EOS_BIT | ADC_ISR_OVR_BIT | ADC_ISR_EOSMP_BIT;
    ADC1_CR = ADC_CR_ADVREGEN_BIT | ADC_CR_ADEN_BIT | ADC_CR_ADSTART_BIT;
    if (!wait_flag(&ADC1_ISR, ADC_ISR_EOC_BIT, ADC_ISR_EOC_BIT))
        return false;
    out->knob = ADC1_DR & UINT32_C(0xFFF);
    if (!wait_flag(&ADC1_ISR, ADC_ISR_EOC_BIT, ADC_ISR_EOC_BIT))
        return false;
    out->ntc = ADC1_DR & UINT32_C(0xFFF);
    if (!wait_flag(&ADC1_ISR, ADC_ISR_EOS_BIT, ADC_ISR_EOS_BIT) || (ADC1_ISR & ADC_ISR_OVR_BIT))
        return false;
    out->ok = true;
    return true;
}
