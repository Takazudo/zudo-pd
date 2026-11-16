#include "tim3_profile.h"
bool tim3_profile_config_valid(const struct tim3_preload_config *c)
{
 uint32_t cr,sm,ccmr,ccer,dier,ts;
 if(!c || !c->qualified || !c->epoch || c->period_ticks<2 || c->period_ticks>65536)return false;
 cr=c->expected_cr1;sm=c->expected_smcr;ccmr=c->expected_ccmr1;
 ccer=c->expected_ccer;dier=c->expected_dier;
 /* RM pp662-663: legal CR1; ARPE1, edge/up, OPM0, UDIS0.
  * CEN and URS are caller-specified observations, never changed here. */
 if((cr&~UINT32_C(0x0bff)) || (cr&0x300u)==0x300u || (cr&0xfau)!=0x80u)return false;
 /* RM pp665-668: SMS=0/ECE=0, defined SMCR bits and TS encodings. */
 ts=((sm>>4)&7u)|((sm>>17)&24u);
 if((sm&~UINT32_C(0x0031ffff)) || (sm&0x00014007u) || ts>12)return false;
 /* RM pp668-669: defined DIER bits, no timer DMA requests. IRQ handling
  * must separately be excluded from mutating state by held-scope proof. */
 if((dier&~UINT32_C(0x5f5f)) || (dier&0x5f00u))return false;
 /* RM pp674-676: CH1 output/PWM1(OC1M[3]=0)/PE1/FE0/CE0.
  * CH2 stays untouched, but high OC2M bit is reserved in input mode. */
 if((ccmr&~UINT32_C(0x0101ffff)) || (ccmr&0x100ffu)!=0x68u ||
 ((ccmr&0x300u) && (ccmr&0x01000000u)))return false;
 /* RM pp678-679: valid CCER bits, CH1 active-high/NP0. CC1E explicit. */
 if((ccer&~UINT32_C(0xbbbb)) || (ccer&0xau))return false;
 if(c->positive_limits_qualified && (!c->positive_min || c->positive_min>c->positive_max ||
 c->positive_max>c->period_ticks))return false;
 return true;
}
bool tim3_profile_expected(const struct tim3_preload_config *c,enum tim3_preload_register reg,uint32_t *out)
{
 if(out)*out=0;
 if(!out || !tim3_profile_config_valid(c) || (unsigned)reg>=TP_CCR1)return false;
 switch(reg){
 case TP_CR1:*out=c->expected_cr1;break;
 case TP_SMCR:*out=c->expected_smcr;break;
 case TP_DIER:*out=c->expected_dier;break;
 case TP_CCMR1:*out=c->expected_ccmr1;break;
 case TP_CCER:*out=c->expected_ccer;break;
 case TP_PSC:*out=c->psc;break;
 case TP_ARR:*out=c->period_ticks-1u;break;
 default:return false;
 }
 return true;
}
