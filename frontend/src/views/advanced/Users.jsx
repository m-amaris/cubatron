import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api'

export default function UsersView() {
  const [admin, setAdmin] = useState(false)
  const [loading, setLoading] = useState(true)
  const [users, setUsers] = useState([])
  const [newUser, setNewUser] = useState({ username: '', password: '' })
  const [message, setMessage] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editFields, setEditFields] = useState({ username: '', password: '' })

  useEffect(() => {
    let cancelled = false
    api.get('/users/me')
      .then(res => { if (cancelled) return; setAdmin(res.data?.is_admin === true) })
      .catch(() => { if (cancelled) return; setAdmin(false) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  useEffect(() => { if (admin) fetchUsers() }, [admin])

  async function fetchUsers() {
    try { const r = await api.get('/users/'); setUsers(r.data || []) }
    catch (e) { setUsers([]) }
  }

  async function createUser() {
    if (!newUser.username || !newUser.password) { setMessage('Usuario y contraseña son obligatorios'); setTimeout(()=>setMessage(''),3000); return }
    try { await api.post('/users/', newUser); setNewUser({ username: '', password: '' }); setMessage('Usuario creado'); fetchUsers() }
    catch (err) { setMessage('Error: ' + (err.response?.data?.detail || err.message)) }
    setTimeout(()=>setMessage(''),3000)
  }

  async function saveUser(userId, isAdminValue) {
    try { await api.patch(`/users/${userId}`, { is_admin: isAdminValue }); setMessage('Usuario actualizado'); fetchUsers() }
    catch (err) { setMessage('Error: ' + (err.response?.data?.detail || err.message)); setTimeout(()=>setMessage(''),3000) }
  }

  function startEdit(user) {
    setEditingId(user.id)
    setEditFields({ username: user.username || '', password: '' })
  }

  function cancelEdit() {
    setEditingId(null)
    setEditFields({ username: '', password: '' })
  }

  async function patchUser(userId) {
    const original = users.find(u => u.id === userId) || {}
    const payload = {}
    if (editFields.username && editFields.username !== original.username) payload.username = editFields.username
    if (editFields.password) payload.password = editFields.password
    if (Object.keys(payload).length === 0) { setMessage('No hay cambios'); setTimeout(()=>setMessage(''),2000); return }
    try {
      await api.patch(`/users/${userId}`, payload)
      setMessage('Usuario actualizado')
      cancelEdit()
      fetchUsers()
    } catch (err) {
      setMessage('Error: ' + (err.response?.data?.detail || err.message))
      setTimeout(()=>setMessage(''),3000)
    }
  }

  async function removeUser(userId) {
    if (!window.confirm('¿Eliminar usuario?')) return
    try { await api.delete(`/users/${userId}`); setMessage('Usuario eliminado'); fetchUsers() }
    catch (err) { setMessage('Error: ' + (err.response?.data?.detail || err.message)) }
    setTimeout(()=>setMessage(''),3000)
  }

  if (loading) return <div className="p-6 rounded-3xl bg-white border border-gray-100 text-center text-sm text-gray-500">Cargando...</div>
  if (!admin) return <div className="bg-white p-6 rounded-3xl border border-gray-100 text-center text-gray-600">Acceso restringido. Solo administradores.</div>

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to="/menu/avanzado" className="p-2 bg-white rounded-full shadow-sm">←</Link>
        <h2 className="text-lg font-semibold">Gestión de usuarios</h2>
        <div className="w-8" />
      </div>

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
                {editingId === user.id ? (
                  <div className="col-span-1 w-full">
                    <div className="text-sm font-medium mb-2">Editar usuario</div>
                    <div className="grid gap-2">
                      <input value={editFields.username} onChange={e => setEditFields(prev => ({ ...prev, username: e.target.value }))} className="w-full p-2 rounded-2xl border border-gray-100" />
                      <input type="password" placeholder="Nueva contraseña (opcional)" value={editFields.password} onChange={e => setEditFields(prev => ({ ...prev, password: e.target.value }))} className="w-full p-2 rounded-2xl border border-gray-100" />
                      <div className="text-xs text-gray-500">XP: {user.xp} · {user.is_admin ? 'Admin' : 'Usuario'}</div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="font-medium">{user.username}</div>
                    <div className="text-xs text-gray-500">XP: {user.xp} · {user.is_admin ? 'Admin' : 'Usuario'}</div>
                  </div>
                )}
                <div className="flex gap-2">
                  {editingId === user.id ? (
                    <>
                      <button onClick={() => patchUser(user.id)} className="px-3 py-2 rounded-2xl bg-indigo-700 text-white text-xs">Guardar</button>
                      <button onClick={cancelEdit} className="px-3 py-2 rounded-2xl bg-gray-100 text-xs">Cancelar</button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => saveUser(user.id, !user.is_admin)} className="px-3 py-2 rounded-2xl bg-gray-100 text-xs">{user.is_admin ? 'Quitar admin' : 'Admin'}</button>
                      <button onClick={() => startEdit(user)} className="px-3 py-2 rounded-2xl bg-yellow-100 text-yellow-700 text-xs">Editar</button>
                      <button onClick={() => removeUser(user.id)} className="px-3 py-2 rounded-2xl bg-red-100 text-red-700 text-xs">Borrar</button>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
