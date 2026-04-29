import React, { useEffect, useState } from 'react'
import { apiFetch, getToken } from '../lib/api'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [recipes, setRecipes] = useState([])
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    async function init() {
      try {
        const h = await fetch('/health')
        setHealth(h.ok ? 'ok' : 'down')
      } catch (err) {
        setHealth('error')
      }

      if (!getToken()) {
        navigate('/')
        return
      }

      try {
        const r = await apiFetch('/api/drinks/recipes')
        setRecipes(Array.isArray(r) ? r : [])
      } catch (err) {
        if (err.message === 'unauthorized') {
          navigate('/')
        } else {
          setError(err.message || 'Error cargando recetas')
        }
      }
    }
    init()
  }, [navigate])

  return (
    <div className="p-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Cubatron Dashboard</h1>
      </header>
      <div className="mt-4">
        <p className="mb-2">Health: {String(health)}</p>
        {error && <p className="text-red-600">{error}</p>}
        {!error && (
          <div>
            <h2 className="text-lg font-semibold">Recetas</h2>
            {recipes.length === 0 ? (
              <p className="text-sm text-slate-600">No hay recetas disponibles.</p>
            ) : (
              <ul className="mt-2 space-y-2">
                {recipes.map(r => (
                  <li key={r.id} className="p-2 bg-white rounded shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{r.name}</div>
                        <div className="text-sm text-slate-500">{r.description}</div>
                      </div>
                      <div className="text-sm text-slate-400">XP {r.xp_reward}</div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
        <p className="mt-4 text-sm text-slate-600">Interfaz inicial con Tailwind — continúa migrando las vistas.</p>
      </div>
    </div>
  )
}
