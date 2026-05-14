import { useState, useEffect, useRef, useCallback } from 'react'
import TopNav from './components/TopNav'
import VideoSection from './components/VideoSection'
import ChatSection from './components/ChatSection'
import ProcessingBar from './components/ProcessingBar'
import ResizeHandle from './components/ResizeHandle'
import './App.css'

export default function App() {
  const [status, setStatus]       = useState('idle')
  const [statusMsg, setStatusMsg] = useState('')
  const [videoUrl, setVideoUrl]   = useState(null)
  const [videoId, setVideoId]     = useState(null)
  const [seekTime, setSeekTime]   = useState(null)
  const [messages, setMessages]   = useState([])
  const [isAsking, setIsAsking]   = useState(false)
  const [chatWidth, setChatWidth] = useState(440)
  const [theme, setTheme]         = useState(() => localStorage.getItem('tubeai-theme') || 'dark')
  const pollRef = useRef(null)

  // Apply theme to DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('tubeai-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  // Extract YouTube video ID
  const extractVideoId = (url) => {
    try {
      const u = new URL(url)
      if (u.hostname === 'youtu.be') return u.pathname.slice(1).split('?')[0]
      if (u.hostname.includes('youtube.com')) return u.searchParams.get('v')
    } catch {}
    return null
  }

  // Parse timestamp to seconds
  const parseTimestamp = (ts) => {
    const parts = ts.split(':').map(Number)
    if (parts.some(isNaN)) return null
    if (parts.length === 2) return parts[0] * 60 + parts[1]
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return null
  }

  // Fetch status on mount
  useEffect(() => {
    fetch('/api/status')
      .then(r => r.json())
      .then(data => {
        applyState(data)
        if (data.status === 'processing') startPolling()
      })
      .catch(() => {
        setStatus('error')
        setStatusMsg('Server offline')
      })
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  const applyState = (data) => {
    setStatus(data.status)
    setStatusMsg(data.message || data.error || '')
    if (data.video_url) {
      setVideoUrl(data.video_url)
      setVideoId(extractVideoId(data.video_url))
    }
  }

  const startPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch('/api/status')
        const data = await res.json()
        applyState(data)
        if (data.status !== 'processing') {
          clearInterval(pollRef.current)
          pollRef.current = null
        }
      } catch {}
    }, 1500)
  }

  // Process video
  const handleProcess = async (url) => {
    setStatus('processing')
    setStatusMsg('Starting pipeline...')
    setVideoUrl(url)
    setVideoId(extractVideoId(url))
    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })
      const data = await res.json()
      if (data.detail) {
        setStatus('error')
        setStatusMsg(data.detail)
        return
      }
      startPolling()
    } catch {
      setStatus('error')
      setStatusMsg('Server unreachable')
    }
  }

  // Ask question with streaming
  const handleAsk = useCallback(async (question) => {
    if (!question.trim() || isAsking) return

    setIsAsking(true)
    const userMsg = { role: 'user', content: question }
    const botMsg  = { role: 'bot', content: '', sources: [], streaming: true }
    setMessages(prev => [...prev, userMsg, botMsg])

    try {
      const response = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        const err = await response.json()
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          last.content = err.detail || 'An error occurred.'
          last.streaming = false
          return updated
        })
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullText = ''
      let sources = []
      let eventType = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.slice(6))
              if (eventType === 'token') {
                fullText += parsed.content
                setMessages(prev => {
                  const updated = [...prev]
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    content: fullText,
                  }
                  return updated
                })
              } else if (eventType === 'sources') {
                sources = parsed
              } else if (eventType === 'error') {
                fullText = parsed.detail || 'Error'
              }
            } catch {}
            eventType = null
          }
        }
      }

      // Finalize
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: fullText,
          sources,
          streaming: false,
        }
        return updated
      })

    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: 'Could not reach the server.',
          streaming: false,
        }
        return updated
      })
    } finally {
      setIsAsking(false)
    }
  }, [isAsking])

  // Seek video
  const handleSeek = (timestamp) => {
    const seconds = parseTimestamp(timestamp)
    if (seconds !== null) setSeekTime(seconds)
  }

  return (
    <div className="app-shell">
      <TopNav
        status={status}
        statusMsg={statusMsg}
        onProcess={handleProcess}
        isProcessing={status === 'processing'}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <div className="main-layout">
        {/* Processing bar — non-blocking, sits above the video */}
        {status === 'processing' && (
          <ProcessingBar message={statusMsg} />
        )}

        <VideoSection
          videoId={videoId}
          seekTime={seekTime}
          isEmpty={!videoId}
        />

        <ResizeHandle chatWidth={chatWidth} setChatWidth={setChatWidth} />

        <ChatSection
          messages={messages}
          onAsk={handleAsk}
          onSeek={handleSeek}
          onClear={() => setMessages([])}
          disabled={status !== 'ready'}
          isAsking={isAsking}
          width={chatWidth}
        />
      </div>
    </div>
  )
}
