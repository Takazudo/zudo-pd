#ifndef TIM3_ACCESS_H
#define TIM3_ACCESS_H
#include "tim3_preload.h"
struct tim3_access_location {uint32_t address;unsigned width;bool writable;};
bool tim3_access_location(enum tim3_preload_register,struct tim3_access_location *);
/* Explicit seam. RAM tests supply their own implementation. Fixed volatile TU
 * supplies a DIFFERENT implementation which is never linked/run on HOST.
 * API accepts register identity, no caller-selected address/width. */
struct tim3_access_seam {
 void *context;
 enum board_l_result (*read)(void *,enum tim3_preload_register,uint32_t *);
 enum board_l_result (*write_ccr1)(void *,uint16_t);
};
struct tim3_access_evidence {
 struct tim3_preload_proof owner;
 bool fixed_tim3_identity,access_clock_qualified,update_history_qualified;
};
struct tim3_access_provider {
 void *context;
 enum board_l_result (*observe)(void *,struct tim3_access_evidence *);
};
enum tim3_access_error {TA_NONE,TA_CONFIG,TA_REBIND,TA_CONTEXT,TA_REENTRANT,TA_ARGUMENT,
 TA_PROVIDER,TA_PROOF,TA_SCOPE,TA_ORDER,TA_LOCATION,TA_READ,TA_WIDTH,TA_WRITE};
struct tim3_access {
 struct tim3_access *self;struct tim3_access_seam seam;struct tim3_access_provider provider;
 uint64_t epoch,scope;unsigned cursor,tail_queries;
 bool attempted,configured,busy,write_attempted,write_effect_possible;
 enum tim3_access_error first_error;
 enum board_l_result first_result;
 enum tim3_preload_register first_register,current_register;
 bool first_write_effect_possible;
};
bool tim3_access_configure(struct tim3_access *,uint64_t,const struct tim3_access_provider *,const struct tim3_access_seam *);
bool tim3_access_transport(struct tim3_access *,struct tim3_preload_transport *);
/* Target-only factory. Calling returned functions performs volatile accesses;
 * never invoke or link into HOST tests. Does not qualify hardware or lifecycle. */
struct tim3_access_seam tim3_fixed_volatile_seam(void);
#endif
