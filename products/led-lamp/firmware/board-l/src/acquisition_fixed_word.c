#include "acquisition_fixed_word.h"
#include <limits.h>
#if !defined(__arm__) || !defined(__ARM_ARCH_6M__)
#error "Target-only volatile ADC source; do not compile/link/run in HOST tests"
#endif
_Static_assert(CHAR_BIT==8 && sizeof(uint32_t)==4,"32bit word required");
_Static_assert(UINTPTR_MAX>=UINT32_C(0x40012440),"ADC address representation");
static enum board_l_result fixed_read(void *ctx,enum acquisition_register reg,uint32_t *out)
{
 struct acquisition_location location;(void)ctx;
 if(out)*out=0;
 if(!out || !acquisition_word_read_location(reg,&location))return BOARD_L_UNCONFIGURED;
 *out=*(volatile const uint32_t *)(uintptr_t)location.address;
 return BOARD_L_OK;
}
static enum board_l_result fixed_store(void *ctx,enum acquisition_store operation,uint32_t value)
{
 struct acquisition_location location;(void)ctx;
 if(!acquisition_word_store_location(operation,value,&location))return BOARD_L_UNCONFIGURED;
 *(volatile uint32_t *)(uintptr_t)location.address=value;
 return BOARD_L_OK; /* reached C store, not bus/active-state acknowledgment */
}
struct acquisition_register_transport acquisition_fixed_word_transport(void)
{
 struct acquisition_register_transport transport={0,fixed_read,fixed_store};return transport;
}
