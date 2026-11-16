#include "output_composition.h"
static bool fail(struct output_composition *o,enum output_composition_error e,enum board_l_result r)
{
 if(o->first_error==OC_NONE){o->first_error=e;o->first_result=r;}
 return false;
}
static bool valid(struct output_composition *o,const struct output_composition_inputs *i)
{
 struct ctrl_timer_mapper checked={0};uint32_t first_positive;
 if(!i || !tim3_profile_config_valid(&i->profile) ||
 ctrl_timer_initialize(&checked,&i->mapper)!=CTRL_TIMER_CONDITIONAL ||
 i->mapper.period_ticks!=i->profile.period_ticks ||
 !i->access_proof.observe || !i->access_proof.context || !i->access_seam.read || !i->access_seam.write_ccr1 ||
 !i->readiness.proof || !i->readiness.proof_context || !i->readiness.read || !i->readiness.read_context ||
 i->readiness.read_context==&o->access || !i->owner || !i->owner_context ||
 !i->initialize_off || !i->init_context || !i->request_off || !i->inhibit_context)return false;
 /* Pure coherence: all potentially nonzero mapped CCRs must fit explicit
  * preload permission interval. No endpoint/positive floor is selected here. */
 if(i->mapper.positive_endpoints_supplied && i->mapper.positive_full_ccr){
  first_positive=i->mapper.positive_min_ccr?i->mapper.positive_min_ccr:1u;
  if(!i->profile.positive_limits_qualified || first_positive<i->profile.positive_min ||
   i->mapper.positive_full_ccr>i->profile.positive_max)return false;
 }
 return true;
}
bool output_composition_configure(struct output_composition *o,const struct output_composition_inputs *i)
{
 struct tim3_preload_transport transport;struct preload_lifecycle_providers providers;
 struct host_timer_setup setup;
 if(!o)return false;
 if(o->attempted)return fail(o,OC_REBIND,BOARD_L_UNCONFIGURED);
 o->attempted=true;o->self=o;
 if(!valid(o,i))return fail(o,OC_CONFIG,BOARD_L_UNCONFIGURED);
 o->inputs=*i;
 if(!tim3_access_configure(&o->access,i->profile.epoch,&i->access_proof,&i->access_seam) ||
 !tim3_access_transport(&o->access,&transport) ||
 !tim3_readiness_configure(&o->readiness,&i->profile,&i->readiness))return fail(o,OC_CONFIG,BOARD_L_UNCONFIGURED);
 providers=(struct preload_lifecycle_providers){i->owner_context,i->owner,i->init_context,i->initialize_off,
 &o->readiness,tim3_readiness_observe,i->inhibit_context,i->request_off};
 if(!preload_lifecycle_configure(&o->lifecycle,&i->profile,&transport,&providers))return fail(o,OC_CONFIG,BOARD_L_UNCONFIGURED);
 setup.mapper=i->mapper;
 if(!preload_lifecycle_sink(&o->lifecycle,&setup.sink) || host_timer_bind(&o->output,&setup)!=BOARD_L_OK)
  return fail(o,OC_CONFIG,BOARD_L_UNCONFIGURED);
 o->configured=true;return true;
}
static bool enter(struct output_composition *o)
{
 if(!o)return false;
 if(o->self!=o)return fail(o,OC_CONTEXT,BOARD_L_UNCONFIGURED);
 if(!o->configured || o->first_error!=OC_NONE)return false;
 if(o->busy)return fail(o,OC_REENTRANT,BOARD_L_UNCONFIGURED);
 o->busy=true;return true;
}
static enum board_l_result finish(struct output_composition *o,enum board_l_result r)
{
 if(o->first_error!=OC_NONE)return BOARD_L_UNCONFIGURED;
 if(r!=BOARD_L_OK){(void)fail(o,OC_OUTPUT,r);return r;}
 o->busy=false;return BOARD_L_OK;
}
static enum board_l_result initialize(void *ctx,const struct board_l_config *cfg)
{
 struct output_composition *o=ctx;struct lamp_output_backend backend;
 if(!enter(o))return BOARD_L_UNCONFIGURED;
 backend=host_timer_backend(&o->output);return finish(o,backend.initialize_off(backend.context,cfg));
}
static enum board_l_result apply(void *ctx,uint32_t value)
{
 struct output_composition *o=ctx;struct lamp_output_backend backend;
 if(!enter(o))return BOARD_L_UNCONFIGURED;
 backend=host_timer_backend(&o->output);return finish(o,backend.apply_normalized(backend.context,value));
}
static void inhibit(void *ctx)
{
 struct output_composition *o=ctx;struct lamp_output_backend backend;
 if(!o)return;
 if(o->self!=o){(void)fail(o,OC_CONTEXT,BOARD_L_UNCONFIGURED);return;}
 if(!o->configured)return;
 if(o->inhibit_busy){(void)fail(o,OC_REENTRANT,BOARD_L_UNCONFIGURED);return;}
 o->inhibit_busy=true;backend=host_timer_backend(&o->output);backend.force_off(backend.context);o->inhibit_busy=false;
}
bool output_composition_backend(struct output_composition *o,struct lamp_output_backend *out)
{
 if(out)*out=(struct lamp_output_backend){0};
 if(!o || !out || o->self!=o || !o->configured)return false;
 *out=(struct lamp_output_backend){o,initialize,apply,inhibit};return true;
}
