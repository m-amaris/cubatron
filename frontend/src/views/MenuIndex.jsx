import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

const ITEMS = [
  { key: 'perfil', label: 'Perfil', icon: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4z M6 20v-1c0-2.21 3.58-4 6-4s6 1.79 6 4v1' },
  { key: 'cuenta', label: 'Cuenta', icon: 'M12 17a2 2 0 100-4 2 2 0 000 4zm6-8h-1V7a5 5 0 00-10 0v2H6a2 2 0 00-2 2v7a2 2 0 002 2h12a2 2 0 002-2v-7a2 2 0 00-2-2z' },
  { key: 'apariencia', label: 'Apariencia', icon: 'M12 2l3 7h7l-5.5 4 2 7L12 17l-6.5 3 2-7L2 9h7z' },
  { key: 'notificaciones', label: 'Notificaciones', icon: 'M18 8a6 6 0 10-12 0v4l-2 2h16l-2-2V8' },
  { key: 'avanzado', label: 'Avanzado', icon: 'M4 6h16 M4 12h10 M4 18h7' }
]

export default function MenuIndex(){
  const navigate = useNavigate()
  const [isAdmin, setIsAdmin] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    api.get('/users/me')
      .then(res => {
        if (cancelled) return
        setIsAdmin(res.data?.is_admin === true)
      })
      .catch(() => {
        if (cancelled) return
        setIsAdmin(false)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const visibleItems = ITEMS.filter(item => item.key !== 'avanzado' || isAdmin)

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <button onClick={()=>navigate(-1)} className="p-2 bg-white rounded-full shadow-sm">←</button>
        <h2 className="text-lg font-semibold">Ajustes</h2>
        <div className="w-8" />
      </div>

      <div className="rounded-2xl overflow-hidden bg-white text-gray-800 shadow-lg border border-gray-100">
        {loading ? (
          <div className="p-6 text-center text-sm text-gray-500">Cargando opciones...</div>
        ) : visibleItems.length === 0 ? (
          <div className="p-6 text-center text-sm text-gray-500">No hay opciones disponibles.</div>
        ) : visibleItems.map((item, idx) => (
          <button
            key={item.key}
            onClick={() => navigate(`/menu/${item.key}`)}
            className="w-full flex items-center justify-between px-4 py-4 border-b border-gray-100 last:border-b-0 transition-transform transition-colors duration-150 ease-in-out hover:translate-x-1 hover:bg-gray-50 focus:outline-none animate-fade-in-up menu-item"
            style={{ animationDelay: `${idx * 60}ms` }}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-gray-800" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" xmlns="http://www.w3.org/2000/svg"><path d={item.icon} /></svg>
              </div>
              <div className="text-left">
                <div className="font-medium">{item.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">Configuración de {item.label.toLowerCase()}</div>
              </div>
            </div>
            <div className="text-gray-400">›</div>
          </button>
        ))}
      </div>
    </div>
  )
}
