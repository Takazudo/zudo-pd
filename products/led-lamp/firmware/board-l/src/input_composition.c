#include "input_composition.h"
static bool fail(struct input_composition *i,enum input_composition_error error,enum board_l_result result)
{
 if(i->first_error==IC_NONE){i->first_error=error;i->first_result=result;i->first_stage=i->stage;}
 return false;
}
bool input_composition_configure(struct input_composition *i,const struct input_composition_inputs *in)
{
 struct da_io io;struct completed_frame_providers providers;
 if(!i)return false;
 if(i->attempted)return fail(i,IC_REBIND,BOARD_L_UNCONFIGURED);
 i->attempted=true;i->self=i;i->stage=IC_CONFIGURATION;
 if(!in || !in->epoch || !in->clock_ticks_per_second || in->clock_ticks_per_second!=in->limits.ticks_per_second ||
 !in->providers.proof || !in->providers.proof_context || !in->providers.clock || !in->providers.clock_context ||
 !in->transport.read_word || !in->transport.store_word || !in->owner || !in->owner_context ||
 !in->thermal || !in->thermal_context)return fail(i,IC_CONFIG,BOARD_L_UNCONFIGURED);
 i->inputs=*in;
 if(!acquisition_registers_configure(&i->registers,&in->choice,in->epoch,in->limits.scope_until,&in->providers,&in->transport) ||
 !acquisition_registers_io(&i->registers,&io) ||
 !da_configure(&i->producer,&in->choice,in->epoch,in->first_sequence,&in->limits,&io))
  return fail(i,IC_CONFIG,BOARD_L_UNCONFIGURED);
 providers=(struct completed_frame_providers){in->owner_context,in->owner,&i->producer,da_produce,
 in->providers.clock_context,in->providers.clock,in->thermal_context,in->thermal};
 if(!completed_frame_bridge_configure(&i->bridge,&in->choice,in->epoch,&providers) ||
 !completed_frame_bridge_hooks(&i->bridge,&i->bridge_hooks))return fail(i,IC_CONFIG,BOARD_L_UNCONFIGURED);
 i->configured=true;return true;
}
static bool enter(struct input_composition *i,enum input_composition_stage stage)
{
 if(!i)return false;
 if(i->self!=i)return fail(i,IC_CONTEXT,BOARD_L_UNCONFIGURED);
 if(!i->configured || i->first_error!=IC_NONE)return false;
 if(i->busy)return fail(i,IC_REENTRANT,BOARD_L_UNCONFIGURED);
 i->busy=true;i->stage=stage;return true;
}
static enum board_l_result finish(struct input_composition *i,enum board_l_result result)
{
 if(i->first_error!=IC_NONE)return BOARD_L_UNCONFIGURED;
 if(result!=BOARD_L_OK){(void)fail(i,IC_PROVIDER,result);return result;}
 i->busy=false;return BOARD_L_OK;
}
static enum board_l_result acquire(void *ctx,struct sample_frame *out)
{
 struct input_composition *i=ctx;struct sample_frame local={0};enum board_l_result r;
 if(out)*out=(struct sample_frame){0};
 if(!enter(i,IC_ACQUIRE))return BOARD_L_UNCONFIGURED;
 if(!out){(void)fail(i,IC_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 r=finish(i,i->bridge_hooks.acquire(i->bridge_hooks.context,&local));
 if(r==BOARD_L_OK)*out=local;
 return r;
}
static enum board_l_result clock_read(void *ctx,struct sample_clock *out)
{
 struct input_composition *i=ctx;struct sample_clock local={0};enum board_l_result r;
 if(out)*out=(struct sample_clock){0};
 if(!enter(i,IC_CLOCK))return BOARD_L_UNCONFIGURED;
 if(!out){(void)fail(i,IC_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 r=finish(i,i->bridge_hooks.clock(i->bridge_hooks.context,&local));
 if(r==BOARD_L_OK)*out=local;
 return r;
}
static enum board_l_result thermal(void *ctx,uint32_t raw,struct sample_thermal *out)
{
 struct input_composition *i=ctx;struct sample_thermal local={0};enum board_l_result r;
 if(out)*out=(struct sample_thermal){0};
 if(!enter(i,IC_THERMAL))return BOARD_L_UNCONFIGURED;
 if(!out){(void)fail(i,IC_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 r=finish(i,i->bridge_hooks.thermal(i->bridge_hooks.context,raw,&local));
 if(r==BOARD_L_OK)*out=local;
 return r;
}
bool input_composition_hooks(struct input_composition *i,struct sample_adapter_hooks *out)
{
 if(out)*out=(struct sample_adapter_hooks){0};
 if(!i || !out || i->self!=i || !i->configured)return false;
 *out=(struct sample_adapter_hooks){i,acquire,clock_read,thermal};return true;
}
