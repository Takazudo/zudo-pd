#include "adc_operation_config.h"
bool adc_operation_describe(const struct adc_operation_config *c,struct adc_operation_descriptor *d)
{
 uint32_t divisor,low,high;
 if(d)*d=(struct adc_operation_descriptor){0};
 if(!c || !d || !c->bounds_supplied || !c->source_min_hz || c->source_max_hz<c->source_min_hz ||
 c->clock_mode<ADC_OPERATION_ASYNC || c->clock_mode>ADC_OPERATION_PCLK)return false;
 if(c->clock_mode!=ADC_OPERATION_ASYNC && c->source_max_hz>64000000u)return false; /* DS Table21 PCLK */
 divisor=c->clock_mode==ADC_OPERATION_PCLK_DIV2?2u:c->clock_mode==ADC_OPERATION_PCLK_DIV4?4u:1u;
 low=c->source_min_hz/divisor;high=c->source_max_hz/divisor+(c->source_max_hz%divisor!=0);
 /* DS12992Rev4 Table59 Range1; no default clock or Range2 adoption. */
 if(low<140000u || high>35000000u)return false;
 *d=(struct adc_operation_descriptor){UINT32_C(0x0001fc03),UINT32_C(0x00010000),
 UINT32_C(0xe0000001),((uint32_t)c->clock_mode-1u)<<30|UINT32_C(0x20000000),low,high};
 return true;
}
bool adc_operation_cfgr2_valid(uint32_t value)
{
 return !(value&~UINT32_C(0xe00003fd)) && ((value>>5)&15u)<=8u;
}
bool adc_operation_cfgr2_write_allowed(const struct adc_operation_config *c,bool range1,bool duty50,
 uint32_t cr,uint32_t previous,uint32_t requested)
{
 struct adc_operation_descriptor d;
 if(!adc_operation_describe(c,&d) || !range1 || (c->clock_mode==ADC_OPERATION_PCLK && !duty50) ||
 (cr&~UINT32_C(0x10000000)) || !adc_operation_cfgr2_valid(previous) || !adc_operation_cfgr2_valid(requested))return false;
 return (requested&d.cfgr2_mask)==d.cfgr2_value &&
 (requested&~d.cfgr2_mask)==(previous&~d.cfgr2_mask);
}
