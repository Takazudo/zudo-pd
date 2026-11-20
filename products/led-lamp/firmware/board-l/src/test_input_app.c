#include "output_composition.h"
#include "discontinuous_acquisition.h"
#include "completed_frame_bridge.h"
#include "input_composition.h"
#include "acquisition_fixed_word.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
struct ram {
 uint32_t regs[TP_REGISTER_COUNT];struct tim3_preload_proof proof;
 unsigned positive_writes,proofs,reads,writes,fail_kind,fail_at,mutation;
 struct tim3_preload *adapter;
};
static unsigned cases;
static enum board_l_result proof(void *ctx,struct tim3_preload_proof *out)
{
 struct ram *r=ctx;++r->proofs;*out=r->proof;
 if(r->fail_kind==1 && r->proofs==r->fail_at)return BOARD_L_IO_ERROR;
 if(r->mutation==1 && r->writes)out->epoch++;
 if(r->mutation==2 && r->writes)out->scope_current=false;
 if(r->mutation==3 && r->reads>=3)out->scope_generation++;
 if(r->mutation==4){struct timer_sink_receipt receipt;assert(tim3_preload_write(r->adapter,0,&receipt)!=BOARD_L_OK);}
 return BOARD_L_OK;
}
static enum board_l_result read_reg(void *ctx,enum tim3_preload_register reg,uint32_t *value)
{
 struct ram *r=ctx;assert(reg<TP_REGISTER_COUNT);++r->reads;*value=r->regs[reg];
 if(r->fail_kind==2 && r->reads==r->fail_at)return BOARD_L_IO_ERROR;
 if(r->mutation==5 && reg==TP_CCR1)*value^=1u;
 if(r->mutation==6 && reg==TP_ARR && r->writes)*value+=1u;
 if(r->mutation==7 && reg==TP_CCR1)*value|=0x10000u;
 return BOARD_L_OK;
}
static enum board_l_result write_reg(void *ctx,uint16_t ccr)
{
 struct ram *r=ctx;++r->writes;if(ccr)++r->positive_writes;r->regs[TP_CCR1]=ccr;
 if(r->fail_kind==3)return BOARD_L_IO_ERROR; /* uncertain write DID affect RAM */
 return BOARD_L_OK;
}
static struct tim3_preload_config config(void)
{
 /* RAM-only fixture: no adopted timer PSC/ARR/endpoint/clock values. */
 return (struct tim3_preload_config){true,42,3200,0,0x85,0,1,0x7868,0x11,true,1,3200};
}
static void setup(struct ram *r,struct tim3_preload *p)
{
 struct tim3_preload_config c=config();struct tim3_preload_transport t={r,proof,read_reg,write_reg};
 *r=(struct ram){0};*p=(struct tim3_preload){0};r->adapter=p;
 r->regs[TP_CR1]=c.expected_cr1;r->regs[TP_SMCR]=c.expected_smcr;r->regs[TP_DIER]=c.expected_dier;
 r->regs[TP_CCMR1]=c.expected_ccmr1;r->regs[TP_CCER]=c.expected_ccer;r->regs[TP_PSC]=c.psc;
 r->regs[TP_ARR]=c.period_ticks-1;r->regs[TP_CCR1]=17;
 r->proof=(struct tim3_preload_proof){42,1,true,true,true,true,true,true,true,true,true};
 assert(tim3_preload_configure(p,&c,&t));assert(!r->reads && !r->proofs && !r->writes);
}
/* New combined-flow fixture; no original V60 main/cases invoked. */
struct board_l_config {unsigned fixture;};
struct rig;
struct provider_context {unsigned tag;struct rig *rig;};
struct rig {
 struct ram ram;struct output_composition composition;struct output_composition_inputs inputs;
 struct lamp_board_binding board;struct lamp_app app;struct lamp_app_io app_io;
 struct provider_context contexts[4];struct preload_lifecycle_providers providers;
 struct tim3_preload_config timer;struct tim3_preload_transport transport;
 struct host_timer_setup timer_setup;struct lamp_board_setup board_setup;
 struct board_l_config board_config;
 unsigned init_calls,ready_calls,inhibit_calls,scenario,prep_calls;bool initialized;
 uint64_t owner_epoch,ticks,sequence;
 struct input_composition input;struct input_composition_inputs input_settings;
 uint32_t adc_cr,adc_isr,adc_dr;
 unsigned adc_starts,adc_reads,adc_clears,adc_proofs,input_fault;
 uint32_t knob_raw; bool thermal_known,thermal_allows,input_qualified;
 bool adc_active,adc_eoc,adc_eos,consumer_valid;
};
static struct rig *provider(void *ctx,unsigned expected)
{struct provider_context *c=ctx;assert(c && c->tag==expected);return c->rig;}
static enum board_l_result life_owner(void *ctx,struct preload_lifecycle_owner *out)
{
 struct rig *r=provider(ctx,1);*out=(struct preload_lifecycle_owner){r->owner_epoch,true,true,true,true};
 return BOARD_L_OK;
}
static enum board_l_result life_init(void *ctx,const struct board_l_config *config)
{
 struct rig *r=provider(ctx,2);assert(config==&r->board_config && config->fixture==61);++r->init_calls;
 if(r->scenario==1)return BOARD_L_IO_ERROR;
 r->initialized=true;return BOARD_L_OK;
}
static void life_inhibit(void *ctx){struct rig *r=provider(ctx,4);++r->inhibit_calls;}
static enum board_l_result sample_clock(void *ctx,struct sample_clock *out)
{struct rig *r=ctx;*out=(struct sample_clock){++r->ticks,true};return BOARD_L_OK;}
static enum board_l_result sample_thermal(void *ctx,uint32_t raw,struct sample_thermal *out)
{
 struct rig *r=ctx;assert(raw==1234);*out=(struct sample_thermal){r->thermal_known,r->thermal_allows};
 if(r->input_fault==5){r->ticks+=20000;}
 return BOARD_L_OK;
}
static struct adc_channel_choice adc_choice(void)
{return (struct adc_channel_choice){ADC_CHANNEL_BITMAP,ADC_KNOB_THEN_NTC,ADC_ALIGN_RIGHT,12,0,4,1,2,321};}
static enum board_l_result adc_proof(void *ctx,struct da_proof *out)
{
 struct rig *r=ctx;++r->adc_proofs;
 *out=(struct da_proof){.epoch=r->owner_epoch,.scope_until=1000000,.choice=adc_choice(),
 .valid=true,.exclusive=true,.whole_consumer_scope=true,.consumer_epoch_valid=r->consumer_valid,
 .clock_qualified=r->input_qualified,.entry_qualified=r->input_qualified,.configuration_qualified=r->input_qualified,.normal_enable=true,
 .discontinuous=true,.software_only=true,.lftrig=true,.sequence_integrity=true};return BOARD_L_OK;
}
static enum board_l_result adc_word_read(void *ctx,enum acquisition_register reg,uint32_t *out)
{
 struct rig *r=ctx;struct acquisition_location location;
 assert(acquisition_word_read_location(reg,&location) && location.width==4);
 if(reg==ACQ_ISR && (r->adc_cr&4u) && r->input_fault!=1){
  r->adc_cr&=~4u;r->adc_isr|=4u;
  if((r->adc_starts%2u)==0 && r->input_fault!=4)r->adc_isr|=8u;
  if(r->input_fault==2)r->adc_isr|=16u;
  r->adc_dr=(r->adc_starts%2u)?r->knob_raw:1234u;
 }
 if(reg==ACQ_CR)*out=r->adc_cr;
 else if(reg==ACQ_ISR)*out=r->adc_isr;
 else{
  assert(r->adc_isr&4u);*out=r->adc_dr;r->adc_isr&=~4u;++r->adc_reads;
  if(r->input_fault==3 && (r->adc_reads%2u)==0)return BOARD_L_IO_ERROR;
  if(r->input_fault==6 && (r->adc_reads%2u))++r->owner_epoch;
 }
 return BOARD_L_OK;
}
static enum board_l_result adc_word_store(void *ctx,enum acquisition_store kind,uint32_t word)
{
 struct rig *r=ctx;struct acquisition_location location;
 assert(acquisition_word_store_location(kind,word,&location));
 if(kind==ACQ_START_COMMAND){
  assert(r->adc_cr==0x10000001u && !(r->adc_isr&0x1cu));
  r->adc_cr=(r->adc_cr&1u)|word;++r->adc_starts;
 }else{assert((r->adc_isr&8u) && !(r->adc_isr&4u));r->adc_isr&=~word;++r->adc_clears;}
 return BOARD_L_OK;
}
static enum board_l_result input_owner(void *ctx,struct completed_frame_owner *out)
{
 struct rig *r=ctx;*out=(struct completed_frame_owner){r->owner_epoch,true,true,true,r->consumer_valid};return BOARD_L_OK;
}
static void connect_input(struct rig *r)
{
 r->adc_cr=0x10000001u;r->adc_isr=0x2803u;r->consumer_valid=true;
 r->input_settings.choice=adc_choice();r->input_settings.epoch=42;r->input_settings.first_sequence=7;
 r->input_settings.clock_ticks_per_second=1000000;
 r->input_settings.limits=(struct da_limits){1000000,16000000,10000,50000,50000,50000,100,1000000,3,true};
 r->input_settings.providers=(struct acquisition_register_providers){r,adc_proof,r,sample_clock};
 r->input_settings.transport=(struct acquisition_register_transport){r,adc_word_read,adc_word_store};
 r->input_settings.owner_context=r;r->input_settings.owner=input_owner;
 r->input_settings.thermal_context=r;r->input_settings.thermal=sample_thermal;
 assert(input_composition_configure(&r->input,&r->input_settings));
 assert(input_composition_hooks(&r->input,&r->board_setup.acquisition));
}
static bool prepare(void *ctx,enum adc_kind kind,enum adc_operation op,uint8_t value,struct adc_reply *reply)
{
 struct rig *r=ctx;assert((unsigned)op==r->prep_calls++);
 *reply=(struct adc_reply){true,true,kind==ADC_VERIFY?value:7};return true;
}
static enum board_l_result access_proof(void *ctx,struct tim3_access_evidence *out)
{
 struct rig *r=ctx;*out=(struct tim3_access_evidence){r->ram.proof,true,r->initialized,true};return BOARD_L_OK;
}
static enum board_l_result readiness_proof(void *ctx,struct tim3_readiness_proof *out)
{
 struct rig *r=provider(ctx,3);
 *out=(struct tim3_readiness_proof){r->owner_epoch,7,true,true,true,r->initialized,true,true,true};
 if(r->scenario==2)out->shadow_update_history_qualified=false;
 return BOARD_L_OK;
}
static enum board_l_result readiness_read(void *ctx,enum tim3_preload_register reg,uint32_t *out)
{
 struct rig *r=provider(ctx,3);assert((unsigned)reg<TP_CCR1);++r->ready_calls;*out=r->ram.regs[reg];return BOARD_L_OK;
}
static void build(struct rig *r,unsigned scenario)
{
 struct tim3_preload temporary;unsigned i;
 *r=(struct rig){0};r->scenario=scenario;r->knob_raw=4095;r->thermal_known=true;r->thermal_allows=true;r->input_qualified=true;r->owner_epoch=42;r->board_config.fixture=61;
 setup(&r->ram,&temporary);
 for(i=0;i<4;++i)r->contexts[i]=(struct provider_context){i+1,r};
 r->inputs.profile=config();r->inputs.mapper=(struct ctrl_timer_config){true,CTRL_TIMER_EDGE_UP_PWM1_ACTIVE_HIGH,3200,true,100,2000};
 r->inputs.access_proof=(struct tim3_access_provider){r,access_proof};
 r->inputs.access_seam=(struct tim3_access_seam){&r->ram,read_reg,write_reg};
 r->inputs.readiness=(struct tim3_readiness_io){&r->contexts[2],readiness_proof,&r->contexts[2],readiness_read};
 r->inputs.owner_context=&r->contexts[0];r->inputs.owner=life_owner;
 r->inputs.init_context=&r->contexts[1];r->inputs.initialize_off=life_init;
 r->inputs.inhibit_context=&r->contexts[3];r->inputs.request_off=life_inhibit;
 assert(output_composition_configure(&r->composition,&r->inputs));r->ram.adapter=&r->composition.lifecycle.preload;
 assert(output_composition_backend(&r->composition,&r->board_setup.output));
 r->board_setup.samples=(struct sample_adapter_config){true,true,10000,{true,4095,0,4095},4};
 connect_input(r);
 if(scenario==99){struct adc_backend backend={r,prepare};struct adc_qualification q={1,true,true,true};
 assert(lamp_board_bind_preparation(&r->board,&r->board_setup,&backend,&q)==BOARD_L_OK);}
 else{assert(lamp_board_bind(&r->board,&r->board_setup)==BOARD_L_OK);}
 r->app_io=lamp_board_io(&r->board);
 assert(!r->init_calls && !r->ready_calls && !r->inhibit_calls && !r->ram.writes);
}
static struct lamp_app_report init_app(struct rig *r)
{return lamp_app_initialize(&r->app,&r->app_io,&r->board_config);}
static struct lamp_app_report tick(struct rig *r)
{
 struct lamp_config policy={LAMP_FULL,LAMP_RECOVERY_AUTO};
 r->ticks+=200;++r->ram.proof.scope_generation;return lamp_app_tick(&r->app,&policy);
}
static void positive(struct rig *r)
{
 struct lamp_app_report report=init_app(r);assert(report.status==LAMP_APP_CORE_OFF && !r->adc_starts);
 report=tick(r);assert(report.status==LAMP_APP_OK && report.command==LAMP_FULL && r->ram.regs[TP_CCR1]==2000);
 assert(r->adc_starts==2 && r->adc_reads==2 && r->adc_isr==0x2803u && !report.physical_off_verified);
}
struct direct {uint32_t raw;uint64_t time,sequence;bool thermal;};
static enum board_l_result dclock(void *ctx,struct sample_clock *out)
{struct direct *d=ctx;*out=(struct sample_clock){d->time,true};return BOARD_L_OK;}
static enum board_l_result dacquire(void *ctx,struct sample_frame *out)
{struct direct *d=ctx;++d->sequence;*out=(struct sample_frame){{d->raw,d->sequence,d->time,true},{1234,d->sequence,d->time,true}};return BOARD_L_OK;}
static enum board_l_result dthermal(void *ctx,uint32_t raw,struct sample_thermal *out)
{struct direct *d=ctx;(void)raw;*out=(struct sample_thermal){true,d->thermal};return BOARD_L_OK;}
static void held(struct lamp_app_report x){assert(!x.command && !x.physical_off_verified);}
int main(void)
{
 struct rig r;struct lamp_app_report x;unsigned i,j;
 /* Actual consumer path: fill old zero window, then a full raw step. */
 build(&r,0);r.knob_raw=0;held(init_app(&r));
 for(i=0;i<4;++i)held(tick(&r));
 r.knob_raw=4095;
 for(i=1;i<=4;++i){uint32_t expected;assert(knob_request((4095u*i)/4,&r.board_setup.samples.knob,&expected));
  x=tick(&r);assert(x.core_command==expected && r.board.adapter.knob_count==4);}
 ++cases;
 /* Each invalid kind clears all history immediately and application stays latched. */
 for(i=0;i<3;++i){struct lamp_samples first;unsigned positive_count;
  build(&r,0);positive(&r);for(j=0;j<3;++j)(void)tick(&r);
  if(i==0)r.thermal_allows=false;
  if(i==1)r.thermal_known=false;
  if(i==2)r.input_fault=5;
  held(tick(&r));assert(r.app.core.latched && !r.board.adapter.knob_count && !r.board.adapter.knob_sum);
  first=r.app.first_invalid_sample;positive_count=r.ram.positive_writes;
  r.thermal_allows=true;r.thermal_known=true;r.input_fault=0;r.knob_raw=4095;
  held(tick(&r));assert(r.ram.positive_writes==positive_count);
  r.knob_raw=0;held(tick(&r));r.knob_raw=4095;held(tick(&r));
  ++r.ram.proof.scope_generation;held(init_app(&r));assert(!r.board.adapter.knob_count);
  r.knob_raw=1024;x=tick(&r);assert(x.command==((uint64_t)1024*LAMP_FULL)/4095);
  assert(r.board.adapter.knob_count==1 && !memcmp(&first,&x.first_invalid_sample,sizeof first));++cases;
 }
 /* Age eviction: old accepted values cannot survive a long gap. */
 build(&r,0);positive(&r);r.ticks+=20000;r.knob_raw=0;held(tick(&r));
 assert(r.board.adapter.knob_count==1 && !r.app.core.latched);++cases;
 /* Terminal uncertain acquisition/output paths remain terminal with populated filter. */
 for(i=0;i<2;++i){unsigned starts,writes,positives;build(&r,0);positive(&r);
  if(i==0)r.input_fault=3;else r.ram.fail_kind=3;
  held(tick(&r));assert(r.app.reinitialize_required);
  if(!i)assert(!r.board.adapter.knob_count);
  starts=r.adc_starts;writes=r.ram.writes;positives=r.ram.positive_writes;
  r.input_fault=0;r.ram.fail_kind=0;++r.ram.proof.scope_generation;held(init_app(&r));held(tick(&r));
  assert(r.adc_starts==starts && r.ram.positive_writes==positives);
  if(i){assert(r.ram.writes==writes);}
  ++cases;
 }
 /* All supported windows, bounded arithmetic, ring rollover, explicit bypass. */
 for(i=1;i<=KNOB_AVERAGE_MAX_WINDOW;++i){struct sample_adapter a={0};struct direct d={UINT32_MAX,1,0,true};
  struct sample_adapter_config cfg={true,true,100000,{true,UINT32_MAX,0,UINT32_MAX},(uint8_t)i};
  struct sample_adapter_hooks hooks={&d,dacquire,dclock,dthermal};struct lamp_samples out;
  assert(sample_adapter_initialize(&a,&cfg,&hooks)==BOARD_L_OK);
  for(j=0;j<100;++j){++d.time;assert(sample_adapter_read(&a,&out)==BOARD_L_OK && out.knob==LAMP_FULL);
   assert(a.knob_count<=i && a.knob_sum==(uint64_t)a.knob_count*UINT32_MAX);}
  d.raw=0;
  for(j=1;j<=i;++j){uint32_t expected;uint32_t mean=(uint32_t)(((uint64_t)(i-j)*UINT32_MAX)/i);
   assert(knob_request(mean,&cfg.knob,&expected));++d.time;
   assert(sample_adapter_read(&a,&out)==BOARD_L_OK && out.knob==expected);}
  assert(!out.knob);++cases;
 }
 for(i=0;i<2;++i){struct sample_adapter a={0};struct direct d={0,1,0,true};
  struct sample_adapter_config cfg={true,true,100,{true,4095,0,4095},i?33:0};
  struct sample_adapter_hooks hooks={&d,dacquire,dclock,dthermal};
  assert(sample_adapter_initialize(&a,&cfg,&hooks)==BOARD_L_UNCONFIGURED && !d.sequence);++cases;
 }
 {struct sample_adapter a={0};struct direct d={4095,1,0,true};struct lamp_samples out;
  struct sample_adapter_config cfg={true,true,100,{true,4095,0,4095},4};
  struct sample_adapter_hooks hooks={&d,dacquire,dclock,dthermal};
  assert(sample_adapter_initialize(&a,&cfg,&hooks)==BOARD_L_OK);
  assert(sample_adapter_read(&a,&out)==BOARD_L_OK && a.knob_count==1);
  d.raw=4096;++d.time;assert(sample_adapter_read(&a,&out)==BOARD_L_OK);
  assert(a.status==SAMPLE_KNOB_INVALID && !out.knob_valid && !a.knob_count && !a.knob_sum);++cases;
 }
 {struct sample_adapter a={0};struct direct d={4095,1,0,true};struct lamp_samples out;
  struct sample_adapter_config cfg={true,true,100,{true,4095,0,4095},4};
  struct sample_adapter_hooks hooks={&d,dacquire,dclock,dthermal};
  assert(sample_adapter_initialize(&a,&cfg,&hooks)==BOARD_L_OK);
  assert(sample_adapter_read(&a,&out)==BOARD_L_OK);d.time=101;d.raw=0;
  assert(sample_adapter_read(&a,&out)==BOARD_L_OK && a.knob_count==2 && out.knob>0);
  d.time=102;assert(sample_adapter_read(&a,&out)==BOARD_L_OK && a.knob_count==2 && !out.knob);
  --d.sequence;assert(sample_adapter_read(&a,&out)==BOARD_L_OK && a.status==SAMPLE_REPLAY && !a.knob_count);
  ++d.sequence;d.raw=1000;assert(sample_adapter_read(&a,&out)==BOARD_L_OK && a.knob_count==1);++cases;
 }
 {build(&r,0);positive(&r);r.knob_raw=4096;held(tick(&r));
  assert(r.app.reinitialize_required && !r.board.adapter.knob_count && r.input.first_error!=IC_NONE);++cases;}
 printf("PASS %u explicit-window knob averaging scenarios\n",cases);return 0;
}
