#include "discontinuous_acquisition.h"
#include <stddef.h>
static bool fail(struct discontinuous_acquisition *a,enum da_error e,enum board_l_result r)
{
 if(a->first_error==DA_NONE){a->first_error=e;a->first_stage=a->stage;a->first_rank=a->rank;a->first_callback=r;}
 return false;
}
static bool same(const struct adc_channel_choice *a,const struct adc_channel_choice *b)
{
 return a->mode==b->mode && a->order==b->order && a->alignment==b->alignment &&
 a->resolution_bits==b->resolution_bits && a->knob_channel==b->knob_channel &&
 a->ntc_channel==b->ntc_channel && a->knob_sample_group==b->knob_sample_group &&
 a->ntc_sample_group==b->ntc_sample_group && a->sampling_cycles_times_two==b->sampling_cycles_times_two;
}
/* Bracket every I/O with fresh independent proof and monotonic clock. A scope
 * is held externally across the entire operation/consumer read, not acquired by
 * these queries. Exclusive fixed epoch prevents honest provider ABA. */
static bool checkpoint(struct discontinuous_acquisition *a)
{
 struct da_proof p={0};struct sample_clock c={0};enum board_l_result r;
 if(a->first_error!=DA_NONE)return false;
 r=a->io.proof(a->io.context,&p);
 if(a->first_error!=DA_NONE)return false;
 if(r!=BOARD_L_OK)return fail(a,DA_PROOF_CALLBACK,r);
 if(!p.valid || p.epoch!=a->epoch || !p.exclusive || !p.whole_consumer_scope ||
 !p.consumer_epoch_valid || !p.clock_qualified || !p.entry_qualified ||
 !p.configuration_qualified || !same(&p.choice,&a->choice) || !p.normal_enable ||
 !p.discontinuous || !p.software_only || !p.lftrig || p.autoff || p.continuous ||
 p.oversampling || !p.sequence_integrity || p.scope_until!=a->limits.scope_until)
  return fail(a,DA_PROOF,BOARD_L_UNCONFIGURED);
 r=a->io.clock(a->io.context,&c);
 if(a->first_error!=DA_NONE)return false;
 if(r!=BOARD_L_OK)return fail(a,DA_CLOCK_CALLBACK,r);
 if(!c.valid || (a->have_clock && c.ticks<a->last_clock))return fail(a,DA_CLOCK,BOARD_L_UNCONFIGURED);
 a->last_clock=c.ticks;a->have_clock=true;
 if(c.ticks>=a->limits.scope_until)return fail(a,DA_SCOPE,BOARD_L_UNCONFIGURED);
 if(a->in_frame && (c.ticks-a->frame_begin>a->limits.frame_ticks ||
 c.ticks-a->frame_begin>a->limits.skew_ticks || c.ticks-a->frame_begin>a->limits.max_age_ticks ||
 c.ticks-a->step_begin>a->limits.step_ticks))return fail(a,DA_TIME,BOARD_L_UNCONFIGURED);
 return true;
}
static bool status(struct discontinuous_acquisition *a,struct da_status *s)
{
 enum board_l_result r;*s=(struct da_status){0};
 if(!checkpoint(a))return false;
 r=a->io.status(a->io.context,s);
 if(r!=BOARD_L_OK)return fail(a,DA_STATUS_CALLBACK,r);
 if(!checkpoint(a))return false;
 if(!s->valid || s->error)return fail(a,DA_STATUS,BOARD_L_IO_ERROR);
 if(s->overrun)return fail(a,DA_OVERRUN,BOARD_L_IO_ERROR);
 return true;
}
static bool idle(struct discontinuous_acquisition *a,bool eos)
{
 struct da_status s;
 if(!status(a,&s))return false;
 if(s.adstart || s.eoc || s.eos!=eos)return fail(a,DA_STATUS,BOARD_L_IO_ERROR);
 return true;
}
bool da_configure(struct discontinuous_acquisition *a,const struct adc_channel_choice *choice,
 uint64_t epoch,uint64_t sequence,const struct da_limits *limits,const struct da_io *io)
{
 struct adc_preparation neutral={0};struct adc_channel_descriptor d;uint64_t numerator,min_ticks;
 if(!a)return false;
 if(a->attempted)return fail(a,DA_REBIND,BOARD_L_UNCONFIGURED);
 a->attempted=true;a->stage=DA_CONFIGURATION;
 if(!choice || !limits || !io || !epoch || sequence==UINT64_MAX || !limits->qualified ||
 !io->proof || !io->clock || !io->status || !io->start || !io->read || !io->clear_eos ||
 !limits->ticks_per_second || limits->ticks_per_second>UINT64_MAX/174u ||
 limits->adc_hz<140000u || limits->adc_hz>35000000u || !limits->polls_per_conversion ||
 !limits->step_ticks || !limits->frame_ticks || !limits->skew_ticks || !limits->max_age_ticks ||
 !limits->minimum_spacing_ticks || !limits->scope_until ||
 adc_channel_describe(choice,&neutral,&d)!=ADC_CHANNEL_VALID_DESCRIPTOR)
  return fail(a,DA_CONFIG,BOARD_L_UNCONFIGURED);
 /* LFTRIG adds one clock per software trigger. Necessary conversion-time floor,
  * NOT sufficient latency budget. No rounded-down divide and no overflow. */
 numerator=174u*limits->ticks_per_second;
 min_ticks=numerator/limits->adc_hz+(numerator%limits->adc_hz!=0u);
 if(min_ticks>UINT64_MAX/2u || limits->step_ticks<min_ticks ||
 limits->frame_ticks<2u*min_ticks || limits->skew_ticks<2u*min_ticks ||
 limits->max_age_ticks<2u*min_ticks)return fail(a,DA_CONFIG,BOARD_L_UNCONFIGURED);
 a->choice=*choice;a->limits=*limits;a->io=*io;a->epoch=epoch;a->next_sequence=sequence;
 a->configured=true;return true;
}
enum board_l_result da_produce(void *context,struct adc_completed_frame *out)
{
 struct discontinuous_acquisition *a=context;struct adc_completed_frame f={0};
 struct sample_frame decoded;enum board_l_result r;unsigned first;
 if(out)*out=(struct adc_completed_frame){0};
 if(!a)return BOARD_L_UNCONFIGURED;
 if(a->first_error!=DA_NONE || !a->configured)return BOARD_L_UNCONFIGURED;
 if(!out){(void)fail(a,DA_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(a->busy){(void)fail(a,DA_REENTRANT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 a->busy=true;a->stage=DA_ENTRY;a->rank=0;
 if(a->next_sequence==UINT64_MAX){(void)fail(a,DA_SEQUENCE_EXHAUSTED,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!checkpoint(a))return BOARD_L_UNCONFIGURED;
 if(a->have_frame && a->last_clock-a->last_begin<a->limits.minimum_spacing_ticks){
  (void)fail(a,DA_SPACING,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 a->frame_begin=a->last_clock;a->step_begin=a->last_clock;a->in_frame=true;
 if(!idle(a,false))return BOARD_L_UNCONFIGURED;
 f.owner_epoch=a->epoch;f.sequence=a->next_sequence;f.captured_at=a->frame_begin;
 f.count=2;f.resolution_bits=12;f.alignment=a->choice.alignment;f.kind=ADC_COMPLETED_CONVERSIONS;
 first=a->choice.order==ADC_KNOB_THEN_NTC?0u:4u;
 for(a->rank=0;a->rank<2;++a->rank){
  struct da_status s;uint32_t word=0;bool ready=false;
  a->stage=DA_START;a->step_begin=a->last_clock;
  if(!checkpoint(a))return BOARD_L_UNCONFIGURED;
  a->start_uncertain=true;r=a->io.start(a->io.context);
  if(r!=BOARD_L_OK){(void)fail(a,DA_START_CALLBACK,r);return BOARD_L_UNCONFIGURED;}
  if(!checkpoint(a))return BOARD_L_UNCONFIGURED;
  a->stage=DA_WAIT;
  for(a->polls=0;a->polls<a->limits.polls_per_conversion;++a->polls){
   if(!status(a,&s))return BOARD_L_UNCONFIGURED;
   if(s.eos!=(a->rank==1 && s.eoc) || s.adstart==s.eoc){
    (void)fail(a,DA_STATUS,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
   if(s.eoc){ready=true;break;}
  }
  if(!ready){(void)fail(a,DA_POLL_LIMIT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
  a->stage=DA_READ;
  if(!checkpoint(a))return BOARD_L_UNCONFIGURED;
  r=a->io.read(a->io.context,&word);
  if(r!=BOARD_L_OK){(void)fail(a,DA_READ_CALLBACK,r);return BOARD_L_UNCONFIGURED;}
  if(!checkpoint(a))return BOARD_L_UNCONFIGURED;
  if(word & ~(a->choice.alignment==ADC_ALIGN_LEFT?UINT32_C(0xfff0):UINT32_C(0x0fff))){
   (void)fail(a,DA_FORMAT,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
  a->stage=DA_AFTER_READ;if(!idle(a,a->rank==1))return BOARD_L_UNCONFIGURED;
  a->start_uncertain=false;
  f.words[a->rank]=(struct adc_completed_word){word,a->rank==0?first:4u-first,a->epoch,f.sequence,true,true};
 }
 a->stage=DA_CLEAR;
 if(!checkpoint(a))return BOARD_L_UNCONFIGURED;
 r=a->io.clear_eos(a->io.context);
 if(r!=BOARD_L_OK){(void)fail(a,DA_CLEAR_CALLBACK,r);return BOARD_L_UNCONFIGURED;}
 if(!checkpoint(a))return BOARD_L_UNCONFIGURED;
 a->stage=DA_FINAL;if(!idle(a,false))return BOARD_L_UNCONFIGURED;
 f.owner_valid=true;f.sequence_valid=true;f.capture_valid=true;f.configuration_valid=true;
 f.format_valid=true;f.status_valid=true;f.completed=true;f.coherent=true;
 if(adc_decode_completed_frame(&a->choice,a->epoch,&f,&decoded)!=ADC_FRAME_DECODE_OK){
  (void)fail(a,DA_FORMAT,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
 if(!checkpoint(a))return BOARD_L_UNCONFIGURED;
 *out=f;a->last_begin=a->frame_begin;a->have_frame=true;a->in_frame=false;a->busy=false;++a->next_sequence;
 return BOARD_L_OK;
}
