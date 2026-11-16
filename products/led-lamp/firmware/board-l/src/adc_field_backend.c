#include "adc_field_backend.h"
#include <stddef.h>
#define CR_IDLE UINT32_C(0x80000017)
#define CFGR_INTERLOCK UINT32_C(0x00008c01)
#define CFGR_RESERVED UINT32_C(0x831e0200)
#define SMPR_RESERVED UINT32_C(0xf8000088)
static bool failure(struct adc_field_adapter *a,enum adc_field_backend_error e,
 enum lamp_adc_field_operation op,enum adc_register_offset reg) {
 if(a->first_error==ADC_FIELD_NO_ERROR){a->first_error=e;a->first_operation=op;a->first_register=reg;}
 return false;
}
static bool read_reg(struct adc_field_adapter *a,enum lamp_adc_field_operation op,
 enum adc_register_offset reg,uint32_t *v) {
 uint32_t raw=0;
 if(!a->transport.read(a->transport.context,reg,&raw))return failure(a,ADC_FIELD_READ_ERROR,op,reg);
 *v=raw;return true;
}
static bool write_reg(struct adc_field_adapter *a,enum lamp_adc_field_operation op,
 enum adc_register_offset reg,uint32_t v) {
 if(!a->transport.write(a->transport.context,reg,v))return failure(a,ADC_FIELD_WRITE_ERROR,op,reg);
 return true;
}
bool adc_field_adapter_initialize(struct adc_field_adapter *a,const struct adc_field_transport *t,
 uint64_t epoch,const struct adc_channel_choice *c) {
 struct adc_preparation empty={0};struct adc_channel_descriptor descriptor;
 if(!a)return false;
 if(a->configured || a->first_error!=ADC_FIELD_NO_ERROR)
  return failure(a,ADC_FIELD_BAD_CONFIG,LAMP_ADC_BASELINE,ADC_REG_CR);
 if(!t || !t->evidence || !t->read || !t->write || !epoch ||
    adc_channel_describe(c,&empty,&descriptor)!=ADC_CHANNEL_VALID_DESCRIPTOR)
  return failure(a,ADC_FIELD_BAD_CONFIG,LAMP_ADC_BASELINE,ADC_REG_CR);
 a->transport=*t;a->descriptor=descriptor;a->epoch=epoch;a->configured=true;return true;
}
static bool transaction(void *ctx,enum lamp_adc_field_operation op,
 const struct adc_masked_field *request,struct adc_reply *reply) {
 struct adc_field_adapter *a=ctx;struct adc_field_evidence evidence={0};
 struct adc_masked_field expected={0};uint32_t cr=0,cfgr=0,raw=0;
 enum adc_register_offset reg=ADC_REG_CR;bool writing=false,reading=false;
 if(reply)*reply=(struct adc_reply){0};
 if(!a || !reply)return false;
 if(a->first_error!=ADC_FIELD_NO_ERROR)return false;
 if(!a->configured || !request || (unsigned)op>=LAMP_ADC_FIELD_COUNT)
  return failure(a,ADC_FIELD_REQUEST,op,reg);
 if(op!=LAMP_ADC_BASELINE && !a->baseline_verified)
  return failure(a,ADC_FIELD_BASELINE_ERROR,op,reg);
 if(!a->transport.evidence(a->transport.context,&evidence) || !evidence.valid ||
    evidence.ownership_epoch!=a->epoch || !evidence.exclusive_owner || !evidence.clock_supply_qualified)
  return failure(a,ADC_FIELD_EVIDENCE,op,reg);
 if(!read_reg(a,op,ADC_REG_CR,&cr) || !read_reg(a,op,ADC_REG_CFGR1,&cfgr))return false;
 if(cr&CR_IDLE)return failure(a,ADC_FIELD_GUARD,op,ADC_REG_CR);
 if(cfgr&CFGR_INTERLOCK)return failure(a,ADC_FIELD_GUARD,op,ADC_REG_CFGR1);
 if(cfgr&CFGR_RESERVED)return failure(a,ADC_FIELD_RESERVED,op,ADC_REG_CFGR1);
 if(op==LAMP_ADC_BASELINE) {
  if(a->baseline_verified || evidence.reset_channel_evidence_epoch!=a->epoch || !evidence.no_channel_update_inflight || (cfgr&0x200004))
   return failure(a,ADC_FIELD_BASELINE_ERROR,op,ADC_REG_CFGR1);
  if(!read_reg(a,op,ADC_REG_SMPR,&raw))return false;
  if(raw&SMPR_RESERVED)return failure(a,ADC_FIELD_RESERVED,op,ADC_REG_SMPR);
  if(!read_reg(a,op,ADC_REG_CHSELR,&raw))return false;
  if(raw)return failure(a,ADC_FIELD_BASELINE_ERROR,op,ADC_REG_CHSELR);
  if(request->mask || request->value)return failure(a,ADC_FIELD_REQUEST,op,reg);
  a->baseline_verified=true;reply->valid=true;reply->met=true;return true;
 }
 if(op==LAMP_ADC_WRITE_CFGR || op==LAMP_ADC_READ_CFGR) {
  reg=ADC_REG_CFGR1;expected=a->descriptor.cfgr1;writing=op==LAMP_ADC_WRITE_CFGR;reading=!writing;
 } else if(op==LAMP_ADC_WRITE_CHANNELS || op==LAMP_ADC_READ_CHANNELS) {
  reg=ADC_REG_CHSELR;expected=a->descriptor.chselr;writing=op==LAMP_ADC_WRITE_CHANNELS;reading=!writing;
 } else if(op==LAMP_ADC_WRITE_SMPR || op==LAMP_ADC_READ_SMPR) {
  reg=ADC_REG_SMPR;expected=a->descriptor.smpr;writing=op==LAMP_ADC_WRITE_SMPR;reading=!writing;
 } else if(op==LAMP_ADC_CLEAR_BEFORE_CFGR || op==LAMP_ADC_CLEAR_BEFORE_CHANNELS) {
  expected=(struct adc_masked_field){0x2000,0x2000};reg=ADC_REG_ISR;writing=true;
 } else if(op!=LAMP_ADC_FINAL_DISABLED) {reg=ADC_REG_ISR;reading=true;}
 if(request->mask!=expected.mask || request->value!=expected.value)
  return failure(a,ADC_FIELD_REQUEST,op,reg);
 if(reg==ADC_REG_ISR && writing) {
  /* Dedicated W1C: never read/merge ISR. Only CCRDY is written as1. */
  return write_reg(a,op,reg,0x2000);
 }
 if(reading || writing) {
  if(reg==ADC_REG_CFGR1)raw=cfgr;
  else if(!read_reg(a,op,reg,&raw))return false;
  if(reg==ADC_REG_SMPR && (raw&SMPR_RESERVED))return failure(a,ADC_FIELD_RESERVED,op,reg);
  if(reg==ADC_REG_CHSELR && !(cfgr&0x200000) && (raw&0xfff80000))
   return failure(a,ADC_FIELD_RESERVED,op,reg);
  if(writing) {
   /* Request must match encoded mode; refuse mode drift before CHSELR access. */
   if(reg==ADC_REG_CHSELR && ((cfgr^a->descriptor.cfgr1.value)&0x200004))
    return failure(a,ADC_FIELD_GUARD,op,ADC_REG_CFGR1);
   return write_reg(a,op,reg,adc_channel_merge(raw,expected));
  }
  reply->valid=true;reply->value=(int32_t)raw;return true;
 }
 reply->valid=true;reply->met=true;return true;
}
struct lamp_adc_field_backend adc_field_adapter_backend(struct adc_field_adapter *a) {
 struct lamp_adc_field_backend b={a,transaction};return b;
}
