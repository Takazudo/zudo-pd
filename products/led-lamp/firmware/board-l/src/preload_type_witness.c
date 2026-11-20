#include "tim3_preload.h"
#include <stddef.h>
/* Signature compatibility only. Deliberately does NOT create a full sink or
 * supply initialization/ready/OFF providers. Context composition remains external. */
bool preload_type_witness(void)
{
 struct host_timer_sink partial={0};partial.write_preload=tim3_preload_write;
 return partial.write_preload!=NULL && partial.initialize_off==NULL &&
 partial.ready==NULL && partial.request_off==NULL;
}
