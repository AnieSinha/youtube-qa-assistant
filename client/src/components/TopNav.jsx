import { useState, useRef, useEffect } from 'react'
import './TopNav.css'

export default function TopNav({ status, statusMsg, onProcess, isProcessing, theme, onToggleTheme }) {
  const [urls, setUrls] = useState([''])
  const navRef = useRef(null)

  // Keep --nav-h in sync with actual nav height so main layout adjusts
  useEffect(() => {
    if (!navRef.current) return
    const ro = new ResizeObserver(() => {
      document.documentElement.style.setProperty('--nav-h', navRef.current.offsetHeight + 'px')
    })
    ro.observe(navRef.current)
    return () => ro.disconnect()
  }, [])

  const updateUrl = (i, value) => {
    const next = [...urls]; next[i] = value; setUrls(next)
  }

  const addUrl = () => {
    if (urls.length < 3) setUrls([...urls, ''])
  }

  const removeUrl = (i) => {
    const next = urls.filter((_, idx) => idx !== i)
    setUrls(next.length ? next : [''])
  }

  const handleSubmit = () => {
    const valid = urls.map(u => u.trim()).filter(Boolean)
    if (valid.length) onProcess(valid)
  }

  const count      = urls.filter(u => u.trim()).length
  const canAdd     = urls.length < 3 && !isProcessing
  const isMulti    = urls.length > 1

  const statusLabels = { idle: 'Ready', processing: 'Processing…', ready: 'Video Ready', error: 'Error' }

  return (
    <nav ref={navRef} className={`topnav${isMulti ? ' topnav-multi' : ''}`}>
      {/* Brand */}
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

      {/* URL input stack */}
      <div className="nav-search">
        {urls.map((url, i) => (
          <div key={i} className="url-row">
            {/* Video number badge */}
            {isMulti && (
              <span className="url-badge">V{i + 1}</span>
            )}

            {/* Input pill */}
            <div className={`url-pill${i === 0 ? ' url-pill-primary' : ''}`}>
              <svg className="pill-icon" width="13" height="13" viewBox="0 0 24 24"
                   fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input
                className="url-input"
                type="url"
                placeholder={
                  isMulti
                    ? (i === 0 ? 'Video 1 — paste YouTube URL…' : `Video ${i + 1} — paste YouTube URL…`)
                    : 'Paste a YouTube URL…'
                }
                value={url}
                onChange={e => updateUrl(i, e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                disabled={isProcessing}
              />

              {/* Row 0 actions: add + analyze */}
              {i === 0 && canAdd && (
                <button className="add-btn" onClick={addUrl} title="Compare another video">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
                       stroke="currentColor" strokeWidth="2.5">
                    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                  </svg>
                  <span>Video</span>
                </button>
              )}

              {i === 0 && (
                <button
                  className="search-btn"
                  onClick={handleSubmit}
                  disabled={isProcessing || count === 0}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                       stroke="currentColor" strokeWidth="2.5">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  <span>{isProcessing ? 'Analyzing…' : count > 1 ? `Analyze (${count})` : 'Analyze'}</span>
                </button>
              )}

              {/* Secondary rows: remove button */}
              {i > 0 && (
                <button
                  className="remove-btn"
                  onClick={() => removeUrl(i)}
                  disabled={isProcessing}
                  title="Remove this video"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                       stroke="currentColor" strokeWidth="2.5">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Right actions */}
      <div className="nav-actions">
        <button className="theme-toggle" onClick={onToggleTheme}
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
          {theme === 'dark' ? (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>  <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>  <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          )}
        </button>

        <div className={`status-chip status-${status}`}>
          <span className="status-dot"/>
          <span>{statusLabels[status] || 'Idle'}</span>
        </div>
      </div>
    </nav>
  )
}
