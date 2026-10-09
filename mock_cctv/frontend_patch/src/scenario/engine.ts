export type PlaybackStatus = 'idle'|'playing'|'paused'|'complete'|'error'
interface Player { video:HTMLVideoElement; offset:number; id:string; cleanup:()=>void }
export class PlaybackEngine {
 private players = new Set<Player>()
 private epoch = 0
 private intent = false
 position = 0
 status:PlaybackStatus = 'idle'
 error = ''
 buffering = false
 constructor(private ids:string[], private changed:()=>void, _now=()=>performance.now()) {}
 get ready(){return new Set([...this.players].filter(p=>p.video.readyState>=2&&Number.isFinite(p.video.duration)).map(p=>p.id)).size}
 get duration(){return Math.max(0,...[...this.players].filter(p=>Number.isFinite(p.video.duration)).map(p=>Math.max(0,p.video.duration-p.offset)))}
 register(video:HTMLVideoElement,offset:number,id:string){
  const update=()=>{this.align(player);this.changed()}
  const fail=()=>this.fail('영상 로드 실패 · 연결과 영상 파일을 확인하세요.')
  const player:Player={video,offset,id,cleanup:()=>{video.removeEventListener('loadeddata',update);video.removeEventListener('canplay',update);video.removeEventListener('error',fail)}}
  this.players.add(player);video.addEventListener('loadeddata',update);video.addEventListener('canplay',update);video.addEventListener('error',fail)
  update()
  return()=>{video.pause();player.cleanup();this.players.delete(player);this.changed()}
 }
 private fail(message:string){this.epoch++;this.intent=false;this.status='error';this.error=message;for(const p of this.players)p.video.pause();this.changed()}
 private startVideo(video:HTMLVideoElement){const token=this.epoch;void video.play().catch(()=>{if(token===this.epoch&&this.intent)this.fail('영상 재생이 실패했습니다. 다시 재생하거나 연결을 확인하세요.')})}
 private align(p:Player,seek=true){
  if(!Number.isFinite(p.video.duration))return
  const target=Math.min(p.video.duration,Math.max(0,this.position+p.offset))
  if(seek&&Math.abs(p.video.currentTime-target)>.3)p.video.currentTime=target
  if(this.intent&&p.video.currentTime<p.video.duration){if(p.video.paused)this.startVideo(p.video)}else p.video.pause()
 }
 play(){
  if(this.ids.some(id=>![...this.players].some(p=>p.id===id&&p.video.readyState>=2&&Number.isFinite(p.video.duration)))){this.fail('9개 영상이 준비된 뒤 재생하세요.');return false}
  if(this.status==='complete')this.reset()
  const seek=this.status==='idle'||this.status==='error'
  this.epoch++;this.intent=true;this.status='playing';this.error='';this.buffering=false
  for(const p of this.players)this.align(p,seek)
  this.changed();return true
 }
 pause(){this.epoch++;this.intent=false;this.buffering=false;this.status=this.position>=this.duration&&this.duration>0?'complete':'paused';for(const p of this.players)p.video.pause();this.changed()}
 reset(){this.epoch++;this.intent=false;this.position=0;this.status='idle';this.error='';this.buffering=false;for(const p of this.players)this.align(p);this.changed()}
 tick(){
  if(!this.intent)return
  const active=[...this.players].filter(p=>p.video.currentTime<p.video.duration)
  this.buffering=active.some(p=>p.video.readyState<2||p.video.seeking)
  // Use decoded media time. Repeated seeks across nine decoders can stall playback.
  this.position=Math.min(this.duration,Math.max(0,...[...this.players].map(p=>p.video.currentTime-p.offset)))
  for(const p of this.players)this.align(p,false)
  if(!active.length&&this.players.size){this.intent=false;this.status='complete';for(const p of this.players)p.video.pause()}
  this.changed()
 }
 dispose(){this.epoch++;this.intent=false;for(const p of this.players){p.video.pause();p.cleanup()}this.players.clear()}
}
