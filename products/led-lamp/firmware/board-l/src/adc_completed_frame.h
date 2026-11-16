#ifndef ADC_COMPLETED_FRAME_H
#define ADC_COMPLETED_FRAME_H
#include "adc_channel_config.h"
#include "sample_adapter.h"
enum adc_completed_kind {ADC_COMPLETED_UNSPECIFIED,ADC_COMPLETED_CONVERSIONS,ADC_COMPLETED_CALIBRATION};
struct adc_completed_word {
    uint32_t data_word;
    unsigned channel;
    uint64_t owner_epoch,frame_sequence;
    bool present,valid;
};
/* A producer-supplied COMPLETED coherent pair, not two arbitrary DR reads.
 * Flags are external factual guarantees; this decoder cannot verify physical
 * simultaneity, actual acquisition permission or honestly assigned tags.
 * captured_at is the producer's whole-frame capture tag in sample_adapter clock
 * units, not a claim that sequential channels converted at one physical instant.
 */
struct adc_completed_frame {
    uint64_t owner_epoch,sequence,captured_at;
    unsigned count,resolution_bits;
    enum adc_alignment alignment;
    enum adc_completed_kind kind;
    bool owner_valid,sequence_valid,capture_valid,configuration_valid;
    bool format_valid,oversampling_enabled,status_valid,completed,coherent,error,overrun;
    struct adc_completed_word words[2];
};
enum adc_frame_decode_result {ADC_FRAME_DECODE_OK,ADC_FRAME_DECODE_ARGUMENT,
    ADC_FRAME_DECODE_CHOICE,ADC_FRAME_DECODE_OWNER,ADC_FRAME_DECODE_EVIDENCE,
    ADC_FRAME_DECODE_COUNT,ADC_FRAME_DECODE_FORMAT,ADC_FRAME_DECODE_INCOMPLETE,
    ADC_FRAME_DECODE_ERROR,ADC_FRAME_DECODE_COHERENCE,ADC_FRAME_DECODE_CHANNEL,
    ADC_FRAME_DECODE_RANGE};
/* Pure bounded validation/mapping into actual sample_frame. No state/callbacks,
 * registers, allocation, readiness, calibration, conversion or freshness policy.
 * expected_epoch is actual external owner, not inferred from input. Nonzero only.
 * Valid nonoverlapping inputs/output required. Nonnull output always cleared on
 * failure; success only after both words pass. Sequence/time zero are legitimate
 * values with explicitvalidity; replay/wrap/freshness remain sample_adapter's job.
 * configuration_valid certifies actual captured configuration matches supplied
 * V35 choice, including mode/order/groups. format_valid covers known RES/ALIGN/
 * OVSE; only explicit unoversampled12bit conversion data is supported here.
 */
enum adc_frame_decode_result adc_decode_completed_frame(const struct adc_channel_choice *,
    uint64_t expected_epoch,const struct adc_completed_frame *,struct sample_frame *);
#endif
