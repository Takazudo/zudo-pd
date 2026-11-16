#ifndef BOARD_CTRL_H
#define BOARD_CTRL_H
#include <stdint.h>
/* Board L CTRL output: PA6 (TSSOP20 pin 13) -> PWM_DIM -> R20 10k -> CTRL, with
 * R21 33k and C21 100nF to GND (scripts/schgen/board_l_spec.py). The external
 * pull-down network is the primary OFF guarantee; firmware must never glitch it. */
void board_ctrl_force_off(void);
void board_ctrl_pwm_init_zero(uint32_t period_ticks);
void board_ctrl_write_ccr(uint32_t ccr);
#endif
