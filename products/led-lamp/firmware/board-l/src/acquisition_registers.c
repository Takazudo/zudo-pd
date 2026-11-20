#include "acquisition_registers.h"
#define ADVREGEN UINT32_C(0x10000000)
#define ADEN UINT32_C(1)
#define ADSTART UINT32_C(4)
#define EOC UINT32_C(4)
#define EOS UINT32_C(8)
#define OVR UINT32_C(16)
#define ISR_ALLOWED UINT32_C(0x2b9f)
bool acquisition_register_location(enum acquisition_register reg,struct acquisition_location *out)
{
 static const uint8_t offset[]={0,8,0x40};
 if(out)*out=(struct acquisition_location){0};
 if(!out || (unsigned)reg>=ACQ_REGISTER_COUNT)return false;
 *out=(struct acquisition_location){UINT32_C(0x40012400)+offset[reg],4};return true;
}
static bool fail(struct acquisition_registers *a,enum acquisition_register_error e,enum board_l_result r)
{
 if(a->first_error==AR_NONE){a->first_error=e;a->first_callback=r;a->first_operation=a->operation;
 a->first_register=a->current_register;a->first_start_uncertain=a->start_uncertain;
 a->first_store_uncertain=a->store_uncertain;a->first_dr_uncertain=a->dr_consumption_uncertain;}
 return false;
}
static bool enter(struct acquisition_registers *a,enum acquisition_register_operation op)
{
 if(!a)return false;
 if(a->self!=a)return fail(a,AR_CONTEXT,BOARD_L_UNCONFIGURED);
 if(!a->configured || a->first_error!=AR_NONE)return false;
 if(a->busy)return fail(a,AR_REENTRANT,BOARD_L_UNCONFIGURED);
 a->busy=true;a->operation=op;a->current_register=ACQ_REGISTER_COUNT;return true;
}
static bool same(const struct adc_channel_choice *a,const struct adc_channel_choice *b)
{
 return a->mode==b->mode && a->order==b->order && a->alignment==b->alignment &&
 a->resolution_bits==b->resolution_bits && a->knob_channel==b->knob_channel && a->ntc_channel==b->ntc_channel &&
 a->knob_sample_group==b->knob_sample_group && a->ntc_sample_group==b->ntc_sample_group &&
 a->sampling_cycles_times_two==b->sampling_cycles_times_two;
}
static bool qualify(struct acquisition_registers *a,struct da_proof *pout,struct sample_clock *cout)
{
 struct da_proof p={0};struct sample_clock c={0};enum board_l_result r;
 if(a->first_error!=AR_NONE)return false;
 r=a->providers.proof(a->providers.proof_context,&p);
 if(a->first_error!=AR_NONE)return false;
 if(r!=BOARD_L_OK)return fail(a,AR_PROOF_CALLBACK,r);
 if(!p.valid || p.epoch!=a->epoch || p.scope_until!=a->scope_until || !same(&p.choice,&a->choice) ||
 !p.exclusive || !p.whole_consumer_scope || !p.consumer_epoch_valid || !p.clock_qualified ||
 !p.entry_qualified || !p.configuration_qualified || !p.normal_enable || !p.discontinuous ||
 !p.software_only || !p.lftrig || p.autoff || p.continuous || p.oversampling || !p.sequence_integrity)
  return fail(a,AR_PROOF,BOARD_L_UNCONFIGURED);
 r=a->providers.clock(a->providers.clock_context,&c);
 if(a->first_error!=AR_NONE)return false;
 if(r!=BOARD_L_OK)return fail(a,AR_CLOCK_CALLBACK,r);
 if(!c.valid || (a->have_clock && c.ticks<a->last_clock) || c.ticks>=a->scope_until)
  return fail(a,AR_CLOCK,BOARD_L_UNCONFIGURED);
 a->last_clock=c.ticks;a->have_clock=true;
 if(pout)*pout=p;
 if(cout)*cout=c;
 return true;
}
static bool read_word(struct acquisition_registers *a,enum acquisition_register reg,uint32_t *value)
{
 enum board_l_result r;struct acquisition_location location;
 a->current_register=reg;*value=0;
 if(!acquisition_register_location(reg,&location) || location.width!=4 || location.address%4)
  return fail(a,AR_ARGUMENT,BOARD_L_UNCONFIGURED);
 if(!qualify(a,0,0))return false;
 if(reg==ACQ_DR)a->dr_consumption_uncertain=true;
 r=a->transport.read_word(a->transport.context,reg,value);
 if(r!=BOARD_L_OK)return fail(a,AR_READ,r);
 return qualify(a,0,0);
}
static bool cr_valid(struct acquisition_registers *a,uint32_t value)
{
 a->last_cr=value;
 /* No ADCAL/ADSTP/ADDIS or reserved bits accepted. ADVREGEN and ADEN on. */
 if((value&~(ADVREGEN|ADEN|ADSTART)) || (value&(ADVREGEN|ADEN))!=(ADVREGEN|ADEN))
  return fail(a,AR_STATE,BOARD_L_UNCONFIGURED);
 return true;
}
static bool snapshot(struct acquisition_registers *a,struct da_status *out,uint32_t *raw)
{
 uint32_t before,isr,after;
 if(!read_word(a,ACQ_CR,&before) || !cr_valid(a,before) || !read_word(a,ACQ_ISR,&isr) ||
 !read_word(a,ACQ_CR,&after) || !cr_valid(a,after))return false;
 if(!(before&ADSTART) && (after&ADSTART))return fail(a,AR_TRANSITION,BOARD_L_UNCONFIGURED);
 /* Legitimate conversion completion can cross the snapshot. Once ADSTART
  * falls in software discontinuous mode, no next rank starts by itself. Read
  * ISR again AFTER observing idle; no loop/retry or fabricated pending flags. */
 if((before&ADSTART) && !(after&ADSTART) && !read_word(a,ACQ_ISR,&isr))return false;
 a->last_isr=isr;
 if(isr&~ISR_ALLOWED)return fail(a,AR_STATE,BOARD_L_IO_ERROR);
 *out=(struct da_status){true,(after&ADSTART)!=0,(isr&EOC)!=0,(isr&EOS)!=0,(isr&OVR)!=0,(isr&0x380u)!=0};
 if(raw)*raw=isr;
 return true;
}
static bool store(struct acquisition_registers *a,enum acquisition_store kind,uint32_t word)
{
 enum board_l_result r;
 if((kind==ACQ_START_COMMAND && word!=(ADVREGEN|ADSTART)) ||
 (kind==ACQ_CLEAR_EOS && word!=EOS) || (kind!=ACQ_START_COMMAND && kind!=ACQ_CLEAR_EOS))
  return fail(a,AR_ARGUMENT,BOARD_L_UNCONFIGURED);
 a->current_register=kind==ACQ_START_COMMAND?ACQ_CR:ACQ_ISR;
 if(!qualify(a,0,0))return false;
 if(kind==ACQ_START_COMMAND){a->start_uncertain=true;a->started=true;}
 a->store_uncertain=true;
 r=a->transport.store_word(a->transport.context,kind,word);
 if(r!=BOARD_L_OK)return fail(a,AR_STORE,r);
 return qualify(a,0,0);
}
static enum board_l_result get_proof(void *ctx,struct da_proof *out)
{
 struct acquisition_registers *a=ctx;
 if(out)*out=(struct da_proof){0};
 if(!enter(a,AR_PROOF_OP))return BOARD_L_UNCONFIGURED;
 if(!out){(void)fail(a,AR_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!qualify(a,out,0))return BOARD_L_UNCONFIGURED;
 a->busy=false;return BOARD_L_OK;
}
static enum board_l_result get_clock(void *ctx,struct sample_clock *out)
{
 struct acquisition_registers *a=ctx;
 if(out)*out=(struct sample_clock){0};
 if(!enter(a,AR_CLOCK_OP))return BOARD_L_UNCONFIGURED;
 if(!out){(void)fail(a,AR_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!qualify(a,0,out))return BOARD_L_UNCONFIGURED;
 a->busy=false;return BOARD_L_OK;
}
static enum board_l_result get_status(void *ctx,struct da_status *out)
{
 struct acquisition_registers *a=ctx;struct da_status s;
 if(out)*out=(struct da_status){0};
 if(!enter(a,AR_STATUS_OP))return BOARD_L_UNCONFIGURED;
 if(!out){(void)fail(a,AR_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!snapshot(a,&s,0))return BOARD_L_UNCONFIGURED;
 *out=s;a->busy=false;return BOARD_L_OK;
}
static enum board_l_result start(void *ctx)
{
 struct acquisition_registers *a=ctx;struct da_status s;
 if(!enter(a,AR_START_OP))return BOARD_L_UNCONFIGURED;
 if(a->started || a->next_rank>=2){(void)fail(a,AR_ORDER,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!snapshot(a,&s,0))return BOARD_L_UNCONFIGURED;
 if(s.adstart || s.eoc || s.eos || s.overrun || s.error){(void)fail(a,AR_STATE,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 /* rs bits ADEN/ADDIS/ADSTP/ADCAL receive0 (no command). ADVREGEN's observed
  * RW value1 is preserved, not changed while enabled. No raw CR RMW replay. */
 if(!store(a,ACQ_START_COMMAND,ADVREGEN|ADSTART))return BOARD_L_UNCONFIGURED;
 a->busy=false;return BOARD_L_OK;
}
static enum board_l_result read_data(void *ctx,uint32_t *out)
{
 struct acquisition_registers *a=ctx;struct da_status s;uint32_t value;
 if(out)*out=0;
 if(!enter(a,AR_READ_OP))return BOARD_L_UNCONFIGURED;
 if(!out || !a->started || a->next_rank>=2){(void)fail(a,AR_ORDER,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!snapshot(a,&s,0))return BOARD_L_UNCONFIGURED;
 if(s.adstart || !s.eoc || s.eos!=(a->next_rank==1) || s.overrun || s.error){(void)fail(a,AR_STATE,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!read_word(a,ACQ_DR,&value))return BOARD_L_UNCONFIGURED;
 if(value>65535u){(void)fail(a,AR_DR_WORD,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
 if(!snapshot(a,&s,0))return BOARD_L_UNCONFIGURED;
 if(s.adstart || s.eoc || s.eos!=(a->next_rank==1) || s.overrun || s.error){(void)fail(a,AR_POST_READ,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
 ++a->next_rank;a->started=false;a->dr_consumption_uncertain=false;a->start_uncertain=false;a->store_uncertain=false;
 *out=value;a->busy=false;return BOARD_L_OK;
}
static enum board_l_result clear_eos(void *ctx)
{
 struct acquisition_registers *a=ctx;struct da_status s;uint32_t before,after;
 if(!enter(a,AR_CLEAR_OP))return BOARD_L_UNCONFIGURED;
 if(a->started || a->next_rank!=2){(void)fail(a,AR_ORDER,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!snapshot(a,&s,&before))return BOARD_L_UNCONFIGURED;
 if(s.adstart || s.eoc || !s.eos || s.overrun || s.error){(void)fail(a,AR_STATE,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!store(a,ACQ_CLEAR_EOS,EOS) || !snapshot(a,&s,&after))return BOARD_L_UNCONFIGURED;
 if(s.adstart || s.eoc || s.eos || s.overrun || s.error || (after&~EOS)!=(before&~EOS)){(void)fail(a,AR_W1C,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
 a->next_rank=0;a->store_uncertain=false;a->busy=false;return BOARD_L_OK;
}
bool acquisition_registers_configure(struct acquisition_registers *a,const struct adc_channel_choice *choice,
 uint64_t epoch,uint64_t scope,const struct acquisition_register_providers *providers,const struct acquisition_register_transport *transport)
{
 struct adc_preparation neutral={0};struct adc_channel_descriptor descriptor;
 if(!a)return false;
 if(a->attempted)return fail(a,AR_REBIND,BOARD_L_UNCONFIGURED);
 a->attempted=true;a->self=a;a->operation=AR_CONFIGURE;a->current_register=ACQ_REGISTER_COUNT;
 if(!epoch || !scope || !providers || !providers->proof || !providers->clock || !transport ||
 !transport->read_word || !transport->store_word || !choice ||
 adc_channel_describe(choice,&neutral,&descriptor)!=ADC_CHANNEL_VALID_DESCRIPTOR)
  return fail(a,AR_CONFIG,BOARD_L_UNCONFIGURED);
 a->choice=*choice;a->epoch=epoch;a->scope_until=scope;a->providers=*providers;a->transport=*transport;a->configured=true;return true;
}
bool acquisition_registers_io(struct acquisition_registers *a,struct da_io *out)
{
 if(out)*out=(struct da_io){0};
 if(!a || !out || a->self!=a || !a->configured)return false;
 *out=(struct da_io){a,get_proof,get_clock,get_status,start,read_data,clear_eos};return true;
}
