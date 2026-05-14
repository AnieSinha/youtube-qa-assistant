import { useEffect, useRef } from 'react'
import './VideoSection.css'

/* ── Video tab bar (only shown when 2–3 videos are loaded) ── */
function VideoTabs({ videoIds, videoUrls, videoTitles, activeIdx, onSelect }) {
  if (!videoIds || videoIds.length <= 1) return null

  return (
    <div className="video-tabs">
      {videoIds.map((id, i) => {
        const title = videoTitles?.[videoUrls?.[i]] || `Video ${i + 1}`
        const short = title.length > 22 ? title.slice(0, 22) + '…' : title
        return (
          <button
            key={i}
            className={`video-tab ${i === activeIdx ? 'active' : ''}`}
            onClick={() => onSelect(i)}
          >
            <span className="tab-num">V{i + 1}</span>
            <span className="tab-title">{short}</span>
          </button>
        )
      })}
    </div>
  )
}

/* ── Main component ── */
export default function VideoSection({
  videoIds, videoUrls, videoTitles,
  activeVideoIdx, onSelectVideo,
  seekTime, isEmpty,
}) {
  const iframeRef = useRef(null)
  const activeId  = videoIds?.[activeVideoIdx] || null

  // Seek: update iframe src with new start time
  useEffect(() => {
    if (activeId && seekTime !== null && iframeRef.current) {
      iframeRef.current.src =
        `https://www.youtube.com/embed/${activeId}?enablejsapi=1&start=${seekTime}&autoplay=1`
    }
  }, [seekTime, activeId])

  // Reset iframe when switching videos (without a seek)
  useEffect(() => {
    if (activeId && iframeRef.current && seekTime === null) {
      iframeRef.current.src =
        `https://www.youtube.com/embed/${activeId}?enablejsapi=1`
    }
  }, [activeVideoIdx, activeId])

  if (isEmpty) {
    return (
      <section className="video-sec">
        <div className="ambient-glow"/>
        <div className="empty-state">
          <div className="empty-vis">
            <div className="empty-orb"/>
            <div className="empty-box">
              <svg width="56" height="56" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="1.2">
                <rect x="2" y="3" width="20" height="14" rx="2"/>
                <polygon points="9.5 7.5 9.5 13.5 14.5 10.5" fill="currentColor" opacity="0.2" stroke="currentColor"/>
                <line x1="12" y1="20" x2="12" y2="17" strokeWidth="1.5"/>
                <line x1="8" y1="20" x2="16" y2="20" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
          </div>
          <h2 className="empty-h">No video loaded</h2>
          <p className="empty-p">Paste a YouTube URL above and click <strong>Analyze</strong></p>
          <div className="pills">
            <div className="pill">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/>
              </svg>
              AI Analysis
            </div>
            <div className="pill">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              Timestamps
            </div>
            <div className="pill">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
              Multi-Video
            </div>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="video-sec">
      <div className="ambient-glow"/>

      <VideoTabs
        videoIds={videoIds}
        videoUrls={videoUrls}
        videoTitles={videoTitles}
        activeIdx={activeVideoIdx}
        onSelect={onSelectVideo}
      />

      <div className="player-wrap">
        <div className="player-frame">
          <iframe
            ref={iframeRef}
            src={`https://www.youtube.com/embed/${activeId}?enablejsapi=1`}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      </div>
    </section>
  )
}
