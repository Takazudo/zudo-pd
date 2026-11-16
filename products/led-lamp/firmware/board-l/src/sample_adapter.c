#include "sample_adapter.h"
#include <stddef.h>

static void clear_knob_history(struct sample_adapter *a) {
    a->knob_sum=0; a->knob_count=0; a->knob_head=0;
}
static enum board_l_result invalid(struct sample_adapter *a, enum sample_adapter_status s) {
    clear_knob_history(a); a->status=s; return BOARD_L_OK;
}
static enum board_l_result fault(struct sample_adapter *a, enum sample_adapter_status s,
                                 enum board_l_result cause) {
    clear_knob_history(a); a->status=s; a->faulted=true;
    return cause==BOARD_L_UNCONFIGURED ? BOARD_L_UNCONFIGURED : BOARD_L_IO_ERROR;
}
enum board_l_result sample_adapter_initialize(struct sample_adapter *a,
    const struct sample_adapter_config *cfg, const struct sample_adapter_hooks *hooks) {
    struct sample_adapter_config c={0};
    struct sample_adapter_hooks h={0};
    uint32_t unused;
    if (!a) return BOARD_L_IO_ERROR;
    if (cfg) c=*cfg;
    if (hooks) h=*hooks;
    *a=(struct sample_adapter){0}; a->status=SAMPLE_UNCONFIGURED;
    if (!cfg || !hooks || !c.configured || !c.freshness_configured ||
        !c.knob_window || c.knob_window>KNOB_AVERAGE_MAX_WINDOW ||
        !knob_request(c.knob.off_code,&c.knob,&unused) ||
        !h.acquire || !h.clock || !h.thermal) return BOARD_L_UNCONFIGURED;
    a->config=c; a->hooks=h; a->configured=true; a->status=SAMPLE_READY;
    return BOARD_L_OK;
}
static enum board_l_result now(struct sample_adapter *a, uint64_t *ticks) {
    struct sample_clock t={0};
    enum board_l_result r=a->hooks.clock(a->hooks.context,&t);
    if (r!=BOARD_L_OK) return fault(a,SAMPLE_CLOCK_ERROR,r);
    if (!t.valid || (a->have_clock && t.ticks<a->last_clock))
        return fault(a,SAMPLE_CLOCK_ERROR,BOARD_L_IO_ERROR);
    a->last_clock=t.ticks; a->have_clock=true; *ticks=t.ticks;
    return BOARD_L_OK;
}
enum board_l_result sample_adapter_initialize_graded(struct sample_adapter *a,
    const struct sample_adapter_config *cfg,const struct sample_adapter_hooks *hooks,
    const struct sample_gain_config *gain) {
    struct sample_gain_config selected={0};enum board_l_result r;
    if(gain)selected=*gain;
    r=sample_adapter_initialize(a,cfg,hooks);if(r!=BOARD_L_OK)return r;
    if(gain) {
        if(!selected.configured || !selected.evaluate) {
            a->configured=false;a->status=SAMPLE_UNCONFIGURED;return BOARD_L_UNCONFIGURED;
        }
        a->gain_enabled=true;a->gain_config=selected;
    }
    return BOARD_L_OK;
}
static enum board_l_result read_frame(void *context,struct lamp_samples *out,struct thermal_gain *gain,bool graded) {
    struct sample_adapter *a=context;
    struct sample_frame frame={0};
    struct sample_thermal thermal={0};
    struct thermal_gain evaluated={0};
    enum board_l_result r;
    uint64_t ticks;
    uint32_t request=0;
    if (out) *out=(struct lamp_samples){0};
    if(gain)*gain=(struct thermal_gain){0};
    if (!a || !out || (graded && !gain)) {
        if (a) return fault(a,SAMPLE_BAD_ARGUMENT,BOARD_L_IO_ERROR);
        return BOARD_L_IO_ERROR;
    }
    if (!a->configured) { a->status=SAMPLE_UNCONFIGURED; return BOARD_L_UNCONFIGURED; }
    if (a->faulted) { a->status=SAMPLE_REINITIALIZE_REQUIRED; return BOARD_L_IO_ERROR; }
    if(graded!=a->gain_enabled)return fault(a,SAMPLE_GAIN_ERROR,BOARD_L_UNCONFIGURED);
    r=now(a,&ticks); if (r!=BOARD_L_OK) return r;
    r=a->hooks.acquire(a->hooks.context,&frame);
    if (r!=BOARD_L_OK) return fault(a,SAMPLE_ACQUIRE_ERROR,r);
    if (!frame.knob.present || !frame.thermal.present) return invalid(a,SAMPLE_INCOMPLETE);
    if (frame.knob.sequence!=frame.thermal.sequence ||
        frame.knob.captured_at!=frame.thermal.captured_at) return invalid(a,SAMPLE_INCOHERENT);
    if (a->have_sequence && frame.knob.sequence<=a->last_sequence) return invalid(a,SAMPLE_REPLAY);
    /* Consume the coherent sequence before validity checks: rejected frames
       must not become acceptable through a callback/config change on replay. */
    a->last_sequence=frame.knob.sequence; a->have_sequence=true;
    /* Capture may occur DURING acquire, so compare with post-acquisition clock. */
    r=now(a,&ticks); if (r!=BOARD_L_OK) return r;
    if (frame.knob.captured_at>ticks ||
        (a->have_capture && frame.knob.captured_at<a->last_capture))
        return invalid(a,SAMPLE_TIME_ORDER);
    a->last_capture=frame.knob.captured_at; a->have_capture=true;
    if (ticks-frame.knob.captured_at>a->config.max_age) return invalid(a,SAMPLE_STALE);
    if (!knob_request(frame.knob.raw,&a->config.knob,&request)) return invalid(a,SAMPLE_KNOB_INVALID);
    r=a->hooks.thermal(a->hooks.context,frame.thermal.raw,&thermal);
    if (r!=BOARD_L_OK) return fault(a,SAMPLE_THERMAL_ERROR,r);
    if (!thermal.known) return invalid(a,SAMPLE_THERMAL_UNKNOWN);
    if (!thermal.allows_light) return invalid(a,SAMPLE_THERMAL_DENIED);
    if(graded) {
        r=a->gain_config.evaluate(a->gain_config.context,frame.thermal.raw,&evaluated);
        if(r!=BOARD_L_OK)return fault(a,SAMPLE_GAIN_ERROR,r);
        if(!evaluated.valid || evaluated.value>LAMP_FULL)return invalid(a,SAMPLE_GAIN_INVALID);
    }
    /* Include thermal evaluation duration in final age; no stale admission. */
    r=now(a,&ticks); if (r!=BOARD_L_OK) return r;
    if (ticks-frame.knob.captured_at>a->config.max_age) return invalid(a,SAMPLE_STALE);
    /* Only fully accepted raw samples enter this bounded history. Oldest
       timestamp is safe to subtract: capture ordering and current age checked. */
    while(a->knob_count && (a->knob_count>=a->config.knob_window ||
          ticks-a->knob_capture_history[a->knob_head]>a->config.max_age)) {
        a->knob_sum-=a->knob_raw_history[a->knob_head];
        a->knob_head=(uint8_t)((a->knob_head+1u)%KNOB_AVERAGE_MAX_WINDOW);
        --a->knob_count;
    }
    {
        uint8_t index=(uint8_t)((a->knob_head+a->knob_count)%KNOB_AVERAGE_MAX_WINDOW);
        a->knob_raw_history[index]=frame.knob.raw;
        a->knob_capture_history[index]=frame.knob.captured_at;
        a->knob_sum+=frame.knob.raw; ++a->knob_count;
        if(!knob_request((uint32_t)(a->knob_sum/a->knob_count),&a->config.knob,&request))
            return invalid(a,SAMPLE_KNOB_INVALID);
    }
    *out=(struct lamp_samples){request,true,true,true,true};
    if(graded)*gain=evaluated;
    a->status=SAMPLE_VALID; return BOARD_L_OK;
}
enum board_l_result sample_adapter_read(void *ctx,struct lamp_samples *out) {
    return read_frame(ctx,out,NULL,false);
}
enum board_l_result sample_adapter_read_graded(void *ctx,struct lamp_samples *out,struct thermal_gain *gain) {
    return read_frame(ctx,out,gain,true);
}
