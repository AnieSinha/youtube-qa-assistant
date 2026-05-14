import './ProgressOverlay.css'

export default function ProgressOverlay({ message }) {
  return (
    <div className="overlay">
      <div className="overlay-card">
        <div className="ring-wrap">
          <svg className="ring" viewBox="0 0 60 60">
            <circle className="ring-bg" cx="30" cy="30" r="26"/>
            <circle className="ring-fg" cx="30" cy="30" r="26"/>
          </svg>
          <div className="ring-pulse" />
        </div>
        <div className="overlay-info">
          <h3>Processing Video</h3>
          <p>{message}</p>
        </div>
      </div>
    </div>
  )
}
