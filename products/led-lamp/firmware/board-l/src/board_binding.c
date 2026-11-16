#include "board_binding.h"
#include <stddef.h>

static void unready(struct lamp_board_binding *b) {
    b->initialized=false; b->zero_accepted=false;
    b->preparation_active=false;b->output_initialized=false;
}
static void force(void *ctx) {
    struct lamp_board_binding *b=ctx;
    if (b && b->bound) b->setup.output.force_off(b->setup.output.context);
}
enum board_l_result lamp_board_bind_graded(struct lamp_board_binding *b,const struct lamp_board_setup *s,
                                          const struct sample_gain_config *gain) {
    struct sample_adapter checked={0};
    if (!b) return BOARD_L_IO_ERROR;
    if (b->bound) {
        unready(b); force(b); return BOARD_L_UNCONFIGURED;
    }
    *b=(struct lamp_board_binding){0};
    if (!s || !s->acquisition.context || !s->output.context ||
        !s->output.initialize_off || !s->output.apply_normalized || !s->output.force_off ||
        sample_adapter_initialize_graded(&checked,&s->samples,&s->acquisition,gain)!=BOARD_L_OK)
        return BOARD_L_UNCONFIGURED;
    b->setup=*s; b->bound=true;
    if(gain){b->gain_config=*gain;b->gain_enabled=true;}
    /* Checked adapter was validation only: actual epoch starts after backend init. */
    return BOARD_L_OK;
}
enum board_l_result lamp_board_bind(struct lamp_board_binding *b,const struct lamp_board_setup *s) {
    return lamp_board_bind_graded(b,s,NULL);
}
enum board_l_result lamp_board_bind_preparation(struct lamp_board_binding *b,
    const struct lamp_board_setup *s,const struct adc_backend *backend,const struct adc_qualification *q) {
    struct adc_preparation checked={0};enum board_l_result r;
    if(!b)return BOARD_L_IO_ERROR;
    if(b->bound){unready(b);force(b);return BOARD_L_UNCONFIGURED;}
    if(adc_begin(&checked,backend,q)!=ADC_RUNNING)return BOARD_L_UNCONFIGURED;
    r=lamp_board_bind(b,s);
    if(r!=BOARD_L_OK)return r;
    b->preparation_enabled=true;b->adc_backend=*backend;b->adc_qualification=*q;
    return BOARD_L_OK;
}
enum board_l_result lamp_board_bind_channel_preparation(struct lamp_board_binding *b,
 const struct lamp_board_setup *setup,const struct adc_backend *adc,const struct adc_qualification *q,
 const struct adc_channel_choice *choice,const struct lamp_adc_field_backend *fields) {
    struct adc_preparation empty={0};struct adc_channel_descriptor descriptor;
    enum board_l_result r;
    if(!b)return BOARD_L_IO_ERROR;
    if(b->bound){unready(b);force(b);return BOARD_L_UNCONFIGURED;}
    if(!fields || !fields->transact ||
       adc_channel_describe(choice,&empty,&descriptor)!=ADC_CHANNEL_VALID_DESCRIPTOR)
        return BOARD_L_UNCONFIGURED;
    r=lamp_board_bind_preparation(b,setup,adc,q);
    if(r!=BOARD_L_OK)return r;
    b->channel_config_enabled=true;b->channel_descriptor=descriptor;b->field_backend=*fields;
    return BOARD_L_OK;
}
static enum board_l_result field_failed(struct lamp_board_binding *b,enum lamp_adc_field_error e) {
    if(b->field_error==LAMP_ADC_FIELD_OK)b->field_error=e;
    adc_abort_channel_configuration(&b->adc);unready(b);return BOARD_L_IO_ERROR;
}
static enum board_l_result advance_fields(struct lamp_board_binding *b) {
    struct adc_reply reply={0};struct adc_masked_field request={0};
    enum lamp_adc_field_operation op;bool wait=false,met=false,readback=false;
    /* Known reset channel baseline: unchanged mode/direction generates no event.
       Skip only that nonexistent wait, never guess a CCRDY event from ALIGN/RES. */
    if(b->field_step==LAMP_ADC_CFGR_CCRDY &&
       !(b->channel_descriptor.cfgr1.value & UINT32_C(0x00200004)))++b->field_step;
    op=(enum lamp_adc_field_operation)b->field_step;
    if(op==LAMP_ADC_CLEAR_BEFORE_CFGR || op==LAMP_ADC_CLEAR_BEFORE_CHANNELS)
        request=(struct adc_masked_field){UINT32_C(0x2000),UINT32_C(0x2000)};
    if(op==LAMP_ADC_WRITE_CFGR || op==LAMP_ADC_READ_CFGR)request=b->channel_descriptor.cfgr1;
    if(op==LAMP_ADC_WRITE_CHANNELS || op==LAMP_ADC_READ_CHANNELS)request=b->channel_descriptor.chselr;
    if(op==LAMP_ADC_WRITE_SMPR || op==LAMP_ADC_READ_SMPR)request=b->channel_descriptor.smpr;
    if(!b->field_backend.transact(b->field_backend.context,op,&request,&reply))
        return field_failed(b,LAMP_ADC_FIELD_CALLBACK);
    if(op==LAMP_ADC_BASELINE || op==LAMP_ADC_FINAL_DISABLED) {
        if(!reply.valid || !reply.met)return field_failed(b,LAMP_ADC_FIELD_BASELINE);
    }
    if(op==LAMP_ADC_CLEARED_BEFORE_CFGR || op==LAMP_ADC_CLEARED_BEFORE_CHANNELS ||
       op==LAMP_ADC_CFGR_CCRDY || op==LAMP_ADC_CHANNELS_CCRDY) {
        if(!reply.valid)return field_failed(b,LAMP_ADC_FIELD_PAYLOAD);
        wait=true;met=((uint32_t)reply.value & UINT32_C(0x2000))!=0;
        if(op==LAMP_ADC_CLEARED_BEFORE_CFGR || op==LAMP_ADC_CLEARED_BEFORE_CHANNELS)met=!met;
    }
    readback=op==LAMP_ADC_READ_CFGR || op==LAMP_ADC_READ_CHANNELS || op==LAMP_ADC_READ_SMPR;
    if(readback && (!reply.valid || (((uint32_t)reply.value & request.mask)!=request.value)))
        return field_failed(b,LAMP_ADC_FIELD_READBACK);
    if(wait) {
        ++b->field_observations;
        if(!met) {
            if(b->field_observations>=b->adc_qualification.observation_budget)
                return field_failed(b,LAMP_ADC_FIELD_TIMEOUT);
            return BOARD_L_PREPARING;
        }
    }
    ++b->field_step;b->field_observations=0;
    if(b->field_step==LAMP_ADC_FIELD_COUNT)b->channel_config_complete=true;
    return BOARD_L_PREPARING;
}
static uint64_t epoch(void *ctx) {
    struct lamp_board_binding *b=ctx;
    return b && b->preparation_enabled && b->preparation_active ? b->preparation_epoch : 0;
}
static enum board_l_result advance_preparation(void *ctx,uint64_t expected) {
    struct lamp_board_binding *b=ctx;enum adc_status s;
    if(!b || !expected || epoch(b)!=expected || !b->output_initialized || !b->zero_accepted)
        return BOARD_L_UNCONFIGURED;
    /* step4 is immediately AFTER disabled interlock readback, BEFORE ADVREGEN. */
    if(b->channel_config_enabled && b->adc.step==4 && !b->channel_config_complete)
        return advance_fields(b);
    s=adc_advance(&b->adc);
    if(s==ADC_FAILED){unready(b);return BOARD_L_IO_ERROR;}
    if(s==ADC_PREPARED_TRIGGER_UNQUALIFIED)return BOARD_L_ACQUISITION_UNQUALIFIED;
    return s==ADC_RUNNING ? BOARD_L_PREPARING : BOARD_L_UNCONFIGURED;
}
struct lamp_app_preparation lamp_board_preparation(void) {
    struct lamp_app_preparation p={epoch,advance_preparation};return p;
}
static enum board_l_result initialize(void *ctx,const struct board_l_config *cfg) {
    struct lamp_board_binding *b=ctx;
    enum board_l_result r;
    if (!b) return BOARD_L_UNCONFIGURED;
    unready(b); b->adapter=(struct sample_adapter){0};
    if (!b->bound || !cfg) return BOARD_L_UNCONFIGURED;
    r=b->setup.output.initialize_off(b->setup.output.context,cfg);
    if (r!=BOARD_L_OK) return r;
    b->output_initialized=true;
    if(b->preparation_enabled) {
        if(b->preparation_epoch==UINT64_MAX){unready(b);return BOARD_L_UNCONFIGURED;}
        ++b->preparation_epoch;b->previous_adc=b->adc;
        b->previous_field_error=b->field_error;b->previous_field_step=b->field_step;
        b->previous_field_observations=b->field_observations;
        b->field_error=LAMP_ADC_FIELD_OK;b->field_step=0;b->field_observations=0;
        b->channel_config_complete=false;
        b->adc=(struct adc_preparation){0};
        if(adc_begin(&b->adc,&b->adc_backend,&b->adc_qualification)!=ADC_RUNNING) {
            unready(b);return BOARD_L_UNCONFIGURED;
        }
        b->preparation_active=true;return BOARD_L_PREPARING;
    }
    r=sample_adapter_initialize_graded(&b->adapter,&b->setup.samples,&b->setup.acquisition,
                                      b->gain_enabled?&b->gain_config:NULL);
    if (r==BOARD_L_OK) b->initialized=true;
    return r;
}
static enum board_l_result read_samples(void *ctx,struct lamp_samples *out) {
    struct lamp_board_binding *b=ctx;
    enum board_l_result r;
    if (out) *out=(struct lamp_samples){0};
    if (!out) {
        if (b) unready(b);
        return BOARD_L_IO_ERROR;
    }
    if (!b || !b->bound || !b->initialized || !b->zero_accepted) return BOARD_L_UNCONFIGURED;
    r=sample_adapter_read(&b->adapter,out);
    if (r!=BOARD_L_OK) { unready(b); *out=(struct lamp_samples){0}; }
    return r;
}
static enum board_l_result apply(void *ctx,uint32_t request) {
    struct lamp_board_binding *b=ctx;
    enum board_l_result r;
    if (!b || !b->bound) return BOARD_L_UNCONFIGURED;
    if (request>LAMP_FULL) { unready(b); return BOARD_L_IO_ERROR; }
    if (request && (!b->initialized || !b->zero_accepted)) return BOARD_L_UNCONFIGURED;
    r=b->setup.output.apply_normalized(b->setup.output.context,request);
    if (r!=BOARD_L_OK) unready(b);
    else if (!request && (b->initialized || (b->preparation_active && b->output_initialized))) b->zero_accepted=true;
    return r;
}
enum board_l_result lamp_board_read_graded(void *ctx,struct lamp_samples *out,struct thermal_gain *gain) {
    struct lamp_board_binding *b=ctx;enum board_l_result r;
    if(out)*out=(struct lamp_samples){0};
    if(gain)*gain=(struct thermal_gain){0};
    if(!out || !gain){if(b)unready(b);return BOARD_L_IO_ERROR;}
    if(!b || !b->bound || !b->initialized || !b->zero_accepted)return BOARD_L_UNCONFIGURED;
    r=sample_adapter_read_graded(&b->adapter,out,gain);
    if(r!=BOARD_L_OK){unready(b);*out=(struct lamp_samples){0};*gain=(struct thermal_gain){0};}
    return r;
}
struct lamp_app_io lamp_board_io(struct lamp_board_binding *b) {
    struct lamp_app_io io={b,initialize,read_samples,apply,force}; return io;
}
