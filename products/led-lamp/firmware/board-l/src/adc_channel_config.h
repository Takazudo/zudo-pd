#ifndef ADC_CHANNEL_CONFIG_H
#define ADC_CHANNEL_CONFIG_H
#include "adc_preparation.h"
/* Zero means UNSPECIFIED, never a selected hardware default. */
enum adc_channel_mode {ADC_CHANNEL_UNSELECTED, ADC_CHANNEL_BITMAP, ADC_CHANNEL_SEQUENCED};
enum adc_channel_order {ADC_ORDER_UNSELECTED, ADC_KNOB_THEN_NTC, ADC_NTC_THEN_KNOB};
enum adc_alignment {ADC_ALIGNMENT_UNSELECTED, ADC_ALIGN_RIGHT, ADC_ALIGN_LEFT};
struct adc_channel_choice {
 enum adc_channel_mode mode;
 enum adc_channel_order order;
 enum adc_alignment alignment;
 unsigned resolution_bits, knob_channel, ntc_channel;
 unsigned knob_sample_group, ntc_sample_group; /* explicit 1 or 2 */
 unsigned sampling_cycles_times_two; /* only decided 321 = 160.5 cycles */
};
struct adc_masked_field {uint32_t mask,value;};
struct adc_channel_descriptor {
 struct adc_masked_field cfgr1, smpr, chselr;
 uint32_t cr_idle_zero_mask, ccrdy_mask;
 bool require_disabled_idle, require_ccrdy_between_channel_changes;
 bool require_final_ccrdy_and_readback;
 bool sample_permission; /* always false */
 enum adc_status preparation_status; /* actual binding.adc snapshot only */
};
enum adc_channel_result {ADC_CHANNEL_VALID_DESCRIPTOR,ADC_CHANNEL_UNQUALIFIED,ADC_CHANNEL_UNSUPPORTED};
/* Pure encoding. No registers read/written. Output cleared on failure.
   descriptor validity never modifies preparation or grants sample readiness.
   Pass &binding.adc to tie the snapshot to actual lifecycle. */
enum adc_channel_result adc_channel_describe(const struct adc_channel_choice *,
 const struct adc_preparation *,struct adc_channel_descriptor *);
/* Pure masked merge for these ordinary RW fields only, never ADC_ISR W1C.
   Caller must validate reserved bits/current mode; not a register writer. */
uint32_t adc_channel_merge(uint32_t,struct adc_masked_field);
#endif
