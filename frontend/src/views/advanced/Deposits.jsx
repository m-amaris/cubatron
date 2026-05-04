import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api'

export default function DepositsView() {
  const [ingredients, setIngredients] = useState([])
  const [deposits, setDeposits] = useState([])
  const [message, setMessage] = useState('')

  useEffect(() => { fetchAll() }, [])

  async function fetchAll() {
    try { const r = await api.get('/machine/ingredients'); setIngredients(r.data || []) } catch(e) { setIngredients([]) }
    try { const r2 = await api.get('/machine/deposits'); setDeposits(r2.data || []) } catch(e) { setDeposits([]) }
  }

  async function updateDeposit(id, payload) {
    try { await api.patch(`/machine/deposits/${id}`, payload); setMessage('Depósito actualizado'); fetchAll() }
    catch (err) { setMessage('Error: ' + (err.response?.data?.detail || err.message)) }
    setTimeout(()=>setMessage(''),3000)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <Link to="/menu/avanzado" className="p-2 bg-white rounded-full shadow-sm">←</Link>
        <h2 className="text-lg font-semibold">Depósitos</h2>
        <div className="w-8" />
      </div>

      <div className="space-y-4">
        <div className="bg-white p-4 rounded-3xl border border-gray-100 shadow-sm space-y-3">
          <div className="text-sm font-medium">Depósitos</div>
          {deposits.length === 0 ? <div className="text-sm text-gray-500">No hay depósitos.</div> : deposits.map(d => (
            <div key={d.id} className="rounded-2xl border border-gray-100 p-3 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Depósito {d.slot}</div>
                  <div className="text-xs text-gray-500">Ingrediente: {d.ingredient_name || 'Sin asignar'}</div>
                </div>
                <div className="text-xs text-gray-500">{d.level_ml}/{d.capacity_ml} ml</div>
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                <select value={d.ingredient_id || ''} onChange={e => updateDeposit(d.id, { ingredient_id: Number(e.target.value) || null })} className="w-full p-3 rounded-2xl border border-gray-100">
                  <option value="">Seleccionar ingrediente</option>
                  {ingredients.map(ing => (<option key={ing.id} value={ing.id}>{ing.name}</option>))}
                </select>
                <input type="number" defaultValue={d.level_ml} onBlur={e => updateDeposit(d.id, { level_ml: Number(e.target.value) })} className="w-full p-3 rounded-2xl border border-gray-100" placeholder="Nivel (ml)" />
                <input type="number" defaultValue={d.capacity_ml} onBlur={e => updateDeposit(d.id, { capacity_ml: Number(e.target.value) })} className="w-full p-3 rounded-2xl border border-gray-100" placeholder="Capacidad (ml)" />
              </div>
            </div>
          ))}
        </div>
      </div>
      {message && <div className="text-sm text-green-700">{message}</div>}
    </div>
  )
}
