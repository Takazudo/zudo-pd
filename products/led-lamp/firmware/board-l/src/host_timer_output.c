#include "host_timer_output.h"
#include <stddef.h>

static enum board_l_result failure(struct host_timer_output *a,enum host_timer_error error,
                                   enum board_l_result cause) {
    if(!a->faulted)a->off_dispatched=false; /* one fresh OFF opportunity per fault */
    if(a->first_error==HOST_TIMER_NO_ERROR) {
        a->first_error=error;
        a->first_result=cause==BOARD_L_UNCONFIGURED?BOARD_L_UNCONFIGURED:BOARD_L_IO_ERROR;
    }
    a->faulted=true;a->initialized=false;a->zero_accepted=false;
    a->last=(struct host_timer_report){0};a->last.off_requested=true;
    return a->first_result;
}
static void force_off(void *ctx) {
    struct host_timer_output *a=ctx;
    if(!a)return;
    if(a->last.requested_ccr || a->last.accepted_ccr) {
        a->last=(struct host_timer_report){0};a->zero_accepted=false;
    }
    a->last.off_requested=true;a->last.physical_off_verified=false;
    if(!a->off_dispatched && a->setup.sink.context && a->setup.sink.request_off) {
        a->setup.sink.request_off(a->setup.sink.context);a->off_dispatched=true;
    }
}
static bool complete(const struct host_timer_sink *s) {
    return s->context && s->initialize_off && s->ready && s->write_preload && s->request_off;
}
enum board_l_result host_timer_bind(struct host_timer_output *a,const struct host_timer_setup *setup) {
    struct host_timer_setup copy={0};
    if(!a)return BOARD_L_IO_ERROR;
    if(a->bind_attempted) {
        a->rebind_refused=true;
        (void)failure(a,HOST_TIMER_REBIND_REFUSED,BOARD_L_UNCONFIGURED);
        force_off(a);return a->first_result;
    }
    if(setup)copy=*setup;
    *a=(struct host_timer_output){0};a->bind_attempted=true;a->setup=copy;
    if(!setup || !complete(&copy.sink) || ctrl_timer_initialize(&a->mapper,&copy.mapper)!=CTRL_TIMER_CONDITIONAL)
        return failure(a,HOST_TIMER_CONFIG_ERROR,BOARD_L_UNCONFIGURED);
    a->configured=true;return BOARD_L_OK;
}
static enum board_l_result ready(struct host_timer_output *a) {
    bool observed=false;
    enum board_l_result r=a->setup.sink.ready(a->setup.sink.context,&observed);
    if(r!=BOARD_L_OK || !observed)return failure(a,HOST_TIMER_READINESS_ERROR,r==BOARD_L_OK?BOARD_L_IO_ERROR:r);
    return BOARD_L_OK;
}
static enum board_l_result initialize(void *ctx,const struct board_l_config *cfg) {
    struct host_timer_output *a=ctx;enum board_l_result r;
    if(!a)return BOARD_L_UNCONFIGURED;
    a->previous_epoch_error=a->first_error;a->first_error=HOST_TIMER_NO_ERROR;a->first_result=BOARD_L_OK;
    a->faulted=false;a->initialized=false;a->zero_accepted=false;a->off_dispatched=false;
    a->last=(struct host_timer_report){0};a->last.off_requested=true;
    if(!a->configured || !cfg || ctrl_timer_initialize(&a->mapper,&a->setup.mapper)!=CTRL_TIMER_CONDITIONAL)
        return failure(a,HOST_TIMER_CONFIG_ERROR,BOARD_L_UNCONFIGURED);
    r=a->setup.sink.initialize_off(a->setup.sink.context,cfg);
    if(r!=BOARD_L_OK)return failure(a,HOST_TIMER_INIT_ERROR,r);
    r=ready(a);if(r!=BOARD_L_OK)return r;
    a->initialized=true;return BOARD_L_OK; /* app must still send accepted zero */
}
static enum board_l_result apply(void *ctx,uint32_t value) {
    struct host_timer_output *a=ctx;struct ctrl_timer_result mapped={0};
    struct timer_sink_receipt receipt={0};enum ctrl_timer_status status;enum board_l_result r;
    if(!a)return BOARD_L_UNCONFIGURED;
    if(a->faulted)return a->first_result; /* no repeated failed zero write */
    if(!a->configured || !a->initialized)return failure(a,HOST_TIMER_CONFIG_ERROR,BOARD_L_UNCONFIGURED);
    if(value && !a->zero_accepted)return failure(a,HOST_TIMER_ZERO_REQUIRED,BOARD_L_UNCONFIGURED);
    status=ctrl_timer_map(&a->mapper,value,&mapped);
    if((status!=CTRL_TIMER_OFF && status!=CTRL_TIMER_CONDITIONAL) || !mapped.ccr_valid)
        return failure(a,HOST_TIMER_MAPPING_ERROR,status==CTRL_TIMER_BAD_INPUT?BOARD_L_IO_ERROR:BOARD_L_UNCONFIGURED);
    r=ready(a);if(r!=BOARD_L_OK)return r;
    if(mapped.ccr)a->off_dispatched=false; /* attempted positive may have uncertain effects */
    r=a->setup.sink.write_preload(a->setup.sink.context,mapped.ccr,&receipt);
    if(r!=BOARD_L_OK)return failure(a,HOST_TIMER_WRITE_ERROR,r);
    if(!receipt.accepted || receipt.accepted_ccr!=mapped.ccr)
        return failure(a,HOST_TIMER_RECEIPT_ERROR,BOARD_L_IO_ERROR);
    a->last=(struct host_timer_report){value,mapped.ccr,receipt.accepted_ccr,true,mapped.ccr==0,false};
    if(!mapped.ccr){a->zero_accepted=true;force_off(a);}
    return BOARD_L_OK;
}
struct lamp_output_backend host_timer_backend(struct host_timer_output *a) {
    struct lamp_output_backend b={a,initialize,apply,force_off};return b;
}
