import test from 'node:test';
import assert from 'node:assert/strict';
import { chmod, mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { internal } from './compatibility-helpers.mjs';
const { launchChrome } = await internal('browser-smoke/chrome.js');
// Real executable argv/process teardown, fake CDP transport: no Chrome or browser runs.
test('installed launcher restores foreground argv/CDP and tears down success and connection failure',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'zudo-pd-fake-chrome-'));
 const bin=join(dir,'fake-chrome.mjs'), log=join(dir,'argv.json');
 const originalSocket=globalThis.WebSocket, previousLog=process.env.ZUDO_PD_FAKE_CHROME_LOG;
 let failConnection=false, methods=[], closed=0;
 class FakeSocket extends EventTarget {
  constructor(){super();queueMicrotask(()=>this.dispatchEvent(new Event(failConnection?'error':'open')));}
  send(payload){const request=JSON.parse(payload);methods.push(request.method);queueMicrotask(()=>this.dispatchEvent(new MessageEvent('message',{data:JSON.stringify({id:request.id,result:{}})})));}
  close(){closed++;this.dispatchEvent(new Event('close'));}
 }
 try {
  await writeFile(bin,`#!/usr/bin/env node\nimport {createServer} from 'node:http';\nimport {writeFileSync} from 'node:fs';\nconst argv=process.argv.slice(2);\nconst profile=argv.find(arg=>arg.startsWith('--user-data-dir=')).slice('--user-data-dir='.length);\nwriteFileSync(process.env.ZUDO_PD_FAKE_CHROME_LOG,JSON.stringify({argv,profile,pid:process.pid}));\nconst server=createServer((request,response)=>{response.writeHead(200,{'content-type':'application/json'});response.end(JSON.stringify([{type:'page',webSocketDebuggerUrl:'ws://127.0.0.1/fake-cdp'}]));});\nserver.listen(0,'127.0.0.1',()=>process.stderr.write('DevTools listening on ws://127.0.0.1:'+server.address().port+'/devtools/browser/fake\\n'));\n`);
  await chmod(bin,0o755);process.env.ZUDO_PD_FAKE_CHROME_LOG=log;globalThis.WebSocket=FakeSocket;
  const session=await launchChrome(bin), first=JSON.parse(await readFile(log,'utf8'));
  for(const flag of ['--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows'])assert.ok(first.argv.includes(flag),`launched child receives ${flag}`);
  assert.deepEqual(methods,['Page.enable','Page.bringToFront','Runtime.enable','Network.enable']);
  assert.ok((await stat(first.profile)).isDirectory());
  await session.close();assert.equal(closed,1);await assert.rejects(stat(first.profile),{code:'ENOENT'});assert.throws(()=>process.kill(first.pid,0),{code:'ESRCH'});
  failConnection=true;methods=[];await assert.rejects(launchChrome(bin),/could not connect to/u);
  const failed=JSON.parse(await readFile(log,'utf8'));assert.notEqual(failed.profile,first.profile);
  await assert.rejects(stat(failed.profile),{code:'ENOENT'});assert.throws(()=>process.kill(failed.pid,0),{code:'ESRCH'});
 } finally {globalThis.WebSocket=originalSocket;if(previousLog===undefined)delete process.env.ZUDO_PD_FAKE_CHROME_LOG;else process.env.ZUDO_PD_FAKE_CHROME_LOG=previousLog;await rm(dir,{recursive:true,force:true});}
});
