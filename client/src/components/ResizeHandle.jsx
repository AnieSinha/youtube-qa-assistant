import { useCallback, useRef } from 'react'
import './ResizeHandle.css'

export default function ResizeHandle({ chatWidth, setChatWidth }) {
  const dragging = useRef(false)

  const onMouseDown = useCallback((e) => {
    e.preventDefault()
    dragging.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    const handleMove = (moveEvent) => {
      if (!dragging.current) return
      const windowW = window.innerWidth
      const newWidth = windowW - moveEvent.clientX
      // Clamp between 320 and 700
      setChatWidth(Math.max(320, Math.min(700, newWidth)))
    }

    const handleUp = () => {
      dragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      window.removeEventListener('mousemove', handleMove)
      window.removeEventListener('mouseup', handleUp)
    }

    window.addEventListener('mousemove', handleMove)
    window.addEventListener('mouseup', handleUp)
  }, [setChatWidth])

  return (
    <div className="resize-handle" onMouseDown={onMouseDown}>
      <div className="resize-grip">
        <span /><span /><span />
      </div>
    </div>
  )
}
