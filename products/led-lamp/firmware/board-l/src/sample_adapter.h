#ifndef SAMPLE_ADAPTER_H
#define SAMPLE_ADAPTER_H
#include "board_l_io.h"
#include "input_conversion.h"
#include "thermal_gain.h"

/* Abstract raw units: channel calibration/thermal meaning belong to caller.
   Present means raw+sequence+captured_at were all written for THIS channel.
   Matching sequence/time tags declare one coherent snapshot. Hardware must
   establish that declaration; this code cannot prove simultaneous acquisition. */
struct sample_channel {
    uint32_t raw;
    uint64_t sequence, captured_at;
    bool present;
};
struct sample_frame { struct sample_channel knob, thermal; };
struct sample_clock { uint64_t ticks; bool valid; };
struct sample_thermal { bool known, allows_light; };
struct sample_gain_config {
    bool configured;
    void *context;
    enum board_l_result (*evaluate)(void *,uint32_t,struct thermal_gain *);
};
#define KNOB_AVERAGE_MAX_WINDOW 32u
struct sample_adapter_config {
    bool configured, freshness_configured;
    uint64_t max_age; /* inclusive, caller clock units; zero is explicitly valid */
    struct knob_calibration knob;
    uint8_t knob_window; /* mandatory explicit 1..32; 1 is explicit bypass */
};
struct sample_adapter_hooks {
    void *context;
    enum board_l_result (*acquire)(void *, struct sample_frame *);
    enum board_l_result (*clock)(void *, struct sample_clock *);
    enum board_l_result (*thermal)(void *, uint32_t, struct sample_thermal *);
};
enum sample_adapter_status {
    SAMPLE_UNCONFIGURED, SAMPLE_READY, SAMPLE_VALID, SAMPLE_INCOMPLETE,
    SAMPLE_INCOHERENT, SAMPLE_REPLAY, SAMPLE_TIME_ORDER, SAMPLE_STALE,
    SAMPLE_KNOB_INVALID, SAMPLE_THERMAL_UNKNOWN, SAMPLE_THERMAL_DENIED,
    SAMPLE_ACQUIRE_ERROR, SAMPLE_CLOCK_ERROR, SAMPLE_THERMAL_ERROR,
    SAMPLE_REINITIALIZE_REQUIRED, SAMPLE_BAD_ARGUMENT, SAMPLE_GAIN_INVALID, SAMPLE_GAIN_ERROR
};
struct sample_adapter {
    struct sample_adapter_config config;
    struct sample_adapter_hooks hooks;
    enum sample_adapter_status status;
    bool configured, faulted, have_clock, have_sequence, have_capture;
    uint64_t last_clock, last_sequence, last_capture;
    bool gain_enabled;
    struct sample_gain_config gain_config;
    uint32_t knob_raw_history[KNOB_AVERAGE_MAX_WINDOW];
    uint64_t knob_capture_history[KNOB_AVERAGE_MAX_WINDOW];
    uint64_t knob_sum;
    uint8_t knob_count, knob_head;
};
/* Zero initialize; single owner, no reentrancy/concurrency or callback mutation.
   Init copies config/hooks, resets epoch, samples, watermarks and filter history.
   Averaging is a bounded raw-sample moving mean after ALL validity/thermal/age
   checks. Explicit window1 bypasses; zero/unset is unconfigured, no default.
   Warmup uses only actual accepted samples (no padding). Invalid/fault paths
   clear history. Entries older than max_age at final clock are evicted before
   averaging; no stale history is allowed to influence a fresh result.
   uint64 sum holds at most32 UINT32 values; division truncates raw mean. Caller MUST
   coordinate explicit app/board reinitialization and discard old queued frames
   before changing epoch/config. No physical OFF is performed here.
   Unsigned64 time/sequence NEVER wrap within an epoch: clock nondecreasing,
   sequence strictly increasing, capture time nondecreasing. Clock rollback
   faults until init; sequence wrap/replay rejects data until a new epoch.
   Cannot detect a full unseen wrap or dishonest tags. Hardware must extend
   narrower counters or explicitly start a new epoch while OFF. */
enum board_l_result sample_adapter_initialize(struct sample_adapter *,
    const struct sample_adapter_config *, const struct sample_adapter_hooks *);
/* NULL gain config explicitly disables graded path. No cached gain is exposed. */
enum board_l_result sample_adapter_initialize_graded(struct sample_adapter *,
    const struct sample_adapter_config *,const struct sample_adapter_hooks *,const struct sample_gain_config *);
/* Compatible read callback for lamp_app, with adapter as context. Shared app
   contexts can forward to this function. Output ALWAYS cleared first.
   Sensor invalid => OK with entirely invalid samples (core AUTO/LATCH).
   Callback/clock contract failure => IO_ERROR and adapter fault hold.
   Missing config => UNCONFIGURED. App separately inhibits on non-OK.
   Complete coherent fresh tags are consumed even if conversion rejects them;
   replaying the same frame never restores a previously accepted command. */
enum board_l_result sample_adapter_read(void *, struct lamp_samples *);
/* Same-frame output pair; mode mismatch/NULL gain never silently grants unity. */
enum board_l_result sample_adapter_read_graded(void *,struct lamp_samples *,struct thermal_gain *);
#endif
