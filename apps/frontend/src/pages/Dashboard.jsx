import React, { useEffect, useState } from 'react'

export default function Dashboard() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    async function fetchHealth() {
      try {
        const res = await fetch('/health')
        const data = await res.json().catch(() => ({}))
        setHealth(data.ok ? 'ok' : 'down')
      } catch (err) {
        setHealth('error')
      }
    }
    fetchHealth()
  }, [])

  return (
    <div className="p-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Cubatron Dashboard</h1>
      </header>
      <div className="mt-4">
        <p>Health: {String(health)}</p>
        <p className="mt-2 text-sm text-slate-600">Interfaz inicial con Tailwind — desarrolla tus vistas aquí.</p>
      </div>
    </div>
  )
}
