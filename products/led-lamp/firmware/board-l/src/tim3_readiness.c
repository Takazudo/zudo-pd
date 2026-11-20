#include "tim3_readiness.h"
#include "tim3_access.h"
static bool fail(struct tim3_readiness *r,enum tim3_readiness_error e,enum board_l_result result)
{
 if(r->first_error==TR_NONE){r->first_error=e;r->first_result=result;r->first_register=r->current_register;}
 return false;
}
static bool proof(struct tim3_readiness *r)
{
 struct tim3_readiness_proof p={0};enum board_l_result result;
 if(r->first_error!=TR_NONE)return false;
 result=r->io.proof(r->io.proof_context,&p);
 if(r->first_error!=TR_NONE)return false;
 if(result!=BOARD_L_OK)return fail(r,TR_PROOF_CALLBACK,result);
 if(!p.valid || !p.current || !p.exclusive_held || p.epoch!=r->config.epoch || !p.scope ||
 !p.initialization_qualified || !p.inhibit_available || !p.access_clock_qualified ||
 !p.shadow_update_history_qualified)return fail(r,TR_PROOF,BOARD_L_UNCONFIGURED);
 if(!r->scope){if(p.scope<r->last_scope)return fail(r,TR_SCOPE,BOARD_L_UNCONFIGURED);r->scope=p.scope;}
 else if(p.scope!=r->scope)return fail(r,TR_SCOPE,BOARD_L_UNCONFIGURED);
 return true;
}
bool tim3_readiness_configure(struct tim3_readiness *r,const struct tim3_preload_config *c,const struct tim3_readiness_io *io)
{
 if(!r)return false;
 if(r->attempted)return fail(r,TR_REBIND,BOARD_L_UNCONFIGURED);
 r->attempted=true;r->self=r;r->current_register=TP_REGISTER_COUNT;
 if(!tim3_profile_config_valid(c) || !io || !io->proof || !io->read)
  return fail(r,TR_CONFIG,BOARD_L_UNCONFIGURED);
 r->config=*c;r->io=*io;r->configured=true;return true;
}
enum board_l_result tim3_readiness_observe(void *ctx,bool *out)
{
 struct tim3_readiness *r=ctx;unsigned i;
 if(out)*out=false;
 if(!r)return BOARD_L_UNCONFIGURED;
 if(r->self!=r){(void)fail(r,TR_CONTEXT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!r->configured || r->first_error!=TR_NONE)return BOARD_L_UNCONFIGURED;
 if(r->busy){(void)fail(r,TR_REENTRANT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 if(!out){(void)fail(r,TR_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 r->busy=true;r->scope=0;r->current_register=TP_REGISTER_COUNT;
 if(!proof(r))return BOARD_L_UNCONFIGURED;
 for(i=0;i<7;++i){
  struct tim3_access_location location;uint32_t expected=0,value=0;enum board_l_result result;
  r->current_register=(enum tim3_preload_register)i;
  if(!tim3_profile_expected(&r->config,r->current_register,&expected) ||
   !tim3_access_location(r->current_register,&location)){
   (void)fail(r,TR_CONFIG,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
  if(!proof(r))return BOARD_L_UNCONFIGURED;
  result=r->io.read(r->io.read_context,r->current_register,&value);
  if(result!=BOARD_L_OK){(void)fail(r,TR_READ,result);return BOARD_L_UNCONFIGURED;}
  if(!proof(r))return BOARD_L_UNCONFIGURED;
  if(location.width==2 && value>65535u){(void)fail(r,TR_WIDTH,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
  if(value!=expected){(void)fail(r,TR_PROFILE,BOARD_L_IO_ERROR);return BOARD_L_UNCONFIGURED;}
 }
 r->last_scope=r->scope;r->busy=false;*out=true;return BOARD_L_OK;
}
