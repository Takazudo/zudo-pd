#ifndef TIM3_PRELOAD_H
#define TIM3_PRELOAD_H
#include "host_timer_output.h"
/* Abstract register identities only. Word reads CCMR1/SMCR, halfword reads
 * CR1/DIER/CCER/PSC/ARR/CCR1. Sole write is CCR1 halfword, preserving other
 * registers and any unaddressed high half. No actual bus implementation. */
enum tim3_preload_register {TP_CR1,TP_SMCR,TP_DIER,TP_CCMR1,TP_CCER,TP_PSC,TP_ARR,TP_CCR1,TP_REGISTER_COUNT};
struct tim3_preload_config {
 bool qualified;
 uint64_t epoch;
 uint32_t period_ticks;
 uint16_t psc;
 uint32_t expected_cr1,expected_smcr,expected_dier,expected_ccmr1,expected_ccer;
 bool positive_limits_qualified;
 uint16_t positive_min,positive_max;
};
struct tim3_preload_proof {
 uint64_t epoch,scope_generation;
 bool valid,exclusive_scope_held,scope_current,register_access_qualified;
 bool configuration_stable,clock_history_qualified,initialization_qualified;
 bool inhibit_lifecycle_available,positive_transaction_permitted;
};
struct tim3_preload_transport {
 void *context;
 enum board_l_result (*proof)(void *,struct tim3_preload_proof *);
 enum board_l_result (*read)(void *,enum tim3_preload_register,uint32_t *);
 enum board_l_result (*write_ccr1_halfword)(void *,uint16_t);
};
enum tim3_preload_error {TP_NONE,TP_CONFIG,TP_REBIND,TP_ARGUMENT,TP_REENTRANT,
 TP_RANGE,TP_PROOF_CALLBACK,TP_PROOF,TP_SCOPE_REPLAY,TP_READ,TP_STATE,TP_WRITE,TP_READBACK};
/* Zero initialize once, stable address/contexts, single owner; fields private.
 * No reset/recovery/init/ready/OFF implementation. Existing V31 sink integration
 * needs independent lifecycle providers and one context composition, not a cast.
 * Receipt is only this synchronous preload transaction and must not be reused. */
struct tim3_preload {
 struct tim3_preload_config config;struct tim3_preload_transport transport;
 bool attempted,configured,busy,write_attempted,write_uncertain;
 bool first_write_uncertain;
 uint64_t last_scope,active_scope;
 uint32_t requested;
 enum tim3_preload_register current_register,first_register;
 enum tim3_preload_error first_error;
 enum board_l_result first_callback;
};
bool tim3_preload_configure(struct tim3_preload *,const struct tim3_preload_config *,const struct tim3_preload_transport *);
enum board_l_result tim3_preload_write(void *,uint32_t,struct timer_sink_receipt *);
#endif
