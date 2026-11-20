#ifndef BOARD_SAMPLES_H
#define BOARD_SAMPLES_H
/* Portable Board L sample source (host-tested): one raw ADC pair per tick feeds the
 * unchanged V72 sample_adapter (freshness, replay, knob averaging, thermal gate and
 * graded gain). PROPOSED values; knob endpoints and NTC codes need bench calibration. */
#include "../src/sample_adapter.h"

/* NTC (RT1 10k B3380 to GND, 100k to V3P3, ratiometric 12-bit code on PA4), from
 * doc/src/content/docs/architecture/board-l.mdx "Thermal derate" and the owner's
 * bring-up firmware. The code falls as temperature rises. */
#define NTC_DERATE_CODE 104u   /* ~65 C: start linear roll-off */
#define NTC_CRITICAL_CODE 69u  /* ~80 C: no light */
#define NTC_OPEN_CODE 3500u    /* open sensor: thermal unknown */
/* Knob (PA0) endpoints: bring-up placeholders (60..4000 plus its 2/255 off band). */
#define KNOB_ADC_MAX 4095u
#define KNOB_OFF_CODE 91u
#define KNOB_FULL_CODE 4000u
#define KNOB_WINDOW 8u
/* V72 sample_adapter evicts history older than max_age, and this target takes one
 * sample per tick, so max_age must span the window (ages 0..KNOB_WINDOW-1) for the
 * mean to really cover KNOB_WINDOW samples. 7 ms is still fresh for a knob/NTC. */
#define SAMPLE_MAX_AGE_TICKS (KNOB_WINDOW - 1u)
_Static_assert(KNOB_WINDOW >= 1u && KNOB_WINDOW <= KNOB_AVERAGE_MAX_WINDOW, "knob window range");

/* One completed knob/NTC conversion pair. ok=false means the converter failed. */
struct raw_pair { uint32_t knob, ntc; bool ok; };
struct raw_source {
    void *context;
    bool (*convert)(void *, struct raw_pair *);
    uint64_t (*now)(void *);
};
struct board_samples {
    struct raw_source source;
    uint64_t sequence;
    struct sample_adapter adapter;
};

enum board_l_result ntc_thermal(void *, uint32_t raw, struct sample_thermal *);
enum board_l_result ntc_gain(void *, uint32_t raw, struct thermal_gain *);
/* Binds the source and initializes the graded V72 sample_adapter. */
enum board_l_result board_samples_init(struct board_samples *, const struct raw_source *);
/* lamp_target sample_port callbacks; context is the struct board_samples. */
enum board_l_result board_samples_read(void *, struct lamp_samples *);
enum board_l_result board_samples_read_graded(void *, struct lamp_samples *, struct thermal_gain *);
#endif
