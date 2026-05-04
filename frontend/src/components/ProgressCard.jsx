import React from 'react'

function CircularProgress({ percent = 75, size = 88, stroke = 8, number = null, unit = '' }) {
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (percent / 100) * circumference
  const innerRadius = Math.max(0, radius - stroke / 2 - 2)
  return (
    <svg width={size} height={size} className="block text-gray-500">
      <g transform={`translate(${size / 2}, ${size / 2})`}>
        <circle r={radius} stroke="var(--accent-color)" strokeWidth={stroke} fill="none" strokeOpacity="0.12" />
        <circle r={radius} stroke="var(--accent-color)" strokeWidth={stroke} fill="none" strokeLinecap="round" strokeDasharray={`${circumference} ${circumference}`} strokeDashoffset={offset} transform="rotate(-90)" />
        <circle r={innerRadius} fill="var(--card-bg)" />
        {number !== null && (
          <text x="0" y="-4" textAnchor="middle" fill="var(--accent-color)" fontWeight="700" fontSize={Math.max(12, Math.round(size / 4))}>{number}</text>
        )}
        {unit && (
          <text x="0" y={Math.round(size / 6)} textAnchor="middle" fill="currentColor" fontSize={12}>{unit}</text>
        )}
      </g>
    </svg>
  )
}

export default function ProgressCard({ days = 3, goal = 7 }) {
  const percent = Math.round((days / goal) * 100)
  return (
    <div className="relative bg-gradient-to-br from-emerald-100 to-green-50 p-4 rounded-2xl overflow-hidden shadow-sm w-full animate-pop" style={{backgroundImage: `linear-gradient(135deg, rgba(var(--accent-color-rgb),0.06), rgba(6,95,70,0.03))`}}>
      <div className="min-w-0 pr-28">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-md bg-white/80 flex items-center justify-center">
            <svg className="w-4 h-4 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M13 2L3 14h7l-1 8L21 10h-7l1-8z" /></svg>
          </div>
          <div className="text-xs text-emerald-700 font-medium">Daily intake</div>
        </div>

        <div className="text-lg font-semibold text-gray-800 leading-tight">Your Weekly Progress</div>
        <div className="text-sm text-gray-500 mt-1">Keep a steady streak to gain XP</div>
      </div>

      <div className="absolute right-4 top-4">
        <CircularProgress percent={percent} size={88} stroke={8} number={days} unit="days" />
      </div>
    </div>
  )
}
