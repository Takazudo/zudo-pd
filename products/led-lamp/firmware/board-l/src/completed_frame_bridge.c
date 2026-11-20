#include "completed_frame_bridge.h"
#include <stddef.h>
static void failed(struct completed_frame_bridge *b,enum completed_bridge_error error,
                   enum completed_bridge_stage stage,enum board_l_result result,uint64_t owner)
{
    if(b && b->first_error==COMPLETED_BRIDGE_NO_ERROR){
        b->first_error=error;b->first_stage=stage;b->first_callback_result=result;b->first_observed_owner=owner;
    }
}
static bool owner_valid(struct completed_frame_bridge *b,enum completed_bridge_stage stage)
{
    struct completed_frame_owner owner={0};enum board_l_result r;
    if(!b || b->first_error!=COMPLETED_BRIDGE_NO_ERROR)return false;
    if(!b->configured){failed(b,COMPLETED_BRIDGE_CONFIG,stage,BOARD_L_UNCONFIGURED,0);return false;}
    r=b->providers.owner(b->providers.owner_context,&owner);
    if(r!=BOARD_L_OK){failed(b,COMPLETED_BRIDGE_OWNER_CALLBACK,stage,r,owner.epoch);return false;}
    if(!owner.valid){failed(b,COMPLETED_BRIDGE_OWNER_INVALID,stage,r,owner.epoch);return false;}
    if(owner.epoch!=b->epoch){failed(b,COMPLETED_BRIDGE_OWNER_EPOCH,stage,r,owner.epoch);return false;}
    if(!owner.exclusive_owner || !owner.read_scope_held || !owner.consumer_epoch_valid){
        failed(b,COMPLETED_BRIDGE_OWNER_SCOPE,stage,r,owner.epoch);return false;
    }
    return true;
}
static enum board_l_result acquire(void *context,struct sample_frame *out)
{
    struct completed_frame_bridge *b=context;struct adc_completed_frame input={0};struct sample_frame decoded={0};
    if(out)*out=(struct sample_frame){0};
    if(!b || !out){failed(b,COMPLETED_BRIDGE_ARGUMENT,COMPLETED_BRIDGE_ACQUIRE_STAGE,BOARD_L_IO_ERROR,0);return BOARD_L_IO_ERROR;}
    if(b->first_error!=COMPLETED_BRIDGE_NO_ERROR)return BOARD_L_UNCONFIGURED;
    b->producer_attempted=false;b->decode_attempted=false;
    b->producer_result=BOARD_L_UNCONFIGURED;b->decode_result=ADC_FRAME_DECODE_ARGUMENT;
    if(!owner_valid(b,COMPLETED_BRIDGE_ACQUIRE_STAGE))return BOARD_L_UNCONFIGURED;
    b->producer_attempted=true;
    b->producer_result=b->providers.produce(b->providers.producer_context,&input);
    if(b->producer_result!=BOARD_L_OK){
        failed(b,COMPLETED_BRIDGE_PRODUCER,COMPLETED_BRIDGE_ACQUIRE_STAGE,b->producer_result,0);
        return b->producer_result;
    }
    b->decode_attempted=true;
    b->decode_result=adc_decode_completed_frame(&b->choice,b->epoch,&input,&decoded);
    if(b->decode_result!=ADC_FRAME_DECODE_OK){
        failed(b,COMPLETED_BRIDGE_DECODE,COMPLETED_BRIDGE_ACQUIRE_STAGE,b->producer_result,0);
        return BOARD_L_IO_ERROR;
    }
    if(!owner_valid(b,COMPLETED_BRIDGE_ACQUIRE_STAGE))return BOARD_L_UNCONFIGURED;
    *out=decoded;return BOARD_L_OK;
}
static enum board_l_result clock_read(void *context,struct sample_clock *out)
{
    struct completed_frame_bridge *b=context;struct sample_clock clock={0};enum board_l_result r;
    if(out)*out=(struct sample_clock){0};
    if(!b || !out){failed(b,COMPLETED_BRIDGE_ARGUMENT,COMPLETED_BRIDGE_CLOCK_STAGE,BOARD_L_IO_ERROR,0);return BOARD_L_IO_ERROR;}
    if(!owner_valid(b,COMPLETED_BRIDGE_CLOCK_STAGE))return BOARD_L_UNCONFIGURED;
    r=b->providers.clock(b->providers.clock_context,&clock);
    if(r!=BOARD_L_OK){failed(b,COMPLETED_BRIDGE_CLOCK,COMPLETED_BRIDGE_CLOCK_STAGE,r,0);return r;}
    if(!owner_valid(b,COMPLETED_BRIDGE_CLOCK_STAGE))return BOARD_L_UNCONFIGURED;
    *out=clock;return BOARD_L_OK;
}
static enum board_l_result thermal_read(void *context,uint32_t raw,struct sample_thermal *out)
{
    struct completed_frame_bridge *b=context;struct sample_thermal thermal={0};enum board_l_result r;
    if(out)*out=(struct sample_thermal){0};
    if(!b || !out){failed(b,COMPLETED_BRIDGE_ARGUMENT,COMPLETED_BRIDGE_THERMAL_STAGE,BOARD_L_IO_ERROR,0);return BOARD_L_IO_ERROR;}
    if(!owner_valid(b,COMPLETED_BRIDGE_THERMAL_STAGE))return BOARD_L_UNCONFIGURED;
    r=b->providers.thermal(b->providers.thermal_context,raw,&thermal);
    if(r!=BOARD_L_OK){failed(b,COMPLETED_BRIDGE_THERMAL,COMPLETED_BRIDGE_THERMAL_STAGE,r,0);return r;}
    if(!owner_valid(b,COMPLETED_BRIDGE_THERMAL_STAGE))return BOARD_L_UNCONFIGURED;
    *out=thermal;return BOARD_L_OK;
}
bool completed_frame_bridge_configure(struct completed_frame_bridge *b,
    const struct adc_channel_choice *choice,uint64_t epoch,const struct completed_frame_providers *p)
{
    struct adc_preparation neutral={0};struct adc_channel_descriptor descriptor;
    if(!b)return false;
    if(b->attempted || b->first_error!=COMPLETED_BRIDGE_NO_ERROR){
        b->rebind_refused=true;failed(b,COMPLETED_BRIDGE_REBIND,COMPLETED_BRIDGE_CONFIGURATION,BOARD_L_UNCONFIGURED,0);return false;
    }
    b->attempted=true;
    if(!epoch || !p || !p->owner_context || !p->owner || !p->producer_context || !p->produce ||
       !p->clock_context || !p->clock || !p->thermal_context || !p->thermal ||
       adc_channel_describe(choice,&neutral,&descriptor)!=ADC_CHANNEL_VALID_DESCRIPTOR){
        failed(b,COMPLETED_BRIDGE_CONFIG,COMPLETED_BRIDGE_CONFIGURATION,BOARD_L_UNCONFIGURED,0);return false;
    }
    b->choice=*choice;b->epoch=epoch;b->providers=*p;b->configured=true;return true;
}
bool completed_frame_bridge_hooks(struct completed_frame_bridge *b,struct sample_adapter_hooks *out)
{
    if(out)*out=(struct sample_adapter_hooks){0};
    if(!b || !out || !b->configured || b->first_error!=COMPLETED_BRIDGE_NO_ERROR)return false;
    *out=(struct sample_adapter_hooks){b,acquire,clock_read,thermal_read};return true;
}
