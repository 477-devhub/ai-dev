export interface AnalysisSource {camera_id:string;clip_ref:string;duration_sec:number;reused_from:string|null}
export interface AnalysisJob {job_id:string;state:'queued'|'preparing'|'cv'|'p1'|'p4'|'completed'|'failed';camera_id:string;needs_review:boolean|null;incident_id:string|null;suppressed_id:string|null;error_code:string|null;stage_trace:{stage:string;status:string}[]}
export interface CycleRow {source:AnalysisSource;state:string;job?:AnalysisJob;error?:string}
const storageKey='477-recorded-analysis-cycle-v1'
export function rememberCycle(rows:CycleRow[]){
 try{if(typeof sessionStorage!=='undefined')sessionStorage.setItem(storageKey,JSON.stringify(rows))}catch{/* Storage is optional. */}
}
export class AnalysisCycle {
 rows:CycleRow[]
 active=false
 finished=false
 private keys=new Map<string,string>()
 constructor(sources:AnalysisSource[],private changed:()=>void,private transport:typeof fetch=(...args)=>fetch(...args),private wait=(ms:number)=>new Promise<void>(r=>setTimeout(r,ms)),private now=()=>Date.now()){
  this.rows=sources.map(source=>({source,state:source.reused_from?'reused':'idle'}))
  try{
   const saved:CycleRow[]=typeof sessionStorage!=='undefined'?JSON.parse(sessionStorage.getItem(storageKey)??'[]'):[]
   if(saved.length===sources.length&&saved.every((r,i)=>r.source.camera_id===sources[i].camera_id&&r.source.clip_ref===sources[i].clip_ref&&r.source.duration_sec===sources[i].duration_sec)){
    this.rows=saved.map(r=>r.job?{...r,state:r.job.state,error:undefined}:{source:r.source,state:r.source.reused_from?'reused':'idle'})
    this.finished=this.rows.filter(r=>!r.source.reused_from).every(r=>['completed','failed'].includes(r.state))
   }
  }catch{/* Ignore unavailable or malformed tab storage. */}
  let savedKeys:Record<string,string>={}
  try{if(typeof sessionStorage!=='undefined')savedKeys=JSON.parse(sessionStorage.getItem(storageKey+'-keys')??'{}')}catch{/* Optional storage. */}
  for(const s of sources){const signature=JSON.stringify([s.camera_id,s.clip_ref,s.duration_sec]);const key=typeof savedKeys[signature]==='string'?savedKeys[signature]:crypto.randomUUID();this.keys.set(s.camera_id,key);savedKeys[signature]=key}
  try{if(typeof sessionStorage!=='undefined')sessionStorage.setItem(storageKey+'-keys',JSON.stringify(savedKeys))}catch{/* Optional storage. */}
 }
 private publish(){rememberCycle(this.rows);this.changed()}
 private async request(path:string,body?:unknown,key?:string){
  const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),10000)
  try{
   const r=await this.transport(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json','Idempotency-Key':key!}:undefined,body:body?JSON.stringify(body):undefined,signal:abort.signal,cache:'no-store'})
   const value=await r.json()
   if(!r.ok)throw Object.assign(Error(value?.error?.message??value?.detail??`요청 실패 (${r.status})`),{status:r.status})
   return value
  }finally{clearTimeout(timer)}
 }
 async run(){
  if(this.active||this.finished)return
  this.active=true;this.publish()
  try{
   for(const row of this.rows.filter(r=>!r.source.reused_from)){
    if(row.job)continue
    row.state='submitting';this.publish()
    const body={camera_id:row.source.camera_id,clip_ref:row.source.clip_ref,start_ms:0,end_ms:Math.floor(row.source.duration_sec*1000)}
    try{
     // A network retry keeps the same idempotency key, never creates a second job.
     let job:AnalysisJob
     try{job=await this.request('/api/analysis/jobs',body,this.keys.get(row.source.camera_id))}
     catch(e){if(e instanceof TypeError||e instanceof DOMException)job=await this.request('/api/analysis/jobs',body,this.keys.get(row.source.camera_id));else throw e}
     if(!job.job_id)throw Error('작업 응답 형식이 맞지 않습니다.')
     row.job=job;row.state=job.state
    }catch(e){row.state='failed';row.error=e instanceof Error?e.message:'분석 접수 실패'}
    this.publish()
   }
   const deadline=this.now()+3*60*60*1000
   while(this.rows.some(r=>r.job&&!['completed','failed'].includes(r.state))){
    if(this.now()>deadline){for(const row of this.rows.filter(r=>r.job&&!['completed','failed'].includes(r.state))){row.state='failed';row.error='결과 조회 시간이 초과됐습니다. 서버 작업은 계속될 수 있습니다.'}break}
    await this.wait(2000)
    for(const row of this.rows.filter(r=>r.job&&!['completed','failed'].includes(r.state))){
     try{const job:AnalysisJob=await this.request('/api/analysis/jobs/'+encodeURIComponent(row.job!.job_id));if(job.job_id!==row.job!.job_id)throw Error('작업 식별자가 맞지 않습니다.');row.job=job;row.state=job.state;row.error=undefined}
     catch(e){if((e as {status?:number}).status===404){row.state='failed';row.job=undefined;row.error='분석 작업이 없습니다. 서버 재시작 여부를 확인하세요.'}else row.error='결과 조회 연결 대기 · 서버 작업은 유지됩니다.'}
    }
    this.publish()
   }
   this.finished=true
  }finally{this.active=false;this.publish()}
 }
}

