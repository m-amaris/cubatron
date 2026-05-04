import React from 'react'

export default function ActivityFeed({ items = [] }) {
  return (
    <div className="space-y-3">
      {items.length === 0 && <div className="text-sm text-gray-500">No recent activity</div>}
      {items.map((h) => (
        <div key={h.id} className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm flex justify-between items-center">
          <div>
            <div className="font-medium text-gray-800">{h.recipe_name || 'Custom'}</div>
            <div className="text-xs text-gray-400">{new Date(h.created_at).toLocaleString()}</div>
          </div>
          <div className="text-sm text-gray-700">{h.ml_total} ml</div>
        </div>
      ))}
    </div>
  )
}
