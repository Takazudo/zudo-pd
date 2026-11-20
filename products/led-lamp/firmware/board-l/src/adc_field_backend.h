#ifndef ADC_FIELD_BACKEND_H
#define ADC_FIELD_BACKEND_H
#include "board_binding.h"
#include "adc_operation_config.h"
enum adc_register_offset {ADC_REG_ISR=0x00,ADC_REG_CR=0x08,ADC_REG_CFGR1=0x0c,
 ADC_REG_CFGR2=0x10,ADC_REG_SMPR=0x14,ADC_REG_CHSELR=0x28,ADC_REG_CALFACT=0xb4};
struct adc_field_evidence {
 uint64_t ownership_epoch, reset_channel_evidence_epoch;
 bool valid, exclusive_owner, clock_supply_qualified, no_channel_update_inflight;
 /* Independent permission for selected target ADC mode/source bounds, not a
  * claim CFGR2 is already programmed. Covers stable source/Range1/held action. */
 struct adc_operation_config operation_clock_plan;
 bool operation_clock_plan_qualified,operation_range1_qualified,operation_duty50_qualified;
};
struct adc_field_transport {
 void *context;
 bool (*evidence)(void *,struct adc_field_evidence *);
 bool (*read)(void *,enum adc_register_offset,uint32_t *);
 bool (*write)(void *,enum adc_register_offset,uint32_t);
};
enum adc_field_backend_error {ADC_FIELD_NO_ERROR,ADC_FIELD_BAD_CONFIG,ADC_FIELD_EVIDENCE,
 ADC_FIELD_READ_ERROR,ADC_FIELD_WRITE_ERROR,ADC_FIELD_GUARD,ADC_FIELD_RESERVED,
 ADC_FIELD_BASELINE_ERROR,ADC_FIELD_REQUEST};
struct adc_field_adapter {
 struct adc_field_transport transport;
 struct adc_channel_descriptor descriptor;
 uint64_t epoch;
 bool configured, baseline_verified;
 enum adc_field_backend_error first_error;
 enum lamp_adc_field_operation first_operation;
 enum adc_register_offset first_register;
};
/* Zero initialize; immutable one-epoch adapter. No rearm/reset function or recovery
   policy. Evidence callback supplies actual externally qualified ownership/reset
   provenance, NEVER inferred from CCRDY0. No context grants sample permission. */
bool adc_field_adapter_initialize(struct adc_field_adapter *,const struct adc_field_transport *,
 uint64_t,const struct adc_channel_choice *);
struct lamp_adc_field_backend adc_field_adapter_backend(struct adc_field_adapter *);
#endif
