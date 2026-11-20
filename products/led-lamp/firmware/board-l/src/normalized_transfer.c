#include "normalized_transfer.h"
static bool valid(const struct transfer_point *p,size_t n) {
    size_t i;
    if(!p || n<2 || n>NORMALIZED_TRANSFER_MAX_POINTS || p[0].input || p[0].output ||
       p[n-1].input!=LAMP_FULL)return false;
    for(i=0;i<n;++i) {
        if(p[i].input>LAMP_FULL || p[i].output>p[i].input)return false;
        if(i && (p[i].input<=p[i-1].input || p[i].output<p[i-1].output))return false;
    }
    return true;
}
enum transfer_status transfer_initialize(struct normalized_transfer *s,const struct transfer_config *cfg) {
    struct normalized_transfer next={0};size_t i;
    if(!s)return TRANSFER_BAD_ARGUMENT;
    if(!cfg || !cfg->configured || !valid(cfg->points,cfg->count)) {
        *s=next;return TRANSFER_UNCONFIGURED;
    }
    /* Local snapshot also permits explicit reinit from the object's own points. */
    next.count=cfg->count;
    for(i=0;i<next.count;++i)next.points[i]=cfg->points[i];
    next.configured=true;*s=next;return TRANSFER_OK;
}
enum transfer_status transfer_apply(const struct normalized_transfer *s,uint32_t input,uint32_t *out) {
    size_t i;
    if(!out)return TRANSFER_BAD_ARGUMENT;
    *out=0;
    if(!s || !s->configured || !valid(s->points,s->count))return TRANSFER_UNCONFIGURED;
    if(input>LAMP_FULL)return TRANSFER_BAD_INPUT;
    if(!input)return TRANSFER_OK;
    for(i=1;i<s->count;++i) {
        if(input<=s->points[i].input) {
            const struct transfer_point *a=&s->points[i-1],*b=&s->points[i];
            *out=a->output+(uint32_t)(((uint64_t)(input-a->input)*(b->output-a->output))/(b->input-a->input));
            return TRANSFER_OK;
        }
    }
    return TRANSFER_BAD_INPUT; /* validated domain makes this unreachable */
}
