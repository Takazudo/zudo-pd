#include "adc_preparation.h"
#include <stddef.h>
static const enum adc_kind kinds[]={ADC_OBSERVE,ADC_OBSERVE,ADC_ACTION,ADC_OBSERVE,ADC_ACTION,ADC_OBSERVE,ADC_OBSERVE,ADC_ACTION,ADC_OBSERVE,ADC_READ,ADC_OBSERVE,ADC_ACTION,ADC_ACTION,ADC_OBSERVE,ADC_OBSERVE,ADC_WRITE,ADC_VERIFY};
static const char *names[]={"qualified_clock_supply_run_and_exclusive_owner","disabled_idle_no_pending_commands","configure_disabled_calibration_interlock","disabled_config_readback","enable_adc_regulator","regulator_stable_20us_elapsed","calibration_preconditions","start_calibration","calibration_complete","raw_calfact","enable_preconditions","clear_adrdy_w1c","enable_normal_adc","adrdy","aden_set_adstart_clear_interlock_held","corrected_calfact","corrected_calfact_readback"};
const char *adc_operation_name(enum adc_operation op) {
 return (unsigned)op<ADC_OPERATION_COUNT ? names[op] : "invalid";
}
static enum adc_status fail(struct adc_preparation *s, enum adc_error e) {
 if(s->first_error==ADC_NO_ERROR)s->first_error=e;
 s->status=ADC_FAILED;s->factor=0;s->factor_valid=false;
 s->prepared=false;s->sample_ready=false;s->software_inhibited=true;
 return s->status;
}
enum adc_status adc_begin(struct adc_preparation *s,const struct adc_backend *b,const struct adc_qualification *q) {
 if(!s)return ADC_FAILED;
 if(s->status!=ADC_NEW) {
  s->restart_refused=true;
  if(s->status==ADC_FAILED)return s->status;
  return fail(s,ADC_RESTART_REFUSED);
 }
 s->software_inhibited=true;
 if(!b || !q || !b->transact || !q->observation_budget || q->observation_budget>1000000 ||
    !q->clock_supply_run_qualified || !q->exclusive_owner || !q->temporary_normal_enable)
  return fail(s,ADC_CONFIG_ERROR);
 s->backend=*b;s->qualification=*q;s->status=ADC_RUNNING;return s->status;
}
enum adc_status adc_advance(struct adc_preparation *s) {
 struct adc_reply r={0};enum adc_kind k;uint8_t input=0;
 if(!s)return ADC_FAILED;
 if(s->status!=ADC_RUNNING)return s->status;
 k=kinds[s->step];
 if(k==ADC_WRITE || k==ADC_VERIFY)input=s->factor;
 if(!s->backend.transact(s->backend.context,k,(enum adc_operation)s->step,input,&r))
  return fail(s,ADC_BACKEND_ERROR);
 if(k==ADC_OBSERVE) {
  ++s->observations;
  if(!r.valid)return fail(s,ADC_INVALID_OBSERVATION);
  if(!r.met) {
   if(s->observations>=s->qualification.observation_budget)return fail(s,ADC_WAIT_LIMIT);
   return s->status;
  }
 } else if(k==ADC_READ) {
  if(!r.valid || r.value<0 || r.value>127)return fail(s,ADC_INVALID_FACTOR);
  s->factor=(uint8_t)(r.value<127 ? r.value+1 : 127);s->factor_valid=true;
 } else if(k==ADC_VERIFY) {
  if(!r.valid || r.value!=s->factor)return fail(s,ADC_READBACK_MISMATCH);
 }
 ++s->step;s->observations=0;
 if(s->step==ADC_OPERATION_COUNT) {s->status=ADC_PREPARED_TRIGGER_UNQUALIFIED;s->prepared=true;}
 return s->status;
}

enum adc_status adc_abort_channel_configuration(struct adc_preparation *s) {
 if(!s)return ADC_FAILED;
 if(s->status==ADC_FAILED)return s->status;
 return fail(s,ADC_CHANNEL_CONFIG_FAILURE);
}
