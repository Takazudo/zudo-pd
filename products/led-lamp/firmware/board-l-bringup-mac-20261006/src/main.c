#include <stdint.h>
#include "stm32g0xx.h"

/* Board L bring-up firmware: knob (PA0) -> gamma -> 20 kHz PWM (PA6) into the
 * CTRL RC filter, NTC (PA4) thermal derate, status over USART2 (J4, 115200 8N1).
 * No flame modulation yet. Pin map: doc/src/content/docs/architecture/board-l.mdx. */

#define FRAME_MS            20

/* CTRL window from the R20/R21 divider and the AL8860 0.3-2.5 V analog range
 * (board-l.mdx "Modulation algorithm"). Raise DUTY_FLOOR_Q16 above the
 * pulse-skip point recorded at Gate 4 if it bursts below ~300 Hz. */
#define DUTY_FLOOR_Q16      10617u   /* CTRL 0.41 V -> 5% of I_NOM */
#define DUTY_FULL_Q16       65535u   /* CTRL 2.53 V -> 100%        */

#define PWM_HZ              20000u
#define PWM_PERIOD          (64000000u / PWM_HZ)   /* 3200 timer ticks */

/* Knob calibration. Read raw codes over UART at both stops, then set these.
 * R22 (100k) loads the wiper, so the ends are not exactly 0 and 4095. */
#define KNOB_MIN_CODE       60
#define KNOB_MAX_CODE       4000
#define KNOB_INVERT         0
#define KNOB_OFF_LEVEL      2        /* perceptual level at or below which the lamp is off */

/* Slew limit: perceptual steps per frame (0 -> 255 in ~2.5 s at 50 Hz). */
#define RAMP_STEP           2

/* NTC thresholds as 12-bit codes (board-l.mdx "Thermal derate"); code falls as
 * temperature rises. Above NTC_OPEN_CODE the sensor is treated as open. */
#define NTC_DERATE_CODE     104      /* ~65 C */
#define NTC_CRITICAL_CODE   69       /* ~80 C */
#define NTC_OPEN_CODE       3500

#define ADC_CH_KNOB         0
#define ADC_CH_NTC          4

static const uint8_t gamma_lut[256] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,
      1,   1,   1,   1,   1,   1,   1,   1,   1,   2,   2,   2,   2,   2,   2,   2,
      3,   3,   3,   3,   3,   4,   4,   4,   4,   5,   5,   5,   5,   6,   6,   6,
      6,   7,   7,   7,   8,   8,   8,   9,   9,   9,  10,  10,  11,  11,  11,  12,
     12,  13,  13,  13,  14,  14,  15,  15,  16,  16,  17,  17,  18,  18,  19,  19,
     20,  20,  21,  22,  22,  23,  23,  24,  25,  25,  26,  26,  27,  28,  28,  29,
     30,  30,  31,  32,  33,  33,  34,  35,  35,  36,  37,  38,  39,  39,  40,  41,
     42,  43,  43,  44,  45,  46,  47,  48,  49,  49,  50,  51,  52,  53,  54,  55,
     56,  57,  58,  59,  60,  61,  62,  63,  64,  65,  66,  67,  68,  69,  70,  71,
     73,  74,  75,  76,  77,  78,  79,  81,  82,  83,  84,  85,  87,  88,  89,  90,
     91,  93,  94,  95,  97,  98,  99, 100, 102, 103, 105, 106, 107, 109, 110, 111,
    113, 114, 116, 117, 119, 120, 121, 123, 124, 126, 127, 129, 130, 132, 133, 135,
    137, 138, 140, 141, 143, 145, 146, 148, 149, 151, 153, 154, 156, 158, 159, 161,
    163, 165, 166, 168, 170, 172, 173, 175, 177, 179, 181, 182, 184, 186, 188, 190,
    192, 194, 196, 197, 199, 201, 203, 205, 207, 209, 211, 213, 215, 217, 219, 221,
    223, 225, 227, 229, 231, 234, 236, 238, 240, 242, 244, 246, 248, 251, 253, 255,
};

static volatile uint32_t ms_ticks;

void SysTick_Handler(void)
{
    ms_ticks++;
}

static void delay_ms(uint32_t ms)
{
    uint32_t start = ms_ticks;
    while ((ms_ticks - start) < ms) {
    }
}

static void clock_init(void)
{
    /* HSI16 -> PLL (M=1, N=8, R=2) -> 64 MHz SYSCLK; flash needs 2 wait states. */
    FLASH->ACR = (FLASH->ACR & ~FLASH_ACR_LATENCY) | FLASH_ACR_LATENCY_1 | FLASH_ACR_PRFTEN | FLASH_ACR_ICEN;
    while ((FLASH->ACR & FLASH_ACR_LATENCY) != FLASH_ACR_LATENCY_1) {
    }

    RCC->PLLCFGR = RCC_PLLCFGR_PLLSRC_HSI
                 | (0u << RCC_PLLCFGR_PLLM_Pos)
                 | (8u << RCC_PLLCFGR_PLLN_Pos)
                 | (1u << RCC_PLLCFGR_PLLR_Pos)
                 | RCC_PLLCFGR_PLLREN;
    RCC->CR |= RCC_CR_PLLON;
    while (!(RCC->CR & RCC_CR_PLLRDY)) {
    }

    RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_SW) | (2u << RCC_CFGR_SW_Pos);
    while ((RCC->CFGR & RCC_CFGR_SWS) != (2u << RCC_CFGR_SWS_Pos)) {
    }

    SystemCoreClock = 64000000u;
    SysTick_Config(SystemCoreClock / 1000u);
}

static void gpio_set_af(uint32_t pin, uint32_t af)
{
    GPIOA->MODER = (GPIOA->MODER & ~(3u << (pin * 2))) | (2u << (pin * 2));
    if (pin < 8) {
        GPIOA->AFR[0] = (GPIOA->AFR[0] & ~(0xFu << (pin * 4))) | (af << (pin * 4));
    } else {
        GPIOA->AFR[1] = (GPIOA->AFR[1] & ~(0xFu << ((pin - 8) * 4))) | (af << ((pin - 8) * 4));
    }
}

static void gpio_set_input(uint32_t pin)
{
    GPIOA->MODER &= ~(3u << (pin * 2));
}

/* PA6 stays in its reset (analog, Hi-Z) state until TIM3 is running at 0% duty,
 * so R21 holds CTRL low throughout init. PA13/PA14 (SWD) and PA15 (bonded to the
 * SWCLK pin) are never touched. */
static void pwm_init(void)
{
    TIM3->PSC = 0;
    TIM3->ARR = PWM_PERIOD - 1u;
    TIM3->CCR1 = 0;
    TIM3->CCMR1 = (6u << TIM_CCMR1_OC1M_Pos) | TIM_CCMR1_OC1PE;
    TIM3->CCER = TIM_CCER_CC1E;
    TIM3->CR1 = TIM_CR1_ARPE;
    TIM3->EGR = TIM_EGR_UG;
    TIM3->CR1 |= TIM_CR1_CEN;

    gpio_set_af(6, 1);   /* PA6 = TIM3_CH1 */
}

static void pwm_set_duty_q16(uint32_t duty_q16)
{
    TIM3->CCR1 = (duty_q16 * PWM_PERIOD) >> 16;
}

static void uart_init(void)
{
    gpio_set_af(2, 1);   /* PA2 = USART2_TX */
    gpio_set_af(3, 1);   /* PA3 = USART2_RX */
    USART2->BRR = (64000000u + 115200u / 2u) / 115200u;
    USART2->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_UE;
}

static void uart_putc(char c)
{
    while (!(USART2->ISR & USART_ISR_TXE_TXFNF)) {
    }
    USART2->TDR = (uint8_t)c;
}

static void uart_puts(const char *s)
{
    while (*s) {
        uart_putc(*s++);
    }
}

static void uart_put_u32(uint32_t v)
{
    char buf[10];
    int n = 0;
    do {
        buf[n++] = (char)('0' + v % 10u);
        v /= 10u;
    } while (v);
    while (n) {
        uart_putc(buf[--n]);
    }
}

static void uart_field(const char *name, uint32_t v)
{
    uart_puts(name);
    uart_putc('=');
    uart_put_u32(v);
    uart_putc(' ');
}

static void adc_init(void)
{
    ADC1->CFGR2 = (1u << ADC_CFGR2_CKMODE_Pos);   /* PCLK/2 = 32 MHz, within the 35 MHz table */
    ADC1->CR |= ADC_CR_ADVREGEN;
    delay_ms(1);                                   /* regulator startup, >= 20 us */

    ADC1->CR |= ADC_CR_ADCAL;
    while (ADC1->CR & ADC_CR_ADCAL) {
    }

    /* 160.5-cycle sampling for the ~3.35 kOhm knob and up to ~44 kOhm NTC source
     * (board-l.mdx Knob mapping / Thermal derate). */
    ADC1->SMPR = (7u << ADC_SMPR_SMP1_Pos);

    ADC1->ISR = ADC_ISR_ADRDY;
    ADC1->CR |= ADC_CR_ADEN;
    while (!(ADC1->ISR & ADC_ISR_ADRDY)) {
    }
}

static uint32_t adc_read_once(void)
{
    ADC1->CR |= ADC_CR_ADSTART;
    while (!(ADC1->ISR & ADC_ISR_EOC)) {
    }
    return ADC1->DR;
}

/* Selects one channel, discards the first conversion after the switch, and
 * averages the rest. */
static uint32_t adc_read_avg(uint32_t channel, uint32_t samples)
{
    ADC1->ISR = ADC_ISR_CCRDY;
    ADC1->CHSELR = (1u << channel);
    while (!(ADC1->ISR & ADC_ISR_CCRDY)) {
    }

    (void)adc_read_once();
    uint32_t sum = 0;
    for (uint32_t i = 0; i < samples; i++) {
        sum += adc_read_once();
    }
    return sum / samples;
}

static uint32_t knob_to_perceptual(uint32_t code)
{
    int32_t c = (int32_t)code;
    if (c < KNOB_MIN_CODE) {
        c = KNOB_MIN_CODE;
    }
    if (c > KNOB_MAX_CODE) {
        c = KNOB_MAX_CODE;
    }
    uint32_t level = (uint32_t)(c - KNOB_MIN_CODE) * 255u / (uint32_t)(KNOB_MAX_CODE - KNOB_MIN_CODE);
    if (KNOB_INVERT) {
        level = 255u - level;
    }
    return level <= KNOB_OFF_LEVEL ? 0u : level;
}

/* Returns the perceptual ceiling allowed by temperature: 255 when cool, linear
 * roll-off between DERATE and CRITICAL, 0 at/over CRITICAL or with an open sensor. */
static uint32_t thermal_limit(uint32_t ntc_code)
{
    if (ntc_code >= NTC_OPEN_CODE || ntc_code <= NTC_CRITICAL_CODE) {
        return 0;
    }
    if (ntc_code >= NTC_DERATE_CODE) {
        return 255;
    }
    return (ntc_code - NTC_CRITICAL_CODE) * 255u / (NTC_DERATE_CODE - NTC_CRITICAL_CODE);
}

static uint32_t perceptual_to_duty_q16(uint32_t level)
{
    if (level == 0) {
        return 0;
    }
    uint32_t g = gamma_lut[level];
    return DUTY_FLOOR_Q16 + g * (DUTY_FULL_Q16 - DUTY_FLOOR_Q16) / 255u;
}

int main(void)
{
    clock_init();

    RCC->IOPENR |= RCC_IOPENR_GPIOAEN;
    RCC->APBENR1 |= RCC_APBENR1_TIM3EN | RCC_APBENR1_USART2EN;
    RCC->APBENR2 |= RCC_APBENR2_ADCEN;
    (void)RCC->APBENR2;

    pwm_init();
    uart_init();
    adc_init();
    gpio_set_input(5);   /* PA5 = PDOK, R24 pull-up */
    gpio_set_input(7);   /* PA7 = ATT,  R25 pull-up */

    uart_puts("\r\nzudo-led-lamp bring-up fw\r\n");

    uint32_t current = 0;
    uint32_t frame = 0;
    uint32_t next = ms_ticks;

    for (;;) {
        while ((int32_t)(ms_ticks - next) < 0) {
        }
        next += FRAME_MS;

        uint32_t knob = adc_read_avg(ADC_CH_KNOB, 8);
        uint32_t ntc = adc_read_avg(ADC_CH_NTC, 8);

        uint32_t target = knob_to_perceptual(knob);
        uint32_t limit = thermal_limit(ntc);
        if (target > limit) {
            target = limit;
        }

        if (current < target) {
            current = (target - current > RAMP_STEP) ? current + RAMP_STEP : target;
        } else if (current > target) {
            current = (current - target > RAMP_STEP) ? current - RAMP_STEP : target;
        }
        /* Over-temperature or open NTC cuts immediately instead of ramping. */
        if (limit == 0) {
            current = 0;
        }

        uint32_t duty = perceptual_to_duty_q16(current);
        pwm_set_duty_q16(duty);

        if (++frame >= 10) {   /* 5 Hz status line */
            frame = 0;
            uart_field("knob", knob);
            uart_field("ntc", ntc);
            uart_field("target", target);
            uart_field("level", current);
            uart_field("duty_pct10", duty * 1000u / 65536u);
            uart_field("pdok", (GPIOA->IDR >> 5) & 1u);
            uart_field("att", (GPIOA->IDR >> 7) & 1u);
            uart_puts("\r\n");
        }
    }
}
