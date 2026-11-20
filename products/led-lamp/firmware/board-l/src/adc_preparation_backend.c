#include "adc_preparation_backend.h"
#include <stddef.h>
#define REG UINT32_C(0x10000000)
#define CAL UINT32_C(0x80000000)
#define COMMANDS UINT32_C(0x80000017)
#define INTERLOCK UINT32_C(0x8c01)
#define CFGR_RESERVED UINT32_C(0x831e0200)
static bool failed(struct adc_preparation_adapter *a,enum adc_preparation_backend_error e,
 enum adc_operation op,enum adc_register_offset reg) {
 if(a->first_error==ADC_PREP_NO_ERROR){a->first_error=e;a->first_operation=op;a->first_register=reg;a->first_write_effect_possible=a->write_effect_possible;}
 return false;
}
static bool rd(struct adc_preparation_adapter *a,enum adc_operation op,enum adc_register_offset reg,uint32_t *out) {
 uint32_t raw=0;if(!a->transport.registers.read(a->transport.registers.context,reg,&raw))return failed(a,ADC_PREP_READ,op,reg);
 *out=raw;return true;
}
static bool wr(struct adc_preparation_adapter *a,enum adc_operation op,enum adc_register_offset reg,uint32_t v) {
 a->write_effect_possible=true;a->last_write_register=reg;a->last_write_value=v;
 if(!a->transport.registers.write(a->transport.registers.context,reg,v))return failed(a,ADC_PREP_WRITE,op,reg);
 return true;
}
static bool time_read(struct adc_preparation_adapter *a,enum adc_operation op,uint64_t *earliest,uint64_t *latest) {
 struct adc_time_evidence t={0};
 if(!a->transport.time(a->transport.registers.context,&t) || !t.valid || !t.qualified_monotonic || t.epoch!=a->epoch ||
    t.earliest_us>t.latest_us ||
    (a->time_started && t.earliest_us<a->last_time))return failed(a,ADC_PREP_TIME,op,ADC_REG_CR);
 *earliest=t.earliest_us;*latest=t.latest_us;a->last_time=t.earliest_us;return true;
}
bool adc_preparation_adapter_initialize(struct adc_preparation_adapter *a,const struct adc_preparation_transport *t,uint64_t epoch) {
 if(!a)return false;
 if(a->configured || a->first_error!=ADC_PREP_NO_ERROR)return failed(a,ADC_PREP_CONFIG,ADC_QUALIFIED_CLOCK_SUPPLY_RUN_AND_EXCLUSIVE_OWNER,ADC_REG_CR);
 if(!t || !epoch || !t->registers.evidence || !t->registers.read || !t->registers.write || !t->time)
  return failed(a,ADC_PREP_CONFIG,ADC_QUALIFIED_CLOCK_SUPPLY_RUN_AND_EXCLUSIVE_OWNER,ADC_REG_CR);
 a->transport=*t;a->epoch=epoch;a->configured=true;return true;
}
bool adc_preparation_adapter_initialize_operation(struct adc_preparation_adapter *a,
 const struct adc_preparation_transport *t,uint64_t epoch,const struct adc_operation_config *config) {
 struct adc_operation_descriptor d;
 if(!a)return false;
 if(!adc_operation_describe(config,&d))return failed(a,ADC_PREP_CONFIG,ADC_QUALIFIED_CLOCK_SUPPLY_RUN_AND_EXCLUSIVE_OWNER,ADC_REG_CFGR2);
 if(!adc_preparation_adapter_initialize(a,t,epoch))return false;
 a->operation_config=*config;a->operation_descriptor=d;a->operation_config_enabled=true;return true;
}
static bool operation_clock(struct adc_preparation_adapter *a,const struct adc_field_evidence *e) {
 const struct adc_operation_config *x=&a->operation_config,*y=&e->operation_clock_plan;
 return e->operation_clock_plan_qualified && e->operation_range1_qualified &&
 (x->clock_mode!=ADC_OPERATION_PCLK || e->operation_duty50_qualified) && y->bounds_supplied &&
 x->clock_mode==y->clock_mode && x->source_min_hz==y->source_min_hz && x->source_max_hz==y->source_max_hz;
}
static bool transact(void *ctx,enum adc_kind kind,enum adc_operation op,uint8_t factor,struct adc_reply *reply) {
 static const enum adc_kind kinds[]={ADC_OBSERVE,ADC_OBSERVE,ADC_ACTION,ADC_OBSERVE,ADC_ACTION,
 ADC_OBSERVE,ADC_OBSERVE,ADC_ACTION,ADC_OBSERVE,ADC_READ,ADC_OBSERVE,ADC_ACTION,ADC_ACTION,
 ADC_OBSERVE,ADC_OBSERVE,ADC_WRITE,ADC_VERIFY};
 struct adc_preparation_adapter *a=ctx;struct adc_field_evidence e={0};uint32_t cr=0,cfgr=0,cfgr2=0,raw=0;
 uint64_t now=0,latest=0;bool enabled_phase;
 if(reply)*reply=(struct adc_reply){0};
 if(!a || !reply)return false;
 if(a->first_error!=ADC_PREP_NO_ERROR)return false;
 if(!a->configured || (unsigned)op>=ADC_OPERATION_COUNT || kind!=kinds[op])return failed(a,ADC_PREP_REQUEST,op,ADC_REG_CR);
 if(!a->transport.registers.evidence(a->transport.registers.context,&e) || !e.valid || !e.exclusive_owner ||
    !e.clock_supply_qualified || e.ownership_epoch!=a->epoch)return failed(a,ADC_PREP_CONTEXT,op,ADC_REG_CR);
 if(a->operation_config_enabled && !operation_clock(a,&e))return failed(a,ADC_PREP_CONTEXT,op,ADC_REG_CFGR2);
 if(op==ADC_QUALIFIED_CLOCK_SUPPLY_RUN_AND_EXCLUSIVE_OWNER) {
  if(e.reset_channel_evidence_epoch!=a->epoch || !e.no_channel_update_inflight)return failed(a,ADC_PREP_CONTEXT,op,ADC_REG_CR);
  reply->valid=true;reply->met=true;return true;
 }
 if(!rd(a,op,ADC_REG_CR,&cr) || !rd(a,op,ADC_REG_CFGR1,&cfgr))return false;
 if(cr & ~(COMMANDS|REG))return failed(a,ADC_PREP_STATE,op,ADC_REG_CR);
 if(cfgr&CFGR_RESERVED)return failed(a,ADC_PREP_STATE,op,ADC_REG_CFGR1);
 if(a->operation_config_enabled) {
  if(!rd(a,op,ADC_REG_CFGR2,&cfgr2))return false;
  if(!adc_operation_cfgr2_valid(cfgr2))return failed(a,ADC_PREP_STATE,op,ADC_REG_CFGR2);
  if(op>=ADC_DISABLED_CONFIG_READBACK) {
   if((cfgr&a->operation_descriptor.cfgr1_mask)!=a->operation_descriptor.cfgr1_value)
    return failed(a,ADC_PREP_STATE,op,ADC_REG_CFGR1);
   if((cfgr2&a->operation_descriptor.cfgr2_mask)!=a->operation_descriptor.cfgr2_value)
    return failed(a,ADC_PREP_STATE,op,ADC_REG_CFGR2);
  }
 }
 enabled_phase=op>=ADC_ADRDY;
 /* No command is replayed: CR rs bits receive only the explicitly requested1. */
 if(enabled_phase) {
  if((cr&COMMANDS)!=1 || !(cr&REG))return failed(a,ADC_PREP_STATE,op,ADC_REG_CR);
 } else if(op==ADC_CALIBRATION_COMPLETE) {
  if((cr&(COMMANDS&~CAL)) || !(cr&REG))return failed(a,ADC_PREP_STATE,op,ADC_REG_CR);
 } else if(cr&COMMANDS)return failed(a,ADC_PREP_STATE,op,ADC_REG_CR);
 if(op>=ADC_DISABLED_CONFIG_READBACK && (cfgr&INTERLOCK))return failed(a,ADC_PREP_STATE,op,ADC_REG_CFGR1);
 if(op>=ADC_REGULATOR_STABLE_20US_ELAPSED && !(cr&REG))return failed(a,ADC_PREP_STATE,op,ADC_REG_CR);
 if(op==ADC_CONFIGURE_DISABLED_CALIBRATION_INTERLOCK) {
  if(!a->operation_config_enabled)return wr(a,op,ADC_REG_CFGR1,cfgr&~INTERLOCK);
  if(!e.no_channel_update_inflight)return failed(a,ADC_PREP_CONTEXT,op,ADC_REG_CFGR2);
  raw=(cfgr2&~a->operation_descriptor.cfgr2_mask)|a->operation_descriptor.cfgr2_value;
  if(!adc_operation_cfgr2_write_allowed(&a->operation_config,e.operation_range1_qualified,
   e.operation_duty50_qualified,cr,cfgr2,raw))return failed(a,ADC_PREP_STATE,op,ADC_REG_CFGR2);
  if(!wr(a,op,ADC_REG_CFGR1,(cfgr&~a->operation_descriptor.cfgr1_mask)|a->operation_descriptor.cfgr1_value))return false;
  return wr(a,op,ADC_REG_CFGR2,raw);
 }
 if(op==ADC_ENABLE_ADC_REGULATOR) {
  if(!wr(a,op,ADC_REG_CR,REG))return false;
  /* Timestamp AFTER successful action: conservative >=20us since this point. */
  if(!time_read(a,op,&now,&latest))return false;
  a->regulator_started=latest;a->time_started=true;return true;
 }
 if(op==ADC_REGULATOR_STABLE_20US_ELAPSED) {
  if(!a->time_started)return failed(a,ADC_PREP_TIME,op,ADC_REG_CR);
  if(!time_read(a,op,&now,&latest))return false;
  reply->valid=true;reply->met=now>=a->regulator_started && (now-a->regulator_started)>=20;
  if(reply->met)a->elapsed_qualified=true;
  return true;
 }
 if(op>=ADC_CALIBRATION_PRECONDITIONS && !a->elapsed_qualified)return failed(a,ADC_PREP_TIME,op,ADC_REG_CR);
 if(op==ADC_START_CALIBRATION) {
  if(!wr(a,op,ADC_REG_CR,REG|CAL))return false;
  a->calibration_started=true;return true;
 }
 if(op==ADC_CALIBRATION_COMPLETE) {
  if(!a->calibration_started)return failed(a,ADC_PREP_STATE,op,ADC_REG_CR);
  reply->valid=true;reply->met=!(cr&CAL);
  if(reply->met)a->calibration_completed=true;
  return true;
 }
 if(op>=ADC_RAW_CALFACT && !a->calibration_completed)return failed(a,ADC_PREP_STATE,op,ADC_REG_CR);
 if(op==ADC_RAW_CALFACT || op==ADC_CORRECTED_CALFACT_READBACK) {
  if(!rd(a,op,ADC_REG_CALFACT,&raw))return false;
  if(raw>127)return failed(a,ADC_PREP_STATE,op,ADC_REG_CALFACT);
  reply->valid=true;reply->value=(int32_t)raw;return true; /* never +1 here */
 }
 if(op==ADC_CLEAR_ADRDY_W1C)return wr(a,op,ADC_REG_ISR,1);
 if(op==ADC_ENABLE_NORMAL_ADC) {
  if(!rd(a,op,ADC_REG_ISR,&raw))return false;
  if(raw&1)return failed(a,ADC_PREP_STATE,op,ADC_REG_ISR);
  return wr(a,op,ADC_REG_CR,REG|1);
 }
 if(op==ADC_ADRDY) {
  if(!rd(a,op,ADC_REG_ISR,&raw))return false;
  reply->valid=true;reply->met=(raw&1)!=0;return true;
 }
 if(op==ADC_CORRECTED_CALFACT) {
  if(factor>127)return failed(a,ADC_PREP_REQUEST,op,ADC_REG_CALFACT);
  if(!rd(a,op,ADC_REG_CALFACT,&raw))return false;
  if(raw>127)return failed(a,ADC_PREP_STATE,op,ADC_REG_CALFACT);
  return wr(a,op,ADC_REG_CALFACT,factor);
 }
 reply->valid=true;reply->met=true;return true;
}
struct adc_backend adc_preparation_adapter_backend(struct adc_preparation_adapter *a) {
 struct adc_backend b={a,transact};return b;
}
