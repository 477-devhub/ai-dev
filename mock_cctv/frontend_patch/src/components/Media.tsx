import { useEffect, useState, useRef } from 'react'
import { usePlayback } from '../scenario/playback'
import { mediaUrl } from '../console/apiProvider'
export function EvidenceImage({url,alt}:{url:string|null;alt:string}){
 const src=mediaUrl(url),[broken,setBroken]=useState(false)
 useEffect(()=>setBroken(false),[src])
 return src&&!broken?<img className="evidence-image" src={src} alt={alt} loading="lazy" onError={()=>setBroken(true)}/>:<p className="media-placeholder">근거 이미지 미제공 또는 불러오기 실패</p>
}
export function ServerVideo({url,start,end,camId}:{url:string|null;start?:number|null;end?:number|null;camId?:string}){
 const playback=usePlayback(),config=playback?.scenario?.cameras.find(c=>c.id===camId),register=playback?.register
 const streamSrc=mediaUrl(url),managed=!!(camId&&streamSrc?.startsWith('/stream/')&&playback?.enabled)
 const src=managed?`/mock-cctv-media/${camId}.mp4`:streamSrc
 const [broken,setBroken]=useState(false),ref=useRef<HTMLVideoElement>(null)
 useEffect(()=>setBroken(false),[src,start,end])
 useEffect(()=>{if(ref.current&&managed&&register&&!broken)return register(ref.current,config?.offset_sec??0,camId!)},[src,register,config,broken,managed,camId])
 return src&&!broken?<video key={src+':'+start+':'+end} ref={ref} className="tile-frame" src={src} controls={!managed} muted playsInline preload={managed?'auto':'metadata'}
 onError={()=>setBroken(true)}
 onLoadedMetadata={e=>{const v=e.currentTarget;if(!config&&start!=null&&start>=0&&start<v.duration)v.currentTime=start;else if(!config&&start!=null)setBroken(true)}}
 onPlay={e=>{const v=e.currentTarget;if(!config&&end!=null&&v.currentTime>=end&&start!=null)v.currentTime=start}}
 onTimeUpdate={e=>{if(!config&&end!=null&&e.currentTarget.currentTime>=end)e.currentTarget.pause()}}/>:<p className="media-placeholder">영상 미제공 또는 재생 실패</p>
}
