/* Board L target: V72 lamp_app drives CTRL through lamp_target.c, fed by the ADC
 * sample source (board_samples.c -> V72 sample_adapter). OFF by default: any refusal
 * of the boot policy, clock, watchdog, ADC or sample setup keeps CTRL low.
 * PROPOSAL only; never flashed or run. */
#include <stdint.h>
#include "board_adc.h"
#include "board_ctrl.h"
#include "board_iwdg.h"
#include "board_l_proposal.h"
#include "board_policy.h"
#include "board_samples.h"
#include "clock.h"
#include "lamp_target.h"
#include "stm32g031_regs.h"

#define TICK_HZ 1000u

static volatile uint32_t g_ticks;
static uint32_t g_ticks_seen;
static uint64_t g_ticks64;
static struct lamp_target g_target;
static struct board_samples g_samples;
static struct lamp_app g_app;
/* Not cleared by Reset_Handler (.noinit): the reset-cause latch record. */
__attribute__((section(".noinit"))) struct reset_record g_reset_record;
/* Debugger-readable diagnostics. */
volatile enum clock_result g_clock_result;
volatile struct boot_decision g_boot_decision;
volatile uint32_t g_reset_csr, g_optr;
volatile struct lamp_app_report g_last_report;

void SysTick_Handler(void)
{
    g_ticks++;
}

static int systick_start(uint32_t hclk_hz)
{
    uint32_t reload = hclk_hz / TICK_HZ;
    if (reload == 0u || reload - 1u > SYST_RVR_MAX)
        return 0;
    SYST_RVR = reload - 1u;
    SYST_CVR = 0u;
    SYST_CSR = SYST_CSR_CLKSOURCE | SYST_CSR_TICKINT | SYST_CSR_ENABLE;
    return 1;
}

static void delay_ms(uint32_t ms)
{
    uint32_t start = g_ticks;
    while ((uint32_t)(g_ticks - start) <= ms) {
    }
}

/* 64-bit extension of the 1 kHz tick: sample_adapter faults on clock rollback. */
static uint64_t ticks_now(void *ctx)
{
    (void)ctx;
    uint32_t t = g_ticks;
    g_ticks64 += (uint32_t)(t - g_ticks_seen);
    g_ticks_seen = t;
    return g_ticks64;
}

/* Unexpected failure: OFF and no watchdog refresh, so the IWDG resets and the
 * reset-cause latch counts it. */
static void halt_off(void)
{
    for (;;)
        board_ctrl_force_off();
}

/* Deliberate refusal (latch, option bytes): stable OFF, diagnostics readable. The
 * uptime still marks a long run, so a later power cycle can clear a latch. */
static void park_off(void)
{
    uint32_t start;
    (void)systick_start(clock_hclk_hz(g_clock_result));
    start = g_ticks;
    for (;;) {
        board_ctrl_force_off();
        board_iwdg_refresh();
        reset_record_note_uptime(&g_reset_record, g_ticks - start, false);
    }
}

int main(void)
{
    static const struct ctrl_port port = {board_ctrl_force_off, board_ctrl_pwm_init_zero,
                                          board_ctrl_write_ccr};
    static const struct sample_port samples = {&g_samples, board_samples_read,
                                               board_samples_read_graded};
    static const struct raw_source source = {NULL, board_adc_convert, ticks_now};
    static const struct board_l_config cfg = {{true, CTRL_TIMER_EDGE_UP_PWM1_ACTIVE_HIGH,
        CTRL_PERIOD_TICKS, true, CTRL_MIN_CCR, CTRL_FULL_CCR}};
    const struct lamp_config policy = {LAMP_RAMP_INCREMENT, LAMP_RECOVERY_LATCH};
    const struct lamp_app_gain_path gain = lamp_target_gain_path();
    struct lamp_app_io io;
    struct boot_decision d;

    board_ctrl_force_off();                          /* 1. CTRL defined low (GPIO)   */
    g_reset_csr = RCC_CSR;                           /* 2. reset cause, then clear   */
    RCC_CSR |= RCC_CSR_RMVF_BIT;
    g_optr = FLASH_OPTR;
    if (!board_iwdg_start())                         /* 3. watchdog before anything  */
        halt_off();
    g_clock_result = clock_init_64mhz();             /* 4. 64 MHz or refuse          */
    d = boot_decide(&g_reset_record, g_reset_csr, g_optr, g_clock_result == CLOCK_PLL_64MHZ);
    g_boot_decision = d;
    switch (boot_action_for(&d)) {                   /*    latch first: parks OFF     */
    case BOOT_RUN:
        break;
    case BOOT_HALT_OFF:                              /*    clock: counted-reset retry */
        halt_off();
        break;
    default:
        park_off();
        break;
    }
    if (!systick_start(clock_hclk_hz(g_clock_result)))
        halt_off();
    if (!board_adc_init(delay_ms))                   /* 5. sample source             */
        halt_off();
    (void)ticks_now(NULL);
    if (board_samples_init(&g_samples, &source) != BOARD_L_OK)
        halt_off();
    if (!lamp_target_bind(&g_target, &port, &samples))
        halt_off();
    io = lamp_target_io(&g_target);
    g_last_report = lamp_app_initialize_with_thermal_gain(&g_app, &io, &cfg, NULL, &gain);
    if (g_last_report.status != LAMP_APP_CORE_OFF)          /* initialized, OFF */
        halt_off();

    uint32_t seen = g_ticks, start = g_ticks;
    for (;;) {
        __asm volatile("wfi");
        if (g_ticks != seen) {
            seen = g_ticks;
            g_last_report = lamp_app_tick(&g_app, &policy); /* 6. every tick re-applies */
            board_iwdg_refresh();                           /*    main loop only         */
            reset_record_note_uptime(&g_reset_record, seen - start, true); /* consecutive */
        }
    }
}
