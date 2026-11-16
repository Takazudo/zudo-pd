#include "tim3_preload.h"
#include "tim3_profile.h"
#include <stddef.h>
static bool fail(struct tim3_preload *p,enum tim3_preload_error error,enum board_l_result result)
{
 if(p->first_error==TP_NONE){p->first_error=error;p->first_callback=result;
  p->first_register=p->current_register;p->first_write_uncertain=p->write_uncertain;}
 return false;
}
static bool check(struct tim3_preload *p)
{
 struct tim3_preload_proof proof={0};enum board_l_result r;
 if(p->first_error!=TP_NONE)return false;
 r=p->transport.proof(p->transport.context,&proof);
 if(p->first_error!=TP_NONE)return false;
 if(r!=BOARD_L_OK)return fail(p,TP_PROOF_CALLBACK,r);
 if(!proof.valid || proof.epoch!=p->config.epoch || !proof.scope_generation ||
 !proof.exclusive_scope_held || !proof.scope_current || !proof.register_access_qualified ||
 !proof.configuration_stable || !proof.clock_history_qualified || !proof.initialization_qualified ||
 !proof.inhibit_lifecycle_available || (p->requested && !proof.positive_transaction_permitted))
  return fail(p,TP_PROOF,BOARD_L_UNCONFIGURED);
 if(!p->active_scope){
  if(proof.scope_generation<=p->last_scope)return fail(p,TP_SCOPE_REPLAY,BOARD_L_UNCONFIGURED);
  p->active_scope=proof.scope_generation;p->last_scope=proof.scope_generation;
 }else if(proof.scope_generation!=p->active_scope)return fail(p,TP_PROOF,BOARD_L_UNCONFIGURED);
 return true;
}
static bool read_register(struct tim3_preload *p,enum tim3_preload_register reg,uint32_t *value)
{
 enum board_l_result r;p->current_register=reg;*value=0;
 if(!check(p))return false;
 r=p->transport.read(p->transport.context,reg,value);
 if(r!=BOARD_L_OK)return fail(p,TP_READ,r);
 if(!check(p))return false;
 if(reg!=TP_SMCR && reg!=TP_CCMR1 && *value>65535u)return fail(p,TP_STATE,BOARD_L_IO_ERROR);
 return true;
}
static bool profile(struct tim3_preload *p)
{
 unsigned i;
 for(i=0;i<7;++i){uint32_t value,expected;
  if(!tim3_profile_expected(&p->config,(enum tim3_preload_register)i,&expected))return fail(p,TP_CONFIG,BOARD_L_UNCONFIGURED);
  if(!read_register(p,(enum tim3_preload_register)i,&value))return false;
  if(value!=expected)return fail(p,TP_STATE,BOARD_L_IO_ERROR);
 }
 return true;
}
bool tim3_preload_configure(struct tim3_preload *p,const struct tim3_preload_config *c,const struct tim3_preload_transport *t)
{
 if(!p)return false;
 if(p->attempted)return fail(p,TP_REBIND,BOARD_L_UNCONFIGURED);
 p->attempted=true;p->current_register=TP_REGISTER_COUNT;
 if(!tim3_profile_config_valid(c) || !t || !t->proof || !t->read || !t->write_ccr1_halfword)
  return fail(p,TP_CONFIG,BOARD_L_UNCONFIGURED);
 p->config=*c;p->transport=*t;p->configured=true;return true;
}
enum board_l_result tim3_preload_write(void *ctx,uint32_t ccr,struct timer_sink_receipt *receipt)
{
 struct tim3_preload *p=ctx;uint32_t readback;enum board_l_result r;
 if(receipt)*receipt=(struct timer_sink_receipt){0};
 if(!p || !p->configured || p->first_error!=TP_NONE)return BOARD_L_UNCONFIGURED;
 if(!receipt){(void)fail(p,TP_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(p->busy){(void)fail(p,TP_REENTRANT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 p->busy=true;p->active_scope=0;p->requested=ccr;p->current_register=TP_REGISTER_COUNT;
 p->write_attempted=false;p->write_uncertain=false;
 if(ccr>65535u || ccr>p->config.period_ticks || (ccr && (!p->config.positive_limits_qualified ||
 ccr<p->config.positive_min || ccr>p->config.positive_max))){
  (void)fail(p,TP_RANGE,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!profile(p))return BOARD_L_UNCONFIGURED;
 p->current_register=TP_CCR1;if(!check(p))return BOARD_L_UNCONFIGURED;
 p->write_attempted=true;p->write_uncertain=true;
 r=p->transport.write_ccr1_halfword(p->transport.context,(uint16_t)ccr);
 if(r!=BOARD_L_OK){(void)fail(p,TP_WRITE,r);return BOARD_L_UNCONFIGURED;}
 if(!check(p) || !read_register(p,TP_CCR1,&readback))return BOARD_L_UNCONFIGURED;
 if(readback!=ccr){(void)fail(p,TP_READBACK,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
 /* Readback is PRELOAD only; post-check entire fixed profile before receipt. */
 if(!profile(p) || !check(p))return BOARD_L_UNCONFIGURED;
 p->write_uncertain=false;p->busy=false;
 *receipt=(struct timer_sink_receipt){true,ccr};return BOARD_L_OK;
}
