#ifndef BOARD_IWDG_H
#define BOARD_IWDG_H
#include <stdbool.h>
/* Starts the IWDG at the proposed ~100 ms (board_l_proposal.h). Returns false if
 * the prescaler/reload update did not complete; the watchdog may still be running. */
bool board_iwdg_start(void);
/* Main loop only, after a completed lamp_app_tick. Never from an ISR. */
void board_iwdg_refresh(void);
#endif
