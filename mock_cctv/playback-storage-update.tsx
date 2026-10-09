import { createContext,useCallback,useContext,useEffect,useRef,useState,type ReactNode } from 'react'
import type { DemoScenario } from './types'
import { PlaybackEngine } from './engine'
import { AnalysisCycle,rememberCycle,type AnalysisSource,type CycleRow } from './analysisCycle'
interface Playback {
 scenario:DemoScenario|null;playing:boolean;position:number;ready:number;error:string;duration:number;status:string;buffering:boolean
 register:(video:HTMLVideoElement,offset:number,id:string)=>()=>void
 play:()=>void;pause:()=>void;reset:()=>void;rows:CycleRow[];analysisActive:boolean;analysisFinished:boolean;canAnalyze:boolean;enabled:boolean
}
const Context=createContext<Playback|null>(null)
export const usePlayback=()=>useContext(Context)
export function PlaybackProvider({scenario,sources=[],canAnalyze=false,enabled=true,children}:{scenario:DemoScenario|null;sources?:AnalysisSource[];canAnalyze?:boolean;enabled?:boolean;children:ReactNode}){
 const [,render]=useState(0),mounted=useRef(true),notify=useCallback(()=>{if(mounted.current)render(n=>n+1)},[])
 const [engine]=useState(()=>new PlaybackEngine(sources.length?sources.map(s=>s.camera_id):Array.from({length:9},(_,i)=>`CAM_${String(i+1).padStart(2,'0')}`),notify))
 const [cycle]=useState(()=>new AnalysisCycle(sources,notify))
 useEffect(()=>{mounted.current=true;const timer=setInterval(()=>engine.tick(),100);return()=>{mounted.current=false;clearInterval(timer);engine.pause()}},[engine])
 const signature=JSON.stringify(scenario)
 useEffect(()=>{engine.reset()},[signature,engine])
 const register=useCallback((video:HTMLVideoElement,offset:number,id:string)=>engine.register(video,offset,id),[engine])
 const play=()=>{if(engine.play()&&canAnalyze&&!cycle.active&&!cycle.finished)void cycle.run()}
 return <Context.Provider value={{scenario,playing:engine.status==='playing',position:engine.position,ready:engine.ready,error:engine.error,duration:engine.duration,status:engine.status,buffering:engine.buffering,register,play,pause:()=>{rememberCycle(cycle.rows);engine.pause()},reset:()=>{rememberCycle(cycle.rows);engine.reset()},rows:cycle.rows,analysisActive:cycle.active,analysisFinished:cycle.finished,canAnalyze,enabled}}>{children}</Context.Provider>
}
const stages:Record<string,string>={idle:'대기',submitting:'접수 중',queued:'분석 대기',preparing:'프레임 준비',cv:'객체·동작 관측',p1:'1차 판단',p4:'정밀 판단',completed:'판단 완료',failed:'실패',reused:'영상 재사용'}
export function PlaybackControls(){
 const p=usePlayback()
 if(!p?.enabled)return null
 const analyzed=p.rows.filter(r=>!r.source.reused_from),done=analyzed.filter(r=>r.state==='completed').length,failed=analyzed.filter(r=>r.state==='failed').length
 const label=p.playing?'재생 중':p.status==='paused'?'이어 재생':p.status==='complete'?'다시 재생':'관제 시연 재생'
 const finished=p.status==='complete'&&p.analysisFinished
 return <section className="monitoring-controls" aria-label="관제 시연 제어">
  <div className="monitoring-main"><button type="button" className="btn btn-primary" disabled={p.playing||p.ready<9||(!p.canAnalyze&&!p.scenario)} onClick={p.play}>{label}</button><button type="button" className="btn" disabled={!p.playing} onClick={p.pause}>일시정지</button><button type="button" className="btn" onClick={p.reset}>영상 처음으로</button>
   <span role="status">{p.ready}/9 영상 준비 · {p.position.toFixed(1)} / {p.duration.toFixed(1)}초{p.buffering?' · 영상 버퍼링':''}{p.canAnalyze?` · AI 결과 ${done}/${analyzed.length}${failed?` · 실패 ${failed}`:''}`:''}{finished?' · 한 사이클 종료':p.status==='complete'&&p.analysisActive?' · 영상 종료, AI 결과 대기':''}</span></div>
  <small>{p.canAnalyze?'녹화 영상 전체 구간을 실제 AI로 분석합니다. 결과가 도착하면 사건·검토·제외 목록에 반영됩니다. 일시정지·다시 재생은 추가 분석을 요청하지 않습니다.':p.scenario?'녹화 영상 재생 · 시나리오 판단':'실제 AI 관제 시연 서버 연결을 기다리는 중입니다.'}</small>
  {p.error&&<p role="alert">{p.error}</p>}
  {p.canAnalyze&&<details className="analysis-progress"><summary>카메라별 AI 진행 상황</summary><div>{p.rows.map(row=><span key={row.source.camera_id}>{row.source.camera_id} · {row.source.reused_from?`${row.source.reused_from} 재사용 · ${stages[p.rows.find(r=>r.source.camera_id===row.source.reused_from)?.state??'idle']}`:stages[row.state]??row.state}{row.job?.needs_review?' · 사람 검토':''}{row.job?.stage_trace.some(s=>s.status==='failed')?' · 분석 단계 실패':''}{row.error?` · ${row.error}`:''}{row.job?.error_code?` · ${row.job.error_code}`:''}</span>)}</div></details>}
 </section>
}
