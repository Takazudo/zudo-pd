#include "tim3_access.h"
/* TARGET SOURCE ONLY. Never link/run this TU in HOST RAM checks. No caller
 * address/width; mapping is fixed pure code. No init/qualification/probing. */
static enum board_l_result fixed_read(void *ctx,enum tim3_preload_register reg,uint32_t *out)
{
 struct tim3_access_location l;(void)ctx;
 if(out)*out=0;
 if(!out || !tim3_access_location(reg,&l) || l.address%l.width)return BOARD_L_UNCONFIGURED;
 if(l.width==2)*out=*(volatile const uint16_t *)(uintptr_t)l.address;
 else if(l.width==4)*out=*(volatile const uint32_t *)(uintptr_t)l.address;
 else return BOARD_L_UNCONFIGURED;
 return BOARD_L_OK;
}
static enum board_l_result fixed_write(void *ctx,uint16_t value)
{
 (void)ctx;
 /* RM Table6 p66: TIM3=0x40000400; CCR1 offset0x34 pp681-682.
  * Halfword access permitted p662; never touches upper half or other regs. */
 *(volatile uint16_t *)(uintptr_t)UINT32_C(0x40000434)=value;
 return BOARD_L_OK; /* completed C store, not bus/active-shadow/pin/OFF proof */
}
struct tim3_access_seam tim3_fixed_volatile_seam(void)
{
 struct tim3_access_seam s={0,fixed_read,fixed_write};return s;
}
