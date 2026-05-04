import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../../api'

const ADVANCED_ITEMS = [
  { key: 'machine', label: 'Estado de la máquina', description: 'Ver estado del hardware y acciones manuales', icon: 'M4 6h16 M4 12h10 M4 18h7' },
  { key: 'users', label: 'Gestión de usuarios', description: 'Crear, editar roles y eliminar usuarios', icon: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4z' },
  { key: 'recipes', label: 'Gestión de recetas', description: 'Crear, editar y eliminar cócteles', icon: 'M12 2l3 7h7l-5.5 4 2 7L12 17l-6.5 3 2-7L2 9h7z' },
  { key: 'cups', label: 'CRUD de vasos', description: 'Configurar vasos y capacidades', icon: 'M6 2h12l-2 18H8L6 2z' },
  { key: 'deposits', label: 'Depósitos', description: 'Asignar contenido y niveles de los depósitos', icon: 'M5 13l4 4L19 7' }
]

export default function AdvancedIndex(){
  const navigate = useNavigate()
  const [admin, setAdmin] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    api.get('/users/me')
      .then(res => { if (cancelled) return; setAdmin(res.data?.is_admin === true) })
      .catch(() => { if (cancelled) return; setAdmin(false) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="p-6 rounded-3xl bg-white border border-gray-100 text-center text-sm text-gray-500">Cargando...</div>
  if (!admin) return <div className="bg-white p-6 rounded-3xl border border-gray-100 text-center text-gray-600">Acceso restringido. Solo administradores.</div>

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to="/menu" className="p-2 bg-white rounded-full shadow-sm">←</Link>
        <h2 className="text-lg font-semibold">Avanzado</h2>
        <div className="w-8" />
      </div>

      <div className="rounded-2xl overflow-hidden bg-white text-gray-800 shadow-lg border border-gray-100">
        {ADVANCED_ITEMS.map((item, idx) => (
          <button
            key={item.key}
            onClick={() => navigate(`/menu/avanzado/${item.key}`)}
            className="w-full flex items-center justify-between px-4 py-4 border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
            style={{ animationDelay: `${idx * 40}ms` }}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-gray-800" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d={item.icon} /></svg>
              </div>
              <div className="text-left">
                <div className="font-medium">{item.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{item.description}</div>
              </div>
            </div>
            <div className="text-gray-400">›</div>
          </button>
        ))}
      </div>
    </div>
  )
}
