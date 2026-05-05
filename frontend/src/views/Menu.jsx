import React, { useEffect, useState } from 'react'
import api from '../api'
import { Link, useNavigate } from 'react-router-dom'

const SECTIONS = ['Perfil', 'Cuenta', 'Apariencia', 'Notificaciones', 'Avanzado']

function ProfileSection() {
  const [avatar, setAvatar] = useState(null)
  const [name, setName] = useState('')
  const [gender, setGender] = useState('')
  const [status, setStatus] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    // try load from API, fallback to localStorage
    let cancelled = false
    api.get('/users/me').then(res => {
      if (cancelled) return
      const d = res.data || {}
      setName(d.username || '')
      setGender(d.gender || '')
    }).catch(() => {
      const saved = JSON.parse(localStorage.getItem('cubatron_profile') || '{}')
      if (saved) {
        setName(saved.name || '')
        setStatus(saved.status || '')
        setAvatar(saved.avatar || null)
        setGender(saved.gender || '')
      }
    })
    return () => { cancelled = true }
  }, [])

  function handleFile(e) {
    const f = e.target.files && e.target.files[0]
    if (!f) return
    const reader = new FileReader()
    reader.onload = () => setAvatar(reader.result)
    reader.readAsDataURL(f)
  }

  function save() {
    const payload = { username: name, gender }
    api.patch('/users/me', payload).then(res => {
      setMessage('Perfil guardado')
      // update localStorage as backup
      const saved = JSON.parse(localStorage.getItem('cubatron_profile') || '{}')
      saved.name = name
      saved.gender = gender
      localStorage.setItem('cubatron_profile', JSON.stringify(saved))
      setTimeout(() => setMessage(''), 2500)
    }).catch(err => {
      setMessage('Error al guardar: ' + (err.response?.data?.detail || err.message))
      setTimeout(() => setMessage(''), 2500)
    })
  }

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="flex items-center gap-4">
        <div className="w-20 h-20 rounded-xl bg-gray-100 overflow-hidden flex items-center justify-center">
          {avatar ? <img src={avatar} alt="avatar" className="w-full h-full object-cover" /> : <div className="text-gray-400">Sin foto</div>}
        </div>
        <div>
          <label className="block text-sm text-gray-500">Cambiar foto</label>
          <input type="file" accept="image/*" onChange={handleFile} className="mt-2" />
        </div>
      </div>

        <div>
          <label className="block text-xs text-gray-500">Género</label>
          <select value={gender} onChange={e=>setGender(e.target.value)} className="w-full p-3 rounded-lg border border-gray-100">
            <option value="">Prefiero no decir</option>
            <option value="male">Hombre</option>
            <option value="female">Mujer</option>
            <option value="other">Otro</option>
          </select>
        </div>

      <div>
        <label className="block text-xs text-gray-500">Nombre</label>
        <input value={name} onChange={e=>setName(e.target.value)} className="w-full p-3 rounded-lg border border-gray-100" />
      </div>

      <div>
        <label className="block text-xs text-gray-500">Estado</label>
        <input value={status} onChange={e=>setStatus(e.target.value)} className="w-full p-3 rounded-lg border border-gray-100" />
      </div>

      <div className="flex gap-2">
        <button onClick={save} className="px-4 py-2 bg-indigo-700 text-white rounded-lg">Guardar</button>
        <Link to="/" className="px-4 py-2 bg-white border border-gray-100 rounded-lg">Cancelar</Link>
      </div>
      {message && <div className="text-sm text-green-600">{message}</div>}
    </div>
  )
}

function AccountSection() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [current, setCurrent] = useState('')
  const [pwd, setPwd] = useState('')
  const [confirm, setConfirm] = useState('')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    api.get('/users/me').then(res => {
      const d = res.data || {}
      setUsername(d.username || '')
    }).catch(()=>{
      const saved = JSON.parse(localStorage.getItem('cubatron_profile')||'{}')
      setUsername(saved.name || '')
    })
  }, [])

  function saveAccount() {
    if (pwd && pwd !== confirm) { setMsg('Las contraseñas no coinciden'); return }
    // No backend endpoint for update yet — store locally as mock
    const acc = { username, email }
    localStorage.setItem('cubatron_account', JSON.stringify(acc))
    setMsg('Cuenta actualizada (simulado)')
    setTimeout(()=>setMsg(''), 2500)
  }

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div>
        <label className="block text-xs text-gray-500">Nombre de usuario</label>
        <input value={username} onChange={e=>setUsername(e.target.value)} className="w-full p-3 rounded-lg border border-gray-100" />
      </div>
      <div>
        <label className="block text-xs text-gray-500">Email</label>
        <input value={email} onChange={e=>setEmail(e.target.value)} className="w-full p-3 rounded-lg border border-gray-100" />
      </div>

      <hr />
      <div>
        <label className="block text-xs text-gray-500">Contraseña actual</label>
        <input type="password" value={current} onChange={e=>setCurrent(e.target.value)} className="w-full p-3 rounded-lg border border-gray-100" />
      </div>
      <div>
        <label className="block text-xs text-gray-500">Nueva contraseña</label>
        <input type="password" value={pwd} onChange={e=>setPwd(e.target.value)} className="w-full p-3 rounded-lg border border-gray-100" />
      </div>
      <div>
        <label className="block text-xs text-gray-500">Confirmar contraseña</label>
        <input type="password" value={confirm} onChange={e=>setConfirm(e.target.value)} className="w-full p-3 rounded-lg border border-gray-100" />
      </div>

      <div className="flex gap-2">
        <button onClick={saveAccount} className="px-4 py-2 bg-indigo-700 text-white rounded-lg">Guardar</button>
        <button onClick={()=>{setPwd(''); setConfirm(''); setCurrent('')}} className="px-4 py-2 bg-white border border-gray-100 rounded-lg">Limpiar</button>
      </div>
      {msg && <div className="text-sm text-green-600">{msg}</div>}
    </div>
  )
}

function AppearanceSection() {
  const [theme, setTheme] = useState('light')
  const [accent, setAccent] = useState('#6366f1')

  useEffect(()=>{
    const s = localStorage.getItem('cubatron_theme') || 'light'
    const a = localStorage.getItem('cubatron_accent') || '#6366f1'
    setTheme(s)
    setAccent(a)
    applyTheme(s, a)
  }, [])

  function hexToRgb(hex) {
    if (!hex) return '99,102,241'
    const h = hex.replace('#','')
    const full = h.length === 3 ? h.split('').map(c=>c+c).join('') : h
    const num = parseInt(full, 16)
    const r = (num >> 16) & 255
    const g = (num >> 8) & 255
    const b = num & 255
    return `${r},${g},${b}`
  }

  function applyTheme(t, a) {
    document.documentElement.setAttribute('data-theme', t)
    document.documentElement.style.setProperty('--accent-color', a)
    document.documentElement.style.setProperty('--accent-color-rgb', hexToRgb(a))
    document.documentElement.style.setProperty('--card-bg', t === 'dark' ? '#0f1724' : '#ffffff')
    document.documentElement.style.setProperty('--surface-bg', t === 'dark' ? '#0b1220' : '#ffffff')
  }

  function save() {
    localStorage.setItem('cubatron_theme', theme)
    localStorage.setItem('cubatron_accent', accent)
    applyTheme(theme, accent)
  }

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div>
        <div className="text-sm text-gray-600 mb-2">Tema</div>
        <div className="flex gap-2">
          <button onClick={()=>setTheme('light')} className={`px-3 py-1 rounded ${theme==='light'? 'bg-indigo-700 text-white':'bg-white border border-gray-100'}`}>Claro</button>
          <button onClick={()=>setTheme('dark')} className={`px-3 py-1 rounded ${theme==='dark'? 'bg-indigo-700 text-white':'bg-white border border-gray-100'}`}>Oscuro</button>
        </div>
      </div>

      <div>
        <div className="text-sm text-gray-600 mb-2">Acento</div>
        <div className="flex gap-2 items-center">
          {['#6366f1','#10b981','#f97316','#ef4444'].map(c => (
            <button key={c} onClick={()=>setAccent(c)} style={{backgroundColor:c}} className={`w-8 h-8 rounded-full ring-2 ${accent===c? 'ring-offset-2 ring-indigo-500':'ring-white'}`} />
          ))}
          <div className="ml-3 text-sm text-gray-500">Selecciona un color de acento</div>
        </div>
      </div>

      <div className="flex gap-2">
        <button onClick={save} className="px-4 py-2 bg-indigo-700 text-white rounded-lg">Aplicar</button>
      </div>
    </div>
  )
}

function NotificationsSection() {
  const [push, setPush] = useState(false)
  const [other, setOther] = useState(true)
  const [msg, setMsg] = useState('')

  useEffect(()=>{
    setPush(localStorage.getItem('cubatron_push') === '1')
    setOther(localStorage.getItem('cubatron_other') !== '0')
  }, [])

  function togglePush() {
    if (!('Notification' in window)) { setMsg('Notificaciones push no soportadas'); return }
    Notification.requestPermission().then(p => {
      if (p === 'granted') { setPush(true); localStorage.setItem('cubatron_push','1'); setMsg('Push habilitado') }
      else { setPush(false); localStorage.setItem('cubatron_push','0'); setMsg('Push deshabilitado') }
      setTimeout(()=>setMsg(''),2000)
    })
  }

  function toggleOther() {
    setOther(v => { const nv = !v; localStorage.setItem('cubatron_other', nv ? '1' : '0'); return nv })
  }

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">Notificaciones Push</div>
          <div className="text-xs text-gray-500">Recibe alertas en tu dispositivo</div>
        </div>
        <button onClick={togglePush} className={`px-3 py-1 rounded ${push? 'bg-indigo-700 text-white':'bg-white border border-gray-100'}`}>{push? 'ON' : 'OFF'}</button>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">Otras notificaciones</div>
          <div className="text-xs text-gray-500">Emails y novedades</div>
        </div>
        <button onClick={toggleOther} className={`px-3 py-1 rounded ${other? 'bg-indigo-700 text-white':'bg-white border border-gray-100'}`}>{other? 'ON' : 'OFF'}</button>
      </div>
      {msg && <div className="text-sm text-green-600">{msg}</div>}
    </div>
  )
}

export default function Menu() {
  const [active, setActive] = useState('Perfil')
  const navigate = useNavigate()

  function handleTab(section) {
    if (section === 'Avanzado') {
      navigate('/menu/avanzado')
      return
    }
    setActive(section)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to="/" className="p-2 bg-white rounded-full shadow-sm">←</Link>
        <h2 className="text-lg font-semibold">Menu</h2>
        <div className="w-8" />
      </div>

      <div className="flex gap-2 mb-4">
        {SECTIONS.map(s => (
          <button key={s} onClick={() => handleTab(s)} className={`px-3 py-1 rounded-full ${active===s ? 'bg-indigo-700 text-white' : 'bg-white border border-gray-100 text-gray-700'}`}>
            {s}
          </button>
        ))}
      </div>

      <div className="mt-3">
        {active === 'Perfil' && <ProfileSection key="Perfil" />}
        {active === 'Cuenta' && <AccountSection key="Cuenta" />}
        {active === 'Apariencia' && <AppearanceSection key="Apariencia" />}
        {active === 'Notificaciones' && <NotificationsSection key="Notificaciones" />}
      </div>
    </div>
  )
}

export { ProfileSection, AccountSection, AppearanceSection, NotificationsSection }
