#include "preload_lifecycle.h"
#include <stddef.h>
static bool fail(struct preload_lifecycle *p,enum preload_lifecycle_error e,enum board_l_result r)
{
 if(p->first_error==PL_NONE){p->first_error=e;p->first_result=r;
 p->first_write_possible=p->preload.write_attempted;}
 return false;
}
static bool owner(struct preload_lifecycle *p)
{
 struct preload_lifecycle_owner o={0};enum board_l_result r;
 if(p->first_error!=PL_NONE)return false;
 if(p->preload.first_error!=TP_NONE)return fail(p,PL_TERMINAL,BOARD_L_UNCONFIGURED);
 r=p->providers.owner(p->providers.owner_context,&o);
 if(p->first_error!=PL_NONE)return false;
 if(r!=BOARD_L_OK)return fail(p,PL_OWNER_CALLBACK,r);
 if(!o.valid || o.epoch!=p->epoch || !o.exclusive_lifecycle_scope || !o.current || !o.consumer_epoch_valid)
  return fail(p,PL_OWNER,BOARD_L_UNCONFIGURED);
 return true;
}
static bool enter(struct preload_lifecycle *p)
{
 if(!p)return false;
 if(p->self!=p)return fail(p,PL_CONTEXT,BOARD_L_UNCONFIGURED);
 if(!p->configured || p->first_error!=PL_NONE)return false;
 if(p->busy)return fail(p,PL_REENTRANT,BOARD_L_UNCONFIGURED);
 p->busy=true;return owner(p);
}
static enum board_l_result initialize(void *ctx,const struct board_l_config *cfg)
{
 struct preload_lifecycle *p=ctx;enum board_l_result r;
 if(!enter(p))return BOARD_L_UNCONFIGURED;
 if(!cfg){(void)fail(p,PL_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 r=p->providers.initialize_off(p->providers.init_context,cfg);
 if(r!=BOARD_L_OK){(void)fail(p,PL_INIT,r);return r;}
 if(!owner(p))return BOARD_L_UNCONFIGURED;
 p->busy=false;return BOARD_L_OK;
}
static enum board_l_result ready(void *ctx,bool *out)
{
 struct preload_lifecycle *p=ctx;bool observed=false;enum board_l_result r;
 if(out)*out=false;
 if(!enter(p))return BOARD_L_UNCONFIGURED;
 if(!out){(void)fail(p,PL_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 r=p->providers.ready(p->providers.ready_context,&observed);
 if(r!=BOARD_L_OK || !observed){(void)fail(p,PL_READY,r==BOARD_L_OK?BOARD_L_UNCONFIGURED:r);return r==BOARD_L_OK?BOARD_L_UNCONFIGURED:r;}
 if(!owner(p))return BOARD_L_UNCONFIGURED;
 *out=true;p->busy=false;return BOARD_L_OK;
}
static enum board_l_result write_preload(void *ctx,uint32_t ccr,struct timer_sink_receipt *receipt)
{
 struct preload_lifecycle *p=ctx;struct timer_sink_receipt local={0};enum board_l_result r;
 if(receipt)*receipt=(struct timer_sink_receipt){0};
 if(!enter(p))return BOARD_L_UNCONFIGURED;
 if(!receipt){(void)fail(p,PL_ARGUMENT,BOARD_L_UNCONFIGURED);return BOARD_L_UNCONFIGURED;}
 r=tim3_preload_write(&p->preload,ccr,&local);
 if(r!=BOARD_L_OK){(void)fail(p,PL_PRELOAD,r);return r;}
 if(!owner(p))return BOARD_L_UNCONFIGURED;
 *receipt=local;p->busy=false;return BOARD_L_OK;
}
static void inhibit(void *ctx)
{
 struct preload_lifecycle *p=ctx;
 if(!p)return;
 if(p->self!=p){(void)fail(p,PL_CONTEXT,BOARD_L_UNCONFIGURED);return;}
 /* Independent inhibit remains available even when normal owner/preload checks
  * fail. This is request forwarding only; V31 owns dispatch coalescing. */
 if(!p->providers.request_off || !p->providers.inhibit_context)return;
 if(p->inhibit_busy){(void)fail(p,PL_REENTRANT,BOARD_L_UNCONFIGURED);return;}
 p->inhibit_busy=true;p->providers.request_off(p->providers.inhibit_context);p->inhibit_busy=false;
}
bool preload_lifecycle_configure(struct preload_lifecycle *p,const struct tim3_preload_config *c,
 const struct tim3_preload_transport *t,const struct preload_lifecycle_providers *providers)
{
 if(!p)return false;
 if(p->attempted)return fail(p,PL_REBIND,BOARD_L_UNCONFIGURED);
 p->attempted=true;p->self=p;
 if(!c || !t || !providers || !providers->owner_context || !providers->owner ||
 !providers->init_context || !providers->initialize_off || !providers->ready_context || !providers->ready ||
 !providers->inhibit_context || !providers->request_off)return fail(p,PL_CONFIG,BOARD_L_UNCONFIGURED);
 p->providers=*providers;p->epoch=c->epoch;
 if(!tim3_preload_configure(&p->preload,c,t))return fail(p,PL_CONFIG,BOARD_L_UNCONFIGURED);
 p->configured=true;return true;
}
bool preload_lifecycle_sink(struct preload_lifecycle *p,struct host_timer_sink *out)
{
 if(out)*out=(struct host_timer_sink){0};
 if(!p || !out || p->self!=p || !p->configured)return false;
 *out=(struct host_timer_sink){p,initialize,ready,write_preload,inhibit};return true;
}
