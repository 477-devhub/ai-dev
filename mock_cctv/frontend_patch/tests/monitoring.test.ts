import test from 'node:test'
import assert from 'node:assert/strict'
import { PlaybackEngine } from '../src/scenario/engine'
import { AnalysisCycle,rememberCycle } from '../src/scenario/analysisCycle'
function video(duration:number){return {duration,currentTime:0,readyState:4,seeking:false,paused:true,play(){this.paused=false;return Promise.resolve()},pause(){this.paused=true},addEventListener(){},removeEventListener(){}} as unknown as HTMLVideoElement}
test('one cycle ends at longest video, pause/resume preserves position, replay rewinds',()=>{
 let now=0;const e=new PlaybackEngine(['A','B'],()=>{},()=>now),a=video(2),b=video(3)
 e.register(a,0,'A');e.register(b,0,'B');assert.equal(e.play(),true)
 a.currentTime=1;b.currentTime=1;now=1000;e.tick();e.pause();now=6000;e.tick();assert.equal(e.position,1)
 e.play();a.currentTime=2;b.currentTime=2.5;now=7500;e.tick();assert.equal(a.paused,true);assert.equal(b.paused,false)
 b.currentTime=3;now=8500;e.tick();assert.equal(e.status,'complete');assert.equal(e.position,3);assert.equal(b.paused,true)
 e.play();assert.equal(e.position,0);assert.equal(a.currentTime,0)
})
test('missing player cannot start; media time does not run ahead of decoded frames or repeatedly seek',()=>{
 let now=0;const e=new PlaybackEngine(['A','B'],()=>{},()=>now),a=video(3),b=video(3)
 e.register(a,0,'A');assert.equal(e.play(),false);e.register(b,0,'B');e.play()
 Object.defineProperty(b,'readyState',{value:1,configurable:true});now=1000;e.tick();assert.equal(e.position,0)
 Object.defineProperty(b,'readyState',{value:4});a.currentTime=1;b.currentTime=.8;now=2000;e.tick();assert.equal(e.position,1);assert.equal(b.currentTime,.8)
})
test('late rejected play after reset does not poison a new playback session',async()=>{
 const v=video(3);let reject!:(error:Error)=>void;v.play=()=>new Promise((_,r)=>{reject=r})
 const e=new PlaybackEngine(['A'],()=>{});e.register(v,0,'A');e.play();e.reset();reject(Error('aborted'));await Promise.resolve();assert.equal(e.status,'idle')
})
test('analysis deduplicates reused camera, retries with same key, polls result, repeated play sends no jobs',async()=>{
 const requests:{key:string|null;body:any}[]=[];let first=true
 const transport:typeof fetch=async(input,init)=>{
  if(init?.method==='POST'){
   requests.push({key:new Headers(init.headers).get('Idempotency-Key'),body:JSON.parse(init.body as string)})
   if(first){first=false;throw new TypeError('network')}
   return Response.json({job_id:'J1',state:'queued'})
  }
  return Response.json({job_id:'J1',state:'completed',needs_review:true,stage_trace:[]})
 }
 const c=new AnalysisCycle([{camera_id:'CAM_02',clip_ref:'MOCK_CLIP_02',duration_sec:30.6,reused_from:null},{camera_id:'CAM_03',clip_ref:'MOCK_CLIP_03',duration_sec:30.6,reused_from:'CAM_02'}],()=>{},transport,async()=>{})
 await c.run();await c.run();assert.equal(requests.length,2);assert.equal(requests[0].key,requests[1].key);assert.equal(requests[0].body.end_ms,30600);assert.equal(c.rows[0].state,'completed');assert.equal(c.rows[1].state,'reused');assert.equal(c.finished,true)
})
test('failed acceptance is displayed and is never counted as successful analysis',async()=>{
 const c=new AnalysisCycle([{camera_id:'CAM_01',clip_ref:'MOCK_CLIP_01',duration_sec:30,reused_from:null}],()=>{},async()=>Response.json({detail:'adapter unavailable'},{status:503}),async()=>{})
 await c.run();assert.equal(c.rows[0].state,'failed');assert.match(c.rows[0].error!,/adapter unavailable/);assert.equal(c.active,false)
})
test('restored accepted jobs are polled without resubmitting, and a removed job fails visibly',async()=>{
 const values=new Map<string,string>();Object.defineProperty(globalThis,'sessionStorage',{configurable:true,value:{setItem:(k:string,v:string)=>values.set(k,v),getItem:(k:string)=>values.get(k)}})
 const source={camera_id:'CAM_01',clip_ref:'MOCK_CLIP_01',duration_sec:30,reused_from:null}
 rememberCycle([{source,state:'queued',job:{job_id:'old-job',state:'queued',camera_id:'CAM_01',needs_review:null,incident_id:null,suppressed_id:null,error_code:null,stage_trace:[]}}])
 try{
  let posts=0;const c=new AnalysisCycle([source],()=>{},async(_,init)=>{if(init?.method==='POST')posts++;return Response.json({detail:'not found'},{status:404})},async()=>{})
  await c.run();assert.equal(posts,0);assert.equal(c.rows[0].state,'failed');assert.match(c.rows[0].error!,/서버 재시작/)
 }finally{Reflect.deleteProperty(globalThis,'sessionStorage')}
})
test('default fetch is invoked independently of the AnalysisCycle receiver',async()=>{
 const original=globalThis.fetch;let calledOn:unknown
 globalThis.fetch=async function(this:unknown,_input,init){calledOn=this;return Response.json(init?.method==='POST'?{job_id:'J',state:'queued'}:{job_id:'J',state:'completed',stage_trace:[]})}
 try{const c=new AnalysisCycle([{camera_id:'CAM_01',clip_ref:'MOCK_CLIP_01',duration_sec:30,reused_from:null}],()=>{},undefined,async()=>{});await c.run();assert.notEqual(calledOn,c);assert.equal(c.rows[0].state,'completed')}finally{globalThis.fetch=original}
})
