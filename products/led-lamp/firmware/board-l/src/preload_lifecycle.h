#ifndef PRELOAD_LIFECYCLE_H
#define PRELOAD_LIFECYCLE_H
#include "tim3_preload.h"
struct preload_lifecycle_owner {
 uint64_t epoch;
 bool valid,exclusive_lifecycle_scope,current,consumer_epoch_valid;
};
struct preload_lifecycle_providers {
 void *owner_context;enum board_l_result (*owner)(void *,struct preload_lifecycle_owner *);
 void *init_context;enum board_l_result (*initialize_off)(void *,const struct board_l_config *);
 void *ready_context;enum board_l_result (*ready)(void *,bool *);
 void *inhibit_context;void (*request_off)(void *);
};
enum preload_lifecycle_error {PL_NONE,PL_CONFIG,PL_REBIND,PL_CONTEXT,PL_REENTRANT,
 PL_OWNER_CALLBACK,PL_OWNER,PL_INIT,PL_READY,PL_PRELOAD,PL_TERMINAL,PL_ARGUMENT};
struct preload_lifecycle {
 struct preload_lifecycle *self;
 struct preload_lifecycle_providers providers;
 struct tim3_preload preload;
 uint64_t epoch;
 bool attempted,configured,busy,inhibit_busy;
 enum preload_lifecycle_error first_error;
 enum board_l_result first_result;
 bool first_write_possible;
};
/* Once-only, zero-init, fixed-address exclusive owner; all contexts nonnull and
 * outlive every sink copy. Configure is structural, no operational callbacks.
 * No subadapter reset/recovery/new epoch/scope generation is implemented. */
bool preload_lifecycle_configure(struct preload_lifecycle *,const struct tim3_preload_config *,
 const struct tim3_preload_transport *,const struct preload_lifecycle_providers *);
bool preload_lifecycle_sink(struct preload_lifecycle *,struct host_timer_sink *);
#endif
