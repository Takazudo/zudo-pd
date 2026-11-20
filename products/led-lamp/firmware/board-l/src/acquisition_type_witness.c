#include "discontinuous_acquisition.h"
#include "completed_frame_bridge.h"
/* Compile-only real provider signature witness, no configure/start/readiness. */
bool acquisition_type_witness(struct completed_frame_providers *p,struct discontinuous_acquisition *a)
{
 if(!p || !a)return false;
 p->producer_context=a;p->produce=da_produce;return true;
}
