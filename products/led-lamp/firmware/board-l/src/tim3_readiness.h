#ifndef TIM3_READINESS_H
#define TIM3_READINESS_H
#include "tim3_profile.h"
struct tim3_readiness_proof {
 uint64_t epoch,scope;
 bool valid,current,exclusive_held,initialization_qualified,inhibit_available;
 bool access_clock_qualified,shadow_update_history_qualified;
};
struct tim3_readiness_io {
 void *proof_context;enum board_l_result (*proof)(void *,struct tim3_readiness_proof *);
 void *read_context;enum board_l_result (*read)(void *,enum tim3_preload_register,uint32_t *);
};
enum tim3_readiness_error {TR_NONE,TR_CONFIG,TR_REBIND,TR_CONTEXT,TR_REENTRANT,
 TR_ARGUMENT,TR_PROOF_CALLBACK,TR_PROOF,TR_SCOPE,TR_READ,TR_WIDTH,TR_PROFILE};
struct tim3_readiness {
 struct tim3_readiness *self;struct tim3_preload_config config;struct tim3_readiness_io io;
 uint64_t scope,last_scope;bool attempted,configured,busy;
 enum tim3_readiness_error first_error;enum board_l_result first_result;
 enum tim3_preload_register current_register,first_register;
};
/* Pure configuration; all provider lifetimes/exclusion external. No access to
 * V62 write-transaction transport/state. Same held scope may span multiple
 * observations, but every proof is queried fresh, current and epoch-consistent. */
bool tim3_readiness_configure(struct tim3_readiness *,const struct tim3_preload_config *,const struct tim3_readiness_io *);
enum board_l_result tim3_readiness_observe(void *,bool *);
#endif
