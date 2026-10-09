import { PlaybackProvider } from './scenario/playback'
import mockSources from './fixtures/mock-cctv.json'
import { useEffect, useState } from 'react'
import { Header } from './components/Header'
import { CctvWall } from './components/CctvWall'
import { AnalysisPanel } from './components/AnalysisPanel'
import { QueuePanel } from './components/QueuePanel'
import { DetailView } from './components/DetailView'
import { useConsole, type ViewState, type SourceMode } from './console/useConsole'
import { useClock } from './useClock'
import { useFitScale } from './useFitScale'
const hashStep=()=>{const n=Number(window.location.hash.slice(1));return Number.isInteger(n)&&n>=1&&n<=6?n:1}
export default function App(){
 const mode:SourceMode=new URLSearchParams(location.search).get('source')==='local'?'local':'api'
 return <ConsoleApp key={mode} mode={mode}/>
}
function ConsoleApp({mode}:{mode:SourceMode}){
 const [step,setStep]=useState(hashStep),[listStep,setListStep]=useState(3),[selectedId,setSelectedId]=useState<string|null>(null)
 const clock=useClock(),fit=useFitScale(),state=useConsole(step===6?listStep:step,selectedId,mode)
 useEffect(()=>{const handler=()=>setStep(hashStep());window.addEventListener('hashchange',handler);return()=>window.removeEventListener('hashchange',handler)},[])
 const goTo=(n:number)=>{if(n===6&&step!==6&&step>=3)setListStep(step);setStep(n);window.history.replaceState(null,'','#'+n)}
 const open=(id:string)=>{setSelectedId(id);goTo(6)}
 const canMutate=state.busy||state.viewState!=='ready'
 const connected=mode==='api'&&state.connection==='connected'
 return <PlaybackProvider scenario={state.scenario} sources={mockSources} enabled={mode==='api'} canAnalyze={mode==='api'&&state.snapshot?.is_demo===false&&state.viewState==='ready'&&new URLSearchParams(location.search).get('analysis')!=='off'}><div className="app" style={fit}>
  <Header clock={clock} connection={(mode==='local'?'로컬':connected?'API 연결':'연결 대기')+(state.snapshot?.is_demo||mode==='local'?' · 합성 데모':'')}>
  <section className="connection-tools" aria-label="데이터 연결 설정"><b>{mode==='local'?'로컬 fixture':connected?'백엔드 API 연결됨':'백엔드 연결 확인 중'} · {state.snapshot?.is_demo || mode==='local'?state.scenario?'시나리오 판단 · AI 미연결':'합성 데모':'개발 입력'}</b>
   <a href={mode==='local'?'/?source=api':'/?source=local'}>{mode==='local'?'API 모드':'로컬 모드'}</a>
   {mode==='local'?<label>표시 상태 <select value={state.viewState} onChange={e=>state.setViewState(e.target.value as ViewState)}><option value="ready">로컬 데이터</option><option value="loading">로딩 예시</option><option value="error">오류 예시</option><option value="stale">오래된 데이터 예시</option></select></label>:<><button type="button" className="btn" disabled={state.busy} onClick={()=>void state.retry()}>다시 조회</button></>}
  </section>
  </Header>
  <div className="console-notices">
  {state.viewState!=='ready'&&<div className="connection-banner" role="status">{state.viewState==='loading'?'데이터 조회 중':state.viewState==='error'?'서버 조회 실패 · 실제 상태를 확인할 수 없습니다.':'갱신 연결 확인 중 · 마지막 데이터일 수 있습니다. 행동 처리가 잠겨 있습니다.'}</div>}
  {state.error&&<div className="connection-banner" role="alert">{state.error}</div>}{step===6&&state.detailError&&<div className="connection-banner" role="alert">{state.detailError}</div>}{state.message&&<div className="action-feedback" role="status">{state.message}</div>}
  </div>
  {!state.snapshot?<p className="wall-empty">데이터 대기 중 · 로컬 예시로 자동 대체하지 않습니다.</p>:<><main className="body" hidden={step===6}><div className="left"><CctvWall remote={mode==='api'} snapshot={state.snapshot}/><AnalysisPanel snapshot={state.snapshot}/></div><QueuePanel remote={mode==='api'} snapshot={state.snapshot} suppressed={state.suppressed} busy={canMutate} onOpen={open} onVerify={id=>state.ack(id,{action:'verify'})} onRestore={state.restore}/></main>{step===6&&<DetailView key={selectedId} remote={mode==='api'} snapshot={state.snapshot} incident={state.incident} clip={state.clip} busy={canMutate} onBack={()=>goTo(listStep)} onOpen={open} onAck={state.ack}/>}</>}
 </div></PlaybackProvider>
}
