#include "lamp_app.h"
#include <stddef.h>

static struct lamp_app_report report(const struct lamp_app *a) {
    struct lamp_app_report r={0};
    r.status=LAMP_APP_UNCONFIGURED;
    r.cause=BOARD_L_UNCONFIGURED;
    r.last_apply_result=BOARD_L_UNCONFIGURED;
    if (a) {
        r.have_first_invalid_sample=a->have_first_invalid_sample;
        r.first_invalid_sample=a->first_invalid_sample;
        r.command=a->core.command; r.core_status=a->core.status;
        r.core_command=a->core.command; r.noise_enabled=a->noise_enabled;
        r.gain_enabled=a->gain_path.enabled;r.pre_thermal_command=a->core.command;
        r.transfer_enabled=a->transfer_enabled;
        r.board_ready=a->board_ready;
        r.startup_pending=a->startup_pending; r.acquisition_unqualified=a->acquisition_unqualified;
        r.startup_epoch=a->startup_epoch;
        r.reinitialize_required=a->reinitialize_required;
    } else r.status=LAMP_APP_BAD_ARGUMENT;
    return r;
}
static bool complete(const struct lamp_app_io *io) {
    return io && io->initialize_off && io->read_samples && io->apply_command && io->force_off;
}
static bool same(const struct lamp_app_io *a,const struct lamp_app_io *b) {
    return b && a->context==b->context && a->initialize_off==b->initialize_off &&
        a->read_samples==b->read_samples && a->apply_command==b->apply_command &&
        a->force_off==b->force_off;
}
static void request_zero(struct lamp_app *a,struct lamp_app_report *r) {
    a->core.command=0; r->command=0;
    r->core_command=0;noise_reset(&a->noise);
    r->pre_thermal_command=0;
    r->post_thermal_command=0;
    if (a->io.apply_command) {
        r->apply_attempted=true;
        r->last_apply_result=a->io.apply_command(a->io.context,0);
    }
    if (a->io.force_off) {
        a->io.force_off(a->io.context); r->force_off_requested=true;
    }
    /* Neither a void request nor accepted zero establishes physical OFF. */
}
static struct lamp_app_report fail(struct lamp_app *a,enum lamp_app_status status,
                                  enum board_l_result cause,
                                  const struct lamp_app_report *zero_attempt) {
    struct lamp_app_report r;
    lamp_reset(&a->core);
    noise_reset(&a->noise);
    a->board_ready=false; a->reinitialize_required=true;
    a->startup_pending=false; a->acquisition_unqualified=false;
    r=report(a); r.status=status; r.cause=cause;
    if (!zero_attempt) request_zero(a,&r);
    else {
        r.apply_attempted=zero_attempt->apply_attempted;
        r.last_apply_result=zero_attempt->last_apply_result;
        r.force_off_requested=zero_attempt->force_off_requested;
        if (!r.force_off_requested && a->io.force_off) {
            a->io.force_off(a->io.context); r.force_off_requested=true;
        }
    }
    return r;
}
static struct lamp_app_report initialize_full(struct lamp_app *a,
    const struct lamp_app_io *io,const struct board_l_config *cfg,const struct lamp_app_noise *noise,
    const struct lamp_app_gain_path *gain_path,const struct transfer_config *transfer,
    const struct lamp_app_preparation *preparation) {
    enum board_l_result result;
    struct lamp_app_report r;
    struct lamp_app_noise selected={0};
    struct lamp_app_gain_path selected_gain={0};
    struct normalized_transfer selected_transfer={0};
    enum transfer_status transfer_setup=TRANSFER_UNCONFIGURED;
    if (!a) return report(NULL);
    if(noise)selected=*noise;
    if(gain_path)selected_gain=*gain_path;
    if(transfer)transfer_setup=transfer_initialize(&selected_transfer,transfer);
    /* Clear prior software command before any callback during reinitialization. */
    lamp_reset(&a->core); a->board_ready=false;
    a->startup_pending=false;a->acquisition_unqualified=false;a->startup_epoch=0;
    a->noise=(struct noise_stage){0};a->noise_enabled=false;
    a->gain_path=(struct lamp_app_gain_path){0};
    a->transfer=(struct normalized_transfer){0};a->transfer_enabled=false;
    if (a->binding_locked && !same(&a->io,io))
        return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,NULL);
    if (!a->binding_locked) {
        /* Retain partial callbacks to request OFF even on incomplete contracts. */
        if (io) a->io=*io;
        else a->io=(struct lamp_app_io){0};
    }
    if (!complete(&a->io)) return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,NULL);
    a->binding_locked=true;
    if(a->preparation_locked && (!preparation ||
       a->preparation.epoch!=preparation->epoch || a->preparation.advance!=preparation->advance))
        return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,NULL);
    if(preparation) {
        if(!preparation->epoch || !preparation->advance)
            return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,NULL);
        a->preparation=*preparation;a->preparation_locked=true;
    }

    if (!cfg) return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,NULL);
    if(transfer) {
        if(transfer_setup!=TRANSFER_OK)return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,NULL);
        a->transfer=selected_transfer;a->transfer_enabled=true;
    }
    if(selected_gain.enabled) {
        if(!selected_gain.read_graded)return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,NULL);
        a->gain_path=selected_gain;
    }
    if(selected.enabled) {
        if(noise_initialize(&a->noise,&selected.config,&selected.source)!=NOISE_READY)
            return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,NULL);
        a->noise_enabled=true;
    }
    result=a->io.initialize_off(a->io.context,cfg);
    if (result!=BOARD_L_OK && !(preparation && result==BOARD_L_PREPARING))
        return fail(a,result==BOARD_L_UNCONFIGURED ? LAMP_APP_UNCONFIGURED : LAMP_APP_ADAPTER_ERROR,result,NULL);
    r=report(a); request_zero(a,&r);
    if (r.last_apply_result!=BOARD_L_OK)
        return fail(a,LAMP_APP_ADAPTER_ERROR,r.last_apply_result,&r);
    if(preparation) {
        /* Even a buggy preparation backend returning OK cannot grant readiness. */
        if(result!=BOARD_L_PREPARING)
            return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,&r);
        a->startup_epoch=preparation->epoch(a->io.context);
        if(!a->startup_epoch)return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,&r);
        a->startup_pending=true;a->reinitialize_required=false;
        r.status=LAMP_APP_STARTUP_PENDING;r.cause=BOARD_L_PREPARING;
        r.startup_pending=true;r.startup_epoch=a->startup_epoch;r.reinitialize_required=false;
        return r;
    }
    /* Board callback has reported OFF; zero was accepted. This is not bench proof. */
    lamp_initialize_off(&a->core);
    a->board_ready=true; a->reinitialize_required=false;
    r.status=LAMP_APP_CORE_OFF; r.cause=BOARD_L_OK; r.command=0;
    r.core_status=a->core.status; r.board_ready=true; r.reinitialize_required=false;
    return r;
}
struct lamp_app_report lamp_app_initialize_with_transfer(struct lamp_app *a,
    const struct lamp_app_io *io,const struct board_l_config *cfg,const struct lamp_app_noise *noise,
    const struct lamp_app_gain_path *gain,const struct transfer_config *transfer) {
    return initialize_full(a,io,cfg,noise,gain,transfer,NULL);
}
struct lamp_app_report lamp_app_initialize_with_preparation(struct lamp_app *a,
    const struct lamp_app_io *io,const struct board_l_config *cfg,const struct lamp_app_preparation *p) {
    if(!p) {if(!a)return report(NULL);return fail(a,LAMP_APP_UNCONFIGURED,BOARD_L_UNCONFIGURED,NULL);}
    return initialize_full(a,io,cfg,NULL,NULL,NULL,p);
}
struct lamp_app_report lamp_app_initialize(struct lamp_app *a,
    const struct lamp_app_io *io,const struct board_l_config *cfg) {
    return lamp_app_initialize_with_noise(a,io,cfg,NULL);
}
struct lamp_app_report lamp_app_initialize_with_noise(struct lamp_app *a,
    const struct lamp_app_io *io,const struct board_l_config *cfg,const struct lamp_app_noise *noise) {
    return lamp_app_initialize_with_thermal_gain(a,io,cfg,noise,NULL);
}
struct lamp_app_report lamp_app_initialize_with_thermal_gain(struct lamp_app *a,
    const struct lamp_app_io *io,const struct board_l_config *cfg,const struct lamp_app_noise *noise,
    const struct lamp_app_gain_path *gain_path) {
    return lamp_app_initialize_with_transfer(a,io,cfg,noise,gain_path,NULL);
}
struct lamp_app_report lamp_app_tick_frame(struct lamp_app *a,const struct lamp_config *cfg,
                                          const struct lamp_frame *frame) {
    struct lamp_samples samples={0}; /* no sample state survives across calls */
    struct thermal_gain gain={0};
    struct lamp_app_report r;
    enum board_l_result result;
    uint32_t applied;
    struct lamp_config selected={0};
    if(cfg) { selected=*cfg; selected.recovery=LAMP_RECOVERY_LATCH; cfg=&selected; }
    if (!a) return report(NULL);
    if(a->startup_pending || a->acquisition_unqualified) {
        r=report(a);
        /* Already accepted zero remains held; do not repeat zero/failed writes or ADC work. */
        if(a->startup_pending) {
            result=a->preparation.advance(a->io.context,a->startup_epoch);
            if(result==BOARD_L_ACQUISITION_UNQUALIFIED) {
                a->startup_pending=false;a->acquisition_unqualified=true;
            } else if(result!=BOARD_L_PREPARING)
                return fail(a,LAMP_APP_ADAPTER_ERROR,result==BOARD_L_OK ? BOARD_L_UNCONFIGURED : result,NULL);
        } else if(a->preparation.epoch(a->io.context)!=a->startup_epoch)
            return fail(a,LAMP_APP_ADAPTER_ERROR,BOARD_L_UNCONFIGURED,NULL);
        r.startup_pending=a->startup_pending;r.acquisition_unqualified=a->acquisition_unqualified;
        r.status=a->startup_pending ? LAMP_APP_STARTUP_PENDING : LAMP_APP_ACQUISITION_UNQUALIFIED;
        r.cause=a->startup_pending ? BOARD_L_PREPARING : BOARD_L_ACQUISITION_UNQUALIFIED;
        return r;
    }
    if (!a->board_ready || a->reinitialize_required) {
        r=report(a);
        r.status=a->reinitialize_required ? LAMP_APP_REINITIALIZE_REQUIRED : LAMP_APP_UNCONFIGURED;
        request_zero(a,&r);
        if (r.apply_attempted && r.last_apply_result!=BOARD_L_OK) {
            r.status=LAMP_APP_ADAPTER_ERROR; r.cause=r.last_apply_result;
        }
        return r;
    }
    result=a->gain_path.enabled ? a->gain_path.read_graded(a->io.context,&samples,&gain) :
                                 a->io.read_samples(a->io.context,&samples);
    if (result!=BOARD_L_OK) {
        /* A callback may write plausible samples and still fail. Discard them. */
        samples=(struct lamp_samples){0};
        (void)lamp_step(&a->core,cfg,&samples);
        return fail(a,result==BOARD_L_UNCONFIGURED ? LAMP_APP_UNCONFIGURED : LAMP_APP_ADAPTER_ERROR,result,NULL);
    }
    if(a->gain_path.enabled && (!gain.valid || gain.value>LAMP_FULL))
        samples=(struct lamp_samples){0}; /* invalid normalized input */
    /* Selected application policy also holds when ramp config is missing.
       Reuse the core latch; do not introduce a second recovery state machine. */
    if(samples.knob>LAMP_FULL || !samples.knob_valid || !samples.thermal_valid ||
       !samples.thermal_allows_light || !samples.fresh) {
        a->core.latched=true;
        if(!a->have_first_invalid_sample) {
            a->first_invalid_sample=samples; a->have_first_invalid_sample=true;
        }
    }
    (void)lamp_step(&a->core,cfg,&samples);
    r=report(a); r.cause=BOARD_L_OK; r.apply_attempted=true;
    r.gain_valid=a->gain_path.enabled && gain.valid && gain.value<=LAMP_FULL;
    if(r.gain_valid)r.gain=gain.value;
    applied=a->core.command;
    if(a->noise_enabled && a->core.status==LAMP_READY && a->core.command) {
        struct noise_input in={a->core.command,
            samples.knob_valid && samples.thermal_valid && samples.thermal_allows_light && samples.fresh,
            true,frame && frame->qualified};
        struct noise_output out={0};
        r.noise_attempted=true;r.noise_status=noise_step(&a->noise,&in,&out);
        if(r.noise_status==NOISE_INELIGIBLE)applied=0;
        else if((r.noise_status!=NOISE_VALID && r.noise_status!=NOISE_OFF) ||
                !out.valid || out.value>LAMP_FULL) {
            struct lamp_app_report failed=fail(a,LAMP_APP_TRANSFORM_ERROR,BOARD_L_IO_ERROR,NULL);
            failed.noise_attempted=true;failed.noise_status=r.noise_status;return failed;
        } else applied=out.value;
    } else noise_reset(&a->noise);
    r.pre_thermal_command=applied;
    if(a->gain_path.enabled && applied && !thermal_gain_apply(applied,&gain,&applied))
        return fail(a,LAMP_APP_TRANSFORM_ERROR,BOARD_L_IO_ERROR,NULL);
    r.post_thermal_command=applied;
    if(a->transfer_enabled) {
        r.transfer_attempted=true;r.transfer_status=transfer_apply(&a->transfer,applied,&applied);
        if(r.transfer_status!=TRANSFER_OK) {
            struct lamp_app_report failed=fail(a,LAMP_APP_TRANSFORM_ERROR,BOARD_L_IO_ERROR,NULL);
            failed.transfer_attempted=true;failed.transfer_status=r.transfer_status;return failed;
        }
    }
    r.command=applied;
    r.last_apply_result=a->io.apply_command(a->io.context,applied);
    if (r.last_apply_result!=BOARD_L_OK) {
        struct lamp_app_report failed=fail(a,LAMP_APP_ADAPTER_ERROR,r.last_apply_result,applied ? NULL : &r);
        failed.noise_attempted=r.noise_attempted;failed.noise_status=r.noise_status;
        failed.transfer_attempted=r.transfer_attempted;failed.transfer_status=r.transfer_status;return failed;
    }
    if (!applied) {
        noise_reset(&a->noise);
        a->io.force_off(a->io.context); r.force_off_requested=true;
    }
    r.status=a->core.status==LAMP_UNCONFIGURED ? LAMP_APP_UNCONFIGURED :
        (r.noise_attempted && r.noise_status==NOISE_INELIGIBLE ? LAMP_APP_FRAME_OFF :
        (applied ? LAMP_APP_OK : LAMP_APP_CORE_OFF));
    return r;
}
struct lamp_app_report lamp_app_tick(struct lamp_app *a,const struct lamp_config *cfg) {
    return lamp_app_tick_frame(a,cfg,NULL);
}
