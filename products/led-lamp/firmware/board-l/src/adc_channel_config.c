#include "adc_channel_config.h"
#include <stddef.h>
uint32_t adc_channel_merge(uint32_t old,struct adc_masked_field f) {
 return (old & ~f.mask) | (f.value & f.mask);
}
enum adc_channel_result adc_channel_describe(const struct adc_channel_choice *c,
 const struct adc_preparation *preparation,struct adc_channel_descriptor *d) {
 unsigned first,second;
 if(!d)return ADC_CHANNEL_UNSUPPORTED;
 *d=(struct adc_channel_descriptor){0};
 if(!c || !preparation)return ADC_CHANNEL_UNQUALIFIED;
 if(c->mode==ADC_CHANNEL_UNSELECTED || c->order==ADC_ORDER_UNSELECTED ||
    c->alignment==ADC_ALIGNMENT_UNSELECTED || !c->knob_sample_group || !c->ntc_sample_group)
  return ADC_CHANNEL_UNQUALIFIED;
 if((c->mode!=ADC_CHANNEL_BITMAP && c->mode!=ADC_CHANNEL_SEQUENCED) ||
    (c->order!=ADC_KNOB_THEN_NTC && c->order!=ADC_NTC_THEN_KNOB) ||
    (c->alignment!=ADC_ALIGN_RIGHT && c->alignment!=ADC_ALIGN_LEFT) ||
    c->resolution_bits!=12 || c->knob_channel!=0 || c->ntc_channel!=4 ||
    c->sampling_cycles_times_two!=321 || c->knob_sample_group>2 || c->ntc_sample_group>2 ||
    (unsigned)preparation->status>ADC_FAILED)
  return ADC_CHANNEL_UNSUPPORTED;
 /* CFGR1 RES[4:3]=00, ALIGN5 caller-selected, CHSELRMOD21. */
 d->cfgr1.mask=UINT32_C(0x00200038);
 d->cfgr1.value=c->alignment==ADC_ALIGN_LEFT ? UINT32_C(0x20) : 0;
 if(c->mode==ADC_CHANNEL_BITMAP) {
  d->cfgr1.mask|=UINT32_C(4); /* SCANDIR2: CH0->CH4 or CH4->CH0 */
  if(c->order==ADC_NTC_THEN_KNOB)d->cfgr1.value|=UINT32_C(4);
  d->chselr=(struct adc_masked_field){UINT32_C(0x0007ffff),UINT32_C(0x11)};
 } else {
  d->cfgr1.value|=UINT32_C(0x00200000); /* SCANDIR ignored/preserved */
  first=c->order==ADC_KNOB_THEN_NTC ? 0 : 4;second=4-first;
  /* SQ1/SQ2 chosen channels, SQ3=15 terminates. SQ4..8 ignored/preserved. */
  d->chselr=(struct adc_masked_field){UINT32_C(0xfff),UINT32_C(0xf00)|(second<<4)|first};
 }
 /* SMPSEL0 bit8, SMPSEL4 bit12; selected shared groups set to111. */
 d->smpr.mask=UINT32_C(0x1100);
 if(c->knob_sample_group==2)d->smpr.value|=UINT32_C(0x100);
 if(c->ntc_sample_group==2)d->smpr.value|=UINT32_C(0x1000);
 if(c->knob_sample_group==1 || c->ntc_sample_group==1) {
  d->smpr.mask|=UINT32_C(7);d->smpr.value|=UINT32_C(7);
 }
 if(c->knob_sample_group==2 || c->ntc_sample_group==2) {
  d->smpr.mask|=UINT32_C(0x70);d->smpr.value|=UINT32_C(0x70);
 }
 /* ADC_CR ADCAL31, ADSTP4, ADSTART2, ADDIS1, ADEN0 must be zero. */
 d->cr_idle_zero_mask=UINT32_C(0x80000017);
 d->ccrdy_mask=UINT32_C(0x2000); /* ADC_ISR13 W1C: never RMW */
 d->require_disabled_idle=true;d->require_ccrdy_between_channel_changes=true;
 d->require_final_ccrdy_and_readback=true;
 d->preparation_status=preparation->status;
 return ADC_CHANNEL_VALID_DESCRIPTOR;
}
