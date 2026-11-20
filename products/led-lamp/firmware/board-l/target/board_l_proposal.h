#ifndef BOARD_L_PROPOSAL_H
#define BOARD_L_PROPOSAL_H
/* PROPOSED values only (firmware/board-l/target/PROPOSAL-CTRL-RESET-OPTIONS.md).
 * None is a user-approved product parameter. */
#include "lamp_target.h"

/* 20 kHz CTRL carrier at 64 MHz: ARR+1 = 3200. Requires the 64 MHz clock; main.c
 * refuses to start the lamp on the HSI fallback. */
#define CTRL_PERIOD_TICKS 3200u
/* 16.2 % duty -> 0.41 V CTRL nominal -> ~5 % of I_NOM (typical transfer). */
#define CTRL_MIN_CCR 518u

/* The ONE output-duty ceiling. Default 2407/3200 = 75.2 % keeps an unchanged
 * RS1 = 200 mOhm board at <= 81 mA hot-branch peak under the #52 h = 30 % / ballast
 * +-2 % case (candidates/board-l-led-margin-52, ctrl_ceiling_rs200_hys30_rb2). It relies
 * on the TYPICAL CTRL transfer, so it is defence in depth, not a guarantee.
 * Override (-DCTRL_FULL_CCR=3200) only after RS1 = 250 mOhm is measured on that board. */
#ifndef CTRL_FULL_CCR
#define CTRL_FULL_CCR 2407u
#endif
_Static_assert(CTRL_FULL_CCR > CTRL_MIN_CCR && CTRL_FULL_CCR <= CTRL_PERIOD_TICKS,
               "CTRL_FULL_CCR must lie in (CTRL_MIN_CCR, CTRL_PERIOD_TICKS]");

/* 1 kHz tick: zero to full in about 2.5 s (65536 / 26 = 2521 ticks), the ramp time of
 * the owner's 2026-10-06 bring-up firmware (../../board-l-bringup-mac-20261006). */
#define LAMP_RAMP_INCREMENT 26u

/* Reset-cause latch: this many CONSECUTIVE abnormal resets (watchdog, software,
 * low-power, or a BOR/dip that recurs before a healthy run) keep the lamp OFF. A
 * healthy run of RESET_HEALTHY_TICKS in normal operation clears the count. A latched
 * board clears only by a power cycle: off long enough to lose SRAM ([DS]), or after it
 * has been parked for RESET_HEALTHY_TICKS. 10 s is longer than the 2.5 s ramp, so a
 * sag-on-ramp loop counts. */
#define RESET_LATCH_COUNT 3u
#define RESET_HEALTHY_TICKS 10000u

/* IWDG: LSI 32 kHz TYPICAL (ST LL LSI_VALUE) / 32 = 1 kHz, 100 counts -> ~100 ms.
 * LSI tolerance and the exact counter period are [DS/RM], not retained. */
#define IWDG_PRESCALER_FIELD 3u   /* LL_IWDG_PRESCALER_32 */
#define IWDG_RELOAD_FIELD 99u

/* Option bytes required before any light (FLASH_OPTR, ST stm32g031xx.h fields):
 * BOR_EN = 1 with both BOR level fields at 3 ("around 2.8 V" falling / 2.9 V rising,
 * ST HAL OB_BOR_LEVEL_*_3 comments). Thresholds are [DS]. */
#define OPTION_BOR_LEVEL_FIELD 3u

/* Last-line check at the register write, independent of the RAM copy of the
 * mapper config: anything above the compile-time ceiling is refused (forced OFF). */
static inline bool ctrl_ccr_within_ceiling(uint32_t ccr)
{
    return ccr <= CTRL_FULL_CCR;
}

static inline struct board_l_config board_l_proposed_config(uint32_t full_ccr)
{
    return (struct board_l_config){{true, CTRL_TIMER_EDGE_UP_PWM1_ACTIVE_HIGH, CTRL_PERIOD_TICKS,
                                    true, CTRL_MIN_CCR, full_ccr}};
}
#endif
