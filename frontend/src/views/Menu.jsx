import React, { useEffect, useState } from 'react'
import api from '../api'
import { Link, useNavigate, useParams } from 'react-router-dom'

const SECTIONS = ['Perfil', 'Cuenta', 'Apariencia', 'Notificaciones', 'Avanzado']

function SectionTabs({ active, setActive }) {
  return (
    <div className="flex gap-2 mb-4">
      {SECTIONS.map(s => (
        <button key={s} onClick={() => setActive(s)} className={`px-3 py-1 rounded-full ${active===s ? 'bg-indigo-700 text-white' : 'bg-white border border-gray-100 text-gray-700'}`}>
          {s}
        </button>
      ))}
    </div>
  )
}

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

function AdvancedSection() {
  const navigate = useNavigate()
  const { section } = useParams()
  const [activeTab, setActiveTab] = useState(section || 'machine')
  const [admin, setAdmin] = useState(false)
  const [status, setStatus] = useState({ state: 'IDLE', levels: [], temperature: 0 })
  const [users, setUsers] = useState([])
  const [recipes, setRecipes] = useState([])
  const [cups, setCups] = useState([])
  const [deposits, setDeposits] = useState([])
  const [ingredients, setIngredients] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [newUser, setNewUser] = useState({ username: '', password: '' })
  const [newRecipe, setNewRecipe] = useState({ name: '', description: '', composition: '{"1": 50, "2": 50}' })
  const [newCup, setNewCup] = useState({ name: '', capacity_ml: 300, description: '' })

  const ADVANCED_ITEMS = [
    { key: 'machine', label: 'Estado de la máquina', description: 'Ver estado del hardware y acciones manuales', icon: 'M4 6h16 M4 12h10 M4 18h7' },
    { key: 'users', label: 'Gestión de usuarios', description: 'Crear, editar roles y eliminar usuarios', icon: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4z' },
    { key: 'recipes', label: 'Gestión de recetas', description: 'Crear, editar y eliminar cócteles', icon: 'M12 2l3 7h7l-5.5 4 2 7L12 17l-6.5 3 2-7L2 9h7z' },
    { key: 'cups', label: 'CRUD de vasos', description: 'Configurar vasos y capacidades', icon: 'M6 2h12l-2 18H8L6 2z' },
    { key: 'deposits', label: 'Depósitos', description: 'Asignar contenido y niveles de los depósitos', icon: 'M5 13l4 4L19 7' }
  ]

  useEffect(() => {
    if (section && !ADVANCED_ITEMS.some(item => item.key === section)) {
      navigate('/menu/avanzado', { replace: true })
      return
    }
    setActiveTab(section || 'machine')
  }, [section, navigate])

  useEffect(() => {
    let cancelled = false
    api.get('/users/me')
      .then(res => {
        if (cancelled) return
        setAdmin(res.data?.is_admin === true)
      })
      .catch(() => {
        if (cancelled) return
        setAdmin(false)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!admin) return
    fetchStatus()
    fetchUsers()
    fetchRecipes()
    fetchCups()
    fetchIngredients()
    fetchDeposits()
  }, [admin])

  async function fetchStatus() {
    try {
      const r = await api.get('/machine/status')
      setStatus(r.data || {})
    } catch (err) {
      setMessage('No se pudo obtener el estado de la máquina')
      setTimeout(() => setMessage(''), 3000)
    }
  }

  async function fetchUsers() {
    try {
      const r = await api.get('/users')
      setUsers(r.data || [])
    } catch (err) {
      setUsers([])
    }
  }

  async function fetchRecipes() {
    try {
      const r = await api.get('/drinks')
      setRecipes(r.data || [])
    } catch (err) {
      setRecipes([])
    }
  }

  async function fetchCups() {
    try {
      const r = await api.get('/cups')
      setCups(r.data || [])
    } catch (err) {
      setCups([])
    }
  }

  async function fetchIngredients() {
    try {
      const r = await api.get('/machine/ingredients')
      setIngredients(r.data || [])
    } catch (err) {
      setIngredients([])
    }
  }

  async function fetchDeposits() {
    try {
      const r = await api.get('/machine/deposits')
      setDeposits(r.data || [])
    } catch (err) {
      setDeposits([])
    }
  }

  async function sendMachineAction(action, payload = {}) {
    try {
      let res
      if (action === 'clean') res = await api.post('/machine/clean')
      if (action === 'stop') res = await api.post('/machine/stop')
      if (action === 'temp') res = await api.post('/machine/temp', payload)
      if (action === 'refresh') await fetchStatus()
      if (res && res.data && res.data.status) {
        setMessage(`OK: ${res.data.status}`)
      }
      await fetchStatus()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
      setTimeout(() => setMessage(''), 3000)
    }
  }

  async function createUser() {
    if (!newUser.username || !newUser.password) {
      setMessage('Usuario y contraseña son obligatorios')
      setTimeout(() => setMessage(''), 3000)
      return
    }
    try {
      await api.post('/users', newUser)
      setNewUser({ username: '', password: '' })
      setMessage('Usuario creado')
      fetchUsers()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function saveUser(userId, isAdminValue) {
    try {
      await api.patch(`/users/${userId}`, { is_admin: isAdminValue })
      setMessage('Usuario actualizado')
      fetchUsers()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
      setTimeout(() => setMessage(''), 3000)
    }
  }

  async function removeUser(userId) {
    if (!window.confirm('¿Eliminar usuario?')) return
    try {
      await api.delete(`/users/${userId}`)
      setMessage('Usuario eliminado')
      fetchUsers()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function createRecipe() {
    let composition
    try {
      composition = JSON.parse(newRecipe.composition)
    } catch (e) {
      setMessage('La composición debe ser JSON válido')
      setTimeout(() => setMessage(''), 3000)
      return
    }

    try {
      await api.post('/drinks', { name: newRecipe.name, description: newRecipe.description, composition })
      setNewRecipe({ name: '', description: '', composition: '{"1": 50, "2": 50}' })
      setMessage('Receta creada')
      fetchRecipes()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
      setTimeout(() => setMessage(''), 3000)
    }
  }

  async function updateRecipe(recipe) {
    try {
      await api.patch(`/drinks/${recipe.id}`, { name: recipe.name, description: recipe.description, composition: recipe.composition })
      setMessage('Receta guardada')
      fetchRecipes()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
      setTimeout(() => setMessage(''), 3000)
    }
  }

  async function removeRecipe(recipeId) {
    if (!window.confirm('¿Eliminar receta?')) return
    try {
      await api.delete(`/drinks/${recipeId}`)
      setMessage('Receta eliminada')
      fetchRecipes()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function createCup() {
    if (!newCup.name || !newCup.capacity_ml) {
      setMessage('Nombre y capacidad son obligatorios')
      setTimeout(() => setMessage(''), 3000)
      return
    }
    try {
      await api.post('/cups', newCup)
      setNewCup({ name: '', capacity_ml: 300, description: '' })
      setMessage('Vaso creado')
      fetchCups()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function updateCup(cup) {
    try {
      await api.patch(`/cups/${cup.id}`, cup)
      setMessage('Vaso actualizado')
      fetchCups()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function removeCup(cupId) {
    if (!window.confirm('¿Eliminar vaso?')) return
    try {
      await api.delete(`/cups/${cupId}`)
      setMessage('Vaso eliminado')
      fetchCups()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function updateDeposit(depositId, payload) {
    try {
      await api.patch(`/machine/deposits/${depositId}`, payload)
      setMessage('Depósito actualizado')
      fetchDeposits()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  function renderMachineTab() {
    return (
      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm">
          <div className="text-sm text-gray-500">Estado de la máquina</div>
          <div className="mt-2 text-xl font-semibold">{status.state}</div>
          <div className="text-xs text-gray-500">Temperatura: {status.temperature?.toFixed?.(1) ?? status.temperature}°C</div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {status.levels.map((level, idx) => (
              <div key={idx} className="p-3 rounded-2xl bg-gray-50 border border-gray-100">
                <div className="text-xs text-gray-500">Depósito {idx + 1}</div>
                <div className="text-lg font-semibold">{level} ml</div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <button onClick={() => sendMachineAction('clean')} className="px-3 py-3 bg-white border border-gray-100 rounded-3xl text-sm">Limpiar</button>
          <button onClick={() => sendMachineAction('stop')} className="px-3 py-3 bg-white border border-gray-100 rounded-3xl text-sm">Parada emergencia</button>
          <button onClick={() => sendMachineAction('temp', { temperature: 30 })} className="px-3 py-3 bg-white border border-gray-100 rounded-3xl text-sm">Fijar 30°C</button>
          <button onClick={() => sendMachineAction('refresh')} className="px-3 py-3 bg-white border border-gray-100 rounded-3xl text-sm">Refrescar estado</button>
        </div>
      </div>
    )
  }

  function renderUsersTab() {
    return (
      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm">
          <div className="text-sm font-medium mb-3">Crear usuario</div>
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-gray-500">Usuario</label>
              <input value={newUser.username} onChange={e => setNewUser(prev => ({ ...prev, username: e.target.value }))} className="w-full p-3 rounded-2xl border border-gray-100" />
            </div>
            <div>
              <label className="block text-xs text-gray-500">Contraseña</label>
              <input type="password" value={newUser.password} onChange={e => setNewUser(prev => ({ ...prev, password: e.target.value }))} className="w-full p-3 rounded-2xl border border-gray-100" />
            </div>
            <button onClick={createUser} className="w-full py-3 rounded-3xl bg-indigo-700 text-white">Crear usuario</button>
          </div>
        </div>

        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Usuarios existentes</div>
          {users.length === 0 ? (
            <div className="text-sm text-gray-500">No hay usuarios registrados.</div>
          ) : (
            users.map(user => (
              <div key={user.id} className="rounded-2xl border border-gray-100 p-3 grid grid-cols-[1fr_auto] gap-3 items-center">
                <div>
                  <div className="font-medium">{user.username}</div>
                  <div className="text-xs text-gray-500">XP: {user.xp} · {user.is_admin ? 'Admin' : 'Usuario'}</div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => saveUser(user.id, !user.is_admin)} className="px-3 py-2 rounded-2xl bg-gray-100 text-xs">{user.is_admin ? 'Quitar admin' : 'Admin'}</button>
                  <button onClick={() => removeUser(user.id)} className="px-3 py-2 rounded-2xl bg-red-100 text-red-700 text-xs">Borrar</button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    )
  }

  function renderRecipesTab() {
    return (
      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Nueva receta</div>
          <div>
            <label className="block text-xs text-gray-500">Nombre</label>
            <input value={newRecipe.name} onChange={e => setNewRecipe(prev => ({ ...prev, name: e.target.value }))} className="w-full p-3 rounded-2xl border border-gray-100" />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Descripción</label>
            <input value={newRecipe.description} onChange={e => setNewRecipe(prev => ({ ...prev, description: e.target.value }))} className="w-full p-3 rounded-2xl border border-gray-100" />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Composición (JSON)</label>
            <textarea value={newRecipe.composition} onChange={e => setNewRecipe(prev => ({ ...prev, composition: e.target.value }))} rows={4} className="w-full p-3 rounded-2xl border border-gray-100" />
          </div>
          <button onClick={createRecipe} className="w-full py-3 rounded-3xl bg-indigo-700 text-white">Agregar receta</button>
        </div>

        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Recetas existentes</div>
          {recipes.length === 0 ? (
            <div className="text-sm text-gray-500">No hay recetas registradas.</div>
          ) : recipes.map(recipe => (
            <div key={recipe.id} className="rounded-2xl border border-gray-100 p-3 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <div className="font-medium">{recipe.name}</div>
                  <div className="text-xs text-gray-500">{recipe.description || 'Sin descripción'}</div>
                </div>
                <button onClick={() => removeRecipe(recipe.id)} className="px-3 py-2 rounded-2xl bg-red-100 text-red-700 text-xs">Eliminar</button>
              </div>
              <div className="text-xs text-gray-500">Composición: {JSON.stringify(recipe.composition)}</div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  function renderCupsTab() {
    return (
      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Nuevo vaso</div>
          <div>
            <label className="block text-xs text-gray-500">Nombre</label>
            <input value={newCup.name} onChange={e => setNewCup(prev => ({ ...prev, name: e.target.value }))} className="w-full p-3 rounded-2xl border border-gray-100" />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Capacidad (ml)</label>
            <input type="number" value={newCup.capacity_ml} onChange={e => setNewCup(prev => ({ ...prev, capacity_ml: Number(e.target.value) }))} className="w-full p-3 rounded-2xl border border-gray-100" />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Descripción</label>
            <input value={newCup.description} onChange={e => setNewCup(prev => ({ ...prev, description: e.target.value }))} className="w-full p-3 rounded-2xl border border-gray-100" />
          </div>
          <button onClick={createCup} className="w-full py-3 rounded-3xl bg-indigo-700 text-white">Agregar vaso</button>
        </div>

        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Vasos registrados</div>
          {cups.length === 0 ? (
            <div className="text-sm text-gray-500">No hay vasos disponibles.</div>
          ) : cups.map(cup => (
            <div key={cup.id} className="rounded-2xl border border-gray-100 p-3 grid grid-cols-[1fr_auto] gap-3 items-center">
              <div>
                <div className="font-medium">{cup.name}</div>
                <div className="text-xs text-gray-500">{cup.capacity_ml} ml · {cup.description || 'Sin descripción'}</div>
              </div>
              <button onClick={() => removeCup(cup.id)} className="px-3 py-2 rounded-2xl bg-red-100 text-red-700 text-xs">Eliminar</button>
            </div>
          ))}
        </div>
      </div>
    )
  }

  function renderDepositsTab() {
    return (
      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Depósitos</div>
          {deposits.length === 0 ? (
            <div className="text-sm text-gray-500">No hay información de depósitos.</div>
          ) : deposits.map(deposit => (
            <div key={deposit.id} className="rounded-2xl border border-gray-100 p-3 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="font-medium">Depósito {deposit.slot}</div>
                  <div className="text-xs text-gray-500">Ingrediente: {deposit.ingredient_name || 'Sin asignar'}</div>
                </div>
                <span className="text-xs text-gray-500">{deposit.level_ml}/{deposit.capacity_ml} ml</span>
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                <select value={deposit.ingredient_id || ''} onChange={e => updateDeposit(deposit.id, { ingredient_id: Number(e.target.value) || null })} className="w-full p-3 rounded-2xl border border-gray-100">
                  <option value="">Seleccionar ingrediente</option>
                  {ingredients.map(ing => (
                    <option key={ing.id} value={ing.id}>{ing.name}</option>
                  ))}
                </select>
                <input type="number" defaultValue={deposit.level_ml} onBlur={e => updateDeposit(deposit.id, { level_ml: Number(e.target.value) })} className="w-full p-3 rounded-2xl border border-gray-100" placeholder="Nivel (ml)" />
                <input type="number" defaultValue={deposit.capacity_ml} onBlur={e => updateDeposit(deposit.id, { capacity_ml: Number(e.target.value) })} className="w-full p-3 rounded-2xl border border-gray-100" placeholder="Capacidad (ml)" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (loading) {
    return <div className="space-y-4 animate-fade-in-up"><div className="p-6 rounded-3xl bg-white border border-gray-100 text-center text-sm text-gray-500">Cargando panel avanzado…</div></div>
  }

  if (!admin) {
    return (
      <div className="animate-fade-in-up space-y-4">
        <div className="bg-white p-6 rounded-3xl border border-gray-100 text-center text-gray-600">
          Acceso restringido. Solo los administradores pueden ver el panel avanzado.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="rounded-2xl overflow-hidden bg-white text-gray-800 shadow-lg border border-gray-100">
        {ADVANCED_ITEMS.map((item, idx) => (
          <button
            key={item.key}
            onClick={() => navigate(`/menu/avanzado/${item.key}`)}
            className={`w-full flex items-center justify-between px-4 py-4 border-b border-gray-100 last:border-b-0 transition-transform transition-colors duration-150 ease-in-out hover:translate-x-1 hover:bg-gray-50 focus:outline-none ${activeTab === item.key ? 'bg-indigo-50' : 'bg-white'}`}
            style={{ animationDelay: `${idx * 40}ms` }}
          >
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl bg-gray-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-gray-800" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d={item.icon} /></svg>
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

      {message && <div className="text-sm text-green-700">{message}</div>}

      {activeTab === 'machine' && renderMachineTab()}
      {activeTab === 'users' && renderUsersTab()}
      {activeTab === 'recipes' && renderRecipesTab()}
      {activeTab === 'cups' && renderCupsTab()}
      {activeTab === 'deposits' && renderDepositsTab()}
    </div>
  )
}

export default function Menu() {
  const [active, setActive] = useState('Perfil')

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to="/" className="p-2 bg-white rounded-full shadow-sm">←</Link>
        <h2 className="text-lg font-semibold">Menu</h2>
        <div className="w-8" />
      </div>

      <SectionTabs active={active} setActive={setActive} />

      <div className="mt-3">
        {active === 'Perfil' && <ProfileSection key="Perfil" />}
        {active === 'Cuenta' && <AccountSection key="Cuenta" />}
        {active === 'Apariencia' && <AppearanceSection key="Apariencia" />}
        {active === 'Notificaciones' && <NotificationsSection key="Notificaciones" />}
        {active === 'Avanzado' && <AdvancedSection key="Avanzado" />}
      </div>
    </div>
  )
}

export { ProfileSection, AccountSection, AppearanceSection, NotificationsSection, AdvancedSection }
