import React from 'react'

function computeLevel(xp) {
  const n = Number(xp) || 0
  return Math.max(1, Math.floor(n / 10) + 1)
}

export default function LevelCard({ xp = 0 }) {
  const level = computeLevel(xp)
  return (
    <div className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm flex-1">
      <div className="text-xs text-gray-400">Nivel Actual</div>
      <div className="mt-2">
        <div className="flex items-baseline gap-2">
          <div className="text-sm text-gray-600">Nivel:</div>
          <div className="font-semibold text-gray-800">{level}</div>
        </div>
      </div>
      <div className="text-sm text-gray-500 mt-1">{xp} XP</div>
    </div>
  )
}
