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
export function PlaybackControls(){
 const p=usePlayback()
 if(!p?.enabled)return null
 return <div className="monitoring-controls" aria-label="예시 데이터 재생">
  <span className="sample-data-label">예시 데이터</span>
  <button type="button" className="btn btn-primary" disabled={p.playing||p.ready<9} onClick={p.play} title={p.error||undefined}>{p.playing?'재생 중':p.status==='complete'?'다시 재생':'재생'}</button>
 </div>
}
