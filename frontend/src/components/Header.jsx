import React, { useEffect, useState, useRef } from 'react'
import api from '../api'

export default function Header({ username = 'Sajibur Rahman' }) {
  const [profile, setProfile] = useState({})
  const [showNews, setShowNews] = useState(false)
  const [showNotifs, setShowNotifs] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [notLoading, setNotLoading] = useState(true)

  const headerRef = useRef(null)
  const newsRef = useRef(null)
  const notifRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    api.get('/users/me').then(res => {
      if (cancelled) return
      setProfile(res.data || {})
    }).catch(() => {
      // fallback to localStorage
      try {
        const saved = JSON.parse(localStorage.getItem('cubatron_profile') || '{}')
        setProfile(saved)
      } catch (e) {
        setProfile({})
      }
    })
    return () => { cancelled = true }
  }, [])

  useEffect(() => { fetchNotifications() }, [])

  async function fetchNotifications() {
    try {
      const r = await api.get('/notifications')
      setNotifications(r.data || [])
    } catch (e) {
      // fallback: read from localStorage or use sample notifications
      const saved = JSON.parse(localStorage.getItem('cubatron_notifications') || 'null')
      if (saved) setNotifications(saved)
      else setNotifications([
        { id: 1, type: 'friend_request', from: 'Ana', message: 'Ana te ha enviado una solicitud de amistad', created_at: new Date().toISOString() },
        { id: 2, type: 'recipe', message: 'Nueva receta disponible: Mango Mule', created_at: new Date().toISOString() }
      ])
    } finally {
      setNotLoading(false)
    }
  }

  useEffect(() => {
    function onClickOutside(e) {
      // don't close when clicking inside header, news popup or notif popup
      if (newsRef.current && newsRef.current.contains(e.target)) return
      if (notifRef.current && notifRef.current.contains(e.target)) return
      if (headerRef.current && headerRef.current.contains(e.target)) return
      setShowNews(false)
      setShowNotifs(false)
    }
    window.addEventListener('mousedown', onClickOutside)
    return () => window.removeEventListener('mousedown', onClickOutside)
  }, [])

  const newsList = [
    { version: '1.2.0', date: '2026-05-01', notes: ['Panel avanzado completo', 'Animaciones modernas en la interfaz'] },
    { version: '1.1.0', date: '2026-04-20', notes: ['Soporte PWA', 'Mejoras en autenticación'] }
  ]

  const displayName = profile.username || username
  const initials = (displayName || '').split(' ').map(n => n[0] || '').join('').slice(0, 2).toUpperCase()

  const gender = profile.gender || ''
  const greeting = gender === 'female' ? 'Bienvenida' : 'Bienvenido'

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('cubatron_profile')
    window.location.href = '/login'
  }

  function markAsRead(id) {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  async function acceptFriend(id) {
    try { await api.post('/friends/accept', { id }) } catch (e) { /* ignore */ }
    markAsRead(id)
  }

  return (
    <div ref={headerRef} className="flex items-center justify-between mb-4 relative">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-green-400 flex items-center justify-center text-white font-semibold text-sm shadow-md animate-pop">{initials}</div>
        <div>
          <div className="text-xs text-gray-500">{greeting}!</div>
          <div className="text-sm font-semibold">{displayName}</div>
        </div>
      </div>

      <div className="flex items-center gap-2 relative z-50">
        <div className="relative">
          <button onClick={() => { setShowNews(v => !v); setShowNotifs(false) }} className="p-2 bg-white rounded-lg shadow-sm text-gray-500 btn-press" aria-label="Novedades">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7 10h10M7 14h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </button>
          {showNews && (
            <div className="fixed inset-0 z-50 flex items-center justify-center">
              <div className="absolute inset-0 bg-black/40" onClick={() => setShowNews(false)} />
              <div ref={newsRef} className="relative w-11/12 max-w-md bg-white rounded-2xl p-4 shadow-lg border border-gray-100 animate-slide-down z-10">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Novedades</div>
                  <button onClick={() => setShowNews(false)} className="text-xs text-gray-400">Cerrar</button>
                </div>
                <div className="space-y-3 max-h-64 overflow-auto">
                  {newsList.map(n => (
                    <div key={n.version} className="p-2 rounded-lg bg-gray-50 border border-gray-100">
                      <div className="font-medium">v{n.version} <span className="text-xs text-gray-400">{n.date}</span></div>
                      <ul className="text-xs text-gray-600 mt-1 list-disc ml-4">
                        {n.notes.map((it, i) => <li key={i}>{it}</li>)}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="relative">
          <button onClick={() => { setShowNotifs(v => !v); setShowNews(false) }} className="p-2 bg-white rounded-lg shadow-sm text-gray-500 btn-press" aria-label="Notificaciones">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M13.73 21a2 2 0 01-3.46 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            {notifications.length > 0 && <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[11px] w-5 h-5 rounded-full flex items-center justify-center">{notifications.length}</span>}
          </button>
          {showNotifs && (
            <div className="fixed inset-0 z-50 flex items-center justify-center">
              <div className="absolute inset-0 bg-black/40" onClick={() => setShowNotifs(false)} />
              <div ref={notifRef} className="relative w-11/12 max-w-md bg-white rounded-2xl p-4 shadow-lg border border-gray-100 animate-slide-down z-10">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Notificaciones</div>
                  <button onClick={() => { setNotifications([]); localStorage.removeItem('cubatron_notifications') }} className="text-xs text-gray-400">Marcar todas como leídas</button>
                </div>
                <div className="space-y-2 max-h-64 overflow-auto text-sm text-gray-700">
                  {notLoading ? <div className="text-xs text-gray-500">Cargando...</div> : (
                    notifications.length === 0 ? <div className="text-xs text-gray-500">No hay notificaciones</div> : (
                      notifications.map(n => (
                        <div key={n.id} className="p-2 rounded-lg bg-gray-50 border border-gray-100">
                          <div className="flex items-start justify-between gap-2">
                            <div className="text-xs text-gray-600">
                              {n.type === 'friend_request' ? (<><span className="font-medium">{n.from}</span> te ha enviado una solicitud</>) : n.type === 'recipe' ? (<>{n.message}</>) : (<>{n.message}</>)}
                              <div className="text-[11px] text-gray-400">{new Date(n.created_at || Date.now()).toLocaleString()}</div>
                            </div>
                            <div className="flex gap-2">
                              {n.type === 'friend_request' && <button onClick={() => acceptFriend(n.id)} className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded-lg text-xs">Aceptar</button>}
                              <button onClick={() => markAsRead(n.id)} className="px-2 py-1 bg-white border border-gray-100 rounded-lg text-xs">Cerrar</button>
                            </div>
                          </div>
                        </div>
                      ))
                    )
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <button onClick={handleLogout} className="p-2 bg-white rounded-lg shadow-sm text-gray-500 btn-press">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </div>
  )
}
