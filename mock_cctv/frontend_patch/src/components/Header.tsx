import type { ReactNode } from 'react'
import { PlaybackControls } from '../scenario/playback'
import logoMark from '../assets/logo-mark.svg'
import wordmark4 from '../assets/wordmark-4.svg'
import wordmark7Mirrored from '../assets/wordmark-7-mirrored.svg'
import wordmark7 from '../assets/wordmark-7.svg'
import dotLive from '../assets/dot-live.svg'

interface Props {
  clock: string
  connection: string
  children?: ReactNode
}

export function Header({ clock, connection, children }: Props) {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="brand">
          <img src={logoMark} alt="" />
          <div className="wordmark" role="img" aria-label="477">
            <span className="wordmark-4">
              <img src={wordmark4} alt="" />
            </span>
            <img src={wordmark7Mirrored} alt="" />
            <img src={wordmark7} alt="" />
          </div>
          <span className="brand-rule" />
          <span className="brand-tag">AI 관제 보조</span>
        </div>

        <div className="status">
          <span className="status-site">477 로컬 관제 데모</span>
          <span className="status-live">
            <img src={dotLive} alt="" />
            {connection}
          </span>
          <details className="header-tools"><summary>연결 설정</summary>{children}</details>
          <time className="status-clock">{clock}</time>
          <span className="user" aria-label="관제사">
            관
          </span>
          <PlaybackControls />
        </div>
      </div>
    </header>
  )
}
