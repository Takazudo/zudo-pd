#ifndef NOISE_STAGE_H
#define NOISE_STAGE_H
#include "lamp_control.h"

struct noise_config {
    bool configured;
    int32_t noise_min, noise_max;
    uint32_t denominator, slow_alpha, fast_alpha, slow_depth, fast_depth;
};
struct noise_pair { int32_t slow, fast; bool complete; };
/* false may still have written plausible values; they MUST be discarded. */
struct noise_source { void *context; bool (*read_pair)(void *, struct noise_pair *); };
struct noise_input {
    uint32_t base;
    bool base_valid, startup_complete, frame_qualified;
};
struct noise_output { uint32_t value; bool valid; };
enum noise_status {
    NOISE_UNCONFIGURED, NOISE_READY, NOISE_VALID, NOISE_OFF, NOISE_INELIGIBLE,
    NOISE_INPUT_INVALID, NOISE_RNG_ERROR, NOISE_BAD_ARGUMENT
};
struct noise_stage {
    struct noise_config config;
    struct noise_source source;
    int32_t slow_state, fast_state;
    bool initialized;
};
/* Explicit config, no RNG/seed or physical defaults. Zero initialize; single
   owner; callbacks cannot mutate this object. Reinitialization copies settings.
   See ../NUMERIC-CONTRACT.md for signed toward-zero rounding and units.
   Standalone stage only: does not set eligibility or call core/app/output. */
enum noise_status noise_initialize(struct noise_stage *, const struct noise_config *,
                                   const struct noise_source *);
void noise_reset(struct noise_stage *); /* filter reset only, no readiness grant */
enum noise_status noise_step(struct noise_stage *, const struct noise_input *, struct noise_output *);
#endif
