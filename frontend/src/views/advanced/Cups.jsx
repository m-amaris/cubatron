import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api'

export default function CupsView() {
  const [cups, setCups] = useState([])
  const [newCup, setNewCup] = useState({ name: '', capacity_ml: 300, description: '' })
  const [message, setMessage] = useState('')

  useEffect(() => { fetchCups() }, [])

  async function fetchCups() {
    try { const r = await api.get('/cups'); setCups(r.data || []) }
    catch (e) { setCups([]) }
  }

  async function createCup() {
    if (!newCup.name || !newCup.capacity_ml) { setMessage('Nombre y capacidad obligatorios'); setTimeout(()=>setMessage(''),3000); return }
    try { await api.post('/cups', newCup); setNewCup({ name: '', capacity_ml: 300, description: '' }); setMessage('Vaso creado'); fetchCups() }
    catch (err) { setMessage('Error: '+(err.response?.data?.detail||err.message)) }
    setTimeout(()=>setMessage(''),3000)
  }

  async function removeCup(id) {
    if (!window.confirm('Eliminar vaso?')) return
    try { await api.delete(`/cups/${id}`); setMessage('Vaso eliminado'); fetchCups() }
    catch (err) { setMessage('Error: '+(err.response?.data?.detail||err.message)) }
    setTimeout(()=>setMessage(''),3000)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to="/menu/avanzado" className="p-2 bg-white rounded-full shadow-sm">←</Link>
        <h2 className="text-lg font-semibold">Vasos</h2>
        <div className="w-8" />
      </div>

      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm">
          <div className="text-sm font-medium mb-2">Nuevo vaso</div>
          <input placeholder="Nombre" value={newCup.name} onChange={e=>setNewCup(p=>({...p,name:e.target.value}))} className="w-full p-3 rounded-2xl border border-gray-100 mb-2" />
          <input type="number" placeholder="Capacidad (ml)" value={newCup.capacity_ml} onChange={e=>setNewCup(p=>({...p,capacity_ml:Number(e.target.value)}))} className="w-full p-3 rounded-2xl border border-gray-100 mb-2" />
          <input placeholder="Descripción" value={newCup.description} onChange={e=>setNewCup(p=>({...p,description:e.target.value}))} className="w-full p-3 rounded-2xl border border-gray-100" />
          <button onClick={createCup} className="w-full mt-3 py-3 rounded-3xl bg-indigo-700 text-white">Agregar vaso</button>
        </div>

        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Vasos registrados</div>
          {cups.map(c => (
            <div key={c.id} className="rounded-2xl border border-gray-100 p-3 flex items-center justify-between">
              <div>
                <div className="font-medium">{c.name}</div>
                <div className="text-xs text-gray-500">{c.capacity_ml} ml · {c.description || 'Sin descripción'}</div>
              </div>
              <div className="flex gap-2">
                <button onClick={()=>removeCup(c.id)} className="px-3 py-2 rounded-2xl bg-red-100 text-red-700 text-xs">Eliminar</button>
              </div>
            </div>
          ))}
        </div>
      </div>
      {message && <div className="text-sm text-green-700">{message}</div>}
    </div>
  )
}
