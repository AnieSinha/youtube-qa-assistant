import { useState, useRef, useEffect, useMemo } from 'react'
import { marked } from 'marked'
import './ChatSection.css'

marked.setOptions({ breaks: true, gfm: true })

function renderMd(text) {
  try { return { __html: marked.parse(text) } }
  catch { return { __html: text } }
}

/* ────── Avatar ────── */
function Avatar({ type }) {
  return (
    <div className={`avatar avatar-${type}`}>
      {type === 'user' ? (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      ) : (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
        </svg>
      )}
    </div>
  )
}

/* ────── Source Chip ────── */
function SourceChip({ timestamp, preview, onSeek }) {
  return (
    <button className="src-chip" title={preview} onClick={() => onSeek(timestamp)}>
      <span className="src-ts">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
        </svg>
        {timestamp}
      </span>
      <span className="src-pv">{preview.slice(0, 45)}{preview.length > 45 ? '...' : ''}</span>
    </button>
  )
}

/* ────── Response Loader (shimmer skeleton) ────── */
function ResponseLoader() {
  return (
    <div className="msg-row msg-bot">
      <Avatar type="bot" />
      <div className="msg-body">
        <div className="loader-bubble">
          <div className="loader-header">
            <div className="loader-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/>
              </svg>
            </div>
            <span className="loader-label">Analyzing transcript...</span>
          </div>
          <div className="shimmer-lines">
            <div className="shimmer-line" style={{ width: '92%' }} />
            <div className="shimmer-line" style={{ width: '78%', animationDelay: '0.15s' }} />
            <div className="shimmer-line" style={{ width: '85%', animationDelay: '0.3s' }} />
            <div className="shimmer-line short" style={{ width: '55%', animationDelay: '0.45s' }} />
          </div>
        </div>
      </div>
    </div>
  )
}

/* ────── Message Bubble ────── */
function MessageBubble({ msg, onSeek }) {
  const isUser = msg.role === 'user'

  const html = useMemo(() => {
    if (isUser) return null
    return renderMd(msg.content || '')
  }, [msg.content, isUser])

  return (
    <div className={`msg-row msg-${msg.role}`}>
      <Avatar type={msg.role} />
      <div className="msg-body">
        <div className={`bubble ${msg.streaming ? 'streaming' : ''}`}>
          {isUser ? (
            msg.content
          ) : (
            <div className="md-content" dangerouslySetInnerHTML={html} />
          )}
        </div>
        {!isUser && !msg.streaming && msg.sources && msg.sources.length > 0 && (
          <div className="src-row">
            {msg.sources.map((s, i) => (
              <SourceChip key={i} {...s} onSeek={onSeek} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/* ────── Main ChatSection ────── */
export default function ChatSection({ messages, onAsk, onSeek, onClear, disabled, isAsking, width }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = () => {
    if (!input.trim() || disabled || isAsking) return
    onAsk(input.trim())
    setInput('')
  }

  // Determine if the last bot message is empty and still streaming
  const showLoader = isAsking && messages.length > 0 &&
    messages[messages.length - 1]?.role === 'bot' &&
    !messages[messages.length - 1]?.content

  return (
    <section className="chat-sec" style={{ width: `${width}px`, minWidth: '320px' }}>
      {/* Header */}
      <div className="chat-head">
        <div className="chat-head-l">
          <div className="chat-head-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
            </svg>
          </div>
          <div>
            <h2 className="ch-title">Conversation</h2>
            <p className="ch-sub">{disabled ? 'Process a video first' : 'Ask questions about the video'}</p>
          </div>
        </div>
        <button className="ch-clear" onClick={onClear} title="Clear">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
          </svg>
        </button>
      </div>

      {/* Messages */}
      <div className="msg-list">
        {messages.length === 0 && (
          <div className="msg-empty">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <p>Your conversation will appear here</p>
          </div>
        )}

        {messages.map((msg, i) => {
          // Don't render the empty bot message placeholder; show loader instead
          if (msg.role === 'bot' && !msg.content && msg.streaming) return null
          return <MessageBubble key={i} msg={msg} onSeek={onSeek} />
        })}

        {showLoader && <ResponseLoader />}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-foot">
        <div className="input-box">
          <input
            className="chat-in"
            type="text"
            placeholder={disabled ? 'Process a video first...' : 'Type your question...'}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            disabled={disabled || isAsking}
          />
          <button
            className="send-btn"
            onClick={handleSubmit}
            disabled={disabled || isAsking || !input.trim()}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
          </button>
        </div>
      </div>
    </section>
  )
}
