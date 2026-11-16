#ifndef CTRL_TIMER_MAP_H
#define CTRL_TIMER_MAP_H
#include "lamp_control.h"
enum ctrl_timer_mode {CTRL_TIMER_UNSET,CTRL_TIMER_EDGE_UP_PWM1_ACTIVE_HIGH};
struct ctrl_timer_config {
    bool configured;
    enum ctrl_timer_mode mode;
    uint32_t period_ticks; /* ARR+1, NOT normalized brightness */
    bool positive_endpoints_supplied;
    uint32_t positive_min_ccr,positive_full_ccr;
};
struct ctrl_timer_mapper {struct ctrl_timer_config config;bool initialized;};
struct ctrl_timer_result {
    uint32_t ccr;
    bool ccr_valid,off_requested,physical_off_verified;
};
enum ctrl_timer_status {
    CTRL_TIMER_UNCONFIGURED,CTRL_TIMER_OFF,CTRL_TIMER_CONDITIONAL,
    CTRL_TIMER_POSITIVE_UNQUALIFIED,CTRL_TIMER_BAD_INPUT,CTRL_TIMER_BAD_ARGUMENT
};
/* Source-only conditional arithmetic, NEVER an MMIO permission/readiness proof.
   Config copied; exclusive owner/no concurrent external state mutation.
   Endpoints must be explicitly supplied; no physical qualification claimed. */
enum ctrl_timer_status ctrl_timer_initialize(struct ctrl_timer_mapper *,const struct ctrl_timer_config *);
enum ctrl_timer_status ctrl_timer_map(const struct ctrl_timer_mapper *,uint32_t,struct ctrl_timer_result *);
#endif
