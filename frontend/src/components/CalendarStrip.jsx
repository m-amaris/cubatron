import React, { useEffect, useRef } from 'react'

function formatDay(d) {
  return d.toLocaleDateString(undefined, { weekday: 'short' })
}

export default function CalendarStrip() {
  const today = new Date()
  // start 14 days ago
  const start = new Date(today)
  start.setDate(today.getDate() - 14)
  // show inclusive range from 14 days ago to today (15 days)
  const days = Array.from({ length: 15 }).map((_, i) => {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    return d
  })
  const containerRef = useRef(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    // Wait a frame to ensure layout is ready then scroll so today is visible
    requestAnimationFrame(() => {
      const todayEl = el.querySelector('[data-today="true"]')
      if (todayEl) {
        const offset = todayEl.offsetLeft + todayEl.offsetWidth - el.clientWidth
        const left = Math.max(0, offset)
        el.scrollTo({ left, behavior: 'smooth' })
      } else {
        el.scrollTo({ left: el.scrollWidth, behavior: 'smooth' })
      }
    })
  }, [])

  return (
    <div ref={containerRef} className="flex gap-2 overflow-x-auto py-2">
      {days.map((d) => {
        const isToday = d.toDateString() === today.toDateString()
        return (
          <div
            key={d.toISOString()}
            data-today={isToday ? 'true' : 'false'}
            className={`min-w-[48px] p-2 rounded-xl flex flex-col items-center justify-center text-center ${isToday ? 'text-indigo-700 shadow-md' : 'bg-gray-100 text-gray-700'}`}
            style={isToday ? {backgroundColor: `rgba(var(--accent-color-rgb),0.08)`} : {}}
          >
            <div className="text-xs text-gray-500 leading-none">{formatDay(d)}</div>
            <div className="font-semibold mt-1 leading-tight">{d.getDate()}</div>
          </div>
        )
      })}
    </div>
  )
}
