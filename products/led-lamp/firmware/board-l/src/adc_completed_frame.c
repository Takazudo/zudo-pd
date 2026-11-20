#include "adc_completed_frame.h"
#include <stddef.h>
enum adc_frame_decode_result adc_decode_completed_frame(const struct adc_channel_choice *choice,
    uint64_t expected_epoch,const struct adc_completed_frame *frame,struct sample_frame *out)
{
    struct adc_preparation neutral={0};struct adc_channel_descriptor descriptor;
    struct sample_frame decoded={0};unsigned i,first,shift;uint32_t allowed;
    if(out)*out=(struct sample_frame){0};
    if(!out || !choice || !frame)return ADC_FRAME_DECODE_ARGUMENT;
    /* Existing pure validator only; neutral is not actual preparation state. */
    if(adc_channel_describe(choice,&neutral,&descriptor)!=ADC_CHANNEL_VALID_DESCRIPTOR)
        return ADC_FRAME_DECODE_CHOICE;
    if(!expected_epoch || !frame->owner_valid || frame->owner_epoch!=expected_epoch)
        return ADC_FRAME_DECODE_OWNER;
    if(!frame->sequence_valid || !frame->capture_valid || !frame->configuration_valid || !frame->status_valid)
        return ADC_FRAME_DECODE_EVIDENCE;
    if(frame->count!=2)return ADC_FRAME_DECODE_COUNT;
    if(!frame->format_valid || frame->oversampling_enabled || frame->resolution_bits!=12 ||
       frame->alignment!=choice->alignment || frame->kind!=ADC_COMPLETED_CONVERSIONS)
        return ADC_FRAME_DECODE_FORMAT;
    if(frame->error || frame->overrun)return ADC_FRAME_DECODE_ERROR;
    if(!frame->completed)return ADC_FRAME_DECODE_INCOMPLETE;
    if(!frame->coherent)return ADC_FRAME_DECODE_COHERENCE;
    first=choice->order==ADC_KNOB_THEN_NTC?0u:4u;
    shift=choice->alignment==ADC_ALIGN_LEFT?4u:0u;
    allowed=UINT32_C(0xfff)<<shift;
    for(i=0;i<2;++i){
        const struct adc_completed_word *word=&frame->words[i];
        struct sample_channel *channel;
        if(!word->present || !word->valid)return ADC_FRAME_DECODE_INCOMPLETE;
        if(word->owner_epoch!=expected_epoch || word->frame_sequence!=frame->sequence)
            return ADC_FRAME_DECODE_COHERENCE;
        if(word->channel!=(i==0?first:4u-first))return ADC_FRAME_DECODE_CHANNEL;
        if(word->data_word&~allowed)return ADC_FRAME_DECODE_RANGE;
        channel=word->channel==0?&decoded.knob:&decoded.thermal;
        *channel=(struct sample_channel){word->data_word>>shift,frame->sequence,frame->captured_at,true};
    }
    *out=decoded;return ADC_FRAME_DECODE_OK;
}
