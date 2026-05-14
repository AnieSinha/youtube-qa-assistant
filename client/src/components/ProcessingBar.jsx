import './ProcessingBar.css'

export default function ProcessingBar({ message }) {
  return (
    <div className="processing-bar">
      <div className="pb-track">
        <div className="pb-fill" />
      </div>
      <div className="pb-content">
        <div className="pb-spinner">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
        </div>
        <span className="pb-text">{message}</span>
      </div>
    </div>
  )
}
