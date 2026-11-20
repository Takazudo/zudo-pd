#ifndef OUTPUT_COMPOSITION_H
#define OUTPUT_COMPOSITION_H
#include "tim3_access.h"
#include "tim3_readiness.h"
#include "preload_lifecycle.h"
struct output_composition_inputs {
 struct tim3_preload_config profile;struct ctrl_timer_config mapper;
 struct tim3_access_provider access_proof;struct tim3_access_seam access_seam;
 struct tim3_readiness_io readiness;
 void *owner_context;enum board_l_result (*owner)(void *,struct preload_lifecycle_owner *);
 void *init_context;enum board_l_result (*initialize_off)(void *,const struct board_l_config *);
 void *inhibit_context;void (*request_off)(void *);
};
enum output_composition_error {OC_NONE,OC_CONFIG,OC_REBIND,OC_CONTEXT,OC_REENTRANT,OC_OUTPUT};
struct output_composition {
 struct output_composition *self;struct output_composition_inputs inputs;
 struct tim3_access access;struct tim3_readiness readiness;
 struct preload_lifecycle lifecycle;struct host_timer_output output;
 bool attempted,configured,busy,inhibit_busy;
 enum output_composition_error first_error;enum board_l_result first_result;
};
/* Zero-init/final stable address, immutable lifetime, single exclusive owner.
 * All real providers caller-owned and explicit. No configure-time callbacks,
 * default values, volatile factory invocation, scope creation or reset/recovery. */
bool output_composition_configure(struct output_composition *,const struct output_composition_inputs *);
bool output_composition_backend(struct output_composition *,struct lamp_output_backend *);
#endif
