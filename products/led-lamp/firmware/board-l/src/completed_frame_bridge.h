#ifndef COMPLETED_FRAME_BRIDGE_H
#define COMPLETED_FRAME_BRIDGE_H
#include "adc_completed_frame.h"
/* Independent current-owner proof, NOT copied from the completed frame.
 * Scope must cover the ENTIRE sample_adapter read, not only this callback:
 * nonreentrant owner, no epoch/consumer rebind, queued-old-frame discard at change.
 * Existing adapter has no reset notification to hooks; external consumer_epoch_valid
 * must be false unless its one-epoch lifetime/queue contract is actually satisfied.
 */
struct completed_frame_owner {
    uint64_t epoch;
    bool valid,exclusive_owner,read_scope_held,consumer_epoch_valid;
};
struct completed_frame_providers {
    void *owner_context;
    enum board_l_result (*owner)(void *,struct completed_frame_owner *);
    void *producer_context;
    enum board_l_result (*produce)(void *,struct adc_completed_frame *);
    void *clock_context;
    enum board_l_result (*clock)(void *,struct sample_clock *);
    void *thermal_context;
    enum board_l_result (*thermal)(void *,uint32_t,struct sample_thermal *);
};
enum completed_bridge_error {COMPLETED_BRIDGE_NO_ERROR,COMPLETED_BRIDGE_CONFIG,
    COMPLETED_BRIDGE_REBIND,COMPLETED_BRIDGE_ARGUMENT,COMPLETED_BRIDGE_OWNER_CALLBACK,
    COMPLETED_BRIDGE_OWNER_INVALID,COMPLETED_BRIDGE_OWNER_EPOCH,COMPLETED_BRIDGE_OWNER_SCOPE,
    COMPLETED_BRIDGE_PRODUCER,COMPLETED_BRIDGE_DECODE,COMPLETED_BRIDGE_CLOCK,COMPLETED_BRIDGE_THERMAL};
enum completed_bridge_stage {COMPLETED_BRIDGE_CONFIGURATION,COMPLETED_BRIDGE_ACQUIRE_STAGE,
    COMPLETED_BRIDGE_CLOCK_STAGE,COMPLETED_BRIDGE_THERMAL_STAGE};
/* Private fields, zero-init once at final address, one nonreentrant owner.
 * Immutable choice/epoch/providers; no reset/rebind/copy/move. Provider contexts
 * outlive bridge and all hook copies/consumers. No cached completed-frame buffer.
 */
struct completed_frame_bridge {
    struct adc_channel_choice choice;
    struct completed_frame_providers providers;
    uint64_t epoch;
    bool attempted,configured,rebind_refused;
    enum completed_bridge_error first_error;
    enum completed_bridge_stage first_stage;
    enum board_l_result first_callback_result;
    uint64_t first_observed_owner;
    /* Most recent acquire attempt, frozen after first failure. Flags distinguish
     * actual invocation from an enum's default numeric value. */
    bool producer_attempted,decode_attempted;
    enum board_l_result producer_result;
    enum adc_frame_decode_result decode_result;
};
bool completed_frame_bridge_configure(struct completed_frame_bridge *,
    const struct adc_channel_choice *,uint64_t epoch,const struct completed_frame_providers *);
bool completed_frame_bridge_hooks(struct completed_frame_bridge *,struct sample_adapter_hooks *);
/* Configuration is structural/pure, not ownership/acquisition admission.
 * Every hook queries independent owner before/after its external callback;
 * acquire additionally invokes actual V55 decoder. Only successful decoded frame
 * published. Invalid clock/thermal payloads are forwarded for unchanged adapter
 * validity/freshness/replay/conversion policy. Callback/owner/decode failures
 * latch and block further normal callbacks, with no automatic recovery/rearm.
 * No hardware producer, app readiness, physical OFF or qualification is supplied.
 */
#endif
