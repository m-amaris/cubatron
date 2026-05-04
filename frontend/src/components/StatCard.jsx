import React from 'react'

export default function StatCard({ title, value, unit }) {
  return (
    <div className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm flex-1">
      <div className="text-xs text-gray-400">{title}</div>
      <div className="mt-2 font-semibold text-gray-800">{value} <span className="text-sm text-gray-500">{unit}</span></div>
    </div>
  )
}
