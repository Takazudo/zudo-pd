#include "tim3_access.h"
static bool fail(struct tim3_access *a,enum tim3_access_error e,enum board_l_result r)
{
 if(a->first_error==TA_NONE){a->first_error=e;a->first_result=r;a->first_register=a->current_register;
 a->first_write_effect_possible=a->write_effect_possible;}
 return false;
}
static bool enter(struct tim3_access *a)
{
 if(!a)return false;
 if(a->self!=a)return fail(a,TA_CONTEXT,BOARD_L_UNCONFIGURED);
 if(!a->configured || a->first_error!=TA_NONE)return false;
 if(a->busy)return fail(a,TA_REENTRANT,BOARD_L_UNCONFIGURED);
 a->busy=true;return true;
}
static bool evidence(struct tim3_access *a,struct tim3_preload_proof *out)
{
 struct tim3_access_evidence e={0};enum board_l_result r;
 if(a->first_error!=TA_NONE)return false;
 r=a->provider.observe(a->provider.context,&e);
 if(a->first_error!=TA_NONE)return false;
 if(r!=BOARD_L_OK)return fail(a,TA_PROVIDER,r);
 if(!e.fixed_tim3_identity || !e.access_clock_qualified || !e.update_history_qualified ||
 !e.owner.valid || e.owner.epoch!=a->epoch || !e.owner.scope_generation ||
 !e.owner.exclusive_scope_held || !e.owner.scope_current || !e.owner.register_access_qualified ||
 !e.owner.configuration_stable || !e.owner.clock_history_qualified || !e.owner.initialization_qualified ||
 !e.owner.inhibit_lifecycle_available)return fail(a,TA_PROOF,BOARD_L_UNCONFIGURED);
 if(e.owner.scope_generation!=a->scope){
  if(e.owner.scope_generation<=a->scope || (a->scope && (a->cursor!=16 || a->tail_queries<2)))
   return fail(a,TA_SCOPE,BOARD_L_UNCONFIGURED);
  a->scope=e.owner.scope_generation;a->cursor=0;a->tail_queries=0;a->write_attempted=false;a->write_effect_possible=false;
 }
 if(out)*out=e.owner;
 return true;
}
static enum board_l_result query(void *ctx,struct tim3_preload_proof *out)
{
 struct tim3_access *a=ctx;
 if(out)*out=(struct tim3_preload_proof){0};
 if(!enter(a))return BOARD_L_UNCONFIGURED;
 if(!out){(void)fail(a,TA_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!evidence(a,out))return BOARD_L_UNCONFIGURED;
 /* V60 post-last-read proof and final receipt proof must finish in this scope. */
 if(a->cursor==16 && a->tail_queries<2)++a->tail_queries;
 a->busy=false;return BOARD_L_OK;
}
static enum board_l_result read_access(void *ctx,enum tim3_preload_register reg,uint32_t *out)
{
 struct tim3_access *a=ctx;struct tim3_access_location location;enum board_l_result r;
 uint32_t value=0;unsigned expected;
 if(out)*out=0;
 if(!enter(a))return BOARD_L_UNCONFIGURED;
 a->current_register=reg;
 if(!out){(void)fail(a,TA_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!tim3_access_location(reg,&location) || (location.width!=2 && location.width!=4) || location.address%location.width){
  (void)fail(a,TA_LOCATION,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!evidence(a,0))return BOARD_L_UNCONFIGURED;
 expected=a->cursor<7?a->cursor:a->cursor==8?TP_CCR1:a->cursor>=9 && a->cursor<16?a->cursor-9:TP_REGISTER_COUNT;
 if((unsigned)reg!=expected){(void)fail(a,TA_ORDER,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 r=a->seam.read(a->seam.context,reg,&value);
 if(r!=BOARD_L_OK){(void)fail(a,TA_READ,r);return BOARD_L_UNCONFIGURED;}
 if(!evidence(a,0))return BOARD_L_UNCONFIGURED;
 if(location.width==2 && value>65535u){(void)fail(a,TA_WIDTH,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
 ++a->cursor;*out=value;a->busy=false;return BOARD_L_OK;
}
static enum board_l_result write_access(void *ctx,uint16_t value)
{
 struct tim3_access *a=ctx;struct tim3_access_location location;struct tim3_preload_proof p;
 enum board_l_result r;
 if(!enter(a))return BOARD_L_UNCONFIGURED;
 a->current_register=TP_CCR1;
 if(!evidence(a,&p))return BOARD_L_UNCONFIGURED;
 if(a->cursor!=7 || (value && !p.positive_transaction_permitted)){
  (void)fail(a,TA_ORDER,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!tim3_access_location(TP_CCR1,&location) || !location.writable || location.width!=2 || location.address%2){
  (void)fail(a,TA_LOCATION,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 a->write_attempted=true;a->write_effect_possible=true;
 r=a->seam.write_ccr1(a->seam.context,value);
 if(r!=BOARD_L_OK){(void)fail(a,TA_WRITE,r);return BOARD_L_UNCONFIGURED;}
 if(!evidence(a,0))return BOARD_L_UNCONFIGURED;
 ++a->cursor;a->busy=false;return BOARD_L_OK;
}
bool tim3_access_configure(struct tim3_access *a,uint64_t epoch,const struct tim3_access_provider *p,const struct tim3_access_seam *s)
{
 if(!a)return false;
 if(a->attempted)return fail(a,TA_REBIND,BOARD_L_UNCONFIGURED);
 a->attempted=true;a->self=a;a->current_register=TP_REGISTER_COUNT;
 if(!epoch || !p || !p->observe || !s || !s->read || !s->write_ccr1)return fail(a,TA_CONFIG,BOARD_L_UNCONFIGURED);
 a->epoch=epoch;a->provider=*p;a->seam=*s;a->configured=true;return true;
}
bool tim3_access_transport(struct tim3_access *a,struct tim3_preload_transport *out)
{
 if(out)*out=(struct tim3_preload_transport){0};
 if(!a || !out || a->self!=a || !a->configured)return false;
 *out=(struct tim3_preload_transport){a,query,read_access,write_access};return true;
}
