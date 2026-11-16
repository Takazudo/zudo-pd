#include "ctrl_timer_map.h"
static bool valid(const struct ctrl_timer_config *c) {
    if(!c || !c->configured || c->mode!=CTRL_TIMER_EDGE_UP_PWM1_ACTIVE_HIGH ||
       c->period_ticks<2 || c->period_ticks>65536)return false;
    return !c->positive_endpoints_supplied ||
        (c->positive_min_ccr<=c->positive_full_ccr && c->positive_full_ccr<=c->period_ticks &&
         c->positive_full_ccr<=65535);
}
enum ctrl_timer_status ctrl_timer_initialize(struct ctrl_timer_mapper *m,const struct ctrl_timer_config *c) {
    struct ctrl_timer_mapper next={0};
    if(!m)return CTRL_TIMER_BAD_ARGUMENT;
    if(!valid(c)){*m=next;return CTRL_TIMER_UNCONFIGURED;}
    next.config=*c;next.initialized=true;*m=next;return CTRL_TIMER_CONDITIONAL;
}
enum ctrl_timer_status ctrl_timer_map(const struct ctrl_timer_mapper *m,uint32_t value,struct ctrl_timer_result *out) {
    if(!out)return CTRL_TIMER_BAD_ARGUMENT;
    *out=(struct ctrl_timer_result){0,false,true,false};
    if(!m || !m->initialized || !valid(&m->config))return CTRL_TIMER_UNCONFIGURED;
    if(value>LAMP_FULL)return CTRL_TIMER_BAD_INPUT;
    if(!value){out->ccr_valid=true;return CTRL_TIMER_OFF;}
    if(!m->config.positive_endpoints_supplied)return CTRL_TIMER_POSITIVE_UNQUALIFIED;
    out->ccr=m->config.positive_min_ccr+(uint32_t)(((uint64_t)(value-1)*
        (m->config.positive_full_ccr-m->config.positive_min_ccr))/(LAMP_FULL-1));
    out->ccr_valid=true;out->off_requested=out->ccr==0;
    return CTRL_TIMER_CONDITIONAL;
}
