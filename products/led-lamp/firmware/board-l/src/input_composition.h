#ifndef INPUT_COMPOSITION_H
#define INPUT_COMPOSITION_H
#include "acquisition_registers.h"
#include "completed_frame_bridge.h"
struct input_composition_inputs {
 struct adc_channel_choice choice;uint64_t epoch,first_sequence,clock_ticks_per_second;
 struct da_limits limits;
 struct acquisition_register_providers providers;
 struct acquisition_register_transport transport;
 void *owner_context;enum board_l_result (*owner)(void *,struct completed_frame_owner *);
 void *thermal_context;enum board_l_result (*thermal)(void *,uint32_t,struct sample_thermal *);
};
enum input_composition_error {IC_NONE,IC_CONFIG,IC_REBIND,IC_CONTEXT,IC_REENTRANT,IC_ARGUMENT,IC_PROVIDER};
enum input_composition_stage {IC_CONFIGURATION,IC_ACQUIRE,IC_CLOCK,IC_THERMAL};
struct input_composition {
 struct input_composition *self;struct input_composition_inputs inputs;
 struct acquisition_registers registers;struct discontinuous_acquisition producer;
 struct completed_frame_bridge bridge;struct sample_adapter_hooks bridge_hooks;
 bool attempted,configured,busy;
 enum input_composition_error first_error;enum input_composition_stage stage,first_stage;
 enum board_l_result first_result;
};
/* Zero-init once/final address; provider lifetimes/exclusion externally held.
 * One choice/epoch/scope is reused; same external clock feeds register guard,
 * producer and bridge. Declared tick frequency is coherence, not measurement.
 * No provider executes during configure; no default qualifiers/scope/recovery. */
bool input_composition_configure(struct input_composition *,const struct input_composition_inputs *);
bool input_composition_hooks(struct input_composition *,struct sample_adapter_hooks *);
#endif
