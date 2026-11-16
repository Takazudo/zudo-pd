#include "board_iwdg.h"
#include "board_l_proposal.h"
#include "stm32g031_regs.h"

#define IWDG_SPIN_LIMIT 200000u

/* Sequence as in ST LL (LL_IWDG_Enable, EnableWriteAccess, SetPrescaler,
 * SetReloadCounter, IsReady, ReloadCounter). Enabling the IWDG also starts the LSI
 * per ST's documentation [RM, not retained]. */
bool board_iwdg_start(void)
{
#ifndef BOARD_L_PRODUCTION
    /* Development: freeze the IWDG while a debugger halts the core. */
    RCC_APBENR1 |= RCC_APBENR1_DBGEN_BIT;
    (void)RCC_APBENR1;
    DBG_APBFZ1 |= DBG_APB_FZ1_IWDG_STOP_BIT;
#endif
    IWDG_KR = IWDG_KEY_ENABLE;
    IWDG_KR = IWDG_KEY_WR_ACCESS;
    IWDG_PR = IWDG_PRESCALER_FIELD;
    IWDG_RLR = IWDG_RELOAD_FIELD;
    for (uint32_t i = 0; i < IWDG_SPIN_LIMIT; i++) {
        if ((IWDG_SR & (IWDG_SR_PVU_BIT | IWDG_SR_RVU_BIT | IWDG_SR_WVU_BIT)) == 0u) {
            IWDG_KR = IWDG_KEY_RELOAD;
            return true;
        }
    }
    return false;
}

void board_iwdg_refresh(void)
{
    IWDG_KR = IWDG_KEY_RELOAD;
}
