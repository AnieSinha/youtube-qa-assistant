import { useState } from 'react'
import './TopNav.css'

export default function TopNav({ status, statusMsg, onProcess, isProcessing, theme, onToggleTheme }) {
  const [url, setUrl] = useState('')

  const handleSubmit = () => {
    if (url.trim()) onProcess(url.trim())
  }

  const statusLabels = {
    idle: 'Ready',
    processing: 'Processing...',
    ready: 'Video Ready',
    error: 'Error',
  }

  return (
    <nav className="topnav">
      <div className="nav-brand">
        <div className="brand-logo">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="#fff">
            <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356
              2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246
              15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549
              -4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
          </svg>
        </div>
        <span className="brand-text">TubeAI</span>
      </div>

      <div className="nav-search">
        <div className="search-bar">
          <svg className="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            className="search-input"
            type="url"
            placeholder="Paste a YouTube URL..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            disabled={isProcessing}
          />
          <button className="search-btn" onClick={handleSubmit} disabled={isProcessing || !url.trim()}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            <span>{isProcessing ? 'Analyzing...' : 'Analyze'}</span>
          </button>
        </div>
      </div>

      <div className="nav-actions">
        {/* Theme toggle */}
        <button className="theme-toggle" onClick={onToggleTheme} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
          {theme === 'dark' ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
        </button>

        {/* Status pill */}
        <div className={`status-chip status-${status}`}>
          <span className="status-dot" />
          <span>{statusLabels[status] || statusMsg}</span>
        </div>
      </div>
    </nav>
  )
}
